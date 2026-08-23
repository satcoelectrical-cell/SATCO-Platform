"""Governed Supporting File Evidence Intake.

Revision ID: e04300000001
Revises: e04100000001
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e04300000001"
down_revision = "e04100000001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "supporting_file_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("engineering_workspaces.id", ondelete="RESTRICT")),
        sa.Column("safe_filename", sa.String(255), nullable=False),
        sa.Column("safe_ascii_filename", sa.String(120), nullable=False),
        sa.Column("media_type", sa.String(128), nullable=False),
        sa.Column("byte_size", sa.BigInteger(), nullable=False),
        sa.Column("digest_algorithm", sa.String(16), nullable=False, server_default="sha256"),
        sa.Column("content_digest", sa.String(64), nullable=False),
        sa.Column("storage_key", sa.String(80), nullable=False),
        sa.Column("object_version", sa.String(160), nullable=False),
        sa.Column("uploader_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("lifecycle", sa.String(16), nullable=False, server_default="quarantined"),
        sa.Column("predecessor_asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("supporting_file_assets.id", ondelete="RESTRICT")),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scan_requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scanned_at", sa.DateTime(timezone=True)),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True)),
        sa.Column("withdrawn_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("withdrawal_reason_code", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("storage_key", name="uq_supporting_file_storage_key"),
        sa.CheckConstraint("byte_size BETWEEN 1 AND 26214400", name="ck_supporting_file_size"),
        sa.CheckConstraint("version >= 1", name="ck_supporting_file_version"),
        sa.CheckConstraint("lifecycle IN ('quarantined','available','rejected','withdrawn')", name="ck_supporting_file_lifecycle"),
        sa.CheckConstraint("digest_algorithm='sha256' AND content_digest ~ '^[0-9a-f]{64}$'", name="ck_supporting_file_digest"),
        sa.CheckConstraint("storage_key ~ '^objects/[0-9a-f]{64}$'", name="ck_supporting_file_opaque_key"),
        sa.CheckConstraint("workspace_id IS NULL OR project_id IS NOT NULL", name="ck_supporting_file_workspace_project"),
        sa.CheckConstraint("(lifecycle IN ('quarantined','available','rejected') AND withdrawn_at IS NULL AND withdrawn_by_id IS NULL AND withdrawal_reason_code IS NULL) OR (lifecycle='withdrawn' AND withdrawn_at IS NOT NULL AND withdrawn_by_id IS NOT NULL AND withdrawal_reason_code IS NOT NULL)", name="ck_supporting_file_withdrawal"),
    )
    op.create_index("ix_supporting_file_scope_order", "supporting_file_assets", ["organization_id", "project_id", "workspace_id", "uploaded_at", "id"])
    op.create_table("supporting_file_upload_reservations", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False), sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False), sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False), sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("engineering_workspaces.id", ondelete="RESTRICT")), sa.Column("storage_key", sa.String(80), nullable=False), sa.Column("status", sa.String(16), nullable=False, server_default="reserved"), sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("supporting_file_assets.id", ondelete="RESTRICT")), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.UniqueConstraint("storage_key", name="uq_supporting_file_reservation_key"), sa.UniqueConstraint("asset_id", name="uq_supporting_file_reservation_asset"), sa.CheckConstraint("status IN ('reserved','streaming','uploaded','consumed','failed','expired')", name="ck_supporting_file_reservation_status"), sa.CheckConstraint("storage_key ~ '^objects/[0-9a-f]{64}$'", name="ck_supporting_file_reservation_key"))
    op.create_table("supporting_file_scan_attempts", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("supporting_file_assets.id", ondelete="RESTRICT"), nullable=False), sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False), sa.Column("expected_asset_version", sa.Integer(), nullable=False), sa.Column("object_digest", sa.String(64), nullable=False), sa.Column("attempt_number", sa.Integer(), nullable=False), sa.Column("state", sa.String(16), nullable=False), sa.Column("engine_id", sa.String(128)), sa.Column("signature_set_id", sa.String(128)), sa.Column("correlation_id", postgresql.UUID(as_uuid=True)), sa.Column("disposition", sa.String(16)), sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False), sa.Column("completed_at", sa.DateTime(timezone=True)), sa.UniqueConstraint("asset_id", "attempt_number", name="uq_supporting_file_scan_attempt_ordinal"), sa.UniqueConstraint("correlation_id", name="uq_supporting_file_scan_attempt_correlation"), sa.CheckConstraint("attempt_number BETWEEN 1 AND 3", name="ck_supporting_file_scan_attempt_ordinal"), sa.CheckConstraint("state IN ('requested','completed','failed')", name="ck_supporting_file_scan_attempt_state"), sa.CheckConstraint("disposition IS NULL OR disposition IN ('clean','unsafe','indeterminate')", name="ck_supporting_file_scan_attempt_disposition"), sa.CheckConstraint("object_digest ~ '^[0-9a-f]{64}$'", name="ck_supporting_file_scan_attempt_digest"), sa.CheckConstraint("(state='requested' AND completed_at IS NULL AND disposition IS NULL AND engine_id IS NULL AND signature_set_id IS NULL AND correlation_id IS NULL) OR (state='completed' AND completed_at IS NOT NULL AND disposition IN ('clean','unsafe') AND engine_id IS NOT NULL AND signature_set_id IS NOT NULL AND correlation_id IS NOT NULL) OR (state='failed' AND completed_at IS NOT NULL AND (disposition IS NULL OR disposition='indeterminate') AND ((disposition IS NULL AND engine_id IS NULL AND signature_set_id IS NULL AND correlation_id IS NULL) OR (disposition='indeterminate' AND engine_id IS NOT NULL AND signature_set_id IS NOT NULL AND correlation_id IS NOT NULL)))", name="ck_supporting_file_scan_attempt_state_closure"))
    op.create_index("ix_supporting_file_scan_attempt_scope", "supporting_file_scan_attempts", ["organization_id", "asset_id", "attempt_number"])
    op.create_table("evidence_supporting_file_links", sa.Column("evidence_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("evidence.id", ondelete="RESTRICT"), primary_key=True), sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("supporting_file_assets.id", ondelete="RESTRICT"), primary_key=True), sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("project_id", sa.Integer(), nullable=False), sa.Column("workspace_id", sa.Integer()), sa.Column("evidence_version", sa.Integer(), nullable=False), sa.Column("ordinal", sa.Integer(), nullable=False), sa.Column("linked_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False), sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("evidence_id", "ordinal", name="uq_evidence_file_ordinal"), sa.CheckConstraint("ordinal BETWEEN 0 AND 9", name="ck_evidence_file_ordinal"))
    op.create_table("supporting_file_outbox", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("supporting_file_assets.id", ondelete="RESTRICT"), nullable=False), sa.Column("aggregate_version", sa.Integer(), nullable=False), sa.Column("event_type", sa.String(96), nullable=False), sa.Column("payload", sa.JSON(), nullable=False), sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False), sa.Column("published_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.UniqueConstraint("event_id", name="uq_supporting_file_outbox_event"), sa.CheckConstraint("aggregate_version>=1", name="ck_supporting_file_outbox_version"))
    op.create_table("supporting_file_idempotency", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False), sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False), sa.Column("operation", sa.String(32), nullable=False), sa.Column("idempotency_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("request_fingerprint", sa.String(64), nullable=False), sa.Column("status", sa.String(16), nullable=False, server_default="pending"), sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("supporting_file_assets.id", ondelete="RESTRICT")), sa.Column("result", sa.JSON()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.UniqueConstraint("organization_id", "actor_id", "operation", "idempotency_id", name="uq_supporting_file_idempotency_scope"), sa.CheckConstraint("status IN ('pending','completed')", name="ck_supporting_file_idempotency_status"))
    op.add_column("evidence", sa.Column("supporting_file_links_sealed_at", sa.DateTime(timezone=True)))
    op.execute("""
    CREATE OR REPLACE FUNCTION satco_guard_supporting_file_asset() RETURNS trigger
    LANGUAGE plpgsql AS $$
    BEGIN
      IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'supporting file delete denied'; END IF;
      IF TG_OP = 'UPDATE' THEN
        IF NEW.organization_id IS DISTINCT FROM OLD.organization_id OR NEW.project_id IS DISTINCT FROM OLD.project_id OR NEW.workspace_id IS DISTINCT FROM OLD.workspace_id OR NEW.safe_filename IS DISTINCT FROM OLD.safe_filename OR NEW.safe_ascii_filename IS DISTINCT FROM OLD.safe_ascii_filename OR NEW.media_type IS DISTINCT FROM OLD.media_type OR NEW.byte_size IS DISTINCT FROM OLD.byte_size OR NEW.digest_algorithm IS DISTINCT FROM OLD.digest_algorithm OR NEW.content_digest IS DISTINCT FROM OLD.content_digest OR NEW.storage_key IS DISTINCT FROM OLD.storage_key OR NEW.object_version IS DISTINCT FROM OLD.object_version OR NEW.uploader_id IS DISTINCT FROM OLD.uploader_id OR NEW.uploaded_at IS DISTINCT FROM OLD.uploaded_at OR NEW.predecessor_asset_id IS DISTINCT FROM OLD.predecessor_asset_id THEN RAISE EXCEPTION 'supporting file immutable metadata'; END IF;
        IF NEW.version <> OLD.version + 1 OR NOT ((OLD.lifecycle='quarantined' AND NEW.lifecycle IN ('available','rejected')) OR (OLD.lifecycle='available' AND NEW.lifecycle='withdrawn')) THEN RAISE EXCEPTION 'supporting file transition denied'; END IF;
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER trg_supporting_file_guard BEFORE UPDATE OR DELETE ON supporting_file_assets FOR EACH ROW EXECUTE FUNCTION satco_guard_supporting_file_asset();
    CREATE OR REPLACE FUNCTION satco_guard_supporting_file_scan_attempt() RETURNS trigger
    LANGUAGE plpgsql AS $$
    DECLARE asset_row supporting_file_assets%ROWTYPE; expected_ordinal integer;
    BEGIN
      IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'supporting file scan history delete denied'; END IF;
      IF TG_OP = 'INSERT' THEN
        SELECT * INTO asset_row FROM supporting_file_assets WHERE id=NEW.asset_id FOR SHARE;
        IF asset_row.id IS NULL
           OR NEW.organization_id IS DISTINCT FROM asset_row.organization_id
           OR NEW.expected_asset_version IS DISTINCT FROM asset_row.version
           OR NEW.object_digest IS DISTINCT FROM asset_row.content_digest
           OR asset_row.lifecycle <> 'quarantined'
           OR NEW.state <> 'requested' THEN
          RAISE EXCEPTION 'supporting file scan attempt binding denied';
        END IF;
        SELECT COALESCE(MAX(attempt_number),0)+1 INTO expected_ordinal
          FROM supporting_file_scan_attempts WHERE asset_id=NEW.asset_id;
        IF NEW.attempt_number <> expected_ordinal THEN
          RAISE EXCEPTION 'supporting file scan attempt ordinal denied';
        END IF;
        RETURN NEW;
      END IF;
      IF OLD.state <> 'requested'
         OR NEW.state NOT IN ('completed','failed')
         OR NEW.id IS DISTINCT FROM OLD.id
         OR NEW.asset_id IS DISTINCT FROM OLD.asset_id
         OR NEW.organization_id IS DISTINCT FROM OLD.organization_id
         OR NEW.expected_asset_version IS DISTINCT FROM OLD.expected_asset_version
         OR NEW.object_digest IS DISTINCT FROM OLD.object_digest
         OR NEW.attempt_number IS DISTINCT FROM OLD.attempt_number
         OR NEW.requested_at IS DISTINCT FROM OLD.requested_at THEN
        RAISE EXCEPTION 'supporting file scan history immutable';
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER trg_supporting_file_scan_attempt_guard BEFORE INSERT OR UPDATE OR DELETE ON supporting_file_scan_attempts FOR EACH ROW EXECUTE FUNCTION satco_guard_supporting_file_scan_attempt();
    CREATE OR REPLACE FUNCTION satco_seal_evidence_file_links() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF OLD.lifecycle='proposed' AND NEW.lifecycle <> 'proposed' AND OLD.supporting_file_links_sealed_at IS NULL THEN NEW.supporting_file_links_sealed_at := NEW.updated_at; END IF;
      IF OLD.supporting_file_links_sealed_at IS NOT NULL AND NEW.supporting_file_links_sealed_at IS DISTINCT FROM OLD.supporting_file_links_sealed_at THEN RAISE EXCEPTION 'evidence supporting-file link seal immutable'; END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER trg_evidence_file_link_seal BEFORE UPDATE ON evidence FOR EACH ROW EXECUTE FUNCTION satco_seal_evidence_file_links();

    CREATE OR REPLACE FUNCTION satco_guard_evidence_supporting_file_link() RETURNS trigger
    LANGUAGE plpgsql AS $$
    DECLARE evidence_row evidence%ROWTYPE; asset_row supporting_file_assets%ROWTYPE;
    BEGIN
      IF TG_OP = 'DELETE' THEN
        SELECT * INTO evidence_row FROM evidence WHERE id=OLD.evidence_id;
        IF evidence_row.supporting_file_links_sealed_at IS NOT NULL OR evidence_row.lifecycle <> 'proposed' THEN
          RAISE EXCEPTION 'evidence supporting-file links are sealed';
        END IF;
        RETURN OLD;
      END IF;
      SELECT * INTO evidence_row FROM evidence WHERE id=NEW.evidence_id;
      SELECT * INTO asset_row FROM supporting_file_assets WHERE id=NEW.asset_id;
      IF NOT FOUND OR evidence_row.id IS NULL OR evidence_row.lifecycle <> 'proposed' OR evidence_row.supporting_file_links_sealed_at IS NOT NULL THEN
        RAISE EXCEPTION 'evidence supporting-file link is not mutable';
      END IF;
      IF asset_row.lifecycle <> 'available'
         OR NEW.organization_id <> evidence_row.organization_id
         OR NEW.organization_id <> asset_row.organization_id
         OR NEW.project_id IS DISTINCT FROM evidence_row.project_id
         OR NEW.project_id IS DISTINCT FROM asset_row.project_id
         OR NEW.workspace_id IS DISTINCT FROM evidence_row.workspace_id
         OR (asset_row.workspace_id IS NOT NULL
             AND asset_row.workspace_id IS DISTINCT FROM evidence_row.workspace_id)
         OR NEW.evidence_version <> evidence_row.version THEN
        RAISE EXCEPTION 'evidence supporting-file link scope or version mismatch';
      END IF;
      IF TG_OP = 'UPDATE' AND (NEW.evidence_id IS DISTINCT FROM OLD.evidence_id OR NEW.asset_id IS DISTINCT FROM OLD.asset_id OR NEW.organization_id IS DISTINCT FROM OLD.organization_id OR NEW.project_id IS DISTINCT FROM OLD.project_id OR NEW.workspace_id IS DISTINCT FROM OLD.workspace_id OR NEW.evidence_version IS DISTINCT FROM OLD.evidence_version OR NEW.ordinal IS DISTINCT FROM OLD.ordinal OR NEW.linked_by_id IS DISTINCT FROM OLD.linked_by_id OR NEW.linked_at IS DISTINCT FROM OLD.linked_at) THEN
        RAISE EXCEPTION 'evidence supporting-file link is immutable';
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER trg_evidence_supporting_file_link_guard BEFORE INSERT OR UPDATE OR DELETE ON evidence_supporting_file_links FOR EACH ROW EXECUTE FUNCTION satco_guard_evidence_supporting_file_link();
    """)
    op.execute("GRANT SELECT, INSERT, UPDATE ON supporting_file_assets, supporting_file_upload_reservations, supporting_file_scan_attempts, evidence_supporting_file_links TO satco_runtime")


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS trg_evidence_supporting_file_link_guard ON evidence_supporting_file_links; DROP FUNCTION IF EXISTS satco_guard_evidence_supporting_file_link(); DROP TRIGGER IF EXISTS trg_evidence_file_link_seal ON evidence; DROP FUNCTION IF EXISTS satco_seal_evidence_file_links(); DROP TRIGGER IF EXISTS trg_supporting_file_scan_attempt_guard ON supporting_file_scan_attempts; DROP FUNCTION IF EXISTS satco_guard_supporting_file_scan_attempt(); DROP TRIGGER IF EXISTS trg_supporting_file_guard ON supporting_file_assets; DROP FUNCTION IF EXISTS satco_guard_supporting_file_asset()")
    op.drop_column("evidence", "supporting_file_links_sealed_at")
    op.drop_table("evidence_supporting_file_links")
    op.execute("DROP TABLE IF EXISTS supporting_file_idempotency")
    op.execute("DROP TABLE IF EXISTS supporting_file_outbox")
    op.execute("DROP INDEX IF EXISTS ix_supporting_file_scan_attempt_scope")
    op.execute("DROP TABLE IF EXISTS supporting_file_scan_attempts")
    op.drop_table("supporting_file_upload_reservations")
    op.drop_index("ix_supporting_file_scope_order", table_name="supporting_file_assets")
    op.drop_table("supporting_file_assets")
