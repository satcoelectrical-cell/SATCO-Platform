from app.core.security import create_access_token


def test_auth_version_invalidates_old_access_token(client, engineer_user, db_session):
    token = create_access_token(engineer_user.id, engineer_user.auth_version)
    engineer_user.auth_version += 1
    db_session.commit()
    response = client.get("/customers/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_public_registration_is_payload_protected(client):
    response = client.post("/auth/register", json={"username": "x", "password": "x"})
    assert response.status_code == 404
    assert response.json() == {"outcome": "protected_not_found"}


def test_protected_bootstrap_does_not_disclose_validation(client):
    response = client.post(
        "/platform/bootstrap/organizations",
        json={"invalid": "payload"},
        headers={"X-SATCO-Bootstrap-Key": "wrong", "Idempotency-Key": "not-a-uuid"},
    )
    assert response.status_code == 200
    assert response.json() == {"outcome": "protected_not_found"}
