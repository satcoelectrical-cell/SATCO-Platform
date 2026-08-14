"""Strict transport and provider schemas for PATCH-035."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

from app.enums.ai_capture_assistant import AdviceConfidence, AdviceOutputKind, AdviceRefusalCode, ProviderAdviceStatus
from app.enums.engineering_experience_capture import EngineeringExperienceSourceKind


Text512 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=512)]
Text1000 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
Text10000 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10000)]


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class CaptureAdviceRequestSchema(StrictSchema):
    # JSON transports necessarily encode UUIDs and enums as strings; fields
    # remain closed and validated while unknown/coercive shapes stay forbidden.
    model_config = ConfigDict(extra="forbid", strict=False)

    capture_id: UUID
    project_id: int = Field(gt=0)
    workspace_id: int | None = Field(default=None, gt=0)
    human_instruction: Annotated[str, StringConstraints(min_length=1, max_length=2000)]
    output_kind: Literal[AdviceOutputKind.CAPTURE_REFINEMENT] = AdviceOutputKind.CAPTURE_REFINEMENT


class ProviderCaptureAdviceResponseSchema(StrictSchema):
    schema_version: Literal[1]
    status: ProviderAdviceStatus
    suggested_text: Text10000 | None = None
    observations: tuple[Text512, ...] = Field(max_length=10)
    assumptions: tuple[Text512, ...] = Field(max_length=10)
    missing_information: tuple[Text512, ...] = Field(max_length=10)
    confidence: AdviceConfidence
    confidence_rationale: Text1000
    limitations: tuple[Text512, ...] = Field(min_length=1, max_length=10)
    recommended_next_step: Text1000
    refusal_code: AdviceRefusalCode | None = None
    provider_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")]
    model_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")]
    model_version: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")]

    @field_validator("observations", "assumptions", "missing_information", "limitations")
    @classmethod
    def unique_ordered(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("items must be unique")
        return value

    @model_validator(mode="after")
    def status_shape(self):
        if self.status is ProviderAdviceStatus.SUCCESS:
            if self.suggested_text is None or self.refusal_code is not None:
                raise ValueError("success shape is invalid")
        elif self.suggested_text is not None or self.refusal_code is None:
            raise ValueError("refusal shape is invalid")
        return self


class CaptureAttributionSchema(StrictSchema):
    capture_id: UUID
    version: int = Field(gt=0)
    project_id: int = Field(gt=0)
    workspace_id: int | None = Field(default=None, gt=0)
    source_kind: EngineeringExperienceSourceKind
    updated_at: datetime


class ProviderAttributionSchema(StrictSchema):
    provider_id: str
    model_id: str
    model_version: str


class CaptureAdviceProposalSchema(StrictSchema):
    advisory: Literal[True]
    suggested_text: Text10000
    observations: tuple[Text512, ...]
    assumptions: tuple[Text512, ...]
    missing_information: tuple[Text512, ...]
    confidence: AdviceConfidence
    confidence_rationale: Text1000
    limitations: tuple[Text512, ...]
    recommended_next_step: Text1000
    capture_attribution: CaptureAttributionSchema
    provider_attribution: ProviderAttributionSchema
    generated_at: datetime


class CaptureAdviceSuccessSchema(StrictSchema):
    outcome: Literal["success"]
    proposal: CaptureAdviceProposalSchema


class CaptureAdviceRefusedSchema(StrictSchema):
    outcome: Literal["refused"]
    refusal_code: AdviceRefusalCode
    recommended_next_step: Text1000


class PayloadFreeOutcomeSchema(StrictSchema):
    outcome: Literal["protected_not_found", "invalid_request", "disabled", "unavailable"]


CaptureAdviceResponseSchema = CaptureAdviceSuccessSchema | CaptureAdviceRefusedSchema | PayloadFreeOutcomeSchema
