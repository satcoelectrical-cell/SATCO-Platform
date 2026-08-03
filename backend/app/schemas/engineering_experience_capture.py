"""Strict Pydantic contracts for Engineering Experience Capture."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.enums.engineering_experience_capture import (
    EngineeringExperienceCaptureLifecycle,
    EngineeringExperienceSourceKind,
)


class EngineeringExperienceCaptureCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: int = Field(gt=0)
    workspace_id: int | None = Field(None, gt=0)
    engineering_object_id: UUID | None = None
    source_kind: EngineeringExperienceSourceKind
    original_content: str = Field(min_length=1, max_length=10_000)
    source_reference: str | None = Field(None, min_length=1, max_length=512)

    @model_validator(mode="after")
    def object_requires_workspace(self):
        if self.engineering_object_id is not None and self.workspace_id is None:
            raise ValueError("engineering_object_id requires workspace_id")
        return self


class WithdrawEngineeringExperienceCaptureRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(gt=0)
    rationale: str = Field(min_length=1, max_length=1_000)


class SupersedeEngineeringExperienceCaptureRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(gt=0)
    replacement_capture_id: UUID
    rationale: str = Field(min_length=1, max_length=1_000)


class EngineeringExperienceCaptureFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lifecycle: EngineeringExperienceCaptureLifecycle | None = None
    source_kind: EngineeringExperienceSourceKind | None = None
    creator_id: int | None = Field(None, gt=0)
    engineering_object_id: UUID | None = None


class EngineeringExperienceCaptureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    organization_id: UUID
    project_id: int
    workspace_id: int | None
    discipline: str | None
    engineering_object_id: UUID | None
    source_kind: EngineeringExperienceSourceKind
    original_content: str
    source_reference: str | None
    creator_id: int
    lifecycle: EngineeringExperienceCaptureLifecycle
    superseded_by_capture_id: UUID | None
    version: int
    created_at: datetime
    updated_at: datetime
    allowed_actions: tuple[str, ...] = ()


class EngineeringExperienceCaptureListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[EngineeringExperienceCaptureResponse]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    size: int = Field(ge=1, le=100)


class EngineeringExperienceCaptureSupersessionChainResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[EngineeringExperienceCaptureResponse] = Field(max_length=20)
