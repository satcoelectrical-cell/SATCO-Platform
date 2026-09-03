"""Focused regression vectors for PATCH-051 Batch-1 remediation findings."""

from __future__ import annotations

import pytest
from dataclasses import replace
from pydantic import ValidationError

from app.adapters.discipline_package_registry import StaticDisciplinePackageAdapter
from app.discipline_packages.canonical import descriptor_digest, profile_digest
from app.discipline_packages.compatibility import CompatibilityEvaluationV1, CompatibilityInputV1, _validate_collisions, evaluate_package_compatibility
from app.discipline_packages.contributions import (
    AuthorizationRequirementDeclarationV1, ConformanceEvidenceDeclarationV1,
    ContextContributionDeclarationV1, DeliverableDeclarationV1, DeterministicRuleHookDeclarationV1,
    EngineeringInputDeclarationV1, EvidenceRequirementDeclarationV1, FrontendMetadataV1,
    InterfaceDeclarationV1, MigrationCompatibilityDeclarationV1, ObjectTypeDeclarationV1,
    PackageContributionsV1, RelationshipTypeDeclarationV1, ResourceDeclarationV1,
    RoleRequirementDeclarationV1, StandardsApplicabilityHookV1, TaxonomyFamilyDeclarationV1,
)
from app.discipline_packages.contracts import (
    AllowedCombinationV1, CompatibilityProfileV1, DescriptorRegistrationV1, DisciplinePackageDescriptorV1, ExactPackageSelectionV1,
    PackageReferenceV1, RegistryReleaseManifestV1,
)
from app.discipline_packages.identity import (
    CombinationDigest, DescriptorDigest, PackageKey, PackageVersion, ProfileDigest, RegistryDigest,
    SelectedDescriptorSetDigest,
)
from app.discipline_packages.registry import assemble_registry
from app.enums.discipline_package import CompatibilityDecision, DisciplinePackageStanding
from app.exceptions.discipline_package import DisciplinePackageReasonCode


def _base(**extra: object) -> dict[str, object]:
    value: dict[str, object] = {"id": "fixture.item", "version": "1.0.0", "owner": "PACKAGE", "ordinal": 1, "display_name": "Fixture"}
    value.update(extra)
    return value


def _descriptor(key: str, version: str = "1.0.0", **changes: object) -> DisciplinePackageDescriptorV1:
    values: dict[str, object] = {
        "package_key": key, "package_version": version, "primary_discipline_id": "electrical",
        "core_contract_versions": (1,), "display_name": key, "entitlement_key": f"fixture.{key}",
        "adapter_id": f"fixture.{key}",
    }
    values.update(changes)
    return DisciplinePackageDescriptorV1(**values)


def _registry(*descriptors: DisciplinePackageDescriptorV1):
    adapters = tuple(StaticDisciplinePackageAdapter(item.adapter_id, PackageKey(item.package_key), PackageVersion(item.package_version), frozenset()) for item in descriptors)
    return assemble_registry(
        RegistryReleaseManifestV1(
            release_id="remediation.fixture", core_contract_version=1,
            descriptors=tuple(DescriptorRegistrationV1(descriptor=item, adapter_id=item.adapter_id, standing=DisciplinePackageStanding.EXECUTABLE_SUPPORTED) for item in descriptors),
        ), adapters=adapters,
    )


def _selection(descriptor: DisciplinePackageDescriptorV1) -> ExactPackageSelectionV1:
    return ExactPackageSelectionV1(package_key=descriptor.package_key, package_version=descriptor.package_version, descriptor_digest=descriptor_digest(descriptor))


def test_semantic_sets_are_canonical_but_ordered_fields_remain_meaningful() -> None:
    d1 = _descriptor("main_package", dependencies=(PackageReferenceV1(package_key="zeta", package_version="1.0.0"), PackageReferenceV1(package_key="alpha", package_version="1.0.0")), conflicts=(PackageReferenceV1(package_key="gamma", package_version="1.0.0"), PackageReferenceV1(package_key="beta", package_version="1.0.0")))
    d2 = _descriptor("main_package", dependencies=tuple(reversed(d1.dependencies)), conflicts=tuple(reversed(d1.conflicts)))
    assert d1.dependencies == d2.dependencies
    assert d1.conflicts == d2.conflicts
    assert descriptor_digest(d1) == descriptor_digest(d2)
    one = TaxonomyFamilyDeclarationV1(**_base(id="taxonomy.one", ordinal=2))
    two = TaxonomyFamilyDeclarationV1(**_base(id="taxonomy.two", ordinal=1))
    first = PackageContributionsV1(taxonomy_families=(one, two), resource_declaration=ResourceDeclarationV1(taxonomy_families=2))
    second = PackageContributionsV1(taxonomy_families=(two, one), resource_declaration=ResourceDeclarationV1(taxonomy_families=2))
    assert first.taxonomy_families == second.taxonomy_families
    assert tuple(item.ordinal for item in first.taxonomy_families) == (2, 1)  # ordinal is metadata, not sequence identity


def test_registry_descriptor_registration_order_is_canonical() -> None:
    alpha, beta = _descriptor("alpha_package"), _descriptor("beta_package")
    one = _registry(alpha, beta)
    two = _registry(beta, alpha)
    assert one.digest == two.digest
    alpha_selection, beta_selection = _selection(alpha), _selection(beta)
    first = CompatibilityProfileV1(profile_id="fixture.profile", profile_version="1.0.0", core_contract_version=1, combinations=(AllowedCombinationV1(members=(alpha_selection, beta_selection)),))
    second = CompatibilityProfileV1(profile_id="fixture.profile", profile_version="1.0.0", core_contract_version=1, combinations=(AllowedCombinationV1(members=(beta_selection, alpha_selection)),))
    assert profile_digest(first) == profile_digest(second)


def test_digest_contract_boundaries_are_strict_and_canonical() -> None:
    text = "a" * 64
    with pytest.raises(ValidationError):
        ExactPackageSelectionV1(package_key="fixture_package", package_version="1.0.0", descriptor_digest=RegistryDigest(text))
    with pytest.raises(ValidationError):
        ExactPackageSelectionV1(package_key="fixture_package", package_version="1.0.0", descriptor_digest=text)
    assert descriptor_digest({"digest": DescriptorDigest(text)}) == descriptor_digest({"digest": DescriptorDigest(text)})
    assert DescriptorDigest(text) != ProfileDigest(text)
    assert CombinationDigest(text) != SelectedDescriptorSetDigest(text)


def test_compatibility_evaluation_provenance_is_typed_at_constructor_and_json_boundaries() -> None:
    text = "a" * 64
    selection = ExactPackageSelectionV1(package_key="fixture_package", package_version="1.0.0", descriptor_digest=DescriptorDigest(text))
    result = CompatibilityEvaluationV1(
        decision=CompatibilityDecision.COMPATIBLE,
        selections=(selection,),
        registry_digest=RegistryDigest(text),
        selected_descriptor_set_digest=SelectedDescriptorSetDigest(text),
        profile_digest=ProfileDigest(text),
        reason_codes=(),
    )
    assert result.model_dump(mode="json") == {
        "decision": "compatible",
        "selections": [{"package_key": "fixture_package", "package_version": "1.0.0", "descriptor_digest": text}],
        "registry_digest": text,
        "selected_descriptor_set_digest": text,
        "profile_digest": text,
        "reason_codes": [],
    }
    restored = CompatibilityEvaluationV1.model_validate_json(result.model_dump_json())
    assert type(restored.registry_digest) is RegistryDigest
    assert type(restored.selected_descriptor_set_digest) is SelectedDescriptorSetDigest
    assert type(restored.profile_digest) is ProfileDigest
    for field, invalid in (
        ("registry_digest", DescriptorDigest(text)),
        ("registry_digest", text),
        ("profile_digest", DescriptorDigest(text)),
        ("selected_descriptor_set_digest", CombinationDigest(text)),
    ):
        values = result.model_dump(mode="python")
        values[field] = invalid
        with pytest.raises(ValidationError):
            CompatibilityEvaluationV1(**values)


def test_every_closed_contribution_section_has_a_minimum_shape() -> None:
    assert TaxonomyFamilyDeclarationV1(**_base(parent_family_id=None))
    assert ObjectTypeDeclarationV1(**_base(family_id="family", lifecycle_id="active"))
    assert RelationshipTypeDeclarationV1(**_base(source_object_family_ids=("source",), target_object_family_ids=("target",), direction="directed", cardinality="one_to_many", lifecycle_id="active"))
    assert ContextContributionDeclarationV1(**_base(context_kind_id="context", allowed_subject_kind_ids=("subject",), value_schema_id="schema", required=True))
    assert EngineeringInputDeclarationV1(**_base(input_type_id="input", source_kind="context", required=True, max_occurrences=1))
    assert DeliverableDeclarationV1(**_base(deliverable_type_id="deliverable", output_representation_ids=("json",), human_acceptance_required=True))
    assert EvidenceRequirementDeclarationV1(**_base(evidence_kind_id="evidence", minimum_count=1, applicable_operation_id="operation", human_verification_required=True))
    assert DeterministicRuleHookDeclarationV1(**_base(hook_id="rule", hook_version="1.0.0", input_schema_id="in", output_schema_id="out", max_findings=0, timeout_ms=1))
    assert StandardsApplicabilityHookV1(hook_id="standard", version="1.0.0", input_schema_id="in", output_schema_id="out", max_results=0, timeout_ms=1)
    assert InterfaceDeclarationV1(interface_type_id="interface", source_discipline_id="electrical", target_discipline_id="process", dependency_kind="requires", version="1.0.0")
    assert RoleRequirementDeclarationV1(**_base(operation_id="operation", accepted_human_role_ids=("engineer",), minimum_authority_predicate_id="predicate"))
    assert AuthorizationRequirementDeclarationV1(**_base(operation_id="operation", source_owner_policy_id="source", package_policy_id="package"))
    assert FrontendMetadataV1(route_keys=("route",), navigation_keys=("nav",), component_keys=("component",))
    assert ResourceDeclarationV1()
    assert MigrationCompatibilityDeclarationV1(**_base(from_package_key="fixture_package", from_package_version="1.0.0", to_package_key="fixture_package", to_package_version="1.1.0", direction="forward", migration_guard_id="guard", reversible=False))
    assert ConformanceEvidenceDeclarationV1(**_base(vector_id="vector", contract_version="1.0.0", suite_version="1.0.0", expected_result_digest="a" * 64, reviewed_source_reference="review"))


def test_contribution_schema_rejects_wrong_payload_unknown_fields_and_executable_content() -> None:
    with pytest.raises(ValidationError):
        ObjectTypeDeclarationV1(**_base(family_id="family"))
    with pytest.raises(ValidationError):
        TaxonomyFamilyDeclarationV1(**_base(executable_python="import os"))
    with pytest.raises(ValidationError):
        DeterministicRuleHookDeclarationV1(**_base(hook_id="bad/id", hook_version="1.0.0", input_schema_id="in", output_schema_id="out", max_findings=0, timeout_ms=1))
    with pytest.raises(ValidationError):
        FrontendMetadataV1(component_keys=("component",), import_path="pkg.module")


@pytest.mark.parametrize(
    ("model", "fields", "maximum"),
    (
        (TaxonomyFamilyDeclarationV1, {"parent_family_id": None}, 32),
        (ObjectTypeDeclarationV1, {"family_id": "family", "lifecycle_id": "active"}, 256),
        (RelationshipTypeDeclarationV1, {"source_object_family_ids": ("source",), "target_object_family_ids": ("target",), "direction": "directed", "cardinality": "one_to_many", "lifecycle_id": "active"}, 128),
        (ContextContributionDeclarationV1, {"context_kind_id": "context", "allowed_subject_kind_ids": ("subject",), "value_schema_id": "schema", "required": True}, 64),
        (EngineeringInputDeclarationV1, {"input_type_id": "input", "source_kind": "context", "required": True, "max_occurrences": 1}, 128),
        (DeliverableDeclarationV1, {"deliverable_type_id": "deliverable", "output_representation_ids": ("json",), "human_acceptance_required": True}, 128),
        (EvidenceRequirementDeclarationV1, {"evidence_kind_id": "evidence", "minimum_count": 1, "applicable_operation_id": "operation", "human_verification_required": True}, 64),
        (DeterministicRuleHookDeclarationV1, {"hook_id": "rule", "hook_version": "1.0.0", "input_schema_id": "in", "output_schema_id": "out", "max_findings": 0, "timeout_ms": 1}, 128),
        (RoleRequirementDeclarationV1, {"operation_id": "operation", "accepted_human_role_ids": ("engineer",), "minimum_authority_predicate_id": "predicate"}, 32),
        (AuthorizationRequirementDeclarationV1, {"operation_id": "operation", "source_owner_policy_id": "source", "package_policy_id": "package"}, 32),
        (MigrationCompatibilityDeclarationV1, {"from_package_key": "fixture_package", "from_package_version": "1.0.0", "to_package_key": "fixture_package", "to_package_version": "1.1.0", "direction": "forward", "migration_guard_id": "guard", "reversible": False}, 16),
        (ConformanceEvidenceDeclarationV1, {"vector_id": "vector", "contract_version": "1.0.0", "suite_version": "1.0.0", "expected_result_digest": "a" * 64, "reviewed_source_reference": "review"}, 256),
    ),
)
def test_every_ordinal_bearing_contribution_enforces_accepted_strict_section_bounds(model: object, fields: dict[str, object], maximum: int) -> None:
    assert model(**_base(**fields, ordinal=1)).ordinal == 1  # type: ignore[operator]
    assert model(**_base(**fields, ordinal=maximum)).ordinal == maximum  # type: ignore[operator]
    for invalid in (0, maximum + 1, "1"):
        with pytest.raises(ValidationError):
            model(**_base(**fields, ordinal=invalid))  # type: ignore[operator]


def test_ordinal_remains_metadata_for_set_order_but_changes_descriptor_provenance() -> None:
    one = TaxonomyFamilyDeclarationV1(**_base(id="taxonomy.one", ordinal=1))
    two = TaxonomyFamilyDeclarationV1(**_base(id="taxonomy.two", ordinal=2))
    first = PackageContributionsV1(taxonomy_families=(one, two), resource_declaration=ResourceDeclarationV1(taxonomy_families=2))
    reversed_members = PackageContributionsV1(taxonomy_families=(two, one), resource_declaration=ResourceDeclarationV1(taxonomy_families=2))
    changed_ordinal = PackageContributionsV1(taxonomy_families=(one.model_copy(update={"ordinal": 3}), two), resource_declaration=ResourceDeclarationV1(taxonomy_families=2))
    assert descriptor_digest(_descriptor("ordinal_package", contributions=first)) == descriptor_digest(_descriptor("ordinal_package", contributions=reversed_members))
    assert descriptor_digest(_descriptor("ordinal_package", contributions=first)) != descriptor_digest(_descriptor("ordinal_package", contributions=changed_ordinal))


def test_compatibility_returns_closed_results_for_collision_migration_budget_and_invalid_registry() -> None:
    taxonomy = TaxonomyFamilyDeclarationV1(**_base(id="shared.taxonomy"))
    resource = ResourceDeclarationV1(taxonomy_families=1)
    left = _descriptor("left_package", contributions=PackageContributionsV1(taxonomy_families=(taxonomy,), resource_declaration=resource))
    right = _descriptor("right_package", contributions=PackageContributionsV1(taxonomy_families=(taxonomy.model_copy(update={"id": "shared.taxonomy", "ordinal": 2}),), resource_declaration=resource))
    # Assembly rejects a colliding release.  This deliberately malformed
    # trusted-state fixture exercises the evaluator's independent closed check.
    source = _registry(left)
    registry = replace(
        source,
        descriptors={(left.package_key, left.package_version): left, (right.package_key, right.package_version): right},
        descriptor_digests={(left.package_key, left.package_version): descriptor_digest(left), (right.package_key, right.package_version): descriptor_digest(right)},
    )
    result = evaluate_package_compatibility(CompatibilityInputV1(registry=registry, core_contract_version=1, selections=(_selection(left), _selection(right)), resource_budget=1))
    assert result.decision is CompatibilityDecision.UNAVAILABLE
    assert result.reason_codes == (DisciplinePackageReasonCode.REGISTRY_UNAVAILABLE,)
    reasons: set[DisciplinePackageReasonCode] = set()
    _validate_collisions((left, right), reasons)
    assert DisciplinePackageReasonCode.TAXONOMY_COLLISION in reasons
    unavailable = evaluate_package_compatibility(CompatibilityInputV1(registry=object(), core_contract_version=1, selections=()))
    assert unavailable.decision is CompatibilityDecision.UNAVAILABLE
    assert unavailable.reason_codes == (DisciplinePackageReasonCode.REGISTRY_UNAVAILABLE,)
    structurally_invalid = replace(source, descriptor_digests=object())
    unavailable = evaluate_package_compatibility(CompatibilityInputV1(registry=structurally_invalid, core_contract_version=1, selections=()))
    assert unavailable.decision is CompatibilityDecision.UNAVAILABLE
    assert unavailable.reason_codes == (DisciplinePackageReasonCode.REGISTRY_UNAVAILABLE,)


def test_compatibility_evaluates_organization_enablement_with_closed_ordered_reason() -> None:
    descriptor = _descriptor("enabled_package")
    registry = _registry(descriptor)
    selection = _selection(descriptor)
    enabled = evaluate_package_compatibility(CompatibilityInputV1(
        registry=registry, core_contract_version=1, selections=(selection,), enabled_package_keys=frozenset({descriptor.package_key}),
    ))
    assert DisciplinePackageReasonCode.ORGANIZATION_DISABLED not in enabled.reason_codes
    disabled = evaluate_package_compatibility(CompatibilityInputV1(
        registry=registry, core_contract_version=1, selections=(selection,), enabled_package_keys=frozenset(), resource_budget=-1,
    ))
    assert disabled.decision is CompatibilityDecision.INCOMPATIBLE
    assert DisciplinePackageReasonCode.ORGANIZATION_DISABLED in disabled.reason_codes
    assert disabled.reason_codes == tuple(sorted(disabled.reason_codes, key=lambda item: item.value))


def test_invalid_registry_handling_does_not_swallow_unrelated_programmer_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.discipline_packages.compatibility as compatibility_module

    descriptor = _descriptor("programmer_failure_package")
    registry = _registry(descriptor)

    def programmer_failure(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError("programmer failure")

    monkeypatch.setattr(compatibility_module, "assemble_registry", programmer_failure)
    with pytest.raises(RuntimeError, match="programmer failure"):
        evaluate_package_compatibility(CompatibilityInputV1(
            registry=registry, core_contract_version=1, selections=(_selection(descriptor),),
        ))


def test_migration_declarations_require_the_matching_guard_and_accept_it_when_present() -> None:
    old = _descriptor("upgrade_package", "1.0.0")
    migration = MigrationCompatibilityDeclarationV1(**_base(
        id="upgrade.v1_to_v11", from_package_key="upgrade_package", from_package_version="1.0.0",
        to_package_key="upgrade_package", to_package_version="1.1.0", direction="forward",
        migration_guard_id="upgrade.guard", reversible=False,
    ))
    target = _descriptor(
        "upgrade_package", "1.1.0",
        contributions=PackageContributionsV1(
            migration_compatibility=(migration,),
            resource_declaration=ResourceDeclarationV1(migration_compatibility_entries=1),
        ),
    )
    registry = _registry(old, target)
    unsatisfied = evaluate_package_compatibility(CompatibilityInputV1(
        registry=registry, core_contract_version=1, selections=(_selection(target),), existing_selections=(_selection(old),),
    ))
    assert DisciplinePackageReasonCode.MIGRATION_INCOMPATIBLE in unsatisfied.reason_codes
    satisfied = evaluate_package_compatibility(CompatibilityInputV1(
        registry=registry, core_contract_version=1, selections=(_selection(target),), existing_selections=(_selection(old),),
        satisfied_migration_guard_ids=frozenset({"upgrade.guard"}),
    ))
    assert satisfied.decision is CompatibilityDecision.COMPATIBLE
