"""Commands, events, and durable records for Engineering Experience Capture."""

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func

from app.core.database import Base
from app.enums.engineering_experience_capture import EngineeringExperienceSourceKind


Scalar = str | int | bool | UUID | datetime | None


class EngineeringExperienceCaptureCommandError(ValueError):
    pass


class EngineeringExperienceCaptureVersionMismatch(EngineeringExperienceCaptureCommandError):
    pass


class EngineeringExperienceCaptureTransitionRejected(EngineeringExperienceCaptureCommandError):
    pass


class EngineeringExperienceCaptureContentRejected(EngineeringExperienceCaptureCommandError):
    pass


class EngineeringExperienceCaptureContextRejected(EngineeringExperienceCaptureCommandError):
    pass


class EngineeringExperienceCaptureSupersessionRejected(EngineeringExperienceCaptureCommandError):
    pass


@dataclass(frozen=True, slots=True)
class EngineeringExperienceCaptureActor:
    actor_id: int
    organization_id: UUID

    def __post_init__(self) -> None:
        if self.actor_id <= 0:
            raise ValueError("actor_id must be positive")


@dataclass(frozen=True, slots=True)
class EngineeringExperienceCaptureMetadata:
    actor: EngineeringExperienceCaptureActor
    rationale: str
    correlation_id: UUID
    idempotency_id: UUID
    command_id: UUID

    def __post_init__(self) -> None:
        if not self.rationale.strip():
            raise ValueError("rationale must not be empty")


@dataclass(frozen=True, slots=True)
class CreateEngineeringExperienceCapture:
    metadata: EngineeringExperienceCaptureMetadata
    organization_id: UUID
    project_id: int
    workspace_id: int | None
    discipline: str | None
    engineering_object_id: UUID | None
    source_kind: EngineeringExperienceSourceKind
    original_content: str
    source_reference: str | None
    creator_id: int


@dataclass(frozen=True, slots=True)
class WithdrawEngineeringExperienceCapture:
    metadata: EngineeringExperienceCaptureMetadata
    capture_id: UUID
    expected_version: int


@dataclass(frozen=True, slots=True)
class SupersedeEngineeringExperienceCapture:
    metadata: EngineeringExperienceCaptureMetadata
    capture_id: UUID
    expected_version: int
    replacement_capture_id: UUID


@dataclass(frozen=True, slots=True)
class EngineeringExperienceCaptureEvent:
    event_id: UUID
    event_type: str
    capture_id: UUID
    aggregate_version: int
    occurred_at: datetime
    actor_id: int
    correlation_id: UUID
    causation_id: UUID
    organization_id: UUID
    project_id: int
    workspace_id: int | None
    engineering_object_id: UUID | None
    source_kind: str
    payload: Mapping[str, Scalar]


@dataclass(frozen=True, slots=True)
class EngineeringExperienceCaptureResult:
    capture_id: UUID
    previous_version: int | None
    version: int
    command_type: str
    correlation_id: UUID
    events: tuple[EngineeringExperienceCaptureEvent, ...]


@dataclass(frozen=True, slots=True)
class EngineeringExperienceCaptureOutcome:
    result: EngineeringExperienceCaptureResult
    authorized_state: Mapping[str, object]


class EngineeringExperienceCaptureOutbox(Base):
    __tablename__ = "engineering_experience_capture_outbox"
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_experience_capture_outbox_event"),
        UniqueConstraint(
            "aggregate_id",
            "aggregate_version",
            "event_type",
            name="uq_experience_capture_outbox_aggregate_event",
        ),
        CheckConstraint("aggregate_version >= 1", name="ck_experience_capture_outbox_version"),
        CheckConstraint("schema_version = 1", name="ck_experience_capture_outbox_schema_version"),
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_id = Column(PGUUID(as_uuid=True), nullable=False)
    aggregate_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("engineering_experience_captures.id", ondelete="RESTRICT"),
        nullable=False,
    )
    aggregate_version = Column(Integer, nullable=False)
    event_type = Column(String(96), nullable=False)
    schema_version = Column(Integer, nullable=False, default=1, server_default="1")
    payload = Column(JSON, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class EngineeringExperienceCaptureIdempotency(Base):
    __tablename__ = "engineering_experience_capture_idempotency"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "actor_id",
            "command_type",
            "idempotency_id",
            name="uq_experience_capture_idempotency_scope",
        ),
        CheckConstraint(
            "status IN ('pending','completed')",
            name="ck_experience_capture_idempotency_status",
        ),
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    command_type = Column(String(64), nullable=False)
    idempotency_id = Column(PGUUID(as_uuid=True), nullable=False)
    request_fingerprint = Column(String(64), nullable=False)
    status = Column(String(16), nullable=False, default="pending", server_default="pending")
    aggregate_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("engineering_experience_captures.id", ondelete="RESTRICT"),
    )
    result = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
