"""PATCH-034 Batch 2 migration and direct-SQL guard evidence."""

from alembic import command
from alembic.script import ScriptDirectory
import json
import re
from sqlalchemy import inspect, text

from conftest import TEST_DATABASE_REVISION, alembic_config, owner_engine


TABLES = {
    "organizational_memories",
    "organizational_memory_standing_history",
    "organizational_memory_events_outbox",
    "organizational_memory_idempotency",
}
FUNCTIONS = {
    "organizational_memory_projection_v1_valid",
    "organizational_memory_manifest_v1_valid",
    "organizational_memory_event_payload_v1_valid",
    "organizational_memory_idempotency_result_v1_valid",
    "organizational_memory_canonical_json",
    "organizational_memory_lineage_guard",
    "organizational_memory_root_guard",
    "organizational_memory_history_guard",
    "organizational_memory_side_record_guard",
}
TRIGGERS = {
    "a_organizational_memory_lineage_guard",
    "b_organizational_memory_root_guard",
    "organizational_memory_history_guard",
    "organizational_memory_outbox_guard",
    "organizational_memory_idempotency_guard",
}


def test_repository_head_preserves_patch_034_in_current_chain() -> None:
    script = ScriptDirectory.from_config(alembic_config)
    assert TEST_DATABASE_REVISION == "e04700000001"
    assert script.get_revision("e03800000001").down_revision == "e03400000001"


def test_exact_schema_functions_triggers_and_indexes_exist() -> None:
    inspector = inspect(owner_engine)
    assert TABLES <= set(inspector.get_table_names())
    assert {column["name"] for column in inspector.get_columns("organizational_memories")} == {
        "id", "organization_id", "workspace_id", "project_id", "version",
        "standing", "source_report_id", "source_accepted_version",
        "source_snapshot_digest", "projection_contract", "projection",
        "projection_digest", "manifest", "provenance_digest", "admitted_by_id",
        "admitted_at", "admission_rationale", "audience_actor_ids",
        "reuse_restrictions", "predecessor_memory_id", "withdrawn_by_id",
        "withdrawn_at", "withdrawal_reason", "superseded_by_id", "superseded_at",
        "supersession_reason", "replacement_memory_id", "created_at", "updated_at",
    }
    root_indexes = {item["name"] for item in inspector.get_indexes("organizational_memories")}
    assert {
        "ix_organizational_memories_active_order",
        "ix_organizational_memories_predecessor",
        "ix_organizational_memories_replacement",
        "uq_organizational_memories_replacement_once",
        "uq_organizational_memory_source",
    } <= root_indexes
    with owner_engine.connect() as connection:
        functions = set(connection.execute(text(
            "SELECT proname FROM pg_proc WHERE proname LIKE 'organizational_memory_%'"
        )).scalars())
        triggers = set(connection.execute(text(
            "SELECT tgname FROM pg_trigger WHERE tgname LIKE '%organizational_memory%' "
            "AND NOT tgisinternal AND tgenabled='O'"
        )).scalars())
    assert functions == FUNCTIONS
    assert triggers == TRIGGERS


def test_closed_json_validators_reject_unknown_and_cross_paired_payloads() -> None:
    with owner_engine.connect() as connection:
        assert connection.exec_driver_sql(
            "SELECT NOT organizational_memory_projection_v1_valid('{\"unexpected\":true}'::jsonb)"
        ).scalar_one()
        assert connection.exec_driver_sql(
            "SELECT NOT organizational_memory_manifest_v1_valid('{\"unexpected\":true}'::jsonb)"
        ).scalar_one()
        assert connection.exec_driver_sql(
            "SELECT NOT organizational_memory_event_payload_v1_valid("
            "'ORGANIZATIONAL_MEMORY_ADMITTED','{\"content\":\"secret\"}'::jsonb)"
        ).scalar_one()
        assert connection.exec_driver_sql(
            "SELECT NOT organizational_memory_idempotency_result_v1_valid("
            "'withdraw','{\"result_type\":\"admit.v1\"}'::jsonb)"
        ).scalar_one()


def test_event_and_idempotency_validators_reject_malformed_closed_values() -> None:
    event = {
        "memory_id": "11111111-1111-4111-8111-111111111111",
        "aggregate_version": 2,
        "organization_id": "22222222-2222-4222-8222-222222222222",
        "workspace_id": 1,
        "project_id": None,
        "standing": "superseded",
        "actor_id": 1,
        "occurred_at": "2026-08-13T09:00:00.000000Z",
        "command_id": "33333333-3333-4333-8333-333333333333",
        "correlation_id": "44444444-4444-4444-8444-444444444444",
        "causation_id": "55555555-5555-4555-8555-555555555555",
        "source_report_id": "66666666-6666-4666-8666-666666666666",
        "source_accepted_version": 2,
        "predecessor_memory_id": None,
        "replacement_memory_id": "77777777-7777-4777-8777-777777777777",
        "provenance_entry_count": 1,
    }
    with owner_engine.connect() as connection:
        assert connection.execute(text(
            "SELECT organizational_memory_event_payload_v1_valid(:kind,CAST(:value AS jsonb))"
        ), {"kind": "ORGANIZATIONAL_MEMORY_SUPERSEDED", "value": json.dumps(event)}).scalar_one()
        for key, invalid in (
            ("occurred_at", "2026-99-99T99:99:99.000000Z"),
            ("replacement_memory_id", "not-a-uuid"),
            ("aggregate_version", 1.5),
            ("actor_id", True),
        ):
            malformed = {**event, key: invalid}
            assert not connection.execute(text(
                "SELECT organizational_memory_event_payload_v1_valid(:kind,CAST(:value AS jsonb))"
            ), {"kind": "ORGANIZATIONAL_MEMORY_SUPERSEDED", "value": json.dumps(malformed)}).scalar_one()

        valid_admit = {
            "result_type": "admit.v1",
            "memory_id": event["memory_id"],
            "version": 1,
            "standing": "active",
            "source_report_id": event["source_report_id"],
            "source_accepted_version": 2,
        }
        assert connection.execute(text(
            "SELECT organizational_memory_idempotency_result_v1_valid('admit',CAST(:value AS jsonb))"
        ), {"value": json.dumps(valid_admit)}).scalar_one()
        for malformed in (
            {**valid_admit, "memory_id": "not-a-uuid"},
            {**valid_admit, "source_accepted_version": 1.5},
            {**valid_admit, "content": "protected"},
            {**valid_admit, "result_type": "withdraw.v1"},
        ):
            assert not connection.execute(text(
                "SELECT organizational_memory_idempotency_result_v1_valid('admit',CAST(:value AS jsonb))"
            ), {"value": json.dumps(malformed)}).scalar_one()
        oversized = {**valid_admit, "memory_id": "x" * 1100}
        assert not connection.execute(text(
            "SELECT organizational_memory_idempotency_result_v1_valid('admit',CAST(:value AS jsonb))"
        ), {"value": json.dumps(oversized)}).scalar_one()


def test_closed_validators_return_strict_false_for_null_and_semantically_invalid_values() -> None:
    memory_id = "11111111-1111-4111-8111-111111111111"
    source_id = "22222222-2222-4222-8222-222222222222"
    predecessor_id = "33333333-3333-4333-8333-333333333333"
    replacement_id = "44444444-4444-4444-8444-444444444444"
    stored_results = {
        "admit": {
            "result_type": "admit.v1", "memory_id": memory_id, "version": 1,
            "standing": "active", "source_report_id": source_id,
            "source_accepted_version": 1,
        },
        "withdraw": {
            "result_type": "withdraw.v1", "memory_id": memory_id,
            "result_version": 2, "standing": "withdrawn",
            "withdrawn_at": "2026-08-13T09:00:00.000000Z",
        },
        "create_successor": {
            "result_type": "create_successor.v1", "memory_id": memory_id,
            "predecessor_memory_id": predecessor_id, "version": 1,
            "standing": "active", "source_report_id": source_id,
            "source_accepted_version": 2,
        },
        "supersede": {
            "result_type": "supersede.v1",
            "predecessor_memory_id": predecessor_id,
            "predecessor_result_version": 2,
            "predecessor_standing": "superseded",
            "replacement_memory_id": replacement_id,
            "replacement_version_at_command": 1,
            "replacement_standing": "active",
            "superseded_at": "2026-08-13T09:00:00.000000Z",
        },
    }
    null_cases = (
        ("admit", {**stored_results["admit"], "memory_id": None}),
        ("withdraw", {**stored_results["withdraw"], "withdrawn_at": None}),
        ("create_successor", {
            **stored_results["create_successor"], "predecessor_memory_id": None,
        }),
        ("supersede", {
            **stored_results["supersede"], "replacement_memory_id": None,
        }),
    )
    calendar_cases = (
        ("withdraw", {**stored_results["withdraw"],
                      "withdrawn_at": "2026-02-31T09:00:00.000000Z"}),
        ("supersede", {**stored_results["supersede"],
                       "superseded_at": "2026-02-31T09:00:00.000000Z"}),
        ("withdraw", {**stored_results["withdraw"],
                      "withdrawn_at": "2026-08-13T24:00:00.000000Z"}),
    )
    with owner_engine.connect() as connection:
        for operation, payload in (*null_cases, *calendar_cases):
            assert connection.execute(text(
                "SELECT organizational_memory_idempotency_result_v1_valid("
                ":operation,CAST(:payload AS jsonb)) IS FALSE"
            ), {
                "operation": operation, "payload": json.dumps(payload),
            }).scalar_one()

        event = {
            "memory_id": memory_id, "aggregate_version": 1,
            "organization_id": "55555555-5555-4555-8555-555555555555",
            "workspace_id": 1, "project_id": None, "standing": "withdrawn",
            "actor_id": 1, "occurred_at": "2026-08-13T09:00:00.000000Z",
            "command_id": "66666666-6666-4666-8666-666666666666",
            "correlation_id": "77777777-7777-4777-8777-777777777777",
            "causation_id": "88888888-8888-4888-8888-888888888888",
            "source_report_id": source_id, "source_accepted_version": 1,
            "predecessor_memory_id": None, "replacement_memory_id": None,
            "provenance_entry_count": 1,
        }
        for malformed_event in (
            {**event, "memory_id": None},
            {**event, "occurred_at": None},
            {**event, "occurred_at": "2026-02-31T09:00:00.000000Z"},
            {**event, "occurred_at": "2026-08-13T24:00:00.000000Z"},
        ):
            assert connection.execute(text(
                "SELECT organizational_memory_event_payload_v1_valid("
                "'ORGANIZATIONAL_MEMORY_WITHDRAWN',CAST(:payload AS jsonb)) IS FALSE"
            ), {"payload": json.dumps(malformed_event)}).scalar_one()


def test_schema_matrix_matches_ids_types_nullability_defaults_fks_and_constraints() -> None:
    inspector = inspect(owner_engine)
    expected_columns = {
        "organizational_memories": {
            "id": ("UUID", False, None), "organization_id": ("UUID", False, None),
            "workspace_id": ("BIGINT", False, None), "project_id": ("BIGINT", True, None),
            "version": ("BIGINT", False, "'1'::bigint"),
            "standing": ("VARCHAR(16)", False, "'active'::character varying"),
            "source_report_id": ("UUID", False, None),
            "source_accepted_version": ("BIGINT", False, None),
            "source_snapshot_digest": ("CHAR(64)", False, None),
            "projection_contract": ("VARCHAR(64)", False, None),
            "projection": ("JSONB", False, None),
            "projection_digest": ("CHAR(64)", False, None),
            "manifest": ("JSONB", False, None),
            "provenance_digest": ("CHAR(64)", False, None),
            "admitted_by_id": ("BIGINT", False, None),
            "admitted_at": ("TIMESTAMPTZ", False, None),
            "admission_rationale": ("VARCHAR(2000)", False, None),
            "audience_actor_ids": ("BIGINT[]", False, "'{}'::bigint[]"),
            "reuse_restrictions": ("JSONB", False, "'[]'::jsonb"),
            "predecessor_memory_id": ("UUID", True, None),
            "withdrawn_by_id": ("BIGINT", True, None),
            "withdrawn_at": ("TIMESTAMPTZ", True, None),
            "withdrawal_reason": ("VARCHAR(2000)", True, None),
            "superseded_by_id": ("BIGINT", True, None),
            "superseded_at": ("TIMESTAMPTZ", True, None),
            "supersession_reason": ("VARCHAR(2000)", True, None),
            "replacement_memory_id": ("UUID", True, None),
            "created_at": ("TIMESTAMPTZ", False, None),
            "updated_at": ("TIMESTAMPTZ", False, None),
        },
        "organizational_memory_standing_history": {
            "event_id": ("UUID", False, None), "memory_id": ("UUID", False, None),
            "organization_id": ("UUID", False, None),
            "aggregate_version": ("BIGINT", False, None),
            "from_standing": ("VARCHAR(16)", True, None),
            "to_standing": ("VARCHAR(16)", False, None),
            "actor_id": ("BIGINT", False, None),
            "occurred_at": ("TIMESTAMPTZ", False, None),
            "reason": ("VARCHAR(2000)", False, None),
            "replacement_memory_id": ("UUID", True, None),
        },
        "organizational_memory_events_outbox": {
            "event_id": ("UUID", False, None), "memory_id": ("UUID", False, None),
            "aggregate_version": ("BIGINT", False, None),
            "event_type": ("VARCHAR(64)", False, None),
            "payload_schema_version": ("SMALLINT", False, "'1'::smallint"),
            "payload": ("JSONB", False, None),
            "occurred_at": ("TIMESTAMPTZ", False, None),
            "created_at": ("TIMESTAMPTZ", False, None),
            "published_at": ("TIMESTAMPTZ", True, None),
            "attempt_count": ("INTEGER", False, "0"),
            "last_error_category": ("VARCHAR(64)", True, None),
        },
        "organizational_memory_idempotency": {
            "organization_id": ("UUID", False, None),
            "actor_id": ("BIGINT", False, None),
            "operation": ("VARCHAR(32)", False, None),
            "idempotency_id": ("UUID", False, None),
            "request_fingerprint": ("CHAR(64)", False, None),
            "status": ("VARCHAR(16)", False, "'pending'::character varying"),
            "result_schema_version": ("SMALLINT", False, "'1'::smallint"),
            "safe_result": ("JSONB", True, None),
            "created_at": ("TIMESTAMPTZ", False, None),
            "updated_at": ("TIMESTAMPTZ", False, None),
            "completed_at": ("TIMESTAMPTZ", True, None),
        },
    }

    def exact_type(column) -> str:
        column_type = column["type"]
        if str(column_type).upper() == "TIMESTAMP":
            return "TIMESTAMPTZ" if column_type.timezone else "TIMESTAMP"
        if str(column_type).upper() == "ARRAY":
            return f"{str(column_type.item_type).upper()}[]"
        return str(column_type).upper()

    for table_name, expected in expected_columns.items():
        actual = {
            column["name"]: (exact_type(column), column["nullable"], column["default"])
            for column in inspector.get_columns(table_name)
        }
        assert actual == expected

    assert inspector.get_pk_constraint("organizational_memories")["constrained_columns"] == ["id"]
    assert inspector.get_pk_constraint("organizational_memory_standing_history")["constrained_columns"] == ["event_id"]
    assert inspector.get_pk_constraint("organizational_memory_events_outbox")["constrained_columns"] == ["event_id"]
    assert inspector.get_pk_constraint("organizational_memory_idempotency")["constrained_columns"] == [
        "organization_id", "actor_id", "operation", "idempotency_id",
    ]

    expected_checks = {
        "organizational_memories": {
            "ck_organizational_memories_workspace_positive", "ck_organizational_memories_project_positive",
            "ck_organizational_memories_version_positive", "ck_organizational_memories_standing",
            "ck_organizational_memories_source_version", "ck_organizational_memories_source_digest",
            "ck_organizational_memories_projection_contract", "ck_organizational_memories_projection_digest",
            "ck_organizational_memories_provenance_digest", "ck_organizational_memories_admitted_by",
            "ck_organizational_memories_distinct_predecessor", "ck_organizational_memories_distinct_replacement",
            "ck_organizational_memories_audience_bound", "ck_organizational_memories_restrictions_bound",
            "ck_organizational_memories_timestamp_order", "ck_organizational_memories_projection_valid",
            "ck_organizational_memories_manifest_valid", "ck_organizational_memories_projection_digest_coherent",
            "ck_organizational_memories_manifest_root_coherent",
        },
        "organizational_memory_standing_history": {
            "ck_organizational_memory_history_version", "ck_organizational_memory_history_actor",
            "ck_organizational_memory_history_from", "ck_organizational_memory_history_to",
        },
        "organizational_memory_events_outbox": {
            "ck_organizational_memory_outbox_version", "ck_organizational_memory_outbox_event_type",
            "ck_organizational_memory_outbox_schema_version", "ck_organizational_memory_outbox_attempt_count",
            "ck_organizational_memory_outbox_error_category", "ck_organizational_memory_outbox_payload",
            "ck_organizational_memory_outbox_root_coherent",
        },
        "organizational_memory_idempotency": {
            "ck_organizational_memory_idempotency_actor", "ck_organizational_memory_idempotency_operation",
            "ck_organizational_memory_idempotency_fingerprint", "ck_organizational_memory_idempotency_status",
            "ck_organizational_memory_idempotency_schema_version",
            "ck_organizational_memory_idempotency_timestamp_order",
            "ck_organizational_memory_idempotency_result",
        },
    }
    for table_name, expected in expected_checks.items():
        assert {item["name"] for item in inspector.get_check_constraints(table_name)} == expected

    expected_fks = {
        "organizational_memories": {
            (("organization_id",), "organizations"), (("workspace_id",), "engineering_workspaces"),
            (("project_id",), "projects"), (("source_report_id",), "technical_reports"),
            (("admitted_by_id",), "users"), (("predecessor_memory_id",), "organizational_memories"),
            (("withdrawn_by_id",), "users"), (("superseded_by_id",), "users"),
            (("replacement_memory_id",), "organizational_memories"),
        },
        "organizational_memory_standing_history": {
            (("memory_id",), "organizational_memories"), (("organization_id",), "organizations"),
            (("actor_id",), "users"), (("replacement_memory_id",), "organizational_memories"),
        },
        "organizational_memory_events_outbox": {
            (("memory_id",), "organizational_memories"),
        },
        "organizational_memory_idempotency": {
            (("organization_id",), "organizations"), (("actor_id",), "users"),
        },
    }
    for table_name, expected in expected_fks.items():
        actual = {
            (tuple(fk["constrained_columns"]), fk["referred_table"])
            for fk in inspector.get_foreign_keys(table_name)
        }
        assert actual == expected
        assert all(
            fk["referred_columns"] == ["id"] and fk["options"].get("ondelete") == "RESTRICT"
            for fk in inspector.get_foreign_keys(table_name)
        )

    expected_indexes = {
        "organizational_memories": {
            "ix_organizational_memories_active_order", "ix_organizational_memories_predecessor",
            "ix_organizational_memories_replacement", "uq_organizational_memories_replacement_once",
            "uq_organizational_memory_source",
        },
        "organizational_memory_standing_history": {
            "ix_organizational_memory_history_memory_version", "uq_organizational_memory_history_version",
        },
        "organizational_memory_events_outbox": {
            "ix_organizational_memory_outbox_pending", "uq_organizational_memory_outbox_aggregate_event",
        },
        "organizational_memory_idempotency": set(),
    }
    for table_name, expected in expected_indexes.items():
        assert {item["name"] for item in inspector.get_indexes(table_name)} == expected


def test_supersession_guard_contains_deterministic_uuid_lock_order() -> None:
    with owner_engine.connect() as connection:
        definition = connection.execute(text(
            "SELECT pg_get_functiondef('public.organizational_memory_lineage_guard()'::regprocedure)"
        )).scalar_one()
    normalized = re.sub(r"\s+", " ", definition.lower())
    assert re.search(r"id in \(old\.id,\s*new\.replacement_memory_id\)", normalized)
    assert "order by id" in normalized
    assert "for update" in normalized


def test_patch_034_downgrade_and_upgrade_restore_single_head() -> None:
    try:
        # This historical cycle crosses PATCH-038.  Remove disposable rows
        # committed by real-UoW tests so its strict Human-approved legacy
        # Customer inventory guard is exercised from an isolated state.
        with owner_engine.begin() as connection:
            connection.execute(text("TRUNCATE TABLE customers CASCADE"))
        command.downgrade(alembic_config, "e03200000001")
        assert not (TABLES & set(inspect(owner_engine).get_table_names()))
    finally:
        command.upgrade(alembic_config, TEST_DATABASE_REVISION)
    with owner_engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == TEST_DATABASE_REVISION
        )
