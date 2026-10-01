"""Pure effective-state vocabulary and evaluation for PATCH-059."""

from datetime import datetime, timezone
from enum import StrEnum

class CommercialEntitlementState(StrEnum):
    ACTIVE = "active"
    GRACE = "grace"
    EXPIRED = "expired"
    INVALID_OR_UNAVAILABLE = "invalid_or_unavailable"
    TIME_UNTRUSTED = "time_untrusted"


def effective_entitlement_state(
    state,
    observed_now: datetime,
) -> CommercialEntitlementState:
    """Evaluate persisted commercial state using the canonical time rules."""

    if observed_now.tzinfo is None or observed_now.utcoffset() is None:
        raise ValueError("observed_now must be timezone-aware")

    now = observed_now.astimezone(timezone.utc)
    if state.time_untrusted_at is not None:
        return CommercialEntitlementState.TIME_UNTRUSTED
    if now < state.not_before:
        return CommercialEntitlementState.INVALID_OR_UNAVAILABLE
    if now <= state.valid_until:
        return CommercialEntitlementState.ACTIVE
    if now <= state.grace_until:
        return CommercialEntitlementState.GRACE
    return CommercialEntitlementState.EXPIRED
