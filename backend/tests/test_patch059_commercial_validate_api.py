import asyncio
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import HTTPException

from app.api.v1.routers import commercial_entitlements as api
from app.services.commercial_entitlement_service import ValidationPreview


UTC = timezone.utc
ORG = UUID("05900000-0000-4000-8000-000000000001")


class FakeRequest:
    def __init__(self, raw: bytes):
        self._raw = raw

    async def body(self):
        return self._raw


def _admin():
    return SimpleNamespace(
        organization=SimpleNamespace(organization_id=ORG)
    )


def _raw():
    now = datetime(2026, 9, 30, 12, 0, tzinfo=UTC)

    payload = {
        "baseline_release_sequence": 1,
        "deployment_id": "satco-production",
        "entitlement_id": "05900000-0000-4000-8000-000000000101",
        "grace_until": (now + timedelta(days=20)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "issued_at": (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "issuer": "SATCO",
        "max_release_sequence": 10,
        "not_before": (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "organization_id": str(ORG),
        "package_keys": ["electrical"],
        "revision": 1,
        "schema_version": 1,
        "seat_capacity": 5,
        "support_until": None,
        "valid_until": (now + timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    return json.dumps(
        {
            "schema": "satco.commercial-entitlement/v1",
            "key_id": "key-1",
            "payload": payload,
            "signature": "abc",
        },
        separators=(",", ":"),
    ).encode()


def test_validate_uses_raw_canonical_parser_and_read_only_state(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        api.settings,
        "SATCO_DEPLOYMENT_ID",
        "satco-production",
    )
    monkeypatch.setattr(api, "runtime_trust_store", lambda: object())

    original_parse = api.parse_envelope

    def parse(raw):
        captured["raw"] = raw
        return original_parse(raw)

    monkeypatch.setattr(api, "parse_envelope", parse)

    class Repository:
        def __init__(self, db):
            captured["db"] = db

        def get_state(self, *, organization_id, deployment_id, lock):
            captured["organization_id"] = organization_id
            captured["deployment_id"] = deployment_id
            captured["lock"] = lock
            return None

    monkeypatch.setattr(api, "CommercialEntitlementRepository", Repository)

    def preview(**kwargs):
        captured["preview"] = kwargs
        return ValidationPreview(
            valid=True,
            effect="initial",
            entitlement_id=kwargs["envelope"].payload.entitlement_id,
            revision=1,
            canonical_payload_digest="a" * 64,
            reason_code=None,
        )

    monkeypatch.setattr(api, "preview_entitlement", preview)

    raw = _raw()
    response = asyncio.run(
        api.validate_current_commercial_entitlement(
            request=FakeRequest(raw),
            admin=_admin(),
            db=object(),
        )
    )

    assert captured["raw"] == raw
    assert captured["organization_id"] == ORG
    assert captured["deployment_id"] == "satco-production"
    assert captured["lock"] is False
    assert response.valid is True
    assert response.effect == "initial"
    assert response.digest_prefix == "a" * 12


def test_validate_rejects_duplicate_wire_member_before_preview(monkeypatch):
    monkeypatch.setattr(
        api.settings,
        "SATCO_DEPLOYMENT_ID",
        "satco-production",
    )

    raw = _raw()
    text = raw.decode()
    duplicate = text.replace(
        '"key_id":"key-1"',
        '"key_id":"key-1","key_id":"key-2"',
        1,
    ).encode()

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            api.validate_current_commercial_entitlement(
                request=FakeRequest(duplicate),
                admin=_admin(),
                db=object(),
            )
        )

    assert exc.value.status_code == 422
    assert exc.value.detail == "Invalid commercial entitlement envelope"


def test_validate_fail_closes_when_runtime_trust_is_unavailable(monkeypatch):
    monkeypatch.setattr(
        api.settings,
        "SATCO_DEPLOYMENT_ID",
        "satco-production",
    )

    def unavailable():
        raise api.ProductionConfigurationError("commercial_trust_store")

    monkeypatch.setattr(api, "runtime_trust_store", unavailable)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            api.validate_current_commercial_entitlement(
                request=FakeRequest(_raw()),
                admin=_admin(),
                db=object(),
            )
        )

    assert exc.value.status_code == 503
    assert exc.value.detail == "Commercial entitlement verification unavailable"


def test_validate_route_declared():
    matches = [
        route
        for route in api.router.routes
        if route.path == "/organizations/current/commercial-entitlement/validate"
    ]

    assert len(matches) == 1
    assert matches[0].methods == {"POST"}
    assert matches[0].operation_id == "validate_current_commercial_entitlement"
