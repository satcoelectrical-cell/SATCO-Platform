"""PATCH-058 Checkpoint C1 Customer/Contact tenant-isolation evidence."""

from uuid import uuid4

from app.models.contact import Contact
from app.models.customer import Customer
from app.models.organization import Organization


def _foreign_customer_contact(db_session, *, marker: str):
    organization = Organization(id=uuid4(), is_active=True)
    customer = Customer(
        organization_id=organization.id,
        name=f"{marker} Customer",
        email=f"{marker.lower()}-customer@example.com",
    )
    db_session.add_all([organization, customer])
    db_session.flush()
    contact = Contact(
        customer_id=customer.id,
        first_name=marker,
        last_name="Contact",
        email=f"{marker.lower()}-contact@example.com",
    )
    db_session.add(contact)
    db_session.commit()
    return customer, contact


def test_contact_identifier_is_protected_not_found_across_organization(client, db_session, engineer_headers):
    _, foreign = _foreign_customer_contact(db_session, marker="ForeignProbe")

    fetched = client.get(f"/contacts/{foreign.id}", headers=engineer_headers)
    updated = client.put(
        f"/contacts/{foreign.id}", json={"position": "Leaked"}, headers=engineer_headers
    )
    deleted = client.delete(f"/contacts/{foreign.id}", headers=engineer_headers)

    assert fetched.status_code == updated.status_code == deleted.status_code == 404
    assert fetched.json()["detail"] == updated.json()["detail"] == deleted.json()["detail"] == "Contact not found"
    assert db_session.get(Contact, foreign.id).position is None


def test_contact_create_cannot_attach_to_foreign_customer(client, db_session, engineer_headers):
    foreign_customer, _ = _foreign_customer_contact(db_session, marker="ForeignCreate")
    response = client.post(
        "/contacts/",
        json={"customer_id": foreign_customer.id, "first_name": "Injected"},
        headers=engineer_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"


def test_contact_list_foreign_customer_filter_does_not_leak_count(client, db_session, engineer_headers):
    foreign_customer, foreign = _foreign_customer_contact(db_session, marker="ForeignList")
    response = client.get(
        "/contacts/", params={"customer_id": foreign_customer.id, "page": 1, "size": 1}, headers=engineer_headers
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["items"] == []
    assert foreign.id not in {item["id"] for item in response.json()["items"]}


def test_universal_search_foreign_customer_and_contact_do_not_affect_rows_or_totals(client, db_session, engineer_headers):
    foreign_customer, foreign_contact = _foreign_customer_contact(db_session, marker="UniqueForeignNeedle")

    for search_type in ("all", "customer", "contact"):
        response = client.get(
            "/search/", params={"q": "UniqueForeignNeedle", "type": search_type, "page": 1, "size": 1}, headers=engineer_headers
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["total"] == 0
        assert payload["results"]["customers"] == []
        assert payload["results"]["contacts"] == []
        assert foreign_customer.id not in {item["id"] for item in payload["results"]["customers"]}
        assert foreign_contact.id not in {item["id"] for item in payload["results"]["contacts"]}
