"""Frozen post-lock authority and configuration checks for PATCH-052 writes."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.discipline_packages.descriptors.eic_v1 import DESCRIPTOR_DIGESTS_V1
from app.models.discipline_package import (
    OrganizationPackageConfigurationHead,
    OrganizationPackageSelection,
    PackageDescriptor,
    ProjectPackageConfigurationHead,
    ProjectPackageConfigurationRevision,
    ProjectPackageConfigurationSelection,
    RegistryMembership,
    RegistryProfileMembership,
    RegistryRelease,
)
from app.models.engineering_workspace import (
    EngineeringWorkspace,
    EngineeringWorkspaceMember,
)
from app.models.project import Project
from app.services.discipline_package_service import (
    FrozenGuardedIdentity,
    GuardedAuthorityLoader,
    PackageWorkspaceForbidden,
)


class Patch052MutationProtected(LookupError):
    pass


class Patch052MutationUnavailable(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class LockedPackageMutationContext:
    actor: object
    project: Project
    workspace: EngineeringWorkspace
    registry: RegistryRelease | None = None
    revision: ProjectPackageConfigurationRevision | None = None
    selection: ProjectPackageConfigurationSelection | None = None


def _lock_actor(
    session: Session,
    *,
    actor_id: int,
    organization_id: UUID,
    auth_version: int,
):
    try:
        return GuardedAuthorityLoader.load(
            session,
            FrozenGuardedIdentity(
                actor_id=actor_id,
                organization_id=organization_id,
                auth_version=auth_version,
            ),
        )
    except PackageWorkspaceForbidden as exc:
        raise Patch052MutationProtected() from exc


def _lock_project(
    session: Session, *, project_id: int, organization_id: UUID,
) -> Project:
    project = session.scalar(
        select(Project)
        .where(
            Project.id == project_id,
            Project.organization_id == organization_id,
        )
        .with_for_update()
    )
    if project is None:
        raise Patch052MutationProtected()
    return project


def _lock_workspace(
    session: Session, *, workspace_id: int, project_id: int,
) -> EngineeringWorkspace:
    workspace = session.scalar(
        select(EngineeringWorkspace)
        .where(
            EngineeringWorkspace.id == workspace_id,
            EngineeringWorkspace.project_id == project_id,
        )
        .with_for_update()
    )
    if workspace is None:
        raise Patch052MutationProtected()
    return workspace


def _authorize_locked_scope(
    session: Session,
    *,
    actor,
    project: Project,
    workspace: EngineeringWorkspace,
) -> None:
    if (
        not actor.is_active
        or actor.role not in {"admin", "engineer"}
        or project.status in {"completed", "cancelled"}
    ):
        raise Patch052MutationProtected()
    if actor.role == "admin" or actor.id in {
        project.owner_id,
        project.primary_assignee_id,
        workspace.owner_id,
        workspace.primary_assignee_id,
    }:
        return
    membership = session.get(
        EngineeringWorkspaceMember,
        (workspace.id, actor.id),
        with_for_update=True,
    )
    if membership is None:
        raise Patch052MutationProtected()


def lock_owner_mutation_scope(
    session: Session,
    *,
    actor_id: int,
    organization_id: UUID,
    auth_version: int,
    project_id: int,
    workspace_id: int,
) -> LockedPackageMutationContext:
    """Lock mutable Human/tenant authority, Project, then Workspace."""

    actor = _lock_actor(
        session,
        actor_id=actor_id,
        organization_id=organization_id,
        auth_version=auth_version,
    )
    project = _lock_project(
        session, project_id=project_id, organization_id=organization_id,
    )
    workspace = _lock_workspace(
        session, workspace_id=workspace_id, project_id=project_id,
    )
    _authorize_locked_scope(
        session, actor=actor, project=project, workspace=workspace,
    )
    return LockedPackageMutationContext(actor, project, workspace)


def lock_and_authorize_workspaces(
    session: Session, *, context: LockedPackageMutationContext,
    workspace_ids: set[int],
) -> dict[int, EngineeringWorkspace]:
    """Lock every endpoint Workspace deterministically and authorize it."""

    rows: dict[int, EngineeringWorkspace] = {}
    for workspace_id in sorted(workspace_ids):
        workspace = _lock_workspace(
            session, workspace_id=workspace_id, project_id=context.project.id,
        )
        _authorize_locked_scope(
            session, actor=context.actor, project=context.project,
            workspace=workspace,
        )
        rows[workspace_id] = workspace
    return rows


def lock_package_context(
    uow,
    *,
    package_key: str,
    package_version: str = "1.0.0",
    actor_id: int,
    organization_id: UUID,
    auth_version: int,
    project_id: int,
    workspace_id: int,
) -> LockedPackageMutationContext:
    """Lock and recheck current package authority before target aggregates."""

    session: Session = uow.session
    uow.acquire_registry_guard()
    # The advisory guard serializes against Registry/configuration publication.
    # Lock every persisted package-authority fact before mutable owner aggregates.
    registry = session.scalar(
        select(RegistryRelease)
        .where(RegistryRelease.is_current.is_(True))
        .with_for_update(read=True)
    )
    organization_head = session.get(
        OrganizationPackageConfigurationHead,
        organization_id,
        with_for_update={"read": True},
    )
    organization_selection = session.scalar(
        select(OrganizationPackageSelection)
        .where(
            OrganizationPackageSelection.organization_id == organization_id,
            OrganizationPackageSelection.package_key == package_key,
            OrganizationPackageSelection.package_version == package_version,
        )
        .with_for_update(read=True)
    )
    head = session.get(
        ProjectPackageConfigurationHead,
        project_id,
        with_for_update={"read": True},
    )
    if head is None:
        raise Patch052MutationUnavailable()
    revision = session.get(
        ProjectPackageConfigurationRevision,
        (project_id, head.current_revision),
        with_for_update={"read": True},
    )
    selection = session.get(
        ProjectPackageConfigurationSelection,
        (project_id, head.current_revision, package_key),
        with_for_update={"read": True},
    )
    profile_membership = None
    if registry is not None and revision is not None:
        profile_membership = session.get(
            RegistryProfileMembership,
            (registry.registry_digest, revision.profile_id),
            with_for_update={"read": True},
        )
    descriptor = session.get(
        PackageDescriptor,
        (package_key, package_version),
        with_for_update={"read": True},
    )
    membership = None
    if registry is not None:
        membership = session.get(
            RegistryMembership,
            (registry.registry_digest, package_key, package_version),
            with_for_update={"read": True},
        )
    actor = _lock_actor(
        session,
        actor_id=actor_id,
        organization_id=organization_id,
        auth_version=auth_version,
    )
    project = _lock_project(
        session, project_id=project_id, organization_id=organization_id,
    )
    workspace = _lock_workspace(
        session, workspace_id=workspace_id, project_id=project_id,
    )

    if package_key not in {"electrical", "instrumentation", "control_automation"}:
        raise Patch052MutationUnavailable()
    digest = str(DESCRIPTOR_DIGESTS_V1[package_key])
    if (
        registry is None
        or organization_head is None
        or organization_selection is None
        or organization_selection.state != "enabled"
        or organization_selection.configuration_version
        != organization_head.configuration_version
        or revision is None
        or revision.organization_id != organization_id
        or revision.observed_registry_digest != registry.registry_digest
        or profile_membership is None
        or profile_membership.profile_digest != revision.profile_digest
        or selection is None
        or selection.package_version != package_version
        or selection.descriptor_digest != digest
        or descriptor is None
        or descriptor.descriptor_digest != digest
        or membership is None
        or membership.standing != "executable_supported"
        or workspace.package_binding_state != "OPERATIONAL_PACKAGE_BOUND"
        or workspace.bound_package_key != package_key
        or workspace.bound_project_configuration_revision != head.current_revision
    ):
        raise Patch052MutationUnavailable()

    # These values are now held by transaction locks.  Recheck authority only
    # after the complete package execution context and Workspace are stable.
    _authorize_locked_scope(
        session, actor=actor, project=project, workspace=workspace,
    )
    return LockedPackageMutationContext(
        actor, project, workspace, registry, revision, selection,
    )


def lock_electrical_package_context(uow, **kwargs) -> LockedPackageMutationContext:
    """Backward-compatible Batch-2 entry point over the shared guard."""

    return lock_package_context(
        uow, package_key="electrical", package_version="1.0.0", **kwargs,
    )
