from pathlib import Path

from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text

from conftest import TEST_DATABASE_REVISION, alembic_config, owner_engine


TABLES = {
    "project_foundations", "project_scope_items", "project_completion_criteria",
    "project_required_inputs", "project_stage_history",
}


def test_patch_044_is_sole_head_and_preserves_patch_043_parent():
    script = ScriptDirectory.from_config(alembic_config)
    assert script.get_heads() == ["e04500000001"]
    assert script.get_revision("e04400000001").down_revision == "e04300000001"
    assert TEST_DATABASE_REVISION == "e04500000001"


def test_project_foundation_schema_matrix_and_no_legacy_backfill():
    inspector = inspect(owner_engine)
    assert TABLES <= set(inspector.get_table_names())
    assert {column["name"] for column in inspector.get_columns("project_foundations")} == {
        "project_id", "organization_id", "purpose", "engineering_basis", "stage", "version",
        "established_by_id", "established_at", "updated_by_id", "updated_at",
    }
    assert {item["name"] for item in inspector.get_check_constraints("project_required_inputs")} >= {
        "ck_project_input_title", "ck_project_input_required_stage", "ck_project_input_standing",
        "ck_project_input_source_pair", "ck_project_input_version",
    }
    with owner_engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM project_foundations")).scalar_one() == 0
        functions = set(connection.execute(text(
            "SELECT proname FROM pg_proc WHERE proname LIKE 'satco_project_%_guard'"
        )).scalars())
        triggers = set(connection.execute(text(
            "SELECT tgname FROM pg_trigger WHERE tgname LIKE 'trg_project_%_guard' AND NOT tgisinternal"
        )).scalars())
    assert {"satco_project_foundation_parent_guard", "satco_project_foundation_child_guard", "satco_project_input_guard", "satco_project_stage_history_guard"} <= functions
    assert {"trg_project_foundation_parent_guard", "trg_project_input_guard", "trg_project_stage_history_guard"} <= triggers


def test_migration_contains_exact_role_and_immutable_history_contract():
    source = Path("migrations/versions/e04400000001_project_foundation.py").read_text()
    for required in (
        "OWNER TO satco", "TO satco_runtime", "project stage history is immutable",
        "project input source binding mismatch", "e04300000001",
    ):
        assert required in source
    assert "DELETE ON project_scope_items, project_completion_criteria" in source
    assert "GRANT SELECT, INSERT, UPDATE, DELETE ON project_stage_history" not in source
    assert "GRANT SELECT, INSERT ON project_stage_history TO satco_runtime" in source
