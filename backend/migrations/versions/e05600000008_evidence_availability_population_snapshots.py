"""Owner-issued bounded Evidence availability population snapshots.

Revision ID: e05600000008
Revises: e05600000007
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e05600000008"
down_revision = "e05600000007"
branch_labels = None
depends_on = None


def upgrade():
    op.create_check_constraint("ck_eng_perf_snapshot_actor", "engineering_performance_snapshots", "actor_id >= 0")
    op.create_check_constraint("ck_eng_perf_snapshot_reason", "engineering_performance_snapshots", "recomputation_reason IN ('legacy_unclassified','request_calculation')")
    op.create_check_constraint("ck_eng_next_action_actor", "engineering_next_action_projections", "actor_id >= 0")
    op.create_table(
        "supporting_file_availability_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("engineering_workspaces.id", ondelete="RESTRICT")),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_cutoff", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="incomplete"),
        sa.Column("method_version", sa.String(32), nullable=False, server_default="evidence-availability.v1"),
        sa.Column("limitation_codes", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('incomplete','complete')", name="ck_supporting_file_availability_snapshot_status"),
        sa.CheckConstraint("(status='complete' AND completed_at IS NOT NULL) OR status='incomplete'", name="ck_supporting_file_availability_snapshot_completion"),
    )
    op.create_index(
        "ix_supporting_file_availability_snapshot_scope",
        "supporting_file_availability_snapshots",
        ["organization_id", "project_id", "workspace_id", "actor_id", "source_cutoff", "id"],
    )
    op.add_column("supporting_file_availability_observations", sa.Column(
        "snapshot_id", postgresql.UUID(as_uuid=True),
        sa.ForeignKey("supporting_file_availability_snapshots.id", ondelete="RESTRICT"),
    ))
    op.add_column("supporting_file_availability_observations", sa.Column(
        "checked_at", sa.DateTime(timezone=True),
    ))
    op.drop_constraint(
        "uq_supporting_file_availability_instant",
        "supporting_file_availability_observations", type_="unique",
    )
    op.create_unique_constraint(
        "uq_supporting_file_availability_snapshot_asset",
        "supporting_file_availability_observations", ["snapshot_id", "asset_id"],
    )
    op.create_index(
        "uq_supporting_file_availability_legacy_instant",
        "supporting_file_availability_observations", ["asset_id", "observed_at"],
        unique=True, postgresql_where=sa.text("snapshot_id IS NULL"),
    )
    op.create_table(
        "evidence_availability_snapshot_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("supporting_file_availability_snapshots.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("evidence.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("evidence_version", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer()),
        sa.Column("workspace_id", sa.Integer()),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("artifact_versions", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("source_event_ids", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("limitation_codes", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.UniqueConstraint("snapshot_id", "evidence_id", name="uq_evidence_availability_snapshot_item"),
        sa.CheckConstraint("evidence_version >= 1", name="ck_evidence_availability_snapshot_item_version"),
        sa.CheckConstraint("state IN ('available','unavailable','indeterminate')", name="ck_evidence_availability_snapshot_item_state"),
    )
    op.create_index(
        "ix_evidence_availability_snapshot_items",
        "evidence_availability_snapshot_items", ["snapshot_id", "evidence_id"],
    )
    op.execute("""
    CREATE OR REPLACE FUNCTION satco_guard_supporting_file_availability() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE exact_asset supporting_file_assets%ROWTYPE;
    DECLARE batch supporting_file_availability_snapshots%ROWTYPE;
    BEGIN
      IF TG_OP <> 'INSERT' THEN RAISE EXCEPTION 'supporting file availability history is immutable'; END IF;
      SELECT * INTO exact_asset FROM supporting_file_assets WHERE id = NEW.asset_id FOR SHARE;
      IF exact_asset.id IS NULL
         OR NEW.organization_id IS DISTINCT FROM exact_asset.organization_id
         OR NEW.project_id IS DISTINCT FROM exact_asset.project_id
         OR NEW.workspace_id IS DISTINCT FROM exact_asset.workspace_id
         OR NEW.object_version IS DISTINCT FROM exact_asset.object_version
         OR NEW.content_digest IS DISTINCT FROM exact_asset.content_digest
         OR NEW.source_kind <> 'exact_object_head'
         OR NEW.observed_at < exact_asset.uploaded_at
         OR (NEW.checked_at IS NOT NULL AND NEW.checked_at < NEW.observed_at) THEN
        RAISE EXCEPTION 'supporting file availability basis is invalid';
      END IF;
      IF NEW.snapshot_id IS NOT NULL THEN
        SELECT * INTO batch FROM supporting_file_availability_snapshots WHERE id = NEW.snapshot_id FOR SHARE;
        IF batch.id IS NULL OR batch.status <> 'incomplete'
           OR batch.organization_id IS DISTINCT FROM NEW.organization_id
           OR batch.project_id IS DISTINCT FROM NEW.project_id
           OR batch.actor_id IS DISTINCT FROM NEW.observed_by_id
           OR batch.source_cutoff IS DISTINCT FROM NEW.observed_at
           OR NEW.checked_at IS NULL THEN
          RAISE EXCEPTION 'supporting file availability snapshot basis is invalid';
        END IF;
      END IF;
      RETURN NEW;
    END $$;
    CREATE FUNCTION satco_guard_availability_snapshot() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'availability snapshots cannot be deleted'; END IF;
      IF TG_OP = 'INSERT' THEN
        IF NEW.status <> 'incomplete' OR NEW.completed_at IS NOT NULL THEN
          RAISE EXCEPTION 'availability snapshot must start incomplete';
        END IF;
        RETURN NEW;
      END IF;
      IF OLD.status <> 'incomplete'
         OR NEW.id IS DISTINCT FROM OLD.id
         OR NEW.organization_id IS DISTINCT FROM OLD.organization_id
         OR NEW.project_id IS DISTINCT FROM OLD.project_id
         OR NEW.workspace_id IS DISTINCT FROM OLD.workspace_id
         OR NEW.actor_id IS DISTINCT FROM OLD.actor_id
         OR NEW.source_cutoff IS DISTINCT FROM OLD.source_cutoff
         OR NEW.method_version IS DISTINCT FROM OLD.method_version
         OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
        RAISE EXCEPTION 'availability snapshot identity is immutable';
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER trg_supporting_file_availability_snapshot_guard
      BEFORE INSERT OR UPDATE OR DELETE ON supporting_file_availability_snapshots
      FOR EACH ROW EXECUTE FUNCTION satco_guard_availability_snapshot();
    CREATE FUNCTION satco_guard_evidence_availability_snapshot_item() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE batch supporting_file_availability_snapshots%ROWTYPE;
    DECLARE evidence_row evidence%ROWTYPE;
    BEGIN
      IF TG_OP <> 'INSERT' THEN RAISE EXCEPTION 'availability snapshot items are immutable'; END IF;
      SELECT * INTO batch FROM supporting_file_availability_snapshots WHERE id=NEW.snapshot_id FOR SHARE;
      SELECT * INTO evidence_row FROM evidence WHERE id=NEW.evidence_id FOR SHARE;
      IF batch.id IS NULL OR batch.status <> 'incomplete' OR evidence_row.id IS NULL
         OR evidence_row.organization_id IS DISTINCT FROM batch.organization_id
         OR evidence_row.version IS DISTINCT FROM NEW.evidence_version
         OR evidence_row.project_id IS DISTINCT FROM NEW.project_id
         OR evidence_row.workspace_id IS DISTINCT FROM NEW.workspace_id THEN
        RAISE EXCEPTION 'availability snapshot item basis is invalid';
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER trg_evidence_availability_snapshot_item_guard
      BEFORE INSERT OR UPDATE OR DELETE ON evidence_availability_snapshot_items
      FOR EACH ROW EXECUTE FUNCTION satco_guard_evidence_availability_snapshot_item();
    GRANT SELECT, INSERT, UPDATE ON supporting_file_availability_snapshots TO satco_runtime;
    GRANT SELECT, INSERT ON evidence_availability_snapshot_items TO satco_runtime;
    GRANT SELECT, INSERT ON engineering_performance_snapshots TO satco_runtime;
    GRANT SELECT, INSERT, UPDATE ON engineering_next_action_projections TO satco_runtime;
    """)


def downgrade():
    if op.get_bind().execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM supporting_file_availability_snapshots)"
    )).scalar_one():
        raise RuntimeError("Cannot discard Evidence availability population snapshots")
    op.execute("REVOKE ALL ON engineering_performance_snapshots, engineering_next_action_projections FROM satco_runtime")
    op.drop_constraint("ck_eng_next_action_actor", "engineering_next_action_projections")
    op.drop_constraint("ck_eng_perf_snapshot_reason", "engineering_performance_snapshots")
    op.drop_constraint("ck_eng_perf_snapshot_actor", "engineering_performance_snapshots")
    op.execute("""
    DROP TRIGGER IF EXISTS trg_evidence_availability_snapshot_item_guard ON evidence_availability_snapshot_items;
    DROP FUNCTION IF EXISTS satco_guard_evidence_availability_snapshot_item();
    DROP TRIGGER IF EXISTS trg_supporting_file_availability_snapshot_guard ON supporting_file_availability_snapshots;
    DROP FUNCTION IF EXISTS satco_guard_availability_snapshot();
    CREATE OR REPLACE FUNCTION satco_guard_supporting_file_availability() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE exact_asset supporting_file_assets%ROWTYPE;
    BEGIN
      IF TG_OP <> 'INSERT' THEN RAISE EXCEPTION 'supporting file availability history is immutable'; END IF;
      SELECT * INTO exact_asset FROM supporting_file_assets WHERE id = NEW.asset_id FOR SHARE;
      IF exact_asset.id IS NULL
         OR NEW.organization_id IS DISTINCT FROM exact_asset.organization_id
         OR NEW.project_id IS DISTINCT FROM exact_asset.project_id
         OR NEW.workspace_id IS DISTINCT FROM exact_asset.workspace_id
         OR NEW.object_version IS DISTINCT FROM exact_asset.object_version
         OR NEW.content_digest IS DISTINCT FROM exact_asset.content_digest
         OR NEW.source_kind <> 'exact_object_head'
         OR NEW.observed_at < exact_asset.uploaded_at THEN
        RAISE EXCEPTION 'supporting file availability basis is invalid';
      END IF;
      RETURN NEW;
    END $$;
    """)
    op.drop_index("ix_evidence_availability_snapshot_items", table_name="evidence_availability_snapshot_items")
    op.drop_table("evidence_availability_snapshot_items")
    op.drop_index("uq_supporting_file_availability_legacy_instant", table_name="supporting_file_availability_observations")
    op.drop_constraint("uq_supporting_file_availability_snapshot_asset", "supporting_file_availability_observations", type_="unique")
    op.create_unique_constraint(
        "uq_supporting_file_availability_instant",
        "supporting_file_availability_observations", ["asset_id", "observed_at"],
    )
    op.drop_column("supporting_file_availability_observations", "checked_at")
    op.drop_column("supporting_file_availability_observations", "snapshot_id")
    op.drop_index("ix_supporting_file_availability_snapshot_scope", table_name="supporting_file_availability_snapshots")
    op.drop_table("supporting_file_availability_snapshots")
