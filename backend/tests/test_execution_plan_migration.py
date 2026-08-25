from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_patch_045_is_sole_repository_head_and_preserves_patch_044_parent():
    config = Config("alembic.ini")
    config.set_main_option("script_location", "migrations")
    script = ScriptDirectory.from_config(config)
    assert script.get_heads() == ["e04700000001"]
    assert script.get_revision("e04500000001").down_revision == "e04400000001"


def test_execution_migration_contains_required_root_history_dependency_and_role_guards():
    source = Path("migrations/versions/e04500000001_engineering_execution_plan.py").read_text()
    for required in (
        "engineering_execution_plans", "engineering_execution_plan_revisions",
        "engineering_execution_activities", "engineering_execution_activity_history",
        "engineering_execution_milestones", "engineering_execution_dependencies",
        "engineering_execution_idempotency", "satco_execution_dependency_guard",
        "execution dependency cycle", "execution activity history immutable",
        "invalid execution activity transition", "execution activity dependency unsatisfied", "execution activity update requires version increment",
        "execution activity version requires history", "execution plan version requires revision",
        "OWNER TO satco", "satco_runtime",
    ):
        assert required in source
