"""Static-only adapter registrations for trusted PATCH-051 source releases."""

from __future__ import annotations

from dataclasses import dataclass

from app.discipline_packages.identity import PackageKey, PackageVersion
from app.enums.discipline_package import EntitlementDecision
from app.ports.discipline_package import EntitlementRequest


@dataclass(frozen=True, slots=True)
class StaticDisciplinePackageAdapter:
    """Reviewed declarative capabilities; this object never executes package code."""

    adapter_id: str
    package_key: PackageKey
    package_version: PackageVersion
    capability_ids: frozenset[str]


def static_adapter_table() -> tuple[StaticDisciplinePackageAdapter, ...]:
    """Return the compiled release table, never plugins, entry points, or imports.

    PATCH-051 deliberately ships an empty operational-package table. PATCH-052
    may add reviewed entries through its own separately authorized release.
    """

    return ()


class NonCommercialEntitlementAdapter:
    """PATCH-051's source-controlled non-commercial entitlement decision."""

    def evaluate(self, request: EntitlementRequest) -> EntitlementDecision:
        del request
        return EntitlementDecision.NOT_REQUIRED
