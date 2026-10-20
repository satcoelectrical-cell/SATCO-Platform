from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID

import pytest

from app.commercial_entitlements.canonical import EntitlementEnvelope, EntitlementPayload
from app.services import commercial_entitlement_service as service


UTC = timezone.utc
NOW = datetime(2026, 9, 30, 12, 0, tzinfo=UTC)
ORG = UUID("05900000-0000-4000-8000-000000000001")
OTHER_ORG = UUID("05900000-0000-4000-8000-000000000002")
ENTITLEMENT = UUID("05900000-0000-4000-8000-000000000101")
DEPLOYMENT = "satco-production"


def _payload(**overrides):
    values = dict(
        schema_version=1,
        entitlement_id=ENTITLEMENT,
        revision=1,
        organization_id=ORG,
        deployment_id=DEPLOYMENT,
        issuer="SATCO",
        issued_at=NOW - timedelta(days=1),
        not_before=NOW - timedelta(hours=1),
        valid_until=NOW + timedelta(days=10),
        grace_until=NOW + timedelta(days=20),
        package_keys=("electrical",),
        seat_capacity=5,
        support_until=None,
        baseline_release_sequence=1,
        max_release_sequence=10,
    )
    values.update(overrides)
    return EntitlementPayload(**values)


def _envelope(payload=None):
    return EntitlementEnvelope(
        schema="satco.commercial-entitlement/v1",
        key_id="test-key",
        payload=payload or _payload(),
        signature="signature",
    )


@pytest.fixture(autouse=True)
def _verification(monkeypatch):
    monkeypatch.setattr(service, "verify_envelope", lambda *args, **kwargs: None)


def _preview(*, envelope=None, current=None):
    return service.preview_entitlement(
        envelope=envelope or _envelope(),
        trust_store=object(),
        current_state=current,
        expected_organization_id=ORG,
        expected_deployment_id=DEPLOYMENT,
        observed_now=NOW,
    )


def _current(**overrides):
    values = dict(
        accepted_revision=1,
        entitlement_id=ENTITLEMENT,
        canonical_payload_digest="a" * 64,
        last_trusted_time=NOW,
        time_untrusted_at=None,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def test_initial_candidate_is_valid_without_state_mutation():
    result = _preview()

    assert result.valid is True
    assert result.effect == "initial"
    assert result.reason_code is None


def test_successor_candidate_is_previewed():
    incoming = _payload(revision=4)
    digest = service.canonical_payload_digest(_payload(revision=3))
    current = _current(
        accepted_revision=3,
        canonical_payload_digest=digest,
    )

    result = _preview(envelope=_envelope(incoming), current=current)

    assert result.valid is True
    assert result.effect == "successor"


def test_idempotent_candidate_is_previewed():
    payload = _payload(revision=3)
    digest = service.canonical_payload_digest(payload)
    current = _current(
        accepted_revision=3,
        canonical_payload_digest=digest,
    )

    result = _preview(envelope=_envelope(payload), current=current)

    assert result.valid is True
    assert result.effect == "idempotent"


def test_rollback_is_rejected():
    current = _current(
        accepted_revision=4,
        canonical_payload_digest="a" * 64,
    )

    result = _preview(current=current)

    assert result.valid is False
    assert result.effect == "rejected"
    assert result.reason_code == "rollback_detected"


def test_same_revision_conflict_is_rejected():
    current = _current(
        canonical_payload_digest="b" * 64,
    )

    result = _preview(current=current)

    assert result.valid is False
    assert result.reason_code == "same_revision_conflict"


def test_wrong_organization_is_rejected():
    result = _preview(
        envelope=_envelope(_payload(organization_id=OTHER_ORG))
    )

    assert result.valid is False
    assert result.reason_code == "organization_mismatch"


def test_wrong_deployment_is_rejected():
    result = _preview(
        envelope=_envelope(_payload(deployment_id="other-deployment"))
    )

    assert result.valid is False
    assert result.reason_code == "deployment_mismatch"


def test_not_yet_valid_is_rejected():
    result = _preview(
        envelope=_envelope(_payload(not_before=NOW + timedelta(hours=1)))
    )

    assert result.valid is False
    assert result.reason_code == "not_yet_valid"


def test_expired_is_rejected():
    result = _preview(
        envelope=_envelope(
            _payload(
                issued_at=NOW - timedelta(days=4),
                not_before=NOW - timedelta(days=3),
                valid_until=NOW - timedelta(days=2),
                grace_until=NOW - timedelta(days=1),
            )
        )
    )

    assert result.valid is False
    assert result.reason_code == "expired"


def test_grace_is_valid_but_reported():
    result = _preview(
        envelope=_envelope(
            _payload(
                valid_until=NOW - timedelta(hours=1),
                grace_until=NOW + timedelta(days=1),
            )
        )
    )

    assert result.valid is True
    assert result.effect == "initial"
    assert result.reason_code == "grace"


def test_sticky_time_untrusted_is_reported_without_mutation():
    marker = NOW - timedelta(minutes=1)
    current = _current(time_untrusted_at=marker)

    result = _preview(
        envelope=_envelope(_payload(revision=2)),
        current=current,
    )

    assert result.valid is False
    assert result.effect == "rejected"
    assert result.reason_code == "time_untrusted"
    assert current.time_untrusted_at == marker
    assert current.last_trusted_time == NOW


def test_backward_clock_is_previewed_as_time_untrusted_without_mutation():
    trusted = NOW + timedelta(minutes=5, seconds=1)
    current = _current(last_trusted_time=trusted)

    result = _preview(
        envelope=_envelope(_payload(revision=2)),
        current=current,
    )

    assert result.valid is False
    assert result.effect == "rejected"
    assert result.reason_code == "time_untrusted"
    assert current.time_untrusted_at is None
    assert current.last_trusted_time == trusted


def test_tolerated_backward_skew_uses_monotonic_effective_time():
    current = _current(last_trusted_time=NOW + timedelta(minutes=5))
    payload = _payload(
        revision=2,
        valid_until=NOW + timedelta(minutes=4),
        grace_until=NOW + timedelta(days=1),
    )

    result = _preview(envelope=_envelope(payload), current=current)

    assert result.valid is True
    assert result.reason_code == "grace"


def test_verification_failure_maps_to_safe_reason(monkeypatch):
    def fail(*args, **kwargs):
        raise ValueError("invalid signature")

    monkeypatch.setattr(service, "verify_envelope", fail)

    result = _preview()

    assert result.valid is False
    assert result.effect == "rejected"
    assert result.reason_code == "invalid_signature"
