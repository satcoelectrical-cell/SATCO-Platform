"""Same-Session PATCH-034 Organizational Memory transaction boundary."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Self
from uuid import UUID

from sqlalchemy import null
from sqlalchemy.orm import Session

from app.enums.organizational_memory import MemoryOperation
from app.models.audit_log import AuditLog
from app.models.engineering_workspace import EngineeringWorkspace, EngineeringWorkspaceMember
from app.models.organization import Organization, UserOrganizationMembership
from app.models.project import Project
from app.models.user import User
from app.models.organizational_memory_command import (
    MemoryAuditRecord, MemoryFinalRecheckRequest, MemoryIdempotencyCompleted,
    MemoryIdempotencyKey, MemoryIdempotencyMiss, MemoryIdempotencyPending,
    MemoryOutboxRecord, MemoryRejectionAuditRecord,
    StoredAdmissionResultV1, StoredSuccessorResultV1,
    StoredSupersessionResultV1, StoredWithdrawalResultV1,
    canonical_json, validate_stored_result,
)
from app.exceptions.organizational_memory import OrganizationalMemoryVersionConflict
from app.repositories.organizational_memory_repository import (
    OrganizationalMemoryIdempotencyRecord, OrganizationalMemoryOutboxRecord,
    OrganizationalMemoryRecord,
    SqlAlchemyOrganizationalMemoryRepository,
)


class MemoryAuthorizationDenied(Exception):
    """Internal closed denial translated only by the application service."""


def _json(value):
    import json
    return json.loads(canonical_json(value))


class SqlAlchemyMemoryAuthorizationPolicy:
    def __init__(self, session: Session): self.session = session

    def require(self, request, source_owner_id=None) -> None:
        if request.operation not in {
            MemoryOperation.ADMIT, MemoryOperation.GET_ACTIVE,
            MemoryOperation.LIST_ACTIVE, MemoryOperation.INSPECT_HISTORY,
            MemoryOperation.CREATE_SUCCESSOR, MemoryOperation.WITHDRAW,
            MemoryOperation.SUPERSEDE,
        }:
            raise MemoryAuthorizationDenied()
        if request.actor.organization_id != request.scope.organization_id:
            raise MemoryAuthorizationDenied()
        user = self.session.get(User, request.actor.actor_id, with_for_update=True)
        organization = self.session.get(Organization, request.scope.organization_id, with_for_update=True)
        membership = self.session.get(
            UserOrganizationMembership,
            (request.actor.actor_id, request.scope.organization_id),
            with_for_update=True,
        )
        workspace = self.session.get(EngineeringWorkspace, request.scope.workspace_id, with_for_update=True)
        project = None if workspace is None else self.session.get(Project, workspace.project_id, with_for_update=True)
        valid = (
            user is not None and user.is_active and user.role in {"admin", "engineer"}
            and organization is not None and organization.is_active
            and membership is not None and membership.is_enabled and membership.is_selected
            and workspace is not None and getattr(workspace, "status", None) == "active"
            and project is not None and project.organization_id == request.scope.organization_id
            and (request.scope.project_id is None or request.scope.project_id == project.id)
        )
        if not valid:
            raise MemoryAuthorizationDenied()
        is_admin = user.role == "admin"
        assigned_scope = request.actor.actor_id in {
            project.owner_id, project.primary_assignee_id,
            workspace.owner_id, workspace.primary_assignee_id,
        }
        workspace_member = self.session.get(
            EngineeringWorkspaceMember,
            (workspace.id, request.actor.actor_id), with_for_update=True,
        )
        has_read_scope = is_admin or assigned_scope or workspace_member is not None
        is_read = request.operation in {
            MemoryOperation.GET_ACTIVE, MemoryOperation.LIST_ACTIVE,
            MemoryOperation.INSPECT_HISTORY,
        }
        if (not has_read_scope if is_read else not (is_admin or assigned_scope)) or (
            request.audience_actor_ids
            and request.actor.actor_id not in request.audience_actor_ids
            and not is_admin
        ):
            raise MemoryAuthorizationDenied()
        if (
            source_owner_id is not None and not is_admin
            and request.operation in {
                MemoryOperation.ADMIT, MemoryOperation.CREATE_SUCCESSOR,
                MemoryOperation.WITHDRAW, MemoryOperation.SUPERSEDE,
            }
            and source_owner_id != request.actor.actor_id
        ):
            raise MemoryAuthorizationDenied()
        if not is_read:
            for audience_actor_id in request.audience_actor_ids:
                if not self._human_visible(
                    audience_actor_id, request.scope.organization_id,
                    workspace, project,
                ):
                    raise MemoryAuthorizationDenied()
        predecessor = self._memory(request.predecessor_memory_id, request.scope.organization_id)
        subject = self._memory(request.memory_id, request.scope.organization_id)
        replacement = self._memory(request.replacement_memory_id, request.scope.organization_id)
        if request.operation in {MemoryOperation.GET_ACTIVE, MemoryOperation.INSPECT_HISTORY} and subject is None:
            raise MemoryAuthorizationDenied()
        if request.operation is MemoryOperation.INSPECT_HISTORY and (
            not is_admin and (
                subject.admitted_by_id != request.actor.actor_id
                or not assigned_scope
            )
        ):
            raise MemoryAuthorizationDenied()
        if request.operation is MemoryOperation.INSPECT_HISTORY:
            historical_humans = [subject.admitted_by_id]
            if subject.withdrawn_by_id is not None:
                historical_humans.append(subject.withdrawn_by_id)
            if subject.superseded_by_id is not None:
                historical_humans.append(subject.superseded_by_id)
            if any(not self._human_visible(
                actor_id, request.scope.organization_id, workspace, project,
            ) for actor_id in historical_humans):
                raise MemoryAuthorizationDenied()
        if request.operation is MemoryOperation.CREATE_SUCCESSOR and (
            predecessor is None or (not is_admin and predecessor.admitted_by_id != request.actor.actor_id)
        ):
            raise MemoryAuthorizationDenied()
        if request.operation is MemoryOperation.WITHDRAW and (
            subject is None or (not is_admin and subject.admitted_by_id != request.actor.actor_id)
        ):
            raise MemoryAuthorizationDenied()
        if request.operation is MemoryOperation.SUPERSEDE and (
            subject is None or replacement is None
            or (not is_admin and subject.admitted_by_id != request.actor.actor_id)
        ):
            raise MemoryAuthorizationDenied()

    def _memory(self, memory_id, organization_id):
        if memory_id is None:
            return None
        return self.session.query(OrganizationalMemoryRecord).filter_by(
            id=memory_id, organization_id=organization_id,
        ).with_for_update().first()

    def _human_visible(self, actor_id, organization_id, workspace, project):
        user = self.session.get(User, actor_id, with_for_update=True)
        membership = self.session.get(
            UserOrganizationMembership, (actor_id, organization_id),
            with_for_update=True,
        )
        has_scope = actor_id in {
            project.owner_id, project.primary_assignee_id,
            workspace.owner_id, workspace.primary_assignee_id,
        } or self.session.get(
            EngineeringWorkspaceMember, (workspace.id, actor_id),
            with_for_update=True,
        ) is not None
        return bool(
            user is not None and user.is_active
            and membership is not None and membership.is_enabled
            and has_scope
        )


class SqlAlchemyMemoryFinalRecheckPolicy:
    def __init__(self, session, authorization, memories):
        self.session = session; self.authorization = authorization; self.memories = memories

    def require_current(self, request: MemoryFinalRecheckRequest, source_owner_id=None) -> None:
        self.authorization.require(request.authorization, source_owner_id)
        resolved = []
        values = (
            (request.authorization.memory_id, request.expected_memory_version),
            (request.authorization.predecessor_memory_id, request.expected_predecessor_version),
            (request.authorization.replacement_memory_id, request.expected_replacement_version),
        )
        for identity, expected in values:
            if identity is None: continue
            memory = self.memories.lock_scoped(identity, request.authorization.scope.organization_id)
            if memory is None:
                raise MemoryAuthorizationDenied()
            if expected is not None and memory.version != expected:
                raise OrganizationalMemoryVersionConflict()
            resolved.append(memory)
        if (
            request.expected_source_snapshot_digest is not None and resolved
            and request.authorization.operation in {
                MemoryOperation.WITHDRAW, MemoryOperation.SUPERSEDE,
            }
        ):
            if resolved[0].source.accepted_snapshot_digest != request.expected_source_snapshot_digest:
                raise MemoryAuthorizationDenied()


class SqlAlchemyMemoryAuditRecorder:
    def __init__(self, session): self.session = session
    def record(self, record: MemoryAuditRecord) -> None:
        details = {
            "outcome": "succeeded",
            "organization_id": str(record.organization_id),
            "previous_version": record.previous_version,
            "result_version": record.result_version,
            "standing": record.standing.value,
            "source_report_id": str(record.source_report_id),
            "source_accepted_version": record.source_accepted_version,
            "command_id": str(record.command_id),
            "correlation_id": str(record.correlation_id),
            "idempotency_id": str(record.idempotency_id),
            "provenance_entry_count": record.provenance_entry_count,
        }
        if record.predecessor_memory_id is not None:
            details["predecessor_memory_id"] = str(record.predecessor_memory_id)
        if record.replacement_memory_id is not None:
            details["replacement_memory_id"] = str(record.replacement_memory_id)
        self.session.add(AuditLog(
            user_id=record.actor_id, action=record.operation.value,
            entity="ORGANIZATIONAL_MEMORY", entity_uuid=record.memory_id,
            details=details, created_at=record.occurred_at,
        ))


class SqlAlchemyMemoryDomainEventRecorder:
    def __init__(self, session): self.session = session
    def record(self, records: tuple[MemoryOutboxRecord, ...]) -> None:
        for record in records:
            self.session.add(OrganizationalMemoryOutboxRecord(
                event_id=record.event_id, memory_id=record.memory_id,
                aggregate_version=record.aggregate_version,
                event_type=record.event_type.value,
                payload_schema_version=record.payload_schema_version,
                payload=_json(record.payload), occurred_at=record.occurred_at,
                created_at=record.created_at,
            ))


_STORED_TYPES = {
    "admit.v1": StoredAdmissionResultV1,
    "withdraw.v1": StoredWithdrawalResultV1,
    "create_successor.v1": StoredSuccessorResultV1,
    "supersede.v1": StoredSupersessionResultV1,
}


class SqlAlchemyMemoryIdempotencyStore:
    def __init__(self, session, clock): self.session = session; self.clock = clock
    def find(self, key: MemoryIdempotencyKey):
        row = self.session.get(OrganizationalMemoryIdempotencyRecord, (
            key.organization_id, key.actor_id, key.operation, key.idempotency_id,
        ), with_for_update=True)
        if row is None: return MemoryIdempotencyMiss()
        if row.status == "pending": return MemoryIdempotencyPending()
        payload = dict(row.safe_result); result_type = payload.get("result_type")
        for identity in (
            "memory_id", "source_report_id", "predecessor_memory_id",
            "replacement_memory_id",
        ):
            if isinstance(payload.get(identity), str):
                payload[identity] = UUID(payload[identity])
        for timestamp in ("withdrawn_at", "superseded_at"):
            if isinstance(payload.get(timestamp), str):
                payload[timestamp] = datetime.fromisoformat(payload[timestamp].replace("Z", "+00:00"))
        result = _STORED_TYPES[result_type](**payload)
        return MemoryIdempotencyCompleted("completed", row.request_fingerprint, 1, result)
    def reserve(self, key, request_fingerprint):
        now = self.clock.now()
        self.session.add(OrganizationalMemoryIdempotencyRecord(
            organization_id=key.organization_id, actor_id=key.actor_id,
            operation=key.operation, idempotency_id=key.idempotency_id,
            request_fingerprint=request_fingerprint, status="pending",
            result_schema_version=1, safe_result=null(),
            created_at=now, updated_at=now, completed_at=None,
        )); self.session.flush()
    def record_result(self, key, request_fingerprint, result):
        validate_stored_result(key.operation, result)
        row = self.session.get(OrganizationalMemoryIdempotencyRecord, (
            key.organization_id, key.actor_id, key.operation, key.idempotency_id,
        ), with_for_update=True)
        if row is None or row.request_fingerprint != request_fingerprint:
            raise MemoryAuthorizationDenied()
        now = self.clock.now(); row.status = "completed"; row.safe_result = _json(result)
        row.updated_at = now; row.completed_at = now


class SqlAlchemyMemoryRejectionAuditRecorder:
    def __init__(self, session_factory): self.session_factory = session_factory; self.permitted = False
    def permit_after_authoritative_rollback(self): self.permitted = True
    def record_rejection(self, record: MemoryRejectionAuditRecord):
        if not self.permitted: raise RuntimeError("rollback required before rejection Audit")
        try:
            with self.session_factory() as session:
                session.add(AuditLog(
                    user_id=record.actor_id, action=record.operation.value,
                    entity="ORGANIZATIONAL_MEMORY",
                    entity_uuid=record.memory_id,
                    details={"outcome": "rejected", "reason": record.reason.value,
                             "organization_id": str(record.organization_id),
                             "command_id": str(record.command_id),
                             "correlation_id": str(record.correlation_id)},
                    created_at=record.occurred_at,
                )); session.commit()
        finally: self.permitted = False


class SystemMemoryClock:
    def now(self): return datetime.now(timezone.utc)


class SqlAlchemyOrganizationalMemoryUnitOfWork:
    def __init__(self, session_factory, rejection_session_factory=None, clock=None):
        self.session_factory = session_factory; self.clock = clock or SystemMemoryClock()
        self.rejection_audit = SqlAlchemyMemoryRejectionAuditRecorder(
            rejection_session_factory or session_factory,
        )
    def __enter__(self) -> Self:
        self.session = self.session_factory()
        self.memories = SqlAlchemyOrganizationalMemoryRepository(self.session)
        self.authorization = SqlAlchemyMemoryAuthorizationPolicy(self.session)
        self.final_recheck = SqlAlchemyMemoryFinalRecheckPolicy(
            self.session, self.authorization, self.memories,
        )
        self.audit = SqlAlchemyMemoryAuditRecorder(self.session)
        self.domain_events = SqlAlchemyMemoryDomainEventRecorder(self.session)
        self.idempotency = SqlAlchemyMemoryIdempotencyStore(self.session, self.clock)
        return self
    def __exit__(self, exc_type, *_):
        if exc_type is not None: self.rollback()
        self.session.close()
    def flush(self): self.session.flush()
    def commit(self): self.session.commit()
    def rollback(self):
        self.session.rollback(); self.rejection_audit.permit_after_authoritative_rollback()
