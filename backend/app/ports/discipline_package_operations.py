"""Read-only Batch-1 package catalog boundary; later batches own mutations."""

from __future__ import annotations

from typing import Protocol

from app.discipline_packages.operational import OperationalPackageContractV1


class DisciplinePackageCatalogPort(Protocol):
    def contract(self, package_key: str, package_version: str) -> OperationalPackageContractV1 | None: ...
