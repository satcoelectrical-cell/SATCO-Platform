"""PATCH-056 derived engineering performance persistence.

Revision ID: e05600000001
Revises: e05600000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e05600000001"
down_revision = "e05600000000"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("engineering_performance_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("indicator_id", sa.String(64), nullable=False), sa.Column("indicator_version", sa.String(32), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False), sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False), sa.Column("source_cutoff", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_digest", sa.String(64), nullable=False), sa.Column("calculation_version", sa.String(32), nullable=False),
        sa.Column("observation_state", sa.String(24), nullable=False), sa.Column("value_json", postgresql.JSONB(), nullable=False),
        sa.Column("limitation_codes_json", postgresql.JSONB(), nullable=False), sa.Column("eligible_count", sa.Integer(), nullable=True),
        sa.Column("numerator", sa.Integer(), nullable=True), sa.Column("denominator", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("organization_id","project_id","workspace_id","indicator_id","indicator_version","window_start","window_end","source_digest","calculation_version",name="uq_eng_perf_snapshot_repro"),
        sa.CheckConstraint("observation_state IN ('complete','partial','indeterminate','not_applicable')",name="ck_eng_perf_snapshot_state"),
        sa.CheckConstraint("window_end >= window_start",name="ck_eng_perf_snapshot_window"),
        sa.CheckConstraint("eligible_count IS NULL OR eligible_count >= 0",name="ck_eng_perf_snapshot_eligible"))
    op.create_index("uq_eng_perf_snapshot_project_repro", "engineering_performance_snapshots", ["organization_id", "project_id", "indicator_id", "indicator_version", "window_start", "window_end", "source_digest", "calculation_version"], unique=True, postgresql_where=sa.text("workspace_id IS NULL"))
    op.create_table("engineering_next_action_projections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("action_key", sa.String(64), nullable=False), sa.Column("rule_id", sa.String(64), nullable=False), sa.Column("rule_version", sa.String(32), nullable=False),
        sa.Column("title_code", sa.String(128), nullable=False), sa.Column("rationale_codes_json", postgresql.JSONB(), nullable=False),
        sa.Column("supporting_handle_json", postgresql.JSONB(), nullable=False), sa.Column("limitation_codes_json", postgresql.JSONB(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False), sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("absent_recalculation_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("status", sa.String(32), nullable=False),
        sa.Column("superseded_by_action_key", sa.String(64), nullable=True), sa.Column("source_digest", sa.String(64), nullable=False),
        sa.Column("calculation_version", sa.String(32), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("organization_id","project_id","workspace_id","action_key",name="uq_eng_next_action_scope_key"),
        sa.CheckConstraint("status IN ('active','stale','superseded','resolved_by_source_state')",name="ck_eng_next_action_status"),
        sa.CheckConstraint("absent_recalculation_count >= 0",name="ck_eng_next_action_absent_count"),
        sa.CheckConstraint("last_seen_at >= first_seen_at",name="ck_eng_next_action_seen_order"))
    op.create_index("uq_eng_next_action_project_key", "engineering_next_action_projections", ["organization_id", "project_id", "action_key"], unique=True, postgresql_where=sa.text("workspace_id IS NULL"))

def downgrade():
    # Also accepts disposable databases upgraded by the pre-remediation e056 draft.
    op.execute("DROP INDEX IF EXISTS uq_eng_next_action_project_key")
    op.drop_table("engineering_next_action_projections")
    op.execute("DROP INDEX IF EXISTS uq_eng_perf_snapshot_project_repro")
    op.drop_table("engineering_performance_snapshots")
