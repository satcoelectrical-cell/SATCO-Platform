"""Stable PATCH-026 EngineeringRelationship application exceptions."""

from uuid import UUID

from app.exceptions.base import SatcoException


class EngineeringRelationshipException(SatcoException):
    """Base stable relationship failure."""


class EngineeringRelationshipValidationError(EngineeringRelationshipException):
    def __init__(self, message: str = "Engineering Relationship validation failed"):
        super().__init__(422, "ENGINEERING_RELATIONSHIP_VALIDATION_ERROR", message)


class EngineeringRelationshipAuthorizationDenied(
    EngineeringRelationshipException
):
    def __init__(self):
        super().__init__(
            403, "ENGINEERING_RELATIONSHIP_AUTHORIZATION_DENIED",
            "Engineering Relationship operation is not authorized",
        )


class EngineeringRelationshipProtectedNotFound(
    EngineeringRelationshipException
):
    def __init__(self, relationship_id: UUID | None = None):
        message = "Engineering Relationship not found"
        if relationship_id is not None:
            message = f"Engineering Relationship {relationship_id} not found"
        super().__init__(404, "ENGINEERING_RELATIONSHIP_NOT_FOUND", message)


class EngineeringRelationshipDuplicate(EngineeringRelationshipException):
    def __init__(self):
        super().__init__(
            409, "ENGINEERING_RELATIONSHIP_DUPLICATE",
            "An active Engineering Relationship already exists",
        )


class EngineeringRelationshipCycleRejected(EngineeringRelationshipException):
    def __init__(self):
        super().__init__(
            409, "ENGINEERING_RELATIONSHIP_CYCLE_REJECTED",
            "Engineering Relationship would create a prohibited cycle",
        )


class EngineeringRelationshipVersionConflict(EngineeringRelationshipException):
    def __init__(self):
        super().__init__(
            409, "ENGINEERING_RELATIONSHIP_VERSION_CONFLICT",
            "Engineering Relationship was modified by another request",
        )


class EngineeringRelationshipIdempotencyConflict(
    EngineeringRelationshipException
):
    def __init__(self):
        super().__init__(
            409, "ENGINEERING_RELATIONSHIP_IDEMPOTENCY_CONFLICT",
            "Idempotency identifier conflicts with a prior request",
        )


class EngineeringRelationshipInvalidDomainTransition(
    EngineeringRelationshipException
):
    def __init__(self, message: str = "Invalid Engineering Relationship transition"):
        super().__init__(
            409, "ENGINEERING_RELATIONSHIP_INVALID_DOMAIN_TRANSITION", message
        )


class EngineeringRelationshipInternalServerError(
    EngineeringRelationshipException
):
    def __init__(self):
        super().__init__(
            500, "ENGINEERING_RELATIONSHIP_INTERNAL_SERVER_ERROR",
            "An unexpected Engineering Relationship error occurred",
        )
