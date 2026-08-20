"""PATCH-038 Customer tenant scoping and protected disclosure evidence."""

from uuid import UUID, uuid4

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from conftest import owner_engine

from app.models.customer import Customer
from app.models.organization import Organization


ORGANIZATION_ID = UUID("02810000-0000-4000-8000-000000000001")


def test_customer_list_update_delete_and_project_create_protect_foreign_tenant(
    client,
    db_session,
    engineer_headers,
    admin_headers,
) -> None:
    foreign_organization = Organization(id=uuid4(), is_active=True)
    foreign_customer = Customer(
        organization_id=foreign_organization.id,
        name="Foreign Confidential Customer",
    )
    db_session.add_all([foreign_organization, foreign_customer])
    db_session.commit()

    listed = client.get(
        "/customers/",
        params={"search": "Foreign Confidential"},
        headers=engineer_headers,
    )
    assert listed.status_code == 200
    assert listed.json()["items"] == []
    assert listed.json()["total"] == 0

    updated = client.put(
        f"/customers/{foreign_customer.id}",
        json={"name": "Leaked"},
        headers=engineer_headers,
    )
    assert updated.status_code == 404
    deleted = client.delete(
        f"/customers/{foreign_customer.id}",
        headers=admin_headers,
    )
    assert deleted.status_code == 404

    project = client.post(
        "/projects/",
        json={"name": "Cross Tenant", "customer_id": foreign_customer.id},
        headers=engineer_headers,
    )
    assert project.status_code == 404
    assert project.json()["error"]["code"] == "CUSTOMER_NOT_FOUND"


def test_customer_organization_cannot_be_client_supplied(
    client,
    engineer_headers,
) -> None:
    response = client.post(
        "/customers/",
        json={"name": "Injected", "organization_id": str(uuid4())},
        headers=engineer_headers,
    )
    assert response.status_code == 422


def test_runtime_role_cannot_transfer_ownership_or_execute_guards() -> None:
    runtime = create_engine(owner_engine.url.set(
        username="satco_runtime",
        password=os.getenv(
            "TEST_RUNTIME_DATABASE_PASSWORD",
            "satco_runtime_test_password",
        ),
    ))
    try:
        with runtime.connect() as connection:
            update_columns = set(connection.execute(text(
                "SELECT column_name FROM information_schema.role_column_grants "
                "WHERE grantee=current_user AND table_name='customers' "
                "AND privilege_type='UPDATE'"
            )).scalars())
            assert update_columns == {"name", "company", "phone", "email"}
            executable = connection.execute(text(
                "SELECT EXISTS (SELECT 1 FROM pg_proc "
                "WHERE proname IN ('satco_customer_org_immutable',"
                "'satco_project_customer_org_guard') "
                "AND has_function_privilege(current_user, oid, 'EXECUTE'))"
            )).scalar_one()
            assert executable is False
        with pytest.raises(DBAPIError), runtime.begin() as connection:
            connection.execute(text(
                "UPDATE customers SET organization_id=organization_id WHERE false"
            ))
    finally:
        runtime.dispose()
