"""PATCH-055 retention-governance persistence models."""

from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    CHAR,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.sql import func, text

from app.core.database import Base


class RetentionRecord(Base):
    __tablename__ = "retention_records"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    workspace_id = Column(
        Integer,
        ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"),
        nullable=True,
    )
    subject_kind = Column(String(32), nullable=False)
    subject_id = Column(PGUUID(as_uuid=True), nullable=False)
    version = Column(Integer, nullable=False)
    is_current = Column(Boolean, nullable=False, default=True)
    mode = Column(String(32), nullable=False)
    retain_until = Column(DateTime(timezone=True), nullable=True)
    policy_source = Column(String(32), nullable=False)
    basis_code = Column(String(64), nullable=False)
    rationale = Column(String(2000), nullable=True)
    created_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    supersedes_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("retention_records.id", ondelete="RESTRICT"),
        nullable=True,
    )
    request_digest = Column(String(64), nullable=False)
    record_digest = Column(CHAR(64), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "subject_kind",
            "subject_id",
            "version",
            name="uq_retention_record_subject_version",
        ),
        Index(
            "uq_retention_record_current_subject",
            "organization_id",
            "subject_kind",
            "subject_id",
            unique=True,
            postgresql_where=text("is_current"),
        ),
        CheckConstraint("version >= 1", name="ck_retention_record_version"),
        CheckConstraint(
            "subject_kind IN ('evidence','supporting_file')",
            name="ck_retention_record_subject_kind",
        ),
        CheckConstraint(
            "mode IN ('retain_until','retain_indefinitely')",
            name="ck_retention_record_mode",
        ),
        CheckConstraint(
            "policy_source IN "
            "('platform_default','organization_default','human_subject_override')",
            name="ck_retention_record_policy_source",
        ),
        CheckConstraint(
            "basis_code ~ '^[a-z0-9_.-]{1,64}$'",
            name="ck_retention_record_basis_code",
        ),
        CheckConstraint(
            "(mode = 'retain_until' AND retain_until IS NOT NULL) OR "
            "(mode = 'retain_indefinitely' AND retain_until IS NULL)",
            name="ck_retention_record_until_shape",
        ),
        CheckConstraint(
            "record_digest ~ '^[0-9a-f]{64}$'",
            name="ck_retention_record_digest",
        ),
    )


class RetentionHold(Base):
    __tablename__ = "retention_holds"

    row_id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    hold_id = Column(PGUUID(as_uuid=True), nullable=False)

    organization_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    workspace_id = Column(
        Integer,
        ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"),
        nullable=True,
    )
    subject_kind = Column(String(32), nullable=False)
    subject_id = Column(PGUUID(as_uuid=True), nullable=False)

    status = Column(String(16), nullable=False)
    reason_code = Column(String(64), nullable=False)
    rationale = Column(String(2000), nullable=False)
    authority_reference = Column(String(512), nullable=False)

    placed_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    placed_at = Column(DateTime(timezone=True), nullable=False)

    released_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    released_at = Column(DateTime(timezone=True), nullable=True)
    release_rationale = Column(String(2000), nullable=True)

    version = Column(Integer, nullable=False)
    predecessor_row_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("retention_holds.row_id", ondelete="RESTRICT"),
        nullable=True,
    )
    digest = Column(CHAR(64), nullable=False)
    is_current = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint(
            "hold_id",
            "version",
            name="uq_retention_hold_version",
        ),
        Index(
            "uq_retention_hold_current_active_subject",
            "organization_id",
            "subject_kind",
            "subject_id",
            unique=True,
            postgresql_where=text("is_current AND status = 'active'"),
        ),
        CheckConstraint(
            "subject_kind IN ('evidence','supporting_file')",
            name="ck_retention_hold_subject_kind",
        ),
        CheckConstraint(
            "status IN ('active','released')",
            name="ck_retention_hold_status",
        ),
        CheckConstraint(
            "reason_code ~ '^[a-z0-9_.-]{1,64}$'",
            name="ck_retention_hold_reason_code",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_retention_hold_version",
        ),
        CheckConstraint(
            "digest ~ '^[0-9a-f]{64}$'",
            name="ck_retention_hold_digest",
        ),
        CheckConstraint(
            "(status = 'active' "
            "AND released_by_user_id IS NULL "
            "AND released_at IS NULL "
            "AND release_rationale IS NULL) "
            "OR "
            "(status = 'released' "
            "AND released_by_user_id IS NOT NULL "
            "AND released_at IS NOT NULL "
            "AND release_rationale IS NOT NULL)",
            name="ck_retention_hold_release_shape",
        ),
    )


class RetentionDispositionDecision(Base):
    __tablename__ = "retention_disposition_decisions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    organization_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    workspace_id = Column(
        Integer,
        ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"),
        nullable=True,
    )
    subject_kind = Column(String(32), nullable=False)
    subject_id = Column(PGUUID(as_uuid=True), nullable=False)

    retention_record_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("retention_records.id", ondelete="RESTRICT"),
        nullable=False,
    )
    eligibility_snapshot = Column(String(32), nullable=False)
    decision = Column(String(32), nullable=False)
    reason = Column(String(2000), nullable=False)

    decided_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    decided_at = Column(DateTime(timezone=True), nullable=False)

    subject_version_snapshot = Column(Integer, nullable=False)
    request_digest = Column(String(64), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "subject_kind IN ('evidence','supporting_file')",
            name="ck_retention_disposition_subject_kind",
        ),
        CheckConstraint(
            "eligibility_snapshot IN "
            "('not_eligible','eligible','blocked_by_hold','indeterminate')",
            name="ck_retention_disposition_eligibility",
        ),
        CheckConstraint(
            "decision IN ('retain','approve_disposition')",
            name="ck_retention_disposition_decision",
        ),
        CheckConstraint(
            "subject_version_snapshot >= 1",
            name="ck_retention_disposition_subject_version",
        ),
        CheckConstraint(
            "request_digest ~ '^[0-9a-f]{64}$'",
            name="ck_retention_disposition_request_digest",
        ),
    )


class RetentionExport(Base):
    __tablename__ = "retention_exports"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    workspace_id = Column(
        Integer,
        ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"),
        nullable=True,
    )
    requested_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    purpose = Column(String(1000), nullable=False)
    status = Column(String(16), nullable=False)
    format = Column(String(16), nullable=False)
    requested_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    aggregate_digest = Column(String(64), nullable=True)
    byte_count = Column(BigInteger, nullable=True)
    failure_code = Column(String(64), nullable=True)
    request_digest = Column(String(64), nullable=False)

    artifact_storage_key = Column(String(80), nullable=True)
    artifact_object_version = Column(String(128), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('requested','completed','failed')",
            name="ck_retention_export_status",
        ),
        CheckConstraint(
            "format = 'zip_v1'",
            name="ck_retention_export_format",
        ),
        CheckConstraint(
            "request_digest ~ '^[0-9a-f]{64}$'",
            name="ck_retention_export_request_digest",
        ),
        CheckConstraint(
            "aggregate_digest IS NULL OR aggregate_digest ~ '^[0-9a-f]{64}$'",
            name="ck_retention_export_aggregate_digest",
        ),
        CheckConstraint(
            "(status = 'completed' "
            "AND completed_at IS NOT NULL "
            "AND aggregate_digest IS NOT NULL "
            "AND byte_count IS NOT NULL "
            "AND artifact_storage_key IS NOT NULL "
            "AND artifact_object_version IS NOT NULL) "
            "OR "
            "(status <> 'completed' "
            "AND artifact_storage_key IS NULL "
            "AND artifact_object_version IS NULL)",
            name="ck_retention_export_completed_shape",
        ),
    )


class RetentionExportSubject(Base):
    __tablename__ = "retention_export_subjects"

    export_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("retention_exports.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    ordinal = Column(Integer, primary_key=True)

    organization_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    workspace_id = Column(
        Integer,
        ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"),
        nullable=True,
    )
    subject_kind = Column(String(32), nullable=False)
    subject_id = Column(PGUUID(as_uuid=True), nullable=False)

    subject_version = Column(Integer, nullable=True)
    content_digest = Column(String(64), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "subject_kind IN ('evidence','supporting_file')",
            name="ck_retention_export_subject_kind",
        ),
        CheckConstraint(
            "ordinal BETWEEN 0 AND 31",
            name="ck_retention_export_subject_ordinal",
        ),
        CheckConstraint(
            "subject_version IS NULL OR subject_version >= 1",
            name="ck_retention_export_subject_version",
        ),
        CheckConstraint(
            "content_digest IS NULL OR content_digest ~ '^[0-9a-f]{64}$'",
            name="ck_retention_export_subject_digest",
        ),
    )


class RetentionRecovery(Base):
    __tablename__ = "retention_recoveries"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    organization_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    workspace_id = Column(
        Integer,
        ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"),
        nullable=True,
    )
    subject_kind = Column(String(32), nullable=False)
    subject_id = Column(PGUUID(as_uuid=True), nullable=False)

    requested_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status = Column(String(32), nullable=False)
    requested_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    expected_digest = Column(String(64), nullable=True)
    verified_digest = Column(String(64), nullable=True)
    failure_code = Column(String(64), nullable=True)
    request_digest = Column(String(64), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "subject_kind IN ('evidence','supporting_file')",
            name="ck_retention_recovery_subject_kind",
        ),
        CheckConstraint(
            "status IN "
            "('not_required','available','temporarily_unavailable',"
            "'recovered','unrecoverable')",
            name="ck_retention_recovery_status",
        ),
        CheckConstraint(
            "expected_digest IS NULL OR expected_digest ~ '^[0-9a-f]{64}$'",
            name="ck_retention_recovery_expected_digest",
        ),
        CheckConstraint(
            "verified_digest IS NULL OR verified_digest ~ '^[0-9a-f]{64}$'",
            name="ck_retention_recovery_verified_digest",
        ),
        CheckConstraint(
            "request_digest ~ '^[0-9a-f]{64}$'",
            name="ck_retention_recovery_request_digest",
        ),
    )


class RetentionIdempotency(Base):
    __tablename__ = "retention_idempotency"

    organization_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    actor_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    operation = Column(String(64), nullable=False)
    idempotency_key = Column(PGUUID(as_uuid=True), nullable=False)
    request_digest = Column(CHAR(64), nullable=False)
    status = Column(String(16), nullable=False)
    safe_result = Column(JSONB, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "actor_user_id",
            "operation",
            "idempotency_key",
            name="uq_retention_idempotency_scope",
        ),
        CheckConstraint(
            "status IN ('pending','completed')",
            name="ck_retention_idempotency_status",
        ),
        CheckConstraint(
            "request_digest ~ '^[0-9a-f]{64}$'",
            name="ck_retention_idempotency_request_digest",
        ),
        CheckConstraint(
            "(status = 'pending' AND safe_result IS NULL AND completed_at IS NULL) "
            "OR "
            "(status = 'completed' AND safe_result IS NOT NULL "
            "AND completed_at IS NOT NULL)",
            name="ck_retention_idempotency_completion_shape",
        ),
    )

    __mapper_args__ = {
        "primary_key": [
            organization_id,
            actor_user_id,
            operation,
            idempotency_key,
        ]
    }


class RetentionOutbox(Base):
    __tablename__ = "retention_outbox"

    event_id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    organization_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=True,
    )
    workspace_id = Column(
        Integer,
        ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"),
        nullable=True,
    )

    aggregate_kind = Column(String(64), nullable=False)
    aggregate_id = Column(PGUUID(as_uuid=True), nullable=False)
    aggregate_version = Column(Integer, nullable=False)

    event_type = Column(String(96), nullable=False)
    payload_schema_version = Column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    payload = Column(JSONB, nullable=False)

    occurred_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    published_at = Column(DateTime(timezone=True), nullable=True)

    attempt_count = Column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    last_error_category = Column(String(64), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "aggregate_kind",
            "aggregate_id",
            "aggregate_version",
            "event_type",
            name="uq_retention_outbox_event",
        ),
        CheckConstraint(
            "aggregate_version >= 1",
            name="ck_retention_outbox_aggregate_version",
        ),
        CheckConstraint(
            "payload_schema_version = 1",
            name="ck_retention_outbox_payload_schema",
        ),
        CheckConstraint(
            "attempt_count >= 0",
            name="ck_retention_outbox_attempt_count",
        ),
    )
