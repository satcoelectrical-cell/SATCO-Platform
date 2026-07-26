"""create projects table

Revision ID: d25733017b10
Revises: 
Create Date: 2026-07-23 13:34:32.234675

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd25733017b10'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the root identity and legacy Project schema."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="users_pkey"),
    )
    op.create_index(
        "ix_users_id",
        "users",
        ["id"],
    )
    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
    )
    op.create_index(
        "ix_users_username",
        "users",
        ["username"],
        unique=True,
    )

    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("customer", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="projects_pkey"),
    )
    op.create_index(
        "ix_projects_id",
        "projects",
        ["id"],
    )


def downgrade() -> None:
    """Drop the root legacy Project and identity schema."""
    op.drop_index(
        "ix_projects_id",
        table_name="projects",
    )
    op.drop_table("projects")

    op.drop_index(
        "ix_users_username",
        table_name="users",
    )
    op.drop_index(
        "ix_users_email",
        table_name="users",
    )
    op.drop_index(
        "ix_users_id",
        table_name="users",
    )
    op.drop_table("users")
