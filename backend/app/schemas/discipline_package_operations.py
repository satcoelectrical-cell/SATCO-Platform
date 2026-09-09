"""Closed DTOs for trusted discipline-package operations."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums.engineering_experience_capture import EngineeringExperienceSourceKind
from app.schemas.engineering_deliverable import CreateDeliverableRequest


class PackageCatalogEntryV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    package_key: str = Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")
    package_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    adapter_id: str = Field(pattern=r"^[a-z][a-z0-9_.-]*$")
    component_key: str = Field(pattern=r"^[a-z][a-z0-9_.-]*$")
    rule_ids: tuple[str, ...] = Field(min_length=5, max_length=5)


Rationale = Annotated[str, Field(min_length=1, max_length=2000)]


class PackageOperationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    declaration_id: str = Field(pattern=r"^(electrical|instrumentation|control_automation)\.[a-z_]+\.[a-z_]+$", max_length=128)
    rationale: Rationale

    @field_validator("rationale")
    @classmethod
    def normalize_rationale(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("rationale must not be empty")
        return value


class PackageObjectCreateRequest(PackageOperationRequest):
    primary_identifier_display_value: str = Field(min_length=1, max_length=128)
    primary_identifier_evidence_references: tuple[UUID, ...] = Field(default=(), max_length=8)
    steward_id: int | None = Field(default=None, ge=1)

    @field_validator("primary_identifier_evidence_references")
    @classmethod
    def ordered_evidence(cls, value: tuple[UUID, ...]) -> tuple[UUID, ...]:
        if value != tuple(sorted(set(value), key=str)):
            raise ValueError("Evidence references must be unique and UUID-lexical")
        return value


class PackageRelationshipCreateRequest(PackageOperationRequest):
    source_object_id: UUID
    target_object_id: UUID
    evidence_references: tuple[UUID, ...] = Field(default=(), max_length=8)
    steward_id: int | None = Field(default=None, ge=1)

    @field_validator("evidence_references")
    @classmethod
    def ordered_relationship_evidence(cls, value: tuple[UUID, ...]) -> tuple[UUID, ...]:
        if value != tuple(sorted(set(value), key=str)):
            raise ValueError("Evidence references must be unique and UUID-lexical")
        return value


class PackageCaptureCreateRequest(PackageOperationRequest):
    declaration_id: str = Field(
        pattern=r"^(electrical|instrumentation|control_automation)\.[a-z_]+\.input$", max_length=128,
    )
    engineering_object_id: UUID | None = None
    source_kind: EngineeringExperienceSourceKind
    original_content: str = Field(min_length=1, max_length=10_000)
    source_reference: str | None = Field(default=None, min_length=1, max_length=512)


class PackageDeliverableCreateRequest(CreateDeliverableRequest):
    declaration_id: str = Field(
        pattern=r"^(electrical|instrumentation|control_automation)\.deliverable\.[a-z_]+$", max_length=128,
    )


class PackageRuleEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hook_id: str = Field(pattern=r"^(electrical|instrumentation|control_automation)\.[a-z_]+$", max_length=128)
    hook_version: Literal["1.0.0"] = "1.0.0"
    envelope: dict[str, object]


class PackageRuleEvaluationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["PASS", "FINDINGS", "INDETERMINATE", "UNAVAILABLE"]
    finding_codes: tuple[str, ...]
    limitations: tuple[str, ...]
    result_digest: str = Field(pattern=r"^[0-9a-f]{64}$")


InputDeclarationId = Annotated[
    str, Field(pattern=r"^(electrical|instrumentation|control_automation)\.[a-z_]+\.input$", max_length=128)
]


class PackageContextBindingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    input_declaration_id: InputDeclarationId
    context_id: int = Field(gt=0)
    context_subject_reference_id: int = Field(gt=0)
    expected_context_version: int = Field(gt=0)
    expected_configuration_revision: int = Field(gt=0)
    rationale: Rationale


class PackageEvidenceBindingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    input_declaration_id: InputDeclarationId
    evidence_id: UUID
    expected_evidence_version: int = Field(gt=0)
    expected_configuration_revision: int = Field(gt=0)
    rationale: Rationale


class PackageContextBindingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    context_id: int
    context_version: int
    context_subject_reference_id: int
    project_id: int
    workspace_id: int | None
    package_key: str
    package_version: str
    descriptor_digest: str
    project_configuration_revision: int
    input_declaration_id: str
    context_declaration_id: str
    bound_at: datetime


class PackageEvidenceBindingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    evidence_id: UUID
    evidence_version: int
    project_id: int
    workspace_id: int | None
    package_key: str
    package_version: str
    descriptor_digest: str
    project_configuration_revision: int
    input_declaration_id: str
    evidence_requirement_id: str
    bound_at: datetime


class PackageContextResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    input_declaration_id: str
    context_declaration_id: str
    context_kind_id: str
    subject_kind: Literal["workspace", "engineering_object"]
    subject_id: str
    required: bool
    context_id: int | None
    context_version: int | None
    status: Literal["SATISFIED", "MISSING", "STALE", "INDETERMINATE"]
    reason_code: str | None


class PackageEvidenceResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    input_declaration_id: str
    evidence_requirement_id: str
    evidence_kind_id: str
    minimum_count: int
    evidence_id: UUID | None
    evidence_version: int | None
    status: Literal["SATISFIED", "MISSING", "STALE", "INDETERMINATE"]
    reason_code: str | None


class PackageContextEvaluationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    project_id: int
    workspace_id: int
    package_key: str
    package_version: str
    descriptor_digest: str
    project_configuration_revision: int
    status: Literal["PASS", "FINDINGS", "INDETERMINATE"]
    object_ids: tuple[UUID, ...] = Field(max_length=64)
    required_input_ids: tuple[str, ...]
    context_results: tuple[PackageContextResult, ...]
    findings: tuple[str, ...]
    limitations: tuple[str, ...]
    observation_started_at: datetime
    observation_completed_at: datetime
    source_version_digest: str = Field(pattern=r"^[0-9a-f]{64}$")


class PackageReadinessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    project_id: int
    workspace_id: int
    deliverable_id: UUID
    revision_id: UUID
    deliverable_version: int
    revision_version: int
    package_key: str
    package_version: str
    descriptor_digest: str
    project_configuration_revision: int
    status: Literal["PASS", "FINDINGS", "INDETERMINATE"]
    required_input_ids: tuple[str, ...]
    context_results: tuple[PackageContextResult, ...]
    evidence_results: tuple[PackageEvidenceResult, ...]
    transition_allowed: bool
    findings: tuple[str, ...]
    limitations: tuple[str, ...]
    observation_started_at: datetime
    observation_completed_at: datetime
    rule_hook_id: str
    rule_hook_version: Literal["1.0.0"] = "1.0.0"
    source_version_digest: str = Field(pattern=r"^[0-9a-f]{64}$")


class PackageTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_standing: Literal["ready_for_review", "issued"]
    expected_deliverable_version: int = Field(gt=0)
    expected_revision_version: int = Field(gt=0)
    expected_configuration_revision: int = Field(gt=0)
    object_ids: tuple[UUID, ...] = Field(default=(), max_length=64)
    evidence_ids: tuple[UUID, ...] = Field(default=(), max_length=24)
    rationale: Rationale

    @field_validator("object_ids", "evidence_ids")
    @classmethod
    def ordered_ids(cls, value):
        if value != tuple(sorted(set(value), key=str)):
            raise ValueError("identifiers must be unique and UUID-lexical")
        return value

    @field_validator("evidence_ids")
    @classmethod
    def issue_bound(cls, value, info):
        if info.data.get("target_standing") == "issued" and len(value) > 8:
            raise ValueError("issue accepts at most eight Evidence items")
        return value
