from enum import StrEnum


class RiskStanding(StrEnum): OPEN="open"; TREATED="treated"; ACCEPTED="accepted"; CLOSED="closed"
class IssueStanding(StrEnum): OPEN="open"; RESOLVED="resolved"; CLOSED="closed"
class DecisionStanding(StrEnum): DRAFT="draft"; ACCEPTED="accepted"; SUPERSEDED="superseded"
class ChangeStanding(StrEnum): RECORDED="recorded"; CONFIRMED="confirmed"; WITHDRAWN="withdrawn"
class ImpactStanding(StrEnum): POTENTIAL="potential"; CONFIRMED="confirmed"
class ImpactTargetKind(StrEnum): ACTIVITY="activity"; MILESTONE="milestone"; DELIVERABLE="deliverable"; DELIVERABLE_REVISION="deliverable_revision"; EVIDENCE="evidence"; SUPPORTING_FILE="supporting_file"
