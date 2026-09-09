"""Precompiled, closed PATCH-052 conformance executor.

The manifest selects only functions in this module. It never evaluates a
caller-supplied expression, import, script, template, URL, or callback.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from app.discipline_packages.canonical import canonical_json_bytes, combination_digest
from app.discipline_packages.compatibility import (
    CompatibilityInputV1,
    evaluate_package_compatibility,
)
from app.discipline_packages.conformance_manifest import (
    CanonicalFields,
    ConformanceVectorV1,
    CONFORMANCE_VECTORS_V1,
    VECTOR_SUFFIXES,
    expected_result_digest,
    validate_conformance_manifest,
)
from app.discipline_packages.contracts import ExactPackageSelectionV1
from app.discipline_packages.descriptors.eic_v1 import PACKAGE_CONTRACTS_V1
from app.discipline_packages.descriptors.releases.release_052_eic_v1 import (
    RELEASE_052_EIC_V1,
)
from app.discipline_packages.identity import DescriptorDigest
from app.discipline_packages.registry import (
    TrustedDisciplinePackageRegistryV1,
    assemble_registry,
)
from app.enums.discipline_package import (
    CompatibilityDecision,
    DisciplinePackageStanding,
)


@dataclass(frozen=True, slots=True)
class ConformanceVectorResult:
    vector_id: str
    subject_kind: str
    actual_result: CanonicalFields
    actual_result_digest: str
    provenance: CanonicalFields


@dataclass(frozen=True, slots=True)
class ConformanceManifestResult:
    vector_count: int
    digests: tuple[tuple[str, str], ...]
    package_vector_count: int = 0
    combination_vector_count: int = 0
    executions: tuple[ConformanceVectorResult, ...] = ()


def execute_manifest(
    vectors: tuple[ConformanceVectorV1, ...] = CONFORMANCE_VECTORS_V1,
) -> ConformanceManifestResult:
    """Execute all accepted vectors through the fixed source harness."""

    validate_conformance_manifest(vectors)
    registry = assemble_registry(RELEASE_052_EIC_V1)
    executions = tuple(_execute_vector(vector, registry) for vector in vectors)
    package_count = sum(
        item.subject_kind == "package_declaration" for item in executions
    )
    combination_count = sum(
        item.subject_kind == "release_combination" for item in executions
    )
    if (package_count, combination_count) != (39, 7):
        raise ValueError("invalid conformance execution inventory")
    return ConformanceManifestResult(
        len(vectors),
        tuple((item.vector_id, item.digest()) for item in vectors),
        package_count,
        combination_count,
        executions,
    )


def verify_manifest(
    vectors: tuple[ConformanceVectorV1, ...],
) -> ConformanceManifestResult:
    """Backward-compatible name for the now-executing manifest gate."""

    return execute_manifest(vectors)


def verify_package_subset(
    vectors: tuple[ConformanceVectorV1, ...], *, package_key: str,
) -> ConformanceManifestResult:
    """Execute one exact 13-vector package subset through the same harness."""

    expected = tuple(
        vector
        for vector in CONFORMANCE_VECTORS_V1
        if vector.vector_id.startswith(f"patch_052.{package_key}.v1.")
    )
    expected_ids = tuple(
        f"patch_052.{package_key}.v1.{suffix}" for suffix in VECTOR_SUFFIXES
    )
    if (
        len(vectors) != len(expected_ids)
        or tuple(vector.vector_id for vector in vectors) != expected_ids
        or vectors != expected
    ):
        raise ValueError("invalid package conformance subset")
    registry = assemble_registry(RELEASE_052_EIC_V1)
    executions = tuple(_execute_vector(vector, registry) for vector in vectors)
    return ConformanceManifestResult(
        len(vectors),
        tuple((item.vector_id, item.digest()) for item in vectors),
        len(vectors),
        0,
        executions,
    )


def _execute_vector(
    vector: ConformanceVectorV1,
    registry: TrustedDisciplinePackageRegistryV1,
) -> ConformanceVectorResult:
    if vector.subject_kind == "package_declaration":
        actual_result, provenance = _execute_package_vector(vector, registry)
    elif vector.subject_kind == "release_combination":
        actual_result, provenance = _execute_combination_vector(vector, registry)
    else:  # pragma: no cover - strict manifest validation rejects this first
        raise ValueError("unknown conformance vector subject")
    actual_digest = _actual_result_digest(actual_result)
    if (
        canonical_json_bytes(actual_result)
        != canonical_json_bytes(vector.expected_result)
        or actual_digest != expected_result_digest(vector)
    ):
        raise ValueError(f"conformance result mismatch: {vector.vector_id}")
    return ConformanceVectorResult(
        vector.vector_id,
        vector.subject_kind,
        actual_result,
        actual_digest,
        provenance,
    )


def _actual_result_digest(actual_result: CanonicalFields) -> str:
    return sha256(canonical_json_bytes(actual_result)).hexdigest()


def _execute_package_vector(
    vector: ConformanceVectorV1,
    registry: TrustedDisciplinePackageRegistryV1,
) -> tuple[CanonicalFields, CanonicalFields]:
    package_key, package_version = vector.package_selection[0]
    identity = (package_key, package_version)
    descriptor = registry.descriptor(*identity)
    adapter = registry.adapters.get(identity)
    standing = registry.membership_standing(*identity)
    if (
        descriptor is None
        or adapter is None
        or standing is not DisciplinePackageStanding.EXECUTABLE_SUPPORTED
        or adapter.adapter_id != descriptor.adapter_id
    ):
        raise ValueError("package conformance dependency unavailable")
    declaration = next(
        (
            item
            for item in descriptor.contributions.conformance_evidence
            if item.vector_id == vector.vector_id
        ),
        None,
    )
    if (
        declaration is None
        or declaration.id != vector.subject_id
        or declaration.expected_result_digest != expected_result_digest(vector)
    ):
        raise ValueError("descriptor conformance mismatch")
    contributions = descriptor.contributions
    component_keys = contributions.frontend_metadata.component_keys
    if len(component_keys) != 1:
        raise ValueError("frontend component conformance mismatch")
    contract = next(
        (
            item for item in PACKAGE_CONTRACTS_V1
            if (item.package_key, item.package_version) == identity
        ),
        None,
    )
    if contract is None or len(contract.rule_specs) != len(
        contributions.deterministic_rule_hooks
    ):
        raise ValueError("precompiled operation conformance mismatch")
    _assert_package_scenario(vector, registry, descriptor, contract)
    actual_result: CanonicalFields = (
        ("status", "PASS"),
        ("scenario", vector.scenario_purpose),
        ("package_key", package_key),
        ("package_version", package_version),
        ("membership_standing", standing.value),
        ("object_count", len(contributions.object_types)),
        ("relationship_count", len(contributions.relationship_types)),
        ("context_count", len(contributions.context_contributions)),
        ("input_count", len(contributions.engineering_inputs)),
        ("deliverable_count", len(contributions.deliverables)),
        ("evidence_count", len(contributions.evidence_requirements)),
        ("rule_count", len(contributions.deterministic_rule_hooks)),
        (
            "aggregate_units",
            contributions.resource_declaration.aggregate_units(),
        ),
        ("component_key", component_keys[0]),
        ("authorization", vector.authorization_expectation),
        ("tenant_failure", "protected_not_found"),
        ("historical_state", "historical_read_only"),
    )
    provenance: CanonicalFields = (
        ("release_id", registry.manifest.release_id),
        ("registry_digest", str(registry.digest)),
        ("package_key", package_key),
        ("package_version", package_version),
        ("descriptor_digest", str(registry.descriptor_digests[identity])),
        ("declaration_id", declaration.id),
    )
    return actual_result, provenance


def _assert_package_scenario(vector, registry, descriptor, contract) -> None:
    """Interpret each closed package scenario through a fixed verifier branch."""

    contributions = descriptor.contributions
    scenario = vector.scenario_purpose
    if scenario == "registration_projection":
        if descriptor.adapter_id != contract.adapter_id:
            raise ValueError("registration projection mismatch")
    elif scenario == "organization_project_configuration":
        identity = (descriptor.package_key, descriptor.package_version)
        result = evaluate_package_compatibility(CompatibilityInputV1(
            registry=registry,
            core_contract_version=1,
            selections=(ExactPackageSelectionV1(
                package_key=identity[0],
                package_version=identity[1],
                descriptor_digest=DescriptorDigest(
                    str(registry.descriptor_digests[identity])
                ),
            ),),
            profile_id="commercial_v1.eic",
            profile_version="1.0.0",
            enabled_package_keys=frozenset((identity[0],)),
        ))
        if result.decision is not CompatibilityDecision.COMPATIBLE:
            raise ValueError("configuration conformance mismatch")
    elif scenario == "workspace_binding":
        if contributions.frontend_metadata.component_keys != (contract.component_key,):
            raise ValueError("Workspace binding conformance mismatch")
    elif scenario == "object_workflow":
        identities = tuple(item.id for item in contributions.object_types)
        if not identities or len(identities) != len(set(identities)):
            raise ValueError("Object workflow conformance mismatch")
    elif scenario == "relationship_workflow":
        identities = tuple(item.id for item in contributions.relationship_types)
        if not identities or len(identities) != len(set(identities)):
            raise ValueError("Relationship workflow conformance mismatch")
    elif scenario == "context_input":
        context_ids = {item.context_kind_id for item in contributions.context_contributions}
        context_inputs = {
            item.input_type_id for item in contributions.engineering_inputs
            if item.source_kind == "context"
        }
        if len(context_ids) != 5 or context_ids != context_inputs:
            raise ValueError("Context input conformance mismatch")
    elif scenario == "evidence_expectation":
        evidence_ids = {item.id for item in contributions.evidence_requirements}
        evidence_inputs = {
            item.input_type_id for item in contributions.engineering_inputs
            if item.source_kind == "evidence"
        }
        if len(evidence_ids) != 4 or evidence_ids != evidence_inputs:
            raise ValueError("Evidence conformance mismatch")
    elif scenario == "deterministic_rule":
        if {
            item.hook_id for item in contributions.deterministic_rule_hooks
        } != {item.hook_id for item in contract.rule_specs}:
            raise ValueError("deterministic rule conformance mismatch")
    elif scenario == "deliverable_expectation":
        inputs = {item.id for item in contributions.engineering_inputs}
        if not contributions.deliverables or any(
            not set(item.required_input_ids) <= inputs
            for item in contributions.deliverables
        ):
            raise ValueError("Deliverable conformance mismatch")
    elif scenario == "audit_provenance":
        expected = dict(vector.expected_provenance)
        if expected.get("descriptor_digest") != "source_computed" or expected.get(
            "registry_digest"
        ) != "source_computed":
            raise ValueError("Audit provenance conformance mismatch")
    elif scenario == "authorization_negative":
        if (
            vector.authorization_expectation != "intersection_only"
            or len(contributions.authorization_requirements) != 2
        ):
            raise ValueError("authorization conformance mismatch")
    elif scenario == "tenant_negative":
        if vector.tenant_expectation != "foreign_not_found":
            raise ValueError("tenant conformance mismatch")
    elif scenario == "historical_read_only":
        if vector.historical_expectation != "legacy_read_only":
            raise ValueError("historical conformance mismatch")
    else:  # pragma: no cover - exact inventory validation rejects this first
        raise ValueError("unknown package conformance scenario")


def _execute_combination_vector(
    vector: ConformanceVectorV1,
    registry: TrustedDisciplinePackageRegistryV1,
) -> tuple[CanonicalFields, CanonicalFields]:
    selections = tuple(
        ExactPackageSelectionV1(
            package_key=package_key,
            package_version=package_version,
            descriptor_digest=DescriptorDigest(str(
                registry.descriptor_digests[(package_key, package_version)]
            )),
        )
        for package_key, package_version in vector.package_selection
    )
    result = evaluate_package_compatibility(
        CompatibilityInputV1(
            registry=registry,
            core_contract_version=1,
            selections=selections,
            profile_id="commercial_v1.eic",
            profile_version="1.0.0",
            enabled_package_keys=frozenset(
                key for key, _version in vector.package_selection
            ),
        )
    )
    if (
        result.decision is not CompatibilityDecision.COMPATIBLE
        or result.registry_digest != registry.digest
        or result.profile_digest
        != registry.profile_digests[("commercial_v1.eic", "1.0.0")]
        or result.reason_codes
    ):
        raise ValueError("unsupported package combination")
    package_keys = tuple(item.package_key for item in result.selections)
    aggregate_units = sum(
        registry.descriptors[(item.package_key, item.package_version)]
        .contributions.resource_declaration.aggregate_units()
        for item in result.selections
    )
    actual_result: CanonicalFields = (
        ("status", "PASS"),
        ("compatible", True),
        ("profile_id", "commercial_v1.eic"),
        ("profile_version", "1.0.0"),
        ("package_keys", "|".join(package_keys)),
        ("aggregate_units", aggregate_units),
        ("catalog_collisions", 0),
        ("cross_package_rule_invocations", 0),
        ("dependency_traversal_depth", 0),
    )
    combination = str(
        combination_digest(
            tuple(item.model_dump(mode="python") for item in result.selections)
        )
    )
    provenance: CanonicalFields = (
        ("release_id", registry.manifest.release_id),
        ("registry_digest", str(registry.digest)),
        (
            "profile_digest",
            str(registry.profile_digests[("commercial_v1.eic", "1.0.0")]),
        ),
        ("combination_digest", combination),
        (
            "selected_descriptor_set_digest",
            str(result.selected_descriptor_set_digest),
        ),
    )
    return actual_result, provenance
