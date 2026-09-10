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
from .cross_discipline.definitions.eic_v1 import (
    load_batch_one_definition_set,
    validate_batch_one_definition_set,
)

__all__ += (
    "load_batch_one_definition_set",
    "validate_batch_one_definition_set",
)
