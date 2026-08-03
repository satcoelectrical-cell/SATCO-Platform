"""Engineering Experience Capture Aggregate Root."""

from datetime import datetime
import unicodedata
from uuid import uuid4

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func

from app.core.database import Base
from app.enums.engineering_experience_capture import (
    EngineeringExperienceCaptureLifecycle,
    EngineeringExperienceSourceKind,
)
from app.models.engineering_experience_capture_command import (
    CreateEngineeringExperienceCapture,
    EngineeringExperienceCaptureContentRejected,
    EngineeringExperienceCaptureContextRejected,
    EngineeringExperienceCaptureEvent,
    EngineeringExperienceCaptureResult,
    EngineeringExperienceCaptureSupersessionRejected,
    EngineeringExperienceCaptureTransitionRejected,
    EngineeringExperienceCaptureVersionMismatch,
    SupersedeEngineeringExperienceCapture,
    WithdrawEngineeringExperienceCapture,
)


def _values(enum_type: type) -> str:
    return ",".join(f"'{item.value}'" for item in enum_type)


def _has_prohibited_control(value: str, *, allow_lf_tab: bool) -> bool:
    for character in value:
        if character in {"\n", "\t"} and allow_lf_tab:
            continue
        if character == "\x00" or unicodedata.category(character) == "Cc":
            return True
    return False


def normalize_capture_text(value: str, *, field: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise EngineeringExperienceCaptureContentRejected(f"{field} must be text")
    normalized = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    if _has_prohibited_control(normalized, allow_lf_tab=True):
        raise EngineeringExperienceCaptureContentRejected(f"{field} contains prohibited controls")
    if not 1 <= len(normalized) <= maximum:
        raise EngineeringExperienceCaptureContentRejected(f"{field} length is invalid")
    return normalized


def normalize_single_line_text(value: str, *, field: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise EngineeringExperienceCaptureContentRejected(f"{field} must be text")
    normalized = value.strip()
    if "\n" in normalized or "\r" in normalized or _has_prohibited_control(normalized, allow_lf_tab=False):
        raise EngineeringExperienceCaptureContentRejected(f"{field} must be a safe single line")
    if not 1 <= len(normalized) <= maximum:
        raise EngineeringExperienceCaptureContentRejected(f"{field} length is invalid")
    return normalized


class EngineeringExperienceCapture(Base):
    __tablename__ = "engineering_experience_captures"
    __table_args__ = (
        CheckConstraint(
            f"lifecycle IN ({_values(EngineeringExperienceCaptureLifecycle)})",
            name="ck_experience_captures_lifecycle",
        ),
        CheckConstraint(
            f"source_kind IN ({_values(EngineeringExperienceSourceKind)})",
            name="ck_experience_captures_source_kind",
        ),
        CheckConstraint("version >= 1", name="ck_experience_captures_version"),
        CheckConstraint("updated_at >= created_at", name="ck_experience_captures_timestamp_order"),
        CheckConstraint(
            "workspace_id IS NOT NULL OR (discipline IS NULL AND engineering_object_id IS NULL)",
            name="ck_experience_captures_project_wide_context",
        ),
        CheckConstraint(
            "workspace_id IS NULL OR discipline IS NOT NULL",
            name="ck_experience_captures_workspace_discipline",
        ),
        CheckConstraint(
            "engineering_object_id IS NULL OR workspace_id IS NOT NULL",
            name="ck_experience_captures_object_workspace",
        ),
        CheckConstraint(
            "(lifecycle = 'superseded') = (superseded_by_capture_id IS NOT NULL)",
            name="ck_experience_captures_supersession_state",
        ),
        CheckConstraint(
            "superseded_by_capture_id IS NULL OR superseded_by_capture_id <> id",
            name="ck_experience_captures_distinct_replacement",
        ),
        CheckConstraint(
            "char_length(original_content) BETWEEN 1 AND 10000",
            name="ck_experience_captures_content_length",
        ),
        CheckConstraint(
            "source_reference IS NULL OR char_length(source_reference) BETWEEN 1 AND 512",
            name="ck_experience_captures_reference_length",
        ),
        Index(
            "ix_experience_captures_project_order",
            "organization_id",
            "project_id",
            text("created_at DESC"),
            text("id DESC"),
        ),
        Index(
            "ix_experience_captures_workspace_order",
            "organization_id",
            "project_id",
            "workspace_id",
            text("created_at DESC"),
            text("id DESC"),
        ),
        Index(
            "ix_experience_captures_lifecycle_kind",
            "organization_id",
            "project_id",
            "lifecycle",
            "source_kind",
        ),
        Index("ix_experience_captures_creator", "organization_id", "project_id", "creator_id"),
        Index(
            "ix_experience_captures_object",
            "organization_id",
            "engineering_object_id",
            postgresql_where=text("engineering_object_id IS NOT NULL"),
        ),
        Index(
            "uq_experience_captures_replacement",
            "superseded_by_capture_id",
            unique=True,
            postgresql_where="superseded_by_capture_id IS NOT NULL",
        ),
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"))
    discipline = Column(String(32))
    engineering_object_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("engineering_objects.id", ondelete="RESTRICT"),
    )
    source_kind = Column(String(32), nullable=False)
    original_content = Column(Text, nullable=False)
    source_reference = Column(String(512))
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    lifecycle = Column(String(16), nullable=False, default="captured", server_default="captured")
    superseded_by_capture_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("engineering_experience_captures.id", ondelete="RESTRICT"),
    )
    version = Column(Integer, nullable=False, default=1, server_default="1")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    @classmethod
    def create(cls, command: CreateEngineeringExperienceCapture, now: datetime):
        if command.organization_id != command.metadata.actor.organization_id:
            raise EngineeringExperienceCaptureContextRejected("trusted Organization mismatch")
        if command.creator_id != command.metadata.actor.actor_id:
            raise EngineeringExperienceCaptureContextRejected("trusted Creator mismatch")
        if command.project_id <= 0:
            raise EngineeringExperienceCaptureContextRejected("Project is required")
        if command.workspace_id is None and (
            command.discipline is not None or command.engineering_object_id is not None
        ):
            raise EngineeringExperienceCaptureContextRejected("Project-wide context is incoherent")
        if command.workspace_id is not None and command.discipline is None:
            raise EngineeringExperienceCaptureContextRejected("Workspace discipline is required")
        content = normalize_capture_text(
            command.original_content,
            field="original_content",
            maximum=10_000,
        )
        source_reference = None
        if command.source_reference is not None:
            source_reference = normalize_single_line_text(
                command.source_reference,
                field="source_reference",
                maximum=512,
            )
        aggregate = cls(
            id=uuid4(),
            organization_id=command.organization_id,
            project_id=command.project_id,
            workspace_id=command.workspace_id,
            discipline=command.discipline,
            engineering_object_id=command.engineering_object_id,
            source_kind=command.source_kind.value,
            original_content=content,
            source_reference=source_reference,
            creator_id=command.creator_id,
            lifecycle=EngineeringExperienceCaptureLifecycle.CAPTURED.value,
            superseded_by_capture_id=None,
            version=1,
            created_at=now,
            updated_at=now,
        )
        event = aggregate._event(command, "EngineeringExperienceCaptured", now)
        return aggregate, aggregate._result(command, None, (event,))

    def withdraw(self, command: WithdrawEngineeringExperienceCapture, now: datetime):
        self._validate_command(command.capture_id, command.expected_version)
        if self.lifecycle != EngineeringExperienceCaptureLifecycle.CAPTURED.value:
            raise EngineeringExperienceCaptureTransitionRejected("Capture is terminal")
        normalize_single_line_text(command.metadata.rationale, field="rationale", maximum=1_000)
        previous_version = self.version
        self.lifecycle = EngineeringExperienceCaptureLifecycle.WITHDRAWN.value
        self.version += 1
        self.updated_at = now
        event = self._event(command, "EngineeringExperienceCaptureWithdrawn", now)
        return self._result(command, previous_version, (event,))

    def supersede(self, command: SupersedeEngineeringExperienceCapture, now: datetime):
        self._validate_command(command.capture_id, command.expected_version)
        if self.lifecycle != EngineeringExperienceCaptureLifecycle.CAPTURED.value:
            raise EngineeringExperienceCaptureTransitionRejected("Capture is terminal")
        if command.replacement_capture_id == self.id:
            raise EngineeringExperienceCaptureSupersessionRejected("Replacement must be distinct")
        normalize_single_line_text(command.metadata.rationale, field="rationale", maximum=1_000)
        previous_version = self.version
        self.lifecycle = EngineeringExperienceCaptureLifecycle.SUPERSEDED.value
        self.superseded_by_capture_id = command.replacement_capture_id
        self.version += 1
        self.updated_at = now
        event = self._event(command, "EngineeringExperienceCaptureSuperseded", now)
        return self._result(command, previous_version, (event,))

    def _validate_command(self, capture_id, expected_version: int) -> None:
        if capture_id != self.id:
            raise EngineeringExperienceCaptureContextRejected("Capture identity mismatch")
        if expected_version <= 0 or expected_version != self.version:
            raise EngineeringExperienceCaptureVersionMismatch()

    def _event(self, command, event_type: str, now: datetime):
        payload = {"lifecycle": self.lifecycle}
        if self.superseded_by_capture_id is not None:
            payload["replacement_capture_id"] = self.superseded_by_capture_id
        return EngineeringExperienceCaptureEvent(
            event_id=uuid4(),
            event_type=event_type,
            capture_id=self.id,
            aggregate_version=self.version,
            occurred_at=now,
            actor_id=command.metadata.actor.actor_id,
            correlation_id=command.metadata.correlation_id,
            causation_id=command.metadata.command_id,
            organization_id=self.organization_id,
            project_id=self.project_id,
            workspace_id=self.workspace_id,
            engineering_object_id=self.engineering_object_id,
            source_kind=self.source_kind,
            payload=payload,
        )

    def _result(self, command, previous_version, events):
        return EngineeringExperienceCaptureResult(
            capture_id=self.id,
            previous_version=previous_version,
            version=self.version,
            command_type=type(command).__name__,
            correlation_id=command.metadata.correlation_id,
            events=events,
        )
