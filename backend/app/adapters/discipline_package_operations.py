"""Static-only implementation of the Batch-1 catalog port."""

from __future__ import annotations

from app.discipline_packages.descriptors.eic_v1 import PACKAGE_CONTRACTS_V1
from app.discipline_packages.operational import OperationalPackageContractV1, static_operation_table


class StaticDisciplinePackageCatalogAdapter:
    def __init__(self) -> None:
        self._contracts = static_operation_table(PACKAGE_CONTRACTS_V1)

    def contract(self, package_key: str, package_version: str) -> OperationalPackageContractV1 | None:
        # Values are keys into a frozen data table, never Python import paths.
        return self._contracts.get((package_key, package_version))
