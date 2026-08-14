"""Closed PATCH-035 AI Capture Assistant enums."""

from enum import Enum


class AdviceConfidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AdviceOutputKind(str, Enum):
    CAPTURE_REFINEMENT = "capture_refinement"


class AdviceRefusalCode(str, Enum):
    UNSAFE_AUTHORITY_REQUEST = "unsafe_authority_request"
    INSUFFICIENT_CONTEXT = "insufficient_context"


class ProviderAdviceStatus(str, Enum):
    SUCCESS = "success"
    REFUSED = "refused"


class AdviceOutcome(str, Enum):
    SUCCESS = "success"
    REFUSED = "refused"
    PROTECTED_NOT_FOUND = "protected_not_found"
    INVALID_REQUEST = "invalid_request"
    DISABLED = "disabled"
    UNAVAILABLE = "unavailable"
