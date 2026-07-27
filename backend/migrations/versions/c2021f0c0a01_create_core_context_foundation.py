"""create Core Context Foundation

Revision ID: c2021f0c0a01
Revises: a20c1e0201f0
Create Date: 2026-07-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c2021f0c0a01"
down_revision: Union[str, Sequence[str], None] = "a20c1e0201f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "engineering_contexts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("context_key", sa.String(length=36), nullable=False),
        sa.Column("kind", sa.String(length=48), nullable=False),
        sa.Column("scope", sa.String(length=16), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=True),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("steward_id", sa.Integer(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("authority", sa.String(length=32), nullable=False),
        sa.Column(
            "lifecycle",
            sa.String(length=16),
            server_default="current",
            nullable=False,
        ),
        sa.Column("purpose", sa.String(length=500), nullable=True),
        sa.Column(
            "version",
            sa.Integer(),
            server_default="1",
            nullable=False,
        ),
        sa.Column("withdrawal_reason", sa.Text(), nullable=True),
        sa.Column(
            "withdrawn_at",
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
            "kind IN ("
            "'subject_reference', 'qualified_fact', "
            "'qualified_engineering_value', 'assumption', "
            "'source_evidence_reference'"
            ")",
            name="ck_engineering_contexts_kind",
        ),
        sa.CheckConstraint(
            "scope IN ('project', 'workspace')",
            name="ck_engineering_contexts_scope",
        ),
        sa.CheckConstraint(
            "authority IN ("
            "'authoritative_fact', 'engineer_verified_fact', "
            "'assumption'"
            ")",
            name="ck_engineering_contexts_authority",
        ),
        sa.CheckConstraint(
            "lifecycle IN ('current', 'withdrawn')",
            name="ck_engineering_contexts_lifecycle",
        ),
        sa.CheckConstraint(
            "(scope = 'project' AND workspace_id IS NULL) OR "
            "(scope = 'workspace' AND workspace_id IS NOT NULL)",
            name="ck_engineering_contexts_scope_workspace",
        ),
        sa.CheckConstraint(
            "(kind = 'assumption' AND authority = 'assumption') OR "
            "(kind <> 'assumption' AND authority <> 'assumption')",
            name="ck_engineering_contexts_kind_authority",
        ),
        sa.CheckConstraint(
            "(lifecycle = 'withdrawn' AND withdrawn_at IS NOT NULL "
            "AND withdrawal_reason IS NOT NULL) OR "
            "(lifecycle = 'current' AND withdrawn_at IS NULL "
            "AND withdrawal_reason IS NULL)",
            name="ck_engineering_contexts_lifecycle_state",
        ),
        sa.CheckConstraint(
            "version >= 1",
            name="ck_engineering_contexts_version",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
            name="fk_engineering_contexts_created_by_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name="fk_engineering_contexts_owner_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_engineering_contexts_project_id_projects",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["steward_id"],
            ["users.id"],
            name="fk_engineering_contexts_steward_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["engineering_workspaces.id"],
            name=(
                "fk_engineering_contexts_workspace_id_"
                "engineering_workspaces"
            ),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_engineering_contexts",
        ),
        sa.UniqueConstraint(
            "context_key",
            name="uq_engineering_contexts_context_key",
        ),
    )
    op.create_index(
        "ix_engineering_contexts_owner_id",
        "engineering_contexts",
        ["owner_id"],
        unique=False,
    )
    op.create_index(
        "ix_engineering_contexts_project_lifecycle",
        "engineering_contexts",
        ["project_id", "lifecycle"],
        unique=False,
    )
    op.create_index(
        "ix_engineering_contexts_steward_id",
        "engineering_contexts",
        ["steward_id"],
        unique=False,
    )
    op.create_index(
        "ix_engineering_contexts_workspace_lifecycle",
        "engineering_contexts",
        ["workspace_id", "lifecycle"],
        unique=False,
    )

    op.create_table(
        "engineering_context_facts",
        sa.Column("context_id", sa.Integer(), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("uncertainty", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["context_id"],
            ["engineering_contexts.id"],
            name="fk_engineering_context_facts_context_id_contexts",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "context_id",
            name="pk_engineering_context_facts",
        ),
    )

    op.create_table(
        "engineering_context_values",
        sa.Column("context_id", sa.Integer(), nullable=False),
        sa.Column(
            "numeric_value",
            sa.Numeric(precision=30, scale=10),
            nullable=False,
        ),
        sa.Column("unit", sa.String(length=64), nullable=False),
        sa.Column(
            "quantity_type",
            sa.String(length=128),
            nullable=False,
        ),
        sa.Column(
            "tolerance_min",
            sa.Numeric(precision=30, scale=10),
            nullable=True,
        ),
        sa.Column(
            "tolerance_max",
            sa.Numeric(precision=30, scale=10),
            nullable=True,
        ),
        sa.Column(
            "range_min",
            sa.Numeric(precision=30, scale=10),
            nullable=True,
        ),
        sa.Column(
            "range_max",
            sa.Numeric(precision=30, scale=10),
            nullable=True,
        ),
        sa.Column("basis", sa.Text(), nullable=False),
        sa.Column(
            "condition_type",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column("condition", sa.Text(), nullable=False),
        sa.Column("uncertainty", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "range_min IS NULL OR range_max IS NULL "
            "OR range_min <= range_max",
            name="ck_engineering_context_values_value_range",
        ),
        sa.CheckConstraint(
            "tolerance_min IS NULL OR tolerance_max IS NULL "
            "OR tolerance_min <= tolerance_max",
            name="ck_engineering_context_values_tolerance_range",
        ),
        sa.ForeignKeyConstraint(
            ["context_id"],
            ["engineering_contexts.id"],
            name="fk_engineering_context_values_context_id_contexts",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "context_id",
            name="pk_engineering_context_values",
        ),
    )

    op.create_table(
        "engineering_context_assumptions",
        sa.Column("context_id", sa.Integer(), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("consequence", sa.Text(), nullable=False),
        sa.Column("confirmation_condition", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["context_id"],
            ["engineering_contexts.id"],
            name=(
                "fk_engineering_context_assumptions_"
                "context_id_contexts"
            ),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "context_id",
            name="pk_engineering_context_assumptions",
        ),
    )

    op.create_table(
        "engineering_context_subject_references",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("context_id", sa.Integer(), nullable=False),
        sa.Column(
            "subject_kind",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column("subject_project_id", sa.Integer(), nullable=True),
        sa.Column("subject_workspace_id", sa.Integer(), nullable=True),
        sa.Column("discipline", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "subject_kind IN ('project', 'workspace', 'discipline')",
            name="ck_engineering_context_subject_refs_kind",
        ),
        sa.CheckConstraint(
            "(subject_kind = 'project' "
            "AND subject_project_id IS NOT NULL "
            "AND subject_workspace_id IS NULL AND discipline IS NULL) OR "
            "(subject_kind = 'workspace' "
            "AND subject_project_id IS NULL "
            "AND subject_workspace_id IS NOT NULL AND discipline IS NULL) "
            "OR (subject_kind = 'discipline' "
            "AND subject_project_id IS NULL "
            "AND subject_workspace_id IS NULL AND discipline IS NOT NULL)",
            name="ck_engineering_context_subject_refs_target",
        ),
        sa.ForeignKeyConstraint(
            ["context_id"],
            ["engineering_contexts.id"],
            name=(
                "fk_engineering_context_subject_refs_"
                "context_id_contexts"
            ),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["subject_project_id"],
            ["projects.id"],
            name=(
                "fk_engineering_context_subject_refs_"
                "project_id_projects"
            ),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["subject_workspace_id"],
            ["engineering_workspaces.id"],
            name=(
                "fk_engineering_context_subject_refs_"
                "workspace_id_workspaces"
            ),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_engineering_context_subject_references",
        ),
        sa.UniqueConstraint(
            "context_id",
            "subject_kind",
            "subject_project_id",
            "subject_workspace_id",
            "discipline",
            name="uq_engineering_context_subject_refs_identity",
        ),
    )
    op.create_index(
        "ix_engineering_context_subject_refs_project_id",
        "engineering_context_subject_references",
        ["subject_project_id"],
        unique=False,
    )
    op.create_index(
        "ix_engineering_context_subject_refs_workspace_id",
        "engineering_context_subject_references",
        ["subject_workspace_id"],
        unique=False,
    )

    op.create_table(
        "engineering_context_source_references",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("context_id", sa.Integer(), nullable=False),
        sa.Column("source_kind", sa.String(length=48), nullable=False),
        sa.Column("source_key", sa.String(length=255), nullable=False),
        sa.Column("source_owner_id", sa.Integer(), nullable=True),
        sa.Column(
            "revision",
            sa.String(length=128),
            server_default="unrevisioned",
            nullable=False,
        ),
        sa.Column(
            "effective_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "observation_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "source_maturity",
            sa.String(length=128),
            nullable=True,
        ),
        sa.Column(
            "confidentiality",
            sa.String(length=32),
            server_default="project",
            nullable=False,
        ),
        sa.Column("applicability", sa.Text(), nullable=False),
        sa.Column("limitations", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "source_kind IN ("
            "'customer_document', 'contract', "
            "'approved_project_document', 'vendor_document', "
            "'site_survey', 'standard', 'calculation', "
            "'engineer_input', 'external_reference', "
            "'historical_project_evidence'"
            ")",
            name="ck_engineering_context_source_refs_kind",
        ),
        sa.CheckConstraint(
            "confidentiality IN ('project', 'workspace', 'restricted')",
            name="ck_engineering_context_source_refs_confidentiality",
        ),
        sa.CheckConstraint(
            "confidentiality <> 'restricted' "
            "OR source_owner_id IS NOT NULL",
            name="ck_engineering_context_source_refs_restricted_owner",
        ),
        sa.ForeignKeyConstraint(
            ["context_id"],
            ["engineering_contexts.id"],
            name=(
                "fk_engineering_context_source_refs_"
                "context_id_contexts"
            ),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_owner_id"],
            ["users.id"],
            name="fk_engineering_context_source_refs_owner_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_engineering_context_source_references",
        ),
        sa.UniqueConstraint(
            "context_id",
            "source_kind",
            "source_key",
            "revision",
            name="uq_engineering_context_source_refs_identity",
        ),
    )
    op.create_index(
        "ix_engineering_context_source_refs_owner_id",
        "engineering_context_source_references",
        ["source_owner_id"],
        unique=False,
    )
    op.create_index(
        "ix_engineering_context_source_refs_source_key",
        "engineering_context_source_references",
        ["source_key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_engineering_context_source_refs_source_key",
        table_name="engineering_context_source_references",
    )
    op.drop_index(
        "ix_engineering_context_source_refs_owner_id",
        table_name="engineering_context_source_references",
    )
    op.drop_table("engineering_context_source_references")

    op.drop_index(
        "ix_engineering_context_subject_refs_workspace_id",
        table_name="engineering_context_subject_references",
    )
    op.drop_index(
        "ix_engineering_context_subject_refs_project_id",
        table_name="engineering_context_subject_references",
    )
    op.drop_table("engineering_context_subject_references")

    op.drop_table("engineering_context_assumptions")
    op.drop_table("engineering_context_values")
    op.drop_table("engineering_context_facts")

    op.drop_index(
        "ix_engineering_contexts_workspace_lifecycle",
        table_name="engineering_contexts",
    )
    op.drop_index(
        "ix_engineering_contexts_steward_id",
        table_name="engineering_contexts",
    )
    op.drop_index(
        "ix_engineering_contexts_project_lifecycle",
        table_name="engineering_contexts",
    )
    op.drop_index(
        "ix_engineering_contexts_owner_id",
        table_name="engineering_contexts",
    )
    op.drop_table("engineering_contexts")
