"""Pure, fixed-order compatibility evaluation for trusted Registry data."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Iterable

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_serializer, field_validator

from app.adapters.discipline_package_registry import StaticDisciplinePackageAdapter
from app.discipline_packages.canonical import combination_digest, selected_descriptor_set_digest
from app.discipline_packages.contributions import MAX_DEPENDENCY_DEPTH, MAX_DEPENDENCY_VISITS, MAX_SELECTIONS_PER_COMBINATION
from app.discipline_packages.contracts import CompatibilityProfileV1, DisciplinePackageDescriptorV1, ExactPackageSelectionV1, RegistryReleaseManifestV1
from app.discipline_packages.identity import DescriptorDigest, ProfileDigest, RegistryDigest, SelectedDescriptorSetDigest
from app.discipline_packages.registry import TrustedDisciplinePackageRegistryV1, _contribution_collision_sets, assemble_registry
from app.enums.discipline_package import CompatibilityDecision, DisciplinePackageStanding
from app.exceptions.discipline_package import DisciplinePackageError, DisciplinePackageReasonCode


@dataclass(frozen=True, slots=True)
class CompatibilityInputV1:
    registry: TrustedDisciplinePackageRegistryV1
    core_contract_version: int
    selections: tuple[ExactPackageSelectionV1, ...]
    profile_id: str | None = None
    profile_version: str | None = None
    enabled_package_keys: frozenset[str] | None = None
    # Bounded persistence facts, never executable migration instructions.
    existing_selections: tuple[ExactPackageSelectionV1, ...] = ()
    satisfied_migration_guard_ids: frozenset[str] = frozenset()
    migration_ready: bool = True
    resource_budget: int | None = None


class CompatibilityEvaluationV1(BaseModel):
    """Strict, serializable compatibility output with typed provenance."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    decision: CompatibilityDecision
    selections: tuple[ExactPackageSelectionV1, ...]
    registry_digest: RegistryDigest | None
    selected_descriptor_set_digest: SelectedDescriptorSetDigest | None
    profile_digest: ProfileDigest | None
    reason_codes: tuple[DisciplinePackageReasonCode, ...]

    @field_validator("registry_digest", mode="before")
    @classmethod
    def _registry_digest(cls, value: object, info: ValidationInfo) -> RegistryDigest | None:
        return _validate_digest_domain(value, RegistryDigest, info)

    @field_validator("selected_descriptor_set_digest", mode="before")
    @classmethod
    def _selected_set_digest(cls, value: object, info: ValidationInfo) -> SelectedDescriptorSetDigest | None:
        return _validate_digest_domain(value, SelectedDescriptorSetDigest, info)

    @field_validator("profile_digest", mode="before")
    @classmethod
    def _profile_digest(cls, value: object, info: ValidationInfo) -> ProfileDigest | None:
        return _validate_digest_domain(value, ProfileDigest, info)

    @field_serializer("registry_digest", "selected_descriptor_set_digest", "profile_digest")
    def _serialize_digest(self, value: RegistryDigest | SelectedDescriptorSetDigest | ProfileDigest | None) -> str | None:
        return None if value is None else str(value)


def _validate_digest_domain[T: RegistryDigest | SelectedDescriptorSetDigest | ProfileDigest](
    value: object,
    expected_type: type[T],
    info: ValidationInfo,
) -> T | None:
    """Accept exact wrappers in Python and exact-domain hex only from JSON."""

    if value is None:
        return None
    if type(value) is expected_type:
        return value
    if info.mode == "json" and type(value) is str:
        return expected_type(value)
    raise ValueError(f"digest must be {expected_type.__name__}")


def evaluate_package_compatibility(input: CompatibilityInputV1) -> CompatibilityEvaluationV1:
    """Evaluate in the exact EDS-051 order without I/O or execution.

    Invalid trusted state is an availability failure; malformed prospective
    selections remain a normal, fail-closed incompatibility result.  Explicit
    type/shape checks avoid converting unrelated programming errors to policy.
    """

    selections_are_well_formed = isinstance(input.selections, tuple) and all(type(item) is ExactPackageSelectionV1 for item in input.selections)
    selections = _normalise_selections(input.selections)
    set_digest = _selection_digest(selections)
    if not _usable_registry(input.registry):
        return _result(CompatibilityDecision.UNAVAILABLE, selections, None, set_digest, None, {DisciplinePackageReasonCode.REGISTRY_UNAVAILABLE})

    registry = input.registry
    reasons: set[DisciplinePackageReasonCode] = set()
    identities = tuple((item.package_key, item.package_version) for item in selections)
    if not selections_are_well_formed:
        reasons.add(DisciplinePackageReasonCode.INVALID_DESCRIPTOR)
    if len(identities) != len(set(identities)):
        reasons.add(DisciplinePackageReasonCode.INVALID_DESCRIPTOR)
    if len(selections) > MAX_SELECTIONS_PER_COMBINATION:
        reasons.add(DisciplinePackageReasonCode.RESOURCE_LIMIT_EXCEEDED)

    # 2. Current membership and executable standing.
    descriptors: list[DisciplinePackageDescriptorV1] = []
    for selection in selections:
        descriptor = registry.descriptor(selection.package_key, selection.package_version)
        if descriptor is None or registry.descriptor_digests.get((selection.package_key, selection.package_version)) != selection.descriptor_digest:
            reasons.add(DisciplinePackageReasonCode.UNSUPPORTED_VERSION)
            continue
        descriptors.append(descriptor)
        if registry.membership_standing(
            selection.package_key, selection.package_version
        ) is not DisciplinePackageStanding.EXECUTABLE_SUPPORTED:
            reasons.add(DisciplinePackageReasonCode.HISTORICAL_ONLY)

    # 3. Organization enablement.
    if input.enabled_package_keys is not None:
        for descriptor in descriptors:
            if descriptor.package_key not in input.enabled_package_keys:
                reasons.add(DisciplinePackageReasonCode.ORGANIZATION_DISABLED)

    # 4. Core contract compatibility.
    for descriptor in descriptors:
        if input.core_contract_version not in descriptor.core_contract_versions:
            reasons.add(DisciplinePackageReasonCode.CORE_CONTRACT_MISMATCH)

    selected_identity_set = set(identities)
    # 5. Key/version sorted, bounded dependency traversal.
    _validate_dependency_traversal(registry, descriptors, selected_identity_set, reasons)

    # 6. Declared conflicts.
    for descriptor in descriptors:
        for conflict in descriptor.conflicts:
            if (conflict.package_key, conflict.package_version) in selected_identity_set:
                reasons.add(DisciplinePackageReasonCode.DECLARED_CONFLICT)

    # 7. Exact profile combination match.
    profile_digest = _validate_profile(input, registry, selections, set_digest, reasons)

    # 8. Explicit taxonomy and contribution collision namespaces.
    _validate_collisions(descriptors, reasons)

    # 9. Migration declarations and bounded guard facts.
    _validate_migrations(input, descriptors, reasons)

    # 10. Aggregate declaration counters and profile ceiling.
    aggregate_units = sum(item.contributions.resource_declaration.aggregate_units() for item in descriptors)
    ceiling = input.resource_budget
    if input.profile_id is not None and input.profile_version is not None:
        profile = registry.profiles.get((input.profile_id, input.profile_version))
        if profile is not None and profile.aggregate_resource_ceiling:
            ceiling = profile.aggregate_resource_ceiling if ceiling is None else min(ceiling, profile.aggregate_resource_ceiling)
    if ceiling is not None and (type(ceiling) is not int or ceiling < 0 or aggregate_units > ceiling):
        reasons.add(DisciplinePackageReasonCode.RESOURCE_LIMIT_EXCEEDED)

    return _result(CompatibilityDecision.INCOMPATIBLE if reasons else CompatibilityDecision.COMPATIBLE, selections, registry.digest, set_digest, profile_digest, reasons)


def _normalise_selections(selections: tuple[ExactPackageSelectionV1, ...]) -> tuple[ExactPackageSelectionV1, ...]:
    if not isinstance(selections, tuple) or any(type(item) is not ExactPackageSelectionV1 for item in selections):
        return ()
    return tuple(sorted(selections, key=lambda item: (item.package_key, item.package_version, str(item.descriptor_digest))))


def _selection_digest(selections: tuple[ExactPackageSelectionV1, ...]) -> SelectedDescriptorSetDigest | None:
    identities = tuple((item.package_key, item.package_version) for item in selections)
    if len(identities) != len(set(identities)):
        return None
    return selected_descriptor_set_digest(tuple(item.model_dump(mode="python") for item in selections))


def _usable_registry(registry: object) -> bool:
    """Reject expected malformed trusted state before evaluator traversal.

    This deliberately validates only Registry-contract structure and the
    assembled immutable state. It does not turn arbitrary evaluator errors
    into policy decisions.
    """

    if type(registry) is not TrustedDisciplinePackageRegistryV1:
        return False
    if type(registry.manifest) is not RegistryReleaseManifestV1 or type(registry.digest) is not RegistryDigest:
        return False
    if not all(isinstance(item, Mapping) for item in (
        registry.descriptors, registry.descriptor_digests,
        registry.membership_standings, registry.profiles,
        registry.profile_digests, registry.adapters,
    )):
        return False
    if not all(
        _package_identity(identity) and type(descriptor) is DisciplinePackageDescriptorV1
        and identity == (descriptor.package_key, descriptor.package_version)
        for identity, descriptor in registry.descriptors.items()
    ):
        return False
    if not all(
        _package_identity(identity) and type(digest) is DescriptorDigest
        and identity in registry.descriptors
        for identity, digest in registry.descriptor_digests.items()
    ) or set(registry.descriptor_digests) != set(registry.descriptors):
        return False
    if not all(
        _package_identity(identity)
        and type(standing) is DisciplinePackageStanding
        and identity in registry.descriptors
        for identity, standing in registry.membership_standings.items()
    ) or set(registry.membership_standings) != set(registry.descriptors):
        return False
    if not all(
        _profile_identity(identity) and type(profile) is CompatibilityProfileV1
        and identity == (profile.profile_id, profile.profile_version)
        for identity, profile in registry.profiles.items()
    ):
        return False
    if not all(
        _profile_identity(identity) and type(digest) is ProfileDigest
        and identity in registry.profiles
        for identity, digest in registry.profile_digests.items()
    ) or set(registry.profile_digests) != set(registry.profiles):
        return False
    if not all(
        _package_identity(identity) and type(adapter) is StaticDisciplinePackageAdapter
        and identity == (str(adapter.package_key), str(adapter.package_version))
        for identity, adapter in registry.adapters.items()
    ):
        return False
    try:
        rebuilt = assemble_registry(registry.manifest, adapters=tuple(registry.adapters.values()))
    except (DisciplinePackageError, TypeError, ValueError, AttributeError):
        return False
    return (
        rebuilt.digest == registry.digest
        and rebuilt.descriptors == registry.descriptors
        and rebuilt.descriptor_digests == registry.descriptor_digests
        and rebuilt.membership_standings == registry.membership_standings
        and rebuilt.profiles == registry.profiles
        and rebuilt.profile_digests == registry.profile_digests
        and rebuilt.adapters == registry.adapters
    )


def _package_identity(value: object) -> bool:
    return (
        type(value) is tuple and len(value) == 2
        and all(type(item) is str for item in value)
    )


def _profile_identity(value: object) -> bool:
    return _package_identity(value)


def _validate_dependency_traversal(registry: TrustedDisciplinePackageRegistryV1, descriptors: Iterable[DisciplinePackageDescriptorV1], selected: set[tuple[str, str]], reasons: set[DisciplinePackageReasonCode]) -> None:
    visits = 0

    def walk(descriptor: DisciplinePackageDescriptorV1, lineage: tuple[tuple[str, str], ...], depth: int) -> None:
        nonlocal visits
        identity = (descriptor.package_key, descriptor.package_version)
        if depth > MAX_DEPENDENCY_DEPTH or visits >= MAX_DEPENDENCY_VISITS or identity in lineage:
            reasons.add(DisciplinePackageReasonCode.RESOURCE_LIMIT_EXCEEDED)
            return
        visits += 1
        for dependency in sorted(descriptor.dependencies, key=lambda item: (item.package_key, item.package_version)):
            dependency_identity = (dependency.package_key, dependency.package_version)
            target = registry.descriptor(*dependency_identity)
            if dependency_identity not in selected or target is None:
                reasons.add(DisciplinePackageReasonCode.MISSING_DEPENDENCY)
                continue
            walk(target, lineage + (identity,), depth + 1)

    for descriptor in sorted(descriptors, key=lambda item: (item.package_key, item.package_version)):
        walk(descriptor, (), 0)


def _validate_profile(input: CompatibilityInputV1, registry: TrustedDisciplinePackageRegistryV1, selections: tuple[ExactPackageSelectionV1, ...], set_digest: SelectedDescriptorSetDigest | None, reasons: set[DisciplinePackageReasonCode]) -> ProfileDigest | None:
    if input.profile_id is None and input.profile_version is None:
        return None
    profile = registry.profiles.get((input.profile_id or "", input.profile_version or ""))
    if profile is None or set_digest is None:
        reasons.add(DisciplinePackageReasonCode.PROFILE_NOT_ALLOWED)
        return None
    digest = registry.profile_digests.get((profile.profile_id, profile.profile_version))
    if type(digest) is not ProfileDigest:
        reasons.add(DisciplinePackageReasonCode.REGISTRY_UNAVAILABLE)
        return None
    if profile.core_contract_version != input.core_contract_version:
        reasons.add(DisciplinePackageReasonCode.CORE_CONTRACT_MISMATCH)
    wanted = combination_digest(tuple(item.model_dump(mode="python") for item in selections))
    allowed = {combination_digest(tuple(member.model_dump(mode="python") for member in combination.members)) for combination in profile.combinations}
    if wanted not in allowed:
        reasons.add(DisciplinePackageReasonCode.PROFILE_NOT_ALLOWED)
    return digest


def _validate_collisions(descriptors: Iterable[DisciplinePackageDescriptorV1], reasons: set[DisciplinePackageReasonCode]) -> None:
    taxonomy: set[str] = set()
    contributions: set[tuple[str, str]] = set()
    for descriptor in descriptors:
        for item in descriptor.contributions.taxonomy_families:
            if item.id in taxonomy:
                reasons.add(DisciplinePackageReasonCode.TAXONOMY_COLLISION)
            taxonomy.add(item.id)
        for namespace, values, identity in _contribution_collision_sets(descriptor):
            for item in values:
                key = (namespace, identity(item))
                if key in contributions:
                    reasons.add(DisciplinePackageReasonCode.CONTRIBUTION_COLLISION)
                contributions.add(key)


def _validate_migrations(input: CompatibilityInputV1, descriptors: Iterable[DisciplinePackageDescriptorV1], reasons: set[DisciplinePackageReasonCode]) -> None:
    if not input.migration_ready:
        reasons.add(DisciplinePackageReasonCode.MIGRATION_REQUIRED)
    existing = {(item.package_key, item.package_version): item for item in input.existing_selections}
    for descriptor in descriptors:
        prior = next((item for (key, _), item in existing.items() if key == descriptor.package_key), None)
        if prior is None or prior.package_version == descriptor.package_version:
            continue
        declarations = tuple(item for item in descriptor.contributions.migration_compatibility if item.from_package_key == prior.package_key and item.from_package_version == prior.package_version and item.to_package_key == descriptor.package_key and item.to_package_version == descriptor.package_version)
        if not declarations:
            reasons.add(DisciplinePackageReasonCode.MIGRATION_REQUIRED)
        elif not any(item.migration_guard_id in input.satisfied_migration_guard_ids for item in declarations):
            reasons.add(DisciplinePackageReasonCode.MIGRATION_INCOMPATIBLE)


def _result(decision: CompatibilityDecision, selections: tuple[ExactPackageSelectionV1, ...], registry_digest: RegistryDigest | None, set_digest: SelectedDescriptorSetDigest | None, profile_digest: ProfileDigest | None, reasons: set[DisciplinePackageReasonCode]) -> CompatibilityEvaluationV1:
    return CompatibilityEvaluationV1(
        decision=decision,
        selections=selections,
        registry_digest=registry_digest,
        selected_descriptor_set_digest=set_digest,
        profile_digest=profile_digest,
        reason_codes=tuple(sorted(reasons, key=lambda item: item.value)),
    )
