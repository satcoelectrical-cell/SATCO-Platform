"""Closed safe failures for trusted Discipline Package Core operations."""

from __future__ import annotations

from enum import Enum


class DisciplinePackageReasonCode(str, Enum):
    INVALID_IDENTITY = "invalid_identity"
    INVALID_DESCRIPTOR = "invalid_descriptor"
    INVALID_CONTRIBUTION = "invalid_contribution"
    DUPLICATE_DESCRIPTOR = "duplicate_descriptor"
    DUPLICATE_ADAPTER = "duplicate_adapter"
    STATIC_ADAPTER_REQUIRED = "static_adapter_required"
    REGISTRY_UNAVAILABLE = "registry_unavailable"
    REGISTRY_DIGEST_MISMATCH = "registry_digest_mismatch"
    UNSUPPORTED_VERSION = "unsupported_version"
    HISTORICAL_ONLY = "historical_only"
    ORGANIZATION_DISABLED = "organization_disabled"
    CORE_CONTRACT_MISMATCH = "core_contract_mismatch"
    MISSING_DEPENDENCY = "missing_dependency"
    DECLARED_CONFLICT = "declared_conflict"
    PROFILE_NOT_ALLOWED = "profile_not_allowed"
    TAXONOMY_COLLISION = "taxonomy_collision"
    CONTRIBUTION_COLLISION = "contribution_collision"
    MIGRATION_REQUIRED = "migration_required"
    MIGRATION_INCOMPATIBLE = "migration_incompatible"
    RESOURCE_LIMIT_EXCEEDED = "resource_limit_exceeded"
    LEGACY_UNRESOLVED = "legacy_unresolved"


class DisciplinePackageError(ValueError):
    """A deliberately detail-free public failure carrying a closed code."""

    def __init__(self, reason_code: DisciplinePackageReasonCode, message: str = "") -> None:
        self.reason_code = reason_code
        super().__init__(message or reason_code.value)


class RegistryAssemblyError(DisciplinePackageError):
    """The trusted in-memory source Registry could not be assembled."""
