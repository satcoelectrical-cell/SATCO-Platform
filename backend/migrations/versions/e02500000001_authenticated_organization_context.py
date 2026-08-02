"""add authenticated Organization context

Revision ID: e02500000001
Revises: e02300000001
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e02500000001"
down_revision: str | None = "e02300000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), server_default="true", nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user_organization_memberships",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "is_enabled", sa.Boolean(), server_default="true", nullable=False
        ),
        sa.Column(
            "is_selected", sa.Boolean(), server_default="false", nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.CheckConstraint(
            "NOT is_selected OR is_enabled",
            name="ck_user_org_memberships_selected_enabled",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("user_id", "organization_id"),
    )
    op.create_index(
        "uq_user_org_memberships_selected_user",
        "user_organization_memberships",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("is_selected"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_user_org_memberships_selected_user",
        table_name="user_organization_memberships",
    )
    op.drop_table("user_organization_memberships")
    op.drop_table("organizations")
