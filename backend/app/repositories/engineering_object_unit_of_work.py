"""Atomic SQLAlchemy Unit of Work and PATCH-023 persistence adapters."""

from datetime import datetime, timezone
from typing import Mapping, Self
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.enums import EngineeringDiscipline
from app.exceptions.engineering_object import EngineeringObjectIdempotencyConflict
from app.exceptions.engineering_object import EngineeringObjectValidationError
from app.models.audit_log import AuditLog
from app.models.engineering_object import EngineeringObject
from app.models.engineering_object_command import AuthenticatedActor
from app.models.engineering_object_command import AuthorizationContext
from app.models.engineering_object_command import EngineeringObjectCommandResult
from app.models.engineering_object_command import EngineeringObjectDomainEvent
from app.models.engineering_object_command import EngineeringObjectIdempotency
from app.models.engineering_object_command import EngineeringObjectIdempotencyOutcome
from app.models.engineering_object_command import EngineeringObjectOutbox
from app.models.engineering_object_command import Scalar
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.engineering_workspace import EngineeringWorkspaceMember
from app.models.project import Project
from app.models.user import User
from app.repositories.engineering_object_repository import (
    SqlAlchemyEngineeringObjectRepository,
)


def _json(value):
    if isinstance(value, (UUID, datetime)):
        return value.isoformat() if isinstance(value, datetime) else str(value)
    if isinstance(value, Mapping):
        return {key: _json(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json(item) for item in value]
    return value


class SqlAlchemyAuditRecorder:
    def __init__(self, session: Session):
        self.session = session

    def record(self, **values) -> None:
        actor = values.pop("actor")
        object_id = values.pop("object_id")
        command_type = values.pop("command_type")
        self.session.add(AuditLog(
            user_id=actor.actor_id, action=command_type,
            entity="ENGINEERING_OBJECT", entity_uuid=object_id,
            details=_json(values),
        ))


class SqlAlchemyDomainEventRecorder:
    def __init__(self, session: Session):
        self.session = session

    def record(self, events: tuple[EngineeringObjectDomainEvent, ...]) -> None:
        for event in events:
            self.session.add(EngineeringObjectOutbox(
                event_id=event.event_id, aggregate_id=event.object_id,
                aggregate_version=event.aggregate_version,
                event_type=event.event_type,
                schema_version=event.schema_version,
                payload=_json({
                    "actor_id": event.actor_id,
                    "correlation_id": event.correlation_id,
                    "causation_id": event.causation_id,
                    "organization_id": event.organization_id,
                    "project_id": event.project_id,
                    "workspace_id": event.workspace_id,
                    "payload": event.payload,
                }),
                occurred_at=event.occurred_at,
            ))


class SqlAlchemyIdempotencyStore:
    def __init__(self, session: Session):
        self.session = session
        self.reservation: EngineeringObjectIdempotency | None = None

    def find(self, *, actor_id: int, command_type: str,
             idempotency_id: UUID, request_fingerprint: str):
        row = self.session.query(EngineeringObjectIdempotency).filter_by(
            actor_id=actor_id, command_type=command_type,
            idempotency_id=idempotency_id,
        ).first()
        if row is None:
            return None
        if row.request_fingerprint != request_fingerprint:
            raise EngineeringObjectIdempotencyConflict()
        if row.status != "completed" or row.result is None:
            raise EngineeringObjectIdempotencyConflict()
        data = row.result
        result = EngineeringObjectCommandResult(
            object_id=UUID(data["object_id"]),
            previous_version=data["previous_version"], version=data["version"],
            command_type=data["command_type"],
            correlation_id=UUID(data["correlation_id"]), events=(),
        )
        return EngineeringObjectIdempotencyOutcome(
            result=result,
            authorized_state=data["authorized_state"],
        )

    def reserve(self, *, actor_id: int, command_type: str,
                idempotency_id: UUID, request_fingerprint: str) -> None:
        self.reservation = EngineeringObjectIdempotency(
            actor_id=actor_id, command_type=command_type,
            idempotency_id=idempotency_id,
            request_fingerprint=request_fingerprint, status="pending",
        )
        self.session.add(self.reservation)
        self.session.flush()

    def record_result(self, result: EngineeringObjectCommandResult,
                      authorized_state: Mapping[str, Scalar]) -> None:
        if self.reservation is None:
            raise RuntimeError("Idempotency reservation is required")
        self.reservation.status = "completed"
        self.reservation.aggregate_id = result.object_id
        self.reservation.result = _json({
            "object_id": result.object_id,
            "previous_version": result.previous_version,
            "version": result.version, "command_type": result.command_type,
            "correlation_id": result.correlation_id,
            "authorized_state": authorized_state,
        })


class UtcClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class SqlAlchemyAuthorizationPolicy:
    """Current-role, Project/Workspace-scoped deny-by-default policy."""

    def __init__(self, session: Session):
        self.session = session

    def authorize(self, *, actor: AuthenticatedActor,
                  context: AuthorizationContext,
                  current_state: EngineeringObject | None,
                  target_state: Mapping[str, Scalar]) -> bool:
        user = self.session.get(User, actor.actor_id)
        if user is None or not user.is_active:
            return False
        project_id = (
            current_state.project_id if current_state is not None
            else target_state.get("project_id")
        )
        project = self.session.query(Project).filter(
            Project.id == project_id,
            Project.organization_id == actor.organization_id,
        ).first() if project_id else None
        if project is None:
            return False
        if user.role == "admin":
            return True
        if actor.actor_id in {project.owner_id, project.primary_assignee_id}:
            return True
        workspace_id = (
            current_state.workspace_id if current_state is not None
            else target_state.get("workspace_id")
        )
        if workspace_id is None:
            return False
        workspace = self.session.get(EngineeringWorkspace, workspace_id)
        if workspace is None or workspace.project_id != project.id:
            return False
        return actor.actor_id in {
            workspace.owner_id, workspace.primary_assignee_id,
        } or self.session.get(
            EngineeringWorkspaceMember, (workspace.id, actor.actor_id)
        ) is not None


class SqlAlchemyReferenceValidator:
    COMPATIBILITY = {
        EngineeringDiscipline.INSTRUMENTATION: "instrumentation",
        EngineeringDiscipline.ELECTRICAL: "electrical",
        EngineeringDiscipline.INDUSTRIAL_AUTOMATION: "control",
    }

    def __init__(self, session: Session):
        self.session = session

    def validate_creation_references(
        self, *, actor: AuthenticatedActor, project_id: int,
        steward_id: int | None, evidence_references: tuple[UUID, ...],
        discipline: EngineeringDiscipline | None = None,
    ) -> Mapping[str, Scalar]:
        project = self.session.query(Project).filter(
            Project.id == project_id,
            Project.organization_id == actor.organization_id,
        ).first()
        if project is None:
            raise EngineeringObjectValidationError("Project is invalid")
        workspace_discipline = self.COMPATIBILITY.get(discipline)
        if workspace_discipline is None:
            raise EngineeringObjectValidationError(
                "Engineering Object discipline has no compatible Workspace"
            )
        workspace = self.session.query(EngineeringWorkspace).join(
            Project, Project.id == EngineeringWorkspace.project_id
        ).filter(
            EngineeringWorkspace.project_id == project_id,
            EngineeringWorkspace.discipline == workspace_discipline,
            Project.organization_id == actor.organization_id,
        ).one_or_none()
        if workspace is None:
            raise EngineeringObjectValidationError(
                "Compatible Engineering Workspace is unavailable"
            )
        target_steward = steward_id or actor.actor_id
        user = self.session.get(User, target_steward)
        if user is None or not user.is_active:
            raise EngineeringObjectValidationError("Steward is invalid")
        return {
            "organization_id": actor.organization_id,
            "customer_id": project.customer_id,
            "workspace_id": workspace.id,
            "creator_id": actor.actor_id,
            "steward_id": target_steward,
        }

    def validate_mutation_references(self, *, actor: AuthenticatedActor,
            object_id: UUID, references: Mapping[str, Scalar]) -> None:
        discipline = references.get("discipline")
        if discipline is not None:
            discipline = EngineeringDiscipline(discipline)
            workspace_discipline = self.COMPATIBILITY.get(discipline)
            aggregate = self.session.query(EngineeringObject).filter_by(
                id=object_id, organization_id=actor.organization_id
            ).first()
            workspace = (
                self.session.get(EngineeringWorkspace, aggregate.workspace_id)
                if aggregate is not None else None
            )
            if (
                workspace_discipline is None
                or workspace is None
                or workspace.discipline != workspace_discipline
            ):
                raise EngineeringObjectValidationError(
                    "Classification is incompatible with Workspace"
                )
        steward_id = references.get("steward_id")
        if steward_id is not None:
            user = self.session.get(User, steward_id)
            if user is None or not user.is_active:
                raise EngineeringObjectValidationError("Steward is invalid")
        replacement_id = references.get("replacement_object_id")
        if replacement_id is not None:
            replacement = self.session.query(EngineeringObject).filter_by(
                id=replacement_id, organization_id=actor.organization_id
            ).first()
            if replacement is None:
                raise EngineeringObjectValidationError(
                    "Replacement Engineering Object is invalid"
                )


class SqlAlchemyEngineeringObjectUnitOfWork:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def __enter__(self) -> Self:
        self.session = self.session_factory()
        self.engineering_objects = SqlAlchemyEngineeringObjectRepository(self.session)
        self.audit = SqlAlchemyAuditRecorder(self.session)
        self.domain_events = SqlAlchemyDomainEventRecorder(self.session)
        self.idempotency = SqlAlchemyIdempotencyStore(self.session)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            self.rollback()
        self.session.close()
        return None

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
