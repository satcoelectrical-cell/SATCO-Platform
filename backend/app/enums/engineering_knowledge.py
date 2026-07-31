from enum import StrEnum


class EngineeringObjectFamily(StrEnum):
    INSTRUMENTATION = "instrumentation"
    ELECTRICAL = "electrical"
    AUTOMATION = "automation"
    SHARED = "shared"


class EngineeringObjectType(StrEnum):
    INSTRUMENT = "instrument"
    TRANSMITTER = "transmitter"
    ANALYZER = "analyzer"
    FLOWMETER = "flowmeter"
    CONTROL_VALVE = "control_valve"
    INSTRUMENT_LOOP = "instrument_loop"
    JUNCTION_BOX = "junction_box"
    INSTRUMENT_PANEL = "instrument_panel"
    MOTOR = "motor"
    TRANSFORMER = "transformer"
    MCC = "mcc"
    SWITCHGEAR = "switchgear"
    ELECTRICAL_PANEL = "electrical_panel"
    ELECTRICAL_CABLE = "electrical_cable"
    PLC = "plc"
    DCS_CONTROLLER = "dcs_controller"
    ESD_CONTROLLER = "esd_controller"
    CONTROL_CABINET = "control_cabinet"
    IO_CHANNEL = "io_channel"
    HMI = "hmi"
    CONTROL_LOGIC = "control_logic"
    PROJECT = "project"
    VENDOR = "vendor"
    REQUIREMENT = "requirement"
    STANDARD = "standard"
    DATASHEET = "datasheet"
    DRAWING = "drawing"
    TECHNICAL_DECISION = "technical_decision"


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
