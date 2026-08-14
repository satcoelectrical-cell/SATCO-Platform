"""PATCH-034 restricted runtime/schema-owner persistence evidence."""

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from app.core.database import validate_organizational_memory_runtime_boundary
from conftest import owner_engine


TABLES = {
    "organizational_memories",
    "organizational_memory_standing_history",
    "organizational_memory_events_outbox",
    "organizational_memory_idempotency",
}


def _runtime_engine():
    return create_engine(owner_engine.url.set(
        username="satco_runtime",
        password=os.getenv("TEST_RUNTIME_DATABASE_PASSWORD", "satco_runtime_test_password"),
    ))


def test_runtime_boundary_is_distinct_restricted_owned_and_enabled() -> None:
    runtime = _runtime_engine()
    try:
        validate_organizational_memory_runtime_boundary(
            runtime, migration_role_name=owner_engine.url.username,
        )
    finally:
        runtime.dispose()


def test_exact_runtime_table_and_column_grants() -> None:
    with owner_engine.connect() as connection:
        table_grants = set(connection.execute(text(
            "SELECT table_name,privilege_type FROM information_schema.role_table_grants "
            "WHERE grantee='satco_runtime' AND table_name=ANY(CAST(:tables AS text[]))"
        ), {"tables": list(TABLES)}).tuples())
        assert table_grants == {
            (table, privilege)
            for table in TABLES
            for privilege in ("SELECT", "INSERT")
        }
        column_grants = set(connection.execute(text(
            "SELECT table_name,column_name FROM information_schema.role_column_grants "
            "WHERE grantee='satco_runtime' AND privilege_type='UPDATE' "
            "AND table_name=ANY(CAST(:tables AS text[]))"
        ), {"tables": list(TABLES)}).tuples())
    assert column_grants == {
        *(('organizational_memories', name) for name in (
            'version', 'standing', 'withdrawn_by_id', 'withdrawn_at',
            'withdrawal_reason', 'superseded_by_id', 'superseded_at',
            'supersession_reason', 'replacement_memory_id', 'updated_at',
        )),
        *(('organizational_memory_events_outbox', name) for name in (
            'published_at', 'attempt_count', 'last_error_category',
        )),
        *(('organizational_memory_idempotency', name) for name in (
            'status', 'result_schema_version', 'safe_result', 'updated_at',
            'completed_at',
        )),
    }


@pytest.mark.parametrize("statement", [
    "CREATE TABLE patch034_runtime_escape(id integer)",
    "ALTER TABLE organizational_memories DISABLE TRIGGER b_organizational_memory_root_guard",
    "DROP FUNCTION organizational_memory_projection_v1_valid(jsonb)",
    "DELETE FROM organizational_memories WHERE false",
    "SELECT organizational_memory_canonical_json('{}'::jsonb)",
])
def test_runtime_cannot_ddl_disable_guards_delete_or_execute_functions(statement: str) -> None:
    runtime = _runtime_engine()
    try:
        with pytest.raises(DBAPIError), runtime.begin() as connection:
            connection.exec_driver_sql(statement)
    finally:
        runtime.dispose()


def test_coincident_role_configuration_fails_closed() -> None:
    with pytest.raises(RuntimeError, match="must be distinct"):
        validate_organizational_memory_runtime_boundary(
            owner_engine,
            migration_role_name=owner_engine.url.username,
            require_objects=False,
        )


def test_runtime_verifier_fails_on_trigger_binding_or_enabled_state_drift() -> None:
    runtime = _runtime_engine()
    try:
        with owner_engine.begin() as connection:
            connection.exec_driver_sql(
                "ALTER TABLE organizational_memories DISABLE TRIGGER "
                "b_organizational_memory_root_guard"
            )
        with pytest.raises(RuntimeError, match="guard enforcement is unsafe"):
            validate_organizational_memory_runtime_boundary(
                runtime, migration_role_name=owner_engine.url.username,
            )
    finally:
        with owner_engine.begin() as connection:
            connection.exec_driver_sql(
                "ALTER TABLE organizational_memories ENABLE TRIGGER "
                "b_organizational_memory_root_guard"
            )
        runtime.dispose()


def test_runtime_verifier_fails_on_exact_function_grant_drift() -> None:
    runtime = _runtime_engine()
    signature = "organizational_memory_projection_v1_valid(jsonb)"
    try:
        with owner_engine.begin() as connection:
            connection.exec_driver_sql(
                f"GRANT EXECUTE ON FUNCTION {signature} TO satco_runtime"
            )
        with pytest.raises(RuntimeError, match="guard enforcement is unsafe"):
            validate_organizational_memory_runtime_boundary(
                runtime, migration_role_name=owner_engine.url.username,
            )
    finally:
        with owner_engine.begin() as connection:
            connection.exec_driver_sql(
                f"REVOKE EXECUTE ON FUNCTION {signature} FROM satco_runtime"
            )
        runtime.dispose()
