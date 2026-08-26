"""Closed typed prerequisites for PATCH-048 read-only context assembly."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Annotated, Literal, TypeAlias
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from app.enums.engineering_relationship import (
    RelationshipFamily,
    RelationshipType,
    validate_relationship_pair,
)


class ProjectContextDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ProjectContextSectionKind(str, Enum):
    PROJECT_BASIS = "project_basis"
    EXECUTION = "execution"
    DELIVERABLES = "deliverables"
    PROJECT_CONTROLS = "project_controls"
    ENGINEERING_CONTEXT = "engineering_context"
    ENGINEERING_OBJECTS = "engineering_objects"
    EVIDENCE = "evidence"
    SUPPORTING_FILES = "supporting_files"
    TECHNICAL_REPORTS = "technical_reports"
    ORGANIZATIONAL_MEMORY = "organizational_memory"


CANONICAL_SECTION_ORDER: tuple[ProjectContextSectionKind, ...] = (
    ProjectContextSectionKind.PROJECT_BASIS,
    ProjectContextSectionKind.EXECUTION,
    ProjectContextSectionKind.DELIVERABLES,
    ProjectContextSectionKind.PROJECT_CONTROLS,
    ProjectContextSectionKind.ENGINEERING_CONTEXT,
    ProjectContextSectionKind.ENGINEERING_OBJECTS,
    ProjectContextSectionKind.EVIDENCE,
    ProjectContextSectionKind.SUPPORTING_FILES,
    ProjectContextSectionKind.TECHNICAL_REPORTS,
    ProjectContextSectionKind.ORGANIZATIONAL_MEMORY,
)


class SourceAvailability(str, Enum):
    AVAILABLE = "available"
    EMPTY = "empty"
    NOT_ESTABLISHED = "not_established"
    NOT_DISCLOSED = "not_disclosed"
    UNAVAILABLE = "unavailable"


class ContextObservationStatus(str, Enum):
    COMPLETE_WITHIN_BOUNDS = "complete_within_bounds"
    PARTIAL = "partial"


class AuthorityClassification(str, Enum):
    HUMAN_AUTHORITATIVE = "human_authoritative"
    EXTERNAL_TOOL_AUTHORED = "external_tool_authored"
    CANONICAL_EVIDENCE = "canonical_evidence"
    DERIVED = "derived"
    CONTEXTUAL_ADVISORY = "contextual_advisory"


class TemporalClassification(str, Enum):
    CURRENT = "current"
    HISTORICAL = "historical"


class ContextNodeKind(str, Enum):
    PROJECT = "project"
    WORKSPACE = "workspace"
    EXECUTION_PLAN = "execution_plan"
    ACTIVITY = "activity"
    MILESTONE = "milestone"
    DELIVERABLE = "deliverable"
    DELIVERABLE_REVISION = "deliverable_revision"
    RISK = "risk"
    ISSUE = "issue"
    HUMAN_DECISION = "human_decision"
    CHANGE = "change"
    CHANGE_IMPACT = "change_impact"
    ENGINEERING_OBJECT = "engineering_object"
    ENGINEERING_CONTEXT = "engineering_context"
    EVIDENCE = "evidence"
    SUPPORTING_FILE = "supporting_file"
    TECHNICAL_REPORT = "technical_report"
    ORGANIZATIONAL_MEMORY = "organizational_memory"


INT_NODE_KINDS = frozenset({
    ContextNodeKind.PROJECT,
    ContextNodeKind.WORKSPACE,
    ContextNodeKind.ENGINEERING_CONTEXT,
})


class GraphDirection(str, Enum):
    OUTGOING = "outgoing"
    INCOMING = "incoming"
    BOTH = "both"


class ContextRelationshipKind(str, Enum):
    CONTEXT_REQUIRES = "context_requires"
    CONTEXT_PROVIDED_BY = "context_provided_by"
    CONTEXT_CONSUMED_BY = "context_consumed_by"
    CONTEXT_POTENTIALLY_AFFECTS = "context_potentially_affects"
    PLAN_ACTIVITY = "plan_activity"
    PLAN_MILESTONE = "plan_milestone"
    ACTIVITY_DEPENDENCY = "activity_dependency"
    MILESTONE_ACTIVITY = "milestone_activity"
    DELIVERABLE_ACTIVITY = "deliverable_activity"
    DELIVERABLE_MILESTONE = "deliverable_milestone"
    DELIVERABLE_REVISION = "deliverable_revision"
    REVISION_REPRESENTATION = "revision_representation"
    DECISION_SUCCESSOR = "decision_successor"
    CHANGE_SUCCESSOR = "change_successor"
    CHANGE_IMPACT = "change_impact"
    IMPACT_TARGET = "impact_target"
    EVIDENCE_SUPPORTING_FILE = "evidence_supporting_file"
    REPORT_EVIDENCE_PROVENANCE = "report_evidence_provenance"
    REPORT_OBJECT_PROVENANCE = "report_object_provenance"
    MEMORY_SOURCE_REPORT = "memory_source_report"


class ProjectContextActor(ProjectContextDTO):
    actor_id: int = Field(gt=0)
    organization_id: UUID


class ProjectContextScope(ProjectContextDTO):
    project_id: int = Field(gt=0)
    workspace_id: int | None = Field(default=None, gt=0)


class SectionPageRequest(ProjectContextDTO):
    page_size: int = Field(default=100, ge=1, le=100)
    continuation: str | None = Field(default=None, min_length=1, max_length=4096)


class ProjectContextSectionRequest(SectionPageRequest):
    kind: ProjectContextSectionKind


class ProjectContextRequest(ProjectContextDTO):
    scope: ProjectContextScope
    sections: tuple[ProjectContextSectionRequest, ...] = ()

    @model_validator(mode="after")
    def _validate_sections(self) -> "ProjectContextRequest":
        sections = self.sections or tuple(
            ProjectContextSectionRequest(kind=kind)
            for kind in CANONICAL_SECTION_ORDER
        )
        if not 1 <= len(sections) <= len(CANONICAL_SECTION_ORDER):
            raise ValueError("section count is invalid")
        kinds = tuple(section.kind for section in sections)
        if len(set(kinds)) != len(kinds):
            raise ValueError("section kinds must be unique")
        expected = tuple(kind for kind in CANONICAL_SECTION_ORDER if kind in kinds)
        if kinds != expected:
            raise ValueError("section kinds must use canonical order")
        object.__setattr__(self, "sections", sections)
        return self


class FactProvenance(ProjectContextDTO):
    owner_kind: str = Field(min_length=1, max_length=64)
    selector: str = Field(min_length=1, max_length=128)
    version: int | None = Field(default=None, gt=0)
    standing: str | None = Field(default=None, min_length=1, max_length=64)
    source_observed_at: datetime | None = None
    observed_at: datetime
    authority_class: AuthorityClassification
    temporal_class: TemporalClassification


class ContinuationMetadata(ProjectContextDTO):
    continuation: str = Field(min_length=1, max_length=4096)
    last_evaluated_key: str = Field(min_length=1, max_length=512)


class TruncationMetadata(ProjectContextDTO):
    truncated: bool
    continuation: ContinuationMetadata | None = None

    @model_validator(mode="after")
    def _validate_truncation(self) -> "TruncationMetadata":
        if self.truncated != (self.continuation is not None):
            raise ValueError("truncation and continuation must agree")
        return self


class SectionAvailable(ProjectContextDTO):
    state: Literal[SourceAvailability.AVAILABLE] = SourceAvailability.AVAILABLE
    visible_count: int = Field(ge=0, le=100)
    truncated: TruncationMetadata
    observed_at: datetime


class SectionEmpty(ProjectContextDTO):
    state: Literal[SourceAvailability.EMPTY] = SourceAvailability.EMPTY


class SectionNotEstablished(ProjectContextDTO):
    state: Literal[SourceAvailability.NOT_ESTABLISHED] = SourceAvailability.NOT_ESTABLISHED


class SectionNotDisclosed(ProjectContextDTO):
    state: Literal[SourceAvailability.NOT_DISCLOSED] = SourceAvailability.NOT_DISCLOSED


class SectionUnavailable(ProjectContextDTO):
    state: Literal[SourceAvailability.UNAVAILABLE] = SourceAvailability.UNAVAILABLE


SectionState: TypeAlias = Annotated[
    SectionAvailable | SectionEmpty | SectionNotEstablished | SectionNotDisclosed | SectionUnavailable,
    Field(discriminator="state"),
]


class ProjectContextProtectedNotFound(ProjectContextDTO):
    status: Literal["protected_not_found"] = "protected_not_found"


class ProjectContextInvalidRequest(ProjectContextDTO):
    status: Literal["invalid_request"] = "invalid_request"


class ProjectContextUnavailable(ProjectContextDTO):
    status: Literal["unavailable"] = "unavailable"


class _SectionItem(ProjectContextDTO):
    """Closed safe fields shared by owner-approved section projections only."""
    selector: str = Field(min_length=1, max_length=128)
    version: int | None = Field(default=None, gt=0)
    standing: str | None = Field(default=None, max_length=64)
    provenance: FactProvenance


class ProjectBasisItem(_SectionItem):
    item_kind: Literal["project_basis"] = "project_basis"
    version: int = Field(gt=0)
    standing: str = Field(min_length=1, max_length=64)
    project_id: int = Field(gt=0)
    project_code: str | None = Field(default=None, max_length=128)
    project_name: str | None = Field(default=None, max_length=512)
    project_status: str | None = Field(default=None, max_length=64)
    foundation_established: bool
    foundation_version: int | None = Field(default=None, gt=0)
    purpose: str | None = Field(default=None, max_length=2000)
    engineering_basis: str | None = Field(default=None, max_length=2000)
    current_stage: str | None = Field(default=None, max_length=128)
    readiness: str | None = Field(default=None, max_length=128)
    ordered_in_scope: tuple[str, ...] = Field(default=(), max_length=100)
    ordered_out_scope: tuple[str, ...] = Field(default=(), max_length=100)
    completion_basis: str | None = Field(default=None, max_length=2000)
    required_project_inputs: tuple[str, ...] = Field(default=(), max_length=100)


class ExecutionPlanItem(_SectionItem):
    item_kind: Literal["execution"] = "execution"
    version: int = Field(gt=0)
    standing: str = Field(min_length=1, max_length=64)
    plan_id: UUID
    project_id: int = Field(gt=0)
    plan_version: int = Field(gt=0)
    activities: tuple["ExecutionActivityItem", ...] = Field(default=(), max_length=200)
    milestones: tuple["ExecutionMilestoneItem", ...] = Field(default=(), max_length=50)
    dependencies: tuple["ActivityDependencyItem", ...] = Field(default=(), max_length=500)
    progress: "ExecutionProgressItem"


class ExecutionActivityItem(ProjectContextDTO):
    activity_id: UUID
    plan_id: UUID
    project_id: int = Field(gt=0)
    workspace_id: int | None = Field(default=None, gt=0)
    title: str = Field(min_length=1, max_length=512)
    ordinal: int = Field(ge=0)
    standing: str = Field(min_length=1, max_length=64)
    version: int = Field(gt=0)
    target_date: datetime | None = None
    blocker_present: bool


class ExecutionMilestoneItem(ProjectContextDTO):
    milestone_id: UUID
    plan_id: UUID
    project_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=512)
    ordinal: int = Field(ge=0)
    standing: str = Field(min_length=1, max_length=64)
    target_date: datetime | None = None


class ActivityDependencyItem(ProjectContextDTO):
    predecessor_activity_id: UUID
    dependent_activity_id: UUID


class ExecutionProgressItem(ProjectContextDTO):
    numerator: int = Field(ge=0)
    denominator: int = Field(gt=0)
    percent: int = Field(ge=0, le=100)


class DeliverableItem(_SectionItem):
    item_kind: Literal["deliverable"] = "deliverable"
    version: int = Field(gt=0)
    standing: str = Field(min_length=1, max_length=64)
    deliverable_id: UUID
    project_id: int = Field(gt=0)
    workspace_id: int | None = Field(default=None, gt=0)
    code: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=512)
    discipline: str = Field(min_length=1, max_length=64)
    deliverable_type: str = Field(min_length=1, max_length=64)
    purpose: str | None = Field(default=None, max_length=2000)
    activity_ids: tuple[UUID, ...] = Field(default=(), max_length=200)
    milestone_ids: tuple[UUID, ...] = Field(default=(), max_length=50)
    target_date: datetime | None = None
    external_authority: bool
    current_revision: "DeliverableRevisionItem | None" = None


class DeliverableRevisionItem(ProjectContextDTO):
    revision_id: UUID
    deliverable_id: UUID
    sequence: int = Field(gt=0)
    external_label: str | None = Field(default=None, max_length=128)
    standing: str = Field(min_length=1, max_length=64)
    version: int = Field(gt=0)
    representation_available: bool


class ProjectControlItem(_SectionItem):
    item_kind: Literal["project_control:risk", "project_control:issue", "project_control:human_decision", "project_control:change"]
    control_id: UUID
    version: int = Field(gt=0)
    standing: str = Field(min_length=1, max_length=64)
    project_id: int = Field(gt=0)
    workspace_id: int | None = Field(default=None, gt=0)
    temporal_class: TemporalClassification
    predecessor_present: bool
    category: str | None = Field(default=None, max_length=128)
    likelihood: str | None = Field(default=None, max_length=64)
    impact: str | None = Field(default=None, max_length=64)
    severity: str | None = Field(default=None, max_length=64)
    impacts: tuple["ChangeImpactItem", ...] = Field(default=(), max_length=100)


class ChangeImpactItem(ProjectContextDTO):
    impact_id: UUID
    change_id: UUID
    target_kind: str | None = Field(default=None, max_length=64)
    standing: str = Field(min_length=1, max_length=64)
    impact_class: Literal["potential", "confirmed"]


class EngineeringObjectItem(_SectionItem):
    item_kind: Literal["engineering_object"] = "engineering_object"
    object_id: UUID
    version: int = Field(gt=0)
    standing: str = Field(min_length=1, max_length=64)
    project_id: int = Field(gt=0)
    workspace_id: int | None = Field(default=None, gt=0)
    organization_id: UUID
    family: str = Field(min_length=1, max_length=64)
    discipline: str = Field(min_length=1, max_length=64)
    object_type: str = Field(min_length=1, max_length=64)
    object_subtype: str | None = Field(default=None, max_length=64)
    lifecycle: str = Field(min_length=1, max_length=64)
    authority_standing: str = Field(min_length=1, max_length=64)
    created_at: datetime
    updated_at: datetime


class EvidenceItem(_SectionItem):
    item_kind: Literal["evidence"] = "evidence"
    evidence_id: UUID
    version: int = Field(gt=0)
    standing: str = Field(min_length=1, max_length=64)
    project_id: int = Field(gt=0)
    workspace_id: int | None = Field(default=None, gt=0)
    evidence_kind: str = Field(min_length=1, max_length=64)
    safe_source_reference: str | None = Field(default=None, max_length=512)
    created_at: datetime
    updated_at: datetime


class SupportingFileItem(_SectionItem):
    item_kind: Literal["supporting_file"] = "supporting_file"
    asset_id: UUID
    version: int = Field(gt=0)
    standing: str = Field(min_length=1, max_length=64)
    project_id: int = Field(gt=0)
    workspace_id: int | None = Field(default=None, gt=0)
    filename: str = Field(min_length=1, max_length=512)
    media_type: str = Field(min_length=1, max_length=128)
    byte_size: int = Field(ge=0)
    lifecycle: str = Field(min_length=1, max_length=64)
    created_at: datetime
    updated_at: datetime


class TechnicalReportItem(_SectionItem):
    item_kind: Literal["technical_report"] = "technical_report"
    report_id: UUID
    version: int = Field(gt=0)
    standing: str = Field(min_length=1, max_length=64)
    project_id: int | None = Field(default=None, gt=0)
    workspace_id: int = Field(gt=0)
    report_type: str = Field(min_length=1, max_length=64)
    title_or_purpose: str | None = Field(default=None, max_length=2000)
    accepted_version_id: int = Field(gt=0)
    accepted_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    accepted_at: datetime


class OrganizationalMemoryItem(_SectionItem):
    item_kind: Literal["organizational_memory"] = "organizational_memory"
    memory_id: UUID
    version: int = Field(gt=0)
    standing: str = Field(min_length=1, max_length=64)
    project_id: int | None = Field(default=None, gt=0)
    workspace_id: int = Field(gt=0)
    limitations_present: bool
    source_report_id: UUID | None = None
    source_report_version: int | None = Field(default=None, gt=0)
    admitted_at: datetime


# Retained only for accepted Batch-1 owner seams. Batch-2 assembly never emits it.
class ProjectContextItem(_SectionItem):
    item_kind: str = Field(min_length=1, max_length=64)
    label: str | None = Field(default=None, max_length=512)


class ProjectContextSection(ProjectContextDTO):
    kind: ProjectContextSectionKind
    state: SectionState
    items: tuple["ProjectContextSectionItem", ...] = Field(default=(), max_length=100)

    @model_validator(mode="after")
    def _items_match_state(self) -> "ProjectContextSection":
        if self.state.state is SourceAvailability.AVAILABLE:
            if self.state.visible_count != len(self.items):
                raise ValueError("visible count must equal returned items")
        elif self.items:
            raise ValueError("nonavailable state cannot disclose items")
        return self


class ProjectContextSuccess(ProjectContextDTO):
    status: Literal["success"] = "success"
    observation_started_at: datetime
    observation_completed_at: datetime
    observation_status: ContextObservationStatus
    sections: tuple[ProjectContextSection, ...]

    @model_validator(mode="after")
    def _canonical_sections(self) -> "ProjectContextSuccess":
        kinds = tuple(section.kind for section in self.sections)
        expected = tuple(kind for kind in CANONICAL_SECTION_ORDER if kind in kinds)
        if not kinds or kinds != expected:
            raise ValueError("sections must use canonical order")
        return self


ProjectContextResult: TypeAlias = Annotated[
    ProjectContextSuccess | ProjectContextProtectedNotFound | ProjectContextInvalidRequest | ProjectContextUnavailable,
    Field(discriminator="status"),
]


class ContextNodeSelector(ProjectContextDTO):
    kind: ContextNodeKind
    value: StrictInt | UUID

    @model_validator(mode="after")
    def _validate_selector(self) -> "ContextNodeSelector":
        if self.kind in INT_NODE_KINDS:
            if type(self.value) is not int or self.value < 1:
                raise ValueError("node kind requires a positive integer selector")
        elif type(self.value) is not UUID:
            raise ValueError("node kind requires a UUID selector")
        return self


class EngineeringRelationshipDiscriminator(ProjectContextDTO):
    family: RelationshipFamily
    relationship_type: RelationshipType

    @model_validator(mode="after")
    def _validate_pair(self) -> "EngineeringRelationshipDiscriminator":
        validate_relationship_pair(self.family, self.relationship_type)
        return self


class ContextRelationshipEndpointKind(str, Enum):
    PROJECT = "project"
    WORKSPACE = "workspace"
    ENGINEERING_CONTEXT = "engineering_context"


class ContextRelationshipEndpointProjection(ProjectContextDTO):
    kind: ContextRelationshipEndpointKind
    selector: int = Field(gt=0)


class ContextRelationshipProjection(ProjectContextDTO):
    relationship_id: int = Field(gt=0)
    relationship_key: str = Field(min_length=1, max_length=128)
    project_id: int = Field(gt=0)
    meaning: ContextRelationshipKind
    source: ContextRelationshipEndpointProjection
    target: ContextRelationshipEndpointProjection
    lifecycle: Literal["current"]
    version: int = Field(gt=0)
    provenance: FactProvenance


class ContextPayloadAbsent(ProjectContextDTO):
    payload_kind: Literal["absent"] = "absent"


class ContextFactPayload(ProjectContextDTO):
    payload_kind: Literal["qualified_fact"] = "qualified_fact"
    statement: str = Field(min_length=1, max_length=10000)
    uncertainty: str | None = Field(default=None, max_length=2000)


class ContextEngineeringValuePayload(ProjectContextDTO):
    payload_kind: Literal["qualified_engineering_value"] = "qualified_engineering_value"
    numeric_value: str | None = Field(default=None, max_length=128)
    unit: str | None = Field(default=None, max_length=128)
    quantity_type: str | None = Field(default=None, max_length=128)
    basis: str | None = Field(default=None, max_length=2000)


class ContextAssumptionPayload(ProjectContextDTO):
    payload_kind: Literal["assumption"] = "assumption"
    statement: str = Field(min_length=1, max_length=10000)
    reason: str | None = Field(default=None, max_length=2000)
    consequence: str | None = Field(default=None, max_length=2000)
    confirmation_condition: str | None = Field(default=None, max_length=2000)


ContextPayload: TypeAlias = Annotated[
    ContextPayloadAbsent | ContextFactPayload | ContextEngineeringValuePayload | ContextAssumptionPayload,
    Field(discriminator="payload_kind"),
]


class EngineeringContextProjection(ProjectContextDTO):
    context_id: int = Field(gt=0)
    context_key: str = Field(min_length=1, max_length=128)
    project_id: int = Field(gt=0)
    workspace_id: int | None = Field(default=None, gt=0)
    kind: str = Field(min_length=1, max_length=64)
    authority: str = Field(min_length=1, max_length=64)
    lifecycle: Literal["current"]
    purpose: str | None = Field(default=None, max_length=2000)
    version: int = Field(gt=0)
    payload: ContextPayload
    created_at: datetime
    updated_at: datetime
    provenance: FactProvenance


ProjectContextSectionItem: TypeAlias = (
    ProjectBasisItem | ExecutionPlanItem | DeliverableItem | ProjectControlItem |
    EngineeringContextProjection | EngineeringObjectItem | EvidenceItem |
    SupportingFileItem | TechnicalReportItem | OrganizationalMemoryItem
)


class OwnerResolved(ProjectContextDTO):
    status: Literal["resolved"] = "resolved"
    item: EngineeringContextProjection | ContextRelationshipProjection | ProjectContextSectionItem | ProjectContextItem


class OwnerPage(ProjectContextDTO):
    status: Literal["page"] = "page"
    items: tuple[EngineeringContextProjection | ContextRelationshipProjection | ProjectContextSectionItem | ProjectContextItem, ...] = Field(max_length=100)
    has_more: bool = False
    last_evaluated_key: str | None = Field(default=None, max_length=512)
    observed_at: datetime


class OwnerProtected(ProjectContextDTO):
    status: Literal["protected"] = "protected"


class OwnerInvalid(ProjectContextDTO):
    """Payload-free owner construction/selector failure; never a section fact."""
    status: Literal["invalid"] = "invalid"


class OwnerUnavailable(ProjectContextDTO):
    status: Literal["unavailable"] = "unavailable"


OwnerReadResult: TypeAlias = Annotated[
    OwnerResolved | OwnerPage | OwnerProtected | OwnerInvalid | OwnerUnavailable,
    Field(discriminator="status"),
]


# Batch 3: closed EKG read contracts.  These deliberately model every node
# variant instead of accepting an open mapping or universal resolver payload.
class NodeNavigation(ProjectContextDTO):
    project_id: int = Field(gt=0)
    workspace_id: int | None = Field(default=None, gt=0)


class _NodeProjection(ProjectContextDTO):
    navigation: NodeNavigation
    provenance: FactProvenance
    authority_class: AuthorityClassification
    temporal_class: TemporalClassification


class ProjectNode(_NodeProjection):
    node_kind: Literal[ContextNodeKind.PROJECT] = ContextNodeKind.PROJECT
    selector: StrictInt = Field(gt=0)
    project_code: str = Field(min_length=1, max_length=128)
    project_name: str = Field(min_length=1, max_length=512)
    lifecycle_status: str = Field(min_length=1, max_length=64)


class WorkspaceNode(_NodeProjection):
    node_kind: Literal[ContextNodeKind.WORKSPACE] = ContextNodeKind.WORKSPACE
    selector: StrictInt = Field(gt=0)
    project_id: int = Field(gt=0)
    discipline: str = Field(min_length=1, max_length=64)
    workspace_status: str = Field(min_length=1, max_length=64)


class ExecutionPlanNode(_NodeProjection):
    node_kind: Literal[ContextNodeKind.EXECUTION_PLAN] = ContextNodeKind.EXECUTION_PLAN
    selector: UUID
    project_id: int = Field(gt=0)
    plan_version: int = Field(gt=0)
    established_standing: str = Field(min_length=1, max_length=64)


class ActivityNode(_NodeProjection):
    node_kind: Literal[ContextNodeKind.ACTIVITY] = ContextNodeKind.ACTIVITY
    selector: UUID
    plan_id: UUID
    project_id: int = Field(gt=0)
    workspace_id: int | None = Field(default=None, gt=0)
    title: str = Field(min_length=1, max_length=512)
    ordinal: int = Field(ge=0, le=199)
    standing: str = Field(min_length=1, max_length=64)
    version: int = Field(gt=0)
    target_date: date | None = None
    blocker_present: bool


class MilestoneNode(_NodeProjection):
    node_kind: Literal[ContextNodeKind.MILESTONE] = ContextNodeKind.MILESTONE
    selector: UUID
    plan_id: UUID
    project_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=512)
    ordinal: int = Field(ge=0, le=49)
    standing: str = Field(min_length=1, max_length=64)
    target_date: date | None = None


class DeliverableNode(_NodeProjection):
    node_kind: Literal[ContextNodeKind.DELIVERABLE] = ContextNodeKind.DELIVERABLE
    selector: UUID
    project_id: int = Field(gt=0)
    workspace_id: int | None = Field(default=None, gt=0)
    code: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=512)
    discipline: str = Field(min_length=1, max_length=64)
    deliverable_type: str = Field(min_length=1, max_length=64)
    standing: str = Field(min_length=1, max_length=64)
    version: int = Field(gt=0)
    external_authority: bool
    target_date: date | None = None


class DeliverableRevisionNode(_NodeProjection):
    node_kind: Literal[ContextNodeKind.DELIVERABLE_REVISION] = ContextNodeKind.DELIVERABLE_REVISION
    selector: UUID
    deliverable_id: UUID
    sequence: int = Field(gt=0)
    external_label: str | None = Field(default=None, max_length=128)
    standing: str = Field(min_length=1, max_length=64)
    version: int = Field(gt=0)
    representation_available: bool


class RiskNode(_NodeProjection):
    node_kind: Literal[ContextNodeKind.RISK] = ContextNodeKind.RISK
    selector: UUID
    project_id: int = Field(gt=0)
    workspace_id: int | None = Field(default=None, gt=0)
    category: str = Field(min_length=1, max_length=128)
    likelihood: str = Field(min_length=1, max_length=64)
    impact: str = Field(min_length=1, max_length=64)
    standing: str = Field(min_length=1, max_length=64)
    version: int = Field(gt=0)


class IssueNode(_NodeProjection):
    node_kind: Literal[ContextNodeKind.ISSUE] = ContextNodeKind.ISSUE
    selector: UUID
    project_id: int = Field(gt=0)
    workspace_id: int | None = Field(default=None, gt=0)
    severity: str = Field(min_length=1, max_length=64)
    standing: str = Field(min_length=1, max_length=64)
    version: int = Field(gt=0)


class DecisionNode(_NodeProjection):
    node_kind: Literal[ContextNodeKind.HUMAN_DECISION] = ContextNodeKind.HUMAN_DECISION
    selector: UUID
    project_id: int = Field(gt=0)
    workspace_id: int | None = Field(default=None, gt=0)
    standing: str = Field(min_length=1, max_length=64)
    version: int = Field(gt=0)
    predecessor_present: bool


class ChangeNode(_NodeProjection):
    node_kind: Literal[ContextNodeKind.CHANGE] = ContextNodeKind.CHANGE
    selector: UUID
    project_id: int = Field(gt=0)
    workspace_id: int | None = Field(default=None, gt=0)
    standing: str = Field(min_length=1, max_length=64)
    version: int = Field(gt=0)
    predecessor_present: bool


class ChangeImpactNode(_NodeProjection):
    node_kind: Literal[ContextNodeKind.CHANGE_IMPACT] = ContextNodeKind.CHANGE_IMPACT
    selector: UUID
    change_id: UUID
    target_kind: str | None = Field(default=None, max_length=64)
    standing: str = Field(min_length=1, max_length=64)
    impact_class: Literal["potential", "human_confirmed"]


class EngineeringObjectNode(_NodeProjection):
    node_kind: Literal[ContextNodeKind.ENGINEERING_OBJECT] = ContextNodeKind.ENGINEERING_OBJECT
    selector: UUID
    organization_id: UUID
    project_id: int = Field(gt=0)
    workspace_id: int | None = Field(default=None, gt=0)
    family: str = Field(min_length=1, max_length=64)
    discipline: str = Field(min_length=1, max_length=64)
    object_type: str = Field(min_length=1, max_length=64)
    object_subtype: str | None = Field(default=None, max_length=64)
    lifecycle: str = Field(min_length=1, max_length=64)
    authority_standing: str = Field(min_length=1, max_length=64)
    version: int = Field(gt=0)
    created_at: datetime
    updated_at: datetime


class EngineeringContextNode(_NodeProjection):
    node_kind: Literal[ContextNodeKind.ENGINEERING_CONTEXT] = ContextNodeKind.ENGINEERING_CONTEXT
    selector: StrictInt = Field(gt=0)
    project_id: int = Field(gt=0)
    workspace_id: int | None = Field(default=None, gt=0)
    context_kind: str = Field(min_length=1, max_length=64)
    authority: str = Field(min_length=1, max_length=64)
    lifecycle: str = Field(min_length=1, max_length=64)
    version: int = Field(gt=0)
    typed_payload_present: bool


class EvidenceNode(_NodeProjection):
    node_kind: Literal[ContextNodeKind.EVIDENCE] = ContextNodeKind.EVIDENCE
    selector: UUID
    project_id: int = Field(gt=0)
    workspace_id: int | None = Field(default=None, gt=0)
    evidence_kind: str = Field(min_length=1, max_length=64)
    standing: str = Field(min_length=1, max_length=64)
    version: int = Field(gt=0)
    created_at: datetime
    updated_at: datetime


class SupportingFileNode(_NodeProjection):
    node_kind: Literal[ContextNodeKind.SUPPORTING_FILE] = ContextNodeKind.SUPPORTING_FILE
    selector: UUID
    project_id: int = Field(gt=0)
    workspace_id: int | None = Field(default=None, gt=0)
    filename: str = Field(min_length=1, max_length=512)
    media_type: str = Field(min_length=1, max_length=128)
    byte_size: int = Field(ge=0)
    lifecycle: str = Field(min_length=1, max_length=64)
    version: int = Field(gt=0)
    created_at: datetime
    updated_at: datetime


class TechnicalReportNode(_NodeProjection):
    node_kind: Literal[ContextNodeKind.TECHNICAL_REPORT] = ContextNodeKind.TECHNICAL_REPORT
    selector: UUID
    project_id: int = Field(gt=0)
    workspace_id: int = Field(gt=0)
    report_type: str = Field(min_length=1, max_length=64)
    title_or_purpose: str | None = Field(default=None, max_length=2000)
    accepted_version_id: int = Field(gt=0)
    accepted_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    standing: Literal["accepted"] = "accepted"
    accepted_at: datetime


class OrganizationalMemoryNode(_NodeProjection):
    node_kind: Literal[ContextNodeKind.ORGANIZATIONAL_MEMORY] = ContextNodeKind.ORGANIZATIONAL_MEMORY
    selector: UUID
    project_id: int = Field(gt=0)
    workspace_id: int = Field(gt=0)
    standing: Literal["active"] = "active"
    version: int = Field(gt=0)
    limitations_present: bool
    admitted_at: datetime


NodeProjection: TypeAlias = Annotated[
    ProjectNode | WorkspaceNode | ExecutionPlanNode | ActivityNode | MilestoneNode |
    DeliverableNode | DeliverableRevisionNode | RiskNode | IssueNode | DecisionNode |
    ChangeNode | ChangeImpactNode | EngineeringObjectNode | EngineeringContextNode |
    EvidenceNode | SupportingFileNode | TechnicalReportNode | OrganizationalMemoryNode,
    Field(discriminator="node_kind"),
]


class GraphNodeResolved(ProjectContextDTO):
    status: Literal["resolved"] = "resolved"
    item: NodeProjection


GraphNodeReadResult: TypeAlias = Annotated[
    GraphNodeResolved | OwnerProtected | OwnerInvalid | OwnerUnavailable,
    Field(discriminator="status"),
]


class GraphEdgeCandidate(ProjectContextDTO):
    candidate_key: str = Field(min_length=1, max_length=512)
    relationship_selector: str = Field(min_length=1, max_length=128)
    relationship_kind: ContextRelationshipKind | EngineeringRelationshipDiscriminator
    source: ContextNodeSelector
    target: ContextNodeSelector
    provenance: FactProvenance


class GraphCandidatePage(ProjectContextDTO):
    status: Literal["page"] = "page"
    items: tuple[GraphEdgeCandidate, ...] = Field(max_length=91)
    has_more: bool = False
    last_evaluated_key: str | None = Field(default=None, max_length=512)
    observed_at: datetime


class ContextEdgeProjection(ProjectContextDTO):
    relationship_selector: str = Field(min_length=1, max_length=128)
    relationship_kind: ContextRelationshipKind | EngineeringRelationshipDiscriminator
    source: ContextNodeSelector
    target: ContextNodeSelector
    provenance: FactProvenance


class GetContextNodeRequest(ProjectContextDTO):
    scope: ProjectContextScope
    selector: ContextNodeSelector


class ExpandOneHopRequest(ProjectContextDTO):
    scope: ProjectContextScope
    start: ContextNodeSelector
    relationship_kinds: tuple[ContextRelationshipKind | EngineeringRelationshipDiscriminator, ...] = Field(
        default=(), max_length=64
    )
    direction: GraphDirection = GraphDirection.BOTH
    page_size: int = Field(default=91, ge=1, le=91)
    continuation: str | None = Field(default=None, min_length=1, max_length=4096)

    @model_validator(mode="after")
    def _validate_relationship_kinds(self) -> "ExpandOneHopRequest":
        keys: list[str] = []
        for item in self.relationship_kinds:
            if isinstance(item, ContextRelationshipKind):
                keys.append(f"context:{item.value}")
            else:
                keys.append(f"engineering:{item.family.value}:{item.relationship_type.value}")
        if len(keys) != len(set(keys)):
            raise ValueError("relationship kinds must be distinct")
        if keys != sorted(keys):
            raise ValueError("relationship kinds must use canonical ordering")
        return self


class ContextNodeSuccess(ProjectContextDTO):
    status: Literal["success"] = "success"
    node: NodeProjection


class OneHopSuccess(ProjectContextDTO):
    status: Literal["success"] = "success"
    start: NodeProjection
    edges: tuple[ContextEdgeProjection, ...] = Field(max_length=91)
    nodes: tuple[NodeProjection, ...] = Field(max_length=91)
    truncated: TruncationMetadata


ContextNodeResult: TypeAlias = Annotated[
    ContextNodeSuccess | ProjectContextProtectedNotFound | ProjectContextInvalidRequest | ProjectContextUnavailable,
    Field(discriminator="status"),
]
OneHopResult: TypeAlias = Annotated[
    OneHopSuccess | ProjectContextProtectedNotFound | ProjectContextInvalidRequest | ProjectContextUnavailable,
    Field(discriminator="status"),
]
