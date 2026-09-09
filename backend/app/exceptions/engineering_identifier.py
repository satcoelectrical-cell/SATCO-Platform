"""Stable transport-neutral ADR-025 failures."""

from app.exceptions.base import SatcoException


class EngineeringIdentifierError(SatcoException):
    status_code = 422
    code = "ENGINEERING_IDENTIFIER_INVALID"
    message = "Engineering Identifier is invalid"

    def __init__(self, message: str | None = None):
        super().__init__(self.status_code, self.code, message or self.message)


class EngineeringIdentifierProtectedNotFound(EngineeringIdentifierError):
    status_code = 404
    code = "ENGINEERING_IDENTIFIER_NOT_FOUND"
    message = "Engineering Identifier was not found"


class EngineeringIdentifierConflict(EngineeringIdentifierError):
    status_code = 409
    code = "ENGINEERING_IDENTIFIER_CONFLICT"
    message = "Engineering Identifier conflicts with current state"


class EngineeringIdentifierLimitExceeded(EngineeringIdentifierConflict):
    code = "ENGINEERING_IDENTIFIER_LIMIT_EXCEEDED"
    message = "Engineering Object already has sixteen current Identifiers"
