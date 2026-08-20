from pathlib import Path

from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text

from conftest import TEST_DATABASE_REVISION, alembic_config, engine


def test_patch_041_is_sole_head_with_expected_parent():
    script = ScriptDirectory.from_config(alembic_config)
    assert script.get_heads() == ["e04100000001"]
    assert script.get_revision("e04100000001").down_revision == "e03800000001"
    assert TEST_DATABASE_REVISION == "e04100000001"


def test_patch_041_schema_and_legacy_backfill_are_present():
    schema = inspect(engine)
    assert {"account_action_credentials", "onboarding_idempotency"} <= set(schema.get_table_names())
    assert {"name", "slug"} <= {column["name"] for column in schema.get_columns("organizations")}
    assert {"activation_pending", "auth_version", "version"} <= {
        column["name"] for column in schema.get_columns("users")
    }
    with engine.connect() as connection:
        row = connection.execute(
            text("SELECT name, slug FROM organizations WHERE id=:id"),
            {"id": "7e7c9d7a-7693-4f75-9bc5-3ef7bf528281"},
        ).mappings().one_or_none()
        if row:
            assert row == {"name": "SATCO Engineering", "slug": "satco-engineering"}


def test_migration_contains_runtime_grant_and_no_plaintext_secret_column():
    migration = Path("migrations/versions/e04100000001_first_customer_onboarding.py").read_text()
    assert "satco_runtime" in migration
    assert "token_digest" in migration
    assert "token_plaintext" not in migration
