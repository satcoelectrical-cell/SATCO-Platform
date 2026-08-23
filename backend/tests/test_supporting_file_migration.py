from pathlib import Path
from alembic.script import ScriptDirectory
from sqlalchemy import inspect
from conftest import TEST_DATABASE_REVISION, alembic_config
from conftest import owner_engine


def test_supporting_file_history_is_preserved_under_patch_044_head():
    script = ScriptDirectory.from_config(alembic_config)
    assert script.get_heads() == ["e04400000001"]
    assert script.get_revision("e04300000001").down_revision == "e04100000001"
    assert TEST_DATABASE_REVISION == "e04400000001"


def test_migration_contains_immutable_key_and_link_seal_guards():
    migration = Path("migrations/versions/e04300000001_supporting_files.py").read_text()
    for value in ("objects/[0-9a-f]{64}", "satco_guard_supporting_file_asset", "satco_seal_evidence_file_links", "supporting_file_links_sealed_at"):
        assert value in migration


def test_supporting_file_scan_attempt_idempotency_and_outbox_persistence_are_present_and_closed():
    inspector = inspect(owner_engine)
    assert {"supporting_file_scan_attempts", "supporting_file_outbox", "supporting_file_idempotency"} <= set(inspector.get_table_names())
    idempotency = {column["name"]: column for column in inspector.get_columns("supporting_file_idempotency")}
    outbox = {column["name"]: column for column in inspector.get_columns("supporting_file_outbox")}
    attempts = {column["name"]: column for column in inspector.get_columns("supporting_file_scan_attempts")}
    assert attempts["asset_id"]["nullable"] is False
    assert attempts["organization_id"]["nullable"] is False
    assert attempts["expected_asset_version"]["nullable"] is False
    assert attempts["attempt_number"]["nullable"] is False
    assert attempts["state"]["nullable"] is False
    assert attempts["requested_at"]["nullable"] is False
    assert attempts["correlation_id"]["nullable"] is True
    assert idempotency["organization_id"]["nullable"] is False
    assert idempotency["actor_id"]["nullable"] is False
    assert idempotency["operation"]["nullable"] is False
    assert idempotency["idempotency_id"]["nullable"] is False
    assert outbox["event_id"]["nullable"] is False
    assert outbox["asset_id"]["nullable"] is False
    assert "uq_supporting_file_idempotency_scope" in {item["name"] for item in inspector.get_unique_constraints("supporting_file_idempotency")}
    assert "uq_supporting_file_scan_attempt_ordinal" in {item["name"] for item in inspector.get_unique_constraints("supporting_file_scan_attempts")}
    assert "uq_supporting_file_scan_attempt_correlation" in {item["name"] for item in inspector.get_unique_constraints("supporting_file_scan_attempts")}
    assert "uq_supporting_file_outbox_event" in {item["name"] for item in inspector.get_unique_constraints("supporting_file_outbox")}
