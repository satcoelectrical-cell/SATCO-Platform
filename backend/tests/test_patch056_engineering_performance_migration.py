"""PATCH-056 Engineering Performance derived-persistence migration qualification."""

from datetime import datetime, timezone
from alembic import command
import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from uuid import uuid4

from conftest import TEST_DATABASE_REVISION, alembic_config, owner_engine

PATCH_055_HEAD = "e05500000002"
PATCH_056_HEAD = "e05600000008"
TABLES = {"engineering_performance_snapshots", "engineering_next_action_projections"}


@pytest.fixture
def derived_scope():
    """A disposable canonical scope, rolled back after real PostgreSQL inserts."""
    connection = owner_engine.connect()
    transaction = connection.begin()
    try:
        organization_id = uuid4()
        project_id = -int(uuid4().int % 100000000 + 10000)
        user_id = project_id
        customer_id = project_id
        workspaces = (project_id, project_id - 1)
        connection.execute(text("INSERT INTO organizations (id, name, slug) VALUES (:id, 'P056 uniqueness probe', :slug)"), {"id": organization_id, "slug": f"p056-{organization_id.hex[:12]}"})
        connection.execute(text("INSERT INTO users (id, email, username, hashed_password, role) VALUES (:id, :email, :username, 'test', 'engineer')"), {"id": user_id, "email": f"p056-{abs(user_id)}@example.invalid", "username": f"p056-{abs(user_id)}"})
        connection.execute(text("INSERT INTO customers (id, name, organization_id) VALUES (:id, 'P056 uniqueness probe', :org)"), {"id": customer_id, "org": organization_id})
        connection.execute(text("""INSERT INTO projects (id, name, status, created_at, customer_id, project_code, priority, progress, organization_id)
            VALUES (:id, 'P056 uniqueness probe', 'new', now(), :customer, :code, 'medium', 0, :org)"""), {"id": project_id, "customer": customer_id, "code": f"SAT-PRJ-2026-{abs(project_id)}", "org": organization_id})
        for workspace_id, discipline in zip(workspaces, ("electrical", "mechanical")):
            connection.execute(text("""INSERT INTO engineering_workspaces
                (id, project_id, discipline, owner_id, created_by_id, canonical_discipline_id, package_binding_state)
                VALUES (:id, :project, :discipline, :actor, :actor, :discipline, 'FUTURE_UNAVAILABLE_UNBOUND')"""), {"id": workspace_id, "project": project_id, "discipline": discipline, "actor": user_id})
        yield connection, organization_id, project_id, workspaces
    finally:
        transaction.rollback()
        connection.close()


def _revision():
    with owner_engine.connect() as connection:
        return connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()


def _truncate():
    with owner_engine.begin() as connection:
        connection.exec_driver_sql(
            "TRUNCATE TABLE engineering_next_action_projections, engineering_performance_snapshots CASCADE"
        )


def test_p056_dat_01_repository_head_and_exact_tables():
    command.upgrade(alembic_config, PATCH_056_HEAD)
    assert TEST_DATABASE_REVISION == PATCH_056_HEAD
    assert _revision() == PATCH_056_HEAD
    tables = set(inspect(owner_engine).get_table_names())
    assert TABLES <= tables


def test_p056_dat_02_snapshot_contract_constraints_and_unique_identity():
    schema = inspect(owner_engine)
    columns = {c["name"] for c in schema.get_columns("engineering_performance_snapshots")}
    assert columns == {
        "id", "organization_id", "project_id", "workspace_id", "actor_id", "indicator_id",
        "indicator_version", "window_start", "window_end", "observed_at",
        "source_cutoff", "source_digest", "source_handles_json",
        "recomputation_reason", "calculation_version",
        "observation_state", "value_json", "limitation_codes_json",
        "eligible_count", "numerator", "denominator", "created_at",
    }
    uniques = {u["name"] for u in schema.get_unique_constraints("engineering_performance_snapshots")}
    checks = {c["name"] for c in schema.get_check_constraints("engineering_performance_snapshots")}
    assert "uq_eng_perf_snapshot_repro" in uniques
    assert {"ck_eng_perf_snapshot_state", "ck_eng_perf_snapshot_window", "ck_eng_perf_snapshot_eligible"} <= checks


def test_p056_dat_03_next_action_contract_constraints_and_unique_identity():
    schema = inspect(owner_engine)
    columns = {c["name"] for c in schema.get_columns("engineering_next_action_projections")}
    assert columns == {
        "id", "organization_id", "project_id", "workspace_id", "actor_id", "action_key",
        "rule_id", "rule_version", "title_code", "rationale_codes_json",
        "supporting_handle_json", "limitation_codes_json", "first_seen_at",
        "last_seen_at", "absent_recalculation_count", "status",
        "superseded_by_action_key", "source_digest", "calculation_version",
        "updated_at",
    }
    uniques = {u["name"] for u in schema.get_unique_constraints("engineering_next_action_projections")}
    checks = {c["name"] for c in schema.get_check_constraints("engineering_next_action_projections")}
    assert "uq_eng_next_action_scope_key" in uniques
    assert {"ck_eng_next_action_status", "ck_eng_next_action_absent_count", "ck_eng_next_action_seen_order"} <= checks


def test_p056_dat_04_empty_downgrade_and_reupgrade_are_safe():
    command.upgrade(alembic_config, PATCH_056_HEAD)
    _truncate()
    command.downgrade(alembic_config, PATCH_055_HEAD)
    assert _revision() == PATCH_055_HEAD
    assert TABLES.isdisjoint(set(inspect(owner_engine).get_table_names()))
    command.upgrade(alembic_config, PATCH_056_HEAD)
    assert _revision() == PATCH_056_HEAD
    assert TABLES <= set(inspect(owner_engine).get_table_names())


def test_p056_project_and_workspace_snapshot_idempotency_on_postgresql(derived_scope):
    connection, organization_id, project_id, workspaces = derived_scope
    statement = text("""INSERT INTO engineering_performance_snapshots
        (id, organization_id, project_id, workspace_id, indicator_id, indicator_version,
         window_start, window_end, observed_at, source_cutoff, source_digest,
         calculation_version, observation_state, value_json, limitation_codes_json)
        VALUES (:id, :org, :project, :workspace, 'required_input_readiness', '1',
                '2026-09-01T00:00:00Z', '2026-09-08T00:00:00Z', now(), now(),
                'probe-digest', '1', 'complete', '{}'::jsonb, '[]'::jsonb)""")
    def insert(workspace_id):
        connection.execute(statement, {"id": uuid4(), "org": organization_id, "project": project_id, "workspace": workspace_id})

    insert(None)
    with pytest.raises(IntegrityError), connection.begin_nested():
        insert(None)
    insert(workspaces[0])
    with pytest.raises(IntegrityError), connection.begin_nested():
        insert(workspaces[0])
    insert(workspaces[1])


def test_p056_project_and_workspace_action_idempotency_on_postgresql(derived_scope):
    connection, organization_id, project_id, workspaces = derived_scope
    statement = text("""INSERT INTO engineering_next_action_projections
        (id, organization_id, project_id, workspace_id, action_key, rule_id, rule_version,
         title_code, rationale_codes_json, supporting_handle_json, limitation_codes_json,
         first_seen_at, last_seen_at, status, source_digest, calculation_version)
        VALUES (:id, :org, :project, :workspace, 'probe-action', 'probe-rule', '1',
                'probe', '[]'::jsonb, '[]'::jsonb, '[]'::jsonb, now(), now(),
                'active', 'probe-digest', '1')""")
    def insert(workspace_id):
        connection.execute(statement, {"id": uuid4(), "org": organization_id, "project": project_id, "workspace": workspace_id})

    insert(None)
    with pytest.raises(IntegrityError), connection.begin_nested():
        insert(None)
    insert(workspaces[0])
    with pytest.raises(IntegrityError), connection.begin_nested():
        insert(workspaces[0])
    insert(workspaces[1])


def test_evidence_availability_snapshot_schema_and_guard(derived_scope):
    schema = inspect(owner_engine)
    assert {"supporting_file_availability_snapshots",
            "evidence_availability_snapshot_items"} <= set(schema.get_table_names())
    observation_columns = {
        column["name"] for column in
        schema.get_columns("supporting_file_availability_observations")
    }
    assert {"snapshot_id", "checked_at"} <= observation_columns
    snapshot_columns = {
        column["name"] for column in
        schema.get_columns("supporting_file_availability_snapshots")
    }
    assert snapshot_columns == {
        "id", "organization_id", "project_id", "workspace_id", "actor_id",
        "source_cutoff", "status", "method_version", "limitation_codes",
        "completed_at", "created_at",
    }
    connection, organization_id, project_id, _ = derived_scope
    snapshot_id = uuid4()
    statement = text("""INSERT INTO supporting_file_availability_snapshots
        (id, organization_id, project_id, actor_id, source_cutoff, status,
         method_version, limitation_codes, completed_at)
        VALUES (:id, :org, :project, :actor, now(), :status,
                'evidence-availability.v1', '[]'::jsonb, :completed)""")
    with pytest.raises(DBAPIError), connection.begin_nested():
        connection.execute(statement, {
            "id": uuid4(), "org": organization_id, "project": project_id,
            "actor": project_id, "status": "complete", "completed": datetime.now(timezone.utc),
        })
    connection.execute(statement, {
        "id": snapshot_id, "org": organization_id, "project": project_id,
        "actor": project_id, "status": "incomplete", "completed": None,
    })
    with pytest.raises(DBAPIError), connection.begin_nested():
        connection.execute(text("""UPDATE supporting_file_availability_snapshots
            SET source_cutoff = source_cutoff + interval '1 second' WHERE id=:id"""),
                           {"id": snapshot_id})
    connection.execute(text("""UPDATE supporting_file_availability_snapshots
        SET status='complete', completed_at=now() WHERE id=:id"""), {"id": snapshot_id})
