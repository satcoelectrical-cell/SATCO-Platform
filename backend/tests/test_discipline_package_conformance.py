from __future__ import annotations

from app.adapters.discipline_package_registry import StaticDisciplinePackageAdapter
from app.discipline_packages.conformance import validate_descriptor_conformance
from app.discipline_packages.contracts import DisciplinePackageDescriptorV1
from app.discipline_packages.identity import PackageKey, PackageVersion
from app.discipline_packages.legacy import LegacyDisposition, LegacySourceContract, translate_legacy_identity


def _descriptor() -> DisciplinePackageDescriptorV1:
    return DisciplinePackageDescriptorV1(
        package_key="fixture_package",
        package_version="1.0.0",
        primary_discipline_id="electrical",
        core_contract_versions=(1,),
        display_name="Fixture Package",
        entitlement_key="fixture.package",
        adapter_id="fixture.adapter",
    )


def test_conformance_accepts_static_declarative_descriptor_only() -> None:
    descriptor = _descriptor()
    adapter = StaticDisciplinePackageAdapter("fixture.adapter", PackageKey("fixture_package"), PackageVersion("1.0.0"), frozenset())
    assert validate_descriptor_conformance(descriptor, adapter).passed is True
    wrong_adapter = StaticDisciplinePackageAdapter("other.adapter", PackageKey("fixture_package"), PackageVersion("1.0.0"), frozenset())
    assert validate_descriptor_conformance(descriptor, wrong_adapter).passed is False


def test_legacy_translation_is_exact_and_never_fuzzy() -> None:
    control = translate_legacy_identity(LegacySourceContract.WORKSPACE, "control")
    assert control.canonical_discipline_id == "control_automation"
    assert control.eligible_package_key == "control_automation"
    automation = translate_legacy_identity(LegacySourceContract.OBJECT_RELATIONSHIP, "automation")
    assert automation.disposition is LegacyDisposition.TAXONOMY_ONLY
    advisory = translate_legacy_identity(LegacySourceContract.GUIDANCE, "automation_and_control")
    assert advisory.disposition is LegacyDisposition.ADVISORY_CATEGORY_ONLY
    assert translate_legacy_identity(LegacySourceContract.WORKSPACE, " Control ").disposition is LegacyDisposition.UNRESOLVED
    assert translate_legacy_identity(LegacySourceContract.WORKSPACE, "CONTROL").disposition is LegacyDisposition.UNRESOLVED
