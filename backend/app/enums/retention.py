"""PATCH-055 closed retention-governance vocabularies."""
from enum import Enum


class RetentionSubjectKind(str, Enum):
    EVIDENCE = "evidence"
    SUPPORTING_FILE = "supporting_file"


class RetentionMode(str, Enum):
    RETAIN_UNTIL = "retain_until"
    RETAIN_INDEFINITELY = "retain_indefinitely"


class RetentionPolicySource(str, Enum):
    PLATFORM_DEFAULT = "platform_default"
    ORGANIZATION_DEFAULT = "organization_default"
    HUMAN_SUBJECT_OVERRIDE = "human_subject_override"


class HoldStatus(str, Enum):
    ACTIVE = "active"
    RELEASED = "released"


class DispositionEligibility(str, Enum):
    NOT_ELIGIBLE = "not_eligible"
    ELIGIBLE = "eligible"
    BLOCKED_BY_HOLD = "blocked_by_hold"
    INDETERMINATE = "indeterminate"


class DispositionDecision(str, Enum):
    NONE = "none"
    RETAIN = "retain"
    APPROVE_DISPOSITION = "approve_disposition"


class RecoveryStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    AVAILABLE = "available"
    TEMPORARILY_UNAVAILABLE = "temporarily_unavailable"
    RECOVERED = "recovered"
    UNRECOVERABLE = "unrecoverable"


class ExportStatus(str, Enum):
    REQUESTED = "requested"
    COMPLETED = "completed"
    FAILED = "failed"
