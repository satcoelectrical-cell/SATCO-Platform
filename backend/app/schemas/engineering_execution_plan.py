from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.enums.engineering_execution_plan import ExecutionActivityStanding, ExecutionMilestoneStanding


class StrictExecutionSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


def clean_execution_text(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not value:
        raise ValueError("value must not be empty")
    return value


class ExecutionActor(StrictExecutionSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    actor_id: int = Field(gt=0)
    organization_id: UUID


class EstablishExecutionPlanRequest(StrictExecutionSchema):
    expected_plan_version: Literal[0]
    rationale: str = Field(min_length=1, max_length=2000)
    @field_validator("rationale")
    @classmethod
    def clean(cls, value: str) -> str: return clean_execution_text(value)


class ActivityFields(StrictExecutionSchema):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    ordinal: int = Field(ge=0, le=199)
    workspace_id: int | None = Field(None, gt=0)
    responsible_user_id: int | None = Field(None, gt=0)
    target_date: date | None = None
    completion_basis: str = Field(min_length=1, max_length=2000)

    @field_validator("title", "completion_basis")
    @classmethod
    def clean_required(cls, value: str) -> str: return clean_execution_text(value)

    @field_validator("description")
    @classmethod
    def clean_optional(cls, value: str | None) -> str | None:
        return None if value is None else clean_execution_text(value)


class CreateExecutionActivityRequest(ActivityFields):
    expected_plan_version: int = Field(ge=1)
    rationale: str = Field(min_length=1, max_length=2000)
    @field_validator("rationale")
    @classmethod
    def clean_rationale(cls, value: str) -> str: return clean_execution_text(value)


class UpdateExecutionActivityRequest(ActivityFields):
    expected_plan_version: int = Field(ge=1)
    expected_activity_version: int = Field(ge=1)
    rationale: str = Field(min_length=1, max_length=2000)
    @field_validator("rationale")
    @classmethod
    def clean_rationale(cls, value: str) -> str: return clean_execution_text(value)


class TransitionExecutionActivityRequest(StrictExecutionSchema):
    expected_activity_version: int = Field(ge=1)
    target_standing: ExecutionActivityStanding
    rationale: str = Field(min_length=1, max_length=2000)
    @field_validator("rationale")
    @classmethod
    def clean_rationale(cls, value: str) -> str: return clean_execution_text(value)


class ExecutionDependencyDTO(StrictExecutionSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    predecessor_activity_id: UUID
    dependent_activity_id: UUID
    @model_validator(mode="after")
    def no_self(self):
        if self.predecessor_activity_id == self.dependent_activity_id:
            raise ValueError("self dependency is invalid")
        return self


class ReplaceExecutionDependenciesRequest(StrictExecutionSchema):
    expected_plan_version: int = Field(ge=1)
    dependencies: tuple[ExecutionDependencyDTO, ...] = Field(max_length=500)
    rationale: str = Field(min_length=1, max_length=2000)
    @field_validator("rationale")
    @classmethod
    def clean_rationale(cls, value: str) -> str: return clean_execution_text(value)
    @field_validator("dependencies")
    @classmethod
    def unique_edges(cls, value: tuple[ExecutionDependencyDTO, ...]):
        keys = {(item.predecessor_activity_id, item.dependent_activity_id) for item in value}
        if len(keys) != len(value): raise ValueError("dependencies must be unique")
        return tuple(sorted(value, key=lambda edge: (str(edge.predecessor_activity_id), str(edge.dependent_activity_id))))


class MilestoneFields(StrictExecutionSchema):
    title: str = Field(min_length=1, max_length=200)
    completion_basis: str = Field(min_length=1, max_length=2000)
    target_date: date | None = None
    ordinal: int = Field(ge=0, le=49)
    activity_ids: tuple[UUID, ...] = Field(max_length=200)
    @field_validator("title", "completion_basis")
    @classmethod
    def clean_required(cls, value: str) -> str: return clean_execution_text(value)
    @field_validator("activity_ids")
    @classmethod
    def unique_ids(cls, value: tuple[UUID, ...]):
        if len(set(value)) != len(value): raise ValueError("activity identities must be unique")
        return value


class CreateExecutionMilestoneRequest(MilestoneFields):
    expected_plan_version: int = Field(ge=1)
    rationale: str = Field(min_length=1, max_length=2000)
    @field_validator("rationale")
    @classmethod
    def clean_rationale(cls, value: str) -> str: return clean_execution_text(value)


class UpdateExecutionMilestoneRequest(MilestoneFields):
    expected_plan_version: int = Field(ge=1)
    rationale: str = Field(min_length=1, max_length=2000)
    @field_validator("rationale")
    @classmethod
    def clean_rationale(cls, value: str) -> str: return clean_execution_text(value)


class ExecutionActivityDTO(ActivityFields):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: UUID
    standing: ExecutionActivityStanding
    version: int = Field(ge=1)
    blocker_rationale: str | None = None
    updated_at: datetime


class ExecutionMilestoneDTO(MilestoneFields):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: UUID
    standing: ExecutionMilestoneStanding


class ExecutionProgressDTO(StrictExecutionSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    completed_count: int = Field(ge=0, le=200)
    eligible_count: int = Field(ge=0, le=200)
    percent: int = Field(ge=0, le=100)
    @model_validator(mode="after")
    def derived(self):
        expected = 0 if not self.eligible_count else (100 * self.completed_count) // self.eligible_count
        if self.percent != expected: raise ValueError("progress must be derived")
        return self


class ExecutionPlanNotEstablished(StrictExecutionSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    outcome: Literal["success"] = "success"
    availability: Literal["plan_not_established"] = "plan_not_established"
    project_id: int = Field(gt=0)
    allowed_actions: tuple[Literal["establish"], ...] = ()


class ExecutionPlanEstablished(StrictExecutionSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    outcome: Literal["success"] = "success"
    availability: Literal["established"] = "established"
    project_id: int = Field(gt=0)
    plan_id: UUID
    version: int = Field(ge=1)
    activities: tuple[ExecutionActivityDTO, ...] = Field(max_length=200)
    milestones: tuple[ExecutionMilestoneDTO, ...] = Field(max_length=50)
    dependencies: tuple[ExecutionDependencyDTO, ...] = Field(max_length=500)
    progress: ExecutionProgressDTO


class ExecutionPlanMutationSuccess(StrictExecutionSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    outcome: Literal["success"] = "success"
    project_id: int = Field(gt=0)
    plan_id: UUID
    plan_version: int = Field(ge=1)
    activity_id: UUID | None = None
    milestone_id: UUID | None = None
    activity_version: int | None = Field(None, ge=1)
    standing: ExecutionActivityStanding | None = None


class ExecutionPlanProtectedResult(StrictExecutionSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    outcome: Literal["protected_not_found"] = "protected_not_found"


class ExecutionPlanInvalidResult(StrictExecutionSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    outcome: Literal["invalid_request"] = "invalid_request"


class ExecutionPlanVersionConflictResult(StrictExecutionSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    outcome: Literal["version_conflict"] = "version_conflict"


class ExecutionPlanIdempotencyConflictResult(StrictExecutionSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    outcome: Literal["idempotency_conflict"] = "idempotency_conflict"


class ExecutionPlanUnavailableResult(StrictExecutionSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    outcome: Literal["unavailable"] = "unavailable"
