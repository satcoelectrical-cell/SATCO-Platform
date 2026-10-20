"""Document Intelligence Golden Demo V1 durable foundation.

Revision ID: di0000000001
Revises: e05900000002
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "di0000000001"
down_revision = "e05900000002"
branch_labels = None
depends_on = None


UUID = postgresql.UUID(as_uuid=True)


def upgrade():
    op.create_table(
        "document_analysis_runs",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("organization_id", UUID, sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("engineering_workspaces.id", ondelete="RESTRICT")),
        sa.Column("supporting_file_asset_id", UUID, sa.ForeignKey("supporting_file_assets.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_asset_version", sa.Integer(), nullable=False),
        sa.Column("source_storage_object_version", sa.String(160), nullable=False),
        sa.Column("source_content_digest", sa.String(64), nullable=False),
        sa.Column("safe_filename", sa.String(255), nullable=False),
        sa.Column("media_type", sa.String(128), nullable=False),
        sa.Column("family_hint", sa.String(40)),
        sa.Column("document_family", sa.String(40)),
        sa.Column("state", sa.String(40), nullable=False, server_default="queued"),
        sa.Column("progress_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("progress_total", sa.Integer()),
        sa.Column("customer_message", sa.String(500), nullable=False, server_default="Analysis queued"),
        sa.Column("page_count", sa.Integer()),
        sa.Column("candidate_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unreviewed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("limitations", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("provider_status", sa.String(32)),
        sa.Column("parser_id", sa.String(128)),
        sa.Column("parser_version", sa.String(128)),
        sa.Column("output_digest", sa.String(64)),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("superseded_by_run_id", UUID, sa.ForeignKey("document_analysis_runs.id", ondelete="RESTRICT")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("source_asset_version >= 1", name="ck_document_analysis_source_version"),
        sa.CheckConstraint("source_content_digest ~ '^[0-9a-f]{64}$'", name="ck_document_analysis_source_digest"),
        sa.CheckConstraint("version >= 1", name="ck_document_analysis_version"),
        sa.CheckConstraint("progress_completed >= 0", name="ck_document_analysis_progress_completed"),
        sa.CheckConstraint("progress_total IS NULL OR progress_total >= progress_completed", name="ck_document_analysis_progress_total"),
        sa.CheckConstraint("candidate_count >= 0 AND unreviewed_count >= 0 AND unreviewed_count <= candidate_count", name="ck_document_analysis_candidate_counts"),
        sa.CheckConstraint("workspace_id IS NULL OR project_id IS NOT NULL", name="ck_document_analysis_scope"),
        sa.CheckConstraint("family_hint IS NULL OR family_hint IN ('narrative_engineering','tabular_engineering')", name="ck_document_analysis_family_hint"),
        sa.CheckConstraint("document_family IS NULL OR document_family IN ('narrative_engineering','tabular_engineering')", name="ck_document_analysis_family"),
        sa.CheckConstraint("state IN ('queued','extracting','interpreting','requires_review','completed','completed_with_limitations','provider_unavailable','failed_retryable','failed_terminal','source_changed','superseded')", name="ck_document_analysis_state"),
    )
    op.create_index("ix_document_analysis_scope", "document_analysis_runs", ["organization_id", "project_id", "workspace_id", "created_at", "id"])
    op.create_index("ix_document_analysis_worker_queue", "document_analysis_runs", ["state", "created_at", "id"])

    op.create_table(
        "document_analysis_pages",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("analysis_run_id", UUID, sa.ForeignKey("document_analysis_runs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("page_index", sa.Integer(), nullable=False),
        sa.Column("page_label", sa.String(64)),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("tables", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("warnings", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("analysis_run_id", "page_index", name="uq_document_analysis_page"),
        sa.CheckConstraint("page_index >= 0", name="ck_document_analysis_page_index"),
        sa.CheckConstraint("status IN ('complete','partial','unsupported','failed')", name="ck_document_analysis_page_status"),
    )
    op.create_index("ix_document_analysis_pages_run", "document_analysis_pages", ["analysis_run_id", "page_index"])

    op.create_table(
        "source_locators",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("locator_kind", sa.String(20), nullable=False),
        sa.Column("supporting_file_asset_id", UUID, sa.ForeignKey("supporting_file_assets.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("asset_version_at_analysis", sa.Integer(), nullable=False),
        sa.Column("storage_object_version", sa.String(160), nullable=False),
        sa.Column("digest_algorithm", sa.String(16), nullable=False, server_default="sha256"),
        sa.Column("content_digest", sa.String(64), nullable=False),
        sa.Column("media_type", sa.String(128), nullable=False),
        sa.Column("page_index", sa.Integer()),
        sa.Column("page_label", sa.String(64)),
        sa.Column("section_path", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("section_title", sa.String(500)),
        sa.Column("table_key", sa.String(128)),
        sa.Column("table_title", sa.String(500)),
        sa.Column("row_index", sa.Integer()),
        sa.Column("row_label", sa.String(256)),
        sa.Column("column_index", sa.Integer()),
        sa.Column("column_label", sa.String(256)),
        sa.Column("text_start", sa.Integer()),
        sa.Column("text_end", sa.Integer()),
        sa.Column("text_excerpt", sa.String(500)),
        sa.Column("text_excerpt_digest", sa.String(64)),
        sa.Column("bbox_x0", sa.Numeric(8, 7)),
        sa.Column("bbox_y0", sa.Numeric(8, 7)),
        sa.Column("bbox_x1", sa.Numeric(8, 7)),
        sa.Column("bbox_y1", sa.Numeric(8, 7)),
        sa.Column("source_revision_label", sa.String(128)),
        sa.Column("extraction_method", sa.String(16), nullable=False),
        sa.Column("locator_digest", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("locator_digest", name="uq_source_locator_digest"),
        sa.CheckConstraint("schema_version = 1", name="ck_source_locator_schema"),
        sa.CheckConstraint("asset_version_at_analysis >= 1", name="ck_source_locator_asset_version"),
        sa.CheckConstraint("content_digest ~ '^[0-9a-f]{64}$'", name="ck_source_locator_content_digest"),
        sa.CheckConstraint("locator_digest ~ '^[0-9a-f]{64}$'", name="ck_source_locator_digest"),
        sa.CheckConstraint("page_index IS NULL OR page_index >= 0", name="ck_source_locator_page"),
        sa.CheckConstraint("locator_kind = 'document' OR page_index IS NOT NULL", name="ck_source_locator_page_required"),
        sa.CheckConstraint("locator_kind IN ('document','page','text_span','table','table_row','table_cell')", name="ck_source_locator_kind"),
        sa.CheckConstraint("extraction_method IN ('deterministic','provider','hybrid')", name="ck_source_locator_method"),
        sa.CheckConstraint("locator_kind <> 'table_cell' OR (table_key IS NOT NULL AND row_index IS NOT NULL AND column_index IS NOT NULL)", name="ck_source_locator_cell_coordinates"),
        sa.CheckConstraint("locator_kind <> 'text_span' OR (text_start IS NOT NULL AND text_end > text_start AND text_excerpt IS NOT NULL AND text_excerpt_digest ~ '^[0-9a-f]{64}$')", name="ck_source_locator_text_span"),
        sa.CheckConstraint("(bbox_x0 IS NULL AND bbox_y0 IS NULL AND bbox_x1 IS NULL AND bbox_y1 IS NULL) OR (page_index IS NOT NULL AND bbox_x0 >= 0 AND bbox_y0 >= 0 AND bbox_x1 <= 1 AND bbox_y1 <= 1 AND bbox_x1 > bbox_x0 AND bbox_y1 > bbox_y0)", name="ck_source_locator_bbox"),
    )
    op.create_index("ix_source_locator_asset_page", "source_locators", ["supporting_file_asset_id", "page_index"])

    op.create_table(
        "document_engineering_candidates",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("analysis_run_id", UUID, sa.ForeignKey("document_analysis_runs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("assertion_mode", sa.String(16), nullable=False),
        sa.Column("review_state", sa.String(16), nullable=False, server_default="unreviewed"),
        sa.Column("subject_key", sa.String(256)),
        sa.Column("subject_label", sa.String(500)),
        sa.Column("raw_value", sa.Text(), nullable=False),
        sa.Column("normalized_value", sa.Text()),
        sa.Column("numeric_value", sa.Numeric(30, 12)),
        sa.Column("unit", sa.String(64)),
        sa.Column("quantity_type", sa.String(128)),
        sa.Column("condition", sa.String(1000)),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("confidence_rationale", sa.String(2000), nullable=False),
        sa.Column("uncertainty", sa.String(2000)),
        sa.Column("assumptions", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("proposed_canonical_target", sa.String(64), nullable=False),
        sa.Column("reviewed_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("analysis_run_id", "ordinal", name="uq_document_candidate_ordinal"),
        sa.CheckConstraint("ordinal >= 0 AND version >= 1", name="ck_document_candidate_version"),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_document_candidate_confidence"),
        sa.CheckConstraint("review_state IN ('unreviewed','accepted','corrected','rejected','deferred')", name="ck_document_candidate_review_state"),
        sa.CheckConstraint("assertion_mode IN ('direct','derived','inferred')", name="ck_document_candidate_assertion"),
    )
    op.create_index("ix_document_candidate_run_review", "document_engineering_candidates", ["analysis_run_id", "review_state", "ordinal"])

    op.create_table(
        "candidate_source_locator_links",
        sa.Column("candidate_id", UUID, sa.ForeignKey("document_engineering_candidates.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("source_locator_id", UUID, sa.ForeignKey("source_locators.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.UniqueConstraint("candidate_id", "ordinal", name="uq_candidate_locator_ordinal"),
        sa.CheckConstraint("ordinal >= 0", name="ck_candidate_locator_ordinal"),
    )
    op.create_table(
        "evidence_source_locator_links",
        sa.Column("evidence_id", UUID, sa.ForeignKey("evidence.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("source_locator_id", UUID, sa.ForeignKey("source_locators.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("evidence_version", sa.Integer(), nullable=False),
        sa.Column("linked_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("evidence_id", "ordinal", name="uq_evidence_locator_ordinal"),
        sa.CheckConstraint("ordinal >= 0 AND evidence_version >= 1", name="ck_evidence_locator_version"),
    )
    op.create_table(
        "document_candidate_reviews",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("candidate_id", UUID, sa.ForeignKey("document_engineering_candidates.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("candidate_version", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("rationale", sa.String(2000), nullable=False),
        sa.Column("correction", postgresql.JSONB()),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("candidate_id", "candidate_version", name="uq_document_candidate_review_version"),
        sa.CheckConstraint("action IN ('accept','correct','reject','defer')", name="ck_document_candidate_review_action"),
        sa.CheckConstraint("candidate_version >= 1", name="ck_document_candidate_review_version"),
    )
    op.create_table(
        "document_promotion_receipts",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("candidate_id", UUID, sa.ForeignKey("document_engineering_candidates.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("candidate_version", sa.Integer(), nullable=False),
        sa.Column("evidence_id", UUID, sa.ForeignKey("evidence.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("engineering_context_id", sa.BigInteger(), sa.ForeignKey("engineering_contexts.id", ondelete="RESTRICT")),
        sa.Column("promoted_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("rationale", sa.String(2000), nullable=False),
        sa.Column("promoted_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("candidate_id", "candidate_version", name="uq_document_promotion_candidate_version"),
        sa.CheckConstraint("candidate_version >= 1", name="ck_document_promotion_candidate_version"),
    )
    op.create_table(
        "document_correlations",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("organization_id", UUID, sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("engineering_workspaces.id", ondelete="RESTRICT")),
        sa.Column("left_candidate_id", UUID, sa.ForeignKey("document_engineering_candidates.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("right_candidate_id", UUID, sa.ForeignKey("document_engineering_candidates.id", ondelete="RESTRICT")),
        sa.Column("rule_id", sa.String(128), nullable=False),
        sa.Column("rule_version", sa.Integer(), nullable=False),
        sa.Column("applicability", sa.String(2000), nullable=False),
        sa.Column("result", postgresql.JSONB(), nullable=False),
        sa.Column("result_digest", sa.String(64), nullable=False),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("result_digest", name="uq_document_correlation_digest"),
        sa.CheckConstraint("rule_version >= 1", name="ck_document_correlation_rule_version"),
        sa.CheckConstraint("result_digest ~ '^[0-9a-f]{64}$'", name="ck_document_correlation_result_digest"),
    )
    op.create_table(
        "document_findings",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("correlation_id", UUID, sa.ForeignKey("document_correlations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("state", sa.String(16), nullable=False, server_default="open"),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("explanation", sa.String(4000), nullable=False),
        sa.Column("uncertainty", sa.String(2000)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('missing_information','discrepancy')", name="ck_document_finding_kind"),
        sa.CheckConstraint("state IN ('open','acknowledged','resolved','deferred')", name="ck_document_finding_state"),
    )
    op.create_table(
        "document_intelligence_idempotency",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("organization_id", UUID, sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("operation", sa.String(64), nullable=False),
        sa.Column("idempotency_id", UUID, nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("aggregate_id", UUID, sa.ForeignKey("document_analysis_runs.id", ondelete="RESTRICT")),
        sa.Column("result", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "actor_id", "operation", "idempotency_id", name="uq_document_intelligence_idempotency"),
        sa.CheckConstraint("status IN ('pending','completed')", name="ck_document_intelligence_idempotency_status"),
    )
    op.create_table(
        "document_intelligence_outbox",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("event_id", UUID, nullable=False, unique=True),
        sa.Column("aggregate_id", UUID, sa.ForeignKey("document_analysis_runs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("aggregate_version", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(96), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("aggregate_version >= 1", name="ck_document_intelligence_outbox_version"),
    )

    immutable = (
        "document_analysis_pages", "source_locators",
        "candidate_source_locator_links", "evidence_source_locator_links",
        "document_candidate_reviews", "document_promotion_receipts",
        "document_correlations",
    )
    op.execute("""
    CREATE FUNCTION document_intelligence_immutable_history_guard()
    RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      RAISE EXCEPTION 'Document Intelligence history is append-only';
    END;
    $$
    """)
    for table in immutable:
        op.execute(
            f"CREATE TRIGGER trg_{table}_immutable BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION document_intelligence_immutable_history_guard()"
        )

    op.execute("""
    DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname='satco_runtime') THEN
        REVOKE ALL ON document_analysis_runs, document_analysis_pages,
          source_locators, document_engineering_candidates,
          candidate_source_locator_links, evidence_source_locator_links,
          document_candidate_reviews, document_promotion_receipts,
          document_correlations, document_findings,
          document_intelligence_idempotency, document_intelligence_outbox
          FROM satco_runtime;
        GRANT SELECT, INSERT ON document_analysis_pages, source_locators,
          candidate_source_locator_links, evidence_source_locator_links,
          document_candidate_reviews, document_promotion_receipts,
          document_correlations TO satco_runtime;
        GRANT SELECT, INSERT, UPDATE ON document_analysis_runs,
          document_engineering_candidates, document_findings TO satco_runtime;
        GRANT SELECT, INSERT ON document_intelligence_idempotency,
          document_intelligence_outbox TO satco_runtime;
        GRANT UPDATE(status, aggregate_id, result, updated_at)
          ON document_intelligence_idempotency TO satco_runtime;
        GRANT UPDATE(published_at) ON document_intelligence_outbox TO satco_runtime;
        REVOKE EXECUTE ON FUNCTION document_intelligence_immutable_history_guard()
          FROM satco_runtime;
      END IF;
    END $$
    """)


def downgrade():
    bind = op.get_bind()
    has_rows = bind.execute(sa.text("SELECT EXISTS (SELECT 1 FROM document_analysis_runs)")).scalar_one()
    if has_rows:
        raise RuntimeError("Cannot discard populated Document Intelligence history")
    op.execute("DROP FUNCTION document_intelligence_immutable_history_guard() CASCADE")
    for table in (
        "document_intelligence_outbox", "document_intelligence_idempotency",
        "document_findings", "document_correlations", "document_promotion_receipts",
        "document_candidate_reviews", "evidence_source_locator_links",
        "candidate_source_locator_links", "document_engineering_candidates",
        "source_locators", "document_analysis_pages", "document_analysis_runs",
    ):
        op.drop_table(table)
