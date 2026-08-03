"""Atomic persistence and policy adapters for Engineering Experience Capture."""

from collections.abc import Mapping
from datetime import datetime, timezone
import hashlib
from typing import Self
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.exceptions.engineering_experience_capture import (
    EngineeringExperienceCaptureAuthorizationDenied,
    EngineeringExperienceCaptureDuplicateSupersession,
    EngineeringExperienceCaptureIdempotencyConflict,
    EngineeringExperienceCaptureInvalidContext,
    EngineeringExperienceCaptureInvalidSupersession,
    EngineeringExperienceCaptureProtectedNotFound,
    EngineeringExperienceCaptureSupersessionCycle,
)
from app.models.audit_log import AuditLog
from app.models.engineering_experience_capture import EngineeringExperienceCapture
from app.models.engineering_experience_capture_command import (
    EngineeringExperienceCaptureActor,
    EngineeringExperienceCaptureEvent,
    EngineeringExperienceCaptureIdempotency,
    EngineeringExperienceCaptureOutcome,
    EngineeringExperienceCaptureOutbox,
    EngineeringExperienceCaptureResult,
)
from app.models.engineering_object import EngineeringObject
from app.models.engineering_workspace import EngineeringWorkspace, EngineeringWorkspaceMember
from app.models.organization import Organization, UserOrganizationMembership
from app.models.project import Project
from app.models.user import User
from app.repositories.engineering_experience_capture_repository import (
    SqlAlchemyEngineeringExperienceCaptureRepository,
)


def _json(value):
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {key: _json(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json(item) for item in value]
    return value


def _scope_access(session: Session, actor: EngineeringExperienceCaptureActor,
                  project: Project, workspace: EngineeringWorkspace | None) -> bool:
    user = session.get(User, actor.actor_id)
    if user is None or not user.is_active:
        return False
    membership = session.get(UserOrganizationMembership, (actor.actor_id, actor.organization_id))
    organization = session.get(Organization, actor.organization_id)
    if membership is None or not membership.is_enabled or organization is None or not organization.is_active:
        return False
    if project.organization_id != actor.organization_id:
        return False
    if user.role == "admin":
        return True
    if user.role != "engineer":
        return False
    if actor.actor_id in {project.owner_id, project.primary_assignee_id}:
        return True
    if workspace is None:
        return False
    if actor.actor_id in {workspace.owner_id, workspace.primary_assignee_id}:
        return True
    return session.get(EngineeringWorkspaceMember, (workspace.id, actor.actor_id)) is not None


class SqlAlchemyCaptureAuthorizationPolicy:
    def __init__(self, session: Session) -> None:
        self.session = session

    def authorize(self, *, actor, operation: str, capture=None, project_id=None,
                  workspace_id=None, engineering_object_id=None) -> bool:
        if capture is not None:
            project_id = capture.project_id
            workspace_id = capture.workspace_id
            engineering_object_id = capture.engineering_object_id
            if capture.organization_id != actor.organization_id:
                return False
        project = self.session.query(Project).filter_by(
            id=project_id, organization_id=actor.organization_id
        ).first()
        if project is None:
            return False
        workspace = None
        if workspace_id is not None:
            workspace = self.session.query(EngineeringWorkspace).filter_by(
                id=workspace_id, project_id=project.id
            ).first()
            if workspace is None:
                return False
        if not _scope_access(self.session, actor, project, workspace):
            return False
        if engineering_object_id is not None:
            object_record = self.session.query(EngineeringObject).filter_by(
                id=engineering_object_id,
                organization_id=actor.organization_id,
                project_id=project.id,
                workspace_id=workspace_id,
            ).first()
            if object_record is None:
                return False
        if operation in {"withdraw", "supersede"}:
            user = self.session.get(User, actor.actor_id)
            return user.role == "admin" or (capture is not None and capture.creator_id == actor.actor_id)
        return True

    def require(self, **values) -> None:
        if not self.authorize(**values):
            raise EngineeringExperienceCaptureProtectedNotFound()

    def project_list_workspace_scope(self, *, actor, project_id: int):
        user = self.session.get(User, actor.actor_id)
        membership = self.session.get(
            UserOrganizationMembership, (actor.actor_id, actor.organization_id)
        )
        organization = self.session.get(Organization, actor.organization_id)
        project = self.session.query(Project).filter_by(
            id=project_id, organization_id=actor.organization_id
        ).first()
        if (
            user is None or not user.is_active or user.role not in {"admin", "engineer"}
            or membership is None or not membership.is_enabled
            or organization is None or not organization.is_active or project is None
        ):
            return ()
        if user.role == "admin" or actor.actor_id in {
            project.owner_id, project.primary_assignee_id
        }:
            return None
        rows = self.session.query(EngineeringWorkspace.id).outerjoin(
            EngineeringWorkspaceMember,
            (EngineeringWorkspaceMember.workspace_id == EngineeringWorkspace.id)
            & (EngineeringWorkspaceMember.user_id == actor.actor_id),
        ).filter(
            EngineeringWorkspace.project_id == project_id,
            (
                (EngineeringWorkspace.owner_id == actor.actor_id)
                | (EngineeringWorkspace.primary_assignee_id == actor.actor_id)
                | (EngineeringWorkspaceMember.user_id == actor.actor_id)
            ),
        ).all()
        return tuple(row[0] for row in rows)


class SqlAlchemyCaptureContextValidator:
    DISCIPLINE_MAP = {
        "electrical": "electrical",
        "instrumentation": "instrumentation",
        "control": "industrial_automation",
    }

    def __init__(self, session: Session) -> None:
        self.session = session

    def resolve_workspace(self, *, actor, workspace_id: int):
        workspace = self.session.query(EngineeringWorkspace).join(
            Project, Project.id == EngineeringWorkspace.project_id
        ).filter(
            EngineeringWorkspace.id == workspace_id,
            Project.organization_id == actor.organization_id,
        ).first()
        if workspace is None:
            raise EngineeringExperienceCaptureInvalidContext("Workspace is unavailable")
        return {
            "project_id": workspace.project_id,
            "workspace": workspace,
            "discipline": self.DISCIPLINE_MAP.get(workspace.discipline),
        }

    def validate(self, *, actor, project_id: int, workspace_id=None, engineering_object_id=None):
        project = self.session.query(Project).filter_by(
            id=project_id, organization_id=actor.organization_id
        ).first()
        if project is None:
            raise EngineeringExperienceCaptureInvalidContext("Project is unavailable")
        workspace = None
        discipline = None
        if workspace_id is not None:
            workspace = self.session.query(EngineeringWorkspace).filter_by(
                id=workspace_id, project_id=project_id
            ).first()
            if workspace is None:
                raise EngineeringExperienceCaptureInvalidContext("Workspace is unavailable")
            discipline = self.DISCIPLINE_MAP.get(workspace.discipline)
            if engineering_object_id is not None and discipline is None:
                raise EngineeringExperienceCaptureInvalidContext("Workspace cannot attach Engineering Objects")
        elif engineering_object_id is not None:
            raise EngineeringExperienceCaptureInvalidContext("Engineering Object requires Workspace")
        object_record = None
        if engineering_object_id is not None:
            object_record = self.session.query(EngineeringObject).filter_by(
                id=engineering_object_id,
                organization_id=actor.organization_id,
                project_id=project_id,
                workspace_id=workspace_id,
                discipline=discipline,
            ).first()
            if object_record is None:
                raise EngineeringExperienceCaptureInvalidContext("Engineering Object is unavailable")
        return {"project": project, "workspace": workspace, "discipline": discipline, "engineering_object": object_record}


class SqlAlchemyCaptureSupersessionValidator:
    def __init__(self, session: Session, repository: SqlAlchemyEngineeringExperienceCaptureRepository) -> None:
        self.session = session
        self.repository = repository

    def validate(self, *, original: EngineeringExperienceCapture, replacement_capture_id: UUID,
                 actor, authorization: SqlAlchemyCaptureAuthorizationPolicy):
        lock_key = int.from_bytes(
            hashlib.sha256(f"{actor.organization_id}:{original.project_id}:{replacement_capture_id}".encode()).digest()[:8],
            "big", signed=True,
        )
        self.session.query(func.pg_advisory_xact_lock(lock_key)).scalar()
        replacement = self.repository.get_scoped(replacement_capture_id, actor.organization_id)
        if replacement is None or not authorization.authorize(actor=actor, operation="read", capture=replacement):
            raise EngineeringExperienceCaptureProtectedNotFound()
        if replacement.id == original.id or replacement.lifecycle != "captured":
            raise EngineeringExperienceCaptureInvalidSupersession()
        context = ("project_id", "workspace_id", "discipline", "engineering_object_id")
        if any(getattr(original, item) != getattr(replacement, item) for item in context):
            raise EngineeringExperienceCaptureInvalidSupersession("Replacement context differs")
        if self.repository.replacement_is_used(replacement.id):
            raise EngineeringExperienceCaptureDuplicateSupersession()
        chain = self.repository.predecessor_chain(original.id, maximum_depth=21)
        if len(chain) > 20 or replacement.id in {item.id for item in chain}:
            raise EngineeringExperienceCaptureSupersessionCycle()
        return replacement


class SqlAlchemyCaptureAuditRecorder:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record(self, *, actor, capture_id, command_type, lifecycle, version,
               project_id, workspace_id=None, engineering_object_id=None,
               correlation_id=None, idempotency_id=None, previous_version=None,
               replacement_capture_id=None, **_values) -> None:
        self.session.add(AuditLog(
            user_id=actor.actor_id,
            action=command_type,
            entity="ENGINEERING_EXPERIENCE_CAPTURE",
            entity_uuid=capture_id,
            details=_json({"lifecycle": lifecycle, "version": version, "project_id": project_id,
                           "workspace_id": workspace_id,
                           "engineering_object_id": engineering_object_id,
                           "correlation_id": correlation_id,
                           "idempotency_id": idempotency_id,
                           "previous_version": previous_version,
                           "replacement_capture_id": replacement_capture_id}),
        ))


class SqlAlchemyCaptureDomainEventRecorder:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record(self, events: tuple[EngineeringExperienceCaptureEvent, ...]) -> None:
        for event in events:
            payload = {
                "organization_id": event.organization_id,
                "project_id": event.project_id,
                "workspace_id": event.workspace_id,
                "engineering_object_id": event.engineering_object_id,
                "source_kind": event.source_kind,
                "actor_id": event.actor_id,
                "correlation_id": event.correlation_id,
                **event.payload,
            }
            self.session.add(EngineeringExperienceCaptureOutbox(
                event_id=event.event_id, aggregate_id=event.capture_id,
                aggregate_version=event.aggregate_version, event_type=event.event_type,
                payload=_json(payload), occurred_at=event.occurred_at,
            ))


class SqlAlchemyCaptureIdempotencyStore:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.reservation = None

    def find(self, *, organization_id, actor_id, command_type, idempotency_id, request_fingerprint):
        row = self.session.query(EngineeringExperienceCaptureIdempotency).filter_by(
            organization_id=organization_id, actor_id=actor_id,
            command_type=command_type, idempotency_id=idempotency_id,
        ).first()
        if row is None:
            return None
        if row.request_fingerprint != request_fingerprint or row.status != "completed" or row.result is None:
            raise EngineeringExperienceCaptureIdempotencyConflict()
        value = row.result
        result = EngineeringExperienceCaptureResult(
            capture_id=UUID(value["capture_id"]), previous_version=value["previous_version"],
            version=value["version"], command_type=value["command_type"],
            correlation_id=UUID(value["correlation_id"]), events=(),
        )
        return EngineeringExperienceCaptureOutcome(result=result, authorized_state=value["authorized_state"])

    def reserve(self, **values) -> None:
        self.reservation = EngineeringExperienceCaptureIdempotency(**values, status="pending")
        self.session.add(self.reservation)
        self.session.flush()

    def record_result(self, result: EngineeringExperienceCaptureResult, authorized_state: Mapping) -> None:
        if self.reservation is None:
            raise RuntimeError("Idempotency reservation is required")
        self.reservation.status = "completed"
        self.reservation.aggregate_id = result.capture_id
        safe_fields = {
            key: value for key, value in authorized_state.items()
            if key not in {"original_content", "source_reference", "content", "rationale"}
        }
        self.reservation.result = _json({
            "capture_id": result.capture_id, "previous_version": result.previous_version,
            "version": result.version, "command_type": result.command_type,
            "correlation_id": result.correlation_id, "authorized_state": safe_fields,
        })


class UtcCaptureClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class SqlAlchemyEngineeringExperienceCaptureUnitOfWork:
    def __init__(self, session_factory) -> None:
        self.session_factory = session_factory

    def __enter__(self) -> Self:
        self.session = self.session_factory()
        self.captures = SqlAlchemyEngineeringExperienceCaptureRepository(self.session)
        self.authorization = SqlAlchemyCaptureAuthorizationPolicy(self.session)
        self.context = SqlAlchemyCaptureContextValidator(self.session)
        self.supersession = SqlAlchemyCaptureSupersessionValidator(self.session, self.captures)
        self.audit = SqlAlchemyCaptureAuditRecorder(self.session)
        self.domain_events = SqlAlchemyCaptureDomainEventRecorder(self.session)
        self.idempotency = SqlAlchemyCaptureIdempotencyStore(self.session)
        self.clock = UtcCaptureClock()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if exc_type is not None:
            self.rollback()
        self.session.close()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
