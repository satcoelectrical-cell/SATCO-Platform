import os
import subprocess
from uuid import uuid4

import pytest
from sqlalchemy import inspect
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.database import engine
from app.models.customer import Customer
from app.models.engineering_context import EngineeringContext
from app.models.engineering_context import EngineeringContextSourceReference
from app.models.engineering_context import EngineeringContextValue
from app.models.project import Project


CONTEXT_TABLES = {
    "engineering_contexts",
    "engineering_context_facts",
    "engineering_context_values",
    "engineering_context_assumptions",
    "engineering_context_subject_references",
    "engineering_context_source_references",
}


def test_engineering_context_database_contract():
    inspector = inspect(engine)
    assert CONTEXT_TABLES <= set(inspector.get_table_names())

    context_columns = {
        column["name"]: column
        for column in inspector.get_columns("engineering_contexts")
    }
    assert {
        "id",
        "context_key",
        "kind",
        "scope",
        "project_id",
        "workspace_id",
        "owner_id",
        "steward_id",
        "created_by_id",
        "authority",
        "lifecycle",
        "purpose",
        "version",
        "withdrawal_reason",
        "withdrawn_at",
        "created_at",
        "updated_at",
    } == set(context_columns)
    for required in (
        "context_key",
        "kind",
        "scope",
        "project_id",
        "owner_id",
        "steward_id",
        "created_by_id",
        "authority",
        "lifecycle",
        "version",
        "created_at",
        "updated_at",
    ):
        assert context_columns[required]["nullable"] is False

    check_names = {
        item["name"]
        for item in inspector.get_check_constraints(
            "engineering_contexts"
        )
    }
    assert {
        "ck_engineering_contexts_kind",
        "ck_engineering_contexts_scope",
        "ck_engineering_contexts_authority",
        "ck_engineering_contexts_lifecycle",
        "ck_engineering_contexts_scope_workspace",
        "ck_engineering_contexts_kind_authority",
        "ck_engineering_contexts_lifecycle_state",
        "ck_engineering_contexts_version",
    } <= check_names

    foreign_keys = {
        item["name"]
        for item in inspector.get_foreign_keys("engineering_contexts")
    }
    assert {
        "fk_engineering_contexts_project_id_projects",
        (
            "fk_engineering_contexts_workspace_id_"
            "engineering_workspaces"
        ),
        "fk_engineering_contexts_owner_id_users",
        "fk_engineering_contexts_steward_id_users",
        "fk_engineering_contexts_created_by_id_users",
    } <= foreign_keys
    assert all(
        item["options"].get("ondelete") == "RESTRICT"
        for item in inspector.get_foreign_keys(
            "engineering_contexts"
        )
    )

    unique_names = {
        item["name"]
        for item in inspector.get_unique_constraints(
            "engineering_contexts"
        )
    }
    assert "uq_engineering_contexts_context_key" in unique_names
    index_names = {
        item["name"]
        for item in inspector.get_indexes("engineering_contexts")
    }
    assert {
        "ix_engineering_contexts_project_lifecycle",
        "ix_engineering_contexts_workspace_lifecycle",
        "ix_engineering_contexts_owner_id",
        "ix_engineering_contexts_steward_id",
    } <= index_names

    with engine.connect() as connection:
        database_name, revision = connection.execute(
            text(
                "SELECT current_database(), "
                "(SELECT version_num FROM alembic_version)"
            )
        ).one()
    assert database_name == "satco_platform_patch02021_test"
    assert revision == "c2021f0c0a01"


def _base_context(project, user, **overrides):
    values = {
        "context_key": str(uuid4()),
        "kind": "subject_reference",
        "scope": "project",
        "project_id": project.id,
        "workspace_id": None,
        "owner_id": user.id,
        "steward_id": user.id,
        "created_by_id": user.id,
        "authority": "authoritative_fact",
        "lifecycle": "current",
        "version": 1,
    }
    values.update(overrides)
    return EngineeringContext(**values)


@pytest.mark.parametrize(
    "overrides",
    [
        {"kind": "derived_finding"},
        {"scope": "global"},
        {"authority": "ai_suggestion"},
        {"lifecycle": "historical"},
        {"version": 0},
        {"scope": "workspace", "workspace_id": None},
        {
            "lifecycle": "withdrawn",
            "withdrawn_at": None,
            "withdrawal_reason": None,
        },
        {
            "kind": "assumption",
            "authority": "authoritative_fact",
        },
    ],
    ids=[
        "invalid-kind",
        "invalid-scope",
        "invalid-authority",
        "invalid-lifecycle",
        "non-positive-version",
        "workspace-scope-without-workspace",
        "withdrawn-without-evidence",
        "assumption-authority-mismatch",
    ],
)
def test_postgresql_rejects_invalid_context_constraints(
    db_session,
    engineer_user,
    overrides,
):
    customer = Customer(name=f"Constraint Customer {uuid4()}")
    db_session.add(customer)
    db_session.flush()
    project = Project(
        project_code=f"SAT-PRJ-2098-{5000 + customer.id:04d}",
        name="Constraint Project",
        customer_id=customer.id,
        owner_id=engineer_user.id,
    )
    db_session.add(project)
    db_session.flush()

    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(
                _base_context(project, engineer_user, **overrides)
            )
            db_session.flush()


def test_postgresql_rejects_duplicate_identity_and_invalid_foreign_key(
    db_session,
    engineer_user,
):
    customer = Customer(name="Context Uniqueness Customer")
    db_session.add(customer)
    db_session.flush()
    project = Project(
        project_code="SAT-PRJ-2098-6001",
        name="Context Uniqueness Project",
        customer_id=customer.id,
        owner_id=engineer_user.id,
    )
    db_session.add(project)
    db_session.flush()
    context_key = str(uuid4())
    db_session.add(
        _base_context(
            project,
            engineer_user,
            context_key=context_key,
        )
    )
    db_session.flush()

    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(
                _base_context(
                    project,
                    engineer_user,
                    context_key=context_key,
                )
            )
            db_session.flush()

    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(
                _base_context(
                    project,
                    engineer_user,
                    project_id=99999999,
                )
            )
            db_session.flush()


def test_postgresql_rejects_invalid_source_and_value_constraints(
    db_session,
    engineer_user,
):
    customer = Customer(name="Context Child Constraint Customer")
    db_session.add(customer)
    db_session.flush()
    project = Project(
        project_code="SAT-PRJ-2098-6002",
        name="Context Child Constraint Project",
        customer_id=customer.id,
        owner_id=engineer_user.id,
    )
    db_session.add(project)
    db_session.flush()
    context = _base_context(
        project,
        engineer_user,
        kind="qualified_engineering_value",
    )
    db_session.add(context)
    db_session.flush()

    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(
                EngineeringContextSourceReference(
                    context_id=context.id,
                    source_kind="ai_interpretation",
                    source_key="INVALID",
                    revision="1",
                    confidentiality="project",
                    applicability="Invalid",
                )
            )
            db_session.flush()

    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(
                EngineeringContextValue(
                    context_id=context.id,
                    numeric_value=10,
                    unit="A",
                    quantity_type="current",
                    tolerance_min=20,
                    tolerance_max=10,
                    basis="Invalid",
                    condition_type="design",
                    condition="Invalid",
                )
            )
            db_session.flush()


def test_migration_fresh_chain_rollback_and_reapplication():
    test_database_url = os.environ["TEST_DATABASE_URL"]
    assert test_database_url.rsplit("/", 1)[-1] == (
        "satco_platform_patch02021_test"
    )
    schema = f"context_migration_{uuid4().hex}"
    with engine.begin() as connection:
        actual = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()
        assert actual == "satco_platform_patch02021_test"
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))

    environment = {
        **os.environ,
        "ALEMBIC_DATABASE_URL": test_database_url,
        "PGOPTIONS": f"-csearch_path={schema}",
    }
    try:
        subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd="/app",
            env=environment,
            check=True,
        )
        with engine.connect().execution_options(
            schema_translate_map={None: schema}
        ) as connection:
            tables = set(
                inspect(connection).get_table_names(schema=schema)
            )
        assert CONTEXT_TABLES <= tables

        subprocess.run(
            ["alembic", "downgrade", "a20c1e0201f0"],
            cwd="/app",
            env=environment,
            check=True,
        )
        with engine.connect() as connection:
            tables = set(
                inspect(connection).get_table_names(schema=schema)
            )
        assert not (CONTEXT_TABLES & tables)
        assert "engineering_workspaces" in tables

        subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd="/app",
            env=environment,
            check=True,
        )
        with engine.connect() as connection:
            tables = set(
                inspect(connection).get_table_names(schema=schema)
            )
        assert CONTEXT_TABLES <= tables
    finally:
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
