"""Control & Automation V1 binding to the accepted shared package mechanics."""

from app.discipline_packages.descriptors.eic_v1 import (
    CONTROL_AUTOMATION_OBJECT_DECLARATIONS,
    CONTROL_AUTOMATION_RELATIONSHIP_DECLARATIONS,
)
from app.services.electrical_package_service import ElectricalPackageService


class ControlAutomationPackageService(ElectricalPackageService):
    """Uses the shared UoW/guard while preserving legacy owner identities."""

    PACKAGE_KEY = "control_automation"
    PACKAGE_TITLE = "ControlAutomation"
    OBJECT_FAMILY = "automation"
    OWNER_DISCIPLINE = "industrial_automation"
    RELATIONSHIP_FAMILY = "automation"
    OBJECT_DECLARATIONS = CONTROL_AUTOMATION_OBJECT_DECLARATIONS
    RELATIONSHIP_DECLARATIONS = CONTROL_AUTOMATION_RELATIONSHIP_DECLARATIONS
