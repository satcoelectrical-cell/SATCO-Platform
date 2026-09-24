from datetime import datetime, timedelta, timezone
import base64
from uuid import UUID

import pyotp
import pytest

from app.core.config import settings
from app.models.auth_security import AuthRefreshFamily, AuthRefreshSession, AuthSecurityEvent, MfaRecoveryCode
from app.services.mfa_service import MfaRejected, MfaService
from app.services.refresh_session_service import RefreshRejected, RefreshSessionService
from tests.test_patch058_mfa_foundation import ORG_ID


@pytest.fixture
def mfa_keys(tmp_path, monkeypatch):
    active = tmp_path / "totp-active"
    recovery = tmp_path / "recovery-verifier"
    active.write_text(base64.urlsafe_b64encode(b"k" * 32).decode("ascii"), encoding="utf-8")
    recovery.write_text("r" * 40, encoding="utf-8")
    monkeypatch.setattr(settings, "TOTP_ENCRYPTION_KEY_FILE", str(active))
    monkeypatch.setattr(settings, "TOTP_ENCRYPTION_KEY_ID", "test-v1")
    monkeypatch.setattr(settings, "TOTP_ENCRYPTION_KEY_VERSION", 1)
    monkeypatch.setattr(settings, "TOTP_PREVIOUS_KEY_FILES", "")
    monkeypatch.setattr(settings, "RECOVERY_CODE_VERIFIER_KEY_FILE", str(recovery))
    return active


def test_recovery_code_is_single_use_and_audited(db_session, admin_user, mfa_keys):
    mfa = MfaService(db_session)
    enrollment = mfa.start_enrollment(admin_user, ORG_ID)
    completed = mfa.verify_enrollment(admin_user, ORG_ID, pyotp.TOTP(enrollment.secret).now())
    code = completed.recovery_codes[0]

    mfa.consume_recovery_code(admin_user, ORG_ID, code)
    with pytest.raises(MfaRejected):
        mfa.consume_recovery_code(admin_user, ORG_ID, code)
    db_session.rollback()

    assert db_session.query(MfaRecoveryCode).filter_by(user_id=admin_user.id, used_at=None).count() == 9
    event = db_session.query(AuthSecurityEvent).filter_by(user_id=admin_user.id, event_type="mfa_recovery_code_used").one()
    assert code not in f"{event.reason_code or ''}{event.safe_context or ''}"


def test_regeneration_invalidates_previous_unused_codes(db_session, admin_user, mfa_keys):
    mfa = MfaService(db_session)
    enrollment = mfa.start_enrollment(admin_user, ORG_ID)
    first = mfa.verify_enrollment(admin_user, ORG_ID, pyotp.TOTP(enrollment.secret).now()).recovery_codes
    second = mfa.regenerate_recovery_codes(admin_user, ORG_ID)

    assert len(second) == 10 and set(first).isdisjoint(second)
    with pytest.raises(MfaRejected):
        mfa.consume_recovery_code(admin_user, ORG_ID, first[0])
    db_session.rollback()
    mfa.consume_recovery_code(admin_user, ORG_ID, second[0])


def test_session_listing_and_current_revocation(db_session, engineer_user):
    service = RefreshSessionService(db_session)
    issued = service.create(engineer_user)
    active = service.list_active(engineer_user)
    assert [item.id for item in active] == [issued.session_id]

    service.revoke_current(engineer_user, issued.session_id)
    assert service.list_active(engineer_user) == []
    session = db_session.get(AuthRefreshSession, issued.session_id)
    assert session.revoked_at is not None
    assert session.revocation_reason == "current_session_logout"


def test_all_session_revocation_revokes_every_family(db_session, engineer_user):
    service = RefreshSessionService(db_session)
    first = service.create(engineer_user)
    second = service.create(engineer_user)
    assert len(service.list_active(engineer_user)) == 2

    assert service.revoke_all(engineer_user) == 2
    assert service.list_active(engineer_user) == []
    assert db_session.query(AuthRefreshFamily).filter_by(user_id=engineer_user.id, revoked_at=None).count() == 0
    assert {first.session_id, second.session_id}


def test_refresh_rotation_does_not_extend_recent_authentication(db_session, engineer_user, monkeypatch):
    service = RefreshSessionService(db_session)
    issued = service.create(engineer_user)
    session = db_session.get(AuthRefreshSession, issued.session_id)
    family = db_session.get(AuthRefreshFamily, session.family_id)
    family.created_at = datetime.now(timezone.utc) - timedelta(minutes=11)
    db_session.commit()

    _, rotated = service.rotate(issued.credential)
    successor = db_session.get(AuthRefreshSession, rotated.session_id)
    assert service.has_recent_authentication(successor) is False

    service.record_step_up(engineer_user, successor)
    assert service.has_recent_authentication(successor) is True


def test_admin_targeted_revocation_requires_distinct_admin_actor(db_session, admin_user, engineer_user):
    service = RefreshSessionService(db_session)
    issued = service.create(engineer_user)
    assert service.revoke_target(admin_user, engineer_user) == 1
    assert db_session.get(AuthRefreshSession, issued.session_id).revoked_at is not None
    event = db_session.query(AuthSecurityEvent).filter_by(event_type="admin_session_revocation", user_id=engineer_user.id).one()
    assert event.actor_user_id == admin_user.id

    with pytest.raises(RefreshRejected):
        service.revoke_target(admin_user, admin_user)


def test_step_up_endpoint_for_optional_mfa_member(client, engineer_user, engineer_headers, db_session):
    response = client.post(
        "/auth/step-up",
        headers=engineer_headers,
        json={"password": "correct-password"},
    )
    assert response.status_code == 200
    assert response.json() == {"outcome": "success"}
    event = db_session.query(AuthSecurityEvent).filter_by(user_id=engineer_user.id, event_type="step_up_success").one()
    assert event.outcome == "success"


def test_sessions_endpoint_exposes_only_safe_current_user_metadata(client, engineer_headers):
    response = client.get("/auth/sessions", headers=engineer_headers)
    assert response.status_code == 200
    payload = response.json()["sessions"]
    assert len(payload) == 1 and payload[0]["current"] is True
    serialized = str(payload).lower()
    assert "secret" not in serialized and "verifier" not in serialized and "selector" not in serialized


def test_current_logout_immediately_invalidates_access_session(client, engineer_headers):
    response = client.post("/auth/logout", headers=engineer_headers)
    assert response.status_code == 200
    assert client.get("/auth/me", headers=engineer_headers).status_code == 401


def test_admin_revocation_is_authorization_before_lookup_and_org_scoped(client, admin_headers, admin_user, engineer_user, db_session):
    service = RefreshSessionService(db_session)
    admin_session = service.list_active(admin_user)[0]
    service.record_step_up(admin_user, admin_session)

    allowed = client.post(f"/auth/admin/users/{engineer_user.id}/sessions/revoke", headers=admin_headers)
    assert allowed.status_code == 200

    missing = client.post("/auth/admin/users/999999999/sessions/revoke", headers=admin_headers)
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Protected resource not found"


def test_admin_revocation_hides_cross_organization_target(client, admin_headers, admin_user, engineer_user, db_session):
    from uuid import uuid4
    from app.models.organization import Organization, UserOrganizationMembership

    service = RefreshSessionService(db_session)
    service.record_step_up(admin_user, service.list_active(admin_user)[0])
    other_org = Organization(id=uuid4(), is_active=True)
    db_session.add(other_org)
    membership = db_session.query(UserOrganizationMembership).filter_by(user_id=engineer_user.id).one()
    membership.is_selected = False
    membership.is_enabled = False
    db_session.flush()
    db_session.add(UserOrganizationMembership(user_id=engineer_user.id, organization_id=other_org.id, is_enabled=True, is_selected=True))
    db_session.commit()

    response = client.post(f"/auth/admin/users/{engineer_user.id}/sessions/revoke", headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Protected resource not found"


def test_engineer_cannot_probe_admin_revocation_targets(client, engineer_headers, admin_user):
    response = client.post(f"/auth/admin/users/{admin_user.id}/sessions/revoke", headers=engineer_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Permission denied"


def test_session_listing_excludes_consumed_refresh_predecessor(db_session, engineer_user):
    service = RefreshSessionService(db_session)
    issued = service.create(engineer_user)
    _, successor = service.rotate(issued.credential)
    active = service.list_active(engineer_user)
    assert [item.id for item in active] == [successor.session_id]
