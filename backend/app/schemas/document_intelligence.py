"""Strict customer/API contracts for provider-neutral Document Intelligence."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.enums.document_intelligence import (
    CandidateAssertionMode,
    CandidateKind,
    CandidateReviewAction,
    CandidateReviewState,
    DocumentAnalysisState,
    DocumentFamily,
    ExtractionStatus,
    FindingKind,
    FindingState,
    SemanticProviderStatus,
)
from app.schemas.source_locator import SourceLocatorV1


class StrictContract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DocumentAnalysisCreate(StrictContract):
    workspace_id: int | None = Field(default=None, gt=0)
    supporting_file_asset_id: UUID
    expected_asset_version: int = Field(gt=0)
    expected_content_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    family_hint: DocumentFamily | None = None
    rationale: str = Field(min_length=1, max_length=2000)


class DocumentAnalysisProgress(StrictContract):
    completed_units: int = Field(ge=0)
    total_units: int | None = Field(default=None, ge=0)
    customer_message: str = Field(min_length=1, max_length=500)


class DocumentAnalysisSummary(StrictContract):
    analysis_run_id: UUID
    project_id: int = Field(gt=0)
    workspace_id: int | None = Field(default=None, gt=0)
    supporting_file_asset_id: UUID
    source_asset_version: int = Field(gt=0)
    source_content_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    safe_filename: str = Field(min_length=1, max_length=255)
    state: DocumentAnalysisState
    document_family: DocumentFamily | None = None
    progress: DocumentAnalysisProgress
    page_count: int | None = Field(default=None, ge=0)
    candidate_count: int = Field(default=0, ge=0)
    unreviewed_count: int = Field(default=0, ge=0)
    limitations: tuple[str, ...] = Field(default=(), max_length=50)
    allowed_actions: tuple[str, ...] = ()
    version: int = Field(gt=0)
    created_at: datetime
    updated_at: datetime


class DocumentAnalysisListResponse(StrictContract):
    items: tuple[DocumentAnalysisSummary, ...]
    total: int = Field(ge=0)


class DocumentAnalysisRetryRequest(StrictContract):
    expected_version: int = Field(gt=0)


class EngineeringCandidateValue(StrictContract):
    raw_value: str = Field(min_length=1, max_length=4000)
    normalized_value: str | None = Field(default=None, max_length=4000)
    numeric_value: Decimal | None = None
    unit: str | None = Field(default=None, max_length=64)
    quantity_type: str | None = Field(default=None, max_length=128)
    condition: str | None = Field(default=None, max_length=1000)


class EngineeringCandidate(StrictContract):
    candidate_id: UUID
    analysis_run_id: UUID
    version: int = Field(gt=0)
    ordinal: int = Field(ge=0)
    kind: CandidateKind
    assertion_mode: CandidateAssertionMode
    review_state: CandidateReviewState
    subject_key: str | None = Field(default=None, max_length=256)
    subject_label: str | None = Field(default=None, max_length=500)
    value: EngineeringCandidateValue
    confidence: Decimal = Field(ge=0, le=1)
    confidence_rationale: str = Field(min_length=1, max_length=2000)
    uncertainty: str | None = Field(default=None, max_length=2000)
    assumptions: tuple[str, ...] = Field(default=(), max_length=20)
    proposed_canonical_target: Literal[
        "evidence", "engineering_context_fact", "engineering_context_value",
        "engineering_context_assumption", "none"
    ]
    locators: tuple[SourceLocatorV1, ...] = Field(min_length=1, max_length=20)
    allowed_actions: tuple[CandidateReviewAction, ...] = ()
    promotion_receipt_id: UUID | None = None
    promoted_evidence_id: UUID | None = None
    promoted_engineering_context_id: int | None = Field(default=None, gt=0)
    allowed_promotions: tuple[
        Literal["evidence", "evidence_and_context"], ...
    ] = ()
    reviewed_by_id: int | None = Field(default=None, gt=0)
    reviewed_at: datetime | None = None

    @model_validator(mode="after")
    def precise_source_required(self):
        if not any(locator.page_index is not None for locator in self.locators):
            raise ValueError("reviewable candidate requires a page-level locator")
        return self


class EngineeringCandidateListResponse(StrictContract):
    items: tuple[EngineeringCandidate, ...]
    total: int = Field(ge=0)
    reviewed_count: int = Field(ge=0)
    unreviewed_count: int = Field(ge=0)


class CandidateCorrection(StrictContract):
    value: EngineeringCandidateValue
    subject_key: str | None = Field(default=None, max_length=256)
    subject_label: str | None = Field(default=None, max_length=500)
    uncertainty: str | None = Field(default=None, max_length=2000)


class CandidateReviewRequest(StrictContract):
    expected_version: int = Field(gt=0)
    action: CandidateReviewAction
    rationale: str = Field(min_length=1, max_length=2000)
    correction: CandidateCorrection | None = None

    @model_validator(mode="after")
    def correction_matches_action(self):
        if self.action is CandidateReviewAction.CORRECT and self.correction is None:
            raise ValueError("correct action requires correction")
        if self.action is not CandidateReviewAction.CORRECT and self.correction is not None:
            raise ValueError("correction is valid only for correct action")
        return self


class DocumentPromotionRequest(StrictContract):
    expected_candidate_version: int = Field(gt=0)
    include_engineering_context: bool = True
    rationale: str = Field(min_length=1, max_length=2000)


class DocumentPromotionResponse(StrictContract):
    promotion_receipt_id: UUID
    candidate_id: UUID
    candidate_version: int = Field(gt=0)
    evidence_id: UUID
    evidence_version: int = Field(gt=0)
    evidence_lifecycle: Literal["proposed"] = "proposed"
    engineering_context_id: int | None = Field(default=None, gt=0)
    source_locator_ids: tuple[UUID, ...] = Field(min_length=1, max_length=20)
    promoted_at: datetime
    promoted_by_id: int = Field(gt=0)


class DocumentEvidenceSource(BaseModel):
    """Immutable binding from one correlation source to its exact locator."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    analysis_run_id: UUID
    candidate_id: UUID
    locator: SourceLocatorV1


class DocumentFinding(StrictContract):
    finding_id: UUID
    analysis_run_ids: tuple[UUID, ...] = Field(min_length=1, max_length=20)
    kind: FindingKind
    state: FindingState
    title: str = Field(min_length=1, max_length=500)
    explanation: str = Field(min_length=1, max_length=4000)
    rule_id: str = Field(min_length=1, max_length=128)
    rule_version: int = Field(gt=0)
    applicability: str = Field(min_length=1, max_length=2000)
    uncertainty: str | None = Field(default=None, max_length=2000)
    evidence_sources: tuple[DocumentEvidenceSource, ...] = Field(
        default=(), max_length=40,
    )
    # Backward-compatible locator-only representation. New clients must use
    # evidence_sources so provenance is never inferred from array position.
    evidence: tuple[SourceLocatorV1, ...] = Field(min_length=1, max_length=40)
    advisory: Literal[True] = True


class DocumentCorrelationRequest(StrictContract):
    analysis_run_ids: tuple[UUID, ...] = Field(min_length=2, max_length=20)
    rule_pack_id: Literal["satco.document-correlation.v2"] = "satco.document-correlation.v2"
    rationale: str = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def unique_runs(self):
        if len(set(self.analysis_run_ids)) != len(self.analysis_run_ids):
            raise ValueError("analysis runs must be unique")
        return self


class DocumentCorrelationView(StrictContract):
    correlation_id: UUID
    analysis_run_ids: tuple[UUID, ...] = Field(min_length=1, max_length=2)
    rule_id: str = Field(min_length=1, max_length=128)
    rule_version: int = Field(gt=0)
    status: Literal["consistent", "discrepant", "missing_information"]
    summary: str = Field(min_length=1, max_length=2000)
    applicability: str = Field(min_length=1, max_length=2000)
    reason_codes: tuple[str, ...] = Field(min_length=1, max_length=20)
    uncertainty: str | None = Field(default=None, max_length=2000)
    evidence_sources: tuple[DocumentEvidenceSource, ...] = Field(
        default=(), max_length=40,
    )
    # Retained for existing API consumers; ordering has no binding semantics.
    evidence: tuple[SourceLocatorV1, ...] = Field(min_length=1, max_length=40)
    finding_id: UUID | None = None
    advisory: Literal[True] = True


class DocumentCorrelationEvaluation(StrictContract):
    rule_pack_id: Literal["satco.document-correlation.v2"]
    rule_pack_version: Literal[2]
    evaluated_run_ids: tuple[UUID, ...] = Field(min_length=2, max_length=20)
    correlations: tuple[DocumentCorrelationView, ...]
    findings: tuple[DocumentFinding, ...]


class DocumentCorrelationPage(StrictContract):
    items: tuple[DocumentCorrelationView, ...]
    total: int = Field(ge=0)


class DocumentFindingPage(StrictContract):
    items: tuple[DocumentFinding, ...]
    total: int = Field(ge=0)


class DocumentReportDraftRequest(StrictContract):
    workspace_id: int = Field(gt=0)
    finding_ids: tuple[UUID, ...] = Field(min_length=1, max_length=20)
    purpose: Literal[
        "field_experience", "troubleshooting", "engineering_analysis",
        "technical_recommendation",
    ] = "engineering_analysis"
    rationale: str = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def unique_findings(self):
        if len(set(self.finding_ids)) != len(self.finding_ids):
            raise ValueError("findings must be unique")
        return self


class DocumentReportDraftResponse(StrictContract):
    report_id: UUID
    version: int = Field(gt=0)
    draft_revision_id: UUID
    lifecycle: Literal["draft"] = "draft"
    preliminary: Literal[True] = True
    finding_ids: tuple[UUID, ...] = Field(min_length=1, max_length=20)


class ExtractedCellBoundingBoxV1(StrictContract):
    """Auditable cell geometry, normalized to the extracted PDF page."""

    coordinate_space: Literal["normalized_page_v1"] = "normalized_page_v1"
    x0: float = Field(ge=0.0, le=1.0)
    top: float = Field(ge=0.0, le=1.0)
    x1: float = Field(ge=0.0, le=1.0)
    bottom: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def positive_area(self):
        if self.x1 <= self.x0 or self.bottom <= self.top:
            raise ValueError("cell bounding box must have positive area")
        return self


class ExtractedTableCellLocatorV1(StrictContract):
    """Stable pointer and optional geometry for one raw table-grid cell."""

    schema_version: Literal[1] = 1
    locator_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    document_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    page_index: int = Field(ge=0)
    table_index: int = Field(ge=0)
    row_index: int = Field(ge=0)
    column_index: int = Field(ge=0)
    raw_value: str = Field(max_length=4000)
    bounding_box: ExtractedCellBoundingBoxV1 | None = None


class ExtractedPageV1(StrictContract):
    page_index: int = Field(ge=0)
    page_label: str | None = Field(default=None, max_length=64)
    status: ExtractionStatus
    text: str = Field(default="", max_length=2_000_000)
    tables: tuple[tuple[tuple[str, ...], ...], ...] = Field(default=(), max_length=100)
    cell_locators: tuple[ExtractedTableCellLocatorV1, ...] = Field(
        default=(), max_length=200_000
    )
    warnings: tuple[str, ...] = Field(default=(), max_length=20)

    @model_validator(mode="after")
    def coherent_cell_locators(self):
        if not self.cell_locators:
            return self
        expected = [
            (table_index, row_index, column_index, value)
            for table_index, table in enumerate(self.tables)
            for row_index, row in enumerate(table)
            for column_index, value in enumerate(row)
        ]
        actual = [
            (item.table_index, item.row_index, item.column_index, item.raw_value)
            for item in self.cell_locators
        ]
        if any(item.page_index != self.page_index for item in self.cell_locators):
            raise ValueError("cell locator page must match extracted page")
        if actual != expected:
            raise ValueError("cell locators must exactly cover the extracted table grid")
        if len({item.locator_id for item in self.cell_locators}) != len(self.cell_locators):
            raise ValueError("cell locator identifiers must be unique")
        return self


class ExtractedDocumentV1(StrictContract):
    schema_version: Literal[1] = 1
    status: ExtractionStatus
    media_type: Literal["application/pdf"]
    page_count: int = Field(ge=0)
    pages: tuple[ExtractedPageV1, ...]
    detected_languages: tuple[str, ...] = Field(default=(), max_length=20)
    warnings: tuple[str, ...] = Field(default=(), max_length=50)
    parser_id: str = Field(min_length=1, max_length=128)
    parser_version: str = Field(min_length=1, max_length=128)
    input_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_digest: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def complete_page_inventory(self):
        if len(self.pages) != self.page_count:
            raise ValueError("page inventory must match page_count")
        if tuple(page.page_index for page in self.pages) != tuple(range(self.page_count)):
            raise ValueError("page inventory must be ordered and complete")
        if any(
            item.document_digest != self.input_digest
            for page in self.pages
            for item in page.cell_locators
        ):
            raise ValueError("cell locator document must match extracted document")
        return self


class SemanticDocumentRequestV1(StrictContract):
    schema_version: Literal[1] = 1
    request_id: UUID
    analysis_run_id: UUID
    document_family: DocumentFamily
    document: ExtractedDocumentV1
    allowed_candidate_kinds: tuple[CandidateKind, ...]
    safety_policy_id: Literal["satco.document-data-only.v1"] = "satco.document-data-only.v1"
    maximum_candidates: int = Field(default=5000, ge=1, le=5000)


class ProviderSourceCellReferenceV1(StrictContract):
    """Server-verifiable table-cell coordinates returned by a semantic provider."""

    page_index: int = Field(ge=0)
    table_index: int = Field(ge=0)
    row_index: int = Field(ge=0)
    column_index: int = Field(ge=0)


class ProviderCandidateV1(StrictContract):
    kind: CandidateKind
    assertion_mode: CandidateAssertionMode
    subject_key: str | None = Field(default=None, max_length=256)
    subject_label: str | None = Field(default=None, max_length=500)
    value: EngineeringCandidateValue
    confidence: Decimal = Field(ge=0, le=1)
    confidence_rationale: str = Field(min_length=1, max_length=2000)
    uncertainty: str | None = Field(default=None, max_length=2000)
    assumptions: tuple[str, ...] = Field(default=(), max_length=20)
    locator_indexes: tuple[int, ...] = Field(min_length=1, max_length=20)
    source_cell_references: tuple[ProviderSourceCellReferenceV1, ...] = Field(
        default=(), max_length=20
    )
    proposed_canonical_target: Literal[
        "evidence", "engineering_context_fact", "engineering_context_value",
        "engineering_context_assumption", "none"
    ]


class SemanticDocumentResponseV1(StrictContract):
    schema_version: Literal[1] = 1
    status: SemanticProviderStatus
    candidates: tuple[ProviderCandidateV1, ...] = Field(default=(), max_length=5000)
    warnings: tuple[str, ...] = Field(default=(), max_length=50)
    provider_id: str = Field(min_length=1, max_length=128)
    model_id: str = Field(min_length=1, max_length=128)
    model_version: str = Field(min_length=1, max_length=128)
    adapter_version: str = Field(min_length=1, max_length=128)
    input_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
