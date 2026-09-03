"""Strict source-only descriptor, profile, selection and manifest contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_serializer, field_validator, model_validator

from app.discipline_packages.contributions import (
    MAX_COMBINATIONS_PER_PROFILE,
    MAX_CONFLICTS,
    MAX_DEPENDENCIES,
    MAX_PROFILES,
    MAX_SELECTIONS_PER_COMBINATION,
    PackageContributionsV1,
)
from app.discipline_packages.identity import (
    DescriptorDigest,
    PackageVersion,
    RegistryDigest,
    WORKSPACE_SELECTABLE_DISCIPLINES,
)
from app.enums.discipline_package import DisciplinePackageStanding


_ID_PATTERN = r"^[a-z][a-z0-9_.-]*$"
_PACKAGE_KEY_PATTERN = r"^[a-z][a-z0-9_]{0,63}$"
_SEMVER_PATTERN = r"^(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})(?:-([0-9A-Za-z-]{1,16}(?:\.[0-9A-Za-z-]{1,16})*))?$"


class _FrozenStrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)


class PackageReferenceV1(_FrozenStrictModel):
    package_key: str = Field(pattern=_PACKAGE_KEY_PATTERN, min_length=1, max_length=64)
    package_version: str = Field(pattern=_SEMVER_PATTERN, min_length=5, max_length=32)

    @field_validator("package_version")
    @classmethod
    def _strict_semver(cls, value: str) -> str:
        PackageVersion(value)
        return value


class ExactPackageSelectionV1(PackageReferenceV1):
    descriptor_digest: DescriptorDigest

    @field_validator("descriptor_digest", mode="before")
    @classmethod
    def _exact_descriptor_digest(cls, value: object, info: ValidationInfo) -> DescriptorDigest:
        if type(value) is DescriptorDigest:
            return value
        if info.mode == "json" and type(value) is str:
            return DescriptorDigest(value)
        raise ValueError("descriptor_digest must be DescriptorDigest")

    @field_serializer("descriptor_digest")
    def _serialize_descriptor_digest(self, value: DescriptorDigest) -> str:
        return str(value)


class AllowedCombinationV1(_FrozenStrictModel):
    members: tuple[ExactPackageSelectionV1, ...] = Field(min_length=1, max_length=MAX_SELECTIONS_PER_COMBINATION)

    @field_validator("members")
    @classmethod
    def _ordered_members(cls, values: tuple[ExactPackageSelectionV1, ...]) -> tuple[ExactPackageSelectionV1, ...]:
        keys = tuple(member.package_key for member in values)
        if len(keys) != len(set(keys)):
            raise ValueError("a compatibility combination may contain one version per package key")
        return tuple(sorted(values, key=lambda item: (item.package_key, item.package_version, str(item.descriptor_digest))))


class CompatibilityProfileV1(_FrozenStrictModel):
    schema_version: Literal[1] = 1
    profile_id: str = Field(pattern=r"^[a-z][a-z0-9_.-]{0,63}$", min_length=1, max_length=64)
    profile_version: str = Field(pattern=_SEMVER_PATTERN, min_length=5, max_length=32)
    core_contract_version: int = Field(ge=1, le=32767)
    combinations: tuple[AllowedCombinationV1, ...] = Field(min_length=1, max_length=MAX_COMBINATIONS_PER_PROFILE)
    required_interface_ids: tuple[str, ...] = Field(default=(), max_length=128)
    aggregate_resource_ceiling: int = Field(default=0, ge=0, le=1_000_000)

    @field_validator("combinations")
    @classmethod
    def _ordered_combinations(cls, values: tuple[AllowedCombinationV1, ...]) -> tuple[AllowedCombinationV1, ...]:
        identities = tuple(
            tuple((member.package_key, member.package_version, str(member.descriptor_digest)) for member in combination.members)
            for combination in values
        )
        if len(identities) != len(set(identities)):
            raise ValueError("compatibility combinations must be unique")
        return tuple(item for _, item in sorted(zip(identities, values, strict=True), key=lambda item: item[0]))

    @field_validator("required_interface_ids")
    @classmethod
    def _unique_interfaces(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(values) != len(set(values)) or any(__import__("re").fullmatch(_ID_PATTERN, value) is None for value in values):
            raise ValueError("interface identifiers must be unique")
        return tuple(sorted(values))


class DisciplinePackageDescriptorV1(_FrozenStrictModel):
    schema_version: Literal[1] = 1
    package_key: str = Field(pattern=_PACKAGE_KEY_PATTERN, min_length=1, max_length=64)
    package_version: str = Field(pattern=_SEMVER_PATTERN, min_length=5, max_length=32)
    primary_discipline_id: str = Field(pattern=_PACKAGE_KEY_PATTERN, min_length=1, max_length=64)
    core_contract_versions: tuple[int, ...] = Field(min_length=1, max_length=32)
    display_name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    entitlement_key: str = Field(pattern=r"^[a-z][a-z0-9_.-]{0,127}$", min_length=1, max_length=128)
    adapter_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)
    dependencies: tuple[PackageReferenceV1, ...] = Field(default=(), max_length=MAX_DEPENDENCIES)
    conflicts: tuple[PackageReferenceV1, ...] = Field(default=(), max_length=MAX_CONFLICTS)
    contributions: PackageContributionsV1 = Field(default_factory=PackageContributionsV1)

    @field_validator("dependencies", "conflicts")
    @classmethod
    def _ordered_references(cls, values: tuple[PackageReferenceV1, ...]) -> tuple[PackageReferenceV1, ...]:
        identities = tuple((item.package_key, item.package_version) for item in values)
        if len(identities) != len(set(identities)):
            raise ValueError("package references must be unique")
        return tuple(sorted(values, key=lambda item: (item.package_key, item.package_version)))

    @field_validator("core_contract_versions")
    @classmethod
    def _contract_versions(cls, values: tuple[int, ...]) -> tuple[int, ...]:
        if any(type(value) is not int or not 1 <= value <= 32767 for value in values):
            raise ValueError("Core contract versions must be bounded integers")
        if len(values) != len(set(values)):
            raise ValueError("Core contract versions must be unique")
        return tuple(sorted(values))

    @field_validator("package_version")
    @classmethod
    def _descriptor_semver(cls, value: str) -> str:
        PackageVersion(value)
        return value

    @field_validator("primary_discipline_id")
    @classmethod
    def _known_primary_discipline(cls, value: str) -> str:
        if value not in {item.value for item in WORKSPACE_SELECTABLE_DISCIPLINES}:
            raise ValueError("descriptor primary discipline must be Workspace-selectable")
        return value

    @model_validator(mode="after")
    def _closed_dependency_sets(self) -> "DisciplinePackageDescriptorV1":
        own = (self.package_key, self.package_version)
        dependencies = {(item.package_key, item.package_version) for item in self.dependencies}
        conflicts = {(item.package_key, item.package_version) for item in self.conflicts}
        if own in dependencies or own in conflicts or len(dependencies) != len(self.dependencies) or len(conflicts) != len(self.conflicts):
            raise ValueError("dependencies and conflicts must be unique and cannot self-reference")
        return self


class DescriptorRegistrationV1(_FrozenStrictModel):
    descriptor: DisciplinePackageDescriptorV1
    adapter_id: str = Field(pattern=_ID_PATTERN, min_length=1, max_length=128)
    standing: DisciplinePackageStanding

    @model_validator(mode="after")
    def _adapter_matches_descriptor(self) -> "DescriptorRegistrationV1":
        if self.adapter_id != self.descriptor.adapter_id:
            raise ValueError("registration adapter must equal descriptor adapter")
        return self


class RegistryReleaseManifestV1(_FrozenStrictModel):
    schema_version: Literal[1] = 1
    release_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_.-]{0,63}$", min_length=1, max_length=64)
    core_contract_version: int = Field(ge=1, le=32767)
    descriptors: tuple[DescriptorRegistrationV1, ...] = Field(default=(), max_length=32)
    profiles: tuple[CompatibilityProfileV1, ...] = Field(default=(), max_length=MAX_PROFILES)
    expected_registry_digest: RegistryDigest | None = None

    @field_validator("expected_registry_digest", mode="before")
    @classmethod
    def _exact_registry_digest(cls, value: object, info: ValidationInfo) -> RegistryDigest | None:
        if value is None:
            return None
        if type(value) is RegistryDigest:
            return value
        if info.mode == "json" and type(value) is str:
            return RegistryDigest(value)
        raise ValueError("expected_registry_digest must be RegistryDigest")

    @field_serializer("expected_registry_digest")
    def _serialize_registry_digest(self, value: RegistryDigest | None) -> str | None:
        return None if value is None else str(value)

    @field_validator("descriptors")
    @classmethod
    def _ordered_descriptors(cls, values: tuple[DescriptorRegistrationV1, ...]) -> tuple[DescriptorRegistrationV1, ...]:
        identities = tuple((item.descriptor.package_key, item.descriptor.package_version) for item in values)
        if len(identities) != len(set(identities)):
            raise ValueError("registry release contains duplicate package/version")
        return tuple(sorted(values, key=lambda item: (item.descriptor.package_key, item.descriptor.package_version)))

    @field_validator("profiles")
    @classmethod
    def _ordered_profiles(cls, values: tuple[CompatibilityProfileV1, ...]) -> tuple[CompatibilityProfileV1, ...]:
        identities = tuple((item.profile_id, item.profile_version) for item in values)
        if len(identities) != len(set(identities)):
            raise ValueError("registry release contains duplicate profile/version")
        return tuple(sorted(values, key=lambda item: (item.profile_id, item.profile_version)))

    @model_validator(mode="after")
    def _release_identity_is_unique(self) -> "RegistryReleaseManifestV1":
        identities = tuple((item.descriptor.package_key, item.descriptor.package_version) for item in self.descriptors)
        if len(identities) != len(set(identities)):
            raise ValueError("registry release contains duplicate package/version")
        profile_ids = tuple((item.profile_id, item.profile_version) for item in self.profiles)
        if len(profile_ids) != len(set(profile_ids)):
            raise ValueError("registry release contains duplicate profile/version")
        return self
