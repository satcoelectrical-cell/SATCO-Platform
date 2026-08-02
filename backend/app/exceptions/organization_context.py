"""Stable failures for trusted Organization-context resolution."""

from app.exceptions.base import SatcoException


class ActiveOrganizationContextRequired(SatcoException):
    """No unique enabled membership in an active Organization is selected."""

    def __init__(self):
        super().__init__(
            status_code=403,
            code="ACTIVE_ORGANIZATION_CONTEXT_REQUIRED",
            message="An active Organization context is required",
        )

