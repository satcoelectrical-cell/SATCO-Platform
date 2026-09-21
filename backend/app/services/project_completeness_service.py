"""Pure Project Completeness evaluator and governed owner observation service."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Callable

from app.ports.project_completeness import (
    CompletenessActor,
    CompletenessAssessmentRequest,
    ProjectContextObservationPort,
)

from app.schemas.project_completeness import (
    ApplicabilityDescriptorV1,
    ClarificationQuestionV1,
    CompletenessChecklistItemV1,
    CompletenessClassification,
    CompletenessEvidenceReferenceV1,
    CompletenessFindingV1,
    CompletenessObservationStatus,
    CompletenessObservationV1,
    CompletenessRuleDescriptorV1,
    EvidenceReferenceKind,
    LimitationCode,
    ObservablePredicateDescriptorV1,
    RuleApplicabilityKind,
    RuleCatalogDescriptorV1,
    RuleCategory,
    RulePredicateKind,
    VisibleFactReferenceV1,
    VisibleSectionStateReferenceV1,
)
from app.schemas.project_context import (
    ActivityDependencyItem,
    ChangeImpactItem,
    ContextAssumptionPayload,
    ContextEngineeringValuePayload,
    ContextFactPayload,
    ContextPayloadAbsent,
    ContinuationMetadata,
    ContextObservationStatus,
    CANONICAL_SECTION_ORDER,
    DeliverableItem,
    DeliverableRevisionItem,
    EngineeringContextProjection,
    EngineeringObjectItem,
    EvidenceItem,
    ExecutionActivityItem,
    ExecutionMilestoneItem,
    ExecutionPlanItem,
    ExecutionProgressItem,
    FactProvenance,
    OrganizationalMemoryItem,
    ProjectControlItem,
    ProjectBasisItem,
    ProjectContextSection,
    ProjectContextSectionKind,
    ProjectContextSectionRequest,
    ProjectContextSuccess,
    ProjectContextRequest,
    ProjectContextScope,
    ProjectContextProtectedNotFound,
    ProjectContextInvalidRequest,
    ProjectContextUnavailable,
    SectionAvailable,
    SectionEmpty,
    SectionNotDisclosed,
    SectionNotEstablished,
    SectionUnavailable,
    SourceAvailability,
    SupportingFileItem,
    TechnicalReportItem,
    TruncationMetadata,
)

from app.schemas.project_completeness import (
    CompletenessAssessmentResult,
    CompletenessInvalidRequest,
    CompletenessPartialSuccess,
    CompletenessProtectedNotFound,
    CompletenessSuccess,
    CompletenessUnavailable,
)

CATALOG_ID = "project_completeness.v1"
CATALOG_VERSION = 1
MAX_RULES = 14
MAX_FINDINGS = 14
MAX_QUESTIONS = 14
MAX_CHECKLIST_ITEMS = 14
MAX_EVIDENCE_PER_FINDING = 4
MAX_EVIDENCE_TOTAL = 56
MAX_EKG_CALLS = 0
MAX_VISIBLE_INPUTS = 1_000
MAX_RESPONSE_BYTES = 131_072


class _VisibleContextValidation(str, Enum):
    VALID = "valid"
    PROTECTED = "protected"
    UNAVAILABLE = "unavailable"


_MISSING = object()

_SECTION_ITEM_TYPES: dict[ProjectContextSectionKind, type[object]] = {
    ProjectContextSectionKind.PROJECT_BASIS: ProjectBasisItem,
    ProjectContextSectionKind.EXECUTION: ExecutionPlanItem,
    ProjectContextSectionKind.DELIVERABLES: DeliverableItem,
    ProjectContextSectionKind.PROJECT_CONTROLS: ProjectControlItem,
    ProjectContextSectionKind.ENGINEERING_CONTEXT: EngineeringContextProjection,
    ProjectContextSectionKind.ENGINEERING_OBJECTS: EngineeringObjectItem,
    ProjectContextSectionKind.EVIDENCE: EvidenceItem,
    ProjectContextSectionKind.SUPPORTING_FILES: SupportingFileItem,
    ProjectContextSectionKind.TECHNICAL_REPORTS: TechnicalReportItem,
    ProjectContextSectionKind.ORGANIZATIONAL_MEMORY: OrganizationalMemoryItem,
}
_NOT_ESTABLISHED_SECTIONS = frozenset({
    ProjectContextSectionKind.PROJECT_BASIS,
    ProjectContextSectionKind.EXECUTION,
})
_CONTEXT_PAYLOAD_TYPES = (
    ContextPayloadAbsent,
    ContextFactPayload,
    ContextEngineeringValuePayload,
    ContextAssumptionPayload,
)

_STAGE_RANK = {
    "definition": 0,
    "preparation": 1,
    "execution": 2,
    "verification": 3,
    "completion_readiness": 4,
}


def _rule(
    *, rule_id: str, ordinal: int, category: RuleCategory, title: str,
    description: str, applicability_code: str, applicability_kind: RuleApplicabilityKind,
    applicability_terms: tuple[str, ...], predicate_code: str,
    predicate_kind: RulePredicateKind, fields: tuple[str, ...],
    sections: tuple[ProjectContextSectionKind, ...], question: str, checklist: str,
) -> CompletenessRuleDescriptorV1:
    return CompletenessRuleDescriptorV1(
        rule_id=rule_id, ordinal=ordinal, category=category, title=title,
        description=description,
        applicability=ApplicabilityDescriptorV1(
            code=applicability_code, kind=applicability_kind,
            terms=applicability_terms,
        ),
        required_sections=sections,
        predicate=ObservablePredicateDescriptorV1(
            code=predicate_code, kind=predicate_kind, fields=fields,
        ),
        question_template=question,
        indeterminate_question_template="Verify whether the required governed information is visible and established.",
        checklist_template=checklist,
        indeterminate_checklist_template="Verify the required governed information through its canonical owner.",
    )


# The tuple is intentionally already in accepted lexicographic rule-id order.
CATALOG_RULES_V1: tuple[CompletenessRuleDescriptorV1, ...] = (
    _rule(rule_id="pc.deliverables.current_revision", ordinal=1, category=RuleCategory.DELIVERABLES,
          title="Current Deliverable revision", description="Every applicable visible Deliverable must have a governed current revision.",
          applicability_code="stage_execution_and_visible_deliverable", applicability_kind=RuleApplicabilityKind.VISIBLE_PARENT_EXISTS,
          applicability_terms=("execution", "visible_deliverable"), predicate_code="all_visible_field_present:current_revision",
          predicate_kind=RulePredicateKind.ALL_VISIBLE_FIELD_PRESENT, fields=("current_revision",),
          sections=(ProjectContextSectionKind.PROJECT_BASIS, ProjectContextSectionKind.DELIVERABLES),
          question="Which governed Deliverable requires a current revision?", checklist="Establish the current revision through Deliverable Control."),
    _rule(rule_id="pc.deliverables.register_established", ordinal=2, category=RuleCategory.DELIVERABLES,
          title="Deliverable register", description="An applicable Project must have at least one governed visible Deliverable.",
          applicability_code="stage_preparation", applicability_kind=RuleApplicabilityKind.STAGE_AT_LEAST,
          applicability_terms=("preparation",), predicate_code="visible_item_exists:deliverable",
          predicate_kind=RulePredicateKind.VISIBLE_ITEM_EXISTS, fields=("deliverable",),
          sections=(ProjectContextSectionKind.PROJECT_BASIS, ProjectContextSectionKind.DELIVERABLES),
          question="Which governed Deliverables must be established?", checklist="Establish the Deliverable register through Deliverable Control."),
    _rule(rule_id="pc.deliverables.representation_available", ordinal=3, category=RuleCategory.DELIVERABLES,
          title="Deliverable representation", description="Every applicable current Deliverable revision must have an available governed representation.",
          applicability_code="stage_verification_and_visible_current_revision", applicability_kind=RuleApplicabilityKind.VISIBLE_PARENT_EXISTS,
          applicability_terms=("verification", "visible_current_revision"), predicate_code="all_visible_field_true:current_revision.representation_available",
          predicate_kind=RulePredicateKind.ALL_VISIBLE_FIELD_TRUE, fields=("current_revision.representation_available",),
          sections=(ProjectContextSectionKind.PROJECT_BASIS, ProjectContextSectionKind.DELIVERABLES),
          question="Which current governed Deliverable revision requires an available representation?", checklist="Establish its representation through Deliverable Control or the governed external-authority reference."),
    _rule(rule_id="pc.engineering_context.established", ordinal=4, category=RuleCategory.ENGINEERING_CONTEXT,
          title="Engineering Context", description="Applicable current governed Engineering Context must be established.",
          applicability_code="stage_preparation", applicability_kind=RuleApplicabilityKind.STAGE_AT_LEAST,
          applicability_terms=("preparation",), predicate_code="visible_item_exists:engineering_context",
          predicate_kind=RulePredicateKind.VISIBLE_ITEM_EXISTS, fields=("engineering_context",),
          sections=(ProjectContextSectionKind.PROJECT_BASIS, ProjectContextSectionKind.ENGINEERING_CONTEXT),
          question="What governed Engineering Context must be established?", checklist="Establish current context through Engineering Context."),
    _rule(rule_id="pc.execution.activities_defined", ordinal=5, category=RuleCategory.EXECUTION,
          title="Execution activities", description="An applicable governed execution plan must define at least one Activity.",
          applicability_code="stage_preparation_and_visible_plan", applicability_kind=RuleApplicabilityKind.VISIBLE_PARENT_EXISTS,
          applicability_terms=("preparation", "visible_plan"), predicate_code="any_nested_item:activities",
          predicate_kind=RulePredicateKind.ANY_NESTED_ITEM, fields=("activities",),
          sections=(ProjectContextSectionKind.PROJECT_BASIS, ProjectContextSectionKind.EXECUTION),
          question="Which governed execution activities must be defined?", checklist="Define execution activities through Engineering Execution."),
    _rule(rule_id="pc.execution.milestones_defined", ordinal=6, category=RuleCategory.EXECUTION,
          title="Execution milestones", description="An applicable governed execution plan must define at least one Milestone.",
          applicability_code="stage_preparation_and_visible_plan", applicability_kind=RuleApplicabilityKind.VISIBLE_PARENT_EXISTS,
          applicability_terms=("preparation", "visible_plan"), predicate_code="any_nested_item:milestones",
          predicate_kind=RulePredicateKind.ANY_NESTED_ITEM, fields=("milestones",),
          sections=(ProjectContextSectionKind.PROJECT_BASIS, ProjectContextSectionKind.EXECUTION),
          question="Which governed execution milestones must be defined?", checklist="Define milestones through Engineering Execution."),
    _rule(rule_id="pc.execution.plan_established", ordinal=7, category=RuleCategory.EXECUTION,
          title="Execution plan", description="An applicable Project must have a governed execution plan.",
          applicability_code="stage_preparation", applicability_kind=RuleApplicabilityKind.STAGE_AT_LEAST,
          applicability_terms=("preparation",), predicate_code="visible_item_exists:execution",
          predicate_kind=RulePredicateKind.VISIBLE_ITEM_EXISTS, fields=("execution",),
          sections=(ProjectContextSectionKind.PROJECT_BASIS, ProjectContextSectionKind.EXECUTION),
          question="Has the governed execution plan been established?", checklist="Establish the plan through Engineering Execution."),
    _rule(rule_id="pc.project_basis.engineering_basis", ordinal=8, category=RuleCategory.PROJECT_BASIS,
          title="Engineering basis", description="The governed Project engineering basis must be stated.",
          applicability_code="always", applicability_kind=RuleApplicabilityKind.ALWAYS, applicability_terms=(),
          predicate_code="nonblank_field:engineering_basis", predicate_kind=RulePredicateKind.NONBLANK_FIELD,
          fields=("engineering_basis",), sections=(ProjectContextSectionKind.PROJECT_BASIS,),
          question="What governed engineering basis must be established for this Project?", checklist="Establish the engineering basis through Project Foundation."),
    _rule(rule_id="pc.project_basis.purpose", ordinal=9, category=RuleCategory.PROJECT_BASIS,
          title="Project purpose", description="The governed Project purpose must be stated.",
          applicability_code="always", applicability_kind=RuleApplicabilityKind.ALWAYS, applicability_terms=(),
          predicate_code="nonblank_field:purpose", predicate_kind=RulePredicateKind.NONBLANK_FIELD,
          fields=("purpose",), sections=(ProjectContextSectionKind.PROJECT_BASIS,),
          question="What governed purpose must be established for this Project?", checklist="Establish the Project purpose through Project Foundation."),
    _rule(rule_id="pc.project_completion.basis", ordinal=10, category=RuleCategory.PROJECT_BASIS,
          title="Completion basis", description="The governed Project completion basis must be stated.",
          applicability_code="always", applicability_kind=RuleApplicabilityKind.ALWAYS, applicability_terms=(),
          predicate_code="nonblank_field:completion_basis", predicate_kind=RulePredicateKind.NONBLANK_FIELD,
          fields=("completion_basis",), sections=(ProjectContextSectionKind.PROJECT_BASIS,),
          question="What governed completion basis must be established for this Project?", checklist="Establish the completion basis through Project Foundation."),
    _rule(rule_id="pc.project_foundation.established", ordinal=11, category=RuleCategory.PROJECT_BASIS,
          title="Project Foundation", description="The canonical Project Foundation must be established.",
          applicability_code="always", applicability_kind=RuleApplicabilityKind.ALWAYS, applicability_terms=(),
          predicate_code="true_field:foundation_established", predicate_kind=RulePredicateKind.TRUE_FIELD,
          fields=("foundation_established",), sections=(ProjectContextSectionKind.PROJECT_BASIS,),
          question="Has the governed Project Foundation been established?", checklist="Establish the Project Foundation through its canonical workflow."),
    _rule(rule_id="pc.project_inputs.declared", ordinal=12, category=RuleCategory.PROJECT_BASIS,
          title="Required Project inputs", description="At least one required governed Project input must be declared.",
          applicability_code="always", applicability_kind=RuleApplicabilityKind.ALWAYS, applicability_terms=(),
          predicate_code="nonempty_tuple:required_project_inputs", predicate_kind=RulePredicateKind.NONEMPTY_TUPLE,
          fields=("required_project_inputs",), sections=(ProjectContextSectionKind.PROJECT_BASIS,),
          question="Which required governed Project inputs must be declared?", checklist="Declare required Project inputs through Project Foundation."),
    _rule(rule_id="pc.project_scope.in_scope", ordinal=13, category=RuleCategory.PROJECT_BASIS,
          title="In-scope work", description="At least one governed in-scope Project statement must be established.",
          applicability_code="always", applicability_kind=RuleApplicabilityKind.ALWAYS, applicability_terms=(),
          predicate_code="nonempty_tuple:ordered_in_scope", predicate_kind=RulePredicateKind.NONEMPTY_TUPLE,
          fields=("ordered_in_scope",), sections=(ProjectContextSectionKind.PROJECT_BASIS,),
          question="What governed in-scope Project work must be established?", checklist="Establish in-scope work through Project Foundation."),
    _rule(rule_id="pc.verification.evidence_established", ordinal=14, category=RuleCategory.VERIFICATION_EVIDENCE,
          title="Verification Evidence", description="An applicable Project must have governed visible verification Evidence.",
          applicability_code="stage_verification", applicability_kind=RuleApplicabilityKind.STAGE_AT_LEAST,
          applicability_terms=("verification",), predicate_code="visible_item_exists:evidence",
          predicate_kind=RulePredicateKind.VISIBLE_ITEM_EXISTS, fields=("evidence",),
          sections=(ProjectContextSectionKind.PROJECT_BASIS, ProjectContextSectionKind.EVIDENCE),
          question="What governed verification Evidence must be established?", checklist="Establish verification Evidence through Evidence."),
)


def catalog_canonical_json(rules: tuple[CompletenessRuleDescriptorV1, ...] = CATALOG_RULES_V1) -> bytes:
    """Return the accepted UTF-8 catalog byte representation."""
    payload = [rule.model_dump(mode="json") for rule in rules]
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def catalog_digest(rules: tuple[CompletenessRuleDescriptorV1, ...] = CATALOG_RULES_V1) -> str:
    return hashlib.sha256(catalog_canonical_json(rules)).hexdigest()


def catalog_descriptor() -> RuleCatalogDescriptorV1:
    return RuleCatalogDescriptorV1(catalog_digest=catalog_digest(), rules=CATALOG_RULES_V1)


def _section_map(context: ProjectContextSuccess) -> dict[ProjectContextSectionKind, ProjectContextSection]:
    expected = tuple(ProjectContextSectionKind)
    actual = tuple(section.kind for section in context.sections)
    if actual != expected:
        raise ValueError("all canonical sections are required in canonical order")
    return {section.kind: section for section in context.sections}


def _state_classification(section: ProjectContextSection) -> CompletenessClassification | None:
    state = section.state.state
    if state is SourceAvailability.NOT_DISCLOSED:
        return CompletenessClassification.NOT_DISCLOSED
    if state is SourceAvailability.UNAVAILABLE:
        return CompletenessClassification.INDETERMINATE
    return None


def _is_truncated(section: ProjectContextSection) -> bool:
    return isinstance(section.state, SectionAvailable) and section.state.truncated.truncated


def _basis_item(section: ProjectContextSection) -> ProjectBasisItem | None:
    items = tuple(item for item in section.items if isinstance(item, ProjectBasisItem))
    return items[0] if len(items) == 1 else None


def _stage_result(basis_section: ProjectContextSection, minimum: str) -> tuple[CompletenessClassification | None, tuple[str, ...]]:
    state_result = _state_classification(basis_section)
    if state_result is not None:
        return state_result, ()
    basis = _basis_item(basis_section)
    if basis is None:
        return CompletenessClassification.INDETERMINATE if _is_truncated(basis_section) else CompletenessClassification.NOT_APPLICABLE, ()
    stage = basis.current_stage
    if stage not in _STAGE_RANK:
        return CompletenessClassification.INDETERMINATE, ()
    code = f"stage_{stage}"
    return (None, (code,)) if _STAGE_RANK[stage] >= _STAGE_RANK[minimum] else (CompletenessClassification.NOT_APPLICABLE, (code,))


def _section_existence(section: ProjectContextSection) -> CompletenessClassification:
    state_result = _state_classification(section)
    if state_result is not None:
        return state_result
    if section.items:
        return CompletenessClassification.PRESENT
    if _is_truncated(section):
        return CompletenessClassification.INDETERMINATE
    return CompletenessClassification.MISSING


def _basis_field(section: ProjectContextSection, getter: Callable[[ProjectBasisItem], object]) -> CompletenessClassification:
    state_result = _state_classification(section)
    if state_result is not None:
        return state_result
    basis = _basis_item(section)
    if basis is None:
        return CompletenessClassification.INDETERMINATE if _is_truncated(section) else CompletenessClassification.MISSING
    value = getter(basis)
    satisfied = bool(value.strip()) if isinstance(value, str) else bool(value)
    if satisfied:
        return CompletenessClassification.PRESENT
    return CompletenessClassification.INDETERMINATE if _is_truncated(section) else CompletenessClassification.MISSING


def _fact_reference(item: object, predicate_code: str) -> VisibleFactReferenceV1 | None:
    provenance = getattr(item, "provenance", None)
    selector = getattr(item, "selector", None)
    if provenance is None or not selector:
        return None
    label = None
    if isinstance(item, ProjectBasisItem):
        label = item.project_name
    elif isinstance(item, DeliverableItem):
        label = item.title or item.code
    return VisibleFactReferenceV1(
        owner_kind=provenance.owner_kind, item_kind=getattr(item, "item_kind", "engineering_context"),
        selector=selector, version=getattr(item, "version", None), standing=getattr(item, "standing", None),
        source_observed_at=provenance.source_observed_at, observed_at=provenance.observed_at,
        authority_class=provenance.authority_class, temporal_class=provenance.temporal_class,
        display_label=label, supported_predicate_code=predicate_code,
    )


def _section_reference(section: ProjectContextSection, predicate_code: str) -> VisibleSectionStateReferenceV1 | None:
    if section.state.state not in {SourceAvailability.AVAILABLE, SourceAvailability.EMPTY, SourceAvailability.NOT_ESTABLISHED}:
        return None
    return VisibleSectionStateReferenceV1(
        section_kind=section.kind, state=section.state.state.value,
        observed_at=getattr(section.state, "observed_at", None), truncated=_is_truncated(section),
        supported_predicate_code=predicate_code,
    )


def _dedup_evidence(references: tuple[CompletenessEvidenceReferenceV1, ...]) -> tuple[tuple[CompletenessEvidenceReferenceV1, ...], bool]:
    unique: dict[str, CompletenessEvidenceReferenceV1] = {}
    for reference in references:
        key = json.dumps(reference.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        unique[key] = reference
    ordered = tuple(unique[key] for key in sorted(unique))
    return ordered[:MAX_EVIDENCE_PER_FINDING], len(ordered) > MAX_EVIDENCE_PER_FINDING


def _references(rule: CompletenessRuleDescriptorV1, classification: CompletenessClassification, sections: dict[ProjectContextSectionKind, ProjectContextSection]) -> tuple[tuple[CompletenessEvidenceReferenceV1, ...], bool]:
    if classification is CompletenessClassification.NOT_DISCLOSED:
        return (), False
    refs: list[CompletenessEvidenceReferenceV1] = []
    for kind in rule.required_sections:
        section = sections[kind]
        if section.items:
            for item in section.items:
                ref = _fact_reference(item, rule.predicate.code)
                if ref is not None:
                    refs.append(ref)
        else:
            ref = _section_reference(section, rule.predicate.code)
            if ref is not None:
                refs.append(ref)
    if not refs:
        for kind in rule.required_sections:
            ref = _section_reference(sections[kind], rule.predicate.code)
            if ref is not None:
                refs.append(ref)
    return _dedup_evidence(tuple(refs))


def _evaluate_rule(rule: CompletenessRuleDescriptorV1, sections: dict[ProjectContextSectionKind, ProjectContextSection]) -> tuple[CompletenessClassification, tuple[str, ...]]:
    basis = sections[ProjectContextSectionKind.PROJECT_BASIS]
    if rule.rule_id.startswith("pc.project_"):
        getter: dict[str, Callable[[ProjectBasisItem], object]] = {
            "pc.project_basis.engineering_basis": lambda value: value.engineering_basis,
            "pc.project_basis.purpose": lambda value: value.purpose,
            "pc.project_completion.basis": lambda value: value.completion_basis,
            "pc.project_foundation.established": lambda value: value.foundation_established,
            "pc.project_inputs.declared": lambda value: value.required_project_inputs,
            "pc.project_scope.in_scope": lambda value: value.ordered_in_scope,
        }
        return _basis_field(basis, getter[rule.rule_id]), ("always_applicable",)

    minimum = "preparation"
    if rule.rule_id in {"pc.deliverables.current_revision"}:
        minimum = "execution"
    elif rule.rule_id in {"pc.deliverables.representation_available", "pc.verification.evidence_established"}:
        minimum = "verification"
    stage_result, basis_codes = _stage_result(basis, minimum)
    if stage_result is not None:
        return stage_result, basis_codes

    kind = rule.required_sections[-1]
    section = sections[kind]
    section_state = _state_classification(section)
    if section_state is not None:
        return section_state, basis_codes

    if rule.rule_id == "pc.execution.plan_established":
        return _section_existence(section), basis_codes
    if rule.rule_id in {"pc.execution.activities_defined", "pc.execution.milestones_defined"}:
        plans = tuple(item for item in section.items if isinstance(item, ExecutionPlanItem))
        if not plans:
            return (CompletenessClassification.INDETERMINATE if _is_truncated(section) else CompletenessClassification.NOT_APPLICABLE), basis_codes
        field = "activities" if rule.rule_id.endswith("activities_defined") else "milestones"
        return (CompletenessClassification.PRESENT if any(getattr(item, field) for item in plans) else CompletenessClassification.MISSING), basis_codes + ("visible_plan",)
    if rule.rule_id == "pc.deliverables.register_established":
        return _section_existence(section), basis_codes
    if rule.rule_id in {"pc.deliverables.current_revision", "pc.deliverables.representation_available"}:
        deliverables = tuple(item for item in section.items if isinstance(item, DeliverableItem))
        if not deliverables:
            return (CompletenessClassification.INDETERMINATE if _is_truncated(section) else CompletenessClassification.NOT_APPLICABLE), basis_codes
        if rule.rule_id.endswith("representation_available"):
            revisions = tuple(item.current_revision for item in deliverables if item.current_revision is not None)
            if not revisions:
                return CompletenessClassification.NOT_APPLICABLE, basis_codes
            if any(not item.representation_available for item in revisions):
                return CompletenessClassification.MISSING, basis_codes + ("visible_current_revision",)
            return (CompletenessClassification.INDETERMINATE if _is_truncated(section) else CompletenessClassification.PRESENT), basis_codes + ("visible_current_revision",)
        if any(item.current_revision is None for item in deliverables):
            return CompletenessClassification.MISSING, basis_codes + ("visible_deliverable",)
        return (CompletenessClassification.INDETERMINATE if _is_truncated(section) else CompletenessClassification.PRESENT), basis_codes + ("visible_deliverable",)
    if rule.rule_id == "pc.engineering_context.established":
        return _section_existence(section), basis_codes
    if rule.rule_id == "pc.verification.evidence_established":
        return _section_existence(section), basis_codes
    raise ValueError("unsupported catalog rule")


def _limitations(classification: CompletenessClassification, sections: dict[ProjectContextSectionKind, ProjectContextSection], rule: CompletenessRuleDescriptorV1) -> tuple[LimitationCode, ...]:
    result: list[LimitationCode] = []
    if classification is CompletenessClassification.NOT_DISCLOSED:
        result.append(LimitationCode.SOURCE_NOT_DISCLOSED)
    if classification is CompletenessClassification.INDETERMINATE:
        result.append(LimitationCode.OBSERVATION_INDETERMINATE)
    if any(_is_truncated(sections[kind]) for kind in rule.required_sections):
        result.append(LimitationCode.SOURCE_TRUNCATED)
    return tuple(dict.fromkeys(result))


def _question(rule: CompletenessRuleDescriptorV1, classification: CompletenessClassification) -> ClarificationQuestionV1 | None:
    if classification not in {CompletenessClassification.MISSING, CompletenessClassification.INDETERMINATE}:
        return None
    text = rule.question_template if classification is CompletenessClassification.MISSING else rule.indeterminate_question_template
    return ClarificationQuestionV1(question_id=f"{rule.rule_id}.question.v1", rule_id=rule.rule_id, text=text)


def _checklist(rule: CompletenessRuleDescriptorV1, classification: CompletenessClassification) -> CompletenessChecklistItemV1 | None:
    if classification not in {CompletenessClassification.MISSING, CompletenessClassification.INDETERMINATE}:
        return None
    text = rule.checklist_template if classification is CompletenessClassification.MISSING else rule.indeterminate_checklist_template
    return CompletenessChecklistItemV1(checklist_id=f"{rule.rule_id}.check.v1", rule_id=rule.rule_id, text=text, classification=classification)


def evaluate_project_context(context: ProjectContextSuccess, *, now: datetime | None = None) -> CompletenessObservationV1:
    """Evaluate all fourteen rules over an already authorized public context."""
    sections = _section_map(context)
    catalog = catalog_descriptor()
    if len(CATALOG_RULES_V1) != MAX_RULES:
        raise ValueError("catalog rule limit is invalid")
    started = now or datetime.now(timezone.utc)
    findings: list[CompletenessFindingV1] = []
    questions = 0
    checklist_items = 0
    evidence_total = 0
    for rule in CATALOG_RULES_V1:
        classification, applicability_basis = _evaluate_rule(rule, sections)
        evidence, evidence_truncated = _references(rule, classification, sections)
        question = _question(rule, classification)
        checklist = _checklist(rule, classification)
        questions += int(question is not None)
        checklist_items += int(checklist is not None)
        evidence_total += len(evidence)
        findings.append(CompletenessFindingV1(
            rule_id=rule.rule_id, catalog_digest=catalog.catalog_digest,
            category=rule.category, classification=classification, title=rule.title,
            description=rule.description, applicability_basis=applicability_basis,
            evidence=evidence, source_observation_started_at=context.observation_started_at,
            source_observation_completed_at=context.observation_completed_at,
            limitation_codes=_limitations(classification, sections, rule),
            source_truncated=any(_is_truncated(sections[kind]) for kind in rule.required_sections),
            evidence_truncated=evidence_truncated, question=question, checklist_item=checklist,
        ))
    if len(findings) > MAX_FINDINGS or questions > MAX_QUESTIONS or checklist_items > MAX_CHECKLIST_ITEMS or evidence_total > MAX_EVIDENCE_TOTAL:
        raise ValueError("evaluation bounds exceeded")
    partial = context.observation_status is ContextObservationStatus.PARTIAL or any(
        finding.classification in {CompletenessClassification.INDETERMINATE, CompletenessClassification.NOT_DISCLOSED}
        for finding in findings
    )
    limitations: list[LimitationCode] = [LimitationCode.NON_ATOMIC_OBSERVATION]
    if context.observation_status is ContextObservationStatus.PARTIAL:
        limitations.append(LimitationCode.SOURCE_PARTIAL)
    completed = datetime.now(timezone.utc) if now is None else now
    return CompletenessObservationV1(
        started_at=started, completed_at=completed,
        source_observation_started_at=context.observation_started_at,
        source_observation_completed_at=context.observation_completed_at,
        source_observation_status=context.observation_status, catalog=catalog,
        assessment_status=CompletenessObservationStatus.PARTIAL if partial else CompletenessObservationStatus.COMPLETE_WITHIN_BOUNDS,
        limitation_codes=tuple(dict.fromkeys(limitations)), findings=tuple(findings),
    )


def _validate_visible_context(
    context: ProjectContextSuccess,
    request: CompletenessAssessmentRequest,
    *,
    guidance_expanded: bool = False,
) -> _VisibleContextValidation:
    """Validate structure, scope and the accepted purpose-specific input bound."""
    if _validate_context_structure(context) is not _VisibleContextValidation.VALID:
        return _VisibleContextValidation.UNAVAILABLE

    for section in context.sections:
        for item in section.items:
            item_result = _validate_item_scope(item, request)
            if item_result is not _VisibleContextValidation.VALID:
                return item_result
            if type(item) is ExecutionPlanItem:
                for activity in item.activities:
                    activity_result = _validate_project_scope(
                        getattr(activity, "project_id", _MISSING), request.project_id,
                    )
                    if activity_result is not _VisibleContextValidation.VALID:
                        return activity_result
                    workspace_result = _validate_workspace_scope(
                        getattr(activity, "workspace_id", _MISSING), request.workspace_id,
                    )
                    if workspace_result is not _VisibleContextValidation.VALID:
                        return workspace_result
                for milestone in item.milestones:
                    milestone_result = _validate_project_scope(
                        getattr(milestone, "project_id", _MISSING), request.project_id,
                    )
                    if milestone_result is not _VisibleContextValidation.VALID:
                        return milestone_result

    visible_inputs = 0
    for section in context.sections:
        visible_inputs += len(section.items)
        for item in section.items:
            if type(item) is ExecutionPlanItem:
                visible_inputs += len(item.activities) + len(item.milestones)
                if guidance_expanded:
                    visible_inputs += len(item.dependencies)
            elif type(item) is DeliverableItem and item.current_revision is not None:
                visible_inputs += 1
            elif guidance_expanded and type(item) is ProjectControlItem:
                visible_inputs += len(item.impacts)
            if visible_inputs > MAX_VISIBLE_INPUTS:
                return _VisibleContextValidation.UNAVAILABLE
    return _VisibleContextValidation.VALID


def _validate_context_structure(context: object) -> _VisibleContextValidation:
    """Fail closed over the exact PATCH-048 public projection shape."""
    if type(context) is not ProjectContextSuccess or type(context.sections) is not tuple:
        return _VisibleContextValidation.UNAVAILABLE
    if tuple(section.kind for section in context.sections) != CANONICAL_SECTION_ORDER:
        return _VisibleContextValidation.UNAVAILABLE
    for section in context.sections:
        if type(section) is not ProjectContextSection or type(section.kind) is not ProjectContextSectionKind:
            return _VisibleContextValidation.UNAVAILABLE
        if type(section.items) is not tuple:
            return _VisibleContextValidation.UNAVAILABLE
        state = section.state
        if type(state) is SectionAvailable:
            if (
                not section.items
                or type(state.visible_count) is not int
                or state.visible_count != len(section.items)
                or not _valid_truncation(state.truncated)
            ):
                return _VisibleContextValidation.UNAVAILABLE
            item_type = _SECTION_ITEM_TYPES.get(section.kind)
            if item_type is None or any(type(item) is not item_type for item in section.items):
                return _VisibleContextValidation.UNAVAILABLE
            if any(not _valid_item_structure(item) for item in section.items):
                return _VisibleContextValidation.UNAVAILABLE
        elif type(state) is SectionEmpty:
            if section.kind in _NOT_ESTABLISHED_SECTIONS or section.items:
                return _VisibleContextValidation.UNAVAILABLE
        elif type(state) is SectionNotEstablished:
            if section.kind not in _NOT_ESTABLISHED_SECTIONS or section.items:
                return _VisibleContextValidation.UNAVAILABLE
        elif type(state) in {SectionNotDisclosed, SectionUnavailable}:
            if section.items:
                return _VisibleContextValidation.UNAVAILABLE
        else:
            return _VisibleContextValidation.UNAVAILABLE
    return _VisibleContextValidation.VALID


def _valid_truncation(value: object) -> bool:
    if type(value) is not TruncationMetadata or type(value.truncated) is not bool:
        return False
    if value.truncated != (value.continuation is not None):
        return False
    return value.continuation is None or type(value.continuation) is ContinuationMetadata


def _valid_item_structure(item: object) -> bool:
    if not _has_exact_provenance(item):
        return False
    if type(item) is ExecutionPlanItem:
        return (
            _exact_tuple_of(item.activities, ExecutionActivityItem)
            and _exact_tuple_of(item.milestones, ExecutionMilestoneItem)
            and _exact_tuple_of(item.dependencies, ActivityDependencyItem)
            and type(item.progress) is ExecutionProgressItem
        )
    if type(item) is DeliverableItem:
        return item.current_revision is None or type(item.current_revision) is DeliverableRevisionItem
    if type(item) is ProjectControlItem:
        return _exact_tuple_of(item.impacts, ChangeImpactItem)
    if type(item) is EngineeringContextProjection:
        return type(item.payload) in _CONTEXT_PAYLOAD_TYPES
    return True


def _has_exact_provenance(item: object) -> bool:
    return type(getattr(item, "provenance", _MISSING)) is FactProvenance


def _exact_tuple_of(value: object, item_type: type[object]) -> bool:
    return type(value) is tuple and all(type(item) is item_type for item in value)


def _validate_item_scope(
    item: object,
    request: CompletenessAssessmentRequest,
) -> _VisibleContextValidation:
    """Validate declared top-level scope fields without deriving trust from them."""
    fields = getattr(type(item), "model_fields", None)
    if not isinstance(fields, dict):
        return _VisibleContextValidation.UNAVAILABLE
    project_field = fields.get("project_id")
    if project_field is not None:
        project_id = getattr(item, "project_id", _MISSING)
        if project_id is _MISSING:
            return _VisibleContextValidation.UNAVAILABLE
        if project_id is not None:
            project_result = _validate_project_scope(project_id, request.project_id)
            if project_result is not _VisibleContextValidation.VALID:
                return project_result
    workspace_field = fields.get("workspace_id")
    if workspace_field is not None:
        workspace_id = getattr(item, "workspace_id", _MISSING)
        if workspace_id is _MISSING:
            return _VisibleContextValidation.UNAVAILABLE
        workspace_result = _validate_workspace_scope(workspace_id, request.workspace_id)
        if workspace_result is not _VisibleContextValidation.VALID:
            return workspace_result
    return _VisibleContextValidation.VALID


def _validate_project_scope(
    project_id: object,
    trusted_project_id: int,
) -> _VisibleContextValidation:
    if type(project_id) is not int or project_id <= 0:
        return _VisibleContextValidation.UNAVAILABLE
    if project_id != trusted_project_id:
        return _VisibleContextValidation.PROTECTED
    return _VisibleContextValidation.VALID


def _validate_workspace_scope(
    workspace_id: object,
    trusted_workspace_id: int | None,
) -> _VisibleContextValidation:
    if workspace_id is None:
        return _VisibleContextValidation.VALID
    if workspace_id is _MISSING or type(workspace_id) is not int or workspace_id <= 0:
        return _VisibleContextValidation.UNAVAILABLE
    if trusted_workspace_id is not None and workspace_id != trusted_workspace_id:
        return _VisibleContextValidation.PROTECTED
    return _VisibleContextValidation.VALID


class ProjectCompletenessService:
    """Read-only application orchestration around the immutable evaluator."""

    def __init__(
        self,
        observer: ProjectContextObservationPort,
        *,
        clock: Callable[[], datetime] | None = None,
        evaluator: Callable[[ProjectContextSuccess], CompletenessObservationV1] | None = None,
        observation_repository: object | None = None,
        history_authorization: object | None = None,
    ) -> None:
        self._observer = observer
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._evaluator = evaluator or (lambda context: evaluate_project_context(context, now=self._clock()))
        self._observation_repository = observation_repository
        self._history_authorization = history_authorization

    @staticmethod
    def _history_source_digest(context: ProjectContextSuccess) -> str:
        """Exclude read clocks/cursors, not source facts or owner timestamps."""
        def stable(value):
            if isinstance(value, dict):
                return {key: stable(item) for key, item in value.items()
                        if key not in {"observation_started_at", "observation_completed_at",
                                       "observed_at", "continuation"}}
            if isinstance(value, list):
                return [stable(item) for item in value]
            return value

        payload = stable(context.model_dump(mode="json"))
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    def _history_context(self, *, actor: CompletenessActor,
                         request: CompletenessAssessmentRequest,
                         current_user: object) -> ProjectContextSuccess | None:
        if (self._observation_repository is None or self._history_authorization is None
                or current_user is None or getattr(current_user, "id", None) != actor.actor_id):
            return None
        from app.models.engineering_experience_capture_command import EngineeringExperienceCaptureActor
        principal = EngineeringExperienceCaptureActor(actor.actor_id, actor.organization_id)
        if not self._history_authorization.authorize(
            actor=principal, operation="list", project_id=request.project_id,
            workspace_id=None,
        ):
            return None
        if request.workspace_id is not None and not self._history_authorization.authorize(
            actor=principal, operation="list", project_id=request.project_id,
            workspace_id=request.workspace_id,
        ):
            return None
        context_request = ProjectContextRequest(
            scope=ProjectContextScope(project_id=request.project_id, workspace_id=request.workspace_id),
            sections=tuple(ProjectContextSectionRequest(kind=kind, page_size=100)
                           for kind in ProjectContextSectionKind),
        )
        context = self._observer.observe(
            actor=actor, request=context_request, current_user=current_user,
        )
        if (not isinstance(context, ProjectContextSuccess)
                or _validate_visible_context(context, request) is not _VisibleContextValidation.VALID):
            return None
        return context

    @staticmethod
    def _history_row(row) -> dict:
        return {
            "id": row.id, "observation_version": row.observation_version,
            "organization_id": row.organization_id, "project_id": row.project_id,
            "workspace_id": row.workspace_id, "source_cutoff": row.source_cutoff,
            "observed_at": row.observed_at, "method_version": row.method_version,
            "catalog_digest": row.catalog_digest, "source_digest": row.source_digest,
            "assessment_status": row.assessment_status,
            "classifications": tuple(row.classifications_json),
            "limitations": tuple(row.limitations_json),
        }

    def record_authorized_observation(
        self, *, actor: CompletenessActor, request: CompletenessAssessmentRequest,
        current_user: object,
    ) -> dict:
        """Prospective owner command; never reconstructs earlier assessments."""
        try:
            context = self._history_context(actor=actor, request=request, current_user=current_user)
            if context is None:
                return {"outcome": "protected_not_found"}
            observation = self._evaluator(context)
            if len(observation.findings) != MAX_RULES:
                return {"outcome": "unavailable"}
            classifications = [
                {"rule_id": item.rule_id, "category": item.category.value,
                 "classification": item.classification.value}
                for item in observation.findings
            ]
            limitations = tuple(dict.fromkeys(
                [code.value for code in observation.limitation_codes]
                + [code.value for item in observation.findings for code in item.limitation_codes]
            ))
            row = self._observation_repository.record_once({
                "organization_id": actor.organization_id,
                "project_id": request.project_id, "workspace_id": request.workspace_id,
                "actor_id": actor.actor_id, "observation_version": 1,
                "method_version": CATALOG_ID, "catalog_digest": observation.catalog.catalog_digest,
                "source_digest": self._history_source_digest(context),
                "source_cutoff": context.observation_completed_at,
                "observed_at": self._clock(),
                "assessment_status": observation.assessment_status.value,
                "classifications_json": classifications,
                "limitations_json": list(limitations),
            })
            return {"outcome": "success", "observation": self._history_row(row)}
        except Exception:
            return {"outcome": "unavailable"}

    def list_authorized_observation_history(
        self, *, actor: CompletenessActor, request: CompletenessAssessmentRequest,
        current_user: object, window_days: int,
    ) -> dict:
        if window_days not in {7, 30, 90, 180}:
            return {"outcome": "invalid_request"}
        try:
            context = self._history_context(actor=actor, request=request, current_user=current_user)
            if context is None:
                return {"outcome": "protected_not_found"}
            # A currently protected/incomplete source cannot re-disclose older classifications.
            if context.observation_status is not ContextObservationStatus.COMPLETE_WITHIN_BOUNDS:
                return {"outcome": "unavailable"}
            cutoff = context.observation_completed_at
            rows = self._observation_repository.list_history(
                organization_id=actor.organization_id, project_id=request.project_id,
                workspace_id=request.workspace_id, actor_id=actor.actor_id,
                after_cutoff=cutoff - timedelta(days=window_days),
                before_cutoff=cutoff, limit=1001,
            )
            if len(rows) > 1000:
                return {"outcome": "unavailable"}
            return {"outcome": "success", "source_cutoff": cutoff,
                    "observations": tuple(self._history_row(row) for row in rows)}
        except Exception:
            return {"outcome": "unavailable"}

    def evaluate_authorized_observation(
        self,
        *,
        actor: CompletenessActor,
        request: CompletenessAssessmentRequest,
        context: ProjectContextSuccess,
        context_observation_digest: str,
        current_user: object,
    ) -> CompletenessAssessmentResult:
        """Run the existing evaluator over the exact supplied Context, never the observer."""
        if current_user is None or type(actor.actor_id) is not int or actor.actor_id <= 0:
            return CompletenessProtectedNotFound()
        try:
            canonical = json.dumps(
                context.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
            if hashlib.sha256(canonical).hexdigest() != context_observation_digest:
                return CompletenessUnavailable()
            validation = _validate_visible_context(context, request, guidance_expanded=True)
            if validation is _VisibleContextValidation.PROTECTED:
                return CompletenessProtectedNotFound()
            if validation is not _VisibleContextValidation.VALID:
                return CompletenessUnavailable()
            observation = self._evaluator(context)
            if len(observation.findings) != MAX_RULES:
                return CompletenessUnavailable()
            result: CompletenessAssessmentResult
            if observation.assessment_status is CompletenessObservationStatus.PARTIAL:
                result = CompletenessPartialSuccess(observation=observation)
            else:
                result = CompletenessSuccess(observation=observation)
            encoded = json.dumps(
                result.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
            return result if len(encoded) <= MAX_RESPONSE_BYTES else CompletenessUnavailable()
        except Exception:
            return CompletenessUnavailable()

    def assess(
        self,
        *,
        actor: CompletenessActor,
        request: CompletenessAssessmentRequest,
        current_user: object,
    ) -> CompletenessAssessmentResult:
        try:
            context_request = ProjectContextRequest(
                scope=ProjectContextScope(
                    project_id=request.project_id,
                    workspace_id=request.workspace_id,
                ),
                sections=tuple(
                    ProjectContextSectionRequest(kind=kind, page_size=100)
                    for kind in ProjectContextSectionKind
                ),
            )
        except Exception:
            return CompletenessInvalidRequest()
        try:
            result = self._observer.observe(
                actor=actor,
                request=context_request,
                current_user=current_user,
            )
        except Exception:
            return CompletenessUnavailable()
        if isinstance(result, ProjectContextProtectedNotFound):
            return CompletenessProtectedNotFound()
        if isinstance(result, ProjectContextInvalidRequest):
            return CompletenessInvalidRequest()
        if isinstance(result, ProjectContextUnavailable):
            return CompletenessUnavailable()
        if not isinstance(result, ProjectContextSuccess):
            return CompletenessUnavailable()
        try:
            validation = _validate_visible_context(result, request)
            if validation is _VisibleContextValidation.PROTECTED:
                return CompletenessProtectedNotFound()
            if validation is not _VisibleContextValidation.VALID:
                return CompletenessUnavailable()
            observation = self._evaluator(result)
            if len(observation.findings) != MAX_RULES:
                return CompletenessUnavailable()
            outward_result: CompletenessAssessmentResult
            if observation.assessment_status is CompletenessObservationStatus.PARTIAL:
                outward_result = CompletenessPartialSuccess(observation=observation)
            else:
                outward_result = CompletenessSuccess(observation=observation)
            encoded = json.dumps(
                outward_result.model_dump(mode="json"),
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            if len(encoded) > MAX_RESPONSE_BYTES:
                return CompletenessUnavailable()
            return outward_result
        except Exception:
            return CompletenessUnavailable()
