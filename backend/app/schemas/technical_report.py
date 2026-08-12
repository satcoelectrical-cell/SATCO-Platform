"""Strict Pydantic v2 Technical Report contracts for PATCH-032."""

from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StrictBool, field_validator, model_validator

from app.enums.engineering_experience_capture import EngineeringExperienceCaptureLifecycle, EngineeringExperienceSourceKind
from app.enums.engineering_knowledge import EngineeringAuthorityStanding, EngineeringDiscipline, EngineeringLifecycle, EngineeringObjectFamily, EngineeringObjectType
from app.enums.engineering_relationship import RelationshipFamily, RelationshipLifecycle, RelationshipType
from app.enums.evidence import EvidenceLifecycle, EvidenceSourceKind, EvidenceSourceStanding

from app.enums.technical_report import (
    TechnicalReportAvailabilityStatus,
    TechnicalReportIntegrityAlgorithm,
    TechnicalReportLifecycle,
    TechnicalReportOwningCapability,
    TechnicalReportPurpose,
    TechnicalReportSourceClass,
    TechnicalReportSourceType,
    TechnicalReportVerificationStatus,
)
from app.models.technical_report_command import (
    CaptureHistoricalBasisV1,
    EngineeringObjectHistoricalBasisV1,
    EngineeringRelationshipHistoricalBasisV1,
    EvidenceHistoricalBasisV1,
    ContextualLocator,
    ExternalHumanLocator,
    StandardLocator,
    TechnicalReportProvenanceEntry,
)


PositiveIdentifier = Annotated[int, Field(gt=0)]
PositiveVersion = Annotated[int, Field(gt=0)]
BoundedText = Annotated[str, Field(min_length=1, max_length=10000)]
Rationale = Annotated[str, Field(min_length=1, max_length=2000)]


class StrictTechnicalReportSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def require_utc_datetimes(self):
        for name in type(self).model_fields:
            value = getattr(self, name)
            if isinstance(value, datetime) and value.utcoffset() != timezone.utc.utcoffset(value):
                raise ValueError(f"{name} must be UTC")
        return self


class TechnicalReportContentSchema(StrictTechnicalReportSchema):
    engineering_scope: BoundedText
    technical_content: BoundedText
    assumptions: list[BoundedText] = Field(default_factory=list)
    uncertainty: BoundedText
    limitations: list[BoundedText] = Field(default_factory=list)
    conclusions: BoundedText
    recommendations: list[BoundedText] = Field(default_factory=list)

    @field_validator("engineering_scope", "technical_content", "uncertainty", "conclusions")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        value = value.strip()
        if not value or "\x00" in value:
            raise ValueError("invalid Technical Report content")
        return value

    @field_validator("assumptions", "limitations", "recommendations")
    @classmethod
    def normalize_collection(cls, value: list[str]) -> list[str]:
        normalized = [item.strip() for item in value]
        if any(not item or "\x00" in item for item in normalized):
            raise ValueError("content collection contains an invalid item")
        return normalized


class PreliminaryQualificationSchema(StrictTechnicalReportSchema):
    is_preliminary: StrictBool = False
    evidence_deficiencies: list[BoundedText] = Field(default_factory=list)
    unresolved_issues: list[BoundedText] = Field(default_factory=list)
    follow_up_requirements: list[BoundedText] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_qualification(self):
        values = (self.evidence_deficiencies, self.unresolved_issues, self.follow_up_requirements)
        if self.is_preliminary and not any(values):
            raise ValueError("preliminary qualification requires disclosed basis")
        if not self.is_preliminary and any(values):
            raise ValueError("non-preliminary report cannot carry preliminary deficiencies")
        return self


class CaptureHistoricalBasisSchema(StrictTechnicalReportSchema):
    basis_schema_version: Literal[1]
    source_category: Literal["universal_capture"]
    capture_id: UUID
    source_version: PositiveVersion
    organization_id: UUID
    project_id: PositiveIdentifier
    workspace_id: PositiveIdentifier | None
    discipline: EngineeringDiscipline | None
    engineering_object_id: UUID | None
    source_kind: EngineeringExperienceSourceKind
    original_content: Annotated[str, Field(min_length=1, max_length=10000)]
    source_reference: Annotated[str, Field(min_length=1, max_length=512)] | None
    creator_id: PositiveIdentifier
    lifecycle: EngineeringExperienceCaptureLifecycle
    created_at: AwareDatetime

    def to_domain(self) -> CaptureHistoricalBasisV1:
        return CaptureHistoricalBasisV1(**self.model_dump())


class EvidenceHistoricalBasisSchema(StrictTechnicalReportSchema):
    basis_schema_version: Literal[1]
    source_category: Literal["evidence"]
    evidence_id: UUID
    source_version: PositiveVersion
    organization_id: UUID
    project_id: PositiveIdentifier | None
    workspace_id: PositiveIdentifier | None
    lifecycle: EvidenceLifecycle
    source_kind: EvidenceSourceKind
    source_reference: Annotated[str, Field(min_length=1, max_length=512)]
    source_revision: Annotated[str, Field(min_length=1, max_length=128)]
    source_standing: EvidenceSourceStanding
    effective_at: AwareDatetime | None
    supported_fact: Annotated[str, Field(min_length=1, max_length=2000)]
    creator_id: PositiveIdentifier

    def to_domain(self) -> EvidenceHistoricalBasisV1:
        return EvidenceHistoricalBasisV1(**self.model_dump())


class EngineeringObjectHistoricalBasisSchema(StrictTechnicalReportSchema):
    basis_schema_version: Literal[1]
    source_category: Literal["engineering_object"]
    engineering_object_id: UUID
    source_version: PositiveVersion
    organization_id: UUID
    customer_id: PositiveIdentifier | None
    project_id: PositiveIdentifier
    workspace_id: PositiveIdentifier
    family: EngineeringObjectFamily
    discipline: EngineeringDiscipline
    object_type: EngineeringObjectType
    subtype: None
    lifecycle: EngineeringLifecycle
    authority_standing: EngineeringAuthorityStanding
    creator_id: PositiveIdentifier
    steward_id: PositiveIdentifier

    def to_domain(self) -> EngineeringObjectHistoricalBasisV1:
        return EngineeringObjectHistoricalBasisV1(**self.model_dump())


class EngineeringRelationshipHistoricalBasisSchema(StrictTechnicalReportSchema):
    basis_schema_version: Literal[1]
    source_category: Literal["engineering_relationship"]
    engineering_relationship_id: UUID
    source_version: PositiveVersion
    organization_id: UUID
    project_id: PositiveIdentifier
    workspace_id: PositiveIdentifier
    source_object_id: UUID
    target_object_id: UUID
    relationship_family: RelationshipFamily
    relationship_type: RelationshipType
    lifecycle: RelationshipLifecycle
    authority_standing: EngineeringAuthorityStanding
    evidence_references: list[UUID]
    creator_id: PositiveIdentifier
    steward_id: PositiveIdentifier
    reviewer_id: PositiveIdentifier | None
    approver_id: PositiveIdentifier | None

    @model_validator(mode="after")
    def validate_relationship(self):
        if self.source_object_id == self.target_object_id:
            raise ValueError("relationship endpoints must be distinct")
        if len(self.evidence_references) != len(set(self.evidence_references)):
            raise ValueError("evidence references must be unique")
        return self

    def to_domain(self) -> EngineeringRelationshipHistoricalBasisV1:
        values = self.model_dump()
        values["evidence_references"] = tuple(values["evidence_references"])
        return EngineeringRelationshipHistoricalBasisV1(**values)


HistoricalBasisSchema = Annotated[
    CaptureHistoricalBasisSchema | EvidenceHistoricalBasisSchema | EngineeringObjectHistoricalBasisSchema | EngineeringRelationshipHistoricalBasisSchema,
    Field(discriminator="source_category"),
]


class ExternalHumanLocatorSchema(StrictTechnicalReportSchema):
    locator_type: Literal["external_or_human"] = "external_or_human"
    report_local_source_id: UUID
    external_reference: Annotated[str, Field(min_length=1, max_length=512)]
    submitted_by_id: PositiveIdentifier | None = None
    observed_at: AwareDatetime | None = None
    retrieved_at: AwareDatetime | None = None
    submitted_at: AwareDatetime | None = None
    minimal_representation: BoundedText
    @model_validator(mode="after")
    def require_source_time(self):
        if not any((self.observed_at, self.retrieved_at, self.submitted_at)):
            raise ValueError("external/Human source requires an applicable source time")
        return self
    def to_domain(self) -> ExternalHumanLocator:
        return ExternalHumanLocator(**self.model_dump(exclude={"locator_type"}))


class StandardLocatorSchema(StrictTechnicalReportSchema):
    locator_type: Literal["standard"] = "standard"
    standard_identity: BoundedText
    issuing_authority: BoundedText
    edition: BoundedText
    clause_or_location: BoundedText
    minimal_representation: BoundedText
    retrieved_at: AwareDatetime | None = None
    def to_domain(self) -> StandardLocator:
        return StandardLocator(**self.model_dump(exclude={"locator_type"}))


class ContextualLocatorSchema(StrictTechnicalReportSchema):
    locator_type: Literal["contextual"] = "contextual"
    context_id: UUID
    owning_context: BoundedText
    def to_domain(self) -> ContextualLocator:
        return ContextualLocator(**self.model_dump(exclude={"locator_type"}))


class TechnicalReportProvenanceSchema(StrictTechnicalReportSchema):
    entry_id: UUID
    ordinal: int = Field(ge=0)
    source_class: TechnicalReportSourceClass
    source_type: TechnicalReportSourceType
    is_material: StrictBool
    owning_capability: TechnicalReportOwningCapability | None
    reliance_role: BoundedText
    verification_status: TechnicalReportVerificationStatus
    availability_status: TechnicalReportAvailabilityStatus
    origin_attribution: BoundedText
    limitations: list[BoundedText] = Field(default_factory=list)
    locator: HistoricalBasisSchema | ExternalHumanLocatorSchema | StandardLocatorSchema | ContextualLocatorSchema
    integrity_algorithm: TechnicalReportIntegrityAlgorithm | None
    integrity_digest: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_material_shape(self):
        expected = {
            TechnicalReportSourceType.UNIVERSAL_CAPTURE: (TechnicalReportOwningCapability.UNIVERSAL_CAPTURE, CaptureHistoricalBasisSchema),
            TechnicalReportSourceType.EVIDENCE: (TechnicalReportOwningCapability.EVIDENCE, EvidenceHistoricalBasisSchema),
            TechnicalReportSourceType.ENGINEERING_OBJECT: (TechnicalReportOwningCapability.ENGINEERING_OBJECT, EngineeringObjectHistoricalBasisSchema),
            TechnicalReportSourceType.ENGINEERING_RELATIONSHIP: (TechnicalReportOwningCapability.ENGINEERING_RELATIONSHIP, EngineeringRelationshipHistoricalBasisSchema),
        }
        if self.source_class is TechnicalReportSourceClass.CANONICAL_MATERIAL:
            if self.source_type not in expected:
                raise ValueError("canonical source type is invalid")
            owner, locator_type = expected[self.source_type]
            if not self.is_material or self.owning_capability is not owner or not isinstance(self.locator, locator_type) or self.integrity_algorithm is not TechnicalReportIntegrityAlgorithm.SHA256 or self.integrity_digest is None:
                raise ValueError("canonical material requires complete historical integrity basis")
        elif self.source_class is TechnicalReportSourceClass.EXTERNAL_OR_HUMAN_MATERIAL:
            if self.owning_capability is not None or not self.is_material or self.source_type is not TechnicalReportSourceType.EXTERNAL_OR_HUMAN or not isinstance(self.locator, ExternalHumanLocatorSchema):
                raise ValueError("external/Human provenance is incoherent")
        elif self.source_class is TechnicalReportSourceClass.STANDARDS_MATERIAL:
            if self.owning_capability is not None or not self.is_material or self.source_type is not TechnicalReportSourceType.STANDARD or not isinstance(self.locator, StandardLocatorSchema):
                raise ValueError("standards provenance is incoherent")
        elif self.source_class is TechnicalReportSourceClass.CONTEXTUAL_NON_MATERIAL:
            if self.owning_capability is not None or self.is_material or self.source_type is not TechnicalReportSourceType.CONTEXTUAL or not isinstance(self.locator, ContextualLocatorSchema) or self.integrity_algorithm is not None or self.integrity_digest is not None:
                raise ValueError("contextual provenance is incoherent")
        return self

    def to_domain(self) -> TechnicalReportProvenanceEntry:
        return TechnicalReportProvenanceEntry(
            self.entry_id, self.ordinal, self.source_class, self.source_type,
            self.is_material, self.owning_capability, self.reliance_role,
            self.verification_status, self.availability_status,
            self.origin_attribution, tuple(self.limitations),
            self.locator.to_domain(), self.integrity_algorithm,
            self.integrity_digest,
        )


class TechnicalReportCreateRequest(StrictTechnicalReportSchema):
    workspace_id: PositiveIdentifier
    project_id: PositiveIdentifier | None = None
    purpose: TechnicalReportPurpose
    content: TechnicalReportContentSchema
    qualification: PreliminaryQualificationSchema
    provenance: list[TechnicalReportProvenanceSchema]


class TechnicalReportReviseDraftRequest(StrictTechnicalReportSchema):
    expected_version: PositiveVersion
    expected_draft_revision_id: UUID
    content: TechnicalReportContentSchema
    qualification: PreliminaryQualificationSchema
    provenance: list[TechnicalReportProvenanceSchema]
    rationale: Rationale


class TechnicalReportAcceptRequest(StrictTechnicalReportSchema):
    expected_version: PositiveVersion
    exact_draft_revision_id: UUID
    confirmed: Literal[True]
    rationale: Rationale


class TechnicalReportCreateSuccessorRequest(StrictTechnicalReportSchema):
    expected_predecessor_version: PositiveVersion
    workspace_id: PositiveIdentifier
    project_id: PositiveIdentifier | None = None
    purpose: TechnicalReportPurpose
    content: TechnicalReportContentSchema
    qualification: PreliminaryQualificationSchema
    provenance: list[TechnicalReportProvenanceSchema]
    selected_copy_references: list[UUID] = Field(default_factory=list)
    rationale: Rationale


class TechnicalReportFilter(StrictTechnicalReportSchema):
    workspace_id: PositiveIdentifier
    project_id: PositiveIdentifier | None = None
    purpose: TechnicalReportPurpose | None = None
    lifecycle: TechnicalReportLifecycle | None = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class TechnicalReportSummary(StrictTechnicalReportSchema):
    id: UUID
    organization_id: UUID
    workspace_id: PositiveIdentifier
    project_id: PositiveIdentifier | None
    owner_id: PositiveIdentifier
    purpose: TechnicalReportPurpose
    lifecycle: TechnicalReportLifecycle
    version: PositiveVersion
    draft_revision_id: UUID
    is_preliminary: StrictBool
    predecessor_report_id: UUID | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    allowed_actions: tuple[str, ...] = ()


class TechnicalReportDraftDetail(TechnicalReportSummary):
    content: TechnicalReportContentSchema
    qualification: PreliminaryQualificationSchema
    provenance: list[TechnicalReportProvenanceSchema]


class TechnicalReportAcceptedSnapshotSchema(StrictTechnicalReportSchema):
    report_id: UUID
    purpose: TechnicalReportPurpose
    organization_id: UUID
    workspace_id: PositiveIdentifier
    project_id: PositiveIdentifier | None
    content: TechnicalReportContentSchema
    qualification: PreliminaryQualificationSchema
    provenance: list[TechnicalReportProvenanceSchema]
    accepted_draft_revision_id: UUID
    accepted_aggregate_version: PositiveVersion
    accepted_by_id: PositiveIdentifier
    accepted_at: AwareDatetime
    predecessor_report_id: UUID | None
    integrity_digest: str = Field(pattern=r"^[0-9a-f]{64}$")


class TechnicalReportAcceptedDetail(TechnicalReportSummary):
    accepted_snapshot: TechnicalReportAcceptedSnapshotSchema
    accepted_by_id: PositiveIdentifier
    accepted_at: AwareDatetime
    accepted_draft_revision_id: UUID
    accepted_aggregate_version: PositiveVersion


class TechnicalReportListResponse(StrictTechnicalReportSchema):
    items: list[TechnicalReportSummary]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    size: int = Field(ge=1, le=100)


class TechnicalReportAIProposalRequest(StrictTechnicalReportSchema):
    expected_version: PositiveVersion
    expected_draft_revision_id: UUID
    human_instruction: Rationale
    selected_source_entry_ids: list[UUID] = Field(default_factory=list)

    @field_validator("selected_source_entry_ids")
    @classmethod
    def unique_sources(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("selected source entry IDs must be unique")
        return value


class TechnicalReportAIProposalResponse(StrictTechnicalReportSchema):
    proposal_text: BoundedText
    attribution: BoundedText
    authoritative: Literal[False] = False


class TechnicalReportLineageResponse(StrictTechnicalReportSchema):
    subject: TechnicalReportSummary
    predecessor: TechnicalReportSummary | None
    successors: TechnicalReportListResponse
