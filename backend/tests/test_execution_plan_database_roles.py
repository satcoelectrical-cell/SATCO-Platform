from pathlib import Path


def test_runtime_role_is_denied_schema_object_ownership_and_history_mutation():
    source = Path("migrations/versions/e04500000001_engineering_execution_plan.py").read_text()
    assert "ALTER TABLE engineering_execution_plans OWNER TO satco" in source
    assert "REVOKE ALL ON FUNCTION" in source
    assert "TG_OP <> 'INSERT'" in source
    assert "GRANT SELECT,INSERT ON engineering_execution_plan_revisions" in source
