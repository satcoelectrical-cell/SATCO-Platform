"""Narrow typed seams owned by the pure PATCH-051 Core contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.enums.discipline_package import EntitlementDecision, EntitlementOperation


class PackageContextContributionPort(Protocol):
    def declarations(self) -> tuple[object, ...]: ...


class PackageObjectContributionPort(Protocol):
    def declarations(self) -> tuple[object, ...]: ...


class PackageRelationshipContributionPort(Protocol):
    def declarations(self) -> tuple[object, ...]: ...


class PackageInterfaceDeclarationPort(Protocol):
    def declarations(self) -> tuple[object, ...]: ...


class PackageEvidenceRequirementPort(Protocol):
    def declarations(self) -> tuple[object, ...]: ...


class PackageRuleContributionPort(Protocol):
    def declarations(self) -> tuple[object, ...]: ...


@dataclass(frozen=True, slots=True)
class EntitlementRequest:
    trusted_organization_id: UUID
    trusted_deployment_id: str
    package_key: str
    entitlement_key: str
    operation: EntitlementOperation


class EntitlementDecisionPort(Protocol):
    def evaluate(self, request: EntitlementRequest) -> EntitlementDecision: ...
