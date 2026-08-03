"""Stable Engineering Experience Capture application errors."""

from app.exceptions.base import SatcoException


class EngineeringExperienceCaptureError(SatcoException):
    code = "ENGINEERING_EXPERIENCE_CAPTURE_INTERNAL_ERROR"
    status_code = 500

    def __init__(self, message: object | None = None):
        super().__init__(self.status_code, self.code, str(message or self.code))


class EngineeringExperienceCaptureValidationError(EngineeringExperienceCaptureError):
    code = "ENGINEERING_EXPERIENCE_CAPTURE_VALIDATION_ERROR"
    status_code = 422


class EngineeringExperienceCaptureAuthorizationDenied(EngineeringExperienceCaptureError):
    code = "ENGINEERING_EXPERIENCE_CAPTURE_AUTHORIZATION_DENIED"
    status_code = 403


class EngineeringExperienceCaptureProtectedNotFound(EngineeringExperienceCaptureError):
    code = "ENGINEERING_EXPERIENCE_CAPTURE_NOT_FOUND"
    status_code = 404


class EngineeringExperienceCaptureVersionConflict(EngineeringExperienceCaptureError):
    code = "ENGINEERING_EXPERIENCE_CAPTURE_VERSION_CONFLICT"
    status_code = 409


class EngineeringExperienceCaptureIdempotencyConflict(EngineeringExperienceCaptureError):
    code = "ENGINEERING_EXPERIENCE_CAPTURE_IDEMPOTENCY_CONFLICT"
    status_code = 409


class EngineeringExperienceCaptureInvalidLifecycleTransition(EngineeringExperienceCaptureError):
    code = "ENGINEERING_EXPERIENCE_CAPTURE_INVALID_LIFECYCLE_TRANSITION"
    status_code = 409


class EngineeringExperienceCaptureInvalidContext(EngineeringExperienceCaptureError):
    code = "ENGINEERING_EXPERIENCE_CAPTURE_INVALID_CONTEXT"
    status_code = 422


class EngineeringExperienceCaptureInvalidSupersession(EngineeringExperienceCaptureError):
    code = "ENGINEERING_EXPERIENCE_CAPTURE_INVALID_SUPERSESSION"
    status_code = 409


class EngineeringExperienceCaptureDuplicateSupersession(EngineeringExperienceCaptureError):
    code = "ENGINEERING_EXPERIENCE_CAPTURE_DUPLICATE_SUPERSESSION"
    status_code = 409


class EngineeringExperienceCaptureSupersessionCycle(EngineeringExperienceCaptureError):
    code = "ENGINEERING_EXPERIENCE_CAPTURE_SUPERSESSION_CYCLE"
    status_code = 409


class EngineeringExperienceCaptureContentLimitExceeded(EngineeringExperienceCaptureError):
    code = "ENGINEERING_EXPERIENCE_CAPTURE_CONTENT_LIMIT_EXCEEDED"
    status_code = 422
