"""Pydantic v2 contracts for the Evidence application boundary."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.enums import EvidenceLifecycle, EvidenceSourceKind, EvidenceSourceStanding

class EvidenceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: int | None = Field(None, gt=0)
    workspace_id: int | None = Field(None, gt=0)
    source_kind: EvidenceSourceKind
    source_reference: str = Field(min_length=1, max_length=512)
    source_revision: str = Field(min_length=1, max_length=128)
    source_standing: EvidenceSourceStanding
    effective_at: datetime | None = None
    supported_fact: str = Field(min_length=1, max_length=2000)
    rationale: str = Field(min_length=1)
    @model_validator(mode="after")
    def coherent_scope(self):
        if self.workspace_id is not None and self.project_id is None:
            raise ValueError("workspace_id requires project_id")
        return self

class TransitionEvidenceLifecycleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: int = Field(gt=0)
    lifecycle: EvidenceLifecycle
    replacement_evidence_id: UUID | None = None
    rationale: str = Field(min_length=1)

class LinkEvidenceSupportingFilesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: int = Field(gt=0)
    asset_ids: tuple[UUID, ...] = Field(min_length=1, max_length=10)
    rationale: str = Field(min_length=1, max_length=2000)
    @model_validator(mode="after")
    def exact_ids(self):
        if len(set(self.asset_ids)) != len(self.asset_ids) or self.asset_ids != tuple(sorted(self.asset_ids, key=str)):
            raise ValueError("asset_ids must be unique and ordered")
        return self

class EvidenceFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workspace_id: int | None = Field(None, gt=0)
    lifecycle: EvidenceLifecycle | None = None
    source_kind: EvidenceSourceKind | None = None
    source_standing: EvidenceSourceStanding | None = None

class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    organization_id: UUID
    project_id: int | None
    workspace_id: int | None
    lifecycle: EvidenceLifecycle
    source_kind: EvidenceSourceKind
    source_reference: str
    source_revision: str
    source_standing: EvidenceSourceStanding
    effective_at: datetime | None
    supported_fact: str
    creator_id: int
    version: int
    created_at: datetime
    updated_at: datetime
    allowed_actions: tuple[str, ...] = ()

class EvidenceListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[EvidenceResponse]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    size: int = Field(ge=1)
