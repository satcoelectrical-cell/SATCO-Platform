"""Closed, bounded declaration contracts for PATCH-051 Core contributions."""

from __future__ import annotations

import re
from typing import Callable, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.exceptions.discipline_package import DisciplinePackageError, DisciplinePackageReasonCode


_ID_PATTERN = r"^[a-z][a-z0-9_.-]*$"
_SEMVER_PATTERN = r"^(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})(?:-([0-9A-Za-z-]{1,16}(?:\.[0-9A-Za-z-]{1,16})*))?$"

MAX_REGISTERED_DESCRIPTOR_VERSIONS = 32
MAX_EXECUTABLE_DESCRIPTOR_VERSIONS = 16
MAX_DESCRIPTOR_CANONICAL_BYTES = 256 * 1024
MAX_REGISTRY_CANONICAL_BYTES = 4 * 1024 * 1024
MAX_PROFILES = 32
MAX_COMBINATIONS_PER_PROFILE = 32
MAX_SELECTIONS_PER_COMBINATION = 8
MAX_DEPENDENCIES = 8
MAX_CONFLICTS = 8
MAX_DEPENDENCY_DEPTH = 4
MAX_DEPENDENCY_VISITS = 32
MAX_TAXONOMY_FAMILIES = 32
MAX_OBJECT_TYPES = 256
MAX_RELATIONSHIP_TYPES = 128
MAX_CONTEXT_CONTRIBUTIONS = 64
MAX_ENGINEERING_INPUTS = 128
MAX_DELIVERABLES = 128
MAX_EVIDENCE_REQUIREMENTS = 64
MAX_DETERMINISTIC_RULE_HOOKS = 128
MAX_ROLE_REQUIREMENTS = 32
MAX_AUTHORIZATION_REQUIREMENTS = 32
MAX_MIGRATION_COMPATIBILITY_ENTRIES = 16
MAX_CONFORMANCE_EVIDENCE = 256


class _FrozenStrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


T = TypeVar("T")


def _sorted_unique_strings(values: tuple[str, ...]) -> tuple[str, ...]:
    if len(values) != len(set(values)) or any(re.fullmatch(_ID_PATTERN, value) is None for value in values):
        raise ValueError("identifiers must be unique trusted identifiers")
    return tuple(sorted(values))


def _sorted_unique_models(values: tuple[T, ...], identity: Callable[[T], str]) -> tuple[T, ...]:
    identities = tuple(identity(value) for value in values)
    if len(identities) != len(set(identities)):
        raise ValueError("declaration identities must be unique")
    return tuple(item for _, item in sorted(zip(identities, values, strict=True), key=lambda item: item[0]))


class ContributionDeclarationV1(_FrozenStrictModel):
    """Closed metadata shared by ordinary contribution declarations."""

    schema_version: Literal[1] = 1
    id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)
    version: str = Field(pattern=_SEMVER_PATTERN, min_length=5, max_length=32)
    owner: Literal["CORE", "PACKAGE"]
    ordinal: int = Field(ge=1, strict=True)
    display_name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)


class TaxonomyFamilyDeclarationV1(ContributionDeclarationV1):
    ordinal: int = Field(ge=1, le=MAX_TAXONOMY_FAMILIES, strict=True)
    parent_family_id: str | None = Field(default=None, pattern=_ID_PATTERN, max_length=128)
    collision_namespace: Literal["taxonomy_family"] = "taxonomy_family"


class ObjectTypeDeclarationV1(ContributionDeclarationV1):
    ordinal: int = Field(ge=1, le=MAX_OBJECT_TYPES, strict=True)
    family_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)
    lifecycle_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)
    required_context_kind_ids: tuple[str, ...] = Field(default=(), max_length=64)
    authority_requirement_ids: tuple[str, ...] = Field(default=(), max_length=32)

    @field_validator("required_context_kind_ids", "authority_requirement_ids")
    @classmethod
    def _ordered_ids(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _sorted_unique_strings(values)


class RelationshipTypeDeclarationV1(ContributionDeclarationV1):
    ordinal: int = Field(ge=1, le=MAX_RELATIONSHIP_TYPES, strict=True)
    source_object_family_ids: tuple[str, ...] = Field(min_length=1, max_length=256)
    target_object_family_ids: tuple[str, ...] = Field(min_length=1, max_length=256)
    direction: Literal["directed", "bidirectional"]
    cardinality: Literal["one_to_one", "one_to_many", "many_to_one", "many_to_many"]
    lifecycle_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)

    @field_validator("source_object_family_ids", "target_object_family_ids")
    @classmethod
    def _ordered_families(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _sorted_unique_strings(values)


class ContextContributionDeclarationV1(ContributionDeclarationV1):
    ordinal: int = Field(ge=1, le=MAX_CONTEXT_CONTRIBUTIONS, strict=True)
    context_kind_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)
    allowed_subject_kind_ids: tuple[str, ...] = Field(min_length=1, max_length=128)
    value_schema_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)
    required: bool

    @field_validator("allowed_subject_kind_ids")
    @classmethod
    def _ordered_subjects(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _sorted_unique_strings(values)


class EngineeringInputDeclarationV1(ContributionDeclarationV1):
    ordinal: int = Field(ge=1, le=MAX_ENGINEERING_INPUTS, strict=True)
    input_type_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)
    source_kind: Literal["context", "evidence"]
    required: bool
    max_occurrences: int = Field(ge=1, le=128)


class DeliverableDeclarationV1(ContributionDeclarationV1):
    ordinal: int = Field(ge=1, le=MAX_DELIVERABLES, strict=True)
    deliverable_type_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)
    required_input_ids: tuple[str, ...] = Field(default=(), max_length=128)
    output_representation_ids: tuple[str, ...] = Field(min_length=1, max_length=128)
    human_acceptance_required: bool

    @field_validator("required_input_ids", "output_representation_ids")
    @classmethod
    def _ordered_ids(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _sorted_unique_strings(values)


class EvidenceRequirementDeclarationV1(ContributionDeclarationV1):
    ordinal: int = Field(ge=1, le=MAX_EVIDENCE_REQUIREMENTS, strict=True)
    evidence_kind_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)
    minimum_count: int = Field(ge=1, le=128)
    applicable_operation_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)
    human_verification_required: bool


class DeterministicRuleHookDeclarationV1(ContributionDeclarationV1):
    ordinal: int = Field(ge=1, le=MAX_DETERMINISTIC_RULE_HOOKS, strict=True)
    hook_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)
    hook_version: str = Field(pattern=_SEMVER_PATTERN, min_length=5, max_length=32)
    input_schema_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)
    output_schema_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)
    max_findings: int = Field(ge=0, le=1000)
    timeout_ms: int = Field(ge=1, le=60_000)


class StandardsApplicabilityHookV1(_FrozenStrictModel):
    hook_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)
    version: str = Field(pattern=_SEMVER_PATTERN, min_length=5, max_length=32)
    input_schema_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)
    output_schema_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)
    max_results: int = Field(ge=0, le=1000)
    timeout_ms: int = Field(ge=1, le=60_000)


class InterfaceDeclarationV1(_FrozenStrictModel):
    interface_type_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)
    source_discipline_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=64)
    target_discipline_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=64)
    dependency_kind: Literal["requires", "provides", "constrains"]
    consistency_check_id: str | None = Field(default=None, pattern=_ID_PATTERN, max_length=128)
    change_impact_hook_id: str | None = Field(default=None, pattern=_ID_PATTERN, max_length=128)
    version: str = Field(pattern=_SEMVER_PATTERN, min_length=5, max_length=32)


class RoleRequirementDeclarationV1(ContributionDeclarationV1):
    ordinal: int = Field(ge=1, le=MAX_ROLE_REQUIREMENTS, strict=True)
    operation_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)
    accepted_human_role_ids: tuple[str, ...] = Field(min_length=1, max_length=32)
    minimum_authority_predicate_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)

    @field_validator("accepted_human_role_ids")
    @classmethod
    def _ordered_roles(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _sorted_unique_strings(values)


class AuthorizationRequirementDeclarationV1(ContributionDeclarationV1):
    ordinal: int = Field(ge=1, le=MAX_AUTHORIZATION_REQUIREMENTS, strict=True)
    operation_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)
    source_owner_policy_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)
    package_policy_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)
    composition: Literal["intersection"] = "intersection"


class FrontendMetadataV1(_FrozenStrictModel):
    route_keys: tuple[str, ...] = Field(default=(), max_length=32)
    navigation_keys: tuple[str, ...] = Field(default=(), max_length=32)
    component_keys: tuple[str, ...] = Field(default=(), max_length=64)
    visibility_predicate_id: str | None = Field(default=None, pattern=_ID_PATTERN, max_length=128)

    @field_validator("route_keys", "navigation_keys", "component_keys")
    @classmethod
    def _valid_keys(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _sorted_unique_strings(values)


class ResourceDeclarationV1(_FrozenStrictModel):
    taxonomy_families: int = Field(default=0, ge=0, le=32)
    object_types: int = Field(default=0, ge=0, le=256)
    relationship_types: int = Field(default=0, ge=0, le=128)
    context_kinds: int = Field(default=0, ge=0, le=64)
    engineering_inputs: int = Field(default=0, ge=0, le=128)
    deliverables: int = Field(default=0, ge=0, le=128)
    evidence_requirements: int = Field(default=0, ge=0, le=64)
    deterministic_rule_hooks: int = Field(default=0, ge=0, le=128)
    standards_hooks: int = Field(default=0, ge=0, le=32)
    cross_discipline_interfaces: int = Field(default=0, ge=0, le=128)
    role_requirements: int = Field(default=0, ge=0, le=32)
    authorization_requirements: int = Field(default=0, ge=0, le=32)
    migration_compatibility_entries: int = Field(default=0, ge=0, le=16)
    conformance_vectors: int = Field(default=0, ge=0, le=256)
    adapter_timeout_class_id: str = Field(default="default", pattern=_ID_PATTERN, max_length=128)
    adapter_memory_class_id: str = Field(default="default", pattern=_ID_PATTERN, max_length=128)

    def aggregate_units(self) -> int:
        return sum((
            self.taxonomy_families, self.object_types, self.relationship_types,
            self.context_kinds, self.engineering_inputs, self.deliverables,
            self.evidence_requirements, self.deterministic_rule_hooks,
            self.standards_hooks, self.cross_discipline_interfaces,
            self.role_requirements, self.authorization_requirements,
            self.migration_compatibility_entries, self.conformance_vectors,
        ))


class MigrationCompatibilityDeclarationV1(ContributionDeclarationV1):
    ordinal: int = Field(ge=1, le=MAX_MIGRATION_COMPATIBILITY_ENTRIES, strict=True)
    from_package_key: str = Field(pattern=r"^[a-z][a-z0-9_]{0,63}$", min_length=1, max_length=64)
    from_package_version: str = Field(pattern=_SEMVER_PATTERN, min_length=5, max_length=32)
    to_package_key: str = Field(pattern=r"^[a-z][a-z0-9_]{0,63}$", min_length=1, max_length=64)
    to_package_version: str = Field(pattern=_SEMVER_PATTERN, min_length=5, max_length=32)
    direction: Literal["forward", "backward"]
    migration_guard_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)
    reversible: bool


class ConformanceEvidenceDeclarationV1(ContributionDeclarationV1):
    ordinal: int = Field(ge=1, le=MAX_CONFORMANCE_EVIDENCE, strict=True)
    vector_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)
    contract_version: str = Field(pattern=_SEMVER_PATTERN, min_length=5, max_length=32)
    suite_version: str = Field(pattern=_SEMVER_PATTERN, min_length=5, max_length=32)
    expected_result_digest: str = Field(pattern=r"^[0-9a-f]{64}$", min_length=64, max_length=64)
    reviewed_source_reference: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)


class PackageContributionsV1(_FrozenStrictModel):
    taxonomy_families: tuple[TaxonomyFamilyDeclarationV1, ...] = Field(default=(), max_length=MAX_TAXONOMY_FAMILIES)
    object_types: tuple[ObjectTypeDeclarationV1, ...] = Field(default=(), max_length=MAX_OBJECT_TYPES)
    relationship_types: tuple[RelationshipTypeDeclarationV1, ...] = Field(default=(), max_length=MAX_RELATIONSHIP_TYPES)
    context_contributions: tuple[ContextContributionDeclarationV1, ...] = Field(default=(), max_length=MAX_CONTEXT_CONTRIBUTIONS)
    engineering_inputs: tuple[EngineeringInputDeclarationV1, ...] = Field(default=(), max_length=MAX_ENGINEERING_INPUTS)
    deliverables: tuple[DeliverableDeclarationV1, ...] = Field(default=(), max_length=MAX_DELIVERABLES)
    evidence_requirements: tuple[EvidenceRequirementDeclarationV1, ...] = Field(default=(), max_length=MAX_EVIDENCE_REQUIREMENTS)
    deterministic_rule_hooks: tuple[DeterministicRuleHookDeclarationV1, ...] = Field(default=(), max_length=MAX_DETERMINISTIC_RULE_HOOKS)
    standards_hooks: tuple[StandardsApplicabilityHookV1, ...] = Field(default=(), max_length=32)
    cross_discipline_interfaces: tuple[InterfaceDeclarationV1, ...] = Field(default=(), max_length=128)
    role_requirements: tuple[RoleRequirementDeclarationV1, ...] = Field(default=(), max_length=MAX_ROLE_REQUIREMENTS)
    authorization_requirements: tuple[AuthorizationRequirementDeclarationV1, ...] = Field(default=(), max_length=MAX_AUTHORIZATION_REQUIREMENTS)
    frontend_metadata: FrontendMetadataV1 = Field(default_factory=FrontendMetadataV1)
    resource_declaration: ResourceDeclarationV1 = Field(default_factory=ResourceDeclarationV1)
    migration_compatibility: tuple[MigrationCompatibilityDeclarationV1, ...] = Field(default=(), max_length=MAX_MIGRATION_COMPATIBILITY_ENTRIES)
    conformance_evidence: tuple[ConformanceEvidenceDeclarationV1, ...] = Field(default=(), max_length=MAX_CONFORMANCE_EVIDENCE)

    @field_validator(
        "taxonomy_families", "object_types", "relationship_types", "context_contributions",
        "engineering_inputs", "deliverables", "evidence_requirements", "deterministic_rule_hooks",
        "role_requirements", "authorization_requirements", "migration_compatibility", "conformance_evidence",
    )
    @classmethod
    def _ordered_declarations(cls, values: tuple[ContributionDeclarationV1, ...]) -> tuple[ContributionDeclarationV1, ...]:
        return _sorted_unique_models(values, lambda item: item.id)

    @field_validator("standards_hooks")
    @classmethod
    def _ordered_standards(cls, values: tuple[StandardsApplicabilityHookV1, ...]) -> tuple[StandardsApplicabilityHookV1, ...]:
        return _sorted_unique_models(values, lambda item: item.hook_id)

    @field_validator("cross_discipline_interfaces")
    @classmethod
    def _ordered_interfaces(cls, values: tuple[InterfaceDeclarationV1, ...]) -> tuple[InterfaceDeclarationV1, ...]:
        return _sorted_unique_models(values, lambda item: item.interface_type_id)

    @model_validator(mode="after")
    def _matching_counts(self) -> "PackageContributionsV1":
        sections = (
            (self.taxonomy_families, self.resource_declaration.taxonomy_families),
            (self.object_types, self.resource_declaration.object_types),
            (self.relationship_types, self.resource_declaration.relationship_types),
            (self.context_contributions, self.resource_declaration.context_kinds),
            (self.engineering_inputs, self.resource_declaration.engineering_inputs),
            (self.deliverables, self.resource_declaration.deliverables),
            (self.evidence_requirements, self.resource_declaration.evidence_requirements),
            (self.deterministic_rule_hooks, self.resource_declaration.deterministic_rule_hooks),
            (self.role_requirements, self.resource_declaration.role_requirements),
            (self.authorization_requirements, self.resource_declaration.authorization_requirements),
            (self.migration_compatibility, self.resource_declaration.migration_compatibility_entries),
            (self.conformance_evidence, self.resource_declaration.conformance_vectors),
        )
        if any(len(declarations) != declared_count for declarations, declared_count in sections):
            raise DisciplinePackageError(DisciplinePackageReasonCode.INVALID_CONTRIBUTION)
        if len(self.standards_hooks) != self.resource_declaration.standards_hooks:
            raise DisciplinePackageError(DisciplinePackageReasonCode.INVALID_CONTRIBUTION)
        if len(self.cross_discipline_interfaces) != self.resource_declaration.cross_discipline_interfaces:
            raise DisciplinePackageError(DisciplinePackageReasonCode.INVALID_CONTRIBUTION)
        return self
