from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.enums.project_control import RiskStanding, IssueStanding, DecisionStanding, ChangeStanding, ImpactStanding, ImpactTargetKind

class ControlSchema(BaseModel): model_config=ConfigDict(extra="forbid")
class ControlActor(ControlSchema): model_config=ConfigDict(extra="forbid",frozen=True); actor_id:int=Field(gt=0); organization_id:UUID
class ControlCommand(ControlSchema): workspace_id:int|None=Field(None,gt=0); rationale:str=Field(min_length=1,max_length=4000); expected_version:int|None=Field(None,ge=1)
class ControlTransitionCommand(ControlSchema): target_standing:str=Field(min_length=1,max_length=16); rationale:str=Field(min_length=1,max_length=4000); expected_version:int=Field(ge=1)
class RiskCommand(ControlCommand): statement:str=Field(min_length=1,max_length=2000); category:str=Field(min_length=1,max_length=80); likelihood:Literal["low","medium","high"]; impact:Literal["low","medium","high"]; owner_id:int|None=Field(None,gt=0)
class IssueCommand(ControlCommand): statement:str=Field(min_length=1,max_length=2000); observed_context:str=Field(min_length=1,max_length=4000); severity:Literal["low","medium","high"]; owner_id:int|None=Field(None,gt=0)
class DecisionCommand(ControlCommand): statement:str=Field(min_length=1,max_length=4000); alternatives:tuple[str,...]=Field(default=(),max_length=20); predecessor_id:UUID|None=None
class ChangeCommand(ControlCommand): statement:str=Field(min_length=1,max_length=4000); predecessor_id:UUID|None=None
class ImpactCommand(ControlCommand):
    change_id:UUID; target_kind:ImpactTargetKind; target_id:UUID; deliverable_id:UUID|None=None; statement:str=Field(min_length=1,max_length=2000); standing:ImpactStanding=ImpactStanding.POTENTIAL; expected_version:int=Field(ge=1)
    @model_validator(mode="after")
    def exact_revision_owner_context(self):
        if (self.target_kind is ImpactTargetKind.DELIVERABLE_REVISION) != (self.deliverable_id is not None): raise ValueError("deliverable revision requires exactly one owning deliverable")
        if self.standing is not ImpactStanding.POTENTIAL: raise ValueError("new Change Impact is always potential")
        return self
class ConfirmImpactCommand(ControlSchema): expected_change_version:int=Field(ge=1); deliverable_id:UUID|None=None; rationale:str=Field(min_length=1,max_length=4000)
class SupersedeChangeCommand(ControlSchema): successor_id:UUID; expected_predecessor_version:int=Field(ge=1); rationale:str=Field(min_length=1,max_length=4000)
class ControlSuccess(ControlSchema): outcome:Literal["success"]="success"; id:UUID; version:int=Field(ge=1)
class ImpactSuccess(ControlSchema): outcome:Literal["success"]="success"; id:UUID; change_id:UUID; standing:ImpactStanding
class ImpactRead(ControlSchema):
    id:UUID; change_id:UUID; target_kind:ImpactTargetKind; target_id:UUID; statement:str; standing:ImpactStanding; confirmed_by_id:int|None=None; confirmed_at:datetime|None=None
class ChangeImpactGraphSummary(ControlSchema):
    """Closed graph-safe projection; intentionally excludes text and Human identities."""
    model_config=ConfigDict(extra="forbid", frozen=True)
    id:UUID; change_id:UUID; project_id:int=Field(gt=0); target_kind:ImpactTargetKind; target_id:UUID; standing:ImpactStanding; impact_class:Literal["potential","human_confirmed"]
class RiskGraphSummary(ControlSchema):
    model_config=ConfigDict(extra="forbid", frozen=True)
    id:UUID; project_id:int=Field(gt=0); workspace_id:int|None=Field(None,gt=0); category:str=Field(min_length=1,max_length=80); likelihood:Literal["low","medium","high"]; impact:Literal["low","medium","high"]; standing:RiskStanding; version:int=Field(gt=0)
class IssueGraphSummary(ControlSchema):
    model_config=ConfigDict(extra="forbid", frozen=True)
    id:UUID; project_id:int=Field(gt=0); workspace_id:int|None=Field(None,gt=0); severity:Literal["low","medium","high"]; standing:IssueStanding; version:int=Field(gt=0)
class DecisionGraphSummary(ControlSchema):
    model_config=ConfigDict(extra="forbid", frozen=True)
    id:UUID; project_id:int=Field(gt=0); workspace_id:int|None=Field(None,gt=0); standing:DecisionStanding; version:int=Field(gt=0); predecessor_id:UUID|None=None
class ChangeGraphSummary(ControlSchema):
    model_config=ConfigDict(extra="forbid", frozen=True)
    id:UUID; project_id:int=Field(gt=0); workspace_id:int|None=Field(None,gt=0); standing:ChangeStanding; version:int=Field(gt=0); predecessor_id:UUID|None=None
class ProjectControlGraphIncidentLink(ControlSchema):
    model_config=ConfigDict(extra="forbid", frozen=True)
    relationship:Literal["decision_successor","change_successor","change_impact","impact_target"]
    relationship_selector:str=Field(min_length=1,max_length=200)
    source_kind:Literal["human_decision","change","change_impact"]
    source_id:UUID
    target_kind:Literal["human_decision","change","change_impact","activity","milestone","deliverable","deliverable_revision","evidence","supporting_file"]
    target_id:UUID
    owner_version:int=Field(gt=0)
class ProjectControlGraphIncidentPage(ControlSchema):
    model_config=ConfigDict(extra="forbid", frozen=True)
    items:tuple[ProjectControlGraphIncidentLink,...]=Field(max_length=91)
    has_more:bool=False
class ControlReadSuccess(ControlSuccess):
    organization_id:UUID; project_id:int=Field(gt=0); workspace_id:int|None=None; standing:str; statement:str; rationale:str|None=None; predecessor_id:UUID|None=None; owner_id:int|None=None; disposition:str|None=None; observed_context:str|None=None; alternatives:tuple[str,...]=(); accepted_by_id:int|None=None; accepted_at:datetime|None=None; confirmed_by_id:int|None=None; confirmed_at:datetime|None=None; impacts:tuple[ImpactRead,...]=()
class ControlListSuccess(ControlSchema): outcome:Literal["success"]="success"; kind:Literal["risk","issue","decision","change"]; items:tuple[ControlReadSuccess,...]=Field(max_length=100); visible_count:int=Field(ge=0,le=100)
class ControlHistoryEntry(ControlSchema): id:UUID; aggregate_version:int=Field(ge=1); event_type:str; actor_id:int=Field(gt=0); occurred_at:datetime
class ControlHistorySuccess(ControlSchema): outcome:Literal["success"]="success"; kind:Literal["risk","issue","decision","change"]; control_id:UUID; items:tuple[ControlHistoryEntry,...]=Field(max_length=100); visible_count:int=Field(ge=0,le=100)
class Protected(ControlSchema): outcome:Literal["protected_not_found"]="protected_not_found"
class Invalid(ControlSchema): outcome:Literal["invalid_request"]="invalid_request"
class Conflict(ControlSchema): outcome:Literal["version_conflict"]="version_conflict"
class IdempotencyConflict(ControlSchema): outcome:Literal["idempotency_conflict"]="idempotency_conflict"
class Unavailable(ControlSchema): outcome:Literal["unavailable"]="unavailable"
ControlResult=ControlSuccess|ControlReadSuccess|ControlListSuccess|ControlHistorySuccess|ImpactSuccess|Protected|Invalid|Conflict|IdempotencyConflict|Unavailable
