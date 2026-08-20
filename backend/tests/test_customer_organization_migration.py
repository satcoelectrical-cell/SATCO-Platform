"""PATCH-038 Customer ownership migration and database-guard evidence."""

from alembic import command
from alembic.script import ScriptDirectory
import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError

from conftest import alembic_config, owner_engine
from app.core.database import engine as application_engine


LEGACY_ORGANIZATION_ID = "7e7c9d7a-7693-4f75-9bc5-3ef7bf528281"


def test_patch_038_is_sole_repository_head_with_expected_parent() -> None:
    script = ScriptDirectory.from_config(alembic_config)
    assert script.get_heads() == ["e03800000001"]
    assert script.get_revision("e03800000001").down_revision == "e03400000001"


def test_customer_ownership_schema_index_functions_and_triggers() -> None:
    inspector = inspect(owner_engine)
    columns = {
        column["name"]: column
        for column in inspector.get_columns("customers")
    }
    assert columns["organization_id"]["nullable"] is False
    foreign_keys = {
        item["name"]: item for item in inspector.get_foreign_keys("customers")
    }
    assert foreign_keys[
        "fk_customers_organization_id_organizations"
    ]["referred_table"] == "organizations"
    indexes = {item["name"] for item in inspector.get_indexes("customers")}
    assert "ix_customers_organization_name_id" in indexes

    with owner_engine.connect() as connection:
        functions = set(connection.execute(text(
            "SELECT proname FROM pg_proc WHERE proname IN "
            "('satco_customer_org_immutable','satco_project_customer_org_guard')"
        )).scalars())
        triggers = set(connection.execute(text(
            "SELECT tgname FROM pg_trigger WHERE tgname IN "
            "('trg_customers_org_immutable','trg_projects_customer_org_guard') "
            "AND NOT tgisinternal AND tgenabled='O'"
        )).scalars())
    assert functions == {
        "satco_customer_org_immutable",
        "satco_project_customer_org_guard",
    }
    assert triggers == {
        "trg_customers_org_immutable",
        "trg_projects_customer_org_guard",
    }


def test_direct_sql_cannot_transfer_customer_or_cross_project_tenant(
    db_session,
) -> None:
    from uuid import UUID, uuid4

    from app.models.customer import Customer
    from app.models.organization import Organization
    from app.models.project import Project

    owning = UUID("02810000-0000-4000-8000-000000000001")
    foreign = Organization(id=uuid4(), is_active=True)
    customer = Customer(organization_id=owning, name="Guarded Customer")
    db_session.add_all([foreign, customer])
    db_session.flush()

    ownership_savepoint = db_session.begin_nested()
    with pytest.raises(DBAPIError):
        db_session.execute(
            text("UPDATE customers SET organization_id=:foreign WHERE id=:id"),
            {"foreign": foreign.id, "id": customer.id},
        )
        db_session.flush()
    ownership_savepoint.rollback()

    project = Project(
        organization_id=owning,
        project_code=f"SAT-PRJ-2099-{customer.id + 7000:04d}",
        name="Guarded Project",
        customer_id=customer.id,
    )
    db_session.add(project)
    db_session.flush()
    project_savepoint = db_session.begin_nested()
    with pytest.raises(DBAPIError):
        db_session.execute(
            text("UPDATE projects SET organization_id=:foreign WHERE id=:id"),
            {"foreign": foreign.id, "id": project.id},
        )
        db_session.flush()
    project_savepoint.rollback()


def test_exact_legacy_inventory_upgrade_downgrade_reupgrade_without_loss() -> None:
    application_engine.dispose()
    owner_engine.dispose()
    command.downgrade(alembic_config, "e03400000001")
    try:
        with owner_engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO organizations (id,is_active) VALUES (:id,true) "
                "ON CONFLICT (id) DO UPDATE SET is_active=true"
            ), {"id": LEGACY_ORGANIZATION_ID})
            connection.execute(text(
                "INSERT INTO customers (id,name) VALUES "
                "(1,'SATCO Test Customer'),(2,'SATCO Test Customer'),"
                "(3,'Demo Customer'),(4,'SATCO'),(6,'CONTACT AUDIT CUSTOMER')"
            ))
        application_engine.dispose()
        owner_engine.dispose()
        command.upgrade(alembic_config, "head")
        with owner_engine.connect() as connection:
            mapped = connection.execute(text(
                "SELECT id,organization_id::text FROM customers ORDER BY id"
            )).all()
        assert mapped == [
            (customer_id, LEGACY_ORGANIZATION_ID)
            for customer_id in (1, 2, 3, 4, 6)
        ]
        application_engine.dispose()
        owner_engine.dispose()
        command.downgrade(alembic_config, "e03400000001")
        with owner_engine.begin() as connection:
            connection.execute(text("DELETE FROM customers WHERE id IN (1,2,3,4,6)"))
        application_engine.dispose()
        owner_engine.dispose()
        command.upgrade(alembic_config, "head")
    finally:
        with owner_engine.connect() as connection:
            revision = connection.execute(text(
                "SELECT version_num FROM alembic_version"
            )).scalar_one()
        if revision != "e03800000001":
            command.upgrade(alembic_config, "head")
