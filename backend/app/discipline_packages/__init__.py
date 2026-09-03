"""Pure trusted Core contracts for PATCH-051 Discipline Packages.

This package intentionally contains no database, HTTP, frontend, plugin, or
operational-discipline implementation.
"""

from .identity import (
    CombinationDigest,
    CoreContractVersion,
    DescriptorDigest,
    DisciplineId,
    EntitlementKey,
    PackageKey,
    PackageVersion,
    ProfileDigest,
    RegistryDigest,
    SelectedDescriptorSetDigest,
)

__all__ = (
    "CombinationDigest",
    "CoreContractVersion",
    "DescriptorDigest",
    "DisciplineId",
    "EntitlementKey",
    "PackageKey",
    "PackageVersion",
    "ProfileDigest",
    "RegistryDigest",
    "SelectedDescriptorSetDigest",
)
