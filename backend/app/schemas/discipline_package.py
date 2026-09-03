"""Strict internal DTOs for the Batch-2 Registry projection boundary."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ProjectionDescriptor(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    package_key: str = Field(min_length=1, max_length=64)
    package_version: str = Field(min_length=1, max_length=32)
    descriptor_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    primary_discipline_id: str = Field(min_length=1, max_length=64)
    adapter_id: str = Field(min_length=1, max_length=128)
    standing: str = Field(pattern=r"^(executable_supported|historical_read_only)$")
    descriptor_json: dict[str, object]


class ProjectionProfile(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    profile_id: str = Field(min_length=1, max_length=64)
    profile_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    profile_json: dict[str, object]


class ProjectionRelease(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    registry_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    release_id: str = Field(min_length=1, max_length=64)
    core_contract_version: int = Field(ge=1)
    manifest_json: dict[str, object]
    descriptors: tuple[ProjectionDescriptor, ...]
    profiles: tuple[ProjectionProfile, ...]


# Batch-4 HTTP DTOs deliberately accept only package key/version.  Descriptor
# and profile provenance are resolved from the trusted current projection by
# the server; callers cannot submit a digest or tenant identity.
class PackageSelectionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    package_key: str = Field(min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9_.-]*$")
    package_version: str = Field(min_length=1, max_length=32)


class OrganizationConfigurationReplaceInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    expected_configuration_version: int = Field(ge=0)
    enabled_selections: tuple[PackageSelectionInput, ...] = Field(max_length=16)
    rationale: str = Field(min_length=1, max_length=2000)


class ProjectConfigurationReplaceInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    expected_configuration_version: int = Field(ge=0)
    profile_id: str = Field(min_length=1, max_length=64)
    selections: tuple[PackageSelectionInput, ...] = Field(min_length=1, max_length=8)
    rationale: str = Field(min_length=1, max_length=2000)


class ProjectConfigurationRemoveInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    expected_configuration_version: int = Field(ge=1)
    rationale: str = Field(min_length=1, max_length=2000)


class CompatibilityPreflightInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    profile_id: str = Field(min_length=1, max_length=64)
    selections: tuple[PackageSelectionInput, ...] = Field(min_length=1, max_length=8)
