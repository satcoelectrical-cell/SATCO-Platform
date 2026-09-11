"""Framework-free frozen contracts for the PATCH-053 shared kernel."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType
from typing import Any, Literal, Mapping
import re
import unicodedata
from urllib.parse import unquote_to_bytes
from uuid import UUID


CANONICALIZATION_ID = "cross_discipline.canonical_json.v1"
EVALUATOR_ID = "cross_discipline.evaluator.v1"
LIMITS_PROFILE_ID = "cross_discipline.eic.limits.v1"
DEFINITION_SET_ID = "cross_discipline.eic.v1"
RULE_SET_ID = "cross_discipline.eic.rules.v1"
RELEASE_ID = "patch-053.eic-intelligence-v1"
REGISTRY_RELEASE_ID = "patch-052.eic-v1"
PROFILE_ID = "commercial_v1.eic@1.0.0"

BATCH_TWO_INTERFACE_ID = "cross.interface.ei.power_handoff.v1"
BATCH_TWO_VERSION = "1.0.0"
BATCH_TWO_INTERFACE_NAME = "electrical_instrumentation_power_handoff"
BATCH_TWO_INTERFACE_APPLICABILITY_ID = "xdi.app.interface_assessment.v1"
BATCH_TWO_HANDOFF_APPLICABILITY_ID = "xdi.app.current_handoff.v1"
BATCH_TWO_EVALUATOR_CAPABILITY_ID = "cross_discipline.deterministic.v1"
BATCH_TWO_RULE_IDS = (
    "xdi.ei.instrument_power_required.v1",
    "xdi.ei.motor_instrument_voltage.v1",
    "xdi.ei.cable_jb_path.v1",
    "xdi.ei.handoff_complete.v1",
)
BATCH_TWO_PROJECTION_IDS = (
    "xdi.proj.e.power_endpoint.v1", "xdi.proj.e.cable_supply.v1",
    "xdi.proj.i.instrument_power.v1", "xdi.proj.i.signal.v1",
    "xdi.proj.i.handoff.v1",
)
BATCH_TWO_CONTEXT_IDS = (
    "electrical.system_voltage_basis.input", "electrical.source_feeder_basis.input",
    "instrumentation.design_conditions.input", "instrumentation.signal_basis.input",
)
BATCH_TWO_EVIDENCE_IDS = (
    "electrical.voltage_source_basis_evidence.input",
    "instrumentation.range_condition_basis_evidence.input",
)
BATCH_TWO_REQUIRED_DECLARATIONS = BATCH_TWO_CONTEXT_IDS + BATCH_TWO_EVIDENCE_IDS
BATCH_TWO_SELECTOR_PREFIX = "xdi.sel.v1"
BATCH_TWO_RELATIONSHIP_GRAMMAR_ID = "xdi.grammar.ei.cable_jb_supply.v1"
BATCH_TWO_PATH_ID = "xdi.path.ei.cable_jb_supply.v1"
BATCH_TWO_RELATIONSHIP_PATH = (
    ("instrumentation", "transmits_to"),
    ("physical", ("connected_through", "terminated_at")),
    ("electrical", "powered_by"),
)
BATCH_TWO_INDETERMINATE_REASONS = (
    "protected_not_found", "source_incomplete", "source_ambiguous",
    "source_changed", "unsupported_value", "resource_limit_exceeded",
    "commitment_changed", "binding_changed",
)


@dataclass(frozen=True, slots=True)
class ProjectionDefinitionV1:
    projection_id: str
    schema_id: str
    adapter_capability_id: str
    selector_id: str
    completeness_id: str
    owner_kind: str
    version: str = BATCH_TWO_VERSION


@dataclass(frozen=True, slots=True)
class InterfaceDefinitionV1:
    interface_definition_id: str
    version: str
    name: str
    provider_discipline: str
    consumer_discipline: str
    rule_ids: tuple[str, ...]
    digest: str


@dataclass(frozen=True, slots=True)
class RuleDefinitionV1:
    rule_id: str
    version: str
    interface_definition_id: str
    interface_version: str
    ordered_projection_ids: tuple[str, ...]
    applicability_id: str
    comparison_id: str
    category: str
    subcode: str
    severity: str
    indeterminate_reasons: tuple[str, ...]
    evaluator_capability_id: str
    digest: str


@dataclass(frozen=True, slots=True)
class ExplicitRelationshipV1:
    """One authorized, versioned, forward canonical owner edge."""

    relationship_owner_kind: str
    relationship_id: str
    aggregate_version: int
    relationship_family: str
    relationship_type: str
    source_object_id: str
    target_object_id: str


class RuleIndeterminate(ValueError):
    """Fail the complete evaluation without materializing a partial Finding set."""

    def __init__(self, reason_code: str):
        if reason_code not in BATCH_TWO_INDETERMINATE_REASONS:
            raise ValueError("invalid indeterminate reason")
        super().__init__(reason_code)
        self.reason_code = reason_code


BATCH_TWO_PROJECTIONS = (
    ProjectionDefinitionV1("xdi.proj.e.power_endpoint.v1", "xdi.schema.e.power_endpoint.v1", "xdi.adapter.e.power_endpoint.v1", "xdi.selector.e.power_endpoint.v1", "xdi.complete.e.power_endpoint.v1", "engineering_object"),
    ProjectionDefinitionV1("xdi.proj.e.cable_supply.v1", "xdi.schema.e.cable_supply.v1", "xdi.adapter.e.cable_supply.v1", "xdi.selector.e.cable_supply.v1", "xdi.complete.e.cable_supply.v1", "engineering_object"),
    ProjectionDefinitionV1("xdi.proj.i.instrument_power.v1", "xdi.schema.i.instrument_power.v1", "xdi.adapter.i.instrument_power.v1", "xdi.selector.i.instrument_power.v1", "xdi.complete.i.instrument_power.v1", "engineering_object"),
    ProjectionDefinitionV1("xdi.proj.i.signal.v1", "xdi.schema.i.signal.v1", "xdi.adapter.i.signal.v1", "xdi.selector.i.signal.v1", "xdi.complete.i.signal.v1", "engineering_object"),
    ProjectionDefinitionV1("xdi.proj.i.handoff.v1", "xdi.schema.i.handoff.v1", "xdi.adapter.i.handoff.v1", "xdi.selector.i.handoff.v1", "xdi.complete.i.handoff.v1", "interface_commitment"),
)


def parse_batch_two_selector(value: str) -> tuple[str, str, str, str]:
    """Parse the closed E↔I selector wire form without source lookup."""
    if not isinstance(value, str) or value != unicodedata.normalize("NFC", value):
        raise ValueError("invalid_request")
    if any(character.isspace() for character in value):
        raise ValueError("invalid_request")
    for match in re.finditer("%", value):
        escape = value[match.start() + 1:match.start() + 3]
        if len(escape) != 2 or not re.fullmatch(r"[0-9A-F]{2}", escape):
            raise ValueError("invalid_request")
    parts = value.split("/")
    if len(parts) != 5 or parts[0] != BATCH_TWO_SELECTOR_PREFIX:
        raise ValueError("invalid_request")
    _, discipline, source_kind, canonical_id, role = parts
    if discipline not in {"electrical", "instrumentation"}:
        raise ValueError("invalid_request")
    if source_kind not in {"engineering_object", "engineering_identifier"}:
        raise ValueError("invalid_request")
    if role not in {"power_endpoint", "power_consumer", "signal_endpoint", "junction_box", "cable", "supply_terminal", "handoff_provider", "handoff_consumer"}:
        raise ValueError("invalid_request")
    try:
        decoded_id = unquote_to_bytes(canonical_id).decode("utf-8", "strict")
        parsed = UUID(decoded_id)
    except (ValueError, AttributeError, UnicodeDecodeError) as error:
        raise ValueError("invalid_request") from error
    if str(parsed) != decoded_id:
        raise ValueError("invalid_request")
    return discipline, source_kind, decoded_id, role


def batch_two_occurrence_key(*, project_id: int, provider_workspace_id: int,
                             consumer_workspace_id: int,
                             endpoints: tuple[tuple[str, str], ...]) -> str:
    """Stable occurrence identity, intentionally excluding mutable revisions."""
    if project_id < 1 or provider_workspace_id < 1 or consumer_workspace_id < 1:
        raise ValueError("invalid_request")
    normalized = []
    for owner_kind, owner_id in endpoints:
        if not owner_kind or not owner_id:
            raise ValueError("invalid_request")
        try:
            if str(UUID(owner_id)) != owner_id:
                raise ValueError("invalid_request")
        except ValueError as error:
            raise ValueError("invalid_request") from error
        normalized.append((owner_kind, owner_id))
    ordered = tuple(sorted(normalized, key=lambda item: (item[0], UUID(item[1]).bytes)))
    if not ordered or len(set(ordered)) != len(ordered):
        raise ValueError("invalid_request")
    from .canonical import digest
    return digest({"project_id": project_id, "interface_definition_id": BATCH_TWO_INTERFACE_ID,
                   "provider_workspace_id": provider_workspace_id,
                   "consumer_workspace_id": consumer_workspace_id,
                   "endpoints": ordered}, "satco:cross-discipline-occurrence:v1")


LIMITS = MappingProxyType({
    "workspaces": 12, "participants": 128, "projections": 256,
    "attestations": 128, "occurrences": 128, "nodes": 256,
    "edges": 512, "depth": 4, "fanout": 32, "paths_per_rule": 32,
    "interface_definitions": 16, "definitions_per_type": 32, "rules": 64,
    "findings": 256, "findings_per_rule": 32,
    "dispositions_per_finding": 64, "dispositions": 4096,
    "set_members": 64, "projection_fields": 64,
    "snapshot_bytes": 2_097_152, "request_bytes": 262_144,
    "response_bytes": 2_097_152, "page_default": 50, "page_max": 100,
    "assessment_statements": 256, "replay_statements": 128,
    "assessment_wall_ms": 10_000, "graph_cpu_ms": 2_000,
    "replay_wall_ms": 5_000, "db_attempts": 3,
})


def enforce_resource_limit(name: str, observed: int) -> int:
    """Apply one frozen cardinality/budget ceiling at its owning boundary."""
    if name not in LIMITS or isinstance(observed, bool) or observed < 0:
        raise ValueError("invalid resource limit observation")
    if observed > LIMITS[name]:
        raise ValueError("resource_limit_exceeded")
    return observed


@dataclass(frozen=True, slots=True)
class QuantityV1:
    dimension: str
    magnitude: Decimal
    source_unit: str
    canonical_magnitude: Decimal


@dataclass(frozen=True, slots=True)
class RangeV1:
    lower: Any
    upper: Any
    lower_inclusive: bool = True
    upper_inclusive: bool = True


@dataclass(frozen=True, slots=True)
class ReferenceV1:
    owner_kind: str
    owner_id: str
    version: int


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    outcome: Literal["satisfied", "violated", "not_applicable", "indeterminate"]
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class SourceIdentityV1:
    owner_kind: str
    owner_id: str
    revision_kind: str
    revision: str
    projection_digest: str


@dataclass(frozen=True, slots=True)
class SourceProjectionV1:
    projection_id: str
    owner: SourceIdentityV1
    values: tuple[tuple[str, Any], ...]
    authorization_scope_digest: str
    observed_at: datetime
    projection_digest: str


@dataclass(frozen=True, slots=True)
class CompletenessAttestationV1:
    attestation_id: str
    owner_kind: str
    owner_id: str
    universe_selector_digest: str
    observed_cardinality: int
    page_count: int
    non_truncated: bool
    negative_result: bool
    authorization_scope_digest: str
    attestation_digest: str


@dataclass(frozen=True, slots=True)
class FindingIdentityInputV1:
    assessment_execution_id: str
    assessment_snapshot_id: str
    category: str
    subcode: str
    rule_id: str
    rule_version: str
    rule_digest: str
    interface_definition_id: str
    interface_version: str
    interface_digest: str
    occurrence_key: str
    affected_selector: str
    sources: tuple[SourceIdentityV1, ...]
    attestation_digests: tuple[str, ...] = ()
    commitment: tuple[str, int] | None = None
    change: tuple[str, int] | None = None
    registry_digest: str = ""
    combination_id: str = ""
    project_configuration_revision: int = 1
    workspace_binding_revisions: tuple[tuple[int, str, int], ...] = ()


@dataclass(frozen=True, slots=True)
class FindingV1:
    finding_id: str
    identity: FindingIdentityInputV1
    severity: str
    comparison_outcome: str
    fingerprint: str
    recurrence_key: str
    sort_key: tuple[int, str, str, str, str, str]
    authority_class: str = "advisory_derived"


@dataclass(frozen=True, slots=True)
class DefinitionSetV1:
    schema_version: int
    definition_set_id: str
    version: str
    release_id: str
    registry_release_id: str
    profile_id: str
    canonicalization_id: str
    limits_profile: Mapping[str, int]
    supported_combinations: tuple[str, ...]
    comparison_ids: tuple[str, ...]
    rule_ids: tuple[str, ...]
    conformance_vector_ids: tuple[str, ...]
    digest: str
    interface_definitions: tuple[InterfaceDefinitionV1, ...] = ()
    projection_definitions: tuple[ProjectionDefinitionV1, ...] = ()
    relationship_grammar_ids: tuple[str, ...] = ()
    path_ids: tuple[str, ...] = ()
    rule_definitions: tuple[RuleDefinitionV1, ...] = ()


@dataclass(frozen=True, slots=True)
class EvaluationInputV1:
    execution_id: str
    snapshot_id: str
    values_by_rule: Mapping[str, tuple[Any, ...]]
    sources_by_rule: Mapping[str, tuple[SourceIdentityV1, ...]] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class EvaluationResultV1:
    status: str
    reason_code: str | None
    findings: tuple[FindingV1, ...]
    finding_set_digest: str
    result_digest: str
