from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.routers.commercial_entitlements import (
    CommercialAdminContext,
    require_commercial_admin,
    require_sensitive_commercial_mutation,
)


def _organization_context(*, user_id=1, role="admin"):
    return SimpleNamespace(
        user=SimpleNamespace(id=user_id, role=role),
        organization_id="00000000-0000-0000-0000-000000000001",
    )


def _session_context(*, user_id=1):
    return SimpleNamespace(
        user=SimpleNamespace(id=user_id, role="admin"),
        session=SimpleNamespace(id="session-1", user_id=user_id),
    )


def test_commercial_admin_accepts_same_canonical_admin():
    context = _organization_context()
    auth = _session_context()

    result = require_commercial_admin(context=context, auth=auth)

    assert result.organization is context
    assert result.auth is auth


def test_commercial_admin_hides_non_admin_surface():
    with pytest.raises(HTTPException) as exc:
        require_commercial_admin(
            context=_organization_context(role="engineer"),
            auth=_session_context(),
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "Protected resource not found"


def test_commercial_admin_hides_session_identity_mismatch():
    with pytest.raises(HTTPException) as exc:
        require_commercial_admin(
            context=_organization_context(user_id=1),
            auth=_session_context(user_id=2),
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "Protected resource not found"


def test_sensitive_mutation_requires_csrf_before_step_up():
    request = Mock()
    admin = CommercialAdminContext(
        organization=_organization_context(),
        auth=_session_context(),
    )
    db = Mock()

    with patch(
        "app.api.v1.routers.commercial_entitlements."
        "BrowserAuthSecurityService.require_csrf",
        side_effect=HTTPException(status_code=403, detail="Invalid CSRF token"),
    ) as csrf, patch(
        "app.api.v1.routers.commercial_entitlements.RefreshSessionService"
    ) as refresh:
        with pytest.raises(HTTPException) as exc:
            require_sensitive_commercial_mutation(
                request=request,
                admin=admin,
                db=db,
            )

    assert exc.value.status_code == 403
    assert exc.value.detail == "Invalid CSRF token"
    csrf.assert_called_once_with(request)
    refresh.assert_not_called()


def test_sensitive_mutation_rejects_fresh_login_without_step_up():
    request = Mock()
    admin = CommercialAdminContext(
        organization=_organization_context(),
        auth=_session_context(),
    )
    db = Mock()

    with patch(
        "app.api.v1.routers.commercial_entitlements."
        "BrowserAuthSecurityService.require_csrf"
    ) as csrf, patch(
        "app.api.v1.routers.commercial_entitlements.RefreshSessionService"
    ) as refresh:
        refresh.return_value.has_recent_step_up.return_value = False

        with pytest.raises(HTTPException) as exc:
            require_sensitive_commercial_mutation(
                request=request,
                admin=admin,
                db=db,
            )

    assert exc.value.status_code == 403
    assert exc.value.detail == "Recent authentication required"
    csrf.assert_called_once_with(request)
    refresh.return_value.has_recent_step_up.assert_called_once_with(
        admin.auth.session,
        minutes=10,
    )


def test_sensitive_mutation_accepts_recent_explicit_step_up():
    request = Mock()
    admin = CommercialAdminContext(
        organization=_organization_context(),
        auth=_session_context(),
    )
    db = Mock()

    with patch(
        "app.api.v1.routers.commercial_entitlements."
        "BrowserAuthSecurityService.require_csrf"
    ) as csrf, patch(
        "app.api.v1.routers.commercial_entitlements.RefreshSessionService"
    ) as refresh:
        refresh.return_value.has_recent_step_up.return_value = True

        result = require_sensitive_commercial_mutation(
            request=request,
            admin=admin,
            db=db,
        )

    assert result is admin
    csrf.assert_called_once_with(request)
    refresh.return_value.has_recent_step_up.assert_called_once_with(
        admin.auth.session,
        minutes=10,
    )
