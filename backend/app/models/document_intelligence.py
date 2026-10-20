"""Durable, Human-authoritative Document Intelligence persistence."""

from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func

from app.core.database import Base


class DocumentAnalysisRun(Base):
    __tablename__ = "document_analysis_runs"
    __table_args__ = (
        CheckConstraint("source_asset_version >= 1", name="ck_document_analysis_source_version"),
        CheckConstraint("source_content_digest ~ '^[0-9a-f]{64}$'", name="ck_document_analysis_source_digest"),
        CheckConstraint("version >= 1", name="ck_document_analysis_version"),
        CheckConstraint("progress_completed >= 0", name="ck_document_analysis_progress_completed"),
        CheckConstraint("progress_total IS NULL OR progress_total >= progress_completed", name="ck_document_analysis_progress_total"),
        CheckConstraint("candidate_count >= 0 AND unreviewed_count >= 0 AND unreviewed_count <= candidate_count", name="ck_document_analysis_candidate_counts"),
        CheckConstraint("workspace_id IS NULL OR project_id IS NOT NULL", name="ck_document_analysis_scope"),
        CheckConstraint("family_hint IS NULL OR family_hint IN ('narrative_engineering','tabular_engineering')", name="ck_document_analysis_family_hint"),
        CheckConstraint("document_family IS NULL OR document_family IN ('narrative_engineering','tabular_engineering')", name="ck_document_analysis_family"),
        CheckConstraint("state IN ('queued','extracting','interpreting','requires_review','completed','completed_with_limitations','provider_unavailable','failed_retryable','failed_terminal','source_changed','superseded')", name="ck_document_analysis_state"),
        Index("ix_document_analysis_scope", "organization_id", "project_id", "workspace_id", "created_at", "id"),
        Index("ix_document_analysis_worker_queue", "state", "created_at", "id"),
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"))
    supporting_file_asset_id = Column(PGUUID(as_uuid=True), ForeignKey("supporting_file_assets.id", ondelete="RESTRICT"), nullable=False)
    source_asset_version = Column(Integer, nullable=False)
    source_storage_object_version = Column(String(160), nullable=False)
    source_content_digest = Column(String(64), nullable=False)
    safe_filename = Column(String(255), nullable=False)
    media_type = Column(String(128), nullable=False)
    family_hint = Column(String(40))
    document_family = Column(String(40))
    state = Column(String(40), nullable=False, default="queued", server_default="queued")
    progress_completed = Column(Integer, nullable=False, default=0, server_default="0")
    progress_total = Column(Integer)
    customer_message = Column(String(500), nullable=False, default="Analysis queued", server_default="Analysis queued")
    page_count = Column(Integer)
    candidate_count = Column(Integer, nullable=False, default=0, server_default="0")
    unreviewed_count = Column(Integer, nullable=False, default=0, server_default="0")
    limitations = Column(JSON, nullable=False, default=list, server_default="[]")
    provider_status = Column(String(32))
    parser_id = Column(String(128))
    parser_version = Column(String(128))
    output_digest = Column(String(64))
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    version = Column(Integer, nullable=False, default=1, server_default="1")
    superseded_by_run_id = Column(PGUUID(as_uuid=True), ForeignKey("document_analysis_runs.id", ondelete="RESTRICT"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class DocumentAnalysisPageRecord(Base):
    __tablename__ = "document_analysis_pages"
    __table_args__ = (
        UniqueConstraint("analysis_run_id", "page_index", name="uq_document_analysis_page"),
        CheckConstraint("page_index >= 0", name="ck_document_analysis_page_index"),
        CheckConstraint("status IN ('complete','partial','unsupported','failed')", name="ck_document_analysis_page_status"),
        Index("ix_document_analysis_pages_run", "analysis_run_id", "page_index"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    analysis_run_id = Column(PGUUID(as_uuid=True), ForeignKey("document_analysis_runs.id", ondelete="RESTRICT"), nullable=False)
    page_index = Column(Integer, nullable=False)
    page_label = Column(String(64))
    status = Column(String(16), nullable=False)
    extracted_text = Column(Text, nullable=False, default="", server_default="")
    tables = Column(JSON, nullable=False, default=list, server_default="[]")
    warnings = Column(JSON, nullable=False, default=list, server_default="[]")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SourceLocatorRecord(Base):
    __tablename__ = "source_locators"
    __table_args__ = (
        UniqueConstraint("locator_digest", name="uq_source_locator_digest"),
        CheckConstraint("schema_version = 1", name="ck_source_locator_schema"),
        CheckConstraint("asset_version_at_analysis >= 1", name="ck_source_locator_asset_version"),
        CheckConstraint("content_digest ~ '^[0-9a-f]{64}$'", name="ck_source_locator_content_digest"),
        CheckConstraint("locator_digest ~ '^[0-9a-f]{64}$'", name="ck_source_locator_digest"),
        CheckConstraint("page_index IS NULL OR page_index >= 0", name="ck_source_locator_page"),
        CheckConstraint("locator_kind = 'document' OR page_index IS NOT NULL", name="ck_source_locator_page_required"),
        CheckConstraint("locator_kind IN ('document','page','text_span','table','table_row','table_cell')", name="ck_source_locator_kind"),
        CheckConstraint("extraction_method IN ('deterministic','provider','hybrid')", name="ck_source_locator_method"),
        CheckConstraint("locator_kind <> 'table_cell' OR (table_key IS NOT NULL AND row_index IS NOT NULL AND column_index IS NOT NULL)", name="ck_source_locator_cell_coordinates"),
        CheckConstraint("locator_kind <> 'text_span' OR (text_start IS NOT NULL AND text_end > text_start AND text_excerpt IS NOT NULL AND text_excerpt_digest ~ '^[0-9a-f]{64}$')", name="ck_source_locator_text_span"),
        CheckConstraint("(bbox_x0 IS NULL AND bbox_y0 IS NULL AND bbox_x1 IS NULL AND bbox_y1 IS NULL) OR (page_index IS NOT NULL AND bbox_x0 >= 0 AND bbox_y0 >= 0 AND bbox_x1 <= 1 AND bbox_y1 <= 1 AND bbox_x1 > bbox_x0 AND bbox_y1 > bbox_y0)", name="ck_source_locator_bbox"),
        Index("ix_source_locator_asset_page", "supporting_file_asset_id", "page_index"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    schema_version = Column(Integer, nullable=False, default=1, server_default="1")
    locator_kind = Column(String(20), nullable=False)
    supporting_file_asset_id = Column(PGUUID(as_uuid=True), ForeignKey("supporting_file_assets.id", ondelete="RESTRICT"), nullable=False)
    asset_version_at_analysis = Column(Integer, nullable=False)
    storage_object_version = Column(String(160), nullable=False)
    digest_algorithm = Column(String(16), nullable=False, default="sha256", server_default="sha256")
    content_digest = Column(String(64), nullable=False)
    media_type = Column(String(128), nullable=False)
    page_index = Column(Integer)
    page_label = Column(String(64))
    section_path = Column(JSON, nullable=False, default=list, server_default="[]")
    section_title = Column(String(500))
    table_key = Column(String(128))
    table_title = Column(String(500))
    row_index = Column(Integer)
    row_label = Column(String(256))
    column_index = Column(Integer)
    column_label = Column(String(256))
    text_start = Column(Integer)
    text_end = Column(Integer)
    text_excerpt = Column(String(500))
    text_excerpt_digest = Column(String(64))
    bbox_x0 = Column(Numeric(8, 7))
    bbox_y0 = Column(Numeric(8, 7))
    bbox_x1 = Column(Numeric(8, 7))
    bbox_y1 = Column(Numeric(8, 7))
    source_revision_label = Column(String(128))
    extraction_method = Column(String(16), nullable=False)
    locator_digest = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DocumentEngineeringCandidate(Base):
    __tablename__ = "document_engineering_candidates"
    __table_args__ = (
        UniqueConstraint("analysis_run_id", "ordinal", name="uq_document_candidate_ordinal"),
        CheckConstraint("ordinal >= 0 AND version >= 1", name="ck_document_candidate_version"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_document_candidate_confidence"),
        CheckConstraint("review_state IN ('unreviewed','accepted','corrected','rejected','deferred')", name="ck_document_candidate_review_state"),
        CheckConstraint("assertion_mode IN ('direct','derived','inferred')", name="ck_document_candidate_assertion"),
        Index("ix_document_candidate_run_review", "analysis_run_id", "review_state", "ordinal"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    analysis_run_id = Column(PGUUID(as_uuid=True), ForeignKey("document_analysis_runs.id", ondelete="RESTRICT"), nullable=False)
    ordinal = Column(Integer, nullable=False)
    kind = Column(String(40), nullable=False)
    assertion_mode = Column(String(16), nullable=False)
    review_state = Column(String(16), nullable=False, default="unreviewed", server_default="unreviewed")
    subject_key = Column(String(256))
    subject_label = Column(String(500))
    raw_value = Column(Text, nullable=False)
    normalized_value = Column(Text)
    numeric_value = Column(Numeric(30, 12))
    unit = Column(String(64))
    quantity_type = Column(String(128))
    condition = Column(String(1000))
    confidence = Column(Numeric(5, 4), nullable=False)
    confidence_rationale = Column(String(2000), nullable=False)
    uncertainty = Column(String(2000))
    assumptions = Column(JSON, nullable=False, default=list, server_default="[]")
    proposed_canonical_target = Column(String(64), nullable=False)
    reviewed_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"))
    reviewed_at = Column(DateTime(timezone=True))
    version = Column(Integer, nullable=False, default=1, server_default="1")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class CandidateSourceLocatorLink(Base):
    __tablename__ = "candidate_source_locator_links"
    __table_args__ = (
        UniqueConstraint("candidate_id", "ordinal", name="uq_candidate_locator_ordinal"),
        CheckConstraint("ordinal >= 0", name="ck_candidate_locator_ordinal"),
    )
    candidate_id = Column(PGUUID(as_uuid=True), ForeignKey("document_engineering_candidates.id", ondelete="RESTRICT"), primary_key=True)
    source_locator_id = Column(PGUUID(as_uuid=True), ForeignKey("source_locators.id", ondelete="RESTRICT"), primary_key=True)
    ordinal = Column(Integer, nullable=False)


class EvidenceSourceLocatorLink(Base):
    __tablename__ = "evidence_source_locator_links"
    __table_args__ = (
        UniqueConstraint("evidence_id", "ordinal", name="uq_evidence_locator_ordinal"),
        CheckConstraint("ordinal >= 0 AND evidence_version >= 1", name="ck_evidence_locator_version"),
    )
    evidence_id = Column(PGUUID(as_uuid=True), ForeignKey("evidence.id", ondelete="RESTRICT"), primary_key=True)
    source_locator_id = Column(PGUUID(as_uuid=True), ForeignKey("source_locators.id", ondelete="RESTRICT"), primary_key=True)
    ordinal = Column(Integer, nullable=False)
    evidence_version = Column(Integer, nullable=False)
    linked_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    linked_at = Column(DateTime(timezone=True), nullable=False)


class DocumentCandidateReview(Base):
    __tablename__ = "document_candidate_reviews"
    __table_args__ = (
        UniqueConstraint("candidate_id", "candidate_version", name="uq_document_candidate_review_version"),
        CheckConstraint("action IN ('accept','correct','reject','defer')", name="ck_document_candidate_review_action"),
        CheckConstraint("candidate_version >= 1", name="ck_document_candidate_review_version"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    candidate_id = Column(PGUUID(as_uuid=True), ForeignKey("document_engineering_candidates.id", ondelete="RESTRICT"), nullable=False)
    candidate_version = Column(Integer, nullable=False)
    action = Column(String(16), nullable=False)
    rationale = Column(String(2000), nullable=False)
    correction = Column(JSON)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)


class DocumentPromotionReceipt(Base):
    __tablename__ = "document_promotion_receipts"
    __table_args__ = (
        UniqueConstraint("candidate_id", "candidate_version", name="uq_document_promotion_candidate_version"),
        CheckConstraint("candidate_version >= 1", name="ck_document_promotion_candidate_version"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    candidate_id = Column(PGUUID(as_uuid=True), ForeignKey("document_engineering_candidates.id", ondelete="RESTRICT"), nullable=False)
    candidate_version = Column(Integer, nullable=False)
    evidence_id = Column(PGUUID(as_uuid=True), ForeignKey("evidence.id", ondelete="RESTRICT"), nullable=False)
    engineering_context_id = Column(BigInteger, ForeignKey("engineering_contexts.id", ondelete="RESTRICT"))
    promoted_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    rationale = Column(String(2000), nullable=False)
    promoted_at = Column(DateTime(timezone=True), nullable=False)


class DocumentCorrelation(Base):
    __tablename__ = "document_correlations"
    __table_args__ = (
        UniqueConstraint("result_digest", name="uq_document_correlation_digest"),
        CheckConstraint("rule_version >= 1", name="ck_document_correlation_rule_version"),
        CheckConstraint("result_digest ~ '^[0-9a-f]{64}$'", name="ck_document_correlation_result_digest"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"))
    left_candidate_id = Column(PGUUID(as_uuid=True), ForeignKey("document_engineering_candidates.id", ondelete="RESTRICT"), nullable=False)
    right_candidate_id = Column(PGUUID(as_uuid=True), ForeignKey("document_engineering_candidates.id", ondelete="RESTRICT"))
    rule_id = Column(String(128), nullable=False)
    rule_version = Column(Integer, nullable=False)
    applicability = Column(String(2000), nullable=False)
    result = Column(JSON, nullable=False)
    result_digest = Column(String(64), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)


class DocumentFindingRecord(Base):
    __tablename__ = "document_findings"
    __table_args__ = (CheckConstraint("kind IN ('missing_information','discrepancy')", name="ck_document_finding_kind"), CheckConstraint("state IN ('open','acknowledged','resolved','deferred')", name="ck_document_finding_state"))
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    correlation_id = Column(PGUUID(as_uuid=True), ForeignKey("document_correlations.id", ondelete="RESTRICT"), nullable=False)
    kind = Column(String(32), nullable=False)
    state = Column(String(16), nullable=False, default="open", server_default="open")
    title = Column(String(500), nullable=False)
    explanation = Column(String(4000), nullable=False)
    uncertainty = Column(String(2000))
    created_at = Column(DateTime(timezone=True), nullable=False)


class DocumentIntelligenceIdempotency(Base):
    __tablename__ = "document_intelligence_idempotency"
    __table_args__ = (
        UniqueConstraint("organization_id", "actor_id", "operation", "idempotency_id", name="uq_document_intelligence_idempotency"),
        CheckConstraint("status IN ('pending','completed')", name="ck_document_intelligence_idempotency_status"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    operation = Column(String(64), nullable=False)
    idempotency_id = Column(PGUUID(as_uuid=True), nullable=False)
    request_fingerprint = Column(String(64), nullable=False)
    status = Column(String(16), nullable=False, default="pending", server_default="pending")
    aggregate_id = Column(PGUUID(as_uuid=True), ForeignKey("document_analysis_runs.id", ondelete="RESTRICT"))
    result = Column(JSON)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class DocumentIntelligenceOutbox(Base):
    __tablename__ = "document_intelligence_outbox"
    __table_args__ = (
        CheckConstraint("aggregate_version >= 1", name="ck_document_intelligence_outbox_version"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_id = Column(PGUUID(as_uuid=True), nullable=False, unique=True, default=uuid4)
    aggregate_id = Column(PGUUID(as_uuid=True), ForeignKey("document_analysis_runs.id", ondelete="RESTRICT"), nullable=False)
    aggregate_version = Column(Integer, nullable=False)
    event_type = Column(String(96), nullable=False)
    payload = Column(JSON, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
