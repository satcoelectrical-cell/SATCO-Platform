from __future__ import annotations

from ..canonical import digest
from ..conformance_manifest import BATCH_ONE_VECTOR_IDS, CUMULATIVE_BATCH_TWO_VECTOR_IDS
from ..contracts import (
    BATCH_TWO_EVALUATOR_CAPABILITY_ID, BATCH_TWO_HANDOFF_APPLICABILITY_ID,
    BATCH_TWO_INTERFACE_APPLICABILITY_ID, BATCH_TWO_INTERFACE_ID,
    BATCH_TWO_INTERFACE_NAME, BATCH_TWO_INDETERMINATE_REASONS,
    BATCH_TWO_PATH_ID, BATCH_TWO_PROJECTIONS, BATCH_TWO_RELATIONSHIP_GRAMMAR_ID,
    BATCH_TWO_RULE_IDS, BATCH_TWO_VERSION, CANONICALIZATION_ID,
    DEFINITION_SET_ID, DefinitionSetV1, InterfaceDefinitionV1, LIMITS,
    PROFILE_ID, REGISTRY_RELEASE_ID, RELEASE_ID, RuleDefinitionV1,
)


COMPARISON_IDS = (
    "applicable_if", "disagrees", "enum_map_equal", "equal", "not_equal",
    "present", "range_contains", "range_overlaps", "set_contains",
    "set_equal", "stale_after", "within_absolute_tolerance",
)
SUPPORTED_COMBINATIONS = ("cross.ec.v1", "cross.ei.v1", "cross.eic.v1", "cross.ic.v1")


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
