import asyncio
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import HTTPException

from app.api.v1.routers import commercial_entitlements as api
from app.services.commercial_entitlement_service import (
    ActivationResult,
    CommercialEntitlementActivationError,
    RevisionDecision,
)


ORG = UUID("05900000-0000-4000-8000-000000000001")
ENTITLEMENT = UUID("05900000-0000-4000-8000-000000000101")


class FakeRequest:
    async def body(self):
        return b'{"raw":"envelope"}'


def _admin():
    return SimpleNamespace(
        organization=SimpleNamespace(
            organization_id=ORG,
            user=SimpleNamespace(id=59),
        )
    )


def _envelope():
    return SimpleNamespace(
        payload=SimpleNamespace(
            entitlement_id=ENTITLEMENT,
            revision=3,
            seat_capacity=5,
        )
    )


class FakeUow:
    instances = []

    def __init__(self, factory):
        self.factory = factory
        self.session = object()
        self.committed = False
        type(self).instances.append(self)

    def __enter__(self):
        return self

    def commit(self):
        self.committed = True

    def __exit__(self, exc_type, exc, tb):
        return None


@pytest.fixture(autouse=True)
def _reset():
    FakeUow.instances.clear()


def _wire(monkeypatch):
    monkeypatch.setattr(api, "parse_envelope", lambda raw: _envelope())
    monkeypatch.setattr(api, "runtime_trust_store", lambda: object())
    monkeypatch.setattr(
        api.settings,
        "SATCO_DEPLOYMENT_ID",
        "satco-production",
    )
    monkeypatch.setattr(api, "CommercialEntitlementUnitOfWork", FakeUow)
    monkeypatch.setattr(api, "SessionLocal", object())
    monkeypatch.setattr(api, "stage_audit_log", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        api,
        "require_repository",
        lambda uow: SimpleNamespace(consuming_seats=lambda **kwargs: 0),
    )
    monkeypatch.setattr(
        api,
        "_record_activation_rejection_audit",
        lambda **kwargs: None,
    )


def test_activate_commits_accepted_result(monkeypatch):
    _wire(monkeypatch)
    captured = {}

    def activate(**kwargs):
        captured.update(kwargs)
        return ActivationResult(
            decision=RevisionDecision.SUCCESSOR,
            entitlement_id=ENTITLEMENT,
            revision=3,
            canonical_payload_digest="a" * 64,
            temporal_state="active",
            state_advanced=True,
            accepted=True,
            reason_code=None,
        )

    monkeypatch.setattr(api, "activate_entitlement", activate)

    response = asyncio.run(
        api.activate_current_commercial_entitlement(
            request=FakeRequest(),
            admin=_admin(),
        )
    )

    assert len(FakeUow.instances) == 1
    assert FakeUow.instances[0].committed is True
    assert captured["expected_organization_id"] == ORG
    assert captured["expected_deployment_id"] == "satco-production"
    assert captured["actor_user_id"] == 59
    assert response.valid is True
    assert response.effect == "successor"
    assert response.digest_prefix == "a" * 12


@pytest.mark.parametrize(
    ("decision", "reason"),
    [
        (RevisionDecision.ROLLBACK_DETECTED, "rollback_detected"),
        (
            RevisionDecision.SAME_REVISION_CONFLICT,
            "same_revision_conflict",
        ),
    ],
)
def test_activate_commits_durable_rejection_evidence(
    monkeypatch,
    decision,
    reason,
):
    _wire(monkeypatch)

    monkeypatch.setattr(
        api,
        "activate_entitlement",
        lambda **kwargs: ActivationResult(
            decision=decision,
            entitlement_id=ENTITLEMENT,
            revision=3,
            canonical_payload_digest="b" * 64,
            temporal_state="invalid_or_unavailable",
            state_advanced=False,
            accepted=False,
            reason_code=reason,
        ),
    )

    response = asyncio.run(
        api.activate_current_commercial_entitlement(
            request=FakeRequest(),
            admin=_admin(),
        )
    )

    assert FakeUow.instances[0].committed is True
    assert response.valid is False
    assert response.effect == "rejected"
    assert response.reason_code == reason


def test_activate_commits_time_untrusted_marker(monkeypatch):
    _wire(monkeypatch)

    monkeypatch.setattr(
        api,
        "activate_entitlement",
        lambda **kwargs: ActivationResult(
            decision=RevisionDecision.IDEMPOTENT,
            entitlement_id=ENTITLEMENT,
            revision=3,
            canonical_payload_digest="c" * 64,
            temporal_state="time_untrusted",
            state_advanced=False,
            accepted=False,
            reason_code="time_untrusted",
        ),
    )

    response = asyncio.run(
        api.activate_current_commercial_entitlement(
            request=FakeRequest(),
            admin=_admin(),
        )
    )

    assert FakeUow.instances[0].committed is True
    assert response.reason_code == "time_untrusted"


def test_pre_transaction_activation_error_does_not_commit(monkeypatch):
    _wire(monkeypatch)

    def reject(**kwargs):
        raise CommercialEntitlementActivationError("invalid_signature")

    monkeypatch.setattr(api, "activate_entitlement", reject)

    response = asyncio.run(
        api.activate_current_commercial_entitlement(
            request=FakeRequest(),
            admin=_admin(),
        )
    )

    assert FakeUow.instances[0].committed is False
    assert response.valid is False
    assert response.effect == "rejected"
    assert response.reason_code == "invalid_signature"


def test_pre_transaction_rejection_is_audited_after_uow_rollback(monkeypatch):
    _wire(monkeypatch)
    captured = {}

    def reject(**kwargs):
        raise CommercialEntitlementActivationError("invalid_signature")

    monkeypatch.setattr(api, "activate_entitlement", reject)
    monkeypatch.setattr(
        api,
        "_record_activation_rejection_audit",
        lambda **kwargs: captured.update(kwargs),
    )

    response = asyncio.run(
        api.activate_current_commercial_entitlement(
            request=FakeRequest(),
            admin=_admin(),
        )
    )

    assert FakeUow.instances[0].committed is False
    assert captured["reason_code"] == "invalid_signature"
    assert captured["deployment_id"] == "satco-production"
    assert response.valid is False


def test_activation_audit_failure_prevents_commercial_commit(monkeypatch):
    _wire(monkeypatch)

    monkeypatch.setattr(
        api,
        "activate_entitlement",
        lambda **kwargs: ActivationResult(
            decision=RevisionDecision.SUCCESSOR,
            entitlement_id=ENTITLEMENT,
            revision=3,
            canonical_payload_digest="a" * 64,
            temporal_state="active",
            state_advanced=True,
            accepted=True,
            reason_code=None,
        ),
    )
    monkeypatch.setattr(
        api,
        "stage_audit_log",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("audit")),
    )

    with pytest.raises(RuntimeError, match="audit"):
        asyncio.run(
            api.activate_current_commercial_entitlement(
                request=FakeRequest(),
                admin=_admin(),
            )
        )

    assert FakeUow.instances[0].committed is False


def test_activate_rejects_malformed_wire_before_transaction(monkeypatch):
    monkeypatch.setattr(
        api,
        "parse_envelope",
        lambda raw: (_ for _ in ()).throw(ValueError("duplicate member")),
    )

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            api.activate_current_commercial_entitlement(
                request=FakeRequest(),
                admin=_admin(),
            )
        )

    assert exc.value.status_code == 422
    assert FakeUow.instances == []


def test_activate_route_declared():
    matches = [
        route
        for route in api.router.routes
        if route.path == "/organizations/current/commercial-entitlement/activate"
    ]

    assert len(matches) == 1
    assert matches[0].methods == {"POST"}
    assert matches[0].operation_id == "activate_current_commercial_entitlement"
