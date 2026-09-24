import base64
from uuid import UUID

import pyotp
import pytest

from app.core.config import settings
from app.models.auth_security import (
    AuthSecurityEvent,
    AuthThrottleState,
    MfaRecoveryCode,
    OrganizationMfaPolicy,
    UserTotpAuthenticator,
)
from app.services.mfa_service import MfaRejected, MfaService


ORG_ID = UUID("02810000-0000-4000-8000-000000000001")


@pytest.fixture
def mfa_keys(tmp_path, monkeypatch):
    active = tmp_path / "totp-active"
    recovery = tmp_path / "recovery-verifier"
    throttle = tmp_path / "throttle-key"
    active.write_text(
        base64.urlsafe_b64encode(b"k" * 32).decode("ascii"),
        encoding="utf-8",
    )
    recovery.write_text("r" * 40, encoding="utf-8")
    throttle.write_text("h" * 40, encoding="utf-8")
    monkeypatch.setattr(settings, "TOTP_ENCRYPTION_KEY_FILE", str(active))
    monkeypatch.setattr(settings, "TOTP_ENCRYPTION_KEY_ID", "test-v1")
    monkeypatch.setattr(settings, "TOTP_ENCRYPTION_KEY_VERSION", 1)
    monkeypatch.setattr(settings, "TOTP_PREVIOUS_KEY_FILES", "")
    monkeypatch.setattr(settings, "RECOVERY_CODE_VERIFIER_KEY_FILE", str(recovery))
    monkeypatch.setattr(settings, "AUTH_THROTTLE_KEY_FILE", str(throttle))
    return active


def test_admin_policy_is_mandatory_and_member_defaults_optional(
    db_session, admin_user, engineer_user, mfa_keys
):
    service = MfaService(db_session)

    admin = service.status(admin_user, ORG_ID)
    member = service.status(engineer_user, ORG_ID)

    assert admin.required is True
    assert member.required is False
    assert admin.active is False
    assert member.active is False


def test_current_organization_policy_can_require_member_mfa(
    db_session, engineer_user, mfa_keys
):
    db_session.add(
        OrganizationMfaPolicy(
            organization_id=ORG_ID,
            member_policy="required",
            version=1,
            updated_by_user_id=engineer_user.id,
        )
    )
    db_session.commit()

    status = MfaService(db_session).status(engineer_user, ORG_ID)

    assert status.required is True


def test_enrollment_secret_is_encrypted_and_not_active_before_verification(
    db_session, admin_user, mfa_keys
):
    service = MfaService(db_session)

    enrollment = service.start_enrollment(admin_user, ORG_ID)
    authenticator = (
        db_session.query(UserTotpAuthenticator)
        .filter_by(user_id=admin_user.id)
        .one()
    )

    assert enrollment.secret not in authenticator.encrypted_secret
    assert authenticator.key_id == "test-v1"
    assert authenticator.verified_at is None
    assert service.status(admin_user, ORG_ID).active is False
    assert "otpauth://totp/" in enrollment.provisioning_uri


def test_valid_enrollment_activates_factor_and_returns_ten_one_time_codes(
    db_session, admin_user, mfa_keys
):
    service = MfaService(db_session)
    enrollment = service.start_enrollment(admin_user, ORG_ID)
    code = pyotp.TOTP(enrollment.secret).now()

    completed = service.verify_enrollment(admin_user, ORG_ID, code)

    assert len(completed.recovery_codes) == 10
    assert len(set(completed.recovery_codes)) == 10
    authenticator = (
        db_session.query(UserTotpAuthenticator)
        .filter_by(user_id=admin_user.id)
        .one()
    )
    assert authenticator.verified_at is not None
    assert authenticator.last_accepted_counter is not None
    records = (
        db_session.query(MfaRecoveryCode)
        .filter_by(user_id=admin_user.id, generation=1)
        .all()
    )
    assert len(records) == 10
    assert all(raw not in {record.code_verifier for record in records} for raw in completed.recovery_codes)
    assert all(len(record.code_verifier) == 64 for record in records)
    assert service.status(admin_user, ORG_ID).active is True


def test_enrollment_rejects_invalid_code_without_activation(
    db_session, admin_user, mfa_keys
):
    service = MfaService(db_session)
    service.start_enrollment(admin_user, ORG_ID)

    with pytest.raises(MfaRejected):
        service.verify_enrollment(admin_user, ORG_ID, "000000")
    db_session.rollback()

    authenticator = (
        db_session.query(UserTotpAuthenticator)
        .filter_by(user_id=admin_user.id)
        .one()
    )
    assert authenticator.verified_at is None


def test_same_totp_counter_cannot_be_accepted_twice(
    db_session, admin_user, mfa_keys
):
    service = MfaService(db_session)
    enrollment = service.start_enrollment(admin_user, ORG_ID)
    code = pyotp.TOTP(enrollment.secret).now()
    service.verify_enrollment(admin_user, ORG_ID, code)

    authenticator = (
        db_session.query(UserTotpAuthenticator)
        .filter_by(user_id=admin_user.id)
        .with_for_update()
        .one()
    )
    secret = service._decrypt_secret(authenticator)
    assert service._matching_counter(secret, code) == authenticator.last_accepted_counter
    assert not (
        service._matching_counter(secret, code) is not None
        and service._matching_counter(secret, code) > authenticator.last_accepted_counter
    )


def test_active_factor_cannot_be_silently_replaced(
    db_session, admin_user, mfa_keys
):
    service = MfaService(db_session)
    enrollment = service.start_enrollment(admin_user, ORG_ID)
    service.verify_enrollment(admin_user, ORG_ID, pyotp.TOTP(enrollment.secret).now())

    with pytest.raises(MfaRejected):
        service.start_enrollment(admin_user, ORG_ID)


def test_mfa_events_do_not_contain_raw_factor_or_recovery_secrets(
    db_session, admin_user, mfa_keys
):
    service = MfaService(db_session)
    enrollment = service.start_enrollment(admin_user, ORG_ID)
    completed = service.verify_enrollment(
        admin_user, ORG_ID, pyotp.TOTP(enrollment.secret).now()
    )

    events = (
        db_session.query(AuthSecurityEvent)
        .filter(AuthSecurityEvent.user_id == admin_user.id)
        .all()
    )
    serialized = " ".join(
        f"{event.event_type} {event.reason_code or ''} {event.safe_context or ''}"
        for event in events
    )
    assert enrollment.secret not in serialized
    assert all(code not in serialized for code in completed.recovery_codes)


def test_routes_expose_secret_only_during_bounded_enrollment(
    client, admin_user, admin_headers, db_session, mfa_keys
):
    status = client.get("/auth/mfa/status", headers=admin_headers)
    assert status.status_code == 200
    assert status.json() == {"required": True, "enrolled": False, "active": False}

    started = client.post("/auth/mfa/totp/enrollment", headers=admin_headers)
    assert started.status_code == 200
    secret = started.json()["secret"]

    verified = client.post(
        "/auth/mfa/totp/enrollment/verify",
        headers=admin_headers,
        json={"code": pyotp.TOTP(secret).now()},
    )
    assert verified.status_code == 200
    assert len(verified.json()["recovery_codes"]) == 10

    final_status = client.get("/auth/mfa/status", headers=admin_headers)
    assert final_status.json() == {"required": True, "enrolled": True, "active": True}


def test_previous_totp_key_can_verify_pending_enrollment_after_rotation(
    db_session, admin_user, mfa_keys, tmp_path, monkeypatch
):
    service = MfaService(db_session)
    enrollment = service.start_enrollment(admin_user, ORG_ID)
    old_key_file = str(mfa_keys)
    new_key = tmp_path / "totp-new"
    new_key.write_text(
        base64.urlsafe_b64encode(b"n" * 32).decode("ascii"), encoding="utf-8"
    )
    monkeypatch.setattr(settings, "TOTP_ENCRYPTION_KEY_FILE", str(new_key))
    monkeypatch.setattr(settings, "TOTP_ENCRYPTION_KEY_ID", "test-v2")
    monkeypatch.setattr(settings, "TOTP_ENCRYPTION_KEY_VERSION", 2)
    monkeypatch.setattr(
        settings, "TOTP_PREVIOUS_KEY_FILES", f"test-v1={old_key_file}"
    )

    completed = service.verify_enrollment(
        admin_user, ORG_ID, pyotp.TOTP(enrollment.secret).now()
    )

    assert len(completed.recovery_codes) == 10
    assert service.status(admin_user, ORG_ID).active is True


def test_missing_required_totp_key_fails_closed(
    db_session, admin_user, mfa_keys, monkeypatch
):
    service = MfaService(db_session)
    enrollment = service.start_enrollment(admin_user, ORG_ID)
    monkeypatch.setattr(settings, "TOTP_ENCRYPTION_KEY_FILE", "/missing/totp-key")

    with pytest.raises(MfaRejected):
        service.verify_enrollment(
            admin_user, ORG_ID, pyotp.TOTP(enrollment.secret).now()
        )
    db_session.rollback()

    authenticator = (
        db_session.query(UserTotpAuthenticator)
        .filter_by(user_id=admin_user.id)
        .one()
    )
    assert authenticator.verified_at is None


def test_mfa_verification_throttles_after_five_failures_without_plain_identity(
    client, admin_user, admin_headers, db_session, mfa_keys
):
    started = client.post("/auth/mfa/totp/enrollment", headers=admin_headers)
    assert started.status_code == 200

    for _ in range(5):
        failed = client.post(
            "/auth/mfa/totp/enrollment/verify",
            headers=admin_headers,
            json={"code": "000000"},
        )
        assert failed.status_code == 400

    blocked = client.post(
        "/auth/mfa/totp/enrollment/verify",
        headers=admin_headers,
        json={"code": "000000"},
    )
    assert blocked.status_code == 429
    state = db_session.query(AuthThrottleState).one()
    assert state.failure_count == 5
    assert state.credential_key != str(admin_user.id)
    assert len(state.credential_key) == 64
    assert all(ch in "0123456789abcdef" for ch in state.credential_key)
    assert len(state.credential_key) == 64
    assert len(state.network_key) == 64
    threshold_events = db_session.query(AuthSecurityEvent).filter_by(
        user_id=admin_user.id,
        event_type="auth_throttle_threshold",
    ).all()
    assert len(threshold_events) == 1
    assert threshold_events[0].reason_code == "mfa_verification_threshold"


def test_successful_mfa_verification_clears_failure_state(
    client, admin_user, admin_headers, db_session, mfa_keys
):
    started = client.post("/auth/mfa/totp/enrollment", headers=admin_headers)
    secret = started.json()["secret"]
    failed = client.post(
        "/auth/mfa/totp/enrollment/verify",
        headers=admin_headers,
        json={"code": "000000"},
    )
    assert failed.status_code == 400
    assert db_session.query(AuthThrottleState).count() == 1

    verified = client.post(
        "/auth/mfa/totp/enrollment/verify",
        headers=admin_headers,
        json={"code": pyotp.TOTP(secret).now()},
    )
    assert verified.status_code == 200
    assert db_session.query(AuthThrottleState).count() == 0
