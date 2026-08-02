"""Domain command and result contracts for ``EngineeringObject``.

These contracts are independent of transport and persistence frameworks. The
application layer supplies authenticated and authorized command context before
invoking the aggregate.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping
from uuid import UUID
from uuid import uuid4

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer
from sqlalchemy import JSON, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.sql import func

from app.core.database import Base
from app.enums import EngineeringAuthorityStanding
from app.enums import EngineeringDiscipline
from app.enums import EngineeringLifecycle
from app.enums import EngineeringObjectFamily
from app.enums import EngineeringObjectType


Scalar = str | int | bool | UUID | datetime | None


class EngineeringObjectCommandError(ValueError):
    """Base rejection raised by an EngineeringObject command operation."""


class EngineeringObjectVersionMismatch(EngineeringObjectCommandError):
    """Raised when a command does not target the current aggregate version."""


class EngineeringObjectTransitionRejected(EngineeringObjectCommandError):
    """Raised when a requested lifecycle or authority transition is invalid."""


class EngineeringObjectNoOp(EngineeringObjectCommandError):
    """Raised when a command would not change authoritative aggregate state."""


@dataclass(frozen=True, slots=True)
class AuthenticatedActor:
    """Trusted accountable Human identity supplied by authentication."""

    actor_id: int
    organization_id: UUID

    def __post_init__(self) -> None:
        if isinstance(self.actor_id, bool) or self.actor_id < 1:
            raise ValueError("actor_id must be a positive integer")


@dataclass(frozen=True, slots=True)
class AuthorizationContext:
    """Opaque, application-validated authorization decision context."""

    operation: str
    scope: Mapping[str, Scalar]

    def __post_init__(self) -> None:
        if not self.operation.strip():
            raise ValueError("authorization operation must not be empty")


@dataclass(frozen=True, slots=True)
class CommandMetadata:
    """Common trusted metadata carried by every approved command."""

    actor: AuthenticatedActor
    authorization: AuthorizationContext
    rationale: str
    correlation_id: UUID
    idempotency_id: UUID
    command_id: UUID
    evidence_references: tuple[UUID, ...] = ()

    def __post_init__(self) -> None:
        normalized = self.rationale.strip()
        if not normalized:
            raise ValueError("rationale must not be empty")
        object.__setattr__(self, "rationale", normalized)
        if len(set(self.evidence_references)) != len(
            self.evidence_references
        ):
            raise ValueError("evidence references must be unique")


@dataclass(frozen=True, slots=True)
class CreateEngineeringObject:
    """Create one aggregate from application-derived scope and responsibility."""

    metadata: CommandMetadata
    organization_id: UUID
    customer_id: int | None
    project_id: int
    workspace_id: int
    family: EngineeringObjectFamily
    discipline: EngineeringDiscipline
    object_type: EngineeringObjectType
    creator_id: int
    steward_id: int


@dataclass(frozen=True, slots=True)
class MutationCommand:
    """Common optimistic-concurrency envelope for post-creation commands."""

    metadata: CommandMetadata
    object_id: UUID
    expected_version: int

    def __post_init__(self) -> None:
        if (
            isinstance(self.expected_version, bool)
            or self.expected_version < 1
        ):
            raise ValueError("expected_version must be a positive integer")


@dataclass(frozen=True, slots=True)
class ReclassifyEngineeringObject(MutationCommand):
    """Replace the aggregate's complete approved classification."""

    family: EngineeringObjectFamily
    discipline: EngineeringDiscipline
    object_type: EngineeringObjectType


@dataclass(frozen=True, slots=True)
class TransitionEngineeringObjectLifecycle(MutationCommand):
    """Apply one approved lifecycle transition."""

    lifecycle: EngineeringLifecycle
    replacement_object_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class TransitionEngineeringObjectAuthority(MutationCommand):
    """Apply one approved authority-standing transition."""

    authority_standing: EngineeringAuthorityStanding


@dataclass(frozen=True, slots=True)
class TransferEngineeringObjectSteward(MutationCommand):
    """Transfer stewardship to one application-validated Human."""

    steward_id: int

    def __post_init__(self) -> None:
        MutationCommand.__post_init__(self)
        if isinstance(self.steward_id, bool) or self.steward_id < 1:
            raise ValueError("steward_id must be a positive integer")


@dataclass(frozen=True, slots=True)
class EngineeringObjectDomainEvent:
    """Immutable fact produced by one successful aggregate operation."""

    event_id: UUID
    event_type: str
    schema_version: int
    object_id: UUID
    aggregate_version: int
    occurred_at: datetime
    actor_id: int
    correlation_id: UUID
    causation_id: UUID
    organization_id: UUID
    project_id: int
    workspace_id: int
    payload: Mapping[str, Scalar]


@dataclass(frozen=True, slots=True)
class EngineeringObjectCommandResult:
    """Domain result returned after an accepted in-memory state change."""

    object_id: UUID
    previous_version: int | None
    version: int
    command_type: str
    correlation_id: UUID
    events: tuple[EngineeringObjectDomainEvent, ...]


@dataclass(frozen=True, slots=True)
class EngineeringObjectIdempotencyOutcome:
    """Committed retry outcome with its authorized response snapshot."""

    result: EngineeringObjectCommandResult
    authorized_state: Mapping[str, Scalar]


class EngineeringObjectOutbox(Base):
    """Durable outbox record staged in the aggregate transaction."""

    __tablename__ = "engineering_object_outbox"
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_eo_outbox_event_id"),
        CheckConstraint("aggregate_version >= 1", name="ck_eo_outbox_version"),
    )

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_id = Column(PostgreSQLUUID(as_uuid=True), nullable=False)
    aggregate_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("engineering_objects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    aggregate_version = Column(Integer, nullable=False)
    event_type = Column(String(96), nullable=False)
    schema_version = Column(Integer, nullable=False, server_default="1")
    payload = Column(JSON, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class EngineeringObjectIdempotency(Base):
    """Durable command reservation and authorized result."""

    __tablename__ = "engineering_object_idempotency"
    __table_args__ = (
        UniqueConstraint(
            "actor_id", "command_type", "idempotency_id",
            name="uq_eo_idempotency_scope",
        ),
        CheckConstraint(
            "status IN ('pending', 'completed')",
            name="ck_eo_idempotency_status",
        ),
    )

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    actor_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    command_type = Column(String(64), nullable=False)
    idempotency_id = Column(PostgreSQLUUID(as_uuid=True), nullable=False)
    request_fingerprint = Column(String(64), nullable=False)
    status = Column(String(16), nullable=False, server_default="pending")
    aggregate_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("engineering_objects.id", ondelete="RESTRICT"),
        nullable=True,
    )
    result = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now()
    )
