"""Closed PATCH-053 Batch-2 Electrical ↔ Instrumentation rule handlers."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from uuid import UUID

from ..comparison import enum_map_equal, equal, present, range_contains, set_contains
from ..contracts import (
    BATCH_TWO_HANDOFF_APPLICABILITY_ID, BATCH_TWO_INTERFACE_APPLICABILITY_ID,
    BATCH_TWO_INTERFACE_ID, BATCH_TWO_PATH_ID, BATCH_TWO_RELATIONSHIP_GRAMMAR_ID,
    BATCH_TWO_REQUIRED_DECLARATIONS, BATCH_TWO_RULE_IDS, BATCH_TWO_VERSION,
    ExplicitRelationshipV1, FindingIdentityInputV1, LIMITS, QuantityV1,
    RangeV1, RuleIndeterminate,
)
from ..definitions.eic_v1 import (
    BATCH_THREE_APPLICABILITY_ID, BATCH_THREE_HANDOFF_APPLICABILITY_ID,
    BATCH_THREE_INTERFACE_ID, BATCH_THREE_PATH_ID,
    BATCH_THREE_RULE_IDS, BATCH_THREE_VERSION, batch_three_rule_definition,
    batch_two_rule_definition, load_batch_three_definition_set, load_batch_two_definition_set,
)


BATCH_ONE_RULE_HANDLERS = MappingProxyType({})


def _identity(values: Mapping, *, rule_id: str, category: str, subcode: str) -> FindingIdentityInputV1:
    identity = values.get("identity")
    if not isinstance(identity, FindingIdentityInputV1):
        raise ValueError("invalid_request")
    declaration = batch_two_rule_definition(rule_id)
    interface = load_batch_two_definition_set().interface_definitions[0]
    if identity.rule_id != rule_id or identity.rule_version != BATCH_TWO_VERSION:
        raise ValueError("invalid_request")
    if identity.rule_digest != declaration.digest or identity.interface_digest != interface.digest:
        raise ValueError("invalid_request")
    if identity.interface_definition_id != BATCH_TWO_INTERFACE_ID or identity.interface_version != BATCH_TWO_VERSION:
        raise ValueError("invalid_request")
    if identity.category != category or identity.subcode != subcode:
        raise ValueError("invalid_request")
    return identity


def _finding(values: Mapping, *, rule_id: str, category: str, subcode: str, severity: str):
    return ((_identity(values, rule_id=rule_id, category=category, subcode=subcode), severity, "violated"),)


def _require_applicability(values: Mapping, expected: str) -> None:
    if values.get("applicability_id") != expected:
        raise ValueError("invalid_request")


def instrument_power_required(_request, values):
    if not isinstance(values, Mapping):
        raise ValueError("invalid_request")
    _require_applicability(values, BATCH_TWO_INTERFACE_APPLICABILITY_ID)
    result = present(values.get("power_presence", "unknown"), bool(values.get("complete", False)))
    if result.outcome == "indeterminate":
        raise RuleIndeterminate(result.reason or "source_incomplete")
    if result.outcome == "violated":
        return _finding(values, rule_id=BATCH_TWO_RULE_IDS[0], category="missing", subcode="ei.instrument_power_required", severity="major")
    return ()


def motor_instrument_voltage(_request, values):
    if not isinstance(values, Mapping):
        raise ValueError("invalid_request")
    _require_applicability(values, BATCH_TWO_INTERFACE_APPLICABILITY_ID)
    electrical, instrumentation = values.get("electrical_voltage"), values.get("instrument_voltage")
    if not isinstance(electrical, QuantityV1) or not isinstance(instrumentation, QuantityV1):
        raise RuleIndeterminate("source_incomplete")
    result = equal(electrical, instrumentation)
    if result.outcome == "indeterminate":
        raise RuleIndeterminate(result.reason or "unsupported_value")
    if result.outcome == "violated":
        return _finding(values, rule_id=BATCH_TWO_RULE_IDS[1], category="inconsistent", subcode="ei.motor_instrument_voltage", severity="major")
    return ()


def _canonical_edge(edge: ExplicitRelationshipV1) -> None:
    if edge.relationship_owner_kind != "engineering_relationship" or edge.aggregate_version < 1:
        raise ValueError("invalid_request")
    for value in (edge.relationship_id, edge.source_object_id, edge.target_object_id):
        try:
            if str(UUID(value)) != value:
                raise ValueError("invalid_request")
        except ValueError as error:
            raise ValueError("invalid_request") from error


def _cable_path_outcome(values: Mapping) -> str:
    edges = values.get("edges")
    object_types = values.get("object_types")
    start = values.get("signal_endpoint_id")
    target = values.get("supply_terminal_id")
    if not isinstance(edges, tuple) or not isinstance(object_types, Mapping):
        raise ValueError("invalid_request")
    if not isinstance(start, str) or not isinstance(target, str):
        raise ValueError("invalid_request")
    try:
        if str(UUID(start)) != start or str(UUID(target)) != target:
            raise ValueError("invalid_request")
    except ValueError as error:
        raise ValueError("invalid_request") from error
    if len(edges) > LIMITS["edges"] or len(object_types) > LIMITS["nodes"]:
        raise RuleIndeterminate("resource_limit_exceeded")
    if len({edge.relationship_id for edge in edges}) != len(edges):
        raise RuleIndeterminate("source_ambiguous")
    adjacency: dict[str, list[ExplicitRelationshipV1]] = {}
    for edge in edges:
        if not isinstance(edge, ExplicitRelationshipV1):
            raise ValueError("invalid_request")
        _canonical_edge(edge)
        adjacency.setdefault(edge.source_object_id, []).append(edge)
    # A graph cycle is not a missing path.  The frozen contract treats it as
    # ambiguous topology and never derives a partial path result from it.
    visiting, visited = set(), set()
    def has_cycle(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for edge in adjacency.get(node, ()):
            if has_cycle(edge.target_object_id):
                return True
        visiting.remove(node)
        visited.add(node)
        return False
    if any(has_cycle(node) for node in tuple(adjacency)):
        raise RuleIndeterminate("source_ambiguous")
    if any(len(outgoing) > LIMITS["fanout"] for outgoing in adjacency.values()):
        raise RuleIndeterminate("resource_limit_exceeded")
    if object_types.get(start) not in {"transmitter", "analyzer", "flowmeter"}:
        raise RuleIndeterminate("source_ambiguous")
    for first in sorted(adjacency.get(start, ()), key=lambda item: UUID(item.relationship_id).bytes):
        if (first.relationship_family, first.relationship_type) != ("instrumentation", "transmits_to"):
            continue
        if object_types.get(first.target_object_id) != "junction_box":
            continue
        for second in sorted(adjacency.get(first.target_object_id, ()), key=lambda item: UUID(item.relationship_id).bytes):
            if second.relationship_family != "physical" or second.relationship_type not in {"connected_through", "terminated_at"}:
                continue
            if object_types.get(second.target_object_id) != "electrical_cable":
                continue
            for third in sorted(adjacency.get(second.target_object_id, ()), key=lambda item: UUID(item.relationship_id).bytes):
                if (third.relationship_family, third.relationship_type) != ("electrical", "powered_by"):
                    continue
                if third.target_object_id != target:
                    continue
                if object_types.get(target) in {"electrical_power_source", "transformer", "switchgear", "mcc", "electrical_panel"}:
                    return "satisfied"
    return "violated"


def cable_jb_path(_request, values):
    if not isinstance(values, Mapping):
        raise ValueError("invalid_request")
    _require_applicability(values, BATCH_TWO_INTERFACE_APPLICABILITY_ID)
    if values.get("relationship_grammar_id") != BATCH_TWO_RELATIONSHIP_GRAMMAR_ID or values.get("path_id") != BATCH_TWO_PATH_ID:
        raise ValueError("invalid_request")
    if values.get("complete") is not True:
        raise RuleIndeterminate("source_incomplete")
    if _cable_path_outcome(values) == "violated":
        return _finding(values, rule_id=BATCH_TWO_RULE_IDS[2], category="dependency", subcode="ei.cable_jb_path", severity="warning")
    return ()


def handoff_complete(_request, values):
    if not isinstance(values, Mapping):
        raise ValueError("invalid_request")
    _require_applicability(values, BATCH_TWO_HANDOFF_APPLICABILITY_ID)
    supplied = values.get("declaration_ids", ())
    if not isinstance(supplied, tuple) or len(set(supplied)) != len(supplied):
        raise RuleIndeterminate("source_ambiguous")
    if values.get("complete") is not True:
        raise RuleIndeterminate("source_incomplete")
    if values.get("commitment_current_use") is not True or values.get("commitment_state") in {"disputed", "superseded"} or values.get("reassessment_needed") is True:
        raise RuleIndeterminate("commitment_changed")
    if values.get("provider_workspace_id") != values.get("occurrence_provider_workspace_id") or values.get("consumer_workspace_id") != values.get("occurrence_consumer_workspace_id"):
        raise RuleIndeterminate("source_ambiguous")
    result = set_contains(supplied, BATCH_TWO_REQUIRED_DECLARATIONS)
    if result.outcome == "violated":
        return _finding(values, rule_id=BATCH_TWO_RULE_IDS[3], category="incomplete_handoff", subcode="ei.handoff_complete", severity="major")
    if result.outcome == "indeterminate":
        raise RuleIndeterminate(result.reason or "unsupported_value")
    return ()


BATCH_TWO_RULE_HANDLERS = MappingProxyType({
    "xdi.ei.instrument_power_required.v1": instrument_power_required,
    "xdi.ei.motor_instrument_voltage.v1": motor_instrument_voltage,
    "xdi.ei.cable_jb_path.v1": cable_jb_path,
    "xdi.ei.handoff_complete.v1": handoff_complete,
})


def _batch_three_identity(values: Mapping, *, rule_id: str, category: str, subcode: str) -> FindingIdentityInputV1:
    identity = values.get("identity")
    if not isinstance(identity, FindingIdentityInputV1):
        raise ValueError("invalid_request")
    declaration = batch_three_rule_definition(rule_id)
    interface = load_batch_three_definition_set().interface_definitions[1]
    if identity.rule_id != rule_id or identity.rule_version != BATCH_THREE_VERSION:
        raise ValueError("invalid_request")
    if identity.rule_digest != declaration.digest or identity.interface_digest != interface.digest:
        raise ValueError("invalid_request")
    if identity.interface_definition_id != BATCH_THREE_INTERFACE_ID or identity.interface_version != BATCH_THREE_VERSION:
        raise ValueError("invalid_request")
    if identity.category != category or identity.subcode != subcode:
        raise ValueError("invalid_request")
    return identity


def _batch_three_finding(values: Mapping, *, rule_id: str, category: str, subcode: str):
    return ((_batch_three_identity(values, rule_id=rule_id, category=category, subcode=subcode), "major", "violated"),)


def _batch_three_complete(values: Mapping, applicability: str) -> None:
    if values.get("applicability_id") != applicability:
        raise ValueError("invalid_request")
    if values.get("complete") is not True:
        raise RuleIndeterminate("source_incomplete")


def signal_type(_request, values):
    if not isinstance(values, Mapping):
        raise ValueError("invalid_request")
    _batch_three_complete(values, BATCH_THREE_APPLICABILITY_ID)
    instrumentation, control = values.get("instrumentation_signal_type"), values.get("control_io_type")
    if not isinstance(instrumentation, str) or not isinstance(control, str):
        raise RuleIndeterminate("source_incomplete")
    result = enum_map_equal(instrumentation, control, {
        "signal_current": "analog_current", "signal_voltage": "analog_voltage",
        "signal_discrete": "digital_dry_contact", "signal_pulse": "pulse",
    })
    if result.outcome == "indeterminate":
        raise RuleIndeterminate(result.reason or "unsupported_value")
    if result.outcome == "violated":
        return _batch_three_finding(values, rule_id=BATCH_THREE_RULE_IDS[0], category="inconsistent", subcode="ic.signal_type")
    return ()


def signal_range(_request, values):
    if not isinstance(values, Mapping):
        raise ValueError("invalid_request")
    _batch_three_complete(values, BATCH_THREE_APPLICABILITY_ID)
    instrumentation, accepted = values.get("instrumentation_range"), values.get("control_accepted_range")
    if not isinstance(instrumentation, RangeV1) or not isinstance(accepted, RangeV1):
        raise RuleIndeterminate("source_incomplete")
    result = range_contains(accepted, instrumentation)
    if result.outcome == "indeterminate":
        raise RuleIndeterminate(result.reason or "unsupported_value")
    if result.outcome == "violated":
        return _batch_three_finding(values, rule_id=BATCH_THREE_RULE_IDS[1], category="inconsistent", subcode="ic.signal_range")
    return ()


def valve_command_feedback(_request, values):
    if not isinstance(values, Mapping):
        raise ValueError("invalid_request")
    _batch_three_complete(values, BATCH_THREE_APPLICABILITY_ID)
    if values.get("path_id") != BATCH_THREE_PATH_ID:
        raise ValueError("invalid_request")
    edges, controller, valve, feedback_target = (
        values.get("edges"), values.get("controller_id"), values.get("valve_id"), values.get("feedback_target_id"),
    )
    if not isinstance(edges, tuple) or not all(isinstance(item, ExplicitRelationshipV1) for item in edges):
        raise RuleIndeterminate("source_ambiguous")
    if len(edges) > LIMITS["edges"] or len({edge.relationship_id for edge in edges}) != len(edges):
        raise RuleIndeterminate("resource_limit_exceeded" if len(edges) > LIMITS["edges"] else "source_ambiguous")
    for edge in edges:
        _canonical_edge(edge)
    if not all(isinstance(value, str) for value in (controller, valve, feedback_target)):
        raise ValueError("invalid_request")
    try:
        if any(str(UUID(value)) != value for value in (controller, valve, feedback_target)):
            raise ValueError("invalid_request")
    except ValueError as error:
        raise ValueError("invalid_request") from error
    adjacency = {}
    for edge in edges:
        adjacency.setdefault(edge.source_object_id, []).append(edge.target_object_id)
    visited, visiting = set(), set()
    def cyclic(node):
        if node in visiting: return True
        if node in visited: return False
        visiting.add(node)
        if any(cyclic(target) for target in adjacency.get(node, ())): return True
        visiting.remove(node); visited.add(node)
        return False
    if any(cyclic(node) for node in tuple(adjacency)):
        raise RuleIndeterminate("source_ambiguous")
    command = any(
        edge.source_object_id == controller and edge.target_object_id == valve
        and edge.relationship_type == "commands"
        for edge in edges
    )
    feedback = any(
        edge.source_object_id == valve and edge.target_object_id == feedback_target
        and edge.relationship_type in {"provides_feedback_to", "sends_signal_to"}
        for edge in edges
    )
    if not command or not feedback:
        return _batch_three_finding(values, rule_id=BATCH_THREE_RULE_IDS[2], category="dependency", subcode="ic.valve_command_feedback")
    return ()


def commitment_fulfilment(_request, values):
    if not isinstance(values, Mapping):
        raise ValueError("invalid_request")
    _batch_three_complete(values, BATCH_THREE_HANDOFF_APPLICABILITY_ID)
    if values.get("commitment_current_use") is not True or values.get("commitment_changed") is True:
        raise RuleIndeterminate("commitment_changed")
    state, evidence = values.get("commitment_state"), values.get("evidence_presence")
    if state not in {"fulfilled_for_stated_use", "information_provided"}:
        raise RuleIndeterminate("source_ambiguous")
    evidence_result = present(evidence, True)
    if evidence_result.outcome == "indeterminate":
        raise RuleIndeterminate(evidence_result.reason or "source_incomplete")
    if state != "fulfilled_for_stated_use" or evidence_result.outcome == "violated":
        return _batch_three_finding(values, rule_id=BATCH_THREE_RULE_IDS[3], category="unfulfilled_commitment", subcode="ic.commitment_fulfilment")
    return ()


BATCH_THREE_RULE_HANDLERS = MappingProxyType({
    BATCH_THREE_RULE_IDS[0]: signal_type,
    BATCH_THREE_RULE_IDS[1]: signal_range,
    BATCH_THREE_RULE_IDS[2]: valve_command_feedback,
    BATCH_THREE_RULE_IDS[3]: commitment_fulfilment,
})
