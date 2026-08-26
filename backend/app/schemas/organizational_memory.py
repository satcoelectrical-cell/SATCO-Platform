"""Strict Pydantic v2 Organizational Memory contracts for PATCH-034."""

from datetime import datetime, timezone
from typing import Annotated, Literal
import unicodedata
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StrictBool, StrictInt, field_validator, model_validator

from app.enums.organizational_memory import MemoryStanding
from app.enums.technical_report import (
    TechnicalReportOwningCapability,
    TechnicalReportPurpose,
    TechnicalReportSourceClass,
    TechnicalReportSourceType,
)
from app.models.organizational_memory_command import PROJECTION_CONTRACT


PositiveId = Annotated[StrictInt, Field(gt=0)]
PositiveVersion = Annotated[StrictInt, Field(gt=0)]
ReasonText = Annotated[str, Field(min_length=1, max_length=2000)]
Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
CanonicalSourceText = Annotated[str, Field(min_length=1, max_length=10000)]


class StrictMemorySchema(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, from_attributes=True)

    @model_validator(mode="after")
    def require_utc(self):
        for name in type(self).model_fields:
            value = getattr(self, name)
            if isinstance(value, datetime) and value.utcoffset() != timezone.utc.utcoffset(value):
                raise ValueError(f"{name} must be UTC")
        return self


class MemoryActorSchema(StrictMemorySchema):
    actor_id: PositiveId
    organization_id: UUID


class MemoryScopeSchema(StrictMemorySchema):
    organization_id: UUID
    workspace_id: PositiveId
    project_id: PositiveId | None


class OrganizationalMemoryGraphSourceLink(StrictMemorySchema):
    memory_id: UUID
    report_id: UUID
    accepted_report_version: PositiveVersion
    memory_version: PositiveVersion
    project_id: PositiveId | None
    workspace_id: PositiveId
    observed_at: AwareDatetime


class OrganizationalMemoryGraphSourcePage(StrictMemorySchema):
    items: tuple[OrganizationalMemoryGraphSourceLink, ...] = Field(max_length=91)
    has_more: StrictBool = False


class AcceptedReportSourceSchema(StrictMemorySchema):
    report_id: UUID
    accepted_aggregate_version: PositiveVersion
    accepted_snapshot_digest: Digest


class MemoryCommandMetadataSchema(StrictMemorySchema):
    actor: MemoryActorSchema
    correlation_id: UUID
    command_id: UUID
    idempotency_id: UUID
    rationale: ReasonText


class AdmittedTechnicalContentV1Schema(StrictMemorySchema):
    engineering_scope: CanonicalSourceText
    technical_content: CanonicalSourceText
    assumptions: tuple[CanonicalSourceText, ...]
    uncertainty: CanonicalSourceText
    limitations: tuple[CanonicalSourceText, ...]
    conclusions: CanonicalSourceText
    recommendations: tuple[CanonicalSourceText, ...]

    @field_validator("engineering_scope", "technical_content", "uncertainty", "conclusions")
    @classmethod
    def exact_source_text(cls, value: str) -> str:
        if value.strip() != value or unicodedata.normalize("NFC", value) != value: raise ValueError("source text must already be canonically normalized")
        return value

    @field_validator("assumptions", "limitations", "recommendations")
    @classmethod
    def exact_source_items(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(item.strip() != item or unicodedata.normalize("NFC", item) != item for item in value): raise ValueError("source list text must already be canonically normalized")
        return value


class AdmittedQualificationV1Schema(StrictMemorySchema):
    is_preliminary: StrictBool
    evidence_deficiencies: tuple[CanonicalSourceText, ...]
    unresolved_issues: tuple[CanonicalSourceText, ...]
    follow_up_requirements: tuple[CanonicalSourceText, ...]

    @model_validator(mode="after")
    def coherent_qualification(self):
        values = (self.evidence_deficiencies, self.unresolved_issues, self.follow_up_requirements)
        if self.is_preliminary != any(values): raise ValueError("qualification is incoherent")
        if any(item.strip() != item for group in values for item in group): raise ValueError("qualification text must already be normalized")
        return self


class AdmittedReportProjectionV1Schema(StrictMemorySchema):
    projection_contract: Literal["organizational_memory.accepted_report.v1"] = PROJECTION_CONTRACT
    report_id: UUID
    purpose: TechnicalReportPurpose
    organization_id: UUID
    workspace_id: PositiveId
    project_id: PositiveId | None
    content: AdmittedTechnicalContentV1Schema
    qualification: AdmittedQualificationV1Schema
    accepted_draft_revision_id: UUID
    accepted_draft_revision_number: PositiveVersion
    accepted_aggregate_version: PositiveVersion
    accepted_by_id: PositiveId
    accepted_at: AwareDatetime
    predecessor_report_id: UUID | None


class AdmitAcceptedReportSchema(StrictMemorySchema):
    metadata: MemoryCommandMetadataSchema
    source: AcceptedReportSourceSchema
    scope: MemoryScopeSchema
    audience_actor_ids: tuple[PositiveId, ...] = Field(max_length=100)
    reuse_restrictions: tuple[Annotated[str, Field(min_length=1, max_length=2000)], ...] = Field(max_length=32)
    admission_rationale: ReasonText

    @model_validator(mode="after")
    def validate_scope_and_audience(self):
        if self.metadata.actor.organization_id != self.scope.organization_id:
            raise ValueError("trusted Organization scope mismatch")
        if tuple(sorted(set(self.audience_actor_ids))) != self.audience_actor_ids:
            raise ValueError("audience must be unique and sorted")
        return self


class CreateMemorySuccessorSchema(AdmitAcceptedReportSchema):
    predecessor_memory_id: UUID


class WithdrawMemorySchema(StrictMemorySchema):
    metadata: MemoryCommandMetadataSchema
    memory_id: UUID
    expected_version: PositiveVersion
    reason: ReasonText


class SupersedeMemorySchema(StrictMemorySchema):
    metadata: MemoryCommandMetadataSchema
    predecessor_memory_id: UUID
    replacement_memory_id: UUID
    expected_predecessor_version: PositiveVersion
    expected_replacement_version: PositiveVersion
    reason: ReasonText

    @model_validator(mode="after")
    def distinct_identities(self):
        if self.predecessor_memory_id == self.replacement_memory_id:
            raise ValueError("supersession identities must differ")
        return self


class GetActiveMemorySchema(StrictMemorySchema):
    memory_id: UUID
    include_provenance: StrictBool = False
    reuse_intent: StrictBool = False


class InspectMemoryHistorySchema(StrictMemorySchema):
    memory_id: UUID
    include_predecessor: StrictBool = False
    include_replacement: StrictBool = False
    include_provenance: StrictBool = False


class ListActiveMemorySchema(StrictMemorySchema):
    scope: MemoryScopeSchema
    page_size: Annotated[StrictInt, Field(ge=1, le=100)] = 50
    continuation: Annotated[str, Field(min_length=1, max_length=4096)] | None = None


class SafeAuthorizedProvenanceSchema(StrictMemorySchema):
    entry_id: UUID
    ordinal: Annotated[StrictInt, Field(ge=0)]
    source_class: Literal[TechnicalReportSourceClass.CANONICAL_MATERIAL]
    source_type: Literal[TechnicalReportSourceType.UNIVERSAL_CAPTURE, TechnicalReportSourceType.EVIDENCE, TechnicalReportSourceType.ENGINEERING_OBJECT, TechnicalReportSourceType.ENGINEERING_RELATIONSHIP]
    owning_capability: TechnicalReportOwningCapability
    is_material: Literal[True]
    reliance_role: Annotated[str, Field(min_length=1, max_length=2000)]
    locator_digest: Digest
    source_integrity_algorithm: Literal["sha256"]
    source_integrity_digest: Digest

    @model_validator(mode="after")
    def require_exact_source_owner_pair(self):
        expected = {
            TechnicalReportSourceType.UNIVERSAL_CAPTURE: TechnicalReportOwningCapability.UNIVERSAL_CAPTURE,
            TechnicalReportSourceType.EVIDENCE: TechnicalReportOwningCapability.EVIDENCE,
            TechnicalReportSourceType.ENGINEERING_OBJECT: TechnicalReportOwningCapability.ENGINEERING_OBJECT,
            TechnicalReportSourceType.ENGINEERING_RELATIONSHIP: TechnicalReportOwningCapability.ENGINEERING_RELATIONSHIP,
        }
        if expected[self.source_type] is not self.owning_capability:
            raise ValueError("provenance source and canonical owner are incoherent")
        if self.reliance_role.strip() != self.reliance_role:
            raise ValueError("reliance role must already be normalized")
        return self


class ActiveMemorySummarySchema(StrictMemorySchema):
    memory_id: UUID
    version: PositiveVersion
    standing: Literal[MemoryStanding.ACTIVE]
    source_report_id: UUID
    source_accepted_version: PositiveVersion
    purpose: TechnicalReportPurpose
    organization_id: UUID
    workspace_id: PositiveId
    project_id: PositiveId | None
    admitted_by_id: PositiveId
    admitted_at: AwareDatetime
    updated_at: AwareDatetime


class ActiveMemoryDetailSchema(StrictMemorySchema):
    summary: ActiveMemorySummarySchema
    projection: AdmittedReportProjectionV1Schema
    admission_rationale: ReasonText
    reuse_restrictions: tuple[Annotated[str, Field(min_length=1, max_length=2000)], ...] = Field(max_length=32)
    safe_provenance: tuple[SafeAuthorizedProvenanceSchema, ...]


class AuthorizedMemoryLinkSchema(StrictMemorySchema):
    memory_id: UUID


class _HistoryBase(StrictMemorySchema):
    memory_id: UUID
    version: PositiveVersion
    source: AcceptedReportSourceSchema
    projection: AdmittedReportProjectionV1Schema
    admitted_by_id: PositiveId
    admitted_at: AwareDatetime
    predecessor: AuthorizedMemoryLinkSchema | None
    safe_provenance: tuple[SafeAuthorizedProvenanceSchema, ...]


class ActiveMemoryHistorySchema(_HistoryBase):
    standing: Literal[MemoryStanding.ACTIVE]


class WithdrawnMemoryHistorySchema(_HistoryBase):
    standing: Literal[MemoryStanding.WITHDRAWN]
    withdrawn_by_id: PositiveId
    withdrawn_at: AwareDatetime
    withdrawal_reason: ReasonText


class SupersededMemoryHistorySchema(_HistoryBase):
    standing: Literal[MemoryStanding.SUPERSEDED]
    superseded_by_id: PositiveId
    superseded_at: AwareDatetime
    supersession_reason: ReasonText
    replacement: AuthorizedMemoryLinkSchema | None


HistoricalMemoryDetailSchema = Annotated[ActiveMemoryHistorySchema | WithdrawnMemoryHistorySchema | SupersededMemoryHistorySchema, Field(discriminator="standing")]


class ActiveMemoryPageSchema(StrictMemorySchema):
    items: tuple[ActiveMemorySummarySchema, ...] = Field(max_length=100)
    visible_total: Annotated[StrictInt, Field(ge=0, le=100)]
    next_continuation: str | None

    @model_validator(mode="after")
    def total_is_visible_only(self):
        if self.visible_total != len(self.items): raise ValueError("visible_total must equal returned item count")
        return self


class AdmissionSuccessSchema(StrictMemorySchema):
    outcome: Literal["success"]
    memory_id: UUID
    version: Literal[1]
    standing: Literal[MemoryStanding.ACTIVE]
    source: AcceptedReportSourceSchema


class WithdrawalSuccessSchema(StrictMemorySchema):
    outcome: Literal["success"]
    memory_id: UUID
    version: PositiveVersion
    standing: Literal[MemoryStanding.WITHDRAWN]
    withdrawn_at: AwareDatetime


class CreateSuccessorSuccessSchema(AdmissionSuccessSchema):
    predecessor_memory_id: UUID


class SupersessionSuccessSchema(StrictMemorySchema):
    outcome: Literal["success"]
    predecessor_memory_id: UUID
    predecessor_version: PositiveVersion
    predecessor_standing: Literal[MemoryStanding.SUPERSEDED]
    replacement_memory_id: UUID
    replacement_version: PositiveVersion
    replacement_standing: Literal[MemoryStanding.ACTIVE]
    superseded_at: AwareDatetime


class GetActiveSuccessSchema(StrictMemorySchema): outcome: Literal["success"]; item: ActiveMemoryDetailSchema
class ListActiveSuccessSchema(StrictMemorySchema): outcome: Literal["success"]; page: ActiveMemoryPageSchema
class InspectHistorySuccessSchema(StrictMemorySchema): outcome: Literal["success"]; item: HistoricalMemoryDetailSchema


class MemoryProtectedNotFoundSchema(StrictMemorySchema): outcome: Literal["protected_not_found"] = "protected_not_found"
class MemoryInvalidRequestSchema(StrictMemorySchema): outcome: Literal["invalid_request"] = "invalid_request"
class MemoryVersionConflictSchema(StrictMemorySchema): outcome: Literal["version_conflict"] = "version_conflict"
class MemoryIdempotencyConflictSchema(StrictMemorySchema): outcome: Literal["idempotency_conflict"] = "idempotency_conflict"
class MemoryInvalidStandingSchema(StrictMemorySchema): outcome: Literal["invalid_standing"] = "invalid_standing"
class MemoryDuplicateSourceSchema(StrictMemorySchema): outcome: Literal["duplicate_source"] = "duplicate_source"
class MemoryUnavailableSchema(StrictMemorySchema): outcome: Literal["unavailable"] = "unavailable"


AdmitResultSchema = Annotated[AdmissionSuccessSchema | MemoryProtectedNotFoundSchema | MemoryInvalidRequestSchema | MemoryIdempotencyConflictSchema | MemoryDuplicateSourceSchema | MemoryUnavailableSchema, Field(discriminator="outcome")]
WithdrawResultSchema = Annotated[WithdrawalSuccessSchema | MemoryProtectedNotFoundSchema | MemoryInvalidRequestSchema | MemoryVersionConflictSchema | MemoryIdempotencyConflictSchema | MemoryInvalidStandingSchema | MemoryUnavailableSchema, Field(discriminator="outcome")]
CreateSuccessorResultSchema = Annotated[CreateSuccessorSuccessSchema | MemoryProtectedNotFoundSchema | MemoryInvalidRequestSchema | MemoryIdempotencyConflictSchema | MemoryDuplicateSourceSchema | MemoryUnavailableSchema, Field(discriminator="outcome")]
SupersedeResultSchema = Annotated[SupersessionSuccessSchema | MemoryProtectedNotFoundSchema | MemoryInvalidRequestSchema | MemoryVersionConflictSchema | MemoryIdempotencyConflictSchema | MemoryInvalidStandingSchema | MemoryUnavailableSchema, Field(discriminator="outcome")]
GetActiveResultSchema = Annotated[GetActiveSuccessSchema | MemoryProtectedNotFoundSchema | MemoryInvalidRequestSchema | MemoryUnavailableSchema, Field(discriminator="outcome")]
ListActiveResultSchema = Annotated[ListActiveSuccessSchema | MemoryProtectedNotFoundSchema | MemoryInvalidRequestSchema | MemoryUnavailableSchema, Field(discriminator="outcome")]
InspectHistoryResultSchema = Annotated[InspectHistorySuccessSchema | MemoryProtectedNotFoundSchema | MemoryInvalidRequestSchema | MemoryUnavailableSchema, Field(discriminator="outcome")]
