from datetime import datetime, timedelta, timezone
import pytest
import pyotp
from app.core.security import verify_password
from app.models.auth_security import AuthRecoveryCredential, AuthRefreshSession, MfaRecoveryCode, UserTotpAuthenticator
from app.services.mfa_service import MfaService
from app.services.recovery_service import RecoveryRejected, RecoveryService
from app.services.refresh_session_service import RefreshSessionService
from tests.test_patch058_mfa_foundation import ORG_ID, mfa_keys

@pytest.fixture
def recovery_key(mfa_keys):
    return mfa_keys

def test_account_recovery_single_use_and_invalidates_sessions(db_session, admin_user, engineer_user, recovery_key):
    sessions = RefreshSessionService(db_session)
    active = sessions.create(engineer_user)
    issued = RecoveryService(db_session).issue(actor=admin_user, target=engineer_user, organization_id=ORG_ID, purpose="account_recovery")
    before = engineer_user.auth_version
    RecoveryService(db_session).recover_account(issued.credential, "new-secure-password")
    db_session.refresh(engineer_user)
    assert engineer_user.auth_version == before + 1
    assert verify_password("new-secure-password", engineer_user.hashed_password)
    assert db_session.get(AuthRefreshSession, active.session_id).revoked_at is not None
    with pytest.raises(RecoveryRejected):
        RecoveryService(db_session).recover_account(issued.credential, "another-secure-password")

def test_new_issue_revokes_prior_live_credential(db_session, admin_user, engineer_user, recovery_key):
    service = RecoveryService(db_session)
    first = service.issue(actor=admin_user, target=engineer_user, organization_id=ORG_ID, purpose="account_recovery")
    second = service.issue(actor=admin_user, target=engineer_user, organization_id=ORG_ID, purpose="account_recovery")
    with pytest.raises(RecoveryRejected):
        service.recover_account(first.credential, "first-new-password")
    db_session.rollback()
    service.recover_account(second.credential, "second-new-password")

def test_expired_recovery_fails_closed(db_session, admin_user, engineer_user, recovery_key):
    service = RecoveryService(db_session)
    issued = service.issue(actor=admin_user, target=engineer_user, organization_id=ORG_ID, purpose="account_recovery")
    row = db_session.query(AuthRecoveryCredential).filter_by(user_id=engineer_user.id, purpose="account_recovery").one()
    row.created_at = datetime.now(timezone.utc) - timedelta(minutes=30)
    row.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()
    with pytest.raises(RecoveryRejected):
        service.recover_account(issued.credential, "new-secure-password")

def test_mfa_recovery_disables_factor_codes_and_sessions(db_session, admin_user, engineer_user, mfa_keys, recovery_key):
    mfa = MfaService(db_session)
    enrollment = mfa.start_enrollment(engineer_user, ORG_ID)
    mfa.verify_enrollment(engineer_user, ORG_ID, pyotp.TOTP(enrollment.secret).now())
    sessions = RefreshSessionService(db_session)
    active = sessions.create(engineer_user)
    before = engineer_user.auth_version
    issued = RecoveryService(db_session).issue(actor=admin_user, target=engineer_user, organization_id=ORG_ID, purpose="mfa_recovery")
    RecoveryService(db_session).recover_mfa(issued.credential)
    db_session.refresh(engineer_user)
    assert db_session.query(UserTotpAuthenticator).filter_by(user_id=engineer_user.id).one().disabled_at is not None
    assert db_session.query(MfaRecoveryCode).filter_by(user_id=engineer_user.id, used_at=None).count() == 0
    assert engineer_user.auth_version == before + 1
    assert db_session.get(AuthRefreshSession, active.session_id).revoked_at is not None

def test_recovery_issue_hides_cross_org_and_missing_target(client, admin_headers, admin_user, engineer_user, db_session, recovery_key):
    from uuid import uuid4
    from app.models.organization import Organization, UserOrganizationMembership
    sessions = RefreshSessionService(db_session)
    sessions.record_step_up(admin_user, sessions.list_active(admin_user)[0])
    missing = client.post("/auth/admin/users/999999999/recovery", headers=admin_headers, json={"purpose":"account_recovery"})
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Protected resource not found"
    other = Organization(id=uuid4(), is_active=True)
    db_session.add(other)
    membership = db_session.query(UserOrganizationMembership).filter_by(user_id=engineer_user.id).one()
    membership.is_selected = False
    membership.is_enabled = False
    db_session.flush()
    db_session.add(UserOrganizationMembership(user_id=engineer_user.id, organization_id=other.id, is_enabled=True, is_selected=True))
    db_session.commit()
    cross = client.post(f"/auth/admin/users/{engineer_user.id}/recovery", headers=admin_headers, json={"purpose":"account_recovery"})
    assert cross.status_code == 404
    assert cross.json()["detail"] == missing.json()["detail"]


def test_engineer_cannot_issue_recovery_or_probe_target(client, engineer_headers, admin_user, recovery_key):
    response = client.post(f"/auth/admin/users/{admin_user.id}/recovery", headers=engineer_headers, json={"purpose":"account_recovery"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Permission denied"


def test_account_recovery_endpoint_consumes_once_with_same_external_failure(client, admin_headers, admin_user, engineer_user, db_session, recovery_key):
    sessions = RefreshSessionService(db_session)
    sessions.record_step_up(admin_user, sessions.list_active(admin_user)[0])
    issued = client.post(f"/auth/admin/users/{engineer_user.id}/recovery", headers=admin_headers, json={"purpose":"account_recovery"})
    assert issued.status_code == 200
    credential = issued.json()["recovery_credential"]
    ok = client.post("/auth/recovery/account/complete", json={"recovery_credential":credential,"new_password":"new-secure-password"})
    assert ok.status_code == 200
    reused = client.post("/auth/recovery/account/complete", json={"recovery_credential":credential,"new_password":"another-secure-password"})
    invalid = client.post("/auth/recovery/account/complete", json={"recovery_credential":"x"*24+"."+"y"*43,"new_password":"another-secure-password"})
    assert reused.status_code == invalid.status_code == 400
    assert reused.json()["detail"] == invalid.json()["detail"] == "Invalid or expired recovery credential"

def test_recovery_verification_throttles_without_plain_selector(client, db_session, recovery_key):
    from app.models.auth_security import AuthThrottleState
    selector = "selector-not-stored-plain"
    bad = selector + "." + "z" * 43
    for _ in range(5):
        response = client.post("/auth/recovery/account/complete", json={"recovery_credential":bad,"new_password":"new-secure-password"})
        assert response.status_code == 400
    blocked = client.post("/auth/recovery/account/complete", json={"recovery_credential":bad,"new_password":"new-secure-password"})
    assert blocked.status_code == 429
    state = db_session.query(AuthThrottleState).one()
    assert state.credential_key != selector
    assert selector not in state.credential_key
    assert len(state.credential_key) == 64
