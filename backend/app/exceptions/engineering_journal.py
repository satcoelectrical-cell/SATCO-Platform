"""Stable, disclosure-safe Engineering Journal application outcomes."""

from app.exceptions.base import SatcoException


class EngineeringJournalError(SatcoException):
    """Base Journal error with no protected implementation diagnostics."""

    code = "ENGINEERING_JOURNAL_INTERNAL_ERROR"
    status_code = 500

    def __init__(self, message: str | None = None) -> None:
        super().__init__(
            self.status_code,
            self.code,
            message or "Engineering Journal request failed",
        )


class EngineeringJournalProtectedNotFound(EngineeringJournalError):
    """Stable outcome for missing or unauthorized Journal resources."""

    code = "ENGINEERING_JOURNAL_NOT_FOUND"
    status_code = 404

    def __init__(self) -> None:
        super().__init__("Engineering Journal resource not found")


class EngineeringJournalInvalidPresentationCriteria(EngineeringJournalError):
    """Safe outcome for unsupported temporary presentation criteria."""

    code = "ENGINEERING_JOURNAL_INVALID_PRESENTATION_CRITERIA"
    status_code = 422

    def __init__(self) -> None:
        super().__init__("Engineering Journal presentation criteria are invalid")
