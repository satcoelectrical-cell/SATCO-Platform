class EngineeringDeliverableUnavailable(Exception):
    """Infrastructure failure behind a payload-free result."""


class EngineeringDeliverableValidationError(ValueError):
    """Closed contract validation failure."""
