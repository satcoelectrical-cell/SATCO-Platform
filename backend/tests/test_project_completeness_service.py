from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.schemas.project_completeness import (
    CompletenessClassification,
    CompletenessObservationStatus,
)
from app.schemas.project_context import (
    AuthorityClassification, ContextObservationStatus, DeliverableItem,
    DeliverableRevisionItem, EngineeringContextProjection, EvidenceItem,
    ExecutionPlanItem, ExecutionProgressItem, FactProvenance, ProjectBasisItem,
    ProjectContextSection, ProjectContextSectionKind, ProjectContextSuccess,
    SectionAvailable, SectionEmpty, SectionNotDisclosed, SectionUnavailable,
    TemporalClassification, TruncationMetadata,
)
from app.services.project_completeness_service import evaluate_project_context
from app.services.project_completeness_service import ProjectCompletenessService
from app.ports.project_completeness import CompletenessActor, CompletenessAssessmentRequest
import app.services.project_completeness_service as completeness_module


NOW = datetime(2026, 8, 26, tzinfo=timezone.utc)
PROVENANCE = FactProvenance(owner_kind="project_foundation", selector="basis-1", observed_at=NOW, authority_class=AuthorityClassification.HUMAN_AUTHORITATIVE, temporal_class=TemporalClassification.CURRENT)


def _available(kind, items=(), truncated=False):
    return ProjectContextSection(kind=kind, state=SectionAvailable(visible_count=len(items), truncated=TruncationMetadata(truncated=truncated, continuation=None if not truncated else {"continuation": "token", "last_evaluated_key": "k"}), observed_at=NOW), items=tuple(items))


def _basis(**changes):
    values = dict(selector="basis-1", version=1, standing="active", provenance=PROVENANCE, project_id=1,
                  foundation_established=True, purpose="Purpose", engineering_basis="Basis", current_stage="verification",
                  ordered_in_scope=("scope",), completion_basis="completion", required_project_inputs=("input",))
    values.update(changes)
    return ProjectBasisItem(**values)


def _plan(**changes):
    values = dict(selector="plan-1", version=1, standing="active", provenance=PROVENANCE,
                  plan_id=UUID("00000000-0000-4000-8000-000000000001"), project_id=1, plan_version=1,
                  activities=(), milestones=(), progress=ExecutionProgressItem(numerator=0, denominator=1, percent=0))
    values.update(changes)
    return ExecutionPlanItem(**values)


def _deliverable(current=True, representation=True):
    revision = DeliverableRevisionItem(revision_id=UUID("00000000-0000-4000-8000-000000000003"), deliverable_id=UUID("00000000-0000-4000-8000-000000000002"), sequence=1, standing="active", version=1, representation_available=representation) if current else None
    return DeliverableItem(selector="deliverable-1", version=1, standing="active", provenance=PROVENANCE,
                           deliverable_id=UUID("00000000-0000-4000-8000-000000000002"), project_id=1, code="D-1", title="Deliverable", discipline="electrical", deliverable_type="study", external_authority=False, current_revision=revision)


def _context(*, basis_section=None, execution=(), deliverables=(), engineering_context=(), evidence=(), unavailable=(), protected=(), truncated=()):
    values = {
        ProjectContextSectionKind.PROJECT_BASIS: basis_section or _available(ProjectContextSectionKind.PROJECT_BASIS, (_basis(),)),
        ProjectContextSectionKind.EXECUTION: _available(ProjectContextSectionKind.EXECUTION, execution, ProjectContextSectionKind.EXECUTION in truncated),
        ProjectContextSectionKind.DELIVERABLES: _available(ProjectContextSectionKind.DELIVERABLES, deliverables, ProjectContextSectionKind.DELIVERABLES in truncated),
        ProjectContextSectionKind.PROJECT_CONTROLS: _available(ProjectContextSectionKind.PROJECT_CONTROLS),
        ProjectContextSectionKind.ENGINEERING_CONTEXT: _available(ProjectContextSectionKind.ENGINEERING_CONTEXT, engineering_context),
        ProjectContextSectionKind.ENGINEERING_OBJECTS: _available(ProjectContextSectionKind.ENGINEERING_OBJECTS),
        ProjectContextSectionKind.EVIDENCE: _available(ProjectContextSectionKind.EVIDENCE, evidence),
        ProjectContextSectionKind.SUPPORTING_FILES: _available(ProjectContextSectionKind.SUPPORTING_FILES),
        ProjectContextSectionKind.TECHNICAL_REPORTS: _available(ProjectContextSectionKind.TECHNICAL_REPORTS),
        ProjectContextSectionKind.ORGANIZATIONAL_MEMORY: _available(ProjectContextSectionKind.ORGANIZATIONAL_MEMORY),
    }
    for kind in unavailable:
        values[kind] = ProjectContextSection(kind=kind, state=SectionUnavailable(), items=())
    for kind in protected:
        values[kind] = ProjectContextSection(kind=kind, state=SectionNotDisclosed(), items=())
    return ProjectContextSuccess(observation_started_at=NOW, observation_completed_at=NOW, observation_status=ContextObservationStatus.COMPLETE_WITHIN_BOUNDS, sections=tuple(values[kind] for kind in ProjectContextSectionKind))


def _finding(observation, rule_id):
    return next(item for item in observation.findings if item.rule_id == rule_id)


def test_complete_context_evaluates_deterministically_with_fourteen_findings():
    context = _context(execution=(_plan(),), deliverables=(_deliverable(),), engineering_context=(EngineeringContextProjection(context_id=1, context_key="k", project_id=1, kind="fact", authority="human", lifecycle="current", version=1, payload={"payload_kind": "absent"}, created_at=NOW, updated_at=NOW, provenance=PROVENANCE),), evidence=(EvidenceItem(selector="evidence-1", version=1, standing="active", provenance=PROVENANCE, evidence_id=UUID("00000000-0000-4000-8000-000000000004"), project_id=1, evidence_kind="verification", created_at=NOW, updated_at=NOW),))
    first = evaluate_project_context(context, now=NOW)
    second = evaluate_project_context(context, now=NOW)
    assert first == second
    assert len(first.findings) == 14
    assert tuple(item.rule_id for item in first.findings) == tuple(sorted(item.rule_id for item in first.findings))
    assert len([item for item in first.findings if item.question]) <= 14
    assert len([item for item in first.findings if item.checklist_item]) <= 14


@pytest.mark.parametrize("change,rule_id", [
    ({"engineering_basis": None}, "pc.project_basis.engineering_basis"),
    ({"purpose": ""}, "pc.project_basis.purpose"),
    ({"completion_basis": None}, "pc.project_completion.basis"),
    ({"foundation_established": False}, "pc.project_foundation.established"),
    ({"required_project_inputs": ()}, "pc.project_inputs.declared"),
    ({"ordered_in_scope": ()}, "pc.project_scope.in_scope"),
])
def test_project_basis_rules_produce_safe_missing_for_complete_visible_absence(change, rule_id):
    observation = evaluate_project_context(_context(basis_section=_available(ProjectContextSectionKind.PROJECT_BASIS, (_basis(**change),))), now=NOW)
    assert _finding(observation, rule_id).classification is CompletenessClassification.MISSING


def test_protected_unavailable_and_truncated_never_become_missing():
    protected = evaluate_project_context(_context(protected=(ProjectContextSectionKind.PROJECT_BASIS,)), now=NOW)
    assert _finding(protected, "pc.project_basis.purpose").classification is CompletenessClassification.NOT_DISCLOSED
    unavailable = evaluate_project_context(_context(unavailable=(ProjectContextSectionKind.PROJECT_BASIS,)), now=NOW)
    assert _finding(unavailable, "pc.project_basis.purpose").classification is CompletenessClassification.INDETERMINATE
    truncated = evaluate_project_context(_context(basis_section=_available(ProjectContextSectionKind.PROJECT_BASIS, (_basis(purpose=""),), truncated=True)), now=NOW)
    assert _finding(truncated, "pc.project_basis.purpose").classification is CompletenessClassification.INDETERMINATE


def test_conditional_execution_and_deliverable_rules_have_present_missing_and_not_applicable_vectors():
    base = _context(basis_section=_available(ProjectContextSectionKind.PROJECT_BASIS, (_basis(current_stage="definition"),)))
    assert _finding(evaluate_project_context(base, now=NOW), "pc.execution.plan_established").classification is CompletenessClassification.NOT_APPLICABLE
    missing_plan = _context(basis_section=_available(ProjectContextSectionKind.PROJECT_BASIS, (_basis(current_stage="preparation"),)))
    assert _finding(evaluate_project_context(missing_plan, now=NOW), "pc.execution.plan_established").classification is CompletenessClassification.MISSING
    plan_without_activities = _context(basis_section=_available(ProjectContextSectionKind.PROJECT_BASIS, (_basis(current_stage="preparation"),)), execution=(_plan(),))
    assert _finding(evaluate_project_context(plan_without_activities, now=NOW), "pc.execution.activities_defined").classification is CompletenessClassification.MISSING
    deliverable_missing_revision = _context(basis_section=_available(ProjectContextSectionKind.PROJECT_BASIS, (_basis(current_stage="execution"),)), deliverables=(_deliverable(current=False),))
    assert _finding(evaluate_project_context(deliverable_missing_revision, now=NOW), "pc.deliverables.current_revision").classification is CompletenessClassification.MISSING
    representation_missing = _context(basis_section=_available(ProjectContextSectionKind.PROJECT_BASIS, (_basis(current_stage="verification"),)), deliverables=(_deliverable(representation=False),))
    assert _finding(evaluate_project_context(representation_missing, now=NOW), "pc.deliverables.representation_available").classification is CompletenessClassification.MISSING


def test_engineering_context_and_verification_evidence_rules_cover_present_missing_and_protected():
    basis = _available(ProjectContextSectionKind.PROJECT_BASIS, (_basis(current_stage="verification"),))
    missing = evaluate_project_context(_context(basis_section=basis), now=NOW)
    assert _finding(missing, "pc.engineering_context.established").classification is CompletenessClassification.MISSING
    assert _finding(missing, "pc.verification.evidence_established").classification is CompletenessClassification.MISSING
    protected = evaluate_project_context(_context(basis_section=basis, protected=(ProjectContextSectionKind.EVIDENCE,)), now=NOW)
    assert _finding(protected, "pc.verification.evidence_established").classification is CompletenessClassification.NOT_DISCLOSED


def test_evidence_is_bounded_safe_deduplicated_and_questions_are_advisory_only():
    observation = evaluate_project_context(_context(), now=NOW)
    for finding in observation.findings:
        assert len(finding.evidence) <= 4
        assert all(reference.reference_kind in {"visible_fact", "visible_section_state"} for reference in finding.evidence)
        assert "human_id" not in str(finding.evidence).lower()
        assert "owner_id" not in str(finding.evidence).lower()
        if finding.question:
            assert finding.question.advisory is True
            assert finding.checklist_item is not None
            assert "recommend" not in finding.question.text.lower()


class _Observer:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def observe(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


class _User:
    id = 1


def test_application_assessment_uses_one_fresh_all_ten_section_observation_and_evaluates_once():
    observer = _Observer(_context())
    evaluations = []
    service = ProjectCompletenessService(
        observer,
        clock=lambda: NOW,
        evaluator=lambda context: evaluations.append(context) or evaluate_project_context(context, now=NOW),
    )
    result = service.assess(
        actor=CompletenessActor(1, UUID("00000000-0000-0000-0000-000000000001")),
        request=CompletenessAssessmentRequest(project_id=1, workspace_id=2),
        current_user=_User(),
    )
    assert result.status in {"success", "partial_success"}
    assert len(observer.calls) == len(evaluations) == 1
    context_request = observer.calls[0]["request"]
    assert tuple(section.kind for section in context_request.sections) == tuple(ProjectContextSectionKind)
    assert all(section.page_size == 100 and section.continuation is None for section in context_request.sections)
    assert len(result.observation.findings) == 14


def test_complete_outward_closed_result_not_only_source_observation_is_byte_bounded():
    source = _context()
    source_bytes = len(__import__("json").dumps(source.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode())
    baseline = evaluate_project_context(source, now=NOW)
    assert source_bytes < completeness_module.MAX_RESPONSE_BYTES

    # This is a defensive boundary vector: source remains bounded while a
    # malformed/expanded evaluator result would exceed the exact final limit.
    huge_finding = baseline.findings[0].model_construct(
        **{**baseline.findings[0].model_dump(), "description": "x" * completeness_module.MAX_RESPONSE_BYTES}
    )
    expanded = baseline.model_construct(
        **{**baseline.model_dump(), "findings": (huge_finding,) + baseline.findings[1:]}
    )
    observer = _Observer(source)
    evaluations = []
    service = ProjectCompletenessService(
        observer,
        clock=lambda: NOW,
        evaluator=lambda context: evaluations.append(context) or expanded,
    )
    result = service.assess(
        actor=CompletenessActor(1, UUID("00000000-0000-0000-0000-000000000001")),
        request=CompletenessAssessmentRequest(project_id=1),
        current_user=_User(),
    )
    assert result.model_dump() == {"status": "unavailable"}
    assert len(observer.calls) == len(evaluations) == 1


def test_canonical_outward_boundary_accepts_result_at_or_below_limit(monkeypatch):
    source = _context()
    observation = evaluate_project_context(source, now=NOW)
    result_type = (
        completeness_module.CompletenessPartialSuccess
        if observation.assessment_status is CompletenessObservationStatus.PARTIAL
        else completeness_module.CompletenessSuccess
    )
    success = result_type(observation=observation)
    exact_size = len(__import__("json").dumps(success.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode())
    monkeypatch.setattr(completeness_module, "MAX_RESPONSE_BYTES", exact_size)
    result = ProjectCompletenessService(
        _Observer(source),
        clock=lambda: NOW,
        evaluator=lambda context: observation,
    ).assess(
        actor=CompletenessActor(1, UUID("00000000-0000-0000-0000-000000000001")),
        request=CompletenessAssessmentRequest(project_id=1),
        current_user=_User(),
    )
    assert result.status == success.status
