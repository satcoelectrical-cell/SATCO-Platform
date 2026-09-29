"""PATCH-058 Checkpoint C3 mandatory-MFA login boundary qualification."""

import base64
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import jwt
import pyotp
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import create_access_token
from app.main import app
from app.models.auth_security import (
    AuthRefreshSession,
    AuthSecurityEvent,
    AuthThrottleState,
    OrganizationMfaPolicy,
    UserTotpAuthenticator,
)
from app.models.organization import Organization, UserOrganizationMembership
from app.services.mfa_login_challenge_service import MfaLoginChallengeService
from app.services.mfa_service import MfaService
from app.services.refresh_session_service import RefreshSessionService
from tests.test_patch058_mfa_foundation import ORG_ID


@pytest.fixture
def mfa_login_keys(tmp_path, monkeypatch):
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


def _login(client, user):
    return client.post(
        "/auth/login",
        data={"username": user.username, "password": "correct-password"},
    )


def _activate_totp(db_session, user) -> str:
    service = MfaService(db_session)
    enrollment = service.start_enrollment(user, ORG_ID)
    service.verify_enrollment(user, ORG_ID, pyotp.TOTP(enrollment.secret).now())
    authenticator = (
        db_session.query(UserTotpAuthenticator)
        .filter_by(user_id=user.id)
        .one()
    )
    # Enrollment consumes the current counter. Reset only this test fixture so
    # the login path can qualify the same deterministic clock window.
    authenticator.last_accepted_counter = None
    db_session.commit()
    return enrollment.secret


def _session_count(db_session, user) -> int:
    return (
        db_session.query(AuthRefreshSession)
        .filter_by(user_id=user.id)
        .count()
    )


def _invalid_totp(secret: str) -> str:
    for value in range(1_000_000):
        candidate = f"{value:06d}"
        if MfaService._matching_counter(secret, candidate) is None:
            return candidate
    raise AssertionError("Unable to construct an invalid TOTP")


def test_mandatory_mfa_password_login_issues_only_bounded_challenge(
    client, admin_user, db_session, mfa_login_keys
):
    response = _login(client, admin_user)

    assert response.status_code == 200
    assert response.json()["outcome"] == "mfa_required"
    assert response.json()["enrollment_required"] is True
    assert response.json()["challenge"]
    assert "access_token" not in response.json()
    assert "refresh_token" not in response.json()
    assert client.cookies.get("satco_refresh") is None
    assert _session_count(db_session, admin_user) == 0


def test_active_totp_creates_authority_only_after_verification(
    client, admin_user, db_session, mfa_login_keys
):
    secret = _activate_totp(db_session, admin_user)
    login = _login(client, admin_user)
    challenge = login.json()["challenge"]

    assert login.json()["enrollment_required"] is False
    assert _session_count(db_session, admin_user) == 0

    verified = client.post(
        "/auth/login/mfa/verify",
        json={"challenge": challenge, "code": pyotp.TOTP(secret).now()},
    )

    assert verified.status_code == 200
    assert verified.json()["access_token"]
    assert client.cookies.get("satco_refresh")
    assert _session_count(db_session, admin_user) == 1
    assert client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {verified.json()['access_token']}"},
    ).status_code == 200
    refreshed = client.post(
        "/auth/refresh",
        headers={"X-CSRF-Token": client.cookies.get("satco_csrf")},
    )
    assert refreshed.status_code == 200
    assert client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {refreshed.json()['access_token']}"},
    ).status_code == 200
    event = (
        db_session.query(AuthSecurityEvent)
        .filter_by(
            user_id=admin_user.id,
            event_type="mfa_login_challenge_consumed",
        )
        .one()
    )
    assert event.session_id is not None
    assert challenge not in (event.safe_context or "")


def test_primary_failures_survive_mfa_challenge_and_clear_only_on_mfa_success(
    client, admin_user, db_session, mfa_login_keys
):
    secret = _activate_totp(db_session, admin_user)
    for _ in range(2):
        rejected = client.post(
            "/auth/login",
            data={"username": admin_user.username, "password": "wrong-password"},
        )
        assert rejected.status_code == 401

    login = _login(client, admin_user)
    assert login.status_code == 200
    primary_state = db_session.query(AuthThrottleState).one()
    assert primary_state.failure_count == 2

    challenge = login.json()["challenge"]
    claims = jwt.get_unverified_claims(challenge)
    assert len(claims["pck"]) == 64
    assert len(claims["pnk"]) == 64
    assert admin_user.username not in str(claims)
    assert "testclient" not in str(claims)

    verified = client.post(
        "/auth/login/mfa/verify",
        json={"challenge": challenge, "code": pyotp.TOTP(secret).now()},
    )

    assert verified.status_code == 200
    assert db_session.query(AuthThrottleState).count() == 0


def test_primary_scope_clears_after_mfa_from_a_changed_direct_peer(
    client, admin_user, db_session, mfa_login_keys
):
    secret = _activate_totp(db_session, admin_user)
    assert client.post(
        "/auth/login",
        data={"username": admin_user.username, "password": "wrong-password"},
    ).status_code == 401
    challenge = _login(client, admin_user).json()["challenge"]
    assert db_session.query(AuthThrottleState).count() == 1

    with TestClient(app, client=("198.51.100.25", 50000)) as changed_peer:
        verified = changed_peer.post(
            "/auth/login/mfa/verify",
            json={"challenge": challenge, "code": pyotp.TOTP(secret).now()},
        )

    assert verified.status_code == 200
    assert db_session.query(AuthThrottleState).count() == 0


def test_primary_and_mfa_login_failures_use_distinct_counters(
    client, admin_user, db_session, mfa_login_keys
):
    secret = _activate_totp(db_session, admin_user)
    for _ in range(2):
        assert client.post(
            "/auth/login",
            data={"username": admin_user.username, "password": "wrong-password"},
        ).status_code == 401
    challenge = _login(client, admin_user).json()["challenge"]
    rejected = client.post(
        "/auth/login/mfa/verify",
        json={"challenge": challenge, "code": _invalid_totp(secret)},
    )

    assert rejected.status_code == 401
    states = db_session.query(AuthThrottleState).all()
    assert sorted(state.failure_count for state in states) == [1, 2]
    assert len({state.credential_key for state in states}) == 2


def test_mfa_challenge_rejects_malformed_signed_primary_scope(
    client, admin_user, db_session, mfa_login_keys
):
    secret = _activate_totp(db_session, admin_user)
    challenge = _login(client, admin_user).json()["challenge"]
    claims = jwt.get_unverified_claims(challenge)
    claims["pck"] = admin_user.username
    malformed = jwt.encode(
        claims,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    response = client.post(
        "/auth/login/mfa/verify",
        json={"challenge": malformed, "code": pyotp.TOTP(secret).now()},
    )

    assert response.status_code == 401
    assert _session_count(db_session, admin_user) == 0


@pytest.mark.parametrize("candidate", ["invalid-challenge", "wrong-purpose"])
def test_invalid_or_wrong_purpose_challenge_fails_closed(
    candidate, client, admin_user, db_session, mfa_login_keys
):
    _activate_totp(db_session, admin_user)
    challenge = (
        "x" * 40
        if candidate == "invalid-challenge"
        else create_access_token(admin_user.id, admin_user.auth_version)
    )

    response = client.post(
        "/auth/login/mfa/verify",
        json={"challenge": challenge, "code": "123456"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication credentials"
    assert _session_count(db_session, admin_user) == 0


def test_expired_challenge_fails_closed(
    client, admin_user, db_session, mfa_login_keys
):
    _activate_totp(db_session, admin_user)
    now = datetime.now(timezone.utc)
    expired = jwt.encode(
        {
            "sub": str(admin_user.id),
            "org": str(ORG_ID),
            "type": MfaLoginChallengeService.PURPOSE,
            "stage": "verify",
            "av": admin_user.auth_version,
            "iat": now - timedelta(minutes=10),
            "exp": now - timedelta(minutes=5),
            "jti": str(uuid4()),
            "iss": settings.ACCESS_TOKEN_ISSUER,
            "aud": settings.ACCESS_TOKEN_AUDIENCE,
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    response = client.post(
        "/auth/login/mfa/verify",
        json={"challenge": expired, "code": "123456"},
    )

    assert response.status_code == 401
    assert _session_count(db_session, admin_user) == 0


@pytest.mark.parametrize("change", ["auth_version", "inactive", "activation_pending"])
def test_principal_security_change_invalidates_challenge(
    change, client, admin_user, db_session, mfa_login_keys
):
    secret = _activate_totp(db_session, admin_user)
    challenge = _login(client, admin_user).json()["challenge"]
    if change == "auth_version":
        admin_user.auth_version += 1
    elif change == "inactive":
        admin_user.is_active = False
    else:
        admin_user.activation_pending = True
    db_session.commit()

    response = client.post(
        "/auth/login/mfa/verify",
        json={"challenge": challenge, "code": pyotp.TOTP(secret).now()},
    )

    assert response.status_code == 401
    assert _session_count(db_session, admin_user) == 0


@pytest.mark.parametrize(
    "change",
    ["disabled", "unselected", "inactive_organization", "foreign"],
)
def test_noncanonical_membership_invalidates_challenge(
    change, client, admin_user, db_session, mfa_login_keys
):
    secret = _activate_totp(db_session, admin_user)
    challenge = _login(client, admin_user).json()["challenge"]
    membership = (
        db_session.query(UserOrganizationMembership)
        .filter_by(user_id=admin_user.id, organization_id=ORG_ID)
        .one()
    )
    if change == "disabled":
        membership.is_selected = False
        membership.is_enabled = False
    elif change == "unselected":
        membership.is_selected = False
    elif change == "inactive_organization":
        db_session.get(Organization, ORG_ID).is_active = False
    else:
        other = Organization(id=uuid4(), is_active=True)
        db_session.add(other)
        membership.is_selected = False
        membership.is_enabled = False
        db_session.flush()
        db_session.add(
            UserOrganizationMembership(
                user_id=admin_user.id,
                organization_id=other.id,
                is_enabled=True,
                is_selected=True,
            )
        )
    db_session.commit()

    response = client.post(
        "/auth/login/mfa/verify",
        json={"challenge": challenge, "code": pyotp.TOTP(secret).now()},
    )

    assert response.status_code == 401
    assert _session_count(db_session, admin_user) == 0


def test_invalid_and_replayed_totp_fail_closed(
    client, admin_user, db_session, mfa_login_keys
):
    secret = _activate_totp(db_session, admin_user)
    first_challenge = _login(client, admin_user).json()["challenge"]
    invalid = client.post(
        "/auth/login/mfa/verify",
        json={"challenge": first_challenge, "code": _invalid_totp(secret)},
    )
    assert invalid.status_code == 401
    assert _session_count(db_session, admin_user) == 0

    code = pyotp.TOTP(secret).now()
    accepted = client.post(
        "/auth/login/mfa/verify",
        json={"challenge": first_challenge, "code": code},
    )
    assert accepted.status_code == 200
    assert db_session.query(AuthThrottleState).count() == 0

    next_challenge = _login(client, admin_user).json()["challenge"]
    replayed = client.post(
        "/auth/login/mfa/verify",
        json={"challenge": next_challenge, "code": code},
    )
    assert replayed.status_code == 401
    assert _session_count(db_session, admin_user) == 1


def test_mfa_login_verification_is_throttled_without_issuing_authority(
    client, admin_user, db_session, mfa_login_keys
):
    secret = _activate_totp(db_session, admin_user)
    challenge = _login(client, admin_user).json()["challenge"]
    invalid_code = _invalid_totp(secret)

    for _ in range(5):
        rejected = client.post(
            "/auth/login/mfa/verify",
            json={"challenge": challenge, "code": invalid_code},
        )
        assert rejected.status_code == 401

    blocked = client.post(
        "/auth/login/mfa/verify",
        json={"challenge": challenge, "code": invalid_code},
    )

    assert blocked.status_code == 429
    assert _session_count(db_session, admin_user) == 0
    throttle = db_session.query(AuthThrottleState).one()
    assert throttle.failure_count == 5
    assert throttle.credential_key != str(admin_user.id)


def test_consumed_challenge_cannot_create_a_second_session(
    client, admin_user, db_session, mfa_login_keys
):
    secret = _activate_totp(db_session, admin_user)
    challenge = _login(client, admin_user).json()["challenge"]
    code = pyotp.TOTP(secret).now()
    first = client.post(
        "/auth/login/mfa/verify",
        json={"challenge": challenge, "code": code},
    )
    assert first.status_code == 200

    replay = client.post(
        "/auth/login/mfa/verify",
        json={"challenge": challenge, "code": code},
    )
    assert replay.status_code == 401
    assert _session_count(db_session, admin_user) == 1


def test_first_time_mandatory_enrollment_cannot_bypass_mfa(
    client, admin_user, db_session, mfa_login_keys
):
    login = _login(client, admin_user)
    initial_challenge = login.json()["challenge"]

    wrong_stage = client.post(
        "/auth/login/mfa/verify",
        json={"challenge": initial_challenge, "code": "123456"},
    )
    assert wrong_stage.status_code == 401
    assert _session_count(db_session, admin_user) == 0

    started = client.post(
        "/auth/login/mfa/enrollment",
        json={"challenge": initial_challenge},
    )
    assert started.status_code == 200
    assert started.json()["secret"]
    assert started.json()["challenge"] != initial_challenge
    initial_claims = jwt.get_unverified_claims(initial_challenge)
    continuation_claims = jwt.get_unverified_claims(started.json()["challenge"])
    assert continuation_claims["pck"] == initial_claims["pck"]
    assert continuation_claims["pnk"] == initial_claims["pnk"]
    assert "access_token" not in started.json()
    assert client.cookies.get("satco_refresh") is None
    assert _session_count(db_session, admin_user) == 0

    replayed_start = client.post(
        "/auth/login/mfa/enrollment",
        json={"challenge": initial_challenge},
    )
    assert replayed_start.status_code == 401
    assert _session_count(db_session, admin_user) == 0

    rejected = client.post(
        "/auth/login/mfa/enrollment/verify",
        json={
            "challenge": started.json()["challenge"],
            "code": _invalid_totp(started.json()["secret"]),
        },
    )
    assert rejected.status_code == 401
    assert _session_count(db_session, admin_user) == 0

    completed = client.post(
        "/auth/login/mfa/enrollment/verify",
        json={
            "challenge": started.json()["challenge"],
            "code": pyotp.TOTP(started.json()["secret"]).now(),
        },
    )
    assert completed.status_code == 200
    assert completed.json()["access_token"]
    assert len(completed.json()["recovery_codes"]) == 10
    assert _session_count(db_session, admin_user) == 1


def test_current_organization_policy_requires_member_mfa_at_login(
    client, engineer_user, db_session, mfa_login_keys
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

    response = _login(client, engineer_user)

    assert response.status_code == 200
    assert response.json()["outcome"] == "mfa_required"
    assert "access_token" not in response.json()
    assert _session_count(db_session, engineer_user) == 0


def test_preexisting_admin_session_without_mfa_assurance_cannot_continue(
    client, admin_user, db_session, mfa_login_keys
):
    issued = RefreshSessionService(db_session).create(admin_user)
    token = create_access_token(
        admin_user.id,
        admin_user.auth_version,
        session_id=issued.session_id,
    )

    access = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    client.cookies.set("satco_refresh", issued.credential, path="/auth")
    client.cookies.set("satco_csrf", "csrf-test", path="/auth")
    refresh = client.post(
        "/auth/refresh",
        headers={"X-CSRF-Token": "csrf-test"},
    )

    assert access.status_code == 401
    assert refresh.status_code == 401


def test_admin_mfa_assurance_fails_closed_before_membership_resolution(
    client, admin_user, db_session, mfa_login_keys
):
    issued = RefreshSessionService(db_session).create(admin_user)
    token = create_access_token(
        admin_user.id,
        admin_user.auth_version,
        session_id=issued.session_id,
    )
    membership = (
        db_session.query(UserOrganizationMembership)
        .filter_by(user_id=admin_user.id, organization_id=ORG_ID)
        .one()
    )
    membership.is_selected = False
    db_session.commit()

    response = client.post(
        "/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "irrelevant", "new_password": "irrelevant"},
    )

    assert response.status_code == 401


def test_policy_tightening_invalidates_insufficient_member_session(
    client, engineer_user, db_session, mfa_login_keys
):
    login = _login(client, engineer_user)
    assert login.status_code == 200
    db_session.add(
        OrganizationMfaPolicy(
            organization_id=ORG_ID,
            member_policy="required",
            version=1,
            updated_by_user_id=engineer_user.id,
        )
    )
    db_session.commit()

    access = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    csrf = client.cookies.get("satco_csrf")
    refresh = client.post(
        "/auth/refresh",
        headers={"X-CSRF-Token": csrf},
    )

    assert access.status_code == 401
    assert refresh.status_code == 401


def test_password_only_step_up_cannot_prequalify_later_mfa_policy(
    client,
    engineer_user,
    engineer_headers,
    db_session,
    mfa_login_keys,
):
    step_up = client.post(
        "/auth/step-up",
        headers=engineer_headers,
        json={"password": "correct-password"},
    )
    assert step_up.status_code == 200
    assert (
        db_session.query(AuthSecurityEvent)
        .filter_by(user_id=engineer_user.id, event_type="step_up_success")
        .count()
        == 1
    )

    db_session.add(
        OrganizationMfaPolicy(
            organization_id=ORG_ID,
            member_policy="required",
            version=1,
            updated_by_user_id=engineer_user.id,
        )
    )
    db_session.commit()

    access = client.get("/auth/me", headers=engineer_headers)

    assert access.status_code == 401


def test_password_change_verifier_is_throttled_before_sixth_verification(
    client, engineer_user, engineer_headers, db_session
):
    responses = [
        client.post(
            "/auth/change-password",
            headers=engineer_headers,
            json={
                "current_password": "wrong-password",
                "new_password": "replacement-password",
            },
        )
        for _ in range(settings.AUTH_THROTTLE_FAILURE_THRESHOLD)
    ]
    blocked = client.post(
        "/auth/change-password",
        headers=engineer_headers,
        json={
            "current_password": "correct-password",
            "new_password": "replacement-password",
        },
    )

    assert [response.json() for response in responses] == [
        {"outcome": "invalid_request"}
    ] * 5
    assert blocked.status_code == 200
    assert blocked.json() == {"outcome": "invalid_request"}
    db_session.refresh(engineer_user)
    assert engineer_user.auth_version == 1
    state = db_session.query(AuthThrottleState).one()
    assert state.failure_count == settings.AUTH_THROTTLE_FAILURE_THRESHOLD


def test_successful_password_change_atomically_clears_verifier_failures(
    client, engineer_headers, db_session
):
    rejected = client.post(
        "/auth/change-password",
        headers=engineer_headers,
        json={
            "current_password": "wrong-password",
            "new_password": "replacement-password",
        },
    )
    changed = client.post(
        "/auth/change-password",
        headers=engineer_headers,
        json={
            "current_password": "correct-password",
            "new_password": "replacement-password",
        },
    )

    assert rejected.json() == {"outcome": "invalid_request"}
    assert changed.status_code == 200
    assert changed.json() == {"outcome": "success"}
    assert db_session.query(AuthThrottleState).count() == 0
