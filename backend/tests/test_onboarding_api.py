from uuid import uuid4

from app.core.config import settings
from app.core.security import create_access_token


def bearer(user):
    return {"Authorization": f"Bearer {create_access_token(user.id, user.auth_version)}"}


def test_platform_bootstrap_requires_configured_secret(client, monkeypatch):
    monkeypatch.setattr(settings, "PLATFORM_BOOTSTRAP_KEY", "x" * 40)
    payload = {
        "organization_name": "First Customer",
        "organization_slug": "first-customer",
        "admin_username": "first-admin",
        "admin_email": "first-admin@example.com",
    }
    denied = client.post(
        "/platform/bootstrap/organizations",
        json=payload,
        headers={"X-SATCO-Bootstrap-Key": "wrong", "Idempotency-Key": str(uuid4())},
    )
    assert denied.status_code == 200
    assert denied.json() == {"outcome": "protected_not_found"}
    success = client.post(
        "/platform/bootstrap/organizations",
        json=payload,
        headers={"X-SATCO-Bootstrap-Key": "x" * 40, "Idempotency-Key": str(uuid4())},
    )
    assert success.status_code == 200
    assert success.json()["outcome"] == "success"
    assert len(success.json()["one_time_token"]) >= 40


def test_engineer_cannot_use_organization_admin(client, engineer_user):
    response = client.get("/organization-admin/members", headers=bearer(engineer_user))
    assert response.status_code == 404
    assert response.json() == {"detail": "Protected resource not found"}


def test_admin_can_list_current_organization_members(client, admin_user):
    response = client.get("/organization-admin/members", headers=bearer(admin_user))
    assert response.status_code == 200
    assert response.json()["outcome"] == "success"
    assert any(item["user_id"] == admin_user.id for item in response.json()["items"])


def test_activation_failure_is_payload_free(client):
    response = client.post("/auth/activate", json={"token": "x" * 48, "new_password": "new-secure-password"})
    assert response.status_code == 200
    assert response.json() == {"outcome": "invalid_request"}
