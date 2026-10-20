"""Provider-neutral Document Intelligence vocabulary for Golden Demo V1."""

from enum import StrEnum


class DocumentFamily(StrEnum):
    NARRATIVE_ENGINEERING = "narrative_engineering"
    TABULAR_ENGINEERING = "tabular_engineering"


class DocumentAnalysisState(StrEnum):
    QUEUED = "queued"
    EXTRACTING = "extracting"
    INTERPRETING = "interpreting"
    REQUIRES_REVIEW = "requires_review"
    COMPLETED = "completed"
    COMPLETED_WITH_LIMITATIONS = "completed_with_limitations"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    FAILED_RETRYABLE = "failed_retryable"
    FAILED_TERMINAL = "failed_terminal"
    SOURCE_CHANGED = "source_changed"
    SUPERSEDED = "superseded"


class CandidateKind(StrEnum):
    DOCUMENT_IDENTITY = "document_identity"
    ENGINEERING_ENTITY = "engineering_entity"
    ENGINEERING_FACT = "engineering_fact"
    ENGINEERING_VALUE = "engineering_value"
    ASSUMPTION = "assumption"
    RELATIONSHIP = "relationship"
    CONTROL_STATEMENT = "control_statement"
    MISSING_INFORMATION = "missing_information"
    DISCREPANCY = "discrepancy"


class CandidateAssertionMode(StrEnum):
    DIRECT = "direct"
    DERIVED = "derived"
    INFERRED = "inferred"


class CandidateReviewState(StrEnum):
    UNREVIEWED = "unreviewed"
    ACCEPTED = "accepted"
    CORRECTED = "corrected"
    REJECTED = "rejected"
    DEFERRED = "deferred"


class CandidateReviewAction(StrEnum):
    ACCEPT = "accept"
    CORRECT = "correct"
    REJECT = "reject"
    DEFER = "defer"


class SourceLocatorKind(StrEnum):
    DOCUMENT = "document"
    PAGE = "page"
    TEXT_SPAN = "text_span"
    TABLE = "table"
    TABLE_ROW = "table_row"
    TABLE_CELL = "table_cell"


class ExtractionStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"


class SemanticProviderStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    REFUSED = "refused"
    DISABLED = "disabled"
    UNAVAILABLE = "unavailable"
    TIMED_OUT = "timed_out"
    INVALID_RESPONSE = "invalid_response"


class FindingKind(StrEnum):
    MISSING_INFORMATION = "missing_information"
    DISCREPANCY = "discrepancy"


class FindingState(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DEFERRED = "deferred"
