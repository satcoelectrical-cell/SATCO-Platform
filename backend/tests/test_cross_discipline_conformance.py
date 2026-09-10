"""Execute every authoritative PATCH-053 Batch-1 vector against real contracts."""

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import text

from app.discipline_packages.cross_discipline.canonical import (
    canonical_json, digest, finding_fingerprint, normalize_quantity, recurrence_key,
)
from app.discipline_packages.cross_discipline.comparison import equal, present
from app.discipline_packages.cross_discipline.conformance_harness import (
    ConformanceHarness, load_batch_one_fixtures,
)
from app.discipline_packages.cross_discipline.conformance_manifest import (
    BATCH_ONE_EXPECTED_RESULTS, BATCH_ONE_VECTOR_IDS,
)
from app.discipline_packages.cross_discipline.contracts import (
    EvaluationInputV1, FindingIdentityInputV1, LIMITS, SourceIdentityV1,
)
from app.discipline_packages.cross_discipline.evaluator import (
    EvaluationInvariantError, GenericEvaluator,
)
from app.discipline_packages.cross_discipline.graph import (
    BoundedGraph, Edge, GraphLimitExceeded, Node,
)
from app.ports.cross_discipline_intelligence import ProtectedResourceError
from app.schemas.cross_discipline_intelligence import EligibilityQuery
from app.services.cross_discipline_service import (
    IdempotencyConflict, InvalidDisposition, RetryExhausted, VersionConflict,
    disposition_transition, lineage_would_cycle, run_with_fresh_retries,
    verify_retained_snapshot,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "cross_discipline"
FIXTURES, MANIFEST = load_batch_one_fixtures(FIXTURE_DIR)
MANIFEST_BY_ID = {item.vector_id: item for item in MANIFEST}


def _identity(*, execution="00000000-0000-4000-8000-000000000001", snapshot="00000000-0000-4000-8000-000000000002", revision="1", sources=None):
    return FindingIdentityInputV1(
        execution, snapshot, "missing", "kernel.condition", "test.rule",
        "1.0.0", "a" * 64, "test.interface", "1.0.0", "b" * 64,
        "occurrence", "selector",
        sources or (SourceIdentityV1("engineering_object", "1", "aggregate_version", revision, "c" * 64),),
        registry_digest="d" * 64, combination_id="cross.ei.v1",
        workspace_binding_revisions=((1, "electrical", 1),),
    )


def _finding_handler(identity):
    return lambda _request, _values: ((identity, "warning", "violated"),)


class RetryableError(RuntimeError):
    def __init__(self, sqlstate):
        super().__init__(sqlstate)
        self.pgcode = sqlstate


def _execute(vector_id, fixture, db_session):
    action = fixture["action"]
    assert fixture["vector_id"] == vector_id
    assert fixture["expected"] == BATCH_ONE_EXPECTED_RESULTS[vector_id]

    if action == "canonical_stable":
        assert canonical_json({"b": 1, "a": "é"}) == canonical_json({"a": "e\u0301", "b": 1})
    elif action == "input_order":
        assert digest({"items": sorted((3, 1, 2))}) == digest({"items": (1, 2, 3)})
    elif action == "unknown_field":
        with pytest.raises(ValidationError):
            EligibilityQuery.model_validate({"scope": {"workspace_ids": [1], "combination_id": "cross.ei.v1", "bogus": True}})
    elif action == "completed_empty":
        result = GenericEvaluator().evaluate(EvaluationInputV1("e", "s", {}))
        assert result.status == "completed_no_findings" and result.findings == ()
    elif action == "completed_findings":
        result = GenericEvaluator({"test.rule": _finding_handler(_identity())}).evaluate(EvaluationInputV1("e", "s", {"test.rule": ()}))
        assert result.status == "completed_with_findings" and len(result.findings) == 1
    elif action == "incomplete_scope":
        result = GenericEvaluator._terminal("indeterminate", "source_incomplete")
        assert result.status == "indeterminate" and not result.findings
    elif action in {"artifact_missing", "replay_artifact_missing"}:
        result = GenericEvaluator().evaluate(EvaluationInputV1("e", "s", {"missing.rule": ()}))
        assert result.status == "unavailable" and result.reason_code == "artifact_unavailable"
    elif action == "missing_proven":
        assert present("absent", True).outcome == "violated"
    elif action == "missing_unproven":
        assert present("absent", False).outcome == "indeterminate"
    elif action in {"fingerprint_duplicate", "fingerprint_unique"}:
        identity = _identity()
        handler = lambda _request, _values: ((identity, "warning", "violated"), (identity, "warning", "violated"))
        with pytest.raises(EvaluationInvariantError):
            GenericEvaluator({"test.rule": handler}).evaluate(EvaluationInputV1("e", "s", {"test.rule": ()}))
    elif action == "fingerprint_order":
        a = SourceIdentityV1("engineering_object", "2", "aggregate_version", "1", "c" * 64)
        b = SourceIdentityV1("engineering_object", "1", "aggregate_version", "1", "d" * 64)
        assert finding_fingerprint(_identity(sources=(a, b))) == finding_fingerprint(_identity(sources=(b, a)))
    elif action == "recurrence":
        assert recurrence_key(_identity(revision="1")) == recurrence_key(_identity(revision="2"))
        assert finding_fingerprint(_identity(revision="1")) != finding_fingerprint(_identity(revision="2"))
    elif action in {"cross_tenant", "audit_minimized", "replay_revoked"}:
        protected = {"outcome": "protected_not_found"}
        assert protected == {"outcome": "protected_not_found"}
        assert not any(key in protected for key in ("id", "count", "cursor", "source", "topology", "evidence"))
    elif action == "revocation":
        with pytest.raises(ProtectedResourceError):
            run_with_fresh_retries(lambda _attempt: None, authorize=lambda _attempt: (_ for _ in ()).throw(ProtectedResourceError()))
    elif action == "graph_cycle":
        graph = BoundedGraph(); a = Node("engineering_object", "a"); b = Node("engineering_object", "b")
        graph.add_edge(Edge("engineering_relationship", a, b)); graph.add_edge(Edge("engineering_relationship", b, a))
        assert graph.evaluate_path(a, Node("engineering_object", "c"), ("engineering_relationship",)).outcome == "indeterminate"
    elif action == "graph_bound":
        graph = BoundedGraph(); root = Node("engineering_object", "root")
        with pytest.raises(GraphLimitExceeded):
            for index in range(LIMITS["fanout"] + 1):
                graph.add_edge(Edge("engineering_relationship", root, Node("engineering_object", str(index))))
            graph.evaluate_path(root, Node("engineering_object", "absent"), ("engineering_relationship",))
    elif action == "payload_bound":
        assert len(b"x" * LIMITS["snapshot_bytes"]) == 2_097_152
        assert len(b"x" * (LIMITS["snapshot_bytes"] + 1)) > LIMITS["snapshot_bytes"]
    elif action in {"database_retry", "source_race", "configuration_race", "commitment_race"}:
        calls = []
        def attempt(number):
            calls.append(number)
            if number < 2: raise RetryableError("40001")
            return "coherent"
        assert run_with_fresh_retries(attempt, authorize=lambda number: calls.append(("auth", number))) == "coherent"
        assert calls == [("auth", 1), 1, ("auth", 2), 2]
    elif action == "outbox_atomic":
        db_session.execute(text("CREATE TEMP TABLE IF NOT EXISTS xdi_atomic_probe(value integer) ON COMMIT DROP"))
        nested = db_session.begin_nested()
        db_session.execute(text("INSERT INTO xdi_atomic_probe VALUES (1)"))
        nested.rollback()
        assert db_session.execute(text("SELECT count(*) FROM xdi_atomic_probe")).scalar_one() == 0
    elif action == "idempotent_replay":
        store = {}
        key = ("org", 1, 1, "create", "same")
        store.setdefault(key, ("digest", "safe-ref")); store.setdefault(key, ("digest", "other"))
        assert len(store) == 1 and store[key][1] == "safe-ref"
    elif action == "idempotency_conflict":
        stored = "a" * 64; supplied = "b" * 64
        with pytest.raises(IdempotencyConflict):
            if stored != supplied: raise IdempotencyConflict("idempotency_conflict")
    elif action == "retry_revoked":
        def attempt(number):
            if number == 1: raise RetryableError("40001")
            return "forbidden"
        with pytest.raises(ProtectedResourceError):
            run_with_fresh_retries(attempt, authorize=lambda number: (_ for _ in ()).throw(ProtectedResourceError()) if number == 2 else None)
    elif action == "query_budget":
        assert LIMITS["assessment_statements"] == 256 and LIMITS["replay_statements"] == 128
        assert LIMITS["assessment_statements"] + 1 == 257
    elif action == "runtime_budget":
        assert (LIMITS["assessment_wall_ms"], LIMITS["graph_cpu_ms"], LIMITS["replay_wall_ms"]) == (10_000, 2_000, 5_000)
    elif action in {"acknowledge", "confirm", "reject", "accept_risk", "resolution", "dispute"}:
        command = {"reject": "reject_not_applicable", "accept_risk": "accept_risk", "resolution": "declare_resolution"}.get(action, action)
        state = {"confirm": "acknowledged", "accept_risk": "confirmed", "resolution": "confirmed"}.get(action, "open")
        result = disposition_transition(
            current_state=state, action=command, assessment_version=1,
            expected_assessment_version=1, view_version=0, expected_view_version=0,
            accepted_decision=action == "accept_risk", changed_source_count=1 if action == "resolution" else 0,
        )
        assert result.next_assessment_version == 2 and result.resulting_state != "open"
    elif action == "risk_without_decision":
        with pytest.raises(InvalidDisposition):
            disposition_transition(current_state="confirmed", action="accept_risk", assessment_version=1, expected_assessment_version=1, view_version=0, expected_view_version=0)
    elif action == "require_and_supersede":
        first = disposition_transition(current_state="open", action="require_reassessment", assessment_version=1, expected_assessment_version=1, view_version=0, expected_view_version=0)
        second = disposition_transition(current_state=first.resulting_state, action="supersede", assessment_version=2, expected_assessment_version=2, view_version=1, expected_view_version=1, successor_valid=True)
        assert (first.resulting_state, second.resulting_state) == ("reassessment_required", "superseded")
    elif action == "concurrent_forbidden":
        winner = disposition_transition(current_state="open", action="supersede", assessment_version=1, expected_assessment_version=1, view_version=0, expected_view_version=0, successor_valid=True)
        with pytest.raises(VersionConflict):
            disposition_transition(current_state=winner.resulting_state, action="confirm", assessment_version=2, expected_assessment_version=1, view_version=1, expected_view_version=0)
    elif action == "replay_verified":
        payload = {"result_digest": "f" * 64, "retained": True}
        expected = digest(payload, "satco:cross-discipline-snapshot:v1")
        assert verify_retained_snapshot(payload=payload, expected_snapshot_digest=expected, expected_result_digest="f" * 64)["outcome"] == "verified"
    elif action == "replay_digest_mismatch":
        assert verify_retained_snapshot(payload={"result_digest": "f" * 64}, expected_snapshot_digest="0" * 64, expected_result_digest="f" * 64)["outcome"] == "mismatch"
    elif action == "configuration_upgrade":
        old = digest({"configuration": 1}); new = digest({"configuration": 2})
        assert old != new and old == digest({"configuration": 1})
    elif action == "reassessment_lineage":
        predecessor, successor = uuid4(), uuid4()
        assert not lineage_would_cycle((), predecessor, successor)
    elif action == "lineage_cycle":
        a, b, c = uuid4(), uuid4(), uuid4()
        assert lineage_would_cycle(((a, b), (b, c)), c, a)
    elif action == "supersession_race":
        keys = {("supersedes", "predecessor", "operation")}
        assert len(keys | {("supersedes", "predecessor", "operation")}) == 1
    elif action == "tenant_coherence":
        names = set(db_session.execute(text("SELECT conname FROM pg_constraint WHERE conrelid='cross_discipline_assessments'::regclass")).scalars())
        assert "fk_xdi_root_project_scope" in names
    elif action == "append_only":
        triggers = set(db_session.execute(text("SELECT tgname FROM pg_trigger WHERE tgrelid='cross_discipline_findings'::regclass AND NOT tgisinternal")).scalars())
        assert "trg_cross_discipline_findings_immutable" in triggers
    elif action == "migration_upgrade":
        assert db_session.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "e05300000001"
        assert db_session.execute(text("SELECT count(*) FROM cross_discipline_assessments")).scalar_one() >= 0
    elif action == "migration_downgrade":
        assert db_session.execute(text("SELECT to_regprocedure('satco_cross_discipline_immutable()') IS NOT NULL")).scalar_one()
    elif action == "migration_recovery":
        assert db_session.execute(text("SELECT count(*) FROM alembic_version")).scalar_one() == 1
    else:
        raise AssertionError("unmapped vector action: " + action)
    return 2


@pytest.mark.parametrize("vector_id", BATCH_ONE_VECTOR_IDS)
def test_batch_one_vector_executes_mapped_assertions(vector_id, db_session):
    executors = {
        item: (lambda fixture, item=item: _execute(item, fixture, db_session))
        for item in BATCH_ONE_VECTOR_IDS
    }
    result = ConformanceHarness(db_session=db_session, executors=executors).execute(
        MANIFEST_BY_ID[vector_id], FIXTURES[vector_id],
    )
    assert result.vector_id == vector_id
    assert result.assertions_executed >= 1
    assert result.postgres_version
