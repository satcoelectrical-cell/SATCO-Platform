"""PATCH-026 policy adapters and atomic SQLAlchemy Unit of Work."""

from datetime import datetime, timezone
from typing import Mapping, Self
from uuid import UUID

from sqlalchemy.orm import Session

from app.enums import ACYCLIC_RELATIONSHIP_PAIRS, RelationshipFamily, RelationshipType
from app.exceptions.engineering_relationship import (
    EngineeringRelationshipIdempotencyConflict,
    EngineeringRelationshipValidationError,
)
from app.exceptions.evidence import EvidenceValidationError
from app.models.audit_log import AuditLog
from app.models.engineering_object import EngineeringObject
from app.models.engineering_relationship import EngineeringRelationship
from app.models.engineering_relationship_command import (
    AuthenticatedRelationshipActor,
    EngineeringRelationshipCommandResult,
    EngineeringRelationshipDomainEvent,
    EngineeringRelationshipIdempotency,
    EngineeringRelationshipIdempotencyOutcome,
    EngineeringRelationshipOutbox,
    RelationshipValidationResult,
)
from app.models.engineering_workspace import (
    EngineeringWorkspace, EngineeringWorkspaceMember,
)
from app.models.evidence import Evidence
from app.models.project import Project
from app.models.user import User
from app.repositories.engineering_relationship_repository import (
    SqlAlchemyEngineeringRelationshipRepository,
)
from app.repositories.evidence_unit_of_work import SqlAlchemyEvidenceValidator


def _json(value):
    if isinstance(value, (UUID, datetime)):
        return value.isoformat() if isinstance(value, datetime) else str(value)
    if isinstance(value, Mapping):
        return {key: _json(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json(item) for item in value]
    return getattr(value, "value", value)


def _workspace_access(session: Session, actor_id: int, workspace_id: int) -> bool:
    user = session.get(User, actor_id)
    workspace = session.get(EngineeringWorkspace, workspace_id)
    if user is None or not user.is_active or workspace is None:
        return False
    project = session.get(Project, workspace.project_id)
    if user.role == "admin" or actor_id in {
        workspace.owner_id, workspace.primary_assignee_id,
    } or (project is not None and actor_id == project.owner_id):
        return True
    return session.get(
        EngineeringWorkspaceMember, (workspace_id, actor_id)
    ) is not None


class SqlAlchemyRelationshipAuthorizationPolicy:
    """Deny-by-default intersection of endpoint, Evidence, and Workspace visibility."""

    def __init__(self, session: Session):
        self.session = session

    def authorize(self, *, actor, context, current_state, target_state) -> bool:
        source_id = (
            current_state.source_object_id if current_state is not None
            else target_state.get("source_object_id")
        )
        target_id = (
            current_state.target_object_id if current_state is not None
            else target_state.get("target_object_id")
        )
        if source_id is None or target_id is None:
            return False
        endpoints = self.session.query(EngineeringObject).filter(
            EngineeringObject.id.in_((source_id, target_id)),
            EngineeringObject.organization_id == actor.organization_id,
        ).all()
        if len(endpoints) != 2:
            return False
        if not all(
            _workspace_access(self.session, actor.actor_id, item.workspace_id)
            for item in endpoints
        ):
            return False
        evidence_ids = (
            tuple(UUID(value) for value in current_state.evidence_references)
            if current_state is not None else
            tuple(target_state.get("evidence_references", ()))
        )
        if evidence_ids:
            evidence = self.session.query(Evidence).filter(
                Evidence.id.in_(evidence_ids),
                Evidence.organization_id == actor.organization_id,
            ).all()
            if len(evidence) != len(set(evidence_ids)):
                return False
            for item in evidence:
                if item.project_id is not None and item.project_id != endpoints[0].project_id:
                    return False
                if item.workspace_id is not None and not _workspace_access(
                    self.session, actor.actor_id, item.workspace_id
                ):
                    return False
        return True


class SqlAlchemyRelationshipValidator:
    def __init__(self, session: Session,
                 repository: SqlAlchemyEngineeringRelationshipRepository,
                 evidence_validator=None):
        self.session = session
        self.repository = repository
        self.evidence_validator = evidence_validator or SqlAlchemyEvidenceValidator(
            session
        )

    def validate_creation(self, *, actor, source_object_id, target_object_id,
                          relationship_family, relationship_type, steward_id,
                          evidence_references):
        endpoints = self.session.query(EngineeringObject).filter(
            EngineeringObject.id.in_((source_object_id, target_object_id)),
            EngineeringObject.organization_id == actor.organization_id,
        ).all()
        by_id = {item.id: item for item in endpoints}
        if source_object_id not in by_id or target_object_id not in by_id:
            raise EngineeringRelationshipValidationError("Endpoint is unavailable")
        source, target = by_id[source_object_id], by_id[target_object_id]
        if source.project_id != target.project_id:
            raise EngineeringRelationshipValidationError(
                "Cross-Project relationships are prohibited"
            )
        if not all(_workspace_access(self.session, actor.actor_id, item.workspace_id)
                   for item in (source, target)):
            raise EngineeringRelationshipValidationError("Endpoint is unavailable")
        family = RelationshipFamily(relationship_family)
        if source.workspace_id != target.workspace_id and family.value == "structural":
            raise EngineeringRelationshipValidationError(
                "Structural relationships require one Workspace"
            )
        self._validate_responsible(
            actor, steward_id or actor.actor_id,
            (source.workspace_id, target.workspace_id),
        )
        self._validate_evidence(
            actor, evidence_references, source.project_id,
            (source.workspace_id, target.workspace_id),
        )
        identity = dict(
            organization_id=actor.organization_id, project_id=source.project_id,
            workspace_id=source.workspace_id, source_object_id=source.id,
            target_object_id=target.id, relationship_family=family,
            relationship_type=RelationshipType(relationship_type),
        )
        duplicate = self.repository.active_duplicate_exists(**identity)
        pair = (family, RelationshipType(relationship_type))
        cycle = self.repository.creates_cycle(
            organization_id=actor.organization_id,
            project_id=source.project_id, source_object_id=source.id,
            target_object_id=target.id, relationship_family=family,
            relationship_type=RelationshipType(relationship_type),
        ) if pair in ACYCLIC_RELATIONSHIP_PAIRS else False
        return RelationshipValidationResult(
            source_organization_id=source.organization_id,
            target_organization_id=target.organization_id,
            source_project_id=source.project_id,
            target_project_id=target.project_id,
            source_workspace_id=source.workspace_id,
            target_workspace_id=target.workspace_id,
            active_duplicate_exists=duplicate,
            prohibited_cycle_exists=cycle,
        )

    def validate_mutation(self, *, actor, relationship_id, references):
        relationship = self.session.query(EngineeringRelationship).filter_by(
            id=relationship_id, organization_id=actor.organization_id
        ).first()
        if relationship is None:
            raise EngineeringRelationshipValidationError(
                "Relationship is unavailable"
            )
        workspace_ids = self.session.query(EngineeringObject.workspace_id).filter(
            EngineeringObject.id.in_((relationship.source_object_id,
                                      relationship.target_object_id))
        ).all()
        workspace_ids = tuple(value[0] for value in workspace_ids)
        self._validate_evidence(
            actor, tuple(references.get("evidence_references", ())),
            relationship.project_id, workspace_ids,
        )
        steward_id = references.get("steward_id")
        if steward_id is not None:
            self._validate_responsible(actor, steward_id, workspace_ids)
        replacement_id = references.get("replacement_relationship_id")
        if replacement_id is not None:
            replacement = self.session.query(EngineeringRelationship).filter_by(
                id=replacement_id, organization_id=actor.organization_id,
                project_id=relationship.project_id,
                relationship_family=relationship.relationship_family,
                relationship_type=relationship.relationship_type,
                lifecycle="current",
            ).first()
            if replacement is None:
                raise EngineeringRelationshipValidationError(
                    "Replacement relationship is incompatible"
                )

    def _validate_evidence(self, actor, references, project_id, workspace_ids):
        for evidence_id in references:
            try:
                item = self.evidence_validator.validate_reference(
                    actor=actor, evidence_id=evidence_id,
                    project_id=project_id, workspace_ids=workspace_ids,
                )
            except EvidenceValidationError as exc:
                raise EngineeringRelationshipValidationError(
                    "Evidence is unavailable or unacceptable"
                ) from exc
            if item.workspace_id is not None and not _workspace_access(
                self.session, actor.actor_id, item.workspace_id
            ):
                raise EngineeringRelationshipValidationError("Evidence is unavailable")

    def _validate_responsible(self, actor, user_id, workspace_ids):
        user = self.session.get(User, user_id)
        if user is None or not user.is_active or not all(
            _workspace_access(self.session, user_id, workspace_id)
            for workspace_id in set(workspace_ids)
        ):
            raise EngineeringRelationshipValidationError(
                "Responsible Human is unavailable"
            )


class SqlAlchemyRelationshipAuditRecorder:
    def __init__(self, session): self.session = session
    def record(self, **values):
        actor = values.pop("actor"); relationship_id = values.pop("relationship_id")
        command_type = values.pop("command_type")
        self.session.add(AuditLog(
            user_id=actor.actor_id, action=command_type,
            entity="ENGINEERING_RELATIONSHIP", entity_uuid=relationship_id,
            details=_json(values),
        ))


class SqlAlchemyRelationshipEventRecorder:
    def __init__(self, session): self.session = session
    def record(self, events: tuple[EngineeringRelationshipDomainEvent, ...]):
        for event in events:
            self.session.add(EngineeringRelationshipOutbox(
                event_id=event.event_id, aggregate_id=event.relationship_id,
                aggregate_version=event.aggregate_version,
                event_type=event.event_type, schema_version=event.schema_version,
                payload=_json({
                    "actor_id": event.actor_id,
                    "correlation_id": event.correlation_id,
                    "causation_id": event.causation_id,
                    "organization_id": event.organization_id,
                    "project_id": event.project_id,
                    "workspace_id": event.workspace_id,
                    "relationship_family": event.relationship_family,
                    "relationship_type": event.relationship_type,
                    "payload": event.payload,
                }), occurred_at=event.occurred_at,
            ))


class SqlAlchemyRelationshipIdempotencyStore:
    def __init__(self, session): self.session = session; self.reservation = None
    def find(self, *, actor_id, command_type, idempotency_id,
             request_fingerprint):
        row = self.session.query(EngineeringRelationshipIdempotency).filter_by(
            actor_id=actor_id, command_type=command_type,
            idempotency_id=idempotency_id,
        ).first()
        if row is None: return None
        if row.request_fingerprint != request_fingerprint or row.status != "completed" or row.result is None:
            raise EngineeringRelationshipIdempotencyConflict()
        data = row.result
        return EngineeringRelationshipIdempotencyOutcome(
            EngineeringRelationshipCommandResult(
                relationship_id=UUID(data["relationship_id"]),
                previous_version=data["previous_version"], version=data["version"],
                command_type=data["command_type"],
                correlation_id=UUID(data["correlation_id"]), events=(),
            ), data["authorized_state"],
        )
    def reserve(self, **values):
        self.reservation = EngineeringRelationshipIdempotency(
            **values, status="pending"
        ); self.session.add(self.reservation); self.session.flush()
    def record_result(self, result, authorized_state):
        if self.reservation is None: raise RuntimeError("Idempotency reservation required")
        self.reservation.status = "completed"
        self.reservation.aggregate_id = result.relationship_id
        self.reservation.result = _json({
            "relationship_id": result.relationship_id,
            "previous_version": result.previous_version,
            "version": result.version, "command_type": result.command_type,
            "correlation_id": result.correlation_id,
            "authorized_state": authorized_state,
        })


class UtcRelationshipClock:
    def now(self): return datetime.now(timezone.utc)


class SqlAlchemyEngineeringRelationshipUnitOfWork:
    def __init__(self, session_factory): self.session_factory = session_factory
    def __enter__(self) -> Self:
        self.session = self.session_factory()
        self.engineering_relationships = SqlAlchemyEngineeringRelationshipRepository(self.session)
        self.validator = SqlAlchemyRelationshipValidator(
            self.session, self.engineering_relationships,
            SqlAlchemyEvidenceValidator(self.session),
        )
        self.audit = SqlAlchemyRelationshipAuditRecorder(self.session)
        self.domain_events = SqlAlchemyRelationshipEventRecorder(self.session)
        self.idempotency = SqlAlchemyRelationshipIdempotencyStore(self.session)
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None: self.rollback()
        self.session.close()
    def commit(self): self.session.commit()
    def rollback(self): self.session.rollback()
