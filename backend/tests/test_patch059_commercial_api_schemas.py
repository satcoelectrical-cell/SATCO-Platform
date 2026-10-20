from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.commercial_entitlement import (
    CommercialEntitlementEnvelopeRequest,
    CommercialEntitlementPayloadRequest,
    CommercialSeatRetainedRequest,
)


NOW = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)


def _payload(**overrides):
    values = {
        "schema_version": 1,
        "entitlement_id": uuid4(),
        "revision": 1,
        "organization_id": uuid4(),
        "deployment_id": "satco-production",
        "issuer": "SATCO",
        "issued_at": NOW,
        "not_before": NOW,
        "valid_until": NOW + timedelta(days=30),
        "grace_until": NOW + timedelta(days=40),
        "package_keys": ["electrical", "instrumentation"],
        "seat_capacity": 5,
        "support_until": None,
        "baseline_release_sequence": 1,
        "max_release_sequence": 10,
    }
    values.update(overrides)
    return values


def test_payload_accepts_closed_canonical_contract():
    model = CommercialEntitlementPayloadRequest(**_payload())
    assert model.package_keys == ["electrical", "instrumentation"]
    assert model.revision == 1


def test_payload_rejects_unknown_field():
    with pytest.raises(ValidationError):
        CommercialEntitlementPayloadRequest(
            **_payload(),
            unexpected="forbidden",
        )


@pytest.mark.parametrize(
    "package_keys",
    [
        ["core"],
        ["electrical", "electrical"],
        ["instrumentation", "electrical"],
    ],
)
def test_payload_rejects_invalid_package_sets(package_keys):
    with pytest.raises(ValidationError):
        CommercialEntitlementPayloadRequest(
            **_payload(package_keys=package_keys)
        )


def test_payload_rejects_naive_datetime():
    with pytest.raises(ValidationError):
        CommercialEntitlementPayloadRequest(
            **_payload(issued_at=NOW.replace(tzinfo=None))
        )


def test_payload_rejects_grace_over_30_days():
    with pytest.raises(ValidationError):
        CommercialEntitlementPayloadRequest(
            **_payload(
                grace_until=NOW + timedelta(days=61),
            )
        )


def test_payload_rejects_invalid_release_range():
    with pytest.raises(ValidationError):
        CommercialEntitlementPayloadRequest(
            **_payload(
                baseline_release_sequence=10,
                max_release_sequence=9,
            )
        )


def test_envelope_rejects_unknown_field():
    with pytest.raises(ValidationError):
        CommercialEntitlementEnvelopeRequest(
            schema="satco.commercial-entitlement/v1",
            key_id="key-1",
            payload=_payload(),
            signature="abc",
            private_key="must-not-exist",
        )


def test_retained_set_rejects_duplicate_users():
    with pytest.raises(ValidationError):
        CommercialSeatRetainedRequest(user_ids=[1, 1])


def test_retained_set_allows_empty_exact_set():
    model = CommercialSeatRetainedRequest(user_ids=[])
    assert model.user_ids == []


def test_retained_set_rejects_nonpositive_user():
    with pytest.raises(ValidationError):
        CommercialSeatRetainedRequest(user_ids=[0])
