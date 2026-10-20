from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from app.services.commercial_entitlement_service import (
    RevisionDecision,
    TrustedTimeDecision,
    entitlement_temporal_state,
    evaluate_revision,
    evaluate_trusted_time,
)
from app.commercial_entitlements.canonical import EntitlementPayload


UTC = timezone.utc
ENTITLEMENT_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_ENTITLEMENT_ID = UUID("22222222-2222-4222-8222-222222222222")
DIGEST = "a" * 64
OTHER_DIGEST = "b" * 64


def test_initial_revision_advances_state():
    result = evaluate_revision(
        current_revision=None,
        current_entitlement_id=None,
        current_digest=None,
        incoming_revision=1,
        incoming_entitlement_id=ENTITLEMENT_ID,
        incoming_digest=DIGEST,
    )

    assert result.decision is RevisionDecision.INITIAL
    assert result.should_advance_state is True


def test_higher_revision_is_successor():
    result = evaluate_revision(
        current_revision=3,
        current_entitlement_id=ENTITLEMENT_ID,
        current_digest=DIGEST,
        incoming_revision=4,
        incoming_entitlement_id=OTHER_ENTITLEMENT_ID,
        incoming_digest=OTHER_DIGEST,
    )

    assert result.decision is RevisionDecision.SUCCESSOR
    assert result.should_advance_state is True


def test_lower_revision_is_rollback_detected():
    result = evaluate_revision(
        current_revision=4,
        current_entitlement_id=ENTITLEMENT_ID,
        current_digest=DIGEST,
        incoming_revision=3,
        incoming_entitlement_id=OTHER_ENTITLEMENT_ID,
        incoming_digest=OTHER_DIGEST,
    )

    assert result.decision is RevisionDecision.ROLLBACK_DETECTED
    assert result.should_advance_state is False


def test_equal_revision_same_identity_and_digest_is_idempotent():
    result = evaluate_revision(
        current_revision=4,
        current_entitlement_id=ENTITLEMENT_ID,
        current_digest=DIGEST,
        incoming_revision=4,
        incoming_entitlement_id=ENTITLEMENT_ID,
        incoming_digest=DIGEST,
    )

    assert result.decision is RevisionDecision.IDEMPOTENT
    assert result.should_advance_state is False


@pytest.mark.parametrize(
    ("incoming_entitlement_id", "incoming_digest"),
    (
        (OTHER_ENTITLEMENT_ID, DIGEST),
        (ENTITLEMENT_ID, OTHER_DIGEST),
        (OTHER_ENTITLEMENT_ID, OTHER_DIGEST),
    ),
)
def test_equal_revision_conflict_is_rejected(
    incoming_entitlement_id,
    incoming_digest,
):
    result = evaluate_revision(
        current_revision=4,
        current_entitlement_id=ENTITLEMENT_ID,
        current_digest=DIGEST,
        incoming_revision=4,
        incoming_entitlement_id=incoming_entitlement_id,
        incoming_digest=incoming_digest,
    )

    assert result.decision is RevisionDecision.SAME_REVISION_CONFLICT
    assert result.should_advance_state is False


def test_first_trusted_time_is_persisted():
    now = datetime(2026, 9, 30, 8, 0, tzinfo=UTC)

    result = evaluate_trusted_time(
        observed_now=now,
        last_trusted_time=None,
        time_untrusted_at=None,
    )

    assert result.decision is TrustedTimeDecision.TRUSTED
    assert result.effective_time == now
    assert result.should_persist_checkpoint is True


def test_forward_time_advances_monotonically():
    previous = datetime(2026, 9, 30, 8, 0, tzinfo=UTC)
    observed = previous + timedelta(minutes=4)

    result = evaluate_trusted_time(
        observed_now=observed,
        last_trusted_time=previous,
        time_untrusted_at=None,
    )

    assert result.decision is TrustedTimeDecision.TRUSTED
    assert result.effective_time == observed
    assert result.should_persist_checkpoint is True


def test_small_backward_jump_is_tolerated_without_lowering_checkpoint():
    trusted = datetime(2026, 9, 30, 8, 0, tzinfo=UTC)
    observed = trusted - timedelta(minutes=5)

    result = evaluate_trusted_time(
        observed_now=observed,
        last_trusted_time=trusted,
        time_untrusted_at=None,
    )

    assert result.decision is TrustedTimeDecision.TRUSTED
    assert result.effective_time == trusted
    assert result.should_persist_checkpoint is False


def test_more_than_five_minutes_backward_is_time_untrusted():
    trusted = datetime(2026, 9, 30, 8, 0, tzinfo=UTC)
    observed = trusted - timedelta(minutes=5, seconds=1)

    result = evaluate_trusted_time(
        observed_now=observed,
        last_trusted_time=trusted,
        time_untrusted_at=None,
    )

    assert result.decision is TrustedTimeDecision.TIME_UNTRUSTED
    assert result.effective_time == trusted
    assert result.should_persist_checkpoint is False


def test_recorded_time_untrusted_cannot_self_clear():
    trusted = datetime(2026, 9, 30, 8, 0, tzinfo=UTC)
    later = trusted + timedelta(hours=1)

    result = evaluate_trusted_time(
        observed_now=later,
        last_trusted_time=trusted,
        time_untrusted_at=trusted,
    )

    assert result.decision is TrustedTimeDecision.TIME_UNTRUSTED


def _payload() -> EntitlementPayload:
    return EntitlementPayload(
        schema_version=1,
        entitlement_id=ENTITLEMENT_ID,
        revision=1,
        organization_id=UUID(
            "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        ),
        deployment_id="satco-production",
        issuer="SATCO",
        issued_at=datetime(2026, 9, 1, tzinfo=UTC),
        not_before=datetime(2026, 9, 1, tzinfo=UTC),
        valid_until=datetime(2026, 9, 30, tzinfo=UTC),
        grace_until=datetime(2026, 10, 5, tzinfo=UTC),
        package_keys=(
            "control_automation",
            "electrical",
            "instrumentation",
        ),
        seat_capacity=10,
        support_until=None,
        baseline_release_sequence=1,
        max_release_sequence=10,
    )


def test_temporal_state_boundaries_are_inclusive():
    payload = _payload()

    assert entitlement_temporal_state(
        payload,
        trusted_now=payload.not_before,
    ) == "active"

    assert entitlement_temporal_state(
        payload,
        trusted_now=payload.valid_until,
    ) == "active"

    assert entitlement_temporal_state(
        payload,
        trusted_now=payload.valid_until + timedelta(seconds=1),
    ) == "grace"

    assert entitlement_temporal_state(
        payload,
        trusted_now=payload.grace_until,
    ) == "grace"

    assert entitlement_temporal_state(
        payload,
        trusted_now=payload.grace_until + timedelta(seconds=1),
    ) == "expired"


def test_temporal_state_before_not_before_is_not_yet_valid():
    payload = _payload()

    assert entitlement_temporal_state(
        payload,
        trusted_now=payload.not_before - timedelta(seconds=1),
    ) == "not_yet_valid"
