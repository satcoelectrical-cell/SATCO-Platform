from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID

import pytest

from app.commercial_entitlements.state import CommercialEntitlementState as EffectiveEntitlementState
from app.services.commercial_seat_service import (
    CommercialSeatError,
    CommercialSeatReason,
    CommercialSeatState,
    _effective_entitlement_state,
)


NOW = datetime(2026, 9, 30, 6, 0, tzinfo=timezone.utc)


def _state(**overrides):
    values = {
        "not_before": NOW - timedelta(days=1),
        "valid_until": NOW + timedelta(days=1),
        "grace_until": NOW + timedelta(days=2),
        "time_untrusted_at": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_effective_entitlement_state_active():
    assert (
        _effective_entitlement_state(_state(), NOW)
        is EffectiveEntitlementState.ACTIVE
    )


def test_effective_entitlement_state_grace():
    state = _state(valid_until=NOW - timedelta(seconds=1))
    assert (
        _effective_entitlement_state(state, NOW)
        is EffectiveEntitlementState.GRACE
    )


def test_effective_entitlement_state_expired():
    state = _state(
        valid_until=NOW - timedelta(days=2),
        grace_until=NOW - timedelta(seconds=1),
    )
    assert (
        _effective_entitlement_state(state, NOW)
        is EffectiveEntitlementState.EXPIRED
    )


def test_effective_entitlement_state_time_untrusted_is_sticky():
    state = _state(time_untrusted_at=NOW - timedelta(minutes=1))
    assert (
        _effective_entitlement_state(state, NOW + timedelta(days=30))
        is EffectiveEntitlementState.TIME_UNTRUSTED
    )


def test_effective_entitlement_state_before_not_before_is_unavailable():
    state = _state(not_before=NOW + timedelta(seconds=1))
    assert (
        _effective_entitlement_state(state, NOW)
        is EffectiveEntitlementState.INVALID_OR_UNAVAILABLE
    )


def test_seat_states_are_frozen():
    assert {state.value for state in CommercialSeatState} == {
        "ASSIGNED",
        "RESERVED",
        "RETAINED",
    }


def test_reason_codes_are_bounded():
    assert CommercialSeatReason.SEAT_REQUIRED.value == "seat_required"
    assert CommercialSeatReason.SEAT_RESERVED.value == "seat_reserved"
    assert CommercialSeatReason.OVER_CAPACITY.value == "over_capacity"


def test_seat_error_exposes_only_reason_code():
    error = CommercialSeatError(CommercialSeatReason.OVER_CAPACITY)
    assert error.reason_code == "over_capacity"
    assert str(error) == "over_capacity"


def test_uuid_fixture_is_canonical():
    assert str(UUID("05900000-0000-4000-8000-000000000003")) == (
        "05900000-0000-4000-8000-000000000003"
    )
