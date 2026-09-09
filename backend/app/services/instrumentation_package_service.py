"""Instrumentation V1 binding to the accepted shared package mechanics."""

from app.discipline_packages.descriptors.eic_v1 import (
    INSTRUMENTATION_OBJECT_DECLARATIONS,
    INSTRUMENTATION_RELATIONSHIP_DECLARATIONS,
)
from app.services.electrical_package_service import ElectricalPackageService


class InstrumentationPackageService(ElectricalPackageService):
    """Uses the shared UoW/guard with Instrumentation's finite semantics."""

    PACKAGE_KEY = "instrumentation"
    PACKAGE_TITLE = "Instrumentation"
    OBJECT_FAMILY = "instrumentation"
    OWNER_DISCIPLINE = "instrumentation"
    RELATIONSHIP_FAMILY = "instrumentation"
    OBJECT_DECLARATIONS = INSTRUMENTATION_OBJECT_DECLARATIONS
    RELATIONSHIP_DECLARATIONS = INSTRUMENTATION_RELATIONSHIP_DECLARATIONS
