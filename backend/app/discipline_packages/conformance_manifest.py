"""Closed, inert PATCH-052 conformance-vector source data.

Vectors are declarative test inputs.  They deliberately cannot carry imports,
scripts, SQL, URLs, prompts, templates, or an executable callback.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
from typing import Literal, TypeAlias

from app.discipline_packages.canonical import canonical_json_bytes


PACKAGE_KEYS = ("electrical", "instrumentation", "control_automation")
VECTOR_SUFFIXES = (
    "registration_projection", "organization_project_configuration", "workspace_binding",
    "object_workflow", "relationship_workflow", "context_input", "evidence_expectation",
    "deterministic_rule", "deliverable_expectation", "audit_provenance",
    "authorization_negative", "tenant_negative", "historical_read_only",
)
COMBINATION_IDS = (
    "electrical", "instrumentation", "control_automation", "electrical_instrumentation",
    "electrical_control_automation", "instrumentation_control_automation",
    "electrical_instrumentation_control_automation",
)

CanonicalScalar: TypeAlias = str | int | bool
CanonicalFields: TypeAlias = tuple[tuple[str, CanonicalScalar], ...]

_PACKAGE_EXPECTATIONS = {
    "electrical": (8, 7, 5, 9, 4, 4, 5, 62, "workspace.electrical.v1"),
    "instrumentation": (8, 5, 5, 9, 4, 4, 5, 60, "workspace.instrumentation.v1"),
    "control_automation": (7, 13, 5, 9, 5, 4, 5, 68, "workspace.control_automation.v1"),
}
_COMBINATION_MEMBERS = {
    "electrical": ("electrical",),
    "instrumentation": ("instrumentation",),
    "control_automation": ("control_automation",),
    "electrical_instrumentation": ("electrical", "instrumentation"),
    "electrical_control_automation": ("control_automation", "electrical"),
    "instrumentation_control_automation": ("control_automation", "instrumentation"),
    "electrical_instrumentation_control_automation": (
        "control_automation", "electrical", "instrumentation",
    ),
}
_OPERATION_IDS = {
    "registration_projection": "registry.project",
    "organization_project_configuration": "configuration.resolve",
    "workspace_binding": "workspace.resolve_effective",
    "object_workflow": "owner.object.create",
    "relationship_workflow": "owner.relationship.create",
    "context_input": "{package}.evaluate_readiness",
    "evidence_expectation": "{package}.evidence_sufficiency",
    "deterministic_rule": "{package}.evaluate_readiness",
    "deliverable_expectation": "owner.deliverable.ready_for_review",
    "audit_provenance": "audit.read",
    "authorization_negative": "{package}.authorization_negative",
    "tenant_negative": "{package}.tenant_negative",
    "historical_read_only": "history.resolve",
}


@dataclass(frozen=True, slots=True)
class ConformanceVectorV1:
    schema_version: int
    vector_id: str
    subject_kind: Literal["package_declaration", "release_combination"]
    subject_id: str
    release_id: str
    package_selection: tuple[tuple[str, str], ...]
    descriptor_digest_selector: tuple[tuple[str, str], ...]
    scenario_purpose: str
    fixture_id: str
    setup_preconditions: CanonicalFields
    authoritative_inputs: tuple[tuple[str, str], ...]
    operation_id: str
    executor_reference: str
    expected_result: CanonicalFields
    expected_provenance: CanonicalFields
    authorization_expectation: str
    tenant_expectation: str
    historical_expectation: str
    failure_expectation: str

    def digest(self) -> str:
        return sha256(canonical_json_bytes(asdict(self))).hexdigest()


def _package_vector(package_key: str, suffix: str) -> ConformanceVectorV1:
    (
        object_count, relationship_count, context_count, input_count,
        deliverable_count, evidence_count, rule_count, aggregate_units,
        component_key,
    ) = _PACKAGE_EXPECTATIONS[package_key]
    expected_result: CanonicalFields = (
        ("status", "PASS"),
        ("scenario", suffix),
        ("package_key", package_key),
        ("package_version", "1.0.0"),
        ("membership_standing", "executable_supported"),
        ("object_count", object_count),
        ("relationship_count", relationship_count),
        ("context_count", context_count),
        ("input_count", input_count),
        ("deliverable_count", deliverable_count),
        ("evidence_count", evidence_count),
        ("rule_count", rule_count),
        ("aggregate_units", aggregate_units),
        ("component_key", component_key),
        ("authorization", "intersection_only"),
        ("tenant_failure", "protected_not_found"),
        ("historical_state", "historical_read_only"),
    )
    return ConformanceVectorV1(
        1, f"patch_052.{package_key}.v1.{suffix}", "package_declaration",
        f"{package_key}.conformance.{suffix}", "patch-052.eic-v1",
        ((package_key, "1.0.0"),), ((package_key, "1.0.0"),), suffix,
        "patch_052.common.v1", (
            ("source_release", "exact"), ("fixture_authority", "authorized"),
        ),
        (
            ("organization_id", "00000000-0000-0000-0000-000000000001"),
            ("project_id", "101"),
            ("workspace_id", {"electrical": "201", "instrumentation": "202", "control_automation": "203"}[package_key]),
        ),
        _OPERATION_IDS[suffix].format(package=package_key),
        "patch_052.precompiled_harness.v1", expected_result,
        (
            ("release_id", "patch-052.eic-v1"),
            ("package_key", package_key),
            ("package_version", "1.0.0"),
            ("project_configuration_revision", 1),
            ("descriptor_digest", "source_computed"),
            ("registry_digest", "source_computed"),
        ),
        "intersection_only",
        "foreign_not_found", "legacy_read_only", "none",
    )


def _combination_vector(combination_id: str) -> ConformanceVectorV1:
    package_keys = _COMBINATION_MEMBERS[combination_id]
    members = tuple((key, "1.0.0") for key in package_keys)
    aggregate_units = sum(_PACKAGE_EXPECTATIONS[key][7] for key in package_keys)
    return ConformanceVectorV1(
        1, f"patch_052.eic_v1.combination.{combination_id}", "release_combination",
        f"patch_052.release.combination.{combination_id}", "patch-052.eic-v1", members,
        members, "combination", "patch_052.common.v1", (
            ("source_release", "exact"), ("fixture_authority", "authorized"),
        ),
        (("correlation_id", "00000000-0000-0000-0000-000000009001"),),
        "patch_052.combination.conformance", "patch_052.precompiled_harness.v1",
        (
            ("status", "PASS"),
            ("compatible", True),
            ("profile_id", "commercial_v1.eic"),
            ("profile_version", "1.0.0"),
            ("package_keys", "|".join(package_keys)),
            ("aggregate_units", aggregate_units),
            ("catalog_collisions", 0),
            ("cross_package_rule_invocations", 0),
            ("dependency_traversal_depth", 0),
        ),
        (
            ("release_id", "patch-052.eic-v1"),
            ("registry_digest", "source_computed"),
            ("profile_digest", "source_computed"),
            ("combination_digest", "source_computed"),
            ("selected_descriptor_set_digest", "source_computed"),
        ),
        "intersection_only",
        "foreign_not_found", "legacy_read_only", "none",
    )


CONFORMANCE_VECTORS_V1 = tuple(
    _package_vector(package_key, suffix)
    for package_key in PACKAGE_KEYS for suffix in VECTOR_SUFFIXES
) + tuple(_combination_vector(item) for item in COMBINATION_IDS)


def expected_result_digest(vector: ConformanceVectorV1) -> str:
    """Digest only the accepted canonical expected-result payload."""

    return sha256(canonical_json_bytes(vector.expected_result)).hexdigest()


EXPECTED_RESULT_DIGESTS_V1 = tuple(
    (vector.vector_id, expected_result_digest(vector))
    for vector in CONFORMANCE_VECTORS_V1
)


def validate_conformance_manifest(vectors: tuple[ConformanceVectorV1, ...] = CONFORMANCE_VECTORS_V1) -> None:
    """Validate the exact closed inventory and reject every form of drift."""

    if type(vectors) is not tuple or any(type(item) is not ConformanceVectorV1 for item in vectors):
        raise ValueError("malformed conformance vector")
    if len(vectors) != 46:
        raise ValueError("PATCH-052 requires exactly 46 unique vectors")
    if len({item.vector_id for item in vectors}) != 46:
        raise ValueError("PATCH-052 requires exactly 46 unique vectors")
    expected_by_id = {item.vector_id: item for item in CONFORMANCE_VECTORS_V1}
    if set(item.vector_id for item in vectors) != set(expected_by_id):
        raise ValueError("unknown or missing conformance vector")
    if tuple(item.vector_id for item in vectors) != tuple(expected_by_id):
        raise ValueError("conformance vector order mismatch")
    for vector in vectors:
        expected = expected_by_id[vector.vector_id]
        if vector != expected:
            if vector.release_id != expected.release_id:
                raise ValueError("Registry release mismatch")
            if vector.package_selection != expected.package_selection:
                if vector.subject_kind == "release_combination":
                    raise ValueError("unsupported package combination")
                raise ValueError("package/version mismatch")
            if (
                vector.subject_kind != expected.subject_kind
                or vector.subject_id != expected.subject_id
                or vector.descriptor_digest_selector != expected.descriptor_digest_selector
            ):
                raise ValueError("descriptor mismatch")
            raise ValueError("malformed conformance vector")
        if vector.executor_reference != "patch_052.precompiled_harness.v1":
            raise ValueError("untrusted vector executor")
        if expected_result_digest(vector) != dict(EXPECTED_RESULT_DIGESTS_V1)[vector.vector_id]:
            raise ValueError("expected-result digest mismatch")
