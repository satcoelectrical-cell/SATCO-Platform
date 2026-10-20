"""PATCH-058 Checkpoint C2 bootstrap security qualification."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import base64
import pyotp

from app.core.config import settings
from app.models.auth_security import AuthSecurityEvent, AuthThrottleState
from app.models.organization import UserOrganizationMembership
from app.services.mfa_service import MfaService
from app.services.refresh_session_service import RefreshSessionService


def _payload(suffix: str):
    return {
        "organization_name": f"Bootstrap {suffix}",
        "organization_slug": f"bootstrap-{suffix}",
        "admin_username": f"bootstrap-{suffix}",
        "admin_email": f"bootstrap-{suffix}@example.com",
    }


def _configure(monkeypatch, tmp_path, *, enabled=True, end=None):
    throttle = tmp_path / "bootstrap-throttle-key"
    throttle.write_text("h" * 40, encoding="utf-8")
    monkeypatch.setattr(settings, "AUTH_THROTTLE_KEY_FILE", str(throttle))
    monkeypatch.setattr(settings, "PLATFORM_BOOTSTRAP_KEY", "b" * 40)
    monkeypatch.setattr(settings, "SATCO_BOOTSTRAP_ENABLED", enabled)
    monkeypatch.setattr(
        settings,
        "SATCO_BOOTSTRAP_WINDOW_END",
        end or (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
    )


def _post(client, payload, secret="b" * 40):
    return client.post(
        "/platform/bootstrap/organizations",
        json=payload,
        headers={"X-SATCO-Bootstrap-Key": secret, "Idempotency-Key": str(uuid4())},
    )


def _qualify_admin_reenable(db_session, admin_user, monkeypatch, tmp_path):
    totp_key = tmp_path / "bootstrap-totp-key"
    recovery_key = tmp_path / "bootstrap-recovery-key"
    totp_key.write_text(base64.urlsafe_b64encode(b"k" * 32).decode("ascii"), encoding="utf-8")
    recovery_key.write_text("r" * 40, encoding="utf-8")
    monkeypatch.setattr(settings, "TOTP_ENCRYPTION_KEY_FILE", str(totp_key))
    monkeypatch.setattr(settings, "TOTP_ENCRYPTION_KEY_ID", "bootstrap-test-v1")
    monkeypatch.setattr(settings, "TOTP_ENCRYPTION_KEY_VERSION", 1)
    monkeypatch.setattr(settings, "TOTP_PREVIOUS_KEY_FILES", "")
    monkeypatch.setattr(settings, "RECOVERY_CODE_VERIFIER_KEY_FILE", str(recovery_key))
    organization_id = db_session.query(UserOrganizationMembership.organization_id).filter_by(
        user_id=admin_user.id, is_enabled=True, is_selected=True
    ).scalar()
    service = MfaService(db_session)
    enrollment = service.start_enrollment(admin_user, organization_id)
    service.verify_enrollment(admin_user, organization_id, pyotp.TOTP(enrollment.secret).now())
    refresh = RefreshSessionService(db_session)
    refresh.record_step_up(admin_user, refresh.list_active(admin_user)[0])


def test_bootstrap_disabled_fails_closed(client, monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path, enabled=False)
    response = _post(client, _payload("disabled"))
    assert response.status_code == 200
    assert response.json() == {"outcome": "protected_not_found"}


def test_bootstrap_expired_window_fails_closed(client, monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path, end=(datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat())
    response = _post(client, _payload("expired"))
    assert response.status_code == 200
    assert response.json() == {"outcome": "protected_not_found"}


def test_bootstrap_malformed_window_is_unavailable(client, monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path, end="not-a-time")
    response = _post(client, _payload("malformed"))
    assert response.status_code == 503
    assert response.json()["detail"] == "Bootstrap unavailable"


def test_bootstrap_completion_prevents_second_bootstrap(client, monkeypatch, db_session, tmp_path):
    _configure(monkeypatch, tmp_path)
    first = _post(client, _payload("first"))
    assert first.status_code == 200 and first.json()["outcome"] == "success"

    second = _post(client, _payload("second"))
    assert second.status_code == 200
    assert second.json() == {"outcome": "protected_not_found"}
    assert db_session.query(AuthSecurityEvent).filter_by(
        event_type="bootstrap_qualification", reason_code="completed"
    ).count() >= 1


def test_bootstrap_bad_secret_is_throttled_without_plaintext_secret(client, monkeypatch, db_session, tmp_path):
    _configure(monkeypatch, tmp_path)
    for _ in range(settings.AUTH_THROTTLE_FAILURE_THRESHOLD):
        response = _post(client, _payload("bad"), secret="wrong-secret-value")
        assert response.status_code == 200
        assert response.json() == {"outcome": "protected_not_found"}

    state = db_session.query(AuthThrottleState).one()
    assert "wrong-secret-value" not in state.credential_key
    assert len(state.credential_key) == 64
    assert db_session.query(AuthSecurityEvent).filter_by(
        event_type="bootstrap_qualification", reason_code="throttle_threshold"
    ).count() >= 1

    blocked = _post(client, _payload("blocked"), secret="b" * 40)
    assert blocked.status_code == 200
    assert blocked.json() == {"outcome": "protected_not_found"}


def test_configuration_alone_cannot_reopen_but_recent_admin_can_reenable(
    client, monkeypatch, db_session, tmp_path, admin_headers, admin_user
):
    _configure(monkeypatch, tmp_path)
    first = _post(client, _payload("reenable-first"))
    assert first.status_code == 200 and first.json()["outcome"] == "success"

    closed = _post(client, _payload("reenable-closed"))
    assert closed.status_code == 200
    assert closed.json() == {"outcome": "protected_not_found"}

    _qualify_admin_reenable(db_session, admin_user, monkeypatch, tmp_path)
    reopened = client.post(
        "/organization-admin/bootstrap/re-enable",
        headers={**admin_headers, "X-SATCO-Bootstrap-Key": "b" * 40},
    )
    assert reopened.status_code == 200
    assert reopened.json() == {"outcome": "success"}

    event = db_session.query(AuthSecurityEvent).filter_by(
        event_type="bootstrap_reenabled", outcome="success"
    ).one()
    assert event.actor_user_id is not None
    assert event.organization_id is not None
    assert event.session_id is not None
    assert event.reason_code == "human_admin_reenable"

    second = _post(client, _payload("reenable-second"))
    assert second.status_code == 200
    assert second.json()["outcome"] == "success"



def test_fresh_password_only_admin_session_cannot_reenable_bootstrap(
    client, monkeypatch, tmp_path, admin_headers
):
    _configure(monkeypatch, tmp_path)
    first = _post(client, _payload("password-only"))
    assert first.status_code == 200 and first.json()["outcome"] == "success"
    denied = client.post(
        "/organization-admin/bootstrap/re-enable",
        headers={**admin_headers, "X-SATCO-Bootstrap-Key": "b" * 40},
    )
    assert denied.status_code == 403
    assert denied.json()["detail"] == "MFA assurance required"


def test_organization_admin_alone_cannot_reenable_platform_bootstrap(
    client, monkeypatch, tmp_path, admin_headers
):
    _configure(monkeypatch, tmp_path)
    first = _post(client, _payload("admin-alone"))
    assert first.status_code == 200 and first.json()["outcome"] == "success"

    denied = client.post(
        "/organization-admin/bootstrap/re-enable",
        headers={**admin_headers, "X-SATCO-Bootstrap-Key": "wrong-secret-value"},
    )
    assert denied.status_code == 403
    assert denied.json()["detail"] == "MFA assurance required"

    still_closed = _post(client, _payload("admin-alone-still-closed"))
    assert still_closed.status_code == 200
    assert still_closed.json() == {"outcome": "protected_not_found"}

def test_legacy_platform_reset_cannot_use_bootstrap_secret_after_completion(
    client, monkeypatch, tmp_path
):
    _configure(monkeypatch, tmp_path)
    first = _post(client, _payload("reset-closure"))
    assert first.status_code == 200 and first.json()["outcome"] == "success"

    response = client.post(
        "/platform/bootstrap/resets",
        json={
            "organization_slug": "bootstrap-reset-closure",
            "username": "bootstrap-reset-closure",
        },
        headers={
            "X-SATCO-Bootstrap-Key": "b" * 40,
            "Idempotency-Key": str(uuid4()),
        },
    )
    assert response.status_code == 200
    assert response.json() == {"outcome": "protected_not_found"}
