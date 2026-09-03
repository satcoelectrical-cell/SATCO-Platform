"""Closed enum vocabulary for the pure PATCH-051 Core contract."""

from enum import Enum


class DisciplinePackageStanding(str, Enum):
    EXECUTABLE_SUPPORTED = "executable_supported"
    HISTORICAL_READ_ONLY = "historical_read_only"


class CompatibilityDecision(str, Enum):
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    UNAVAILABLE = "unavailable"


class EntitlementDecision(str, Enum):
    NOT_REQUIRED = "not_required"
    PERMITTED = "permitted"
    DENIED = "denied"
    UNAVAILABLE = "unavailable"


class EntitlementOperation(str, Enum):
    CONFIGURE = "configure"
    EXECUTE = "execute"
    HISTORICAL_READ = "historical_read"
