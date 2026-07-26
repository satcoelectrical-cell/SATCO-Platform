from app.models.audit_log import AuditLog


def create_customer(client, headers):
    response = client.post(
        "/customers/",
        json={"name": "Contact Customer"},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()["id"]


def contact_payload(customer_id):
    return {
        "customer_id": customer_id,
        "first_name": "Contact",
        "last_name": "Person",
        "email": "contact@example.com",
    }


def test_contact_rejects_missing_customer(
    client,
    engineer_headers,
):
    response = client.post(
        "/contacts/",
        json=contact_payload(999999),
        headers=engineer_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"


def test_contact_crud_filtering_missing_records_and_audits(
    client,
    db_session,
    engineer_headers,
):
    customer_id = create_customer(client, engineer_headers)

    created = client.post(
        "/contacts/",
        json=contact_payload(customer_id),
        headers=engineer_headers,
    )
    assert created.status_code == 200
    contact_id = created.json()["id"]

    fetched = client.get(
        f"/contacts/{contact_id}",
        headers=engineer_headers,
    )
    assert fetched.status_code == 200

    listed = client.get(
        "/contacts/",
        params={
            "page": 1,
            "size": 1,
            "customer_id": customer_id,
        },
        headers=engineer_headers,
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == contact_id

    updated = client.put(
        f"/contacts/{contact_id}",
        json={"position": "Engineer"},
        headers=engineer_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["position"] == "Engineer"

    missing_update = client.put(
        "/contacts/999999",
        json={"position": "Missing"},
        headers=engineer_headers,
    )
    assert missing_update.status_code == 404

    deleted = client.delete(
        f"/contacts/{contact_id}",
        headers=engineer_headers,
    )
    assert deleted.status_code == 200

    missing_delete = client.delete(
        "/contacts/999999",
        headers=engineer_headers,
    )
    assert missing_delete.status_code == 404

    actions = {
        row.action
        for row in (
            db_session.query(AuditLog)
            .filter(
                AuditLog.entity == "CONTACT",
                AuditLog.entity_id == contact_id,
            )
            .all()
        )
    }
    assert actions == {"CREATE", "UPDATE", "DELETE"}
