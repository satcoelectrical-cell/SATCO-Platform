from enum import StrEnum


class EngineeringObjectFamily(StrEnum):
    INSTRUMENTATION = "instrumentation"
    ELECTRICAL = "electrical"
    AUTOMATION = "automation"
    SHARED = "shared"


class EngineeringDiscipline(StrEnum):
    INSTRUMENTATION = "instrumentation"
    ELECTRICAL = "electrical"
    INDUSTRIAL_AUTOMATION = "industrial_automation"
    SHARED_ENGINEERING = "shared_engineering"


class EngineeringLifecycle(StrEnum):
    PROPOSED = "proposed"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"
    RETIRED = "retired"


class EngineeringAuthorityStanding(StrEnum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    DISPUTED = "disputed"
    REJECTED = "rejected"


class EngineeringConfidentiality(StrEnum):
    ORGANIZATION = "organization"
    CUSTOMER = "customer"
    PROJECT = "project"
    WORKSPACE = "workspace"
    RESTRICTED = "restricted"


class EngineeringRelationshipFamily(StrEnum):
    STRUCTURAL = "structural"
    PHYSICAL = "physical"
    ELECTRICAL = "electrical"
    INSTRUMENTATION = "instrumentation"
    AUTOMATION = "automation"
    EVIDENCE = "evidence"
    DEPENDENCY = "dependency"
    GOVERNANCE = "governance"


class EngineeringIdentifierKind(StrEnum):
    TAG_NUMBER = "tag_number"
    EQUIPMENT_NUMBER = "equipment_number"
    LOOP_NUMBER = "loop_number"
    CABLE_NUMBER = "cable_number"
    PANEL_NUMBER = "panel_number"
    FEEDER_NUMBER = "feeder_number"
    SYSTEM_IDENTIFIER = "system_identifier"
    SUBSYSTEM_IDENTIFIER = "subsystem_identifier"
    VENDOR_REFERENCE = "vendor_reference"
    MANUFACTURER_MODEL_REFERENCE = "manufacturer_model_reference"
    CONTROLLED_EXTERNAL_KEY = "controlled_external_key"


class EngineeringResponsibilityRole(StrEnum):
    CREATOR = "creator"
    OWNER = "owner"
    STEWARD = "steward"
    DISCIPLINE_OWNER = "discipline_owner"
    REVIEWER = "reviewer"
    APPROVER = "approver"
    ASSIGNEE = "assignee"
    SOURCE_AUTHORITY = "source_authority"
