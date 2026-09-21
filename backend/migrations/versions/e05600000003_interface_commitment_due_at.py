"""Canonical Interface Commitment explicit due-time evidence.

Revision ID: e05600000003
Revises: e05600000002
"""
from alembic import op
import sqlalchemy as sa

revision = "e05600000003"
down_revision = "e05600000002"
branch_labels = None
depends_on = None


def upgrade():
    # Existing rows remain NULL. No prose or lifecycle backfill is permitted.
    op.add_column("interface_commitments", sa.Column("due_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT EXISTS (SELECT 1 FROM interface_commitments WHERE due_at IS NOT NULL)")).scalar_one():
        raise RuntimeError("Cannot discard recorded canonical Interface Commitment due evidence")
    op.drop_column("interface_commitments", "due_at")
