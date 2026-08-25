"""Project risks, issues, decisions and change impacts.

Revision ID: e04700000001
Revises: e04600000001
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e04700000001"
down_revision = "e04600000001"
branch_labels = None
depends_on = None


def _root(name, standing):
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("engineering_workspaces.id", ondelete="RESTRICT")),
        sa.Column("standing", sa.String(16), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(f"standing IN ({standing})", name=f"ck_{name}_standing"),
        sa.CheckConstraint("version>=1", name=f"ck_{name}_version"),
    ]


def upgrade():
    op.create_table("project_risks", *_root("risk", "'open','treated','accepted','closed'"), sa.Column("statement", sa.String(2000), nullable=False), sa.Column("category", sa.String(80), nullable=False), sa.Column("likelihood", sa.String(16), nullable=False), sa.Column("impact", sa.String(16), nullable=False), sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT")), sa.Column("disposition", sa.String(2000)))
    op.create_table("project_issues", *_root("issue", "'open','resolved','closed'"), sa.Column("statement", sa.String(2000), nullable=False), sa.Column("observed_context", sa.String(4000), nullable=False), sa.Column("severity", sa.String(16), nullable=False), sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT")), sa.Column("disposition", sa.String(2000)))
    op.create_table("project_decisions", *_root("decision", "'draft','accepted','superseded'"), sa.Column("statement", sa.String(4000), nullable=False), sa.Column("rationale", sa.String(4000), nullable=False), sa.Column("alternatives", postgresql.JSONB()), sa.Column("predecessor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("project_decisions.id", ondelete="RESTRICT"), unique=True), sa.Column("accepted_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT")), sa.Column("accepted_at", sa.DateTime(timezone=True)))
    op.create_table("project_changes", *_root("change", "'recorded','confirmed','withdrawn'"), sa.Column("statement", sa.String(4000), nullable=False), sa.Column("rationale", sa.String(4000), nullable=False), sa.Column("predecessor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("project_changes.id", ondelete="RESTRICT"), unique=True), sa.Column("confirmed_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT")), sa.Column("confirmed_at", sa.DateTime(timezone=True)))
    op.create_table("project_change_impacts", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("change_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("project_changes.id", ondelete="RESTRICT"), nullable=False), sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False), sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False), sa.Column("target_kind", sa.String(32), nullable=False), sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("statement", sa.String(2000), nullable=False), sa.Column("standing", sa.String(16), nullable=False, server_default="potential"), sa.Column("confirmed_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT")), sa.Column("confirmed_at", sa.DateTime(timezone=True)), sa.UniqueConstraint("change_id", "target_kind", "target_id", name="uq_change_impact_target"))
    for table, column, parent in (("project_risk_history", "risk_id", "project_risks"), ("project_issue_history", "issue_id", "project_issues"), ("project_decision_history", "decision_id", "project_decisions"), ("project_change_history", "change_id", "project_changes")):
        op.create_table(table, sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column(column, postgresql.UUID(as_uuid=True), sa.ForeignKey(f"{parent}.id", ondelete="RESTRICT"), nullable=False), sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False), sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False), sa.Column("aggregate_version", sa.Integer(), nullable=False), sa.Column("event_type", sa.String(80), nullable=False), sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False), sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False), sa.CheckConstraint("aggregate_version>=1", name=f"ck_{table}_version"), sa.UniqueConstraint(column, "aggregate_version", name=f"uq_{table}_version"))
    op.create_table("project_control_idempotency", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False), sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False), sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False), sa.Column("operation", sa.String(48), nullable=False), sa.Column("idempotency_key", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("fingerprint", sa.String(64), nullable=False), sa.Column("replay_json", postgresql.JSONB(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.CheckConstraint("length(fingerprint)=64", name="ck_project_control_idempotency_fingerprint"), sa.CheckConstraint("length(replay_json::text)<=1024", name="ck_project_control_idempotency_size"), sa.UniqueConstraint("organization_id", "project_id", "actor_id", "operation", "idempotency_key", name="uq_project_control_idempotency"))
    op.create_table("project_control_outbox", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False), sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False), sa.Column("aggregate_kind", sa.String(16), nullable=False), sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("aggregate_version", sa.Integer(), nullable=False), sa.Column("event_type", sa.String(96), nullable=False), sa.Column("payload", postgresql.JSONB(), nullable=False), sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False), sa.CheckConstraint("aggregate_kind IN ('risk','issue','decision','change')", name="ck_project_control_outbox_kind"), sa.UniqueConstraint("event_id", name="uq_project_control_outbox_event"))
    for table in ("project_risks", "project_issues", "project_decisions", "project_changes", "project_change_impacts"):
        op.create_index(f"ix_{table}_scope", table, ["organization_id", "project_id", "id"])
    op.execute("""
CREATE FUNCTION satco_project_control_scope_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM projects p WHERE p.id=NEW.project_id AND p.organization_id=NEW.organization_id) THEN RAISE EXCEPTION 'project control scope mismatch'; END IF;
  RETURN NEW;
END $$;
CREATE FUNCTION satco_project_control_root_workspace_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.workspace_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM engineering_workspaces w WHERE w.id=NEW.workspace_id AND w.project_id=NEW.project_id) THEN RAISE EXCEPTION 'project control workspace mismatch'; END IF;
  RETURN NEW;
END $$;
CREATE FUNCTION satco_project_control_impact_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM project_changes c WHERE c.id=NEW.change_id AND c.organization_id=NEW.organization_id AND c.project_id=NEW.project_id) THEN RAISE EXCEPTION 'change impact scope mismatch'; END IF;
  RETURN NEW;
END $$;
CREATE FUNCTION satco_project_control_decision_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.predecessor_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM project_decisions d WHERE d.id=NEW.predecessor_id AND d.organization_id=NEW.organization_id AND d.project_id=NEW.project_id) THEN RAISE EXCEPTION 'decision predecessor scope mismatch'; END IF;
  RETURN NEW;
END $$;
CREATE FUNCTION satco_project_control_change_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.predecessor_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM project_changes c WHERE c.id=NEW.predecessor_id AND c.organization_id=NEW.organization_id AND c.project_id=NEW.project_id) THEN RAISE EXCEPTION 'change predecessor scope mismatch'; END IF;
  RETURN NEW;
END $$;
CREATE FUNCTION satco_project_control_history_scope_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE expected_organization uuid; expected_project integer;
BEGIN
  CASE TG_TABLE_NAME
    WHEN 'project_risk_history' THEN SELECT organization_id,project_id INTO expected_organization,expected_project FROM project_risks WHERE id=NEW.risk_id;
    WHEN 'project_issue_history' THEN SELECT organization_id,project_id INTO expected_organization,expected_project FROM project_issues WHERE id=NEW.issue_id;
    WHEN 'project_decision_history' THEN SELECT organization_id,project_id INTO expected_organization,expected_project FROM project_decisions WHERE id=NEW.decision_id;
    WHEN 'project_change_history' THEN SELECT organization_id,project_id INTO expected_organization,expected_project FROM project_changes WHERE id=NEW.change_id;
  END CASE;
  IF expected_organization IS NULL OR NEW.organization_id IS DISTINCT FROM expected_organization OR NEW.project_id IS DISTINCT FROM expected_project THEN RAISE EXCEPTION 'project control history scope mismatch'; END IF;
  RETURN NEW;
END $$;
CREATE FUNCTION satco_project_control_history_immutable() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'project control history is append-only'; END $$;
CREATE TRIGGER trg_project_risk_scope BEFORE INSERT OR UPDATE ON project_risks FOR EACH ROW EXECUTE FUNCTION satco_project_control_scope_guard();
CREATE TRIGGER trg_project_risk_workspace BEFORE INSERT OR UPDATE ON project_risks FOR EACH ROW EXECUTE FUNCTION satco_project_control_root_workspace_guard();
CREATE TRIGGER trg_project_issue_scope BEFORE INSERT OR UPDATE ON project_issues FOR EACH ROW EXECUTE FUNCTION satco_project_control_scope_guard();
CREATE TRIGGER trg_project_issue_workspace BEFORE INSERT OR UPDATE ON project_issues FOR EACH ROW EXECUTE FUNCTION satco_project_control_root_workspace_guard();
CREATE TRIGGER trg_project_decision_scope BEFORE INSERT OR UPDATE ON project_decisions FOR EACH ROW EXECUTE FUNCTION satco_project_control_scope_guard();
CREATE TRIGGER trg_project_decision_workspace BEFORE INSERT OR UPDATE ON project_decisions FOR EACH ROW EXECUTE FUNCTION satco_project_control_root_workspace_guard();
CREATE TRIGGER trg_project_decision_predecessor BEFORE INSERT OR UPDATE ON project_decisions FOR EACH ROW EXECUTE FUNCTION satco_project_control_decision_guard();
CREATE TRIGGER trg_project_change_scope BEFORE INSERT OR UPDATE ON project_changes FOR EACH ROW EXECUTE FUNCTION satco_project_control_scope_guard();
CREATE TRIGGER trg_project_change_workspace BEFORE INSERT OR UPDATE ON project_changes FOR EACH ROW EXECUTE FUNCTION satco_project_control_root_workspace_guard();
CREATE TRIGGER trg_project_change_predecessor BEFORE INSERT OR UPDATE ON project_changes FOR EACH ROW EXECUTE FUNCTION satco_project_control_change_guard();
CREATE TRIGGER trg_project_impact_scope BEFORE INSERT OR UPDATE ON project_change_impacts FOR EACH ROW EXECUTE FUNCTION satco_project_control_scope_guard();
CREATE TRIGGER trg_project_impact_change BEFORE INSERT OR UPDATE ON project_change_impacts FOR EACH ROW EXECUTE FUNCTION satco_project_control_impact_guard();
CREATE TRIGGER trg_project_idempotency_scope BEFORE INSERT OR UPDATE ON project_control_idempotency FOR EACH ROW EXECUTE FUNCTION satco_project_control_scope_guard();
CREATE TRIGGER trg_project_outbox_scope BEFORE INSERT OR UPDATE ON project_control_outbox FOR EACH ROW EXECUTE FUNCTION satco_project_control_scope_guard();
CREATE TRIGGER trg_project_risk_history_scope BEFORE INSERT ON project_risk_history FOR EACH ROW EXECUTE FUNCTION satco_project_control_history_scope_guard();
CREATE TRIGGER trg_project_issue_history_scope BEFORE INSERT ON project_issue_history FOR EACH ROW EXECUTE FUNCTION satco_project_control_history_scope_guard();
CREATE TRIGGER trg_project_decision_history_scope BEFORE INSERT ON project_decision_history FOR EACH ROW EXECUTE FUNCTION satco_project_control_history_scope_guard();
CREATE TRIGGER trg_project_change_history_scope BEFORE INSERT ON project_change_history FOR EACH ROW EXECUTE FUNCTION satco_project_control_history_scope_guard();
CREATE TRIGGER trg_project_risk_history_immutable BEFORE UPDATE OR DELETE ON project_risk_history FOR EACH ROW EXECUTE FUNCTION satco_project_control_history_immutable();
CREATE TRIGGER trg_project_issue_history_immutable BEFORE UPDATE OR DELETE ON project_issue_history FOR EACH ROW EXECUTE FUNCTION satco_project_control_history_immutable();
CREATE TRIGGER trg_project_decision_history_immutable BEFORE UPDATE OR DELETE ON project_decision_history FOR EACH ROW EXECUTE FUNCTION satco_project_control_history_immutable();
CREATE TRIGGER trg_project_change_history_immutable BEFORE UPDATE OR DELETE ON project_change_history FOR EACH ROW EXECUTE FUNCTION satco_project_control_history_immutable();
""")


def downgrade():
    op.execute("DROP FUNCTION IF EXISTS satco_project_control_history_immutable() CASCADE; DROP FUNCTION IF EXISTS satco_project_control_history_scope_guard() CASCADE; DROP FUNCTION IF EXISTS satco_project_control_change_guard() CASCADE; DROP FUNCTION IF EXISTS satco_project_control_decision_guard() CASCADE; DROP FUNCTION IF EXISTS satco_project_control_impact_guard() CASCADE; DROP FUNCTION IF EXISTS satco_project_control_root_workspace_guard() CASCADE; DROP FUNCTION IF EXISTS satco_project_control_scope_guard() CASCADE")
    op.drop_table("project_control_outbox")
    op.drop_table("project_control_idempotency")
    for table in ("project_change_history", "project_decision_history", "project_issue_history", "project_risk_history"):
        op.drop_table(table)
    for table in ("project_change_impacts", "project_changes", "project_decisions", "project_issues", "project_risks"):
        op.drop_table(table)
