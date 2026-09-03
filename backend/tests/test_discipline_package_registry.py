from __future__ import annotations

import inspect

import pytest
from pydantic import ValidationError

from app.adapters.discipline_package_registry import StaticDisciplinePackageAdapter
from app.discipline_packages.canonical import (
    combination_digest,
    descriptor_digest,
    selected_descriptor_set_digest,
)
from app.discipline_packages.contracts import (
    AllowedCombinationV1,
    CompatibilityProfileV1,
    DescriptorRegistrationV1,
    DisciplinePackageDescriptorV1,
    ExactPackageSelectionV1,
    RegistryReleaseManifestV1,
)
from app.discipline_packages.descriptors.releases import RELEASES, RELEASE_051_CORE_V1
from app.discipline_packages.identity import PackageKey, PackageVersion
from app.discipline_packages.registry import assemble_registry
from app.enums.discipline_package import DisciplinePackageStanding
from app.exceptions.discipline_package import RegistryAssemblyError


def _descriptor(package_key: str = "fixture_package", package_version: str = "1.0.0") -> DisciplinePackageDescriptorV1:
    return DisciplinePackageDescriptorV1(
        package_key=package_key,
        package_version=package_version,
        primary_discipline_id="electrical",
        core_contract_versions=(1,),
        display_name="Fixture Package",
        entitlement_key="fixture.package",
        adapter_id="fixture.adapter",
    )


def _adapter(descriptor: DisciplinePackageDescriptorV1) -> StaticDisciplinePackageAdapter:
    return StaticDisciplinePackageAdapter(
        adapter_id=descriptor.adapter_id,
        package_key=PackageKey(descriptor.package_key),
        package_version=PackageVersion(descriptor.package_version),
        capability_ids=frozenset(),
    )


def test_explicit_empty_core_release_is_deterministic_and_historically_addressable() -> None:
    first = assemble_registry(RELEASE_051_CORE_V1)
    second = assemble_registry(RELEASE_051_CORE_V1)
    assert str(first.digest) == "9f785b463f1ad0374de2eefc93af5591db596d92972628a24d9b7f0e028baece"
    assert first.digest == second.digest
    assert first.descriptors == {}
    assert RELEASES[RELEASE_051_CORE_V1.release_id] is RELEASE_051_CORE_V1


def test_registry_requires_exact_static_adapter_and_rejects_duplicate_identity() -> None:
    descriptor = _descriptor()
    manifest = RegistryReleaseManifestV1(
        release_id="fixture.release",
        core_contract_version=1,
        descriptors=(DescriptorRegistrationV1(descriptor=descriptor, adapter_id=descriptor.adapter_id, standing=DisciplinePackageStanding.EXECUTABLE_SUPPORTED),),
    )
    with pytest.raises(RegistryAssemblyError):
        assemble_registry(manifest, adapters=())
    registry = assemble_registry(manifest, adapters=(_adapter(descriptor),))
    assert registry.descriptor("fixture_package", "1.0.0") == descriptor
    with pytest.raises(ValueError):
        RegistryReleaseManifestV1(
            release_id="duplicate.release",
            core_contract_version=1,
            descriptors=(
                DescriptorRegistrationV1(descriptor=descriptor, adapter_id=descriptor.adapter_id, standing=DisciplinePackageStanding.EXECUTABLE_SUPPORTED),
                DescriptorRegistrationV1(descriptor=descriptor, adapter_id=descriptor.adapter_id, standing=DisciplinePackageStanding.EXECUTABLE_SUPPORTED),
            ),
        )


def test_registry_uses_no_runtime_plugin_discovery() -> None:
    import app.discipline_packages.registry as registry_module

    source = inspect.getsource(registry_module)
    assert "importlib" not in source
    assert "entry_points" not in source
    assert "eval(" not in source
    assert "exec(" not in source


def test_semantic_descriptor_and_profile_reuse_do_not_depend_on_registry_digest() -> None:
    descriptor = _descriptor()
    selection = ExactPackageSelectionV1(
        package_key=descriptor.package_key,
        package_version=descriptor.package_version,
        descriptor_digest=descriptor_digest(descriptor),
    )
    profile = CompatibilityProfileV1(
        profile_id="fixture.profile",
        profile_version="1.0.0",
        core_contract_version=1,
        combinations=(AllowedCombinationV1(members=(selection,)),),
    )
    registration = DescriptorRegistrationV1(descriptor=descriptor, adapter_id=descriptor.adapter_id, standing=DisciplinePackageStanding.EXECUTABLE_SUPPORTED)
    adapter = _adapter(descriptor)
    first = assemble_registry(
        RegistryReleaseManifestV1(
            release_id="fixture.r1", core_contract_version=1, descriptors=(registration,), profiles=(profile,)
        ),
        adapters=(adapter,),
    )
    second = assemble_registry(
        RegistryReleaseManifestV1(
            release_id="fixture.r2", core_contract_version=1, descriptors=(registration,), profiles=(profile,)
        ),
        adapters=(adapter,),
    )
    identity = (descriptor.package_key, descriptor.package_version)
    profile_identity = (profile.profile_id, profile.profile_version)
    assert first.digest != second.digest
    assert first.descriptor_digests[identity] == second.descriptor_digests[identity]
    assert first.profile_digests[profile_identity] == second.profile_digests[profile_identity]


def test_standing_is_release_membership_state_and_not_descriptor_identity() -> None:
    descriptor = _descriptor()
    with pytest.raises(ValidationError):
        DisciplinePackageDescriptorV1(
            **descriptor.model_dump(mode="python"),
            standing=DisciplinePackageStanding.EXECUTABLE_SUPPORTED,
        )
    with pytest.raises(ValidationError):
        DescriptorRegistrationV1(
            descriptor=descriptor,
            adapter_id=descriptor.adapter_id,
        )

    selection = ExactPackageSelectionV1(
        package_key=descriptor.package_key,
        package_version=descriptor.package_version,
        descriptor_digest=descriptor_digest(descriptor),
    )
    profile = CompatibilityProfileV1(
        profile_id="standing.profile",
        profile_version="1.0.0",
        core_contract_version=1,
        combinations=(AllowedCombinationV1(members=(selection,)),),
    )
    executable = assemble_registry(
        RegistryReleaseManifestV1(
            release_id="standing.fixture",
            core_contract_version=1,
            descriptors=(DescriptorRegistrationV1(
                descriptor=descriptor,
                adapter_id=descriptor.adapter_id,
                standing=DisciplinePackageStanding.EXECUTABLE_SUPPORTED,
            ),),
            profiles=(profile,),
        ),
        adapters=(_adapter(descriptor),),
    )
    historical = assemble_registry(
        RegistryReleaseManifestV1(
            release_id="standing.fixture",
            core_contract_version=1,
            descriptors=(DescriptorRegistrationV1(
                descriptor=descriptor,
                adapter_id=descriptor.adapter_id,
                standing=DisciplinePackageStanding.HISTORICAL_READ_ONLY,
            ),),
            profiles=(profile,),
        ),
        adapters=(_adapter(descriptor),),
    )
    identity = (descriptor.package_key, descriptor.package_version)
    members = (selection.model_dump(mode="python"),)
    assert "standing" not in descriptor.model_dump(mode="json")
    assert executable.descriptor_digests[identity] == historical.descriptor_digests[identity]
    assert executable.digest != historical.digest
    assert selected_descriptor_set_digest(members) == selected_descriptor_set_digest(members)
    assert executable.profile_digests == historical.profile_digests
    assert combination_digest(members) == combination_digest(members)
    assert executable.membership_standings[identity] is DisciplinePackageStanding.EXECUTABLE_SUPPORTED
    assert historical.membership_standings[identity] is DisciplinePackageStanding.HISTORICAL_READ_ONLY
