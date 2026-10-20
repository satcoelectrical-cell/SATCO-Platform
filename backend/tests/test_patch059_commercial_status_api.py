from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID
from unittest.mock import Mock, patch

from app.api.v1.routers.commercial_entitlements import (
    get_current_commercial_entitlement,
)


ORG_ID = UUID("00000000-0000-0000-0000-000000000001")
ENTITLEMENT_ID = UUID("00000000-0000-0000-0000-000000000059")


def _context():
    return SimpleNamespace(
        organization_id=ORG_ID,
        user=SimpleNamespace(id=1, role="engineer"),
    )


def _state(*, now, time_untrusted=False, not_before=None, valid_until=None, grace_until=None):
    return SimpleNamespace(
        entitlement_id=ENTITLEMENT_ID,
        accepted_revision=3,
        canonical_payload_digest="a" * 64,
        package_keys=["electrical", "instrumentation"],
        seat_capacity=25,
        not_before=not_before or now - timedelta(days=1),
        valid_until=valid_until or now + timedelta(days=10),
        grace_until=grace_until or now + timedelta(days=20),
        support_until=now + timedelta(days=30),
        baseline_release_sequence=1,
        max_release_sequence=10,
        time_untrusted_at=now if time_untrusted else None,
    )


def test_status_missing_entitlement_is_safe_and_bounded():
    db = Mock()

    with patch(
        "app.api.v1.routers.commercial_entitlements.settings.SATCO_DEPLOYMENT_ID",
        "deployment-a",
    ), patch(
        "app.api.v1.routers.commercial_entitlements.CommercialEntitlementRepository"
    ) as repository:
        repository.return_value.get_state.return_value = None

        result = get_current_commercial_entitlement(
            context=_context(),
            db=db,
        )

    assert result.available is False
    assert result.reason_code == "entitlement_missing"
    assert result.entitlement_id is None
    assert result.package_keys == []

    repository.return_value.get_state.assert_called_once_with(
        organization_id=ORG_ID,
        deployment_id="deployment-a",
        lock=False,
    )


def test_status_active_entitlement_returns_safe_metadata():
    now = datetime.now(timezone.utc)
    state = _state(now=now)
    db = Mock()

    with patch(
        "app.api.v1.routers.commercial_entitlements.settings.SATCO_DEPLOYMENT_ID",
        "deployment-a",
    ), patch(
        "app.api.v1.routers.commercial_entitlements.CommercialEntitlementRepository"
    ) as repository:
        repository.return_value.get_state.return_value = state

        result = get_current_commercial_entitlement(
            context=_context(),
            db=db,
        )

    assert result.available is True
    assert result.effective_state == "active"
    assert result.entitlement_id == ENTITLEMENT_ID
    assert result.revision == 3
    assert result.digest_prefix == "a" * 12
    assert result.package_keys == ["electrical", "instrumentation"]
    assert result.reason_code is None


def test_status_grace_is_visible_without_expansion_authority():
    now = datetime.now(timezone.utc)
    state = _state(
        now=now,
        valid_until=now - timedelta(minutes=1),
        grace_until=now + timedelta(days=2),
    )

    with patch(
        "app.api.v1.routers.commercial_entitlements.settings.SATCO_DEPLOYMENT_ID",
        "deployment-a",
    ), patch(
        "app.api.v1.routers.commercial_entitlements.CommercialEntitlementRepository"
    ) as repository:
        repository.return_value.get_state.return_value = state

        result = get_current_commercial_entitlement(
            context=_context(),
            db=Mock(),
        )

    assert result.available is True
    assert result.effective_state == "grace"
    assert result.reason_code == "grace"


def test_status_expired_is_not_available():
    now = datetime.now(timezone.utc)
    state = _state(
        now=now,
        valid_until=now - timedelta(days=2),
        grace_until=now - timedelta(days=1),
    )

    with patch(
        "app.api.v1.routers.commercial_entitlements.settings.SATCO_DEPLOYMENT_ID",
        "deployment-a",
    ), patch(
        "app.api.v1.routers.commercial_entitlements.CommercialEntitlementRepository"
    ) as repository:
        repository.return_value.get_state.return_value = state

        result = get_current_commercial_entitlement(
            context=_context(),
            db=Mock(),
        )

    assert result.available is True
    assert result.effective_state == "expired"
    assert result.reason_code == "expired"


def test_status_time_untrusted_fails_closed():
    now = datetime.now(timezone.utc)
    state = _state(now=now, time_untrusted=True)

    with patch(
        "app.api.v1.routers.commercial_entitlements.settings.SATCO_DEPLOYMENT_ID",
        "deployment-a",
    ), patch(
        "app.api.v1.routers.commercial_entitlements.CommercialEntitlementRepository"
    ) as repository:
        repository.return_value.get_state.return_value = state

        result = get_current_commercial_entitlement(
            context=_context(),
            db=Mock(),
        )

    assert result.available is False
    assert result.effective_state == "time_untrusted"
    assert result.reason_code == "time_untrusted"


def test_status_missing_runtime_deployment_fails_closed_without_db_lookup():
    with patch(
        "app.api.v1.routers.commercial_entitlements.settings.SATCO_DEPLOYMENT_ID",
        "",
    ), patch(
        "app.api.v1.routers.commercial_entitlements.CommercialEntitlementRepository"
    ) as repository:
        result = get_current_commercial_entitlement(
            context=_context(),
            db=Mock(),
        )

    assert result.available is False
    assert result.reason_code == "entitlement_missing"
    repository.assert_not_called()


def test_commercial_status_route_is_declared_and_registered():
    from app.main import app
    from app.api.v1.routers.commercial_entitlements import router

    matching = [
        route
        for route in router.routes
        if getattr(route, "path", None)
        == "/organizations/current/commercial-entitlement"
    ]

    assert len(matching) == 1
    assert matching[0].methods == {"GET"}
    assert matching[0].operation_id == "get_current_commercial_entitlement"

    assert any(
        getattr(route, "original_router", None) is router
        for route in app.routes
    )
