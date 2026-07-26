def create_customer(client, headers):
    response = client.post(
        "/customers/",
        json={"name": "Audit Customer"},
        headers=headers,
    )
    assert response.status_code == 200


def test_audit_logs_are_admin_only(
    client,
    engineer_headers,
    admin_headers,
):
    create_customer(client, engineer_headers)

    unauthenticated = client.get("/audit-logs/")
    assert unauthenticated.status_code == 401

    engineer = client.get(
        "/audit-logs/",
        headers=engineer_headers,
    )
    assert engineer.status_code == 403

    admin = client.get(
        "/audit-logs/",
        params={"page": 1, "size": 1},
        headers=admin_headers,
    )
    assert admin.status_code == 200
    assert admin.json()["total"] >= 1
    assert len(admin.json()["items"]) == 1
