"""Strict pure contracts for PATCH-049 Project Completeness Batch 1."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.project_context import (
    AuthorityClassification,
    ContextObservationStatus,
    ProjectContextSectionKind,
    TemporalClassification,
)


class ProjectCompletenessDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CompletenessClassification(str, Enum):
    PRESENT = "present"
    MISSING = "missing"
    INDETERMINATE = "indeterminate"
    NOT_DISCLOSED = "not_disclosed"
    NOT_APPLICABLE = "not_applicable"


class CompletenessObservationStatus(str, Enum):
    COMPLETE_WITHIN_BOUNDS = "complete_within_bounds"
    PARTIAL = "partial"


class CompletenessAuthorityClass(str, Enum):
    DERIVED = "derived"


class RuleCategory(str, Enum):
    PROJECT_BASIS = "project_basis"
    EXECUTION = "execution"
    DELIVERABLES = "deliverables"
    ENGINEERING_CONTEXT = "engineering_context"
    VERIFICATION_EVIDENCE = "verification_evidence"


class RuleApplicabilityKind(str, Enum):
    ALWAYS = "always"
    STAGE_AT_LEAST = "stage_at_least"
    VISIBLE_PARENT_EXISTS = "visible_parent_exists"


class RulePredicateKind(str, Enum):
    TRUE_FIELD = "true_field"
    NONBLANK_FIELD = "nonblank_field"
    NONEMPTY_TUPLE = "nonempty_tuple"
    VISIBLE_ITEM_EXISTS = "visible_item_exists"
    ANY_NESTED_ITEM = "any_nested_item"
    ALL_VISIBLE_FIELD_PRESENT = "all_visible_field_present"
    ALL_VISIBLE_FIELD_TRUE = "all_visible_field_true"


class EvidenceReferenceKind(str, Enum):
    VISIBLE_FACT = "visible_fact"
    VISIBLE_SECTION_STATE = "visible_section_state"


class LimitationCode(str, Enum):
    SOURCE_PARTIAL = "source_partial"
    SOURCE_UNAVAILABLE = "source_unavailable"
    SOURCE_NOT_DISCLOSED = "source_not_disclosed"
    SOURCE_TRUNCATED = "source_truncated"
    APPLICABILITY_INDETERMINATE = "applicability_indeterminate"
    OBSERVATION_INDETERMINATE = "observation_indeterminate"
    EVIDENCE_REFERENCE_TRUNCATED = "evidence_reference_truncated"
    NON_ATOMIC_OBSERVATION = "non_atomic_observation"


class ApplicabilityDescriptorV1(ProjectCompletenessDTO):
    code: str = Field(pattern=r"^[a-z0-9_.:-]{1,128}$")
    kind: RuleApplicabilityKind
    terms: tuple[str, ...] = Field(default=(), max_length=8)


class ObservablePredicateDescriptorV1(ProjectCompletenessDTO):
    code: str = Field(pattern=r"^[a-z0-9_.:-]{1,128}$")
    kind: RulePredicateKind
    fields: tuple[str, ...] = Field(min_length=1, max_length=8)


class CompletenessRuleDescriptorV1(ProjectCompletenessDTO):
    rule_id: str = Field(pattern=r"^[a-z0-9_.-]{1,128}$")
    rule_version: Literal[1] = 1
    ordinal: int = Field(ge=1, le=14)
    category: RuleCategory
    title: str = Field(min_length=1, max_length=256)
    description: str = Field(min_length=1, max_length=1024)
    applicability: ApplicabilityDescriptorV1
    required_sections: tuple[ProjectContextSectionKind, ...] = Field(min_length=1, max_length=2)
    predicate: ObservablePredicateDescriptorV1
    question_template: str = Field(min_length=1, max_length=512)
    indeterminate_question_template: str = Field(min_length=1, max_length=512)
    checklist_template: str = Field(min_length=1, max_length=512)
    indeterminate_checklist_template: str = Field(min_length=1, max_length=512)
    limitation_codes: tuple[LimitationCode, ...] = Field(default=(), max_length=8)
    graph_requirement: None = None

    @model_validator(mode="after")
    def _unique_sections(self) -> "CompletenessRuleDescriptorV1":
        if len(set(self.required_sections)) != len(self.required_sections):
            raise ValueError("required sections must be unique")
        return self


class RuleCatalogDescriptorV1(ProjectCompletenessDTO):
    catalog_id: Literal["project_completeness.v1"] = "project_completeness.v1"
    catalog_version: Literal[1] = 1
    catalog_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    rules: tuple[CompletenessRuleDescriptorV1, ...] = Field(min_length=14, max_length=14)

    @model_validator(mode="after")
    def _validate_catalog(self) -> "RuleCatalogDescriptorV1":
        ids = tuple(rule.rule_id for rule in self.rules)
        ordinals = tuple(rule.ordinal for rule in self.rules)
        if len(set(ids)) != 14 or len(set(ordinals)) != 14:
            raise ValueError("catalog identifiers and ordinals must be unique")
        if ordinals != tuple(range(1, 15)):
            raise ValueError("catalog ordinals must be one through fourteen")
        if ids != tuple(sorted(ids)):
            raise ValueError("catalog rules must use lexicographic order")
        return self


class VisibleFactReferenceV1(ProjectCompletenessDTO):
    reference_kind: Literal[EvidenceReferenceKind.VISIBLE_FACT] = EvidenceReferenceKind.VISIBLE_FACT
    owner_kind: str = Field(min_length=1, max_length=64)
    item_kind: str = Field(min_length=1, max_length=64)
    selector: str = Field(min_length=1, max_length=128)
    version: int | None = Field(default=None, gt=0)
    standing: str | None = Field(default=None, min_length=1, max_length=64)
    source_observed_at: datetime | None = None
    observed_at: datetime
    authority_class: AuthorityClassification
    temporal_class: TemporalClassification
    display_label: str | None = Field(default=None, max_length=512)
    supported_predicate_code: str = Field(pattern=r"^[a-z0-9_.:-]{1,128}$")


class VisibleSectionStateReferenceV1(ProjectCompletenessDTO):
    reference_kind: Literal[EvidenceReferenceKind.VISIBLE_SECTION_STATE] = EvidenceReferenceKind.VISIBLE_SECTION_STATE
    section_kind: ProjectContextSectionKind
    state: Literal["available", "empty", "not_established"]
    observed_at: datetime | None = None
    truncated: bool
    supported_predicate_code: str = Field(pattern=r"^[a-z0-9_.:-]{1,128}$")


CompletenessEvidenceReferenceV1: TypeAlias = Annotated[
    VisibleFactReferenceV1 | VisibleSectionStateReferenceV1,
    Field(discriminator="reference_kind"),
]


class ClarificationQuestionV1(ProjectCompletenessDTO):
    question_id: str = Field(pattern=r"^[a-z0-9_.-]{1,180}$")
    rule_id: str = Field(pattern=r"^[a-z0-9_.-]{1,128}$")
    rule_version: Literal[1] = 1
    ordinal: Literal[1] = 1
    text: str = Field(min_length=1, max_length=512)
    advisory: Literal[True] = True


class CompletenessChecklistItemV1(ProjectCompletenessDTO):
    checklist_id: str = Field(pattern=r"^[a-z0-9_.-]{1,180}$")
    rule_id: str = Field(pattern=r"^[a-z0-9_.-]{1,128}$")
    rule_version: Literal[1] = 1
    ordinal: Literal[1] = 1
    text: str = Field(min_length=1, max_length=512)
    classification: CompletenessClassification
    advisory: Literal[True] = True


class CompletenessFindingV1(ProjectCompletenessDTO):
    rule_id: str = Field(pattern=r"^[a-z0-9_.-]{1,128}$")
    rule_version: Literal[1] = 1
    catalog_id: Literal["project_completeness.v1"] = "project_completeness.v1"
    catalog_version: Literal[1] = 1
    catalog_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    category: RuleCategory
    classification: CompletenessClassification
    title: str = Field(min_length=1, max_length=256)
    description: str = Field(min_length=1, max_length=1024)
    applicability_basis: tuple[str, ...] = Field(default=(), max_length=8)
    evidence: tuple[CompletenessEvidenceReferenceV1, ...] = Field(default=(), max_length=4)
    source_observation_started_at: datetime
    source_observation_completed_at: datetime
    limitation_codes: tuple[LimitationCode, ...] = Field(default=(), max_length=8)
    source_truncated: bool
    evidence_truncated: bool
    question: ClarificationQuestionV1 | None = None
    checklist_item: CompletenessChecklistItemV1 | None = None


class CompletenessObservationV1(ProjectCompletenessDTO):
    started_at: datetime
    completed_at: datetime
    source_observation_started_at: datetime
    source_observation_completed_at: datetime
    source_observation_status: ContextObservationStatus
    catalog: RuleCatalogDescriptorV1
    assessment_status: CompletenessObservationStatus
    authority_class: Literal[CompletenessAuthorityClass.DERIVED] = CompletenessAuthorityClass.DERIVED
    advisory: Literal[True] = True
    authoritative: Literal[False] = False
    limitation_codes: tuple[LimitationCode, ...] = Field(default=(), max_length=8)
    findings: tuple[CompletenessFindingV1, ...] = Field(min_length=14, max_length=14)

    @model_validator(mode="after")
    def _validate_observation(self) -> "CompletenessObservationV1":
        if self.completed_at < self.started_at:
            raise ValueError("observation time order is invalid")
        if self.source_observation_completed_at < self.source_observation_started_at:
            raise ValueError("source observation time order is invalid")
        if tuple(item.rule_id for item in self.findings) != tuple(rule.rule_id for rule in self.catalog.rules):
            raise ValueError("findings must match catalog order")
        return self


class CompletenessSuccess(ProjectCompletenessDTO):
    status: Literal["success"] = "success"
    observation: CompletenessObservationV1


class CompletenessPartialSuccess(ProjectCompletenessDTO):
    status: Literal["partial_success"] = "partial_success"
    observation: CompletenessObservationV1


class CompletenessProtectedNotFound(ProjectCompletenessDTO):
    status: Literal["protected_not_found"] = "protected_not_found"


class CompletenessInvalidRequest(ProjectCompletenessDTO):
    status: Literal["invalid_request"] = "invalid_request"


class CompletenessUnavailable(ProjectCompletenessDTO):
    status: Literal["unavailable"] = "unavailable"


CompletenessAssessmentResult: TypeAlias = Annotated[
    CompletenessSuccess | CompletenessPartialSuccess | CompletenessProtectedNotFound |
    CompletenessInvalidRequest | CompletenessUnavailable,
    Field(discriminator="status"),
]
