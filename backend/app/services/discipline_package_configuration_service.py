"""Guarded Batch-3 Organization and Project package-configuration mutations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import DisciplinePackageGuardMode
from app.models.discipline_package import (OrganizationPackageConfigurationHead, OrganizationPackageSelection, PackageConfigurationAuditEvent, PackageDescriptor, ProjectPackageConfigurationHead, ProjectPackageConfigurationRevision, ProjectPackageConfigurationSelection, RegistryMembership, RegistryRelease)
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.project import Project
from app.repositories.discipline_package_unit_of_work import DisciplinePackageUnitOfWork
from app.repositories.project_repository import ProjectRepository
from app.services.discipline_package_service import (
    FrozenGuardedIdentity,
    GuardedAuthorityLoader,
    evaluate_persisted_exact_compatibility,
    is_retryable_database_error,
)


@dataclass(frozen=True, slots=True)
class GuardedRequestIdentity:
    actor_id: int
    organization_id: UUID
    auth_version: int
    correlation_id: UUID = field(default_factory=uuid4)

    def frozen(self) -> FrozenGuardedIdentity:
        return FrozenGuardedIdentity(self.actor_id, self.organization_id, self.auth_version, self.correlation_id)


@dataclass(frozen=True, slots=True)
class ExactPackageSelection:
    package_key: str
    package_version: str
    descriptor_digest: str


@dataclass(frozen=True, slots=True)
class OrganizationConfigurationRequest:
    expected_configuration_version: int
    selections: tuple[ExactPackageSelection, ...]
    rationale: str


@dataclass(frozen=True, slots=True)
class ProjectConfigurationRequest:
    expected_configuration_version: int
    profile_id: str
    profile_digest: str
    selections: tuple[ExactPackageSelection, ...]
    rationale: str


class DisciplinePackageConfigurationService:
    """Only these outer methods complete guarded configuration transactions."""

    def __init__(self, factory: sessionmaker):
        self._factory = factory

    def replace_organization_configuration(self, identity: GuardedRequestIdentity, request: OrganizationConfigurationRequest) -> int:
        self._validate_organization_request(request.expected_configuration_version, request.selections, request.rationale)
        return self._retry(lambda: self._replace_organization_once(identity, request))

    def replace_project_configuration(self, identity: GuardedRequestIdentity, project_id: int, request: ProjectConfigurationRequest) -> int:
        self._validate_request(request.expected_configuration_version, request.selections, request.rationale)
        return self._retry(lambda: self._replace_project_once(identity, project_id, request))

    def remove_project_configuration(self, identity: GuardedRequestIdentity, project_id: int, *, expected_configuration_version: int, rationale: str) -> None:
        if expected_configuration_version < 1 or not rationale.strip():
            raise ValueError("invalid Project configuration removal")
        self._retry(lambda: self._remove_project_once(identity, project_id, expected_configuration_version, rationale))

    def _retry(self, operation):
        for attempt in range(2):
            try:
                return operation()
            except OperationalError as exc:
                if not is_retryable_database_error(exc) or attempt == 1:
                    raise ValueError("concurrent package configuration update") from exc
        raise AssertionError("unreachable")

    def _replace_organization_once(self, identity: GuardedRequestIdentity, request: OrganizationConfigurationRequest) -> int:
        with DisciplinePackageUnitOfWork(self._factory) as uow:
            assert uow.session is not None
            session = uow.session
            uow.acquire_guard(DisciplinePackageGuardMode.SHARED)
            GuardedAuthorityLoader.load(session, identity.frozen(), admin_only=True)
            registry = self._current_registry(session)
            head = session.get(OrganizationPackageConfigurationHead, identity.organization_id, with_for_update=True)
            if head is None:
                if request.expected_configuration_version != 0:
                    raise ValueError("configuration version conflict")
                head = OrganizationPackageConfigurationHead(organization_id=identity.organization_id, configuration_version=0)
                session.add(head); session.flush()
            if head.configuration_version != request.expected_configuration_version:
                raise ValueError("configuration version conflict")
            existing = {(row.package_key, row.package_version): row for row in session.scalars(select(OrganizationPackageSelection).where(OrganizationPackageSelection.organization_id == identity.organization_id).order_by(OrganizationPackageSelection.package_key, OrganizationPackageSelection.package_version).with_for_update())}
            self._validate_descriptors(session, registry.registry_digest, request.selections)
            version = head.configuration_version + 1
            desired = {(item.package_key, item.package_version) for item in request.selections}
            for item in request.selections:
                row = existing.get((item.package_key, item.package_version))
                if row is None:
                    session.add(OrganizationPackageSelection(organization_id=identity.organization_id, package_key=item.package_key, package_version=item.package_version, state="enabled", configuration_version=version))
                else:
                    row.state, row.configuration_version = "enabled", version
            for key, row in existing.items():
                if key not in desired and row.state == "enabled":
                    row.state, row.configuration_version = "disabled", version
            head.configuration_version = version
            self._audit(
                session, identity, "ORG_CONFIGURATION", "replace",
                occurred_at=datetime.now(timezone.utc), rationale=request.rationale,
            )
            uow.commit()
            return version

    def _replace_project_once(self, identity: GuardedRequestIdentity, project_id: int, request: ProjectConfigurationRequest) -> int:
        with DisciplinePackageUnitOfWork(self._factory) as uow:
            assert uow.session is not None
            session = uow.session
            uow.acquire_guard(DisciplinePackageGuardMode.SHARED)
            authority = GuardedAuthorityLoader.load(session, identity.frozen())
            registry = self._current_registry(session)
            org_head = session.get(OrganizationPackageConfigurationHead, identity.organization_id, with_for_update={"read": True})
            if org_head is None:
                raise ValueError("organization package configuration required")
            enabled = {(row.package_key, row.package_version) for row in session.scalars(select(OrganizationPackageSelection).where(OrganizationPackageSelection.organization_id == identity.organization_id, OrganizationPackageSelection.state == "enabled").with_for_update(read=True))}
            requested = {(item.package_key, item.package_version) for item in request.selections}
            if not requested.issubset(enabled):
                raise ValueError("project selection is not organization enabled")
            project = ProjectRepository(session).get_locked_for_package_configuration(project_id, organization_id=identity.organization_id)
            if project is None:
                raise LookupError("project not found")
            if authority.role != "admin" and project.owner_id != identity.actor_id:
                raise PermissionError("project configuration forbidden")
            head = session.get(ProjectPackageConfigurationHead, project_id, with_for_update=True)
            if (0 if head is None else head.configuration_version) != request.expected_configuration_version:
                raise ValueError("configuration version conflict")
            self._validate_descriptors(session, registry.registry_digest, request.selections)
            self._validate_profile_and_combination(
                session,
                registry,
                request,
                enabled_package_keys=frozenset(key for key, _version in enabled),
            )
            workspaces = list(session.scalars(select(EngineeringWorkspace).where(EngineeringWorkspace.project_id == project_id, EngineeringWorkspace.package_binding_state == "OPERATIONAL_PACKAGE_BOUND").order_by(EngineeringWorkspace.id).with_for_update()))
            if len(workspaces) > 6:
                raise ValueError("workspace rebind limit exceeded")
            package_keys = {item.package_key for item in request.selections}
            if any(workspace.bound_package_key not in package_keys for workspace in workspaces):
                raise ValueError("workspace rebind incompatible")
            revision = session.scalar(select(func.coalesce(func.max(ProjectPackageConfigurationRevision.configuration_revision), 0)).where(ProjectPackageConfigurationRevision.project_id == project_id)) + 1
            session.add(ProjectPackageConfigurationRevision(project_id=project_id, configuration_revision=revision, organization_id=identity.organization_id, observed_registry_digest=registry.registry_digest, profile_id=request.profile_id, profile_digest=request.profile_digest, rationale=request.rationale))
            session.flush()
            for item in request.selections:
                session.add(ProjectPackageConfigurationSelection(project_id=project_id, configuration_revision=revision, package_key=item.package_key, package_version=item.package_version, descriptor_digest=item.descriptor_digest))
            if head is None:
                session.add(ProjectPackageConfigurationHead(project_id=project_id, organization_id=identity.organization_id, current_revision=revision, configuration_version=1))
            else:
                head.current_revision, head.configuration_version = revision, head.configuration_version + 1
            audit_occurred_at = datetime.now(timezone.utc)
            self._audit(
                session, identity, "PROJECT_CONFIGURATION", "replace",
                occurred_at=audit_occurred_at, project_id=project_id,
                rationale=request.rationale,
            )
            for workspace in workspaces:
                workspace.bound_project_configuration_revision = revision
                self._audit(
                    session, identity, "WORKSPACE_BINDING", "rebind",
                    occurred_at=audit_occurred_at, project_id=project_id,
                    workspace_id=workspace.id, rationale=request.rationale,
                )
            uow.commit()
            return revision

    def _remove_project_once(self, identity: GuardedRequestIdentity, project_id: int, expected_configuration_version: int, rationale: str) -> None:
        with DisciplinePackageUnitOfWork(self._factory) as uow:
            assert uow.session is not None
            session = uow.session
            uow.acquire_guard(DisciplinePackageGuardMode.SHARED)
            authority = GuardedAuthorityLoader.load(session, identity.frozen())
            project = ProjectRepository(session).get_locked_for_package_configuration(project_id, organization_id=identity.organization_id)
            if project is None:
                raise LookupError("project not found")
            if authority.role != "admin" and project.owner_id != identity.actor_id:
                raise PermissionError("project configuration forbidden")
            head = session.get(ProjectPackageConfigurationHead, project_id, with_for_update=True)
            if head is None or head.configuration_version != expected_configuration_version:
                raise ValueError("configuration version conflict")
            # PostgreSQL forbids FOR UPDATE on an aggregate.  Lock the exact
            # affected rows in the accepted ascending-ID order, then decide
            # whether the immutable head may be removed.
            bound = list(session.scalars(
                select(EngineeringWorkspace.id)
                .where(
                    EngineeringWorkspace.project_id == project_id,
                    EngineeringWorkspace.package_binding_state
                    == "OPERATIONAL_PACKAGE_BOUND",
                )
                .order_by(EngineeringWorkspace.id)
                .with_for_update()
            ))
            if bound:
                raise ValueError("cannot remove Project configuration with bound Workspaces")
            session.delete(head)
            self._audit(
                session, identity, "PROJECT_CONFIGURATION", "remove",
                occurred_at=datetime.now(timezone.utc), project_id=project_id,
                rationale=rationale,
            )
            uow.commit()

    @staticmethod
    def _validate_request(expected_version: int, selections: tuple[ExactPackageSelection, ...], rationale: str) -> None:
        if expected_version < 0 or not 1 <= len(selections) <= 8 or len({item.package_key for item in selections}) != len(selections) or not rationale.strip():
            raise ValueError("configuration requires a rationale and 1..8 exact unique package keys")

    @staticmethod
    def _validate_organization_request(expected_version: int, selections: tuple[ExactPackageSelection, ...], rationale: str) -> None:
        if expected_version < 0 or len(selections) > 16 or len({item.package_key for item in selections}) != len(selections) or not rationale.strip():
            raise ValueError("Organization configuration requires a rationale and 0..16 exact unique package keys")

    @staticmethod
    def _current_registry(session: Session) -> RegistryRelease:
        registry = session.scalar(select(RegistryRelease).where(RegistryRelease.is_current.is_(True)).with_for_update(read=True))
        if registry is None:
            raise ValueError("Registry projection is not ready")
        return registry

    @staticmethod
    def _validate_descriptors(session: Session, registry_digest: str, selections: tuple[ExactPackageSelection, ...]) -> None:
        for item in selections:
            descriptor = session.get(PackageDescriptor, (item.package_key, item.package_version))
            membership = session.get(RegistryMembership, (registry_digest, item.package_key, item.package_version))
            if descriptor is None or membership is None or descriptor.descriptor_digest != item.descriptor_digest or membership.standing != "executable_supported":
                raise ValueError("exact executable package descriptor is unavailable")

    @staticmethod
    def _validate_profile_and_combination(
        session: Session,
        registry: RegistryRelease,
        request: ProjectConfigurationRequest,
        *,
        enabled_package_keys: frozenset[str],
    ) -> None:
        if not evaluate_persisted_exact_compatibility(
            session,
            registry,
            profile_id=request.profile_id,
            profile_digest=request.profile_digest,
            selections=tuple(
                (item.package_key, item.package_version, item.descriptor_digest)
                for item in request.selections
            ),
            enabled_package_keys=enabled_package_keys,
        ):
            raise ValueError("exact Project package combination is unavailable")

    @staticmethod
    def _audit(session: Session, identity: GuardedRequestIdentity, category: str, action: str, *, occurred_at: datetime, project_id: int | None = None, workspace_id: int | None = None, rationale: str) -> None:
        session.add(PackageConfigurationAuditEvent(
            event_id=uuid4(), organization_id=identity.organization_id,
            project_id=project_id, workspace_id=workspace_id,
            actor_user_id=identity.actor_id, category=category, action=action,
            occurred_at=occurred_at,
            correlation_id=identity.correlation_id,
            metadata_json={"rationale_digest": sha256(rationale.encode()).hexdigest()},
        ))
