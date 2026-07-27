"""create Context Relationships and Interface Commitments

Revision ID: b2022c0202f2
Revises: c2021f0c0a01
Create Date: 2026-07-27
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "b2022c0202f2"
down_revision: str | None = "c2021f0c0a01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "engineering_context_relationships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("relationship_key", sa.String(36), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("meaning", sa.String(32), nullable=False),
        sa.Column("purpose", sa.String(500), nullable=False),
        sa.Column("applicability", sa.Text(), nullable=True),
        sa.Column("source_role", sa.String(64), nullable=False),
        sa.Column("target_role", sa.String(64), nullable=False),
        sa.Column("source_kind", sa.String(32), nullable=False),
        sa.Column("source_context_id", sa.Integer(), nullable=True),
        sa.Column("source_project_id", sa.Integer(), nullable=True),
        sa.Column("source_workspace_id", sa.Integer(), nullable=True),
        sa.Column("source_discipline", sa.String(32), nullable=True),
        sa.Column("source_external_key", sa.String(255), nullable=True),
        sa.Column("target_kind", sa.String(32), nullable=False),
        sa.Column("target_context_id", sa.Integer(), nullable=True),
        sa.Column("target_project_id", sa.Integer(), nullable=True),
        sa.Column("target_workspace_id", sa.Integer(), nullable=True),
        sa.Column("target_discipline", sa.String(32), nullable=True),
        sa.Column("target_external_key", sa.String(255), nullable=True),
        sa.Column("steward_id", sa.Integer(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column(
            "lifecycle",
            sa.String(16),
            server_default="current",
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("withdrawal_reason", sa.Text(), nullable=True),
        sa.Column(
            "withdrawn_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
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
            "meaning IN ('requires', 'provided_by', 'consumed_by', "
            "'potentially_affects')",
            name="ck_context_relationships_meaning",
        ),
        sa.CheckConstraint(
            "lifecycle IN ('current', 'withdrawn')",
            name="ck_context_relationships_lifecycle",
        ),
        sa.CheckConstraint(
            "source_kind IN ('context', 'project', 'workspace', "
            "'discipline', 'external_source')",
            name="ck_context_relationships_source_kind",
        ),
        sa.CheckConstraint(
            "target_kind IN ('context', 'project', 'workspace', "
            "'discipline', 'external_source')",
            name="ck_context_relationships_target_kind",
        ),
        sa.CheckConstraint(
            "num_nonnulls(source_context_id, source_project_id, "
            "source_workspace_id, source_discipline, source_external_key) = 1",
            name="ck_context_relationships_source_target",
        ),
        sa.CheckConstraint(
            "(source_kind = 'context' AND source_context_id IS NOT NULL) OR "
            "(source_kind = 'project' AND source_project_id IS NOT NULL) OR "
            "(source_kind = 'workspace' AND source_workspace_id IS NOT NULL) "
            "OR (source_kind = 'discipline' "
            "AND source_discipline IS NOT NULL) OR "
            "(source_kind = 'external_source' "
            "AND source_external_key IS NOT NULL)",
            name="ck_context_relationships_source_kind_target",
        ),
        sa.CheckConstraint(
            "num_nonnulls(target_context_id, target_project_id, "
            "target_workspace_id, target_discipline, target_external_key) = 1",
            name="ck_context_relationships_target_target",
        ),
        sa.CheckConstraint(
            "(target_kind = 'context' AND target_context_id IS NOT NULL) OR "
            "(target_kind = 'project' AND target_project_id IS NOT NULL) OR "
            "(target_kind = 'workspace' AND target_workspace_id IS NOT NULL) "
            "OR (target_kind = 'discipline' "
            "AND target_discipline IS NOT NULL) OR "
            "(target_kind = 'external_source' "
            "AND target_external_key IS NOT NULL)",
            name="ck_context_relationships_target_kind_target",
        ),
        sa.CheckConstraint(
            "source_kind <> target_kind OR "
            "COALESCE(source_context_id, source_project_id, "
            "source_workspace_id, -1) <> "
            "COALESCE(target_context_id, target_project_id, "
            "target_workspace_id, -1) OR "
            "COALESCE(source_discipline, '') <> "
            "COALESCE(target_discipline, '') OR "
            "COALESCE(source_external_key, '') <> "
            "COALESCE(target_external_key, '')",
            name="ck_context_relationships_no_self_reference",
        ),
        sa.CheckConstraint(
            "version >= 1",
            name="ck_context_relationships_version",
        ),
        sa.CheckConstraint(
            "(lifecycle = 'current' AND withdrawn_at IS NULL "
            "AND withdrawal_reason IS NULL) OR "
            "(lifecycle = 'withdrawn' AND withdrawn_at IS NOT NULL "
            "AND withdrawal_reason IS NOT NULL)",
            name="ck_context_relationships_withdrawal",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_context_id"],
            ["engineering_contexts.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_project_id"],
            ["projects.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_workspace_id"],
            ["engineering_workspaces.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["target_context_id"],
            ["engineering_contexts.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["target_project_id"],
            ["projects.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["target_workspace_id"],
            ["engineering_workspaces.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["steward_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "relationship_key",
            name="uq_context_relationships_key",
        ),
    )
    op.create_index(
        "ix_context_relationships_project_lifecycle",
        "engineering_context_relationships",
        ["project_id", "lifecycle"],
    )
    op.create_index(
        "ix_context_relationships_source_workspace",
        "engineering_context_relationships",
        ["source_workspace_id"],
    )
    op.create_index(
        "ix_context_relationships_target_workspace",
        "engineering_context_relationships",
        ["target_workspace_id"],
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_context_relationships_governed_current "
        "ON engineering_context_relationships "
        "(project_id, meaning, purpose, source_kind, source_context_id, "
        "source_project_id, source_workspace_id, source_discipline, "
        "source_external_key, target_kind, target_context_id, "
        "target_project_id, target_workspace_id, target_discipline, "
        "target_external_key) NULLS NOT DISTINCT "
        "WHERE lifecycle = 'current'"
    )

    op.create_table(
        "interface_commitments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("commitment_key", sa.String(36), nullable=False),
        sa.Column("relationship_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("provider_kind", sa.String(32), nullable=False),
        sa.Column("provider_user_id", sa.Integer(), nullable=True),
        sa.Column("provider_workspace_id", sa.Integer(), nullable=True),
        sa.Column("provider_external_key", sa.String(255), nullable=True),
        sa.Column("consumer_workspace_id", sa.Integer(), nullable=False),
        sa.Column("required_information", sa.Text(), nullable=False),
        sa.Column("intended_use", sa.Text(), nullable=False),
        sa.Column("completeness_expectation", sa.Text(), nullable=False),
        sa.Column("expected_source_basis", sa.Text(), nullable=False),
        sa.Column("stage_or_due_condition", sa.Text(), nullable=False),
        sa.Column("criticality", sa.String(16), nullable=False),
        sa.Column("confidentiality", sa.String(32), nullable=False),
        sa.Column("steward_id", sa.Integer(), nullable=False),
        sa.Column("consumer_reviewer_id", sa.Integer(), nullable=False),
        sa.Column(
            "state",
            sa.String(40),
            server_default="identified",
            nullable=False,
        ),
        sa.Column("supplied_source_key", sa.String(255), nullable=True),
        sa.Column("supplied_revision", sa.String(128), nullable=True),
        sa.Column("fulfilment_use", sa.Text(), nullable=True),
        sa.Column("external_review_evidence", sa.String(255), nullable=True),
        sa.Column(
            "external_review_required",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("successor_commitment_id", sa.Integer(), nullable=True),
        sa.Column(
            "current_use",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column("withdrawal_reason", sa.Text(), nullable=True),
        sa.Column(
            "withdrawn_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "reassessment_needed",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("reassessment_trigger", sa.String(255), nullable=True),
        sa.Column("reassessment_reason", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
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
            "provider_kind IN ('user', 'workspace', 'external_source')",
            name="ck_interface_commitments_provider_kind",
        ),
        sa.CheckConstraint(
            "num_nonnulls(provider_user_id, provider_workspace_id, "
            "provider_external_key) = 1",
            name="ck_interface_commitments_provider_target",
        ),
        sa.CheckConstraint(
            "(provider_kind = 'user' AND provider_user_id IS NOT NULL) OR "
            "(provider_kind = 'workspace' "
            "AND provider_workspace_id IS NOT NULL) OR "
            "(provider_kind = 'external_source' "
            "AND provider_external_key IS NOT NULL)",
            name="ck_interface_commitments_provider_kind_target",
        ),
        sa.CheckConstraint(
            "state IN ('identified', 'acknowledged_by_provider', "
            "'information_provided', 'consumer_review_required', "
            "'fulfilled_for_stated_use', 'rejected', 'disputed', "
            "'superseded')",
            name="ck_interface_commitments_state",
        ),
        sa.CheckConstraint(
            "criticality IN ('routine', 'important', 'critical')",
            name="ck_interface_commitments_criticality",
        ),
        sa.CheckConstraint(
            "confidentiality IN ('project', 'workspace', 'restricted')",
            name="ck_interface_commitments_confidentiality",
        ),
        sa.CheckConstraint(
            "version >= 1",
            name="ck_interface_commitments_version",
        ),
        sa.CheckConstraint(
            "(current_use = true AND withdrawn_at IS NULL "
            "AND withdrawal_reason IS NULL) OR "
            "(current_use = false AND withdrawn_at IS NOT NULL "
            "AND withdrawal_reason IS NOT NULL)",
            name="ck_interface_commitments_withdrawal",
        ),
        sa.CheckConstraint(
            "(reassessment_needed = false "
            "AND reassessment_reason IS NULL "
            "AND reassessment_trigger IS NULL) OR "
            "(reassessment_needed = true "
            "AND reassessment_reason IS NOT NULL "
            "AND reassessment_trigger IS NOT NULL)",
            name="ck_interface_commitments_reassessment",
        ),
        sa.CheckConstraint(
            "state <> 'fulfilled_for_stated_use' "
            "OR (supplied_source_key IS NOT NULL "
            "AND supplied_revision IS NOT NULL "
            "AND fulfilment_use IS NOT NULL)",
            name="ck_interface_commitments_fulfilment",
        ),
        sa.CheckConstraint(
            "state <> 'fulfilled_for_stated_use' "
            "OR external_review_required = false "
            "OR external_review_evidence IS NOT NULL",
            name="ck_interface_commitments_review_evidence",
        ),
        sa.CheckConstraint(
            "btrim(required_information) <> '' "
            "AND btrim(intended_use) <> '' "
            "AND btrim(completeness_expectation) <> '' "
            "AND btrim(expected_source_basis) <> '' "
            "AND btrim(stage_or_due_condition) <> ''",
            name="ck_interface_commitments_required_contract",
        ),
        sa.CheckConstraint(
            "provider_workspace_id IS NULL "
            "OR provider_workspace_id <> consumer_workspace_id",
            name="ck_interface_commitments_distinct_workspaces",
        ),
        sa.ForeignKeyConstraint(
            ["relationship_id"],
            ["engineering_context_relationships.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["provider_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["provider_workspace_id"],
            ["engineering_workspaces.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["consumer_workspace_id"],
            ["engineering_workspaces.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["steward_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["consumer_reviewer_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["successor_commitment_id"],
            ["interface_commitments.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "commitment_key",
            name="uq_interface_commitments_key",
        ),
        sa.UniqueConstraint(
            "relationship_id",
            name="uq_interface_commitments_relationship",
        ),
    )
    op.create_index(
        "ix_interface_commitments_project_state",
        "interface_commitments",
        ["project_id", "state"],
    )
    op.create_index(
        "ix_interface_commitments_consumer_workspace",
        "interface_commitments",
        ["consumer_workspace_id"],
    )
    op.create_index(
        "ix_interface_commitments_provider_workspace",
        "interface_commitments",
        ["provider_workspace_id"],
    )
    op.execute(
        """
        CREATE FUNCTION validate_context_relationship_scope()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF NEW.source_project_id IS NOT NULL
             AND NEW.source_project_id <> NEW.project_id THEN
            RAISE EXCEPTION 'source Project is outside governing Project'
              USING ERRCODE = '23514';
          END IF;
          IF NEW.target_project_id IS NOT NULL
             AND NEW.target_project_id <> NEW.project_id THEN
            RAISE EXCEPTION 'target Project is outside governing Project'
              USING ERRCODE = '23514';
          END IF;
          IF NEW.source_workspace_id IS NOT NULL AND NOT EXISTS (
            SELECT 1 FROM engineering_workspaces
            WHERE id = NEW.source_workspace_id
              AND project_id = NEW.project_id
          ) THEN
            RAISE EXCEPTION 'source Workspace is outside governing Project'
              USING ERRCODE = '23514';
          END IF;
          IF NEW.target_workspace_id IS NOT NULL AND NOT EXISTS (
            SELECT 1 FROM engineering_workspaces
            WHERE id = NEW.target_workspace_id
              AND project_id = NEW.project_id
          ) THEN
            RAISE EXCEPTION 'target Workspace is outside governing Project'
              USING ERRCODE = '23514';
          END IF;
          IF NEW.source_context_id IS NOT NULL AND NOT EXISTS (
            SELECT 1 FROM engineering_contexts
            WHERE id = NEW.source_context_id
              AND project_id = NEW.project_id
          ) THEN
            RAISE EXCEPTION 'source Context is outside governing Project'
              USING ERRCODE = '23514';
          END IF;
          IF NEW.target_context_id IS NOT NULL AND NOT EXISTS (
            SELECT 1 FROM engineering_contexts
            WHERE id = NEW.target_context_id
              AND project_id = NEW.project_id
          ) THEN
            RAISE EXCEPTION 'target Context is outside governing Project'
              USING ERRCODE = '23514';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER trg_context_relationship_scope
        BEFORE INSERT OR UPDATE ON engineering_context_relationships
        FOR EACH ROW EXECUTE FUNCTION validate_context_relationship_scope();

        CREATE FUNCTION validate_interface_commitment_scope()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM engineering_context_relationships
            WHERE id = NEW.relationship_id
              AND project_id = NEW.project_id
          ) THEN
            RAISE EXCEPTION 'commitment relationship scope mismatch'
              USING ERRCODE = '23514';
          END IF;
          IF NOT EXISTS (
            SELECT 1 FROM engineering_workspaces
            WHERE id = NEW.consumer_workspace_id
              AND project_id = NEW.project_id
          ) THEN
            RAISE EXCEPTION 'consumer Workspace is outside governing Project'
              USING ERRCODE = '23514';
          END IF;
          IF NEW.provider_workspace_id IS NOT NULL AND NOT EXISTS (
            SELECT 1 FROM engineering_workspaces
            WHERE id = NEW.provider_workspace_id
              AND project_id = NEW.project_id
          ) THEN
            RAISE EXCEPTION 'provider Workspace is outside governing Project'
              USING ERRCODE = '23514';
          END IF;
          IF NOT EXISTS (
            SELECT 1 FROM users
            WHERE id = NEW.steward_id AND is_active = true
          ) OR NOT EXISTS (
            SELECT 1 FROM users
            WHERE id = NEW.consumer_reviewer_id AND is_active = true
          ) OR (
            NEW.provider_user_id IS NOT NULL AND NOT EXISTS (
              SELECT 1 FROM users
              WHERE id = NEW.provider_user_id AND is_active = true
            )
          ) THEN
            RAISE EXCEPTION 'commitment responsibility is not active'
              USING ERRCODE = '23514';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER trg_interface_commitment_scope
        BEFORE INSERT OR UPDATE ON interface_commitments
        FOR EACH ROW EXECUTE FUNCTION validate_interface_commitment_scope();
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS trg_interface_commitment_scope "
        "ON interface_commitments; "
        "DROP FUNCTION IF EXISTS validate_interface_commitment_scope(); "
        "DROP TRIGGER IF EXISTS trg_context_relationship_scope "
        "ON engineering_context_relationships; "
        "DROP FUNCTION IF EXISTS validate_context_relationship_scope();"
    )
    op.drop_index(
        "ix_interface_commitments_provider_workspace",
        table_name="interface_commitments",
    )
    op.drop_index(
        "ix_interface_commitments_consumer_workspace",
        table_name="interface_commitments",
    )
    op.drop_index(
        "ix_interface_commitments_project_state",
        table_name="interface_commitments",
    )
    op.drop_table("interface_commitments")
    op.drop_index(
        "ix_context_relationships_target_workspace",
        table_name="engineering_context_relationships",
    )
    op.execute(
        "DROP INDEX IF EXISTS uq_context_relationships_governed_current"
    )
    op.drop_index(
        "ix_context_relationships_source_workspace",
        table_name="engineering_context_relationships",
    )
    op.drop_index(
        "ix_context_relationships_project_lifecycle",
        table_name="engineering_context_relationships",
    )
    op.drop_table("engineering_context_relationships")
