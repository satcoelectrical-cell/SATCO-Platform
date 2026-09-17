"""patch 055 retention foundation

Revision ID: e05500000001
Revises: e05400000006
Create Date: 2026-09-14 20:59:25.034455

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e05500000001'
down_revision: Union[str, Sequence[str], None] = 'e05400000006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the additive PATCH-055 retention-governance foundation."""

    op.create_table(
        "retention_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            sa.Integer(),
            sa.ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("subject_kind", sa.String(32), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.Column("mode", sa.String(32), nullable=False),
        sa.Column("retain_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("policy_source", sa.String(32), nullable=False),
        sa.Column("basis_code", sa.String(64), nullable=False),
        sa.Column("rationale", sa.String(2000), nullable=True),
        sa.Column(
            "created_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "supersedes_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("retention_records.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("request_digest", sa.String(64), nullable=False),
        sa.Column("record_digest", sa.CHAR(64), nullable=False),
        sa.UniqueConstraint(
            "organization_id",
            "subject_kind",
            "subject_id",
            "version",
            name="uq_retention_record_subject_version",
        ),
        sa.CheckConstraint(
            "version >= 1",
            name="ck_retention_record_version",
        ),
        sa.CheckConstraint(
            "subject_kind IN ('evidence','supporting_file')",
            name="ck_retention_record_subject_kind",
        ),
        sa.CheckConstraint(
            "mode IN ('retain_until','retain_indefinitely')",
            name="ck_retention_record_mode",
        ),
        sa.CheckConstraint(
            "policy_source IN "
            "('platform_default','organization_default','human_subject_override')",
            name="ck_retention_record_policy_source",
        ),
        sa.CheckConstraint(
            "basis_code ~ '^[a-z0-9_.-]{1,64}$'",
            name="ck_retention_record_basis_code",
        ),
        sa.CheckConstraint(
            "(mode = 'retain_until' AND retain_until IS NOT NULL) OR "
            "(mode = 'retain_indefinitely' AND retain_until IS NULL)",
            name="ck_retention_record_until_shape",
        ),
        sa.CheckConstraint(
            "record_digest ~ '^[0-9a-f]{64}$'",
            name="ck_retention_record_digest",
        ),
    )

    op.create_index(
        "uq_retention_record_current_subject",
        "retention_records",
        ["organization_id", "subject_kind", "subject_id"],
        unique=True,
        postgresql_where=sa.text("is_current"),
    )

    op.create_table(
        "retention_holds",
        sa.Column("row_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("hold_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            sa.Integer(),
            sa.ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("subject_kind", sa.String(32), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("reason_code", sa.String(64), nullable=False),
        sa.Column("rationale", sa.String(2000), nullable=False),
        sa.Column("authority_reference", sa.String(512), nullable=False),
        sa.Column(
            "placed_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("placed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "released_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("release_rationale", sa.String(2000), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "predecessor_row_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("retention_holds.row_id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("digest", sa.CHAR(64), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.UniqueConstraint(
            "hold_id",
            "version",
            name="uq_retention_hold_version",
        ),
        sa.CheckConstraint(
            "subject_kind IN ('evidence','supporting_file')",
            name="ck_retention_hold_subject_kind",
        ),
        sa.CheckConstraint(
            "status IN ('active','released')",
            name="ck_retention_hold_status",
        ),
        sa.CheckConstraint(
            "reason_code ~ '^[a-z0-9_.-]{1,64}$'",
            name="ck_retention_hold_reason_code",
        ),
        sa.CheckConstraint(
            "version >= 1",
            name="ck_retention_hold_version",
        ),
        sa.CheckConstraint(
            "digest ~ '^[0-9a-f]{64}$'",
            name="ck_retention_hold_digest",
        ),
        sa.CheckConstraint(
            "(status = 'active' "
            "AND released_by_user_id IS NULL "
            "AND released_at IS NULL "
            "AND release_rationale IS NULL) OR "
            "(status = 'released' "
            "AND released_by_user_id IS NOT NULL "
            "AND released_at IS NOT NULL "
            "AND release_rationale IS NOT NULL)",
            name="ck_retention_hold_release_shape",
        ),
    )

    op.create_index(
        "uq_retention_hold_current_active_subject",
        "retention_holds",
        ["organization_id", "subject_kind", "subject_id"],
        unique=True,
        postgresql_where=sa.text("is_current AND status = 'active'"),
    )

    op.create_table(
        "retention_disposition_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            sa.Integer(),
            sa.ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("subject_kind", sa.String(32), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "retention_record_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("retention_records.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("eligibility_snapshot", sa.String(32), nullable=False),
        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("reason", sa.String(2000), nullable=False),
        sa.Column(
            "decided_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("subject_version_snapshot", sa.Integer(), nullable=False),
        sa.Column("request_digest", sa.String(64), nullable=False),
        sa.CheckConstraint(
            "subject_kind IN ('evidence','supporting_file')",
            name="ck_retention_disposition_subject_kind",
        ),
        sa.CheckConstraint(
            "eligibility_snapshot IN "
            "('not_eligible','eligible','blocked_by_hold','indeterminate')",
            name="ck_retention_disposition_eligibility",
        ),
        sa.CheckConstraint(
            "decision IN ('retain','approve_disposition')",
            name="ck_retention_disposition_decision",
        ),
        sa.CheckConstraint(
            "subject_version_snapshot >= 1",
            name="ck_retention_disposition_subject_version",
        ),
        sa.CheckConstraint(
            "request_digest ~ '^[0-9a-f]{64}$'",
            name="ck_retention_disposition_request_digest",
        ),
    )

    op.create_table(
        "retention_exports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            sa.Integer(),
            sa.ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "requested_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("purpose", sa.String(1000), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("format", sa.String(16), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("aggregate_digest", sa.String(64), nullable=True),
        sa.Column("byte_count", sa.BigInteger(), nullable=True),
        sa.Column("failure_code", sa.String(64), nullable=True),
        sa.Column("request_digest", sa.String(64), nullable=False),
        sa.Column("artifact_storage_key", sa.String(80), nullable=True),
        sa.Column("artifact_object_version", sa.String(128), nullable=True),
        sa.CheckConstraint(
            "status IN ('requested','completed','failed')",
            name="ck_retention_export_status",
        ),
        sa.CheckConstraint(
            "format = 'zip_v1'",
            name="ck_retention_export_format",
        ),
        sa.CheckConstraint(
            "request_digest ~ '^[0-9a-f]{64}$'",
            name="ck_retention_export_request_digest",
        ),
        sa.CheckConstraint(
            "aggregate_digest IS NULL OR "
            "aggregate_digest ~ '^[0-9a-f]{64}$'",
            name="ck_retention_export_aggregate_digest",
        ),
        sa.CheckConstraint(
            "(status = 'completed' "
            "AND completed_at IS NOT NULL "
            "AND aggregate_digest IS NOT NULL "
            "AND byte_count IS NOT NULL "
            "AND artifact_storage_key IS NOT NULL "
            "AND artifact_object_version IS NOT NULL) OR "
            "(status <> 'completed' "
            "AND artifact_storage_key IS NULL "
            "AND artifact_object_version IS NULL)",
            name="ck_retention_export_completed_shape",
        ),
    )

    op.create_table(
        "retention_export_subjects",
        sa.Column(
            "export_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("retention_exports.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("ordinal", sa.Integer(), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            sa.Integer(),
            sa.ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("subject_kind", sa.String(32), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_version", sa.Integer(), nullable=True),
        sa.Column("content_digest", sa.String(64), nullable=True),
        sa.CheckConstraint(
            "subject_kind IN ('evidence','supporting_file')",
            name="ck_retention_export_subject_kind",
        ),
        sa.CheckConstraint(
            "ordinal BETWEEN 0 AND 31",
            name="ck_retention_export_subject_ordinal",
        ),
        sa.CheckConstraint(
            "subject_version IS NULL OR subject_version >= 1",
            name="ck_retention_export_subject_version",
        ),
        sa.CheckConstraint(
            "content_digest IS NULL OR content_digest ~ '^[0-9a-f]{64}$'",
            name="ck_retention_export_subject_digest",
        ),
    )

    op.create_table(
        "retention_recoveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            sa.Integer(),
            sa.ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("subject_kind", sa.String(32), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "requested_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expected_digest", sa.String(64), nullable=True),
        sa.Column("verified_digest", sa.String(64), nullable=True),
        sa.Column("failure_code", sa.String(64), nullable=True),
        sa.Column("request_digest", sa.String(64), nullable=False),
        sa.CheckConstraint(
            "subject_kind IN ('evidence','supporting_file')",
            name="ck_retention_recovery_subject_kind",
        ),
        sa.CheckConstraint(
            "status IN "
            "('not_required','available','temporarily_unavailable',"
            "'recovered','unrecoverable')",
            name="ck_retention_recovery_status",
        ),
        sa.CheckConstraint(
            "expected_digest IS NULL OR expected_digest ~ '^[0-9a-f]{64}$'",
            name="ck_retention_recovery_expected_digest",
        ),
        sa.CheckConstraint(
            "verified_digest IS NULL OR verified_digest ~ '^[0-9a-f]{64}$'",
            name="ck_retention_recovery_verified_digest",
        ),
        sa.CheckConstraint(
            "request_digest ~ '^[0-9a-f]{64}$'",
            name="ck_retention_recovery_request_digest",
        ),
    )

    op.create_table(
        "retention_idempotency",
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "actor_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("operation", sa.String(64), nullable=False),
        sa.Column("idempotency_key", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_digest", sa.CHAR(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("safe_result", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "organization_id",
            "actor_user_id",
            "operation",
            "idempotency_key",
            name="uq_retention_idempotency_scope",
        ),
        sa.CheckConstraint(
            "status IN ('pending','completed')",
            name="ck_retention_idempotency_status",
        ),
        sa.CheckConstraint(
            "request_digest ~ '^[0-9a-f]{64}$'",
            name="ck_retention_idempotency_request_digest",
        ),
        sa.CheckConstraint(
            "(status = 'pending' AND safe_result IS NULL "
            "AND completed_at IS NULL) OR "
            "(status = 'completed' AND safe_result IS NOT NULL "
            "AND completed_at IS NOT NULL)",
            name="ck_retention_idempotency_completion_shape",
        ),
    )

    op.create_table(
        "retention_outbox",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "workspace_id",
            sa.Integer(),
            sa.ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("aggregate_kind", sa.String(64), nullable=False),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("aggregate_version", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(96), nullable=False),
        sa.Column(
            "payload_schema_version",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "attempt_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("last_error_category", sa.String(64), nullable=True),
        sa.UniqueConstraint(
            "aggregate_kind",
            "aggregate_id",
            "aggregate_version",
            "event_type",
            name="uq_retention_outbox_event",
        ),
        sa.CheckConstraint(
            "aggregate_version >= 1",
            name="ck_retention_outbox_aggregate_version",
        ),
        sa.CheckConstraint(
            "payload_schema_version = 1",
            name="ck_retention_outbox_payload_schema",
        ),
        sa.CheckConstraint(
            "attempt_count >= 0",
            name="ck_retention_outbox_attempt_count",
        ),
    )


def downgrade() -> None:
    """Drop PATCH-055 persistence only when all capability tables are empty."""

    bind = op.get_bind()
    tables = (
        "retention_outbox",
        "retention_idempotency",
        "retention_recoveries",
        "retention_export_subjects",
        "retention_exports",
        "retention_disposition_decisions",
        "retention_holds",
        "retention_records",
    )

    nonempty = []
    for table_name in tables:
        count = bind.execute(
            sa.text(f'SELECT COUNT(*) FROM "{table_name}"')
        ).scalar_one()
        if count:
            nonempty.append((table_name, count))

    if nonempty:
        detail = ", ".join(
            f"{table_name}={count}"
            for table_name, count in nonempty
        )
        raise RuntimeError(
            "PATCH-055 downgrade refused because retention persistence "
            f"contains data: {detail}. Use governed forward-repair."
        )

    for table_name in tables:
        op.drop_table(table_name)
