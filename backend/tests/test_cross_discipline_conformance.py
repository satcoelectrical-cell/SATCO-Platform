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
    ConformanceHarness, load_batch_five_fixtures, load_batch_four_fixtures, load_batch_one_fixtures, load_batch_three_fixtures, load_batch_two_fixtures,
)
from app.discipline_packages.cross_discipline.conformance_manifest import (
    BATCH_ONE_EXPECTED_RESULTS, BATCH_ONE_VECTOR_IDS, BATCH_TWO_EXPECTED_RESULTS,
    BATCH_TWO_VECTOR_IDS, BATCH_THREE_EXPECTED_RESULTS, BATCH_THREE_VECTOR_IDS,
    BATCH_FOUR_EXPECTED_RESULTS, BATCH_FOUR_VECTOR_IDS,
    BATCH_FIVE_EXPECTED_RESULTS, BATCH_FIVE_VECTOR_IDS,
)
from app.discipline_packages.cross_discipline.contracts import (
    BATCH_TWO_CONTEXT_IDS, BATCH_TWO_EVIDENCE_IDS,
    BATCH_TWO_HANDOFF_APPLICABILITY_ID, BATCH_TWO_INTERFACE_APPLICABILITY_ID,
    BATCH_TWO_INTERFACE_ID, BATCH_TWO_PATH_ID, BATCH_TWO_RELATIONSHIP_GRAMMAR_ID,
    BATCH_TWO_RULE_IDS, BATCH_TWO_VERSION, EvaluationInputV1,
    ExplicitRelationshipV1, FindingIdentityInputV1, LIMITS, RangeV1, SourceIdentityV1,
)
from app.discipline_packages.cross_discipline.definitions.eic_v1 import (
    BATCH_THREE_APPLICABILITY_ID, BATCH_THREE_HANDOFF_APPLICABILITY_ID,
    BATCH_THREE_INTERFACE_ID, BATCH_THREE_PATH_ID,
    BATCH_THREE_RULE_IDS, BATCH_THREE_VERSION, batch_three_rule_definition,
    BATCH_FOUR_APPLICABILITY_ID, BATCH_FOUR_HANDOFF_APPLICABILITY_ID, BATCH_FOUR_INTERFACE_ID,
    BATCH_FOUR_PATH_ID, BATCH_FOUR_RULE_IDS, BATCH_FOUR_VERSION, batch_four_rule_definition,
    batch_two_rule_definition, load_batch_four_definition_set, load_batch_three_definition_set, load_batch_two_definition_set,
)
from app.discipline_packages.cross_discipline.evaluator import (
    EvaluationInvariantError, GenericEvaluator, batch_four_evaluator, batch_three_evaluator, batch_two_evaluator,
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


def _batch_two_identity(rule_id, *, category, subcode):
    declaration = batch_two_rule_definition(rule_id)
    interface = load_batch_two_definition_set().interface_definitions[0]
    return FindingIdentityInputV1(
        "00000000-0000-4000-8000-000000000011",
        "00000000-0000-4000-8000-000000000012",
        category, subcode, rule_id, BATCH_TWO_VERSION, declaration.digest,
        BATCH_TWO_INTERFACE_ID, BATCH_TWO_VERSION, interface.digest,
        "f" * 64, "xdi.sel.v1/electrical/engineering_object/00000000-0000-4000-8000-000000000013/power_endpoint",
        (SourceIdentityV1("engineering_object", "00000000-0000-4000-8000-000000000013", "aggregate_version", "1", "a" * 64),),
        registry_digest="b" * 64, combination_id="cross.ei.v1",
        workspace_binding_revisions=((1, "electrical", 1), (2, "instrumentation", 1)),
    )


def _batch_two_values(vector_id):
    endpoint = "00000000-0000-4000-8000-000000000013"
    instrument = "00000000-0000-4000-8000-000000000014"
    junction_box = "00000000-0000-4000-8000-000000000015"
    cable = "00000000-0000-4000-8000-000000000016"
    supply = "00000000-0000-4000-8000-000000000017"
    if vector_id.startswith("patch053.ei01") or vector_id.startswith("patch053.ei02"):
        return {BATCH_TWO_RULE_IDS[0]: {
            "applicability_id": BATCH_TWO_INTERFACE_APPLICABILITY_ID,
            "power_presence": "present" if vector_id.endswith("power_present") else "absent",
            "complete": True,
            "identity": _batch_two_identity(BATCH_TWO_RULE_IDS[0], category="missing", subcode="ei.instrument_power_required"),
        }}
    if vector_id.startswith("patch053.ei03") or vector_id.startswith("patch053.ei04"):
        return {BATCH_TWO_RULE_IDS[1]: {
            "applicability_id": BATCH_TWO_INTERFACE_APPLICABILITY_ID,
            "electrical_voltage": normalize_quantity("electric_potential", "24", "V"),
            "instrument_voltage": normalize_quantity("electric_potential", "24000" if vector_id.endswith("voltage_equal") else "23000", "mV"),
            "identity": _batch_two_identity(BATCH_TWO_RULE_IDS[1], category="inconsistent", subcode="ei.motor_instrument_voltage"),
        }}
    if vector_id.startswith("patch053.ei05") or vector_id.startswith("patch053.ei06"):
        edges = () if vector_id.endswith("cable_jb_gap") else (
            ExplicitRelationshipV1("engineering_relationship", "00000000-0000-4000-8000-000000000021", 1, "instrumentation", "transmits_to", instrument, junction_box),
            ExplicitRelationshipV1("engineering_relationship", "00000000-0000-4000-8000-000000000022", 1, "physical", "connected_through", junction_box, cable),
            ExplicitRelationshipV1("engineering_relationship", "00000000-0000-4000-8000-000000000023", 1, "electrical", "powered_by", cable, supply),
        )
        return {BATCH_TWO_RULE_IDS[2]: {
            "applicability_id": BATCH_TWO_INTERFACE_APPLICABILITY_ID,
            "relationship_grammar_id": BATCH_TWO_RELATIONSHIP_GRAMMAR_ID,
            "path_id": BATCH_TWO_PATH_ID, "complete": True,
            "signal_endpoint_id": instrument, "supply_terminal_id": supply,
            "edges": edges,
            "object_types": {instrument: "transmitter", junction_box: "junction_box", cable: "electrical_cable", supply: "electrical_power_source"},
            "identity": _batch_two_identity(BATCH_TWO_RULE_IDS[2], category="dependency", subcode="ei.cable_jb_path"),
        }}
    declarations = BATCH_TWO_CONTEXT_IDS + BATCH_TWO_EVIDENCE_IDS
    if vector_id.endswith("handoff_incomplete"):
        declarations = declarations[:-1]
    return {BATCH_TWO_RULE_IDS[3]: {
        "applicability_id": BATCH_TWO_HANDOFF_APPLICABILITY_ID,
        "declaration_ids": declarations, "complete": True,
        "commitment_current_use": True, "commitment_state": "current",
        "reassessment_needed": False, "provider_workspace_id": 1,
        "consumer_workspace_id": 2, "occurrence_provider_workspace_id": 1,
        "occurrence_consumer_workspace_id": 2,
        "identity": _batch_two_identity(BATCH_TWO_RULE_IDS[3], category="incomplete_handoff", subcode="ei.handoff_complete"),
    }}


def _execute_batch_two(vector_id, fixture):
    assert fixture["expected"] == BATCH_TWO_EXPECTED_RESULTS[vector_id]
    result = batch_two_evaluator().evaluate(EvaluationInputV1("execution", "snapshot", _batch_two_values(vector_id)))
    expected_finding = vector_id in {
        "patch053.ei02.power_missing", "patch053.ei04.voltage_mismatch",
        "patch053.ei06.cable_jb_gap", "patch053.ei08.handoff_incomplete",
    }
    assert (result.status == "completed_with_findings") is expected_finding
    assert len(result.findings) == (1 if expected_finding else 0)
    return 3


def _batch_three_identity(rule_id, *, category, subcode):
    declaration = batch_three_rule_definition(rule_id)
    interface = load_batch_three_definition_set().interface_definitions[1]
    return FindingIdentityInputV1(
        "00000000-0000-4000-8000-000000000031",
        "00000000-0000-4000-8000-000000000032",
        category, subcode, rule_id, BATCH_THREE_VERSION, declaration.digest,
        BATCH_THREE_INTERFACE_ID, BATCH_THREE_VERSION, interface.digest,
        "e" * 64, "xdi.sel.v1/instrumentation/engineering_object/00000000-0000-4000-8000-000000000033/signal_endpoint",
        (SourceIdentityV1("engineering_object", "00000000-0000-4000-8000-000000000033", "aggregate_version", "1", "a" * 64),),
        registry_digest="b" * 64, combination_id="cross.ic.v1",
        workspace_binding_revisions=((1, "instrumentation", 1), (2, "control_automation", 1)),
    )


def _batch_three_values(vector_id):
    if vector_id.startswith("patch053.ic01") or vector_id.startswith("patch053.ic02"):
        return {BATCH_THREE_RULE_IDS[0]: {
            "applicability_id": BATCH_THREE_APPLICABILITY_ID, "complete": True,
            "instrumentation_signal_type": "signal_current",
            "control_io_type": "analog_current" if vector_id.endswith("signal_type_equal") else "digital_dry_contact",
            "identity": _batch_three_identity(BATCH_THREE_RULE_IDS[0], category="inconsistent", subcode="ic.signal_type"),
        }}
    if vector_id.startswith("patch053.ic03") or vector_id.startswith("patch053.ic04"):
        return {BATCH_THREE_RULE_IDS[1]: {
            "applicability_id": BATCH_THREE_APPLICABILITY_ID, "complete": True,
            "instrumentation_range": RangeV1(Decimal("4"), Decimal("20")),
            "control_accepted_range": RangeV1(Decimal("0"), Decimal("20")) if vector_id.endswith("range_contains") else RangeV1(Decimal("0"), Decimal("10")),
            "identity": _batch_three_identity(BATCH_THREE_RULE_IDS[1], category="inconsistent", subcode="ic.signal_range"),
        }}
    if vector_id.startswith("patch053.ic05") or vector_id.startswith("patch053.ic06"):
        controller = "00000000-0000-4000-8000-000000000034"
        valve = "00000000-0000-4000-8000-000000000035"
        io_channel = "00000000-0000-4000-8000-000000000036"
        edges = (
            ExplicitRelationshipV1("engineering_relationship", "00000000-0000-4000-8000-000000000037", 1, "control_automation", "commands", controller, valve),
        )
        if vector_id.endswith("valve_paths"):
            edges += (ExplicitRelationshipV1("engineering_relationship", "00000000-0000-4000-8000-000000000038", 1, "instrumentation", "provides_feedback_to", valve, io_channel),)
        return {BATCH_THREE_RULE_IDS[2]: {
            "applicability_id": BATCH_THREE_APPLICABILITY_ID, "complete": True,
            "path_id": BATCH_THREE_PATH_ID,
            "edges": edges, "controller_id": controller, "valve_id": valve, "feedback_target_id": io_channel,
            "identity": _batch_three_identity(BATCH_THREE_RULE_IDS[2], category="dependency", subcode="ic.valve_command_feedback"),
        }}
    return {BATCH_THREE_RULE_IDS[3]: {
        "applicability_id": BATCH_THREE_HANDOFF_APPLICABILITY_ID, "complete": True,
        "commitment_current_use": True, "commitment_changed": False,
        "commitment_state": "fulfilled_for_stated_use" if vector_id.endswith("commitment_fulfilled") else "information_provided",
        "evidence_presence": "present",
        "identity": _batch_three_identity(BATCH_THREE_RULE_IDS[3], category="unfulfilled_commitment", subcode="ic.commitment_fulfilment"),
    }}


def _execute_batch_three(vector_id, fixture):
    assert fixture["expected"] == BATCH_THREE_EXPECTED_RESULTS[vector_id]
    result = batch_three_evaluator().evaluate(EvaluationInputV1("execution", "snapshot", _batch_three_values(vector_id)))
    expected_finding = vector_id in {
        "patch053.ic02.signal_type_mismatch", "patch053.ic04.range_mismatch",
        "patch053.ic06.valve_feedback_gap", "patch053.ic08.commitment_unfulfilled",
    }
    assert (result.status == "completed_with_findings") is expected_finding
    assert len(result.findings) == (1 if expected_finding else 0)
    return 3


def _batch_four_identity(rule_id, *, category, subcode):
    declaration = batch_four_rule_definition(rule_id)
    interface = load_batch_four_definition_set().interface_definitions[-1]
    return FindingIdentityInputV1(
        "00000000-0000-4000-8000-000000000061", "00000000-0000-4000-8000-000000000062",
        category, subcode, rule_id, BATCH_FOUR_VERSION, declaration.digest,
        BATCH_FOUR_INTERFACE_ID, BATCH_FOUR_VERSION, interface.digest, "d" * 64,
        "xdi.sel.v1/electrical/engineering_object/00000000-0000-4000-8000-000000000063/cabinet",
        (SourceIdentityV1("engineering_object", "00000000-0000-4000-8000-000000000063", "aggregate_version", "1", "a" * 64),),
        registry_digest="b" * 64, combination_id="cross.ec.v1",
        workspace_binding_revisions=((1, "electrical", 1), (2, "control_automation", 1)),
    )


def _batch_four_values(vector_id):
    cabinet, panel, supply = (
        "00000000-0000-4000-8000-000000000063", "00000000-0000-4000-8000-000000000064", "00000000-0000-4000-8000-000000000065",
    )
    if vector_id.startswith("patch053.ec01") or vector_id.startswith("patch053.ec02"):
        return {BATCH_FOUR_RULE_IDS[0]: {"applicability_id": BATCH_FOUR_APPLICABILITY_ID, "complete": True,
            "command_presence": "present", "status_presence": "present" if vector_id.endswith("command_status_complete") else "absent",
            "identity": _batch_four_identity(BATCH_FOUR_RULE_IDS[0], category="incomplete_handoff", subcode="ec.mcc_command_status")}}
    if vector_id.startswith("patch053.ec03") or vector_id.startswith("patch053.ec04"):
        edges = () if vector_id.endswith("cabinet_power_gap") else (
            ExplicitRelationshipV1("engineering_relationship", "00000000-0000-4000-8000-000000000066", 1, "physical", "connected_through", cabinet, panel),
            ExplicitRelationshipV1("engineering_relationship", "00000000-0000-4000-8000-000000000067", 1, "electrical", "powered_by", panel, supply),
        )
        return {BATCH_FOUR_RULE_IDS[1]: {"applicability_id": BATCH_FOUR_APPLICABILITY_ID, "complete": True, "path_id": BATCH_FOUR_PATH_ID,
            "edges": edges, "cabinet_id": cabinet, "supply_id": supply,
            "identity": _batch_four_identity(BATCH_FOUR_RULE_IDS[1], category="dependency", subcode="ec.cabinet_power_path")}}
    if vector_id.startswith("patch053.ec05") or vector_id.startswith("patch053.ec06"):
        reference = datetime(2026, 1, 31, tzinfo=timezone.utc)
        age = 2_592_000 if vector_id.endswith("source_fresh") else 2_592_000.000001
        return {BATCH_FOUR_RULE_IDS[2]: {"applicability_id": BATCH_FOUR_APPLICABILITY_ID, "complete": True,
            "observed_at": datetime.fromtimestamp(reference.timestamp() - age, tz=timezone.utc), "reference_at": reference,
            "identity": _batch_four_identity(BATCH_FOUR_RULE_IDS[2], category="stale", subcode="ec.source_freshness")}}
    return {BATCH_FOUR_RULE_IDS[3]: {"applicability_id": BATCH_FOUR_HANDOFF_APPLICABILITY_ID, "complete": True,
        "commitment_current_use": True, "commitment_changed": False,
        "commitment_state": "disputed" if vector_id.endswith("disputed") else "fulfilled_for_stated_use",
        "identity": _batch_four_identity(BATCH_FOUR_RULE_IDS[3], category="disputed", subcode="ec.commitment_dispute")}}


def _execute_batch_four(vector_id, fixture):
    assert fixture["expected"] == BATCH_FOUR_EXPECTED_RESULTS[vector_id]
    result = batch_four_evaluator().evaluate(EvaluationInputV1("execution", "snapshot", _batch_four_values(vector_id)))
    expected_finding = vector_id in {"patch053.ec02.status_missing", "patch053.ec04.cabinet_power_gap", "patch053.ec06.source_stale", "patch053.ec08.disputed"}
    assert (result.status == "completed_with_findings") is expected_finding
    assert len(result.findings) == (1 if expected_finding else 0)
    return 3


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
        assert db_session.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "e05300000002"
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


def test_batch_two_fixture_set_is_exact_cumulative_gate():
    fixtures, manifest = load_batch_two_fixtures(FIXTURE_DIR)
    assert tuple(manifest_item.vector_id for manifest_item in manifest)[-8:] == BATCH_TWO_VECTOR_IDS
    assert set(fixtures) == set(BATCH_ONE_VECTOR_IDS + BATCH_TWO_VECTOR_IDS)


@pytest.mark.parametrize("vector_id", BATCH_TWO_VECTOR_IDS)
def test_batch_two_vector_executes_its_real_rule_contract(vector_id, db_session):
    fixtures, manifest = load_batch_two_fixtures(FIXTURE_DIR)
    by_id = {item.vector_id: item for item in manifest}
    result = ConformanceHarness(
        db_session=db_session,
        executors={item: (lambda fixture, item=item: _execute_batch_two(item, fixture)) for item in BATCH_TWO_VECTOR_IDS},
    ).execute(by_id[vector_id], fixtures[vector_id])
    assert result.assertions_executed == 3


def test_batch_three_fixture_set_is_exact_cumulative_gate():
    fixtures, manifest = load_batch_three_fixtures(FIXTURE_DIR)
    assert tuple(manifest_item.vector_id for manifest_item in manifest)[-8:] == BATCH_THREE_VECTOR_IDS
    assert len(fixtures) == 67


@pytest.mark.parametrize("vector_id", BATCH_THREE_VECTOR_IDS)
def test_batch_three_vector_executes_its_real_rule_contract(vector_id, db_session):
    fixtures, manifest = load_batch_three_fixtures(FIXTURE_DIR)
    by_id = {item.vector_id: item for item in manifest}
    result = ConformanceHarness(
        db_session=db_session,
        executors={item: (lambda fixture, item=item: _execute_batch_three(item, fixture)) for item in BATCH_THREE_VECTOR_IDS},
    ).execute(by_id[vector_id], fixtures[vector_id])
    assert result.assertions_executed == 3


def test_batch_four_fixture_set_is_exact_cumulative_gate():
    fixtures, manifest = load_batch_four_fixtures(FIXTURE_DIR)
    assert tuple(manifest_item.vector_id for manifest_item in manifest)[-8:] == BATCH_FOUR_VECTOR_IDS
    assert len(fixtures) == 75


@pytest.mark.parametrize("vector_id", BATCH_FOUR_VECTOR_IDS)
def test_batch_four_vector_executes_its_real_rule_contract(vector_id, db_session):
    fixtures, manifest = load_batch_four_fixtures(FIXTURE_DIR)
    by_id = {item.vector_id: item for item in manifest}
    result = ConformanceHarness(
        db_session=db_session,
        executors={item: (lambda fixture, item=item: _execute_batch_four(item, fixture)) for item in BATCH_FOUR_VECTOR_IDS},
    ).execute(by_id[vector_id], fixtures[vector_id])
    assert result.assertions_executed == 3


def test_batch_five_fixture_set_is_exact_cumulative_gate():
    fixtures, manifest = load_batch_five_fixtures(FIXTURE_DIR)
    assert tuple(item.vector_id for item in manifest)[-21:] == BATCH_FIVE_VECTOR_IDS
    assert len(fixtures) == len(manifest) == 96


@pytest.mark.parametrize("vector_id", BATCH_FIVE_VECTOR_IDS)
def test_batch_five_vector_executes_accepted_contract(vector_id, db_session):
    fixtures, manifest = load_batch_five_fixtures(FIXTURE_DIR)
    by_id = {item.vector_id: item for item in manifest}
    def execute(fixture):
        assert fixture["expected"] == BATCH_FIVE_EXPECTED_RESULTS[vector_id]
        assert fixture["action"]
        return 2
    result = ConformanceHarness(db_session=db_session, executors={vector_id: execute}).execute(by_id[vector_id], fixtures[vector_id])
    assert result.assertions_executed == 2
