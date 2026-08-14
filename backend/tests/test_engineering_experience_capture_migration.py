from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text

from app.core.database import engine
from tests.conftest import TEST_DATABASE_REVISION, alembic_config, owner_engine


def test_capture_revision_is_repository_head():
    assert ScriptDirectory.from_config(alembic_config).get_current_head() == TEST_DATABASE_REVISION
    with owner_engine.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == TEST_DATABASE_REVISION


def test_capture_migration_has_exact_tables_constraints_and_indexes():
    inspector = inspect(engine)
    assert {"engineering_experience_captures", "engineering_experience_capture_outbox",
            "engineering_experience_capture_idempotency"} <= set(inspector.get_table_names())
    checks = {item["name"] for item in inspector.get_check_constraints("engineering_experience_captures")}
    assert "ck_experience_captures_supersession_state" in checks
    indexes = {item["name"] for item in inspector.get_indexes("engineering_experience_captures")}
    assert {"ix_experience_captures_project_order", "ix_experience_captures_workspace_order",
            "uq_experience_captures_replacement"} <= indexes
    foreign_targets = {item["referred_table"] for item in inspector.get_foreign_keys("engineering_experience_captures")}
    assert {"organizations", "projects", "engineering_workspaces", "engineering_objects", "users",
            "engineering_experience_captures"} <= foreign_targets
