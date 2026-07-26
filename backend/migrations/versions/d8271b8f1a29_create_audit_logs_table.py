"""create audit logs table

Revision ID: d8271b8f1a29
Revises: b969ae9217a0
Create Date: 2026-07-25 08:06:40.174435

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd8271b8f1a29'
down_revision: Union[str, Sequence[str], None] = 'b969ae9217a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("entity", sa.String(), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("details", postgresql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_audit_logs_id",
        "audit_logs",
        ["id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_audit_logs_id",
        table_name="audit_logs",
    )
    op.drop_table("audit_logs")
