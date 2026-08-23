"""Project Definition, Scope, Inputs and Lifecycle Foundation.

Revision ID: e04400000001
Revises: e04300000001
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "e04400000001"
down_revision = "e04300000001"
branch_labels = None
depends_on = None


STAGES = "'definition','preparation','execution','verification','completion_readiness'"


def upgrade():
    op.create_table(
        "project_foundations",
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("purpose", sa.String(2000), nullable=False),
        sa.Column("engineering_basis", sa.String(5000), nullable=False),
        sa.Column("stage", sa.String(32), nullable=False, server_default="definition"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("established_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("established_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(btrim(purpose)) BETWEEN 1 AND 2000", name="ck_project_foundation_purpose"),
        sa.CheckConstraint("length(btrim(engineering_basis)) BETWEEN 1 AND 5000", name="ck_project_foundation_basis"),
        sa.CheckConstraint(f"stage IN ({STAGES})", name="ck_project_foundation_stage"),
        sa.CheckConstraint("version >= 1", name="ck_project_foundation_version"),
    )
    op.create_index("ix_project_foundation_scope", "project_foundations", ["organization_id", "project_id"])

    op.create_table(
        "project_scope_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("statement", sa.String(1000), nullable=False),
        sa.Column("ordinal", sa.SmallInteger(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('in_scope','out_of_scope')", name="ck_project_scope_kind"),
        sa.CheckConstraint("ordinal BETWEEN 0 AND 49", name="ck_project_scope_ordinal"),
        sa.CheckConstraint("length(btrim(statement)) BETWEEN 1 AND 1000", name="ck_project_scope_statement"),
        sa.UniqueConstraint("project_id", "kind", "ordinal", name="uq_project_scope_ordinal"),
    )
    op.create_index("ix_project_scope_order", "project_scope_items", ["organization_id", "project_id", "kind", "ordinal"])
    op.create_index("uq_project_scope_statement", "project_scope_items", ["project_id", "kind", sa.text("lower(btrim(statement))")], unique=True)

    op.create_table(
        "project_completion_criteria",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("statement", sa.String(1000), nullable=False),
        sa.Column("ordinal", sa.SmallInteger(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("ordinal BETWEEN 0 AND 49", name="ck_project_completion_ordinal"),
        sa.CheckConstraint("length(btrim(statement)) BETWEEN 1 AND 1000", name="ck_project_completion_statement"),
        sa.UniqueConstraint("project_id", "ordinal", name="uq_project_completion_ordinal"),
    )
    op.create_index("ix_project_completion_order", "project_completion_criteria", ["organization_id", "project_id", "ordinal"])
    op.create_index("uq_project_completion_statement", "project_completion_criteria", ["project_id", sa.text("lower(btrim(statement))")], unique=True)

    op.create_table(
        "project_required_inputs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.String(2000)),
        sa.Column("ordinal", sa.SmallInteger(), nullable=False),
        sa.Column("required_by_stage", sa.String(32), nullable=False),
        sa.Column("standing", sa.String(32), nullable=False, server_default="missing"),
        sa.Column("source_kind", sa.String(32)),
        sa.Column("source_id", postgresql.UUID(as_uuid=True)),
        sa.Column("source_version", sa.Integer()),
        sa.Column("source_workspace_id", sa.Integer(), sa.ForeignKey("engineering_workspaces.id", ondelete="RESTRICT")),
        sa.Column("standing_rationale", sa.String(2000), nullable=False),
        sa.Column("standing_changed_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("standing_changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(btrim(title)) BETWEEN 1 AND 200", name="ck_project_input_title"),
        sa.CheckConstraint("description IS NULL OR length(btrim(description)) BETWEEN 1 AND 2000", name="ck_project_input_description"),
        sa.CheckConstraint("ordinal BETWEEN 0 AND 99", name="ck_project_input_ordinal"),
        sa.CheckConstraint(f"required_by_stage IN ({STAGES})", name="ck_project_input_required_stage"),
        sa.CheckConstraint("standing IN ('missing','received','clarification_required','not_applicable')", name="ck_project_input_standing"),
        sa.CheckConstraint("version >= 1", name="ck_project_input_version"),
        sa.CheckConstraint("length(btrim(standing_rationale)) BETWEEN 1 AND 2000", name="ck_project_input_rationale"),
        sa.CheckConstraint("(standing='received' AND source_kind IN ('supporting_file','evidence') AND source_id IS NOT NULL AND source_version >= 1) OR (standing<>'received' AND source_kind IS NULL AND source_id IS NULL AND source_version IS NULL AND source_workspace_id IS NULL)", name="ck_project_input_source_pair"),
        sa.UniqueConstraint("project_id", "ordinal", name="uq_project_input_ordinal", deferrable=True, initially="DEFERRED"),
    )
    op.create_index("ix_project_input_order", "project_required_inputs", ["organization_id", "project_id", "ordinal", "id"])
    op.create_index("ix_project_input_source", "project_required_inputs", ["source_kind", "source_id"])
    op.create_index("uq_project_input_title", "project_required_inputs", ["project_id", sa.text("lower(btrim(title))")], unique=True)

    op.create_table(
        "project_stage_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("from_stage", sa.String(32)),
        sa.Column("to_stage", sa.String(32), nullable=False),
        sa.Column("foundation_version", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("rationale", sa.String(2000), nullable=False),
        sa.Column("transitioned_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(f"from_stage IS NULL OR from_stage IN ({STAGES})", name="ck_project_stage_history_from"),
        sa.CheckConstraint(f"to_stage IN ({STAGES})", name="ck_project_stage_history_to"),
        sa.CheckConstraint("foundation_version >= 1", name="ck_project_stage_history_version"),
        sa.CheckConstraint("length(btrim(rationale)) BETWEEN 1 AND 2000", name="ck_project_stage_history_rationale"),
        sa.UniqueConstraint("project_id", "foundation_version", name="uq_project_stage_history_version"),
    )
    op.create_index("ix_project_stage_history_order", "project_stage_history", ["organization_id", "project_id", "transitioned_at", "id"])

    op.execute("""
    CREATE FUNCTION satco_project_foundation_parent_guard() RETURNS trigger
    LANGUAGE plpgsql AS $$
    DECLARE parent_org uuid; parent_status text;
    BEGIN
      SELECT organization_id, status INTO parent_org, parent_status FROM projects WHERE id=NEW.project_id FOR SHARE;
      IF parent_org IS NULL OR NEW.organization_id IS DISTINCT FROM parent_org THEN
        RAISE EXCEPTION 'project foundation parent scope mismatch';
      END IF;
      IF parent_status IN ('completed','cancelled') THEN RAISE EXCEPTION 'project foundation parent is terminal'; END IF;
      IF TG_OP='UPDATE' AND (NEW.project_id IS DISTINCT FROM OLD.project_id OR NEW.organization_id IS DISTINCT FROM OLD.organization_id OR NEW.established_by_id IS DISTINCT FROM OLD.established_by_id OR NEW.established_at IS DISTINCT FROM OLD.established_at) THEN
        RAISE EXCEPTION 'project foundation identity is immutable';
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER trg_project_foundation_parent_guard BEFORE INSERT OR UPDATE ON project_foundations FOR EACH ROW EXECUTE FUNCTION satco_project_foundation_parent_guard();

    CREATE FUNCTION satco_project_foundation_child_guard() RETURNS trigger
    LANGUAGE plpgsql AS $$
    DECLARE parent_org uuid;
    BEGIN
      SELECT organization_id INTO parent_org FROM project_foundations WHERE project_id=NEW.project_id FOR SHARE;
      IF parent_org IS NULL OR NEW.organization_id IS DISTINCT FROM parent_org THEN RAISE EXCEPTION 'project foundation child scope mismatch'; END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER trg_project_scope_parent_guard BEFORE INSERT OR UPDATE ON project_scope_items FOR EACH ROW EXECUTE FUNCTION satco_project_foundation_child_guard();
    CREATE TRIGGER trg_project_completion_parent_guard BEFORE INSERT OR UPDATE ON project_completion_criteria FOR EACH ROW EXECUTE FUNCTION satco_project_foundation_child_guard();

    CREATE FUNCTION satco_project_input_guard() RETURNS trigger
    LANGUAGE plpgsql AS $$
    DECLARE parent_org uuid; source_org uuid; source_project integer; source_workspace integer; source_v integer; source_state text; workspace_project integer;
    BEGIN
      SELECT organization_id INTO parent_org FROM project_foundations WHERE project_id=NEW.project_id FOR SHARE;
      IF parent_org IS NULL OR NEW.organization_id IS DISTINCT FROM parent_org THEN RAISE EXCEPTION 'project input parent scope mismatch'; END IF;
      IF NEW.standing='received' THEN
        IF NEW.source_kind='supporting_file' THEN
          SELECT organization_id, project_id, workspace_id, version, lifecycle INTO source_org, source_project, source_workspace, source_v, source_state FROM supporting_file_assets WHERE id=NEW.source_id FOR SHARE;
          IF source_state IS DISTINCT FROM 'available' THEN RAISE EXCEPTION 'project input supporting file unavailable'; END IF;
        ELSIF NEW.source_kind='evidence' THEN
          SELECT organization_id, project_id, workspace_id, version, lifecycle INTO source_org, source_project, source_workspace, source_v, source_state FROM evidence WHERE id=NEW.source_id FOR SHARE;
          IF source_state IS DISTINCT FROM 'current' THEN RAISE EXCEPTION 'project input evidence unavailable'; END IF;
        ELSE RAISE EXCEPTION 'project input source kind unsupported';
        END IF;
        IF source_org IS DISTINCT FROM NEW.organization_id OR source_project IS DISTINCT FROM NEW.project_id OR source_workspace IS DISTINCT FROM NEW.source_workspace_id OR source_v IS DISTINCT FROM NEW.source_version THEN
          RAISE EXCEPTION 'project input source binding mismatch';
        END IF;
        IF source_workspace IS NOT NULL THEN
          SELECT project_id INTO workspace_project FROM engineering_workspaces WHERE id=source_workspace;
          IF workspace_project IS DISTINCT FROM NEW.project_id THEN RAISE EXCEPTION 'project input workspace mismatch'; END IF;
        END IF;
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER trg_project_input_guard BEFORE INSERT OR UPDATE ON project_required_inputs FOR EACH ROW EXECUTE FUNCTION satco_project_input_guard();

    CREATE FUNCTION satco_project_stage_history_guard() RETURNS trigger
    LANGUAGE plpgsql AS $$
    DECLARE root project_foundations%ROWTYPE; from_rank integer; to_rank integer;
    BEGIN
      IF TG_OP <> 'INSERT' THEN RAISE EXCEPTION 'project stage history is immutable'; END IF;
      SELECT * INTO root FROM project_foundations WHERE project_id=NEW.project_id FOR SHARE;
      IF root.project_id IS NULL OR root.organization_id IS DISTINCT FROM NEW.organization_id OR root.stage IS DISTINCT FROM NEW.to_stage OR root.version IS DISTINCT FROM NEW.foundation_version THEN
        RAISE EXCEPTION 'project stage history root mismatch';
      END IF;
      IF NEW.from_stage IS NULL THEN
        IF NEW.to_stage <> 'definition' OR NEW.foundation_version <> 1 THEN RAISE EXCEPTION 'invalid initial project stage history'; END IF;
      ELSE
        from_rank := array_position(ARRAY['definition','preparation','execution','verification','completion_readiness'], NEW.from_stage);
        to_rank := array_position(ARRAY['definition','preparation','execution','verification','completion_readiness'], NEW.to_stage);
        IF abs(from_rank-to_rank) <> 1 THEN RAISE EXCEPTION 'non-adjacent project stage history'; END IF;
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER trg_project_stage_history_guard BEFORE INSERT OR UPDATE OR DELETE ON project_stage_history FOR EACH ROW EXECUTE FUNCTION satco_project_stage_history_guard();

    ALTER TABLE project_foundations OWNER TO satco;
    ALTER TABLE project_scope_items OWNER TO satco;
    ALTER TABLE project_completion_criteria OWNER TO satco;
    ALTER TABLE project_required_inputs OWNER TO satco;
    ALTER TABLE project_stage_history OWNER TO satco;
    ALTER FUNCTION satco_project_foundation_parent_guard() OWNER TO satco;
    ALTER FUNCTION satco_project_foundation_child_guard() OWNER TO satco;
    ALTER FUNCTION satco_project_input_guard() OWNER TO satco;
    ALTER FUNCTION satco_project_stage_history_guard() OWNER TO satco;
    REVOKE ALL ON FUNCTION satco_project_foundation_parent_guard() FROM PUBLIC, satco_runtime;
    REVOKE ALL ON FUNCTION satco_project_foundation_child_guard() FROM PUBLIC, satco_runtime;
    REVOKE ALL ON FUNCTION satco_project_input_guard() FROM PUBLIC, satco_runtime;
    REVOKE ALL ON FUNCTION satco_project_stage_history_guard() FROM PUBLIC, satco_runtime;
    GRANT SELECT, INSERT, UPDATE ON project_foundations, project_required_inputs TO satco_runtime;
    GRANT SELECT, INSERT, UPDATE, DELETE ON project_scope_items, project_completion_criteria TO satco_runtime;
    GRANT SELECT, INSERT ON project_stage_history TO satco_runtime;
    """)


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS trg_project_stage_history_guard ON project_stage_history")
    op.execute("DROP TRIGGER IF EXISTS trg_project_input_guard ON project_required_inputs")
    op.execute("DROP TRIGGER IF EXISTS trg_project_completion_parent_guard ON project_completion_criteria")
    op.execute("DROP TRIGGER IF EXISTS trg_project_scope_parent_guard ON project_scope_items")
    op.execute("DROP TRIGGER IF EXISTS trg_project_foundation_parent_guard ON project_foundations")
    op.execute("DROP FUNCTION IF EXISTS satco_project_stage_history_guard()")
    op.execute("DROP FUNCTION IF EXISTS satco_project_input_guard()")
    op.execute("DROP FUNCTION IF EXISTS satco_project_foundation_child_guard()")
    op.execute("DROP FUNCTION IF EXISTS satco_project_foundation_parent_guard()")
    op.drop_index("ix_project_stage_history_order", table_name="project_stage_history")
    op.drop_table("project_stage_history")
    op.drop_index("uq_project_input_title", table_name="project_required_inputs")
    op.drop_index("ix_project_input_source", table_name="project_required_inputs")
    op.drop_index("ix_project_input_order", table_name="project_required_inputs")
    op.drop_table("project_required_inputs")
    op.drop_index("uq_project_completion_statement", table_name="project_completion_criteria")
    op.drop_index("ix_project_completion_order", table_name="project_completion_criteria")
    op.drop_table("project_completion_criteria")
    op.drop_index("uq_project_scope_statement", table_name="project_scope_items")
    op.drop_index("ix_project_scope_order", table_name="project_scope_items")
    op.drop_table("project_scope_items")
    op.drop_index("ix_project_foundation_scope", table_name="project_foundations")
    op.drop_table("project_foundations")
