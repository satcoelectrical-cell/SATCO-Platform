"""Stable Evidence application errors."""
from app.exceptions.base import SatcoException

class EvidenceError(SatcoException):
    code = "EVIDENCE_INTERNAL_ERROR"
    status_code = 500
    def __init__(self, message: object | None = None):
        super().__init__(self.status_code, self.code, str(message or self.code))

class EvidenceValidationError(EvidenceError):
    code = "EVIDENCE_VALIDATION_ERROR"; status_code = 422
class EvidenceAuthorizationDenied(EvidenceError):
    code = "EVIDENCE_AUTHORIZATION_DENIED"; status_code = 403
class EvidenceProtectedNotFound(EvidenceError):
    code = "EVIDENCE_NOT_FOUND"; status_code = 404
class EvidenceVersionConflict(EvidenceError):
    code = "EVIDENCE_VERSION_CONFLICT"; status_code = 409
class EvidenceIdempotencyConflict(EvidenceError):
    code = "EVIDENCE_IDEMPOTENCY_CONFLICT"; status_code = 409
class EvidenceInvalidTransition(EvidenceError):
    code = "EVIDENCE_INVALID_TRANSITION"; status_code = 409
