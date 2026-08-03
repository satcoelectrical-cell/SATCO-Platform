"""add Engineering Experience Capture persistence

Revision ID: e02800000001
Revises: e02810000001
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e02800000001"
down_revision: str | None = "e02810000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "engineering_experience_captures",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=True),
        sa.Column("discipline", sa.String(length=32), nullable=True),
        sa.Column("engineering_object_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_kind", sa.String(length=32), nullable=False),
        sa.Column("original_content", sa.Text(), nullable=False),
        sa.Column("source_reference", sa.String(length=512), nullable=True),
        sa.Column("creator_id", sa.Integer(), nullable=False),
        sa.Column("lifecycle", sa.String(length=16), server_default="captured", nullable=False),
        sa.Column("superseded_by_capture_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("lifecycle IN ('captured','withdrawn','superseded')", name="ck_experience_captures_lifecycle"),
        sa.CheckConstraint("source_kind IN ('observation','question','assumption','rationale','discussion_note','correspondence_note','field_note','review_note','outcome','lesson_candidate','external_record_note')", name="ck_experience_captures_source_kind"),
        sa.CheckConstraint("version >= 1", name="ck_experience_captures_version"),
        sa.CheckConstraint("updated_at >= created_at", name="ck_experience_captures_timestamp_order"),
        sa.CheckConstraint("workspace_id IS NOT NULL OR (discipline IS NULL AND engineering_object_id IS NULL)", name="ck_experience_captures_project_wide_context"),
        sa.CheckConstraint("workspace_id IS NULL OR discipline IS NOT NULL", name="ck_experience_captures_workspace_discipline"),
        sa.CheckConstraint("engineering_object_id IS NULL OR workspace_id IS NOT NULL", name="ck_experience_captures_object_workspace"),
        sa.CheckConstraint("(lifecycle = 'superseded') = (superseded_by_capture_id IS NOT NULL)", name="ck_experience_captures_supersession_state"),
        sa.CheckConstraint("superseded_by_capture_id IS NULL OR superseded_by_capture_id <> id", name="ck_experience_captures_distinct_replacement"),
        sa.CheckConstraint("char_length(original_content) BETWEEN 1 AND 10000", name="ck_experience_captures_content_length"),
        sa.CheckConstraint("source_reference IS NULL OR char_length(source_reference) BETWEEN 1 AND 512", name="ck_experience_captures_reference_length"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workspace_id"], ["engineering_workspaces.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["engineering_object_id"], ["engineering_objects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["superseded_by_capture_id"], ["engineering_experience_captures.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_experience_captures_project_order", "engineering_experience_captures", ["organization_id", "project_id", sa.text("created_at DESC"), sa.text("id DESC")])
    op.create_index("ix_experience_captures_workspace_order", "engineering_experience_captures", ["organization_id", "project_id", "workspace_id", sa.text("created_at DESC"), sa.text("id DESC")])
    op.create_index("ix_experience_captures_lifecycle_kind", "engineering_experience_captures", ["organization_id", "project_id", "lifecycle", "source_kind"])
    op.create_index("ix_experience_captures_creator", "engineering_experience_captures", ["organization_id", "project_id", "creator_id"])
    op.create_index("ix_experience_captures_object", "engineering_experience_captures", ["organization_id", "engineering_object_id"], postgresql_where=sa.text("engineering_object_id IS NOT NULL"))
    op.create_index("uq_experience_captures_replacement", "engineering_experience_captures", ["superseded_by_capture_id"], unique=True, postgresql_where=sa.text("superseded_by_capture_id IS NOT NULL"))

    op.create_table(
        "engineering_experience_capture_outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("aggregate_version", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=96), nullable=False),
        sa.Column("schema_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("aggregate_version >= 1", name="ck_experience_capture_outbox_version"),
        sa.CheckConstraint("schema_version = 1", name="ck_experience_capture_outbox_schema_version"),
        sa.ForeignKeyConstraint(["aggregate_id"], ["engineering_experience_captures.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", name="uq_experience_capture_outbox_event"),
        sa.UniqueConstraint("aggregate_id", "aggregate_version", "event_type", name="uq_experience_capture_outbox_aggregate_event"),
    )

    op.create_table(
        "engineering_experience_capture_idempotency",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("command_type", sa.String(length=64), nullable=False),
        sa.Column("idempotency_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), server_default="pending", nullable=False),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('pending','completed')", name="ck_experience_capture_idempotency_status"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["aggregate_id"], ["engineering_experience_captures.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "actor_id", "command_type", "idempotency_id", name="uq_experience_capture_idempotency_scope"),
    )


def downgrade() -> None:
    op.drop_table("engineering_experience_capture_idempotency")
    op.drop_table("engineering_experience_capture_outbox")
    op.drop_table("engineering_experience_captures")
