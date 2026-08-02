"""create engineering_objects table

Revision ID: e02400000001
Revises: b2022c0202f2
Create Date: 2026-08-01
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e02400000001"
down_revision: str | None = "b2022c0202f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "engineering_objects",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("customer_id", sa.Integer(), nullable=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("family", sa.String(length=32), nullable=False),
        sa.Column("discipline", sa.String(length=32), nullable=False),
        sa.Column("object_type", sa.String(length=64), nullable=False),
        sa.Column("subtype", sa.String(length=64), nullable=True),
        sa.Column(
            "lifecycle",
            sa.String(length=16),
            server_default="proposed",
            nullable=False,
        ),
        sa.Column(
            "authority_standing",
            sa.String(length=16),
            server_default="draft",
            nullable=False,
        ),
        sa.Column(
            "version",
            sa.Integer(),
            server_default="1",
            nullable=False,
        ),
        sa.Column("creator_id", sa.Integer(), nullable=False),
        sa.Column("steward_id", sa.Integer(), nullable=False),
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
        sa.CheckConstraint(
            "family IN ('instrumentation', 'electrical', 'automation', "
            "'shared')",
            name="ck_engineering_objects_family",
        ),
        sa.CheckConstraint(
            "discipline IN ('instrumentation', 'electrical', "
            "'industrial_automation', 'shared_engineering')",
            name="ck_engineering_objects_discipline",
        ),
        sa.CheckConstraint(
            "object_type IN ('instrument', 'transmitter', 'analyzer', "
            "'flowmeter', 'control_valve', 'instrument_loop', "
            "'junction_box', 'instrument_panel', 'motor', 'transformer', "
            "'mcc', 'switchgear', 'electrical_panel', 'electrical_cable', "
            "'plc', 'dcs_controller', 'esd_controller', "
            "'control_cabinet', 'io_channel', 'hmi', 'control_logic', "
            "'project', 'vendor', 'requirement', 'standard', 'datasheet', "
            "'drawing', 'technical_decision')",
            name="ck_engineering_objects_object_type",
        ),
        sa.CheckConstraint(
            "(family = 'instrumentation' AND discipline = "
            "'instrumentation') OR (family = 'electrical' AND "
            "discipline = 'electrical') OR (family = 'automation' AND "
            "discipline = 'industrial_automation') OR (family = 'shared' "
            "AND discipline = 'shared_engineering')",
            name="ck_engineering_objects_family_discipline",
        ),
        sa.CheckConstraint(
            "(family = 'instrumentation' AND object_type IN ('analyzer', "
            "'control_valve', 'flowmeter', 'instrument', "
            "'instrument_loop', 'instrument_panel', 'junction_box', "
            "'transmitter')) OR (family = 'electrical' AND object_type IN "
            "('electrical_cable', 'electrical_panel', 'mcc', 'motor', "
            "'switchgear', 'transformer')) OR (family = 'automation' AND "
            "object_type IN ('control_cabinet', 'control_logic', "
            "'dcs_controller', 'esd_controller', 'hmi', 'io_channel', "
            "'plc')) OR (family = 'shared' AND object_type IN "
            "('datasheet', 'drawing', 'project', 'requirement', 'standard', "
            "'technical_decision', 'vendor'))",
            name="ck_engineering_objects_family_object_type",
        ),
        sa.CheckConstraint(
            "subtype IS NULL",
            name="ck_engineering_objects_subtype_v1",
        ),
        sa.CheckConstraint(
            "lifecycle IN ('proposed', 'active', 'superseded', "
            "'withdrawn', 'retired')",
            name="ck_engineering_objects_lifecycle",
        ),
        sa.CheckConstraint(
            "authority_standing IN ('draft', 'proposed', 'reviewed', "
            "'approved', 'disputed', 'rejected')",
            name="ck_engineering_objects_authority_standing",
        ),
        sa.CheckConstraint(
            "version >= 1",
            name="ck_engineering_objects_version",
        ),
        sa.CheckConstraint(
            "updated_at >= created_at",
            name="ck_engineering_objects_timestamp_order",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            name="fk_engineering_objects_customer_id_customers",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_engineering_objects_project_id_projects",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["engineering_workspaces.id"],
            name=(
                "fk_engineering_objects_workspace_id_"
                "engineering_workspaces"
            ),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["creator_id"],
            ["users.id"],
            name="fk_engineering_objects_creator_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["steward_id"],
            ["users.id"],
            name="fk_engineering_objects_steward_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_engineering_objects_organization_project",
        "engineering_objects",
        ["organization_id", "project_id"],
        unique=False,
    )
    op.create_index(
        "ix_engineering_objects_project_workspace",
        "engineering_objects",
        ["project_id", "workspace_id"],
        unique=False,
    )
    op.create_index(
        "ix_engineering_objects_classification",
        "engineering_objects",
        ["family", "discipline", "object_type"],
        unique=False,
    )
    op.create_index(
        "ix_engineering_objects_lifecycle_authority",
        "engineering_objects",
        ["lifecycle", "authority_standing"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_engineering_objects_lifecycle_authority",
        table_name="engineering_objects",
    )
    op.drop_index(
        "ix_engineering_objects_classification",
        table_name="engineering_objects",
    )
    op.drop_index(
        "ix_engineering_objects_project_workspace",
        table_name="engineering_objects",
    )
    op.drop_index(
        "ix_engineering_objects_organization_project",
        table_name="engineering_objects",
    )
    op.drop_table("engineering_objects")
