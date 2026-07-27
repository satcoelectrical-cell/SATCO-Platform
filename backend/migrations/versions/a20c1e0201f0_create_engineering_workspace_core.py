"""create Engineering Workspace Core

Revision ID: a20c1e0201f0
Revises: f18a1c0e2026
Create Date: 2026-07-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a20c1e0201f0"
down_revision: Union[str, Sequence[str], None] = "f18a1c0e2026"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "engineering_workspaces",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column(
            "discipline",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default=sa.text("'draft'"),
            nullable=False,
        ),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column(
            "primary_assignee_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column(
            "version",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column(
            "archived_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "discipline IN ("
            "'electrical', "
            "'instrumentation', "
            "'control', "
            "'mechanical', "
            "'civil', "
            "'process'"
            ")",
            name="ck_engineering_workspaces_discipline",
        ),
        sa.CheckConstraint(
            "status IN ("
            "'draft', "
            "'active', "
            "'on_hold', "
            "'under_review', "
            "'completed', "
            "'archived'"
            ")",
            name="ck_engineering_workspaces_status",
        ),
        sa.CheckConstraint(
            "version >= 1",
            name="ck_engineering_workspaces_version",
        ),
        sa.CheckConstraint(
            "(status = 'archived' AND archived_at IS NOT NULL) OR "
            "(status <> 'archived' AND archived_at IS NULL)",
            name="ck_engineering_workspaces_archive_state",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_engineering_workspaces_project_id_projects",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name="fk_engineering_workspaces_owner_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["primary_assignee_id"],
            ["users.id"],
            name=(
                "fk_engineering_workspaces_"
                "primary_assignee_id_users"
            ),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
            name="fk_engineering_workspaces_created_by_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_engineering_workspaces",
        ),
        sa.UniqueConstraint(
            "project_id",
            "discipline",
            name=(
                "uq_engineering_workspaces_"
                "project_discipline"
            ),
        ),
    )
    op.create_index(
        "ix_engineering_workspaces_project_status",
        "engineering_workspaces",
        ["project_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_engineering_workspaces_owner_id",
        "engineering_workspaces",
        ["owner_id"],
        unique=False,
    )
    op.create_index(
        "ix_engineering_workspaces_primary_assignee_id",
        "engineering_workspaces",
        ["primary_assignee_id"],
        unique=False,
    )
    op.create_index(
        "ix_engineering_workspaces_status",
        "engineering_workspaces",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_engineering_workspaces_updated_at",
        "engineering_workspaces",
        ["updated_at"],
        unique=False,
    )

    op.create_table(
        "engineering_workspace_members",
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("added_by_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["engineering_workspaces.id"],
            name="fk_ew_members_workspace_id_workspaces",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=(
                "fk_engineering_workspace_members_"
                "user_id_users"
            ),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["added_by_id"],
            ["users.id"],
            name=(
                "fk_engineering_workspace_members_"
                "added_by_id_users"
            ),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "workspace_id",
            "user_id",
            name="pk_engineering_workspace_members",
        ),
    )
    op.create_index(
        "ix_engineering_workspace_members_user_id",
        "engineering_workspace_members",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_engineering_workspace_members_added_by_id",
        "engineering_workspace_members",
        ["added_by_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_engineering_workspace_members_added_by_id",
        table_name="engineering_workspace_members",
    )
    op.drop_index(
        "ix_engineering_workspace_members_user_id",
        table_name="engineering_workspace_members",
    )
    op.drop_table("engineering_workspace_members")

    op.drop_index(
        "ix_engineering_workspaces_updated_at",
        table_name="engineering_workspaces",
    )
    op.drop_index(
        "ix_engineering_workspaces_status",
        table_name="engineering_workspaces",
    )
    op.drop_index(
        "ix_engineering_workspaces_primary_assignee_id",
        table_name="engineering_workspaces",
    )
    op.drop_index(
        "ix_engineering_workspaces_owner_id",
        table_name="engineering_workspaces",
    )
    op.drop_index(
        "ix_engineering_workspaces_project_status",
        table_name="engineering_workspaces",
    )
    op.drop_table("engineering_workspaces")
