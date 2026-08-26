"""Pure deterministic evaluator for PATCH-049 Batch 1.

This module deliberately performs no I/O, authorization, transport, EKG,
database, persistence or model/provider work. Batch 2 supplies fresh public
Project Context data to ``evaluate_project_context``.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
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
    ContextObservationStatus,
    CANONICAL_SECTION_ORDER,
    DeliverableItem,
    EngineeringContextProjection,
    EvidenceItem,
    ExecutionPlanItem,
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
    SourceAvailability,
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
) -> bool:
    """Validate the closed ten-section, at-most-1,000-item public input."""
    if tuple(section.kind for section in context.sections) != CANONICAL_SECTION_ORDER:
        return False
    visible_inputs = 0
    for section in context.sections:
        visible_inputs += len(section.items)
        if visible_inputs > MAX_VISIBLE_INPUTS:
            return False
        for item in section.items:
            if getattr(item, "project_id", request.project_id) != request.project_id:
                return False
            workspace_id = getattr(item, "workspace_id", None)
            if request.workspace_id is not None and workspace_id not in {
                None,
                request.workspace_id,
            }:
                return False
    return True


class ProjectCompletenessService:
    """Read-only application orchestration around the immutable evaluator."""

    def __init__(
        self,
        observer: ProjectContextObservationPort,
        *,
        clock: Callable[[], datetime] | None = None,
        evaluator: Callable[[ProjectContextSuccess], CompletenessObservationV1] | None = None,
    ) -> None:
        self._observer = observer
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._evaluator = evaluator or (lambda context: evaluate_project_context(context, now=self._clock()))

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
            if not _validate_visible_context(result, request):
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
