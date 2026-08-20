from uuid import UUID

from app.models.audit_log import AuditLog


ORGANIZATION_ID = UUID("02810000-0000-4000-8000-000000000001")


def customer_payload(name="Customer One"):
    return {
        "name": name,
        "company": "SATCO Customer Company",
        "phone": "12345",
        "email": f"{name.lower().replace(' ', '-')}@example.com",
    }


def test_customer_crud_missing_records_and_audits(
    client,
    db_session,
    engineer_headers,
    admin_headers,
):
    created = client.post(
        "/customers/",
        json=customer_payload(),
        headers=engineer_headers,
    )
    assert created.status_code == 200
    customer_id = created.json()["id"]

    listed = client.get(
        "/customers/",
        params={"page": 1, "size": 1, "search": "Customer One"},
        headers=engineer_headers,
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == customer_id

    updated = client.put(
        f"/customers/{customer_id}",
        json={"name": "Customer Updated"},
        headers=engineer_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Customer Updated"

    missing_update = client.put(
        "/customers/999999",
        json={"name": "Missing"},
        headers=engineer_headers,
    )
    assert missing_update.status_code == 404

    deleted = client.delete(
        f"/customers/{customer_id}",
        headers=admin_headers,
    )
    assert deleted.status_code == 200

    missing_delete = client.delete(
        "/customers/999999",
        headers=admin_headers,
    )
    assert missing_delete.status_code == 404

    actions = {
        row.action
        for row in (
            db_session.query(AuditLog)
            .filter(
                AuditLog.entity == "CUSTOMER",
                AuditLog.entity_id == customer_id,
            )
            .all()
        )
    }
    assert actions == {"CREATE", "UPDATE", "DELETE"}


def test_customer_response_and_listing_do_not_disclose_organization_id(
    client,
    engineer_headers,
):
    created = client.post(
        "/customers/",
        json=customer_payload("Scoped Customer"),
        headers=engineer_headers,
    )
    assert created.status_code == 200
    assert "organization_id" not in created.json()

    listed = client.get("/customers/", headers=engineer_headers)
    assert listed.status_code == 200
    assert all(
        "organization_id" not in item
        for item in listed.json()["items"]
    )


def test_customer_detail_remains_isolated_and_functional(
    db_session,
):
    from app.repositories.customer_repository import CustomerRepository
    from app.schemas.customer import CustomerCreate
    from app.services.customer_service import CustomerService

    customer = CustomerRepository(db_session).create(
        CustomerCreate(**customer_payload("Detail Customer")),
        organization_id=ORGANIZATION_ID,
    )

    detail = CustomerService(db_session).get_detail(
        customer.id,
        organization_id=ORGANIZATION_ID,
    )

    assert detail["customer"].id == customer.id
    assert detail["contacts"] == []
    assert detail["contact_count"] == 0
    assert CustomerService(db_session).get_detail(
        999999,
        organization_id=ORGANIZATION_ID,
    ) is None
