"""Pure effective-state vocabulary for PATCH-059."""
from enum import StrEnum

class CommercialEntitlementState(StrEnum):
    ACTIVE = "active"
    GRACE = "grace"
    EXPIRED = "expired"
    INVALID_OR_UNAVAILABLE = "invalid_or_unavailable"
    TIME_UNTRUSTED = "time_untrusted"
