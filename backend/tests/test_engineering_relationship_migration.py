from sqlalchemy import inspect, text

from app.core.database import engine
from tests.conftest import TEST_DATABASE_REVISION, owner_engine


def test_relationship_migration_schema_matches_contract():
    inspector = inspect(engine)
    assert {
        "engineering_relationships",
        "engineering_relationship_outbox",
        "engineering_relationship_idempotency",
    } <= set(inspector.get_table_names())
    columns = {
        item["name"] for item in inspector.get_columns("engineering_relationships")
    }
    assert "confidentiality" not in columns
    assert columns == {
        "id", "organization_id", "project_id", "workspace_id",
        "source_object_id", "target_object_id", "relationship_family",
        "relationship_type", "lifecycle", "authority_standing",
        "evidence_references", "version", "creator_id", "steward_id",
        "reviewer_id", "approver_id", "created_at", "updated_at",
    }
    indexes = {
        item["name"] for item in inspector.get_indexes("engineering_relationships")
    }
    assert "uq_engineering_relationships_active_identity" in indexes
    with owner_engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == TEST_DATABASE_REVISION
        )
