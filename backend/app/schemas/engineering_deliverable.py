from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums.engineering_deliverable import DeliverableRevisionStanding, DeliverableStanding, ExternalAuthoringAuthority


class DeliverableSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _text(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not value: raise ValueError("value must not be empty")
    return value


class DeliverableActor(DeliverableSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    actor_id: int = Field(gt=0)
    organization_id: UUID


class DeliverableFields(DeliverableSchema):
    code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    discipline: str = Field(min_length=1, max_length=80)
    deliverable_type: str = Field(min_length=1, max_length=80)
    purpose: str | None = Field(None, max_length=2000)
    external_authority: ExternalAuthoringAuthority
    workspace_id: int | None = Field(None, gt=0)
    activity_id: UUID | None = None
    milestone_id: UUID | None = None
    responsible_user_id: int | None = Field(None, gt=0)
    target_date: date | None = None
    @field_validator("code", "title", "discipline", "deliverable_type")
    @classmethod
    def required(cls, value): return _text(value)
    @field_validator("purpose")
    @classmethod
    def optional(cls, value): return None if value is None else _text(value)


class CreateDeliverableRequest(DeliverableFields):
    rationale: str = Field(min_length=1, max_length=2000)
    initial_external_label: str = Field(min_length=1, max_length=80)
    source_reference: str | None = Field(None, max_length=512)
    supporting_file_id: UUID | None = None
    @field_validator("rationale", "initial_external_label")
    @classmethod
    def rationale_text(cls, value): return _text(value)
    @field_validator("source_reference")
    @classmethod
    def source_text(cls, value): return None if value is None else _text(value)


class UpdateDeliverableRequest(DeliverableFields):
    expected_version: int = Field(ge=1)
    rationale: str = Field(min_length=1, max_length=2000)
    @field_validator("rationale")
    @classmethod
    def rationale_text(cls, value): return _text(value)


class CreateRevisionRequest(DeliverableSchema):
    expected_deliverable_version: int = Field(ge=1)
    expected_current_revision_version: int = Field(ge=1)
    external_label: str = Field(min_length=1, max_length=80)
    source_reference: str | None = Field(None, max_length=512)
    supporting_file_id: UUID | None = None
    rationale: str = Field(min_length=1, max_length=2000)
    @field_validator("external_label", "rationale")
    @classmethod
    def required(cls, value): return _text(value)
    @field_validator("source_reference")
    @classmethod
    def optional(cls, value): return None if value is None else _text(value)


class TransitionRevisionRequest(DeliverableSchema):
    expected_deliverable_version: int = Field(ge=1)
    expected_revision_version: int = Field(ge=1)
    target_standing: DeliverableRevisionStanding
    rationale: str = Field(min_length=1, max_length=2000)
    @field_validator("rationale")
    @classmethod
    def required(cls, value): return _text(value)


class DeliverableRevisionDTO(DeliverableSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: UUID; sequence: int = Field(ge=1); external_label: str; source_reference: str | None
    representation_available: bool; standing: DeliverableRevisionStanding; version: int = Field(ge=1)
    created_at: datetime; transitioned_at: datetime


class DeliverableDTO(DeliverableSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: UUID; project_id: int; workspace_id: int | None; code: str; title: str; discipline: str; deliverable_type: str
    purpose: str | None; external_authority: ExternalAuthoringAuthority; responsible_user_id: int | None; target_date: date | None
    standing: DeliverableStanding; version: int; activity_id: UUID | None; milestone_id: UUID | None; current_revision: DeliverableRevisionDTO


class DeliverableListResponse(DeliverableSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    outcome: Literal["success"] = "success"; items: tuple[DeliverableDTO, ...] = Field(max_length=100); visible_count: int = Field(ge=0, le=100); continuation: str | None = None


class DeliverableMutationSuccess(DeliverableSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)
    outcome: Literal["success"] = "success"; deliverable_id: UUID; deliverable_version: int = Field(ge=1); revision_id: UUID | None = None; revision_version: int | None = Field(None, ge=1); standing: DeliverableStanding | None = None; revision_standing: DeliverableRevisionStanding | None = None


class DeliverableProtectedResult(DeliverableSchema):
    model_config = ConfigDict(extra="forbid", frozen=True); outcome: Literal["protected_not_found"] = "protected_not_found"
class DeliverableInvalidResult(DeliverableSchema):
    model_config = ConfigDict(extra="forbid", frozen=True); outcome: Literal["invalid_request"] = "invalid_request"
class DeliverableVersionConflictResult(DeliverableSchema):
    model_config = ConfigDict(extra="forbid", frozen=True); outcome: Literal["version_conflict"] = "version_conflict"
class DeliverableIdempotencyConflictResult(DeliverableSchema):
    model_config = ConfigDict(extra="forbid", frozen=True); outcome: Literal["idempotency_conflict"] = "idempotency_conflict"
class DeliverableUnavailableResult(DeliverableSchema):
    model_config = ConfigDict(extra="forbid", frozen=True); outcome: Literal["unavailable"] = "unavailable"
