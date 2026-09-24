from datetime import datetime, timezone

import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import create_access_token
from app.models.auth_security import AuthRefreshFamily, AuthRefreshSession, AuthSecurityEvent


def _login(client, user):
    return client.post(
        "/auth/login",
        data={"username": user.username, "password": "correct-password"},
    )


def test_access_token_contract_is_hardened(client, engineer_user):
    response = _login(client, engineer_user)
    assert response.status_code == 200
    token = response.json()["access_token"]
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        issuer="satco-platform",
        audience="satco-web",
    )
    assert payload["type"] == "access"
    assert payload["av"] == engineer_user.auth_version
    assert payload["sid"]
    assert payload["jti"]
    assert payload["iat"]
    assert payload["iss"] == "satco-platform"
    assert payload["aud"] == "satco-web"
    assert payload["exp"] - payload["iat"] == 15 * 60


def test_missing_security_version_fails_closed(client, engineer_user, db_session):
    login = _login(client, engineer_user)
    sid = jwt.decode(
        login.json()["access_token"],
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        issuer=settings.ACCESS_TOKEN_ISSUER,
        audience=settings.ACCESS_TOKEN_AUDIENCE,
    )["sid"]
    now = int(datetime.now(timezone.utc).timestamp())
    token = jwt.encode(
        {
            "sub": str(engineer_user.id),
            "type": "access",
            "iat": now,
            "exp": now + 900,
            "jti": "missing-av",
            "iss": settings.ACCESS_TOKEN_ISSUER,
            "aud": settings.ACCESS_TOKEN_AUDIENCE,
            "sid": sid,
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    response = client.get("/customers/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_login_persists_only_refresh_verifier(client, engineer_user, db_session):
    response = _login(client, engineer_user)
    assert response.status_code == 200
    credential = response.json()["refresh_token"]
    selector, secret = credential.split(".", 1)
    session = db_session.query(AuthRefreshSession).filter_by(selector=selector).one()
    assert session.user_id == engineer_user.id
    assert session.secret_verifier != secret
    assert len(session.secret_verifier) == 64
    assert secret not in session.secret_verifier


def test_refresh_rotates_once_and_reuse_revokes_family(client, engineer_user, db_session):
    first = _login(client, engineer_user)
    credential = first.json()["refresh_token"]
    selector = credential.split(".", 1)[0]
    predecessor = db_session.query(AuthRefreshSession).filter_by(selector=selector).one()
    family_id = predecessor.family_id

    rotated = client.post("/auth/refresh", json={"refresh_token": credential})
    assert rotated.status_code == 200
    replacement = rotated.json()["refresh_token"]
    assert replacement != credential
    db_session.expire_all()
    predecessor = db_session.get(AuthRefreshSession, predecessor.id)
    assert predecessor.consumed_at is not None
    successor = (
        db_session.query(AuthRefreshSession)
        .filter(AuthRefreshSession.predecessor_id == predecessor.id)
        .one()
    )
    assert successor.family_id == family_id
    rotation_event = (
        db_session.query(AuthSecurityEvent)
        .filter(
            AuthSecurityEvent.event_type == "refresh_rotation",
            AuthSecurityEvent.session_id == successor.id,
        )
        .one()
    )
    assert rotation_event.user_id == engineer_user.id
    assert rotation_event.outcome == "success"
    assert rotation_event.safe_context is None

    reused = client.post("/auth/refresh", json={"refresh_token": credential})
    assert reused.status_code == 401
    db_session.expire_all()
    family = db_session.get(AuthRefreshFamily, family_id)
    assert family.reuse_detected_at is not None
    assert family.revoked_at is not None
    assert family.revocation_reason == "refresh_reuse"
    reuse_event = (
        db_session.query(AuthSecurityEvent)
        .filter(
            AuthSecurityEvent.event_type == "refresh_reuse_detected",
            AuthSecurityEvent.session_id == predecessor.id,
        )
        .one()
    )
    assert reuse_event.user_id == engineer_user.id
    assert reuse_event.outcome == "rejected"
    assert reuse_event.safe_context is None
    family_sessions = (
        db_session.query(AuthRefreshSession)
        .filter(AuthRefreshSession.family_id == family_id)
        .all()
    )
    assert family_sessions
    assert all(item.revoked_at is not None for item in family_sessions)

    blocked = client.post("/auth/refresh", json={"refresh_token": replacement})
    assert blocked.status_code == 401


def test_refresh_rejects_stale_auth_version(client, engineer_user, db_session):
    first = _login(client, engineer_user)
    engineer_user.auth_version += 1
    db_session.commit()
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": first.json()["refresh_token"]},
    )
    assert response.status_code == 401


def test_access_token_requires_live_bound_session(client, engineer_user):
    token = create_access_token(engineer_user.id, engineer_user.auth_version)
    response = client.get("/customers/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_refresh_unknown_or_bad_secret_is_generic(client, engineer_user):
    first = _login(client, engineer_user)
    credential = first.json()["refresh_token"]
    selector = credential.split(".", 1)[0]
    for candidate in (
        "x" * 24 + "." + "y" * 43,
        selector + "." + "z" * 43,
    ):
        response = client.post("/auth/refresh", json={"refresh_token": candidate})
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid authentication credentials"


def test_refresh_rejects_disabled_membership(client, engineer_user, db_session):
    first = _login(client, engineer_user)
    from app.models.organization import UserOrganizationMembership

    membership = (
        db_session.query(UserOrganizationMembership)
        .filter(UserOrganizationMembership.user_id == engineer_user.id)
        .one()
    )
    membership.is_selected = False
    membership.is_enabled = False
    db_session.commit()
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": first.json()["refresh_token"]},
    )
    assert response.status_code == 401


def test_revoked_bound_session_invalidates_access(client, engineer_user, db_session):
    first = _login(client, engineer_user)
    access_token = first.json()["access_token"]
    payload = jwt.decode(
        access_token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        issuer=settings.ACCESS_TOKEN_ISSUER,
        audience=settings.ACCESS_TOKEN_AUDIENCE,
    )
    session = db_session.get(AuthRefreshSession, payload["sid"])
    session.revoked_at = datetime.now(timezone.utc)
    session.revocation_reason = "test_revocation"
    db_session.commit()
    response = client.get(
        "/customers/",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
