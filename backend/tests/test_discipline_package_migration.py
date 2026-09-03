import importlib.util
import json
import os
from pathlib import Path
from uuid import uuid4

import pytest
import sqlalchemy as sa
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from sqlalchemy.dialects import postgresql


ROOT = Path(__file__).resolve().parents[1]


def test_batch_three_foundation_migrations_preserve_authorized_topology():
    m1 = (ROOT / "migrations/versions/e05100000001_registry_configuration_audit.py").read_text()
    m2 = (ROOT / "migrations/versions/e05100000002_workspace_binding_shadow.py").read_text()
    assert 'down_revision = "e04700000001"' in m1
    assert 'down_revision = "e05100000001"' in m2
    m3 = (ROOT / "migrations/versions/e05100000003_workspace_binding_cutover.py").read_text()
    assert 'down_revision = "e05100000002"' in m3
    assert "satco_dp_workspace_binding_guard" in m3
    assert "satco_dp_project_head_binding_guard" in m3
    assert m1.count("op.create_table(") == 12


def test_corrective_m4_is_the_sole_audit_time_correlation_successor():
    m4 = (ROOT / "migrations/versions/e05100000004_audit_time_correlation.py").read_text()
    assert 'revision = "e05100000004"' in m4
    assert 'down_revision = "e05100000003"' in m4
    assert "correlation_id = CASE" in m4
    assert "~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'" in m4
    assert "trg_dp_audit_current_insert_guard" in m4
    assert "ix_dp_audit_organization_occurred_event" in m4
    assert "ix_dp_audit_organization_project_occurred_event" in m4


def test_corrective_m5_is_the_sole_nulls_last_successor():
    m5 = (ROOT / "migrations/versions/e05100000005_audit_nulls_last_indexes.py").read_text()
    assert 'revision = "e05100000005"' in m5
    assert 'down_revision = "e05100000004"' in m5
    assert "occurred_at DESC NULLS LAST, event_id DESC" in m5
    assert "project_id, occurred_at DESC NULLS LAST, event_id DESC" in m5


def test_corrective_m6_is_the_sole_registry_standing_successor():
    m6 = (ROOT / "migrations/versions/e05100000006_registry_membership_standing.py").read_text()
    assert 'revision = "e05100000006"' in m6
    assert 'down_revision = "e05100000005"' in m6
    assert "ix_dp_membership_release_standing" in m6
    assert 'op.drop_column(_DESCRIPTOR_TABLE, "standing")' in m6
    assert "No data backfill" not in m6


def _m4_module():
    path = ROOT / "migrations/versions/e05100000004_audit_time_correlation.py"
    spec = importlib.util.spec_from_file_location("patch051_m4", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _m5_module():
    path = ROOT / "migrations/versions/e05100000005_audit_nulls_last_indexes.py"
    spec = importlib.util.spec_from_file_location("patch051_m5", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _m6_module():
    path = ROOT / "migrations/versions/e05100000006_registry_membership_standing.py"
    spec = importlib.util.spec_from_file_location("patch051_m6", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _create_minimal_m5_registry_schema(connection) -> None:
    connection.execute(sa.text("""
CREATE TABLE discipline_package_registry_releases (id integer);
CREATE TABLE discipline_package_descriptors (
  package_key varchar(64) PRIMARY KEY,
  package_version varchar(32) NOT NULL,
  descriptor_digest varchar(64) NOT NULL,
  primary_discipline_id varchar(64) NOT NULL,
  adapter_id varchar(128) NOT NULL,
  standing varchar(40) NOT NULL,
  descriptor_json jsonb NOT NULL
);
CREATE TABLE discipline_package_registry_memberships (
  registry_digest varchar(64) NOT NULL,
  package_key varchar(64) NOT NULL,
  package_version varchar(32) NOT NULL,
  standing varchar(40) NOT NULL,
  CONSTRAINT ck_dp_membership_standing
    CHECK (standing IN ('executable_supported','historical_read_only'))
);
CREATE FUNCTION satco_dp_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'PATCH-051 immutable Registry provenance';
END $$;
CREATE TRIGGER trg_dp_memberships_immutable
BEFORE UPDATE OR DELETE ON discipline_package_registry_memberships
FOR EACH ROW EXECUTE FUNCTION satco_dp_immutable();
CREATE TABLE discipline_package_compatibility_profiles (id integer);
CREATE TABLE discipline_package_registry_profile_memberships (id integer);
CREATE TABLE discipline_package_compatibility_members (id integer);
CREATE TABLE organization_package_configuration_heads (id integer);
CREATE TABLE organization_package_selections (id integer);
CREATE TABLE project_package_configuration_revisions (id integer);
CREATE TABLE project_package_configuration_selections (id integer);
CREATE TABLE project_package_configuration_heads (id integer);
CREATE TABLE package_configuration_audit_events (id integer);
CREATE TABLE engineering_workspaces (
  id integer,
  bound_package_key varchar(64),
  bound_project_configuration_revision bigint
);
"""))


def _m6_descriptor_has_standing(connection) -> bool:
    return connection.execute(sa.text("""
SELECT EXISTS (
  SELECT 1 FROM information_schema.columns
  WHERE table_schema = current_schema()
    AND table_name = 'discipline_package_descriptors'
    AND column_name = 'standing'
)
""")).scalar_one()


def _m6_membership_index(connection) -> str | None:
    return connection.execute(sa.text("""
SELECT indexdef FROM pg_indexes
WHERE schemaname = current_schema()
  AND tablename = 'discipline_package_registry_memberships'
  AND indexname = 'ix_dp_membership_release_standing'
""")).scalar_one_or_none()


def test_m6_empty_upgrade_downgrade_and_reupgrade_converge():
    engine = sa.create_engine(os.environ["TEST_DATABASE_URL"], pool_pre_ping=True)
    schema = f"patch051_m6_{uuid4().hex}"
    m6 = _m6_module()
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                connection.execute(sa.text(f'CREATE SCHEMA "{schema}"'))
                connection.execute(sa.text(f'SET LOCAL search_path TO "{schema}", public'))
                _create_minimal_m5_registry_schema(connection)

                _run_migration(connection, m6.upgrade)
                assert not _m6_descriptor_has_standing(connection)
                index_definition = _m6_membership_index(connection)
                assert index_definition is not None
                assert "(registry_digest, standing, package_key, package_version)" in index_definition

                _run_migration(connection, m6.downgrade)
                assert _m6_descriptor_has_standing(connection)
                assert _m6_membership_index(connection) is None

                _run_migration(connection, m6.upgrade)
                assert not _m6_descriptor_has_standing(connection)
                assert _m6_membership_index(connection) == index_definition
            finally:
                transaction.rollback()
    finally:
        engine.dispose()


def test_m6_upgrade_and_downgrade_fail_closed_on_nonempty_state():
    engine = sa.create_engine(os.environ["TEST_DATABASE_URL"], pool_pre_ping=True)
    schema = f"patch051_m6_guard_{uuid4().hex}"
    m6 = _m6_module()
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                connection.execute(sa.text(f'CREATE SCHEMA "{schema}"'))
                connection.execute(sa.text(f'SET LOCAL search_path TO "{schema}", public'))
                _create_minimal_m5_registry_schema(connection)
                connection.execute(sa.text("""
INSERT INTO discipline_package_descriptors
  (package_key, package_version, descriptor_digest, primary_discipline_id,
   adapter_id, standing, descriptor_json)
VALUES ('unsafe_package', '1.0.0', :digest, 'electrical', 'unsafe.adapter',
        'executable_supported', '{}'::jsonb)
"""), {"digest": "a" * 64})
                with pytest.raises(RuntimeError, match="empty, unreferenced"):
                    _run_migration(connection, m6.upgrade)
                assert _m6_descriptor_has_standing(connection)
                assert _m6_membership_index(connection) is None

                connection.execute(sa.text(
                    "DELETE FROM discipline_package_descriptors"
                ))
                _run_migration(connection, m6.upgrade)
                connection.execute(sa.text("""
INSERT INTO discipline_package_descriptors
  (package_key, package_version, descriptor_digest, primary_discipline_id,
   adapter_id, descriptor_json)
VALUES ('post_m6_package', '1.0.0', :digest, 'electrical', 'post.adapter',
        '{}'::jsonb)
"""), {"digest": "b" * 64})
                with pytest.raises(RuntimeError, match="empty, unreferenced"):
                    _run_migration(connection, m6.downgrade)
                assert not _m6_descriptor_has_standing(connection)
                assert _m6_membership_index(connection) is not None
            finally:
                transaction.rollback()
    finally:
        engine.dispose()


def test_m6_refuses_a_membership_table_without_its_immutable_contract():
    engine = sa.create_engine(os.environ["TEST_DATABASE_URL"], pool_pre_ping=True)
    schema = f"patch051_m6_contract_{uuid4().hex}"
    m6 = _m6_module()
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                connection.execute(sa.text(f'CREATE SCHEMA "{schema}"'))
                connection.execute(sa.text(f'SET LOCAL search_path TO "{schema}", public'))
                _create_minimal_m5_registry_schema(connection)
                connection.execute(sa.text(
                    "DROP TRIGGER trg_dp_memberships_immutable ON discipline_package_registry_memberships"
                ))
                with pytest.raises(RuntimeError, match="membership standing contract"):
                    _run_migration(connection, m6.upgrade)
                assert _m6_descriptor_has_standing(connection)
                assert _m6_membership_index(connection) is None
            finally:
                transaction.rollback()
    finally:
        engine.dispose()


def _run_migration(connection, operation):
    context = MigrationContext.configure(connection)
    with Operations.context(context):
        operation()


def test_m3_to_m5_preserves_audit_truth_and_converges_physical_access_paths():
    """Exercise M4/M5 on an isolated M3-shaped PostgreSQL schema.

    The governed test database can contain current, immutable Audit rows from
    other focused vectors, so this test creates and rolls back a separate
    schema.  That preserves the shared test corpus while still executing the
    actual M4 DDL, data conversion, guard, downgrade and re-upgrade paths.
    """
    engine = sa.create_engine(os.environ["TEST_DATABASE_URL"], pool_pre_ping=True)
    schema = f"patch051_m4_{uuid4().hex}"
    organization_id = uuid4()
    actor_id = 910051
    valid_event, malformed_event, absent_event = uuid4(), uuid4(), uuid4()
    valid_correlation = uuid4()
    m4 = _m4_module()
    m5 = _m5_module()

    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                connection.execute(sa.text(f'CREATE SCHEMA "{schema}"'))
                connection.execute(sa.text(f'SET LOCAL search_path TO "{schema}", public'))
                connection.execute(sa.text("""
CREATE TABLE package_configuration_audit_events (
  event_id uuid PRIMARY KEY,
  organization_id uuid NOT NULL,
  project_id integer NULL,
  workspace_id integer NULL,
  actor_user_id integer NOT NULL,
  category varchar(32) NOT NULL,
  action varchar(32) NOT NULL,
  metadata_json jsonb NOT NULL
)
"""))
                connection.execute(sa.text("""
CREATE FUNCTION satco_m4_test_audit_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'PATCH-051 immutable history'; END $$;
CREATE TRIGGER trg_dp_audit_immutable BEFORE UPDATE OR DELETE
ON package_configuration_audit_events FOR EACH ROW
EXECUTE FUNCTION satco_m4_test_audit_immutable();
CREATE INDEX ix_dp_audit_organization
ON package_configuration_audit_events (organization_id);
"""))
                insert_legacy = sa.text(f"""
INSERT INTO "{schema}".package_configuration_audit_events
  (event_id, organization_id, actor_user_id, category, action, metadata_json)
VALUES (:event_id, :organization_id, :actor_user_id, 'ORG_CONFIGURATION',
        'replace', CAST(:metadata AS jsonb))
""")
                for event_id, metadata in (
                    (valid_event, {"correlation_id": str(valid_correlation)}),
                    (malformed_event, {"correlation_id": "not-a-uuid"}),
                    (absent_event, {}),
                ):
                    connection.execute(insert_legacy, {
                        "event_id": event_id,
                        "organization_id": organization_id,
                        "actor_user_id": actor_id,
                        "metadata": json.dumps(metadata),
                    })

                _run_migration(connection, m4.upgrade)
                rows = connection.execute(sa.text("""
SELECT event_id, occurred_at, correlation_id
FROM package_configuration_audit_events ORDER BY event_id
""")).mappings().all()
                by_event = {row["event_id"]: row for row in rows}
                assert all(row["occurred_at"] is None for row in rows)
                assert by_event[valid_event]["correlation_id"] == valid_correlation
                assert by_event[malformed_event]["correlation_id"] is None
                assert by_event[absent_event]["correlation_id"] is None

                # The post-cutover guard rejects new unknown values, but a
                # failed attempted insert must not taint the migration run.
                failed_insert = connection.begin_nested()
                with pytest.raises(sa.exc.DBAPIError, match="current Audit requires"):
                    connection.execute(sa.text("""
INSERT INTO package_configuration_audit_events
  (event_id, organization_id, actor_user_id, category, action, metadata_json,
   occurred_at, correlation_id)
VALUES (:event_id, :organization_id, :actor_user_id, 'ORG_CONFIGURATION',
        'replace', '{}'::jsonb, NULL, NULL)
"""), {
                        "event_id": uuid4(), "organization_id": organization_id,
                        "actor_user_id": actor_id,
                    })
                failed_insert.rollback()

                # Historical-only state supports M4's explicitly safe recovery
                # path before M5 is introduced.
                _run_migration(connection, m4.downgrade)
                columns_after_downgrade = set(connection.execute(sa.text("""
SELECT column_name FROM information_schema.columns
WHERE table_schema = current_schema()
  AND table_name = 'package_configuration_audit_events'
""")).scalars())
                assert {"occurred_at", "correlation_id"}.isdisjoint(columns_after_downgrade)
                _run_migration(connection, m4.upgrade)

                index_definitions = dict(connection.execute(sa.text("""
SELECT indexname, indexdef FROM pg_indexes
WHERE schemaname = current_schema()
  AND tablename = 'package_configuration_audit_events'
""")).all())
                assert "(organization_id, occurred_at DESC, event_id DESC)" in index_definitions[
                    "ix_dp_audit_organization_occurred_event"
                ]
                assert "(organization_id, project_id, occurred_at DESC, event_id DESC)" in index_definitions[
                    "ix_dp_audit_organization_project_occurred_event"
                ]
                assert "NULLS LAST" not in index_definitions[
                    "ix_dp_audit_organization_occurred_event"
                ]

                # Path A: a schema created from the current M4 source starts
                # with implicit DESC NULLS FIRST and converges through M5.
                _run_migration(connection, m5.upgrade)
                index_definitions = dict(connection.execute(sa.text("""
SELECT indexname, indexdef FROM pg_indexes
WHERE schemaname = current_schema()
  AND tablename = 'package_configuration_audit_events'
""")).all())
                assert "(organization_id, occurred_at DESC NULLS LAST, event_id DESC)" in index_definitions[
                    "ix_dp_audit_organization_occurred_event"
                ]
                assert "(organization_id, project_id, occurred_at DESC NULLS LAST, event_id DESC)" in index_definitions[
                    "ix_dp_audit_organization_project_occurred_event"
                ]

                # M5 downgrade restores M4 source physical semantics only;
                # it must not alter the truthful historical rows or M4 guard.
                original_rows = connection.execute(sa.text("""
SELECT event_id, occurred_at, correlation_id, metadata_json
FROM package_configuration_audit_events ORDER BY event_id
""")).mappings().all()
                _run_migration(connection, m5.downgrade)
                index_definitions = dict(connection.execute(sa.text("""
SELECT indexname, indexdef FROM pg_indexes
WHERE schemaname = current_schema()
  AND tablename = 'package_configuration_audit_events'
""")).all())
                assert "NULLS LAST" not in index_definitions[
                    "ix_dp_audit_organization_occurred_event"
                ]
                assert connection.execute(sa.text("""
SELECT event_id, occurred_at, correlation_id, metadata_json
FROM package_configuration_audit_events ORDER BY event_id
""")).mappings().all() == original_rows

                _run_migration(connection, m5.upgrade)

                # Path B: an already NULLS LAST M4 installation also converges
                # when M5 drops/recreates the named physical access paths.
                _run_migration(connection, m5.downgrade)
                connection.execute(sa.text("""
DROP INDEX ix_dp_audit_organization_project_occurred_event;
DROP INDEX ix_dp_audit_organization_occurred_event;
CREATE INDEX ix_dp_audit_organization_occurred_event
ON package_configuration_audit_events
(organization_id, occurred_at DESC NULLS LAST, event_id DESC);
CREATE INDEX ix_dp_audit_organization_project_occurred_event
ON package_configuration_audit_events
(organization_id, project_id, occurred_at DESC NULLS LAST, event_id DESC);
"""))
                _run_migration(connection, m5.upgrade)
                index_definitions = dict(connection.execute(sa.text("""
SELECT indexname, indexdef FROM pg_indexes
WHERE schemaname = current_schema()
  AND tablename = 'package_configuration_audit_events'
""")).all())
                assert "NULLS LAST" in index_definitions[
                    "ix_dp_audit_organization_occurred_event"
                ]
                assert "NULLS LAST" in index_definitions[
                    "ix_dp_audit_organization_project_occurred_event"
                ]
                assert connection.execute(sa.text("""
SELECT event_id, occurred_at, correlation_id, metadata_json
FROM package_configuration_audit_events ORDER BY event_id
""")).mappings().all() == original_rows

                # Existing Audit rows remain append-only after the M4/M5
                # physical-index transitions.
                failed_update = connection.begin_nested()
                with pytest.raises(sa.exc.DBAPIError, match="immutable history"):
                    connection.execute(sa.text("""
UPDATE package_configuration_audit_events
SET action = 'changed' WHERE event_id = :event_id
"""), {"event_id": valid_event})
                failed_update.rollback()
            finally:
                transaction.rollback()
    finally:
        engine.dispose()


def test_m5_indexes_provide_analyzed_known_time_access_paths():
    """Prove both M5 paths on a bounded committed disposable schema.

    Committing then vacuuming the disposable corpus permits PostgreSQL to
    consider the production-shaped index-only page access that a rollback-only
    fixture cannot represent.  The schema is dropped in ``finally``.
    """
    engine = sa.create_engine(os.environ["TEST_DATABASE_URL"], pool_pre_ping=True)
    schema = f"patch051_m5_plan_{uuid4().hex}"
    organization_id = uuid4()
    m5 = _m5_module()
    try:
        with engine.begin() as connection:
            connection.execute(sa.text(f'CREATE SCHEMA "{schema}"'))
            connection.execute(sa.text(f'SET LOCAL search_path TO "{schema}", public'))
            connection.execute(sa.text("""
CREATE TABLE package_configuration_audit_events (
  event_id uuid PRIMARY KEY,
  organization_id uuid NOT NULL,
  project_id integer NULL,
  actor_user_id integer NOT NULL,
  category varchar(32) NOT NULL,
  action varchar(32) NOT NULL,
  metadata_json jsonb NOT NULL,
  occurred_at timestamptz NULL,
  correlation_id uuid NULL
);
CREATE INDEX ix_dp_audit_organization_occurred_event
ON package_configuration_audit_events
(organization_id, occurred_at DESC, event_id DESC);
CREATE INDEX ix_dp_audit_organization_project_occurred_event
ON package_configuration_audit_events
(organization_id, project_id, occurred_at DESC, event_id DESC);
"""))
            _run_migration(connection, m5.upgrade)
            connection.execute(sa.text("""
INSERT INTO package_configuration_audit_events
  (event_id, organization_id, project_id, actor_user_id, category, action,
   metadata_json, occurred_at, correlation_id)
SELECT md5('m5-target-' || value::text)::uuid, :organization_id,
       CASE WHEN value <= 50 THEN 1 ELSE 2 END, 910051,
       'PROJECT_CONFIGURATION', 'replace', '{}'::jsonb,
       now() - (value * interval '1 second'), :correlation_id
FROM generate_series(1, 100) AS value;
"""), {"organization_id": organization_id, "correlation_id": uuid4()})
            connection.execute(sa.text("""
INSERT INTO package_configuration_audit_events
  (event_id, organization_id, project_id, actor_user_id, category, action,
   metadata_json, occurred_at, correlation_id)
SELECT md5('m5-other-' || value::text)::uuid,
       md5('m5-other-org-' || (value % 10000)::text)::uuid,
       10000 + (value % 100), 910051,
       'PROJECT_CONFIGURATION', 'replace', '{}'::jsonb,
       now() - (value * interval '1 second'), :correlation_id
FROM generate_series(1, 200000) AS value;
"""), {"correlation_id": uuid4()})

        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.exec_driver_sql(f'VACUUM (ANALYZE) "{schema}".package_configuration_audit_events')

        with engine.connect() as connection:
            organization_plan = "\n".join(connection.execute(sa.text(f"""
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF)
SELECT event_id FROM "{schema}".package_configuration_audit_events
WHERE organization_id = :organization_id AND occurred_at IS NOT NULL
ORDER BY occurred_at DESC NULLS LAST, event_id DESC LIMIT 100
"""), {"organization_id": organization_id}).scalars())
            assert "ix_dp_audit_organization_occurred_event" in organization_plan
            assert "Sort" not in organization_plan

            project_plan = "\n".join(connection.execute(sa.text(f"""
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF)
SELECT event_id FROM "{schema}".package_configuration_audit_events
WHERE organization_id = :organization_id
  AND project_id = :project_id
  AND occurred_at IS NOT NULL
ORDER BY occurred_at DESC NULLS LAST, event_id DESC LIMIT 50
"""), {"organization_id": organization_id, "project_id": 1}).scalars())
            assert "ix_dp_audit_organization_project_occurred_event" in project_plan
            assert "Sort" not in project_plan
    finally:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        engine.dispose()


def test_m2_is_nullable_additive_and_not_valid():
    source = (ROOT / "migrations/versions/e05100000002_workspace_binding_shadow.py").read_text()
    assert "postgresql_not_valid=True" in source
    assert "backfill" not in source.lower()
    assert "OPERATIONAL_PACKAGE_BOUND" in source
