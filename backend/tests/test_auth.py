import pytest

from app.core.config import settings
from app.core.security import create_access_token
from app.dependencies.auth import require_role
from app.models.auth_security import AuthThrottleState
from app.models.organization import UserOrganizationMembership
from app.models.user import User
from app.permissions.roles import Role
from app.services import user_service as user_service_module

from conftest import create_user


def registration_payload(**overrides):
    payload = {
        "email": "new-user@example.com",
        "username": "new-user",
        "full_name": "New User",
        "password": "strong-password",
    }
    payload.update(overrides)
    return payload


def test_public_registration_is_closed(client, db_session):
    response = client.post(
        "/auth/register",
        json=registration_payload(),
    )

    assert response.status_code == 404
    assert response.json() == {"outcome": "protected_not_found"}
    assert db_session.query(User).filter(User.username == "new-user").count() == 0


def test_closed_registration_does_not_disclose_role_validation(client):
    response = client.post(
        "/auth/register",
        json=registration_payload(role="admin"),
    )

    assert response.status_code == 404
    assert response.json() == {"outcome": "protected_not_found"}


def test_closed_registration_does_not_disclose_duplicate_email(client):
    first = client.post(
        "/auth/register",
        json=registration_payload(),
    )
    duplicate = client.post(
        "/auth/register",
        json=registration_payload(username="another-user"),
    )

    assert first.status_code == 404
    assert duplicate.status_code == 404
    assert duplicate.json() == {"outcome": "protected_not_found"}


def test_closed_registration_does_not_disclose_duplicate_username(client):
    first = client.post(
        "/auth/register",
        json=registration_payload(),
    )
    duplicate = client.post(
        "/auth/register",
        json=registration_payload(email="another@example.com"),
    )

    assert first.status_code == 404
    assert duplicate.status_code == 404
    assert duplicate.json() == {"outcome": "protected_not_found"}


def test_oauth2_form_login_returns_tokens(
    client,
    engineer_user,
):
    response = client.post(
        "/auth/login",
        data={
            "username": engineer_user.username,
            "password": "correct-password",
        },
    )

    assert response.status_code == 200
    assert response.json()["access_token"]
    assert "refresh_token" not in response.json()
    assert client.cookies.get("satco_refresh")
    assert client.cookies.get("satco_csrf")
    assert response.json()["token_type"] == "bearer"


def test_login_rejects_invalid_credentials(
    client,
    engineer_user,
):
    response = client.post(
        "/auth/login",
        data={
            "username": engineer_user.username,
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401


def test_primary_login_throttles_five_failures_and_blocks_sixth(
    client,
    engineer_user,
    db_session,
):
    responses = [
        client.post(
            "/auth/login",
            data={"username": engineer_user.username, "password": "wrong-password"},
        )
        for _ in range(settings.AUTH_THROTTLE_FAILURE_THRESHOLD)
    ]
    blocked = client.post(
        "/auth/login",
        data={"username": engineer_user.username, "password": "correct-password"},
    )

    assert [response.status_code for response in responses] == [401] * 5
    assert blocked.status_code == 429
    assert blocked.json() == responses[-1].json()
    state = db_session.query(AuthThrottleState).one()
    assert state.failure_count == settings.AUTH_THROTTLE_FAILURE_THRESHOLD
    assert state.blocked_until is not None
    assert engineer_user.username not in state.credential_key
    assert "testclient" not in state.network_key


def test_primary_login_normalizes_unknown_identity_and_ignores_forwarded_peer(
    client,
):
    spellings = ["  Missing-User  ", "missing-user", "MISSING-USER", " missing-user ", "missing-user"]
    responses = [
        client.post(
            "/auth/login",
            headers={"X-Forwarded-For": f"203.0.113.{index}"},
            data={"username": username, "password": "wrong-password"},
        )
        for index, username in enumerate(spellings, start=1)
    ]
    blocked = client.post(
        "/auth/login",
        headers={"X-Forwarded-For": "198.51.100.200"},
        data={"username": "Missing-User", "password": "wrong-password"},
    )

    assert [response.status_code for response in responses] == [401] * 5
    assert blocked.status_code == 429
    assert blocked.json() == responses[-1].json()


def test_unknown_login_executes_dummy_password_verification(client, monkeypatch):
    calls = []
    real_verify = user_service_module.verify_password

    def observed_verify(password, password_hash):
        calls.append((password, password_hash))
        return real_verify(password, password_hash)

    monkeypatch.setattr(user_service_module, "verify_password", observed_verify)
    response = client.post(
        "/auth/login",
        data={"username": "does-not-exist", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert len(calls) == 1
    assert calls[0][0] == "wrong-password"
    assert calls[0][1] == user_service_module._UNKNOWN_USER_PASSWORD_HASH


def test_primary_login_uses_generic_failure_for_unknown_disabled_and_ineligible(
    client,
    db_session,
):
    disabled = create_user(
        db_session,
        username="disabled-login",
        role=Role.ENGINEER,
        is_active=False,
    )
    ineligible = create_user(
        db_session,
        username="ineligible-login",
        role=Role.ENGINEER,
    )
    membership = (
        db_session.query(UserOrganizationMembership)
        .filter_by(user_id=ineligible.id)
        .one()
    )
    membership.is_enabled = False
    membership.is_selected = False
    db_session.commit()

    attempts = (
        ("unknown-login", "correct-password"),
        (disabled.username, "correct-password"),
        (ineligible.username, "correct-password"),
    )
    responses = [
        client.post(
            "/auth/login",
            data={"username": username, "password": password},
        )
        for username, password in attempts
    ]

    assert [response.status_code for response in responses] == [401, 401, 401]
    assert len({str(response.json()) for response in responses}) == 1


def test_successful_primary_authentication_clears_applicable_failures(
    client,
    engineer_user,
):
    for _ in range(settings.AUTH_THROTTLE_FAILURE_THRESHOLD - 1):
        assert client.post(
            "/auth/login",
            data={"username": engineer_user.username, "password": "wrong-password"},
        ).status_code == 401

    assert client.post(
        "/auth/login",
        data={"username": engineer_user.username, "password": "correct-password"},
    ).status_code == 200

    after_reset = [
        client.post(
            "/auth/login",
            data={"username": engineer_user.username, "password": "wrong-password"},
        ).status_code
        for _ in range(settings.AUTH_THROTTLE_FAILURE_THRESHOLD - 1)
    ]
    assert after_reset == [401] * 4


def test_login_does_not_accept_query_credentials(
    client,
    engineer_user,
):
    response = client.post(
        "/auth/login",
        params={
            "username": engineer_user.username,
            "password": "correct-password",
        },
    )

    assert response.status_code == 422


def test_protected_endpoint_rejects_missing_token(client):
    response = client.get("/customers/")

    assert response.status_code == 401


def test_protected_endpoint_rejects_invalid_token(client):
    response = client.get(
        "/customers/",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


def test_refresh_credential_is_not_an_access_token(
    client,
    engineer_user,
):
    login = client.post(
        "/auth/login",
        data={
            "username": engineer_user.username,
            "password": "correct-password",
        },
    )
    assert "refresh_token" not in login.json()
    refresh_credential = client.cookies.get("satco_refresh")
    assert refresh_credential

    response = client.get(
        "/customers/",
        headers={
            "Authorization": f"Bearer {refresh_credential}",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication credentials"

def test_unknown_token_subject_is_rejected(client):
    access_token = create_access_token(999999)

    response = client.get(
        "/customers/",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 401


def test_inactive_user_is_rejected(client, db_session):
    user = create_user(
        db_session,
        username="inactive",
        role=Role.ENGINEER,
        is_active=False,
    )
    access_token = create_access_token(user.id)

    response = client.get(
        "/customers/",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 403


def test_role_dependency_rejects_unsupported_role():
    with pytest.raises(
        ValueError,
        match="Unsupported role",
    ):
        require_role("owner")
