"""add EngineeringObject atomic command persistence

Revision ID: e02300000001
Revises: e02400000001
"""

from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e02300000001"
down_revision: str | None = "e02400000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "audit_logs",
        sa.Column("entity_uuid", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_table(
        "engineering_object_outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "aggregate_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("aggregate_version", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(96), nullable=False),
        sa.Column("schema_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "aggregate_version >= 1",
            name="ck_eo_outbox_version",
        ),
        sa.ForeignKeyConstraint(
            ["aggregate_id"],
            ["engineering_objects.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", name="uq_eo_outbox_event_id"),
    )
    op.create_table(
        "engineering_object_idempotency",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("command_type", sa.String(64), nullable=False),
        sa.Column(
            "idempotency_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), server_default="pending", nullable=False),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'completed')",
            name="ck_eo_idempotency_status",
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"], ["users.id"], ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["aggregate_id"], ["engineering_objects.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "actor_id", "command_type", "idempotency_id",
            name="uq_eo_idempotency_scope",
        ),
    )


def downgrade() -> None:
    op.drop_table("engineering_object_idempotency")
    op.drop_table("engineering_object_outbox")
    op.drop_column("audit_logs", "entity_uuid")
