"""Transport-neutral Technical Report domain/application exceptions."""


class TechnicalReportException(ValueError):
    """Base Technical Report failure with a stable application code."""

    code = "TECHNICAL_REPORT_ERROR"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class TechnicalReportValidationError(TechnicalReportException):
    code = "TECHNICAL_REPORT_VALIDATION_ERROR"
    def __init__(self, message: str = "Technical Report validation failed") -> None: super().__init__(message)


class TechnicalReportInvalidLifecycle(TechnicalReportException):
    code = "TECHNICAL_REPORT_INVALID_LIFECYCLE"
    def __init__(self, message: str = "Invalid Technical Report lifecycle") -> None: super().__init__(message)


class TechnicalReportAcceptedImmutable(TechnicalReportException):
    code = "TECHNICAL_REPORT_ACCEPTED_IMMUTABLE"
    def __init__(self) -> None: super().__init__("Accepted Technical Report content is immutable")


class TechnicalReportVersionConflict(TechnicalReportException):
    code = "TECHNICAL_REPORT_VERSION_CONFLICT"
    def __init__(self) -> None: super().__init__("Technical Report was modified by another request")


class TechnicalReportIdempotencyConflict(TechnicalReportException):
    code = "TECHNICAL_REPORT_IDEMPOTENCY_CONFLICT"
    def __init__(self) -> None: super().__init__("Technical Report idempotency key conflicts with the request")


class TechnicalReportHistoricalBasisIncomplete(TechnicalReportException):
    code = "TECHNICAL_REPORT_HISTORICAL_BASIS_INCOMPLETE"
    def __init__(self, message: str = "Technical Report historical basis is incomplete") -> None: super().__init__(message)


class TechnicalReportIntegrityMismatch(TechnicalReportException):
    code = "TECHNICAL_REPORT_INTEGRITY_MISMATCH"
    def __init__(self) -> None: super().__init__("Technical Report historical basis integrity check failed")


class TechnicalReportInvalidLineage(TechnicalReportException):
    code = "TECHNICAL_REPORT_INVALID_LINEAGE"
    def __init__(self, message: str = "Invalid Technical Report lineage") -> None: super().__init__(message)


class TechnicalReportAuthorizationDenied(TechnicalReportException):
    code = "TECHNICAL_REPORT_AUTHORIZATION_DENIED"
    def __init__(self) -> None: super().__init__("Technical Report operation is not authorized")


class TechnicalReportAcceptanceAuthorityDenied(TechnicalReportAuthorizationDenied):
    """Internal classification for a safely detected Human-owner denial."""



class TechnicalReportAssistantUnavailable(TechnicalReportException):
    code = "TECHNICAL_REPORT_ASSISTANT_UNAVAILABLE"
    def __init__(self) -> None: super().__init__("Technical Report assistant is unavailable")
