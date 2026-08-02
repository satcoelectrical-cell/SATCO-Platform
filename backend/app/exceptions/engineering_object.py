"""Stable application exceptions for the EngineeringObject API contract."""

from uuid import UUID

from app.exceptions.base import SatcoException


class EngineeringObjectException(SatcoException):
    """Base class for stable EngineeringObject application failures."""


class EngineeringObjectValidationError(EngineeringObjectException):
    """Request or application validation failed before domain mutation."""

    def __init__(self, message: str = "Engineering Object validation failed"):
        super().__init__(422, "ENGINEERING_OBJECT_VALIDATION_ERROR", message)


class EngineeringObjectAuthorizationDenied(EngineeringObjectException):
    """A denial that policy explicitly permits the API to disclose."""

    def __init__(self):
        super().__init__(
            403,
            "ENGINEERING_OBJECT_AUTHORIZATION_DENIED",
            "Engineering Object operation is not authorized",
        )


class EngineeringObjectProtectedNotFound(EngineeringObjectException):
    """Absent or inaccessible object without existence disclosure."""

    def __init__(self, object_id: UUID | None = None):
        message = "Engineering Object not found"
        if object_id is not None:
            message = f"Engineering Object {object_id} not found"
        super().__init__(404, "ENGINEERING_OBJECT_NOT_FOUND", message)


class EngineeringObjectVersionConflict(EngineeringObjectException):
    """Optimistic compare-and-change rejected a stale command."""

    def __init__(self):
        super().__init__(
            409,
            "ENGINEERING_OBJECT_VERSION_CONFLICT",
            "Engineering Object was modified by another request",
        )


class EngineeringObjectIdempotencyConflict(EngineeringObjectException):
    """An idempotency identifier was reused with different command content."""

    def __init__(self):
        super().__init__(
            409,
            "ENGINEERING_OBJECT_IDEMPOTENCY_CONFLICT",
            "Idempotency identifier conflicts with a prior request",
        )


class EngineeringObjectInvalidDomainTransition(EngineeringObjectException):
    """The aggregate rejected a prohibited transition or mutation."""

    def __init__(self, message: str = "Invalid Engineering Object transition"):
        super().__init__(
            409,
            "ENGINEERING_OBJECT_INVALID_DOMAIN_TRANSITION",
            message,
        )


class EngineeringObjectInternalServerError(EngineeringObjectException):
    """Stable protected response for an unexpected application failure."""

    def __init__(self):
        super().__init__(
            500,
            "ENGINEERING_OBJECT_INTERNAL_SERVER_ERROR",
            "An unexpected Engineering Object error occurred",
        )

