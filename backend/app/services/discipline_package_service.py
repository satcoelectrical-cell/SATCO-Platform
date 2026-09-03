"""Guarded runtime seams for PATCH-051 package-derived Workspace state."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import DisciplinePackageGuardMode
from app.models.discipline_package import (OrganizationPackageSelection, PackageConfigurationAuditEvent, PackageDescriptor, ProjectPackageConfigurationHead, ProjectPackageConfigurationRevision, ProjectPackageConfigurationSelection, RegistryMembership, RegistryRelease)
from app.models.engineering_workspace import EngineeringWorkspace, EngineeringWorkspaceMember
from app.models.organization import Organization, UserOrganizationMembership
from app.models.project import Project
from app.models.user import User
from app.repositories.discipline_package_unit_of_work import DisciplinePackageUnitOfWork
from app.repositories.engineering_workspace_repository import EngineeringWorkspaceRepository
from app.repositories.project_repository import ProjectRepository
from app.services.audit_service import stage_audit_log
from app.adapters.discipline_package_registry import StaticDisciplinePackageAdapter
from app.discipline_packages.compatibility import (
    CompatibilityInputV1,
    evaluate_package_compatibility,
)
from app.discipline_packages.contracts import (
    ExactPackageSelectionV1,
    RegistryReleaseManifestV1,
)
from app.discipline_packages.identity import DescriptorDigest, PackageKey, PackageVersion
from app.discipline_packages.registry import assemble_registry
from app.enums.discipline_package import CompatibilityDecision
from app.exceptions.discipline_package import DisciplinePackageError


class PackageWorkspaceConflict(ValueError):
    pass


class PackageWorkspaceForbidden(PermissionError):
    pass


class PackageWorkspaceAlreadyExists(PackageWorkspaceConflict):
    pass


class PackageWorkspaceInvalidPerson(PackageWorkspaceConflict):
    def __init__(self, kind: str):
        self.kind = kind
        super().__init__(f"invalid Workspace {kind}")


@dataclass(frozen=True, slots=True)
class FrozenGuardedIdentity:
    actor_id: int
    organization_id: UUID
    auth_version: int
    correlation_id: UUID = field(default_factory=uuid4)


@dataclass(frozen=True, slots=True)
class WorkspaceCreateCommand:
    project_id: int
    discipline: str
    description: str | None
    owner_id: int
    primary_assignee_id: int | None
    collaborator_ids: tuple[int, ...]


class GuardedAuthorityLoader:
    """Reload mutable authority only after the transaction guard is held."""

    @staticmethod
    def load(session: Session, identity: FrozenGuardedIdentity, *, admin_only: bool = False) -> User:
        user = session.scalar(select(User).where(User.id == identity.actor_id).with_for_update())
        membership = session.scalar(select(UserOrganizationMembership).where(UserOrganizationMembership.user_id == identity.actor_id, UserOrganizationMembership.organization_id == identity.organization_id).with_for_update())
        organization = session.scalar(select(Organization).where(Organization.id == identity.organization_id).with_for_update())
        if (user is None or membership is None or organization is None or not user.is_active or user.auth_version != identity.auth_version or user.role not in {"admin", "engineer"} or (admin_only and user.role != "admin") or not membership.is_enabled or not membership.is_selected or not organization.is_active):
            raise PackageWorkspaceForbidden("guarded authority denied")
        return user


def is_retryable_database_error(exc: OperationalError) -> bool:
    return getattr(getattr(exc, "orig", None), "sqlstate", None) in {"55P03", "40P01", "40001"}


def evaluate_persisted_exact_compatibility(
    session: Session,
    registry_release: RegistryRelease,
    *,
    profile_id: str,
    profile_digest: str,
    selections: tuple[tuple[str, str, str], ...],
    enabled_package_keys: frozenset[str] | None = None,
) -> bool:
    """Use the Batch-1 evaluator against the immutable persisted source release.

    The Registry projection retains canonical descriptor/profile JSON.  It is
    reassembled into the same typed deterministic Registry used by Batch 1;
    SQL membership rows remain provenance/availability checks, never a second
    compatibility algorithm.
    """
    try:
        # Projection JSON is intentionally canonical JSON, so parse it through
        # Pydantic's JSON boundary.  That restores the Batch-1 digest-domain
        # values rather than treating their serialized strings as Python input.
        manifest = RegistryReleaseManifestV1.model_validate_json(
            json.dumps(registry_release.manifest_json)
        )
        adapters = tuple(
            StaticDisciplinePackageAdapter(
                adapter_id=item.descriptor.adapter_id,
                package_key=PackageKey(item.descriptor.package_key),
                package_version=PackageVersion(item.descriptor.package_version),
                capability_ids=frozenset(
                    hook.id for hook in item.descriptor.contributions.deterministic_rule_hooks
                ) | frozenset(
                    hook.hook_id for hook in item.descriptor.contributions.standards_hooks
                ) | frozenset(
                    interface.interface_type_id
                    for interface in item.descriptor.contributions.cross_discipline_interfaces
                ),
            )
            for item in manifest.descriptors
        )
        registry = assemble_registry(manifest, adapters=adapters)
        if str(registry.digest) != registry_release.registry_digest:
            return False
        profile = next(
            (
                item for item in manifest.profiles
                if item.profile_id == profile_id
                and str(registry.profile_digests[(item.profile_id, item.profile_version)])
                == profile_digest
            ),
            None,
        )
        if profile is None:
            return False
        result = evaluate_package_compatibility(
            CompatibilityInputV1(
                registry=registry,
                core_contract_version=registry_release.core_contract_version,
                selections=tuple(
                    ExactPackageSelectionV1(
                        package_key=key,
                        package_version=version,
                        descriptor_digest=DescriptorDigest(digest),
                    )
                    for key, version, digest in selections
                ),
                profile_id=profile.profile_id,
                profile_version=profile.profile_version,
                enabled_package_keys=enabled_package_keys,
            )
        )
        return (
            result.decision is CompatibilityDecision.COMPATIBLE
            and result.registry_digest is not None
            and str(result.registry_digest) == registry_release.registry_digest
            and result.profile_digest is not None
            and str(result.profile_digest) == profile_digest
        )
    except (DisciplinePackageError, TypeError, ValueError, KeyError):
        return False


class DisciplinePackageWorkspaceService:
    """The sole commit owner for package-derived Workspace creation."""

    _PACKAGE_DISCIPLINES = {"electrical": ("electrical", "electrical"), "instrumentation": ("instrumentation", "instrumentation"), "control": ("control_automation", "control_automation")}
    _FUTURE_DISCIPLINES = {"mechanical": "mechanical", "civil": "civil", "process": "process"}

    def __init__(self, factory: sessionmaker):
        self._factory = factory

    def create(self, identity: FrozenGuardedIdentity, command: WorkspaceCreateCommand) -> int:
        for attempt in range(2):
            try:
                return self._create_once(identity, command)
            except OperationalError as exc:
                if not is_retryable_database_error(exc) or attempt == 1:
                    raise PackageWorkspaceConflict("concurrent Workspace update") from exc
        raise AssertionError("unreachable")

    def _create_once(self, identity: FrozenGuardedIdentity, command: WorkspaceCreateCommand) -> int:
        with DisciplinePackageUnitOfWork(self._factory) as uow:
            assert uow.session is not None
            session = uow.session
            uow.acquire_guard(DisciplinePackageGuardMode.SHARED)
            actor = GuardedAuthorityLoader.load(session, identity)
            registry = session.scalar(select(RegistryRelease).where(RegistryRelease.is_current.is_(True)).with_for_update(read=True))
            project = ProjectRepository(session).get_locked_for_package_configuration(
                command.project_id, organization_id=identity.organization_id
            )
            if project is None:
                raise PackageWorkspaceForbidden("project not found")
            if actor.role != "admin" and project.owner_id != identity.actor_id:
                raise PackageWorkspaceForbidden("Workspace creation forbidden")
            if project.status in {"completed", "cancelled"}:
                raise PackageWorkspaceConflict("Project cannot accept a Workspace")
            existing = EngineeringWorkspaceRepository(session).get_locked_by_project_discipline(
                command.project_id, command.discipline
            )
            if existing is not None:
                raise PackageWorkspaceAlreadyExists("Workspace discipline already exists")
            self._validate_people(session, command)
            canonical, state, package_key, revision = self._derive_binding(
                session,
                None if registry is None else registry.registry_digest,
                command.project_id,
                project.organization_id,
                command.discipline,
            )
            workspace = EngineeringWorkspace(project_id=command.project_id, discipline=command.discipline, description=command.description, status="draft", owner_id=command.owner_id, primary_assignee_id=command.primary_assignee_id, created_by_id=identity.actor_id, version=1, canonical_discipline_id=canonical, package_binding_state=state, bound_package_key=package_key, bound_project_configuration_revision=revision)
            session.add(workspace)
            session.flush()
            for user_id in command.collaborator_ids:
                session.add(EngineeringWorkspaceMember(workspace_id=workspace.id, user_id=user_id, added_by_id=identity.actor_id))
            stage_audit_log(session, identity.actor_id, "workspace_created", "ENGINEERING_WORKSPACE", workspace.id, {"project_id": command.project_id, "discipline": command.discipline, "package_binding_state": state, "canonical_discipline_id": canonical, "bound_package_key": package_key, "bound_project_configuration_revision": revision, "version": 1})
            session.add(PackageConfigurationAuditEvent(
                event_id=uuid4(), organization_id=identity.organization_id,
                project_id=command.project_id, workspace_id=workspace.id,
                actor_user_id=identity.actor_id, category="WORKSPACE_BINDING",
                action="create", occurred_at=datetime.now(timezone.utc),
                correlation_id=identity.correlation_id,
                metadata_json={"binding_digest": sha256(
                    f"{canonical}:{state}:{package_key}:{revision}".encode()
                ).hexdigest()},
            ))
            workspace_id = workspace.id
            uow.commit()
            return workspace_id

    @staticmethod
    def _validate_people(session: Session, command: WorkspaceCreateCommand) -> None:
        ids = {command.owner_id, *command.collaborator_ids}
        if command.primary_assignee_id is not None:
            ids.add(command.primary_assignee_id)
        people = {row.id: row for row in session.scalars(select(User).where(User.id.in_(ids)).with_for_update())}
        if command.owner_id not in people or not people[command.owner_id].is_active or people[command.owner_id].role not in {"admin", "engineer"}:
            raise PackageWorkspaceInvalidPerson("owner")
        if command.primary_assignee_id is not None and (command.primary_assignee_id not in people or not people[command.primary_assignee_id].is_active or people[command.primary_assignee_id].role not in {"admin", "engineer"}):
            raise PackageWorkspaceInvalidPerson("assignee")
        for user_id in command.collaborator_ids:
            if user_id not in people or not people[user_id].is_active or people[user_id].role not in {"admin", "engineer"}:
                raise PackageWorkspaceInvalidPerson("collaborator")
        if command.owner_id in command.collaborator_ids or command.primary_assignee_id in command.collaborator_ids:
            raise PackageWorkspaceConflict("Workspace collaborator conflicts with assignment")

    def _derive_binding(
        self,
        session: Session,
        registry_digest: str | None,
        project_id: int,
        organization_id: UUID,
        raw_discipline: str,
    ):
        if raw_discipline in self._FUTURE_DISCIPLINES:
            return self._FUTURE_DISCIPLINES[raw_discipline], "FUTURE_UNAVAILABLE_UNBOUND", None, None
        required = self._PACKAGE_DISCIPLINES.get(raw_discipline)
        if required is None:
            raise PackageWorkspaceConflict("unknown Workspace discipline")
        if registry_digest is None:
            raise PackageWorkspaceConflict("Registry projection is not ready")
        registry = session.get(RegistryRelease, registry_digest)
        if registry is None:
            raise PackageWorkspaceConflict("Registry projection is not ready")
        canonical, required_package_key = required
        head = session.get(ProjectPackageConfigurationHead, project_id, with_for_update={"read": True})
        if head is None:
            raise PackageWorkspaceConflict("Project package configuration is required")
        revision = session.get(ProjectPackageConfigurationRevision, (project_id, head.current_revision))
        if revision is None or revision.observed_registry_digest != registry_digest:
            raise PackageWorkspaceConflict("Project configuration does not match current Registry")
        selection = session.scalar(select(ProjectPackageConfigurationSelection).where(ProjectPackageConfigurationSelection.project_id == project_id, ProjectPackageConfigurationSelection.configuration_revision == head.current_revision, ProjectPackageConfigurationSelection.package_key == required_package_key).with_for_update(read=True))
        if selection is None:
            raise PackageWorkspaceConflict("Project has no exact discipline package selection")
        descriptor = session.get(PackageDescriptor, (selection.package_key, selection.package_version))
        membership = session.get(RegistryMembership, (registry_digest, selection.package_key, selection.package_version))
        if descriptor is None or membership is None or descriptor.descriptor_digest != selection.descriptor_digest or membership.standing != "executable_supported":
            raise PackageWorkspaceConflict("exact executable package selection is unavailable")
        selected = list(session.scalars(select(ProjectPackageConfigurationSelection).where(ProjectPackageConfigurationSelection.project_id == project_id, ProjectPackageConfigurationSelection.configuration_revision == head.current_revision).with_for_update(read=True)))
        enabled_keys = frozenset(session.scalars(
            select(OrganizationPackageSelection.package_key).where(
                OrganizationPackageSelection.organization_id == organization_id,
                OrganizationPackageSelection.state == "enabled",
            )
        ))
        if not evaluate_persisted_exact_compatibility(
            session,
            registry_release=registry,
            profile_id=revision.profile_id,
            profile_digest=revision.profile_digest,
            selections=tuple(
                (row.package_key, row.package_version, row.descriptor_digest)
                for row in selected
            ),
            enabled_package_keys=enabled_keys,
        ):
            raise PackageWorkspaceConflict("Project package selection is not compatible")
        return canonical, "OPERATIONAL_PACKAGE_BOUND", selection.package_key, head.current_revision
