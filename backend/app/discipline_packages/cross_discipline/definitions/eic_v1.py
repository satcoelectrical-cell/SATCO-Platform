from __future__ import annotations

from ..canonical import digest
from ..conformance_manifest import (
    BATCH_ONE_VECTOR_IDS, CUMULATIVE_BATCH_TWO_VECTOR_IDS,
    CUMULATIVE_BATCH_THREE_VECTOR_IDS, CUMULATIVE_BATCH_FOUR_VECTOR_IDS,
)
from ..contracts import (
    BATCH_TWO_EVALUATOR_CAPABILITY_ID, BATCH_TWO_HANDOFF_APPLICABILITY_ID,
    BATCH_TWO_INTERFACE_APPLICABILITY_ID, BATCH_TWO_INTERFACE_ID,
    BATCH_TWO_INTERFACE_NAME, BATCH_TWO_INDETERMINATE_REASONS,
    BATCH_TWO_PATH_ID, BATCH_TWO_PROJECTIONS, BATCH_TWO_RELATIONSHIP_GRAMMAR_ID,
    BATCH_TWO_RULE_IDS, BATCH_TWO_VERSION, CANONICALIZATION_ID,
    DEFINITION_SET_ID, DefinitionSetV1, InterfaceDefinitionV1, LIMITS,
    PROFILE_ID, ProjectionDefinitionV1, REGISTRY_RELEASE_ID, RELEASE_ID, RuleDefinitionV1,
)


COMPARISON_IDS = (
    "applicable_if", "disagrees", "enum_map_equal", "equal", "not_equal",
    "present", "range_contains", "range_overlaps", "set_contains",
    "set_equal", "stale_after", "within_absolute_tolerance",
)
SUPPORTED_COMBINATIONS = ("cross.ec.v1", "cross.ei.v1", "cross.eic.v1", "cross.ic.v1")

BATCH_THREE_INTERFACE_ID = "cross.interface.ic.signal_control.v1"
BATCH_THREE_VERSION = "1.0.0"
BATCH_THREE_INTERFACE_NAME = "instrumentation_control_signal_control"
BATCH_THREE_APPLICABILITY_ID = "xdi.app.interface_assessment.v1"
BATCH_THREE_HANDOFF_APPLICABILITY_ID = "xdi.app.current_handoff.v1"
BATCH_THREE_EVALUATOR_CAPABILITY_ID = "cross_discipline.deterministic.v1"
BATCH_THREE_RULE_IDS = (
    "xdi.ic.signal_type.v1", "xdi.ic.signal_range.v1",
    "xdi.ic.valve_command_feedback.v1", "xdi.ic.commitment_fulfilment.v1",
)
BATCH_THREE_PROJECTIONS = (
    ProjectionDefinitionV1("xdi.proj.i.signal.v1", "xdi.schema.i.signal.v1", "xdi.adapter.i.signal.v1", "xdi.selector.i.signal.v1", "xdi.complete.i.signal.v1", "engineering_object"),
    ProjectionDefinitionV1("xdi.proj.c.io.v1", "xdi.schema.c.io.v1", "xdi.adapter.c.io.v1", "xdi.selector.c.io.v1", "xdi.complete.c.io.v1", "engineering_object"),
    ProjectionDefinitionV1("xdi.proj.c.command_status.v1", "xdi.schema.c.command_status.v1", "xdi.adapter.c.command_status.v1", "xdi.selector.c.command_status.v1", "xdi.complete.c.command_status.v1", "engineering_object"),
    ProjectionDefinitionV1("xdi.proj.commitment.v1", "xdi.schema.commitment.v1", "xdi.adapter.commitment.v1", "xdi.selector.commitment.v1", "xdi.complete.commitment.v1", "interface_commitment"),
)
BATCH_THREE_PROJECTION_IDS = tuple(item.projection_id for item in BATCH_THREE_PROJECTIONS)
BATCH_THREE_PATH_ID = "xdi.path.ic.valve_feedback.v1"
BATCH_THREE_INDETERMINATE_REASONS = (
    "protected_not_found", "source_incomplete", "source_ambiguous", "source_changed",
    "unsupported_value", "resource_limit_exceeded", "commitment_changed", "binding_changed",
)

BATCH_FOUR_INTERFACE_ID = "cross.interface.ec.command_power.v1"
BATCH_FOUR_VERSION = "1.0.0"
BATCH_FOUR_INTERFACE_NAME = "electrical_control_command_power"
BATCH_FOUR_APPLICABILITY_ID = "xdi.app.interface_assessment.v1"
BATCH_FOUR_HANDOFF_APPLICABILITY_ID = "xdi.app.current_handoff.v1"
BATCH_FOUR_EVALUATOR_CAPABILITY_ID = "cross_discipline.deterministic.v1"
BATCH_FOUR_RULE_IDS = (
    "xdi.ec.mcc_command_status.v1", "xdi.ec.cabinet_power_path.v1",
    "xdi.ec.source_freshness.v1", "xdi.ec.commitment_dispute.v1",
)
BATCH_FOUR_PROJECTIONS = (
    ProjectionDefinitionV1("xdi.proj.e.power_endpoint.v1", "xdi.schema.e.power_endpoint.v1", "xdi.adapter.e.power_endpoint.v1", "xdi.selector.e.power_endpoint.v1", "xdi.complete.e.power_endpoint.v1", "engineering_object"),
    ProjectionDefinitionV1("xdi.proj.c.command_status.v1", "xdi.schema.c.command_status.v1", "xdi.adapter.c.command_status.v1", "xdi.selector.c.command_status.v1", "xdi.complete.c.command_status.v1", "engineering_object"),
    ProjectionDefinitionV1("xdi.proj.c.cabinet_power.v1", "xdi.schema.c.cabinet_power.v1", "xdi.adapter.c.cabinet_power.v1", "xdi.selector.c.cabinet_power.v1", "xdi.complete.c.cabinet_power.v1", "engineering_object"),
    ProjectionDefinitionV1("xdi.proj.source_freshness.v1", "xdi.schema.source_freshness.v1", "xdi.adapter.source_freshness.v1", "xdi.selector.source_freshness.v1", "xdi.complete.source_freshness.v1", "engineering_object"),
    ProjectionDefinitionV1("xdi.proj.commitment.v1", "xdi.schema.commitment.v1", "xdi.adapter.commitment.v1", "xdi.selector.commitment.v1", "xdi.complete.commitment.v1", "interface_commitment"),
)
BATCH_FOUR_PROJECTION_IDS = tuple(item.projection_id for item in BATCH_FOUR_PROJECTIONS)
BATCH_FOUR_PATH_ID = "xdi.path.ec.cabinet_power.v1"
BATCH_FOUR_INDETERMINATE_REASONS = BATCH_THREE_INDETERMINATE_REASONS


def load_batch_one_definition_set() -> DefinitionSetV1:
    # Pair/integrated production rules remain absent until Batches 2-5.
    body = {
        "schema_version": 1, "definition_set_id": DEFINITION_SET_ID,
        "version": "1.0.0", "release_id": RELEASE_ID,
        "registry_release_id": REGISTRY_RELEASE_ID, "profile_id": PROFILE_ID,
        "canonicalization_id": CANONICALIZATION_ID,
        "limits_profile": dict(LIMITS),
        "supported_combinations": SUPPORTED_COMBINATIONS,
        "comparison_ids": COMPARISON_IDS, "rule_ids": (),
        "conformance_vector_ids": BATCH_ONE_VECTOR_IDS,
    }
    return DefinitionSetV1(**body, digest=digest(body))


def validate_batch_one_definition_set(definition: DefinitionSetV1) -> None:
    if definition != load_batch_one_definition_set():
        raise ValueError("untrusted or modified cross-discipline definition set")
    if definition.rule_ids:
        raise ValueError("Batch-1 must not register pair or integrated rules")


def load_batch_two_definition_set() -> DefinitionSetV1:
    """Cumulative retained V1 release with only the four accepted E↔I rules."""
    rule_inputs = (
        (BATCH_TWO_RULE_IDS[0], ("xdi.proj.e.power_endpoint.v1", "xdi.proj.i.instrument_power.v1"), BATCH_TWO_INTERFACE_APPLICABILITY_ID, "present", "missing", "ei.instrument_power_required", "major"),
        (BATCH_TWO_RULE_IDS[1], ("xdi.proj.e.power_endpoint.v1", "xdi.proj.i.instrument_power.v1"), BATCH_TWO_INTERFACE_APPLICABILITY_ID, "equal", "inconsistent", "ei.motor_instrument_voltage", "major"),
        (BATCH_TWO_RULE_IDS[2], ("xdi.proj.i.signal.v1", "xdi.proj.e.cable_supply.v1"), BATCH_TWO_INTERFACE_APPLICABILITY_ID, BATCH_TWO_PATH_ID, "dependency", "ei.cable_jb_path", "warning"),
        (BATCH_TWO_RULE_IDS[3], ("xdi.proj.i.handoff.v1", "xdi.proj.e.power_endpoint.v1", "xdi.proj.e.cable_supply.v1", "xdi.proj.i.instrument_power.v1", "xdi.proj.i.signal.v1"), BATCH_TWO_HANDOFF_APPLICABILITY_ID, "set_contains", "incomplete_handoff", "ei.handoff_complete", "major"),
    )
    rules = []
    for rule_id, projections, applicability, comparison, category, subcode, severity in rule_inputs:
        rule_body = {
            "rule_id": rule_id, "version": BATCH_TWO_VERSION,
            "interface_definition_id": BATCH_TWO_INTERFACE_ID,
            "interface_version": BATCH_TWO_VERSION,
            "ordered_projection_ids": projections,
            "applicability_id": applicability, "comparison_id": comparison,
            "category": category, "subcode": subcode, "severity": severity,
            "indeterminate_reasons": BATCH_TWO_INDETERMINATE_REASONS,
            "evaluator_capability_id": BATCH_TWO_EVALUATOR_CAPABILITY_ID,
        }
        rules.append(RuleDefinitionV1(**rule_body, digest=digest(rule_body)))
    interface_body = {
        "interface_definition_id": BATCH_TWO_INTERFACE_ID,
        "version": BATCH_TWO_VERSION, "name": BATCH_TWO_INTERFACE_NAME,
        "provider_discipline": "electrical",
        "consumer_discipline": "instrumentation", "rule_ids": BATCH_TWO_RULE_IDS,
    }
    interface = InterfaceDefinitionV1(**interface_body, digest=digest(interface_body))
    body = {
        "schema_version": 1, "definition_set_id": DEFINITION_SET_ID,
        "version": "1.0.0", "release_id": RELEASE_ID,
        "registry_release_id": REGISTRY_RELEASE_ID, "profile_id": PROFILE_ID,
        "canonicalization_id": CANONICALIZATION_ID,
        "limits_profile": dict(LIMITS),
        "supported_combinations": SUPPORTED_COMBINATIONS,
        "comparison_ids": COMPARISON_IDS, "rule_ids": BATCH_TWO_RULE_IDS,
        "conformance_vector_ids": CUMULATIVE_BATCH_TWO_VECTOR_IDS,
        "interface_definitions": (interface,),
        "projection_definitions": BATCH_TWO_PROJECTIONS,
        "relationship_grammar_ids": (BATCH_TWO_RELATIONSHIP_GRAMMAR_ID,),
        "path_ids": (BATCH_TWO_PATH_ID,), "rule_definitions": tuple(rules),
    }
    return DefinitionSetV1(**body, digest=digest(body))


def validate_batch_two_definition_set(definition: DefinitionSetV1) -> None:
    if definition != load_batch_two_definition_set():
        raise ValueError("untrusted or modified Batch-2 definition set")
    if definition.rule_ids != BATCH_TWO_RULE_IDS or len(definition.conformance_vector_ids) != 59:
        raise ValueError("Batch-2 definition scope mismatch")
    if len(definition.interface_definitions) != 1 or len(definition.projection_definitions) != 5:
        raise ValueError("Batch-2 nested definition scope mismatch")
    if tuple(item.rule_id for item in definition.rule_definitions) != BATCH_TWO_RULE_IDS:
        raise ValueError("Batch-2 rule declaration mismatch")


def batch_two_rule_definition(rule_id: str) -> RuleDefinitionV1:
    """Resolve only an exact compiled Batch-2 rule; no dynamic fallback."""
    for declaration in load_batch_two_definition_set().rule_definitions:
        if declaration.rule_id == rule_id:
            return declaration
    raise ValueError("artifact_unavailable")


def load_batch_three_definition_set() -> DefinitionSetV1:
    """Cumulative retained V1 release with exactly the four accepted I↔C rules."""
    rule_inputs = (
        (BATCH_THREE_RULE_IDS[0], ("xdi.proj.i.signal.v1", "xdi.proj.c.io.v1"), BATCH_THREE_APPLICABILITY_ID, "enum_map_equal", "inconsistent", "ic.signal_type", "major"),
        (BATCH_THREE_RULE_IDS[1], ("xdi.proj.i.signal.v1", "xdi.proj.c.io.v1"), BATCH_THREE_APPLICABILITY_ID, "range_contains", "inconsistent", "ic.signal_range", "major"),
        (BATCH_THREE_RULE_IDS[2], ("xdi.proj.i.signal.v1", "xdi.proj.c.command_status.v1"), BATCH_THREE_APPLICABILITY_ID, BATCH_THREE_PATH_ID, "dependency", "ic.valve_command_feedback", "major"),
        (BATCH_THREE_RULE_IDS[3], ("xdi.proj.commitment.v1",), BATCH_THREE_HANDOFF_APPLICABILITY_ID, "equal", "unfulfilled_commitment", "ic.commitment_fulfilment", "major"),
    )
    rules = []
    for rule_id, projections, applicability, comparison, category, subcode, severity in rule_inputs:
        rule_body = {
            "rule_id": rule_id, "version": BATCH_THREE_VERSION,
            "interface_definition_id": BATCH_THREE_INTERFACE_ID,
            "interface_version": BATCH_THREE_VERSION, "ordered_projection_ids": projections,
            "applicability_id": applicability, "comparison_id": comparison,
            "category": category, "subcode": subcode, "severity": severity,
            "indeterminate_reasons": BATCH_THREE_INDETERMINATE_REASONS,
            "evaluator_capability_id": BATCH_THREE_EVALUATOR_CAPABILITY_ID,
        }
        rules.append(RuleDefinitionV1(**rule_body, digest=digest(rule_body)))
    interface_body = {"interface_definition_id": BATCH_THREE_INTERFACE_ID,
        "version": BATCH_THREE_VERSION, "name": BATCH_THREE_INTERFACE_NAME,
        "provider_discipline": "instrumentation", "consumer_discipline": "control_automation",
        "rule_ids": BATCH_THREE_RULE_IDS}
    interface = InterfaceDefinitionV1(**interface_body, digest=digest(interface_body))
    body = {
        "schema_version": 1, "definition_set_id": DEFINITION_SET_ID, "version": "1.0.0",
        "release_id": RELEASE_ID, "registry_release_id": REGISTRY_RELEASE_ID, "profile_id": PROFILE_ID,
        "canonicalization_id": CANONICALIZATION_ID, "limits_profile": dict(LIMITS),
        "supported_combinations": SUPPORTED_COMBINATIONS, "comparison_ids": COMPARISON_IDS,
        "rule_ids": BATCH_TWO_RULE_IDS + BATCH_THREE_RULE_IDS,
        "conformance_vector_ids": CUMULATIVE_BATCH_THREE_VECTOR_IDS,
        "interface_definitions": (load_batch_two_definition_set().interface_definitions[0], interface),
        "projection_definitions": BATCH_TWO_PROJECTIONS + tuple(
            item for item in BATCH_THREE_PROJECTIONS
            if item.projection_id not in {existing.projection_id for existing in BATCH_TWO_PROJECTIONS}
        ),
        "relationship_grammar_ids": (BATCH_TWO_RELATIONSHIP_GRAMMAR_ID,),
        "path_ids": (BATCH_TWO_PATH_ID, BATCH_THREE_PATH_ID),
        "rule_definitions": load_batch_two_definition_set().rule_definitions + tuple(rules),
    }
    return DefinitionSetV1(**body, digest=digest(body))


def validate_batch_three_definition_set(definition: DefinitionSetV1) -> None:
    if definition != load_batch_three_definition_set():
        raise ValueError("untrusted or modified Batch-3 definition set")
    if definition.rule_ids != BATCH_TWO_RULE_IDS + BATCH_THREE_RULE_IDS or len(definition.conformance_vector_ids) != 67:
        raise ValueError("Batch-3 definition scope mismatch")
    if len(definition.projection_definitions) != 8 or tuple(item.rule_id for item in definition.rule_definitions)[-4:] != BATCH_THREE_RULE_IDS:
        raise ValueError("Batch-3 rule declaration mismatch")


def batch_three_rule_definition(rule_id: str) -> RuleDefinitionV1:
    for declaration in load_batch_three_definition_set().rule_definitions:
        if declaration.rule_id == rule_id and rule_id in BATCH_THREE_RULE_IDS:
            return declaration
    raise ValueError("artifact_unavailable")


def load_batch_four_definition_set() -> DefinitionSetV1:
    """Cumulative release with exactly the accepted Electrical ↔ C&A rules."""
    rule_inputs = (
        (BATCH_FOUR_RULE_IDS[0], ("xdi.proj.e.power_endpoint.v1", "xdi.proj.c.command_status.v1"), BATCH_FOUR_APPLICABILITY_ID, "present", "incomplete_handoff", "ec.mcc_command_status", "major"),
        (BATCH_FOUR_RULE_IDS[1], ("xdi.proj.c.cabinet_power.v1", "xdi.proj.e.power_endpoint.v1"), BATCH_FOUR_APPLICABILITY_ID, BATCH_FOUR_PATH_ID, "dependency", "ec.cabinet_power_path", "major"),
        (BATCH_FOUR_RULE_IDS[2], ("xdi.proj.source_freshness.v1",), BATCH_FOUR_APPLICABILITY_ID, "stale_after", "stale", "ec.source_freshness", "warning"),
        (BATCH_FOUR_RULE_IDS[3], ("xdi.proj.commitment.v1",), BATCH_FOUR_HANDOFF_APPLICABILITY_ID, "equal", "disputed", "ec.commitment_dispute", "major"),
    )
    rules = []
    for rule_id, projections, applicability, comparison, category, subcode, severity in rule_inputs:
        rule_body = {"rule_id": rule_id, "version": BATCH_FOUR_VERSION,
            "interface_definition_id": BATCH_FOUR_INTERFACE_ID, "interface_version": BATCH_FOUR_VERSION,
            "ordered_projection_ids": projections, "applicability_id": applicability,
            "comparison_id": comparison, "category": category, "subcode": subcode,
            "severity": severity, "indeterminate_reasons": BATCH_FOUR_INDETERMINATE_REASONS,
            "evaluator_capability_id": BATCH_FOUR_EVALUATOR_CAPABILITY_ID}
        rules.append(RuleDefinitionV1(**rule_body, digest=digest(rule_body)))
    interface_body = {"interface_definition_id": BATCH_FOUR_INTERFACE_ID, "version": BATCH_FOUR_VERSION,
        "name": BATCH_FOUR_INTERFACE_NAME, "provider_discipline": "electrical",
        "consumer_discipline": "control_automation", "rule_ids": BATCH_FOUR_RULE_IDS}
    interface = InterfaceDefinitionV1(**interface_body, digest=digest(interface_body))
    retained = load_batch_three_definition_set()
    existing = {item.projection_id for item in retained.projection_definitions}
    body = {"schema_version": 1, "definition_set_id": DEFINITION_SET_ID, "version": "1.0.0",
        "release_id": RELEASE_ID, "registry_release_id": REGISTRY_RELEASE_ID, "profile_id": PROFILE_ID,
        "canonicalization_id": CANONICALIZATION_ID, "limits_profile": dict(LIMITS),
        "supported_combinations": SUPPORTED_COMBINATIONS, "comparison_ids": COMPARISON_IDS,
        "rule_ids": retained.rule_ids + BATCH_FOUR_RULE_IDS,
        "conformance_vector_ids": CUMULATIVE_BATCH_FOUR_VECTOR_IDS,
        "interface_definitions": retained.interface_definitions + (interface,),
        "projection_definitions": retained.projection_definitions + tuple(item for item in BATCH_FOUR_PROJECTIONS if item.projection_id not in existing),
        "relationship_grammar_ids": retained.relationship_grammar_ids,
        "path_ids": retained.path_ids + (BATCH_FOUR_PATH_ID,),
        "rule_definitions": retained.rule_definitions + tuple(rules)}
    return DefinitionSetV1(**body, digest=digest(body))


def validate_batch_four_definition_set(definition: DefinitionSetV1) -> None:
    if definition != load_batch_four_definition_set():
        raise ValueError("untrusted or modified Batch-4 definition set")
    if definition.rule_ids[-4:] != BATCH_FOUR_RULE_IDS or len(definition.conformance_vector_ids) != 75:
        raise ValueError("Batch-4 definition scope mismatch")


def batch_four_rule_definition(rule_id: str) -> RuleDefinitionV1:
    for declaration in load_batch_four_definition_set().rule_definitions:
        if declaration.rule_id == rule_id and rule_id in BATCH_FOUR_RULE_IDS:
            return declaration
    raise ValueError("artifact_unavailable")
