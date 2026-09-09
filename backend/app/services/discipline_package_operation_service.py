"""Authorization-first shared catalog service for PATCH-052 Batch 1."""

from __future__ import annotations

from app.ports.discipline_package_operations import DisciplinePackageCatalogPort


class DisciplinePackageOperationService:
    def __init__(self, catalog: DisciplinePackageCatalogPort) -> None:
        self._catalog = catalog

    def catalog_entry(self, *, authorized: bool, package_key: str, package_version: str):
        # The caller establishes project/workspace/tenant authority before this
        # method is reached.  A single opaque None prevents catalog disclosure.
        if not authorized:
            return None
        return self._catalog.contract(package_key, package_version)
