from __future__ import annotations

from app.adapters.discipline_package_registry import StaticDisciplinePackageAdapter
from app.discipline_packages.canonical import descriptor_digest
from app.discipline_packages.compatibility import CompatibilityInputV1, evaluate_package_compatibility
from app.discipline_packages.contracts import (
    AllowedCombinationV1,
    CompatibilityProfileV1,
    DescriptorRegistrationV1,
    DisciplinePackageDescriptorV1,
    ExactPackageSelectionV1,
    PackageReferenceV1,
    RegistryReleaseManifestV1,
)
from app.discipline_packages.identity import PackageKey, PackageVersion
from app.discipline_packages.registry import assemble_registry
from app.enums.discipline_package import CompatibilityDecision, DisciplinePackageStanding
from app.exceptions.discipline_package import DisciplinePackageReasonCode


def _descriptor(*, key: str, version: str, dependencies: tuple[PackageReferenceV1, ...] = (), conflicts: tuple[PackageReferenceV1, ...] = ()) -> DisciplinePackageDescriptorV1:
    return DisciplinePackageDescriptorV1(
        package_key=key,
        package_version=version,
        primary_discipline_id="electrical",
        core_contract_versions=(1,),
        display_name=key,
        entitlement_key=f"fixture.{key}",
        adapter_id=f"fixture.{key}",
        dependencies=dependencies,
        conflicts=conflicts,
    )


def _registry():
    base = _descriptor(key="base_package", version="1.0.0")
    dependent = _descriptor(
        key="dependent_package",
        version="1.0.0",
        dependencies=(PackageReferenceV1(package_key="base_package", package_version="1.0.0"),),
    )
    base_selection = ExactPackageSelectionV1(package_key="base_package", package_version="1.0.0", descriptor_digest=descriptor_digest(base))
    dependent_selection = ExactPackageSelectionV1(package_key="dependent_package", package_version="1.0.0", descriptor_digest=descriptor_digest(dependent))
    profile = CompatibilityProfileV1(
        profile_id="fixture.profile",
        profile_version="1.0.0",
        core_contract_version=1,
        combinations=(AllowedCombinationV1(members=(base_selection, dependent_selection)),),
    )
    manifest = RegistryReleaseManifestV1(
        release_id="compatibility.fixture",
        core_contract_version=1,
        descriptors=(
            DescriptorRegistrationV1(descriptor=base, adapter_id=base.adapter_id, standing=DisciplinePackageStanding.EXECUTABLE_SUPPORTED),
            DescriptorRegistrationV1(descriptor=dependent, adapter_id=dependent.adapter_id, standing=DisciplinePackageStanding.EXECUTABLE_SUPPORTED),
        ),
        profiles=(profile,),
    )
    adapters = tuple(
        StaticDisciplinePackageAdapter(item.adapter_id, PackageKey(item.package_key), PackageVersion(item.package_version), frozenset())
        for item in (base, dependent)
    )
    return assemble_registry(manifest, adapters=adapters), base_selection, dependent_selection


def test_compatibility_accepts_exact_allowed_combination_deterministically() -> None:
    registry, base, dependent = _registry()
    result = evaluate_package_compatibility(
        CompatibilityInputV1(
            registry=registry,
            core_contract_version=1,
            selections=(dependent, base),
            profile_id="fixture.profile",
            profile_version="1.0.0",
        )
    )
    assert result.decision is CompatibilityDecision.COMPATIBLE
    assert tuple(item.package_key for item in result.selections) == ("base_package", "dependent_package")
    assert result.reason_codes == ()


def test_compatibility_fails_closed_for_missing_dependency_and_disallowed_profile() -> None:
    registry, base, dependent = _registry()
    result = evaluate_package_compatibility(
        CompatibilityInputV1(
            registry=registry,
            core_contract_version=1,
            selections=(dependent,),
            profile_id="fixture.profile",
            profile_version="1.0.0",
        )
    )
    assert result.decision is CompatibilityDecision.INCOMPATIBLE
    assert DisciplinePackageReasonCode.MISSING_DEPENDENCY in result.reason_codes
    assert DisciplinePackageReasonCode.PROFILE_NOT_ALLOWED in result.reason_codes


def test_compatibility_rejects_project_selection_resource_overflow() -> None:
    registry, base, _dependent = _registry()
    result = evaluate_package_compatibility(
        CompatibilityInputV1(
            registry=registry,
            core_contract_version=1,
            selections=(base,) * 9,
        )
    )
    assert result.decision is CompatibilityDecision.INCOMPATIBLE
    assert DisciplinePackageReasonCode.RESOURCE_LIMIT_EXCEEDED in result.reason_codes


def test_historical_membership_blocks_eligibility_without_changing_descriptor_identity() -> None:
    descriptor = _descriptor(key="historical_package", version="1.0.0")
    selection = ExactPackageSelectionV1(
        package_key=descriptor.package_key,
        package_version=descriptor.package_version,
        descriptor_digest=descriptor_digest(descriptor),
    )
    adapter = StaticDisciplinePackageAdapter(
        descriptor.adapter_id,
        PackageKey(descriptor.package_key),
        PackageVersion(descriptor.package_version),
        frozenset(),
    )
    manifest = RegistryReleaseManifestV1(
        release_id="historical.compatibility",
        core_contract_version=1,
        descriptors=(DescriptorRegistrationV1(
            descriptor=descriptor,
            adapter_id=descriptor.adapter_id,
            standing=DisciplinePackageStanding.HISTORICAL_READ_ONLY,
        ),),
    )
    registry = assemble_registry(manifest, adapters=(adapter,))
    result = evaluate_package_compatibility(CompatibilityInputV1(
        registry=registry,
        core_contract_version=1,
        selections=(selection,),
    ))
    assert result.decision is CompatibilityDecision.INCOMPATIBLE
    assert DisciplinePackageReasonCode.HISTORICAL_ONLY in result.reason_codes
    assert registry.descriptor_digests[(descriptor.package_key, descriptor.package_version)] == descriptor_digest(descriptor)
