from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.enums.project_foundation import (
    ProjectEngineeringStage,
    ProjectFoundationAvailability,
    ProjectInputSourceKind,
    ProjectInputStanding,
    ProjectReadinessBlockerCode,
    ProjectReadinessState,
)


class StrictProjectFoundationSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _clean(value: str) -> str:
    result = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not result:
        raise ValueError("value must not be empty")
    return result


def _unique(values: tuple[str, ...]) -> tuple[str, ...]:
    cleaned = tuple(_clean(value) for value in values)
    if len({value.casefold() for value in cleaned}) != len(cleaned):
        raise ValueError("values must be unique")
    return cleaned


class ProjectFoundationActor(StrictProjectFoundationSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    actor_id: int = Field(gt=0)
    organization_id: UUID


class PutProjectFoundationRequest(StrictProjectFoundationSchema):
    expected_version: int = Field(ge=0)
    purpose: str = Field(min_length=1, max_length=2000)
    engineering_basis: str = Field(min_length=1, max_length=5000)
    in_scope: tuple[str, ...] = Field(min_length=1, max_length=50)
    out_of_scope: tuple[str, ...] = Field(max_length=50)
    completion_criteria: tuple[str, ...] = Field(min_length=1, max_length=50)
    rationale: str = Field(min_length=1, max_length=2000)

    @field_validator("purpose", "engineering_basis", "rationale")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return _clean(value)

    @field_validator("in_scope", "out_of_scope", "completion_criteria")
    @classmethod
    def unique_text(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _unique(value)


class CreateProjectInputRequest(StrictProjectFoundationSchema):
    expected_foundation_version: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    ordinal: int = Field(ge=0, le=99)
    required_by_stage: ProjectEngineeringStage
    rationale: str = Field(min_length=1, max_length=2000)

    @field_validator("title", "rationale")
    @classmethod
    def clean_required(cls, value: str) -> str:
        return _clean(value)

    @field_validator("description")
    @classmethod
    def clean_optional(cls, value: str | None) -> str | None:
        return None if value is None else _clean(value)


class UpdateProjectInputRequest(CreateProjectInputRequest):
    expected_input_version: int = Field(ge=1)


class ReorderProjectInputsRequest(StrictProjectFoundationSchema):
    expected_foundation_version: int = Field(ge=1)
    ordered_input_ids: tuple[UUID, ...] = Field(min_length=1, max_length=100)
    rationale: str = Field(min_length=1, max_length=2000)

    @field_validator("ordered_input_ids")
    @classmethod
    def unique_ids(cls, value: tuple[UUID, ...]) -> tuple[UUID, ...]:
        if len(set(value)) != len(value):
            raise ValueError("input identities must be unique")
        return value

    @field_validator("rationale")
    @classmethod
    def clean_rationale(cls, value: str) -> str:
        return _clean(value)


class TransitionProjectInputRequest(StrictProjectFoundationSchema):
    expected_foundation_version: int = Field(ge=1)
    expected_input_version: int = Field(ge=1)
    target_standing: ProjectInputStanding
    source_kind: ProjectInputSourceKind | None = None
    source_id: UUID | None = None
    source_workspace_id: int | None = Field(None, gt=0)
    rationale: str = Field(min_length=1, max_length=2000)

    @field_validator("rationale")
    @classmethod
    def clean_rationale(cls, value: str) -> str:
        return _clean(value)

    @model_validator(mode="after")
    def source_pair(self):
        received = self.target_standing is ProjectInputStanding.RECEIVED
        if received != (self.source_kind is not None and self.source_id is not None):
            raise ValueError("received requires exactly one source")
        if not received and self.source_workspace_id is not None:
            raise ValueError("source Workspace requires received standing")
        return self


class TransitionProjectStageRequest(StrictProjectFoundationSchema):
    expected_foundation_version: int = Field(ge=1)
    target_stage: ProjectEngineeringStage
    rationale: str = Field(min_length=1, max_length=2000)

    @field_validator("rationale")
    @classmethod
    def clean_rationale(cls, value: str) -> str:
        return _clean(value)


class ProjectScopeItemDTO(StrictProjectFoundationSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: UUID
    ordinal: int = Field(ge=0, le=49)
    statement: str = Field(min_length=1, max_length=1000)


class ProjectCompletionCriterionDTO(ProjectScopeItemDTO):
    pass


class ProjectInputSafeSource(StrictProjectFoundationSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: ProjectInputSourceKind
    source_id: UUID
    version: int = Field(ge=1)
    workspace_id: int | None = Field(None, gt=0)


class ProjectRequiredInputDTO(StrictProjectFoundationSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: UUID
    title: str
    description: str | None
    ordinal: int = Field(ge=0, le=99)
    required_by_stage: ProjectEngineeringStage
    standing: ProjectInputStanding
    source_condition: Literal["not_required", "authorized_current", "source_reauthorization_required"]
    source: ProjectInputSafeSource | None = None
    version: int = Field(ge=1)
    standing_changed_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def exact_source(self):
        if (self.source_condition == "authorized_current") != (self.source is not None):
            raise ValueError("safe source is present only when authorized current")
        return self


class ProjectReadinessBlocker(StrictProjectFoundationSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    code: ProjectReadinessBlockerCode
    input_id: UUID | None = None
    input_title: str | None = None

    @model_validator(mode="after")
    def paired_input(self):
        if (self.input_id is None) != (self.input_title is None):
            raise ValueError("input blocker identity and title are paired")
        return self


class ProjectStageReadiness(StrictProjectFoundationSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    state: ProjectReadinessState
    target_stage: ProjectEngineeringStage | None
    blockers: tuple[ProjectReadinessBlocker, ...] = Field(max_length=100)

    @model_validator(mode="after")
    def coherent(self):
        if self.state is ProjectReadinessState.READY and self.blockers:
            raise ValueError("ready has no blockers")
        if self.state is ProjectReadinessState.NOT_APPLICABLE and self.target_stage is not None:
            raise ValueError("final stage readiness is not applicable")
        return self


class ProjectFoundationNotEstablished(StrictProjectFoundationSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    outcome: Literal["success"] = "success"
    availability: Literal[ProjectFoundationAvailability.BASIS_NOT_ESTABLISHED] = ProjectFoundationAvailability.BASIS_NOT_ESTABLISHED
    project_id: int = Field(gt=0)
    allowed_actions: tuple[Literal["establish"], ...] = ()


class ProjectFoundationEstablished(StrictProjectFoundationSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    outcome: Literal["success"] = "success"
    availability: Literal[ProjectFoundationAvailability.ESTABLISHED] = ProjectFoundationAvailability.ESTABLISHED
    project_id: int = Field(gt=0)
    version: int = Field(ge=1)
    purpose: str
    engineering_basis: str
    stage: ProjectEngineeringStage
    in_scope: tuple[ProjectScopeItemDTO, ...] = Field(min_length=1, max_length=50)
    out_of_scope: tuple[ProjectScopeItemDTO, ...] = Field(max_length=50)
    completion_criteria: tuple[ProjectCompletionCriterionDTO, ...] = Field(min_length=1, max_length=50)
    inputs: tuple[ProjectRequiredInputDTO, ...] = Field(max_length=100)
    next_stage_readiness: ProjectStageReadiness
    allowed_actions: tuple[Literal["edit_basis", "manage_inputs", "transition_stage"], ...] = ()
    established_at: datetime
    updated_at: datetime


class ProjectInputMutationSuccess(StrictProjectFoundationSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    outcome: Literal["success"] = "success"
    project_id: int = Field(gt=0)
    foundation_version: int = Field(ge=1)
    item: ProjectRequiredInputDTO


class ProjectInputReorderSuccess(StrictProjectFoundationSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    outcome: Literal["success"] = "success"
    project_id: int = Field(gt=0)
    foundation_version: int = Field(ge=1)
    ordered_input_ids: tuple[UUID, ...] = Field(min_length=1, max_length=100)


class ProjectStageTransitionSuccess(StrictProjectFoundationSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    outcome: Literal["success"] = "success"
    project_id: int = Field(gt=0)
    previous_stage: ProjectEngineeringStage
    stage: ProjectEngineeringStage
    foundation_version: int = Field(ge=2)


class ProjectInputSourceCandidate(StrictProjectFoundationSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: ProjectInputSourceKind
    source_id: UUID
    version: int = Field(ge=1)
    workspace_id: int | None = Field(None, gt=0)
    display_label: str = Field(min_length=1, max_length=255)


class ProjectInputSourceCandidatePage(StrictProjectFoundationSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    outcome: Literal["success"] = "success"
    items: tuple[ProjectInputSourceCandidate, ...] = Field(max_length=50)
    visible_count: int = Field(ge=0, le=50)

    @model_validator(mode="after")
    def visible_only(self):
        if self.visible_count != len(self.items):
            raise ValueError("visible_count must match items")
        return self


class ProjectFoundationProtectedResult(StrictProjectFoundationSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    outcome: Literal["protected_not_found"] = "protected_not_found"


class ProjectFoundationInvalidResult(StrictProjectFoundationSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    outcome: Literal["invalid_request"] = "invalid_request"


class ProjectFoundationConflictResult(StrictProjectFoundationSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    outcome: Literal["version_conflict"] = "version_conflict"


class ProjectFoundationUnavailableResult(StrictProjectFoundationSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    outcome: Literal["unavailable"] = "unavailable"


ProtectedResults = ProjectFoundationProtectedResult | ProjectFoundationInvalidResult | ProjectFoundationConflictResult | ProjectFoundationUnavailableResult
ProjectFoundationReadResult = ProjectFoundationNotEstablished | ProjectFoundationEstablished | ProjectFoundationProtectedResult | ProjectFoundationUnavailableResult
ProjectFoundationPutResult = ProjectFoundationEstablished | ProjectFoundationProtectedResult | ProjectFoundationInvalidResult | ProjectFoundationConflictResult | ProjectFoundationUnavailableResult
ProjectInputMutationResult = ProjectInputMutationSuccess | ProjectFoundationProtectedResult | ProjectFoundationInvalidResult | ProjectFoundationConflictResult | ProjectFoundationUnavailableResult
ProjectInputReorderResult = ProjectInputReorderSuccess | ProjectFoundationProtectedResult | ProjectFoundationInvalidResult | ProjectFoundationConflictResult | ProjectFoundationUnavailableResult
ProjectStageTransitionResult = ProjectStageTransitionSuccess | ProjectFoundationProtectedResult | ProjectFoundationInvalidResult | ProjectFoundationConflictResult | ProjectFoundationUnavailableResult
ProjectInputSourceCandidateResult = ProjectInputSourceCandidatePage | ProjectFoundationProtectedResult | ProjectFoundationInvalidResult | ProjectFoundationUnavailableResult
