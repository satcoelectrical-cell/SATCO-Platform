from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.adapters.discipline_package_registry import NonCommercialEntitlementAdapter
from app.discipline_packages.canonical import (
    combination_digest,
    descriptor_digest,
    profile_digest,
    registry_digest,
    selected_descriptor_set_digest,
)
from app.discipline_packages.contributions import PackageContributionsV1, ResourceDeclarationV1, TaxonomyFamilyDeclarationV1
from app.discipline_packages.contracts import DisciplinePackageDescriptorV1
from app.discipline_packages.identity import (
    CombinationDigest,
    CoreContractVersion,
    DescriptorDigest,
    DisciplineId,
    PackageKey,
    PackageVersion,
    ProfileDigest,
    RegistryDigest,
    SelectedDescriptorSetDigest,
)
from app.enums.discipline_package import EntitlementDecision, EntitlementOperation
from app.ports.discipline_package import EntitlementRequest


def _descriptor(**changes: object) -> DisciplinePackageDescriptorV1:
    values: dict[str, object] = {
        "package_key": "fixture_package",
        "package_version": "1.0.0",
        "primary_discipline_id": "electrical",
        "core_contract_versions": (1,),
        "display_name": "Fixture Package",
        "entitlement_key": "fixture.package",
        "adapter_id": "fixture.adapter",
    }
    values.update(changes)
    return DisciplinePackageDescriptorV1(**values)


def test_identity_types_are_validated_and_non_interchangeable() -> None:
    assert str(DisciplineId("electrical")) == "electrical"
    assert str(PackageKey("electrical")) == "electrical"
    assert str(PackageVersion("1.2.3-alpha.1")) == "1.2.3-alpha.1"
    assert int(CoreContractVersion(1)) == 1
    digest = "a" * 64
    assert RegistryDigest(digest) != DescriptorDigest(digest)
    assert DescriptorDigest(digest) != SelectedDescriptorSetDigest(digest)
    assert ProfileDigest(digest) != CombinationDigest(digest)
    with pytest.raises(ValueError):
        DisciplineId("Electrical")
    with pytest.raises(ValueError):
        PackageVersion("01.2.3")
    with pytest.raises(ValueError):
        PackageVersion("1.2.3+build")


def test_descriptor_is_strict_and_contribution_bounds_are_enforced() -> None:
    descriptor = _descriptor()
    assert descriptor.schema_version == 1
    with pytest.raises(ValidationError):
        DisciplinePackageDescriptorV1(**descriptor.model_dump(), executable_python="no")
    declarations = tuple(
        TaxonomyFamilyDeclarationV1(id=f"taxonomy.{index}", version="1.0.0", owner="PACKAGE", ordinal=1, display_name="Taxonomy")
        for index in range(33)
    )
    with pytest.raises(ValidationError):
        PackageContributionsV1(taxonomy_families=declarations)
    with pytest.raises(ValueError):
        PackageContributionsV1(
            taxonomy_families=(TaxonomyFamilyDeclarationV1(id="taxonomy.one", version="1.0.0", owner="PACKAGE", ordinal=1, display_name="One"),),
            resource_declaration=ResourceDeclarationV1(taxonomy_families=0),
        )


def test_noncommercial_entitlement_can_never_grant_commercial_behavior() -> None:
    from uuid import UUID

    result = NonCommercialEntitlementAdapter().evaluate(
        EntitlementRequest(
            trusted_organization_id=UUID("00000000-0000-4000-8000-000000000001"),
            trusted_deployment_id="deployment",
            package_key="fixture_package",
            entitlement_key="fixture.package",
            operation=EntitlementOperation.EXECUTE,
        )
    )
    assert result is EntitlementDecision.NOT_REQUIRED


def test_canonical_digests_are_deterministic_ordered_and_semantically_distinct() -> None:
    members = (
        {"package_key": "zeta", "package_version": "1.0.0", "descriptor_digest": "b" * 64},
        {"package_key": "alpha", "package_version": "1.0.0", "descriptor_digest": "a" * 64},
    )
    descriptor = {"package_key": "alpha", "package_version": "1.0.0"}
    assert descriptor_digest(descriptor) == descriptor_digest({"package_version": "1.0.0", "package_key": "alpha"})
    assert selected_descriptor_set_digest(members) == selected_descriptor_set_digest(tuple(reversed(members)))
    assert selected_descriptor_set_digest(members) != combination_digest(members)
    profile = {
        "profile_id": "fixture.profile",
        "profile_version": "1.0.0",
        "core_contract_version": 1,
        "combinations": ({"members": members},),
    }
    assert profile_digest(profile) == profile_digest(profile)
    assert registry_digest({"release_id": "one"}) != registry_digest({"release_id": "two"})
