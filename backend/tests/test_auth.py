import pytest

from app.core.security import create_access_token, create_refresh_token
from app.dependencies.auth import require_role
from app.models.user import User
from app.permissions.roles import Role

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


def test_registration_assigns_engineer_role(client, db_session):
    response = client.post(
        "/auth/register",
        json=registration_payload(),
    )

    assert response.status_code == 200
    assert response.json()["role"] == Role.ENGINEER.value

    user = (
        db_session.query(User)
        .filter(User.username == "new-user")
        .one()
    )
    assert user.role == Role.ENGINEER.value


def test_registration_rejects_role_injection(client):
    response = client.post(
        "/auth/register",
        json=registration_payload(role="admin"),
    )

    assert response.status_code == 422


def test_registration_rejects_duplicate_email(client):
    first = client.post(
        "/auth/register",
        json=registration_payload(),
    )
    duplicate = client.post(
        "/auth/register",
        json=registration_payload(username="another-user"),
    )

    assert first.status_code == 200
    assert duplicate.status_code == 400
    assert duplicate.json()["detail"] == "Email already exists"


def test_registration_rejects_duplicate_username(client):
    first = client.post(
        "/auth/register",
        json=registration_payload(),
    )
    duplicate = client.post(
        "/auth/register",
        json=registration_payload(email="another@example.com"),
    )

    assert first.status_code == 200
    assert duplicate.status_code == 400
    assert duplicate.json()["detail"] == "Username already exists"


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
    assert response.json()["refresh_token"]
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


def test_refresh_token_is_not_an_access_token(
    client,
    engineer_user,
):
    refresh_token = create_refresh_token(engineer_user.id)

    response = client.get(
        "/customers/",
        headers={
            "Authorization": f"Bearer {refresh_token}",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token type"


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
