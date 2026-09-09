"""Composition root for the non-mutating PATCH-052 Batch-1 catalog service."""

from app.adapters.discipline_package_operations import StaticDisciplinePackageCatalogAdapter
from app.services.discipline_package_operation_service import DisciplinePackageOperationService


def get_discipline_package_operation_service() -> DisciplinePackageOperationService:
    return DisciplinePackageOperationService(StaticDisciplinePackageCatalogAdapter())
