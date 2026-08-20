"""PATCH-032 Batch 2 migration structure and rollback evidence."""

from alembic import command
from sqlalchemy import inspect, text

from conftest import TEST_DATABASE_REVISION, alembic_config, owner_engine


EXPECTED_TABLES = {
    "technical_reports",
    "technical_report_provenance_entries",
    "technical_report_outbox",
    "technical_report_idempotency",
}


def test_repository_head_is_patch_032() -> None:
    assert TEST_DATABASE_REVISION == "e03800000001"


def test_technical_report_schema_matches_authorized_persistence() -> None:
    inspector = inspect(owner_engine)
    assert EXPECTED_TABLES <= set(inspector.get_table_names())
    root_columns = {column["name"] for column in inspector.get_columns("technical_reports")}
    assert {
        "id", "organization_id", "workspace_id", "project_id", "owner_id",
        "purpose", "engineering_scope", "draft_content", "assumptions",
        "uncertainty", "limitations", "conclusions", "recommendations",
        "is_preliminary", "evidence_deficiencies", "unresolved_issues",
        "follow_up_requirements", "draft_revision_id", "draft_revision_number",
        "lifecycle", "predecessor_report_id", "version", "accepted_snapshot",
        "accepted_snapshot_digest", "accepted_by_id", "accepted_at",
        "accepted_draft_revision_id", "accepted_aggregate_version", "created_at",
        "updated_at",
    } == root_columns
    provenance_columns = {
        column["name"] for column in inspector.get_columns("technical_report_provenance_entries")
    }
    assert {"source_class", "source_type", "owning_capability", "capture_id", "evidence_id", "engineering_object_id", "engineering_relationship_id", "report_local_source_id", "standard_identity", "context_id", "minimal_historical_representation", "integrity_digest"} <= provenance_columns
    assert {"event_id", "aggregate_id", "aggregate_version", "payload"} <= {
        column["name"] for column in inspector.get_columns("technical_report_outbox")
    }
    assert {"organization_id", "actor_id", "idempotency_id", "request_fingerprint", "status", "result"} <= {
        column["name"] for column in inspector.get_columns("technical_report_idempotency")
    }

    constraints = {item["name"] for item in inspector.get_check_constraints("technical_reports")}
    assert {"ck_technical_reports_lifecycle", "ck_technical_reports_purpose", "ck_technical_reports_acceptance_coherence", "ck_technical_reports_version"} <= constraints
    indexes = {item["name"] for item in inspector.get_indexes("technical_reports")}
    assert {"ix_technical_reports_workspace_order", "ix_technical_reports_project_order", "ix_technical_reports_owner_lifecycle", "ix_technical_reports_predecessor"} <= indexes

    with owner_engine.connect() as connection:
        trigger_names = set(connection.execute(text("SELECT tgname FROM pg_trigger WHERE tgname LIKE 'trg_technical_report%' AND NOT tgisinternal")).scalars())
        function_names = set(connection.execute(text(
            "SELECT proname FROM pg_proc WHERE proname IN "
            "('technical_report_canonical_json','technical_report_canonical_utc_valid',"
            "'technical_report_text_valid','technical_report_historical_basis_valid',"
            "'technical_report_provenance_json_valid','technical_report_root_accepted_immutable',"
            "'technical_report_provenance_accepted_immutable')"
        )).scalars())
    assert trigger_names == {"trg_technical_reports_accepted_immutable", "trg_technical_report_provenance_accepted_immutable"}
    assert function_names == {
        "technical_report_canonical_json", "technical_report_canonical_utc_valid",
        "technical_report_text_valid", "technical_report_historical_basis_valid",
        "technical_report_provenance_json_valid", "technical_report_root_accepted_immutable",
        "technical_report_provenance_accepted_immutable",
    }
    provenance_constraints = {item["name"] for item in inspector.get_check_constraints("technical_report_provenance_entries")}
    assert {
        "ck_technical_report_provenance_digest_format",
        "ck_technical_report_provenance_historical_basis",
    } <= provenance_constraints
    assert "ck_technical_reports_snapshot_digest" in constraints


def test_patch_032_downgrade_and_upgrade_restore_head() -> None:
    try:
        command.downgrade(alembic_config, "e02800000001")
        assert not (EXPECTED_TABLES & set(inspect(owner_engine).get_table_names()))
    finally:
        command.upgrade(alembic_config, TEST_DATABASE_REVISION)
    with owner_engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == TEST_DATABASE_REVISION
        )
