"""Framework-free frozen contracts for the PATCH-053 shared kernel."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType
from typing import Any, Literal, Mapping


CANONICALIZATION_ID = "cross_discipline.canonical_json.v1"
EVALUATOR_ID = "cross_discipline.evaluator.v1"
LIMITS_PROFILE_ID = "cross_discipline.eic.limits.v1"
DEFINITION_SET_ID = "cross_discipline.eic.v1"
RULE_SET_ID = "cross_discipline.eic.rules.v1"
RELEASE_ID = "patch-053.eic-intelligence-v1"
REGISTRY_RELEASE_ID = "patch-052.eic-v1"
PROFILE_ID = "commercial_v1.eic@1.0.0"


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
