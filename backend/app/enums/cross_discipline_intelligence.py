"""Closed PATCH-053 Batch-1 machine vocabularies."""

from enum import StrEnum


class AssessmentStatus(StrEnum):
    COMPLETED_NO_FINDINGS = "completed_no_findings"
    COMPLETED_WITH_FINDINGS = "completed_with_findings"
    INDETERMINATE = "indeterminate"
    UNAVAILABLE = "unavailable"


class OperationOutcome(StrEnum):
    SUCCESS = "success"
    PROTECTED_NOT_FOUND = "protected_not_found"
    INVALID_REQUEST = "invalid_request"
    VERSION_CONFLICT = "version_conflict"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    INDETERMINATE = "indeterminate"
    UNAVAILABLE = "unavailable"


AssessmentOutcome = OperationOutcome


class AssessmentPurpose(StrEnum):
    INTERFACE_ASSESSMENT = "interface_assessment"
    CURRENT_HANDOFF_GATE = "current_handoff_gate"
    EXPLICIT_CHANGE_IMPACT = "explicit_change_impact"


class ReadinessState(StrEnum):
    READY = "ready"
    NOT_READY = "not_ready"
    UNAVAILABLE = "unavailable"
    PROTECTED_NOT_FOUND = "protected_not_found"


class EligibilityState(StrEnum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    INDETERMINATE = "indeterminate"
    UNAVAILABLE = "unavailable"
    PROTECTED_NOT_FOUND = "protected_not_found"


class FindingCategory(StrEnum):
    MISSING = "missing"
    INCONSISTENT = "inconsistent"
    STALE = "stale"
    DISPUTED = "disputed"
    UNFULFILLED_COMMITMENT = "unfulfilled_commitment"
    DEPENDENCY = "dependency"
    POTENTIAL_CHANGE_IMPACT = "potential_change_impact"
    INCOMPLETE_HANDOFF = "incomplete_handoff"


class FindingSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    MAJOR = "major"
    CRITICAL = "critical"


class DispositionAction(StrEnum):
    ACKNOWLEDGE = "acknowledge"
    CONFIRM = "confirm"
    REJECT_NOT_APPLICABLE = "reject_not_applicable"
    ACCEPT_RISK = "accept_risk"
    DECLARE_RESOLUTION = "declare_resolution"
    DISPUTE = "dispute"
    REQUIRE_REASSESSMENT = "require_reassessment"
    SUPERSEDE = "supersede"


class FindingViewState(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    CONFIRMED = "confirmed"
    REJECTED_NOT_APPLICABLE = "rejected_not_applicable"
    RISK_ACCEPTED = "risk_accepted"
    RESOLUTION_DECLARED = "resolution_declared"
    DISPUTED = "disputed"
    REASSESSMENT_REQUIRED = "reassessment_required"
    SUPERSEDED = "superseded"


class LineageKind(StrEnum):
    REASSESSMENT_OF = "reassessment_of"
    SUPERSEDES = "supersedes"


class ComparisonOutcome(StrEnum):
    SATISFIED = "satisfied"
    VIOLATED = "violated"
    NOT_APPLICABLE = "not_applicable"
    INDETERMINATE = "indeterminate"


class ValueType(StrEnum):
    BOOLEAN = "boolean"
    INTEGER = "integer"
    DECIMAL = "decimal"
    STRING = "string"
    TOKEN = "token"
    ENUM = "enum"
    QUANTITY = "quantity"
    REFERENCE = "reference"
    TIMESTAMP = "timestamp"
    DATE = "date"
    PRESENCE = "presence"
    SET = "set"
    RANGE = "range"


class GraphNodeKind(StrEnum):
    ENGINEERING_OBJECT = "engineering_object"
    ENGINEERING_IDENTIFIER = "engineering_identifier"
    ENGINEERING_CONTEXT = "engineering_context"
    EVIDENCE = "evidence"
    DELIVERABLE = "deliverable"
    DELIVERABLE_REVISION = "deliverable_revision"
    INTERFACE_COMMITMENT = "interface_commitment"
    PROJECT_CHANGE = "project_change"
    PROJECT_CHANGE_IMPACT = "project_change_impact"
    ASSESSED_INTERFACE_OCCURRENCE = "assessed_interface_occurrence"


class GraphEdgeKind(StrEnum):
    ENGINEERING_RELATIONSHIP = "engineering_relationship"
    CONTEXT_REQUIRES = "context_requires"
    CONTEXT_PROVIDED_BY = "context_provided_by"
    CONTEXT_CONSUMED_BY = "context_consumed_by"
    CONTEXT_POTENTIALLY_AFFECTS = "context_potentially_affects"
    COMMITMENT_GOVERNS = "commitment_governs"
    COMMITMENT_PROVIDER = "commitment_provider"
    COMMITMENT_CONSUMER = "commitment_consumer"
    COMMITMENT_SUPPLIED_SOURCE = "commitment_supplied_source"
    EVIDENCE_SUPPORTS = "evidence_supports"
    INTERFACE_PROVIDER = "interface_provider"
    INTERFACE_CONSUMER = "interface_consumer"
    ASSESSMENT_CHANGE_SEED = "assessment_change_seed"
    DEFINITION_EXPECTED_DEPENDENCY = "definition_expected_dependency"
