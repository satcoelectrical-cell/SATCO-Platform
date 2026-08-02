"""Framework-independent PATCH-026 relationship command contracts."""

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer
from sqlalchemy import JSON, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.sql import func

from app.core.database import Base
from app.enums import RelationshipFamily
from app.enums import EngineeringRelationshipLifecycle as RelationshipLifecycle
from app.enums import RelationshipType
from app.enums import validate_relationship_pair


Scalar = str | int | bool | UUID | datetime | None


class EngineeringRelationshipCommandError(ValueError):
    """Base rejection for an EngineeringRelationship command."""


class EngineeringRelationshipVersionMismatch(
    EngineeringRelationshipCommandError
):
    """A mutation targeted a stale aggregate version."""


class EngineeringRelationshipTransitionRejected(
    EngineeringRelationshipCommandError
):
    """A lifecycle or authority transition violated the approved contract."""


class EngineeringRelationshipInvariantViolation(
    EngineeringRelationshipCommandError
):
    """Creation or mutation violated an aggregate invariant."""


class EngineeringRelationshipNoOp(EngineeringRelationshipCommandError):
    """A command would not change authoritative aggregate state."""


@dataclass(frozen=True, slots=True)
class AuthenticatedRelationshipActor:
    """Trusted accountable Human supplied by authentication."""

    actor_id: int
    organization_id: UUID

    def __post_init__(self) -> None:
        if isinstance(self.actor_id, bool) or self.actor_id < 1:
            raise ValueError("actor_id must be a positive integer")


@dataclass(frozen=True, slots=True)
class RelationshipAuthorizationContext:
    """Opaque operation-specific authorization context."""

    operation: str
    scope: Mapping[str, Scalar]

    def __post_init__(self) -> None:
        if not self.operation.strip():
            raise ValueError("authorization operation must not be empty")


@dataclass(frozen=True, slots=True)
class RelationshipCommandMetadata:
    """Trusted metadata shared by all relationship commands."""

    actor: AuthenticatedRelationshipActor
    authorization: RelationshipAuthorizationContext
    rationale: str
    correlation_id: UUID
    idempotency_id: UUID
    command_id: UUID
    evidence_references: tuple[UUID, ...] = ()

    def __post_init__(self) -> None:
        rationale = self.rationale.strip()
        if not rationale:
            raise ValueError("rationale must not be empty")
        object.__setattr__(self, "rationale", rationale)
        if len(self.evidence_references) != len(set(self.evidence_references)):
            raise ValueError("evidence references must be unique")


@dataclass(frozen=True, slots=True)
class RelationshipValidationResult:
    """Trusted reference/policy facts required by aggregate creation."""

    source_organization_id: UUID
    target_organization_id: UUID
    source_project_id: int
    target_project_id: int
    source_workspace_id: int
    target_workspace_id: int
    active_duplicate_exists: bool = False
    prohibited_cycle_exists: bool = False

    def __post_init__(self) -> None:
        for field_name in (
            "source_project_id", "target_project_id",
            "source_workspace_id", "target_workspace_id",
        ):
            value = getattr(self, field_name)
            if isinstance(value, bool) or value < 1:
                raise ValueError(f"{field_name} must be a positive integer")


@dataclass(frozen=True, slots=True)
class CreateEngineeringRelationship:
    """Create one validated directional relationship aggregate."""

    metadata: RelationshipCommandMetadata
    relationship_family: RelationshipFamily
    relationship_type: RelationshipType
    source_object_id: UUID
    target_object_id: UUID
    organization_id: UUID
    project_id: int
    workspace_id: int
    creator_id: int
    steward_id: int
    validation: RelationshipValidationResult

    def __post_init__(self) -> None:
        validate_relationship_pair(
            self.relationship_family, self.relationship_type
        )
        for field_name in (
            "project_id", "workspace_id", "creator_id", "steward_id"
        ):
            value = getattr(self, field_name)
            if isinstance(value, bool) or value < 1:
                raise ValueError(f"{field_name} must be a positive integer")


@dataclass(frozen=True, slots=True)
class EngineeringRelationshipMutation:
    """Common optimistic command envelope with canonical vocabulary pair."""

    metadata: RelationshipCommandMetadata
    relationship_id: UUID
    relationship_family: RelationshipFamily
    relationship_type: RelationshipType
    expected_version: int

    def __post_init__(self) -> None:
        validate_relationship_pair(
            self.relationship_family, self.relationship_type
        )
        if isinstance(self.expected_version, bool) or self.expected_version < 1:
            raise ValueError("expected_version must be a positive integer")


@dataclass(frozen=True, slots=True)
class SubmitEngineeringRelationshipForReview(EngineeringRelationshipMutation):
    """Submit a draft relationship for accountable review."""


@dataclass(frozen=True, slots=True)
class ReviewEngineeringRelationship(EngineeringRelationshipMutation):
    """Record successful Human review and its Evidence."""


@dataclass(frozen=True, slots=True)
class ApproveEngineeringRelationship(EngineeringRelationshipMutation):
    """Record accountable Human approval."""


@dataclass(frozen=True, slots=True)
class DisputeEngineeringRelationship(EngineeringRelationshipMutation):
    """Dispute an approved relationship."""


@dataclass(frozen=True, slots=True)
class RejectEngineeringRelationship(EngineeringRelationshipMutation):
    """Reject a proposed, reviewed, or disputed relationship."""


@dataclass(frozen=True, slots=True)
class TransitionEngineeringRelationshipLifecycle(
    EngineeringRelationshipMutation
):
    """Apply one approved lifecycle transition."""

    lifecycle: RelationshipLifecycle
    replacement_relationship_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class TransferEngineeringRelationshipSteward(
    EngineeringRelationshipMutation
):
    """Transfer stewardship to one validated active Human."""

    steward_id: int = 0

    def __post_init__(self) -> None:
        EngineeringRelationshipMutation.__post_init__(self)
        if isinstance(self.steward_id, bool) or self.steward_id < 1:
            raise ValueError("steward_id must be a positive integer")


@dataclass(frozen=True, slots=True)
class EngineeringRelationshipDomainEvent:
    """Immutable fact produced by one successful aggregate command."""

    event_id: UUID
    event_type: str
    schema_version: int
    relationship_id: UUID
    aggregate_version: int
    occurred_at: datetime
    actor_id: int
    correlation_id: UUID
    causation_id: UUID
    organization_id: UUID
    project_id: int
    workspace_id: int
    relationship_family: RelationshipFamily
    relationship_type: RelationshipType
    payload: Mapping[str, Scalar]


@dataclass(frozen=True, slots=True)
class EngineeringRelationshipCommandResult:
    """State-change result returned by an accepted aggregate command."""

    relationship_id: UUID
    previous_version: int | None
    version: int
    command_type: str
    correlation_id: UUID
    events: tuple[EngineeringRelationshipDomainEvent, ...]


@dataclass(frozen=True, slots=True)
class EngineeringRelationshipIdempotencyOutcome:
    """Committed command result and its authorized scalar snapshot."""

    result: EngineeringRelationshipCommandResult
    authorized_state: Mapping[str, object]


class EngineeringRelationshipOutbox(Base):
    """Durable relationship Domain Event outbox row."""

    __tablename__ = "engineering_relationship_outbox"
    __table_args__ = (
        UniqueConstraint(
            "event_id", name="uq_engineering_relationship_outbox_event"
        ),
        CheckConstraint(
            "aggregate_version >= 1",
            name="ck_engineering_relationship_outbox_version",
        ),
        Index(
            "ix_engineering_relationship_outbox_unpublished",
            "published_at", "occurred_at",
        ),
    )

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_id = Column(PostgreSQLUUID(as_uuid=True), nullable=False)
    aggregate_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("engineering_relationships.id", ondelete="RESTRICT"),
        nullable=False,
    )
    aggregate_version = Column(Integer, nullable=False)
    event_type = Column(String(96), nullable=False)
    schema_version = Column(Integer, nullable=False)
    payload = Column(JSON, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class EngineeringRelationshipIdempotency(Base):
    """Durable relationship command reservation and replay result."""

    __tablename__ = "engineering_relationship_idempotency"
    __table_args__ = (
        UniqueConstraint(
            "actor_id", "command_type", "idempotency_id",
            name="uq_engineering_relationship_idempotency_scope",
        ),
        CheckConstraint(
            "status IN ('pending', 'completed')",
            name="ck_engineering_relationship_idempotency_status",
        ),
        Index(
            "ix_engineering_relationship_idempotency_lookup",
            "actor_id", "command_type", "idempotency_id",
        ),
    )

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    actor_id = Column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    command_type = Column(String(80), nullable=False)
    idempotency_id = Column(PostgreSQLUUID(as_uuid=True), nullable=False)
    request_fingerprint = Column(String(64), nullable=False)
    status = Column(String(16), nullable=False, server_default="pending")
    aggregate_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("engineering_relationships.id", ondelete="RESTRICT"),
        nullable=True,
    )
    result = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now(),
    )
