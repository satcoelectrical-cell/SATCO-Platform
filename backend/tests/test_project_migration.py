from sqlalchemy import inspect

from app.core.database import engine


def test_project_core_database_contract():
    inspector = inspect(engine)
    columns = {
        column["name"]: column
        for column in inspector.get_columns("projects")
    }
    expected_columns = {
        "project_code",
        "description",
        "priority",
        "owner_id",
        "primary_assignee_id",
        "start_date",
        "target_completion_date",
        "completed_at",
        "progress",
        "updated_at",
    }
    assert expected_columns <= columns.keys()
    assert columns["project_code"]["nullable"] is False
    assert columns["status"]["nullable"] is False

    unique_constraints = inspector.get_unique_constraints(
        "projects"
    )
    assert any(
        constraint["column_names"] == ["project_code"]
        for constraint in unique_constraints
    )

    indexes = inspector.get_indexes("projects")
    indexed_columns = {
        tuple(index["column_names"])
        for index in indexes
    }
    for column in (
        "customer_id",
        "status",
        "priority",
        "owner_id",
        "primary_assignee_id",
        "start_date",
        "target_completion_date",
    ):
        assert (column,) in indexed_columns

    foreign_keys = inspector.get_foreign_keys("projects")
    constrained_columns = {
        tuple(foreign_key["constrained_columns"])
        for foreign_key in foreign_keys
    }
    assert ("customer_id",) in constrained_columns
    assert ("owner_id",) in constrained_columns
    assert ("primary_assignee_id",) in constrained_columns

    assert "project_code_sequences" in (
        inspector.get_table_names()
    )
