"""Prospective exact-version Supporting File availability observations.

Revision ID: e05600000005
Revises: e05600000004
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e05600000005"
down_revision = "e05600000004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "supporting_file_availability_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("supporting_file_assets.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("engineering_workspaces.id", ondelete="RESTRICT")),
        sa.Column("object_version", sa.String(160), nullable=False),
        sa.Column("content_digest", sa.String(64), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("observed_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_kind", sa.String(32), nullable=False),
        sa.CheckConstraint("state IN ('available','unavailable')", name="ck_supporting_file_availability_state"),
        sa.UniqueConstraint("source_event_id", name="uq_supporting_file_availability_source_event"),
        sa.UniqueConstraint("asset_id", "observed_at", name="uq_supporting_file_availability_instant"),
    )
    op.create_index("ix_supporting_file_availability_history", "supporting_file_availability_observations", ["organization_id", "asset_id", "observed_at", "id"])
    op.execute("""
    CREATE FUNCTION satco_guard_supporting_file_availability() RETURNS trigger LANGUAGE plpgsql AS $$
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
    CREATE TRIGGER trg_supporting_file_availability_guard BEFORE INSERT OR UPDATE OR DELETE ON supporting_file_availability_observations FOR EACH ROW EXECUTE FUNCTION satco_guard_supporting_file_availability();
    GRANT SELECT, INSERT ON supporting_file_availability_observations TO satco_runtime;
    """)


def downgrade():
    if op.get_bind().execute(sa.text("SELECT EXISTS (SELECT 1 FROM supporting_file_availability_observations)")).scalar_one():
        raise RuntimeError("Cannot discard recorded Supporting File availability history")
    op.execute("DROP TRIGGER IF EXISTS trg_supporting_file_availability_guard ON supporting_file_availability_observations; DROP FUNCTION IF EXISTS satco_guard_supporting_file_availability()")
    op.drop_index("ix_supporting_file_availability_history", table_name="supporting_file_availability_observations")
    op.drop_table("supporting_file_availability_observations")
