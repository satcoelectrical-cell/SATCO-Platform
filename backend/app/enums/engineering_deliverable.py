from enum import Enum


class DeliverableStanding(str, Enum):
    PLANNED = "planned"
    IN_PREPARATION = "in_preparation"
    READY_FOR_REVIEW = "ready_for_review"
    REVIEWED = "reviewed"
    ISSUED = "issued"
    WITHDRAWN = "withdrawn"
    CANCELLED = "cancelled"


class DeliverableRevisionStanding(str, Enum):
    DRAFT = "draft"
    READY_FOR_REVIEW = "ready_for_review"
    REVIEWED = "reviewed"
    ISSUED = "issued"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"


class ExternalAuthoringAuthority(str, Enum):
    CAD = "cad"
    EPLAN = "eplan"
    ETAP = "etap"
    SPREADSHEET = "spreadsheet"
    DOCUMENT = "document"
    VENDOR_TOOL = "vendor_tool"
    OTHER = "other"


def revision_transition_allowed(current: str, target: str) -> bool:
    return target in {
        "draft": {"ready_for_review", "withdrawn"},
        "ready_for_review": {"reviewed", "withdrawn"},
        "reviewed": {"issued", "withdrawn"},
        "issued": set(), "superseded": set(), "withdrawn": set(),
    }.get(current, set())
