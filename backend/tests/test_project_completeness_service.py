from datetime import datetime, timedelta, timezone
import hashlib
import json
from uuid import UUID
from types import SimpleNamespace

import pytest

from app.schemas.project_completeness import (
    CompletenessClassification,
    CompletenessObservationStatus,
)
from app.schemas.project_context import (
    ActivityDependencyItem, AuthorityClassification, ChangeImpactItem,
    ContextObservationStatus, DeliverableItem, DeliverableRevisionItem,
    EngineeringContextProjection, EngineeringObjectItem, EvidenceItem, ExecutionActivityItem,
    ExecutionMilestoneItem, ExecutionPlanItem, ExecutionProgressItem,
    FactProvenance, OrganizationalMemoryItem, ProjectBasisItem, ProjectContextItem, ProjectControlItem,
    ProjectContextSection, ProjectContextSectionKind, ProjectContextSuccess,
    SectionAvailable, SectionEmpty, SectionNotDisclosed, SectionNotEstablished, SectionUnavailable,
    SupportingFileItem, TechnicalReportItem, TemporalClassification, TruncationMetadata,
)
from app.services.project_completeness_service import evaluate_project_context
from app.services.project_completeness_service import ProjectCompletenessService
from app.ports.project_completeness import CompletenessActor, CompletenessAssessmentRequest
import app.services.project_completeness_service as completeness_module


NOW = datetime(2026, 8, 26, tzinfo=timezone.utc)
PROVENANCE = FactProvenance(owner_kind="project_foundation", selector="basis-1", observed_at=NOW, authority_class=AuthorityClassification.HUMAN_AUTHORITATIVE, temporal_class=TemporalClassification.CURRENT)


def _available(kind, items=(), truncated=False):
    if not items:
        if kind in {ProjectContextSectionKind.PROJECT_BASIS, ProjectContextSectionKind.EXECUTION}:
            return ProjectContextSection(kind=kind, state=SectionNotEstablished())
        return ProjectContextSection(kind=kind, state=SectionEmpty())
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


def _activity() -> ExecutionActivityItem:
    return ExecutionActivityItem(
        activity_id=UUID("00000000-0000-4000-8000-000000000011"),
        plan_id=UUID("00000000-0000-4000-8000-000000000001"), project_id=1,
        title="Activity", ordinal=1, standing="active", version=1, blocker_present=False,
    )


def _milestone() -> ExecutionMilestoneItem:
    return ExecutionMilestoneItem(
        milestone_id=UUID("00000000-0000-4000-8000-000000000012"),
        plan_id=UUID("00000000-0000-4000-8000-000000000001"), project_id=1,
        title="Milestone", ordinal=1, standing="active",
    )


def _dependency() -> ActivityDependencyItem:
    return ActivityDependencyItem(
        predecessor_activity_id=UUID("00000000-0000-4000-8000-000000000013"),
        dependent_activity_id=UUID("00000000-0000-4000-8000-000000000014"),
    )


def _control(*, impacts=()) -> ProjectControlItem:
    return ProjectControlItem(
        selector="control-1", provenance=PROVENANCE, item_kind="project_control:change",
        control_id=UUID("00000000-0000-4000-8000-000000000015"),
        version=1, standing="active", project_id=1,
        temporal_class=TemporalClassification.CURRENT, predecessor_present=False,
        impacts=tuple(impacts),
    )


def _impact() -> ChangeImpactItem:
    return ChangeImpactItem(
        impact_id=UUID("00000000-0000-4000-8000-000000000016"),
        change_id=UUID("00000000-0000-4000-8000-000000000015"),
        standing="active", impact_class="potential",
    )


def _deliverable(current=True, representation=True):
    revision = DeliverableRevisionItem(revision_id=UUID("00000000-0000-4000-8000-000000000003"), deliverable_id=UUID("00000000-0000-4000-8000-000000000002"), sequence=1, standing="active", version=1, representation_available=representation) if current else None
    return DeliverableItem(selector="deliverable-1", version=1, standing="active", provenance=PROVENANCE,
                           deliverable_id=UUID("00000000-0000-4000-8000-000000000002"), project_id=1, code="D-1", title="Deliverable", discipline="electrical", deliverable_type="study", external_authority=False, current_revision=revision)


def _engineering_context() -> EngineeringContextProjection:
    return EngineeringContextProjection(
        context_id=1, context_key="context-1", project_id=1, kind="fact", authority="human",
        lifecycle="current", version=1, payload={"payload_kind": "absent"},
        created_at=NOW, updated_at=NOW, provenance=PROVENANCE,
    )


def _engineering_object() -> EngineeringObjectItem:
    return EngineeringObjectItem(
        selector="object-1", version=1, standing="active", provenance=PROVENANCE,
        object_id=UUID("00000000-0000-4000-8000-000000000021"), project_id=1,
        organization_id=UUID("00000000-0000-0000-0000-000000000001"), family="automation",
        discipline="electrical", object_type="plc", lifecycle="current",
        authority_standing="approved", created_at=NOW, updated_at=NOW,
    )


def _supporting_file() -> SupportingFileItem:
    return SupportingFileItem(
        selector="file-1", version=1, standing="active", provenance=PROVENANCE,
        asset_id=UUID("00000000-0000-4000-8000-000000000022"), project_id=1,
        filename="evidence.pdf", media_type="application/pdf", byte_size=1,
        lifecycle="current", created_at=NOW, updated_at=NOW,
    )


def _technical_report() -> TechnicalReportItem:
    return TechnicalReportItem(
        selector="report-1", version=1, standing="accepted", provenance=PROVENANCE,
        report_id=UUID("00000000-0000-4000-8000-000000000023"), project_id=1,
        workspace_id=1, report_type="verification", accepted_version_id=1,
        accepted_digest="a" * 64, accepted_at=NOW,
    )


def _organizational_memory() -> OrganizationalMemoryItem:
    return OrganizationalMemoryItem(
        selector="memory-1", version=1, standing="admitted", provenance=PROVENANCE,
        memory_id=UUID("00000000-0000-4000-8000-000000000024"), project_id=1,
        workspace_id=1, limitations_present=False, admitted_at=NOW,
    )


def _matrix_item(kind: ProjectContextSectionKind):
    return {
        ProjectContextSectionKind.PROJECT_BASIS: _basis(),
        ProjectContextSectionKind.EXECUTION: _plan(),
        ProjectContextSectionKind.DELIVERABLES: _deliverable(),
        ProjectContextSectionKind.PROJECT_CONTROLS: _control(),
        ProjectContextSectionKind.ENGINEERING_CONTEXT: _engineering_context(),
        ProjectContextSectionKind.ENGINEERING_OBJECTS: _engineering_object(),
        ProjectContextSectionKind.EVIDENCE: EvidenceItem(
            selector="evidence-1", version=1, standing="active", provenance=PROVENANCE,
            evidence_id=UUID("00000000-0000-4000-8000-000000000025"), project_id=1,
            evidence_kind="verification", created_at=NOW, updated_at=NOW,
        ),
        ProjectContextSectionKind.SUPPORTING_FILES: _supporting_file(),
        ProjectContextSectionKind.TECHNICAL_REPORTS: _technical_report(),
        ProjectContextSectionKind.ORGANIZATIONAL_MEMORY: _organizational_memory(),
    }[kind]


def _matrix_context(*, replacements=None) -> ProjectContextSuccess:
    replacements = replacements or {}
    sections = []
    for kind in ProjectContextSectionKind:
        items = tuple(replacements.get(kind, (_matrix_item(kind),)))
        sections.append(ProjectContextSection.model_construct(
            kind=kind,
            state=SectionAvailable.model_construct(
                visible_count=len(items), observed_at=NOW,
                truncated=TruncationMetadata(truncated=False),
            ),
            items=items,
        ))
    return ProjectContextSuccess.model_construct(
        status="success", observation_started_at=NOW, observation_completed_at=NOW,
        observation_status=ContextObservationStatus.COMPLETE_WITHIN_BOUNDS,
        sections=tuple(sections),
    )


def _matrix_single_item_context(kind: ProjectContextSectionKind, item: object) -> ProjectContextSuccess:
    sections = []
    for section_kind in ProjectContextSectionKind:
        if section_kind is kind:
            sections.append(ProjectContextSection.model_construct(
                kind=section_kind,
                state=SectionAvailable.model_construct(
                    visible_count=1, observed_at=NOW,
                    truncated=TruncationMetadata(truncated=False),
                ),
                items=(item,),
            ))
        else:
            sections.append(ProjectContextSection(
                kind=section_kind,
                state=SectionNotEstablished() if section_kind in {
                    ProjectContextSectionKind.PROJECT_BASIS,
                    ProjectContextSectionKind.EXECUTION,
                } else SectionEmpty(),
            ))
    return ProjectContextSuccess.model_construct(
        status="success", observation_started_at=NOW, observation_completed_at=NOW,
        observation_status=ContextObservationStatus.COMPLETE_WITHIN_BOUNDS,
        sections=tuple(sections),
    )


def _context(*, basis_section=None, execution=(), deliverables=(), engineering_context=(), evidence=(), unavailable=(), protected=(), truncated=()):
    execution_items = execution or ((_plan(),) if ProjectContextSectionKind.EXECUTION in truncated else ())
    values = {
        ProjectContextSectionKind.PROJECT_BASIS: basis_section or _available(ProjectContextSectionKind.PROJECT_BASIS, (_basis(),)),
        ProjectContextSectionKind.EXECUTION: _available(ProjectContextSectionKind.EXECUTION, execution_items, ProjectContextSectionKind.EXECUTION in truncated),
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
    states = tuple(values[kind].state for kind in ProjectContextSectionKind)
    partial = any(
        type(state) in {SectionNotDisclosed, SectionUnavailable}
        or (type(state) is SectionAvailable and state.truncated.truncated)
        for state in states
    )
    return ProjectContextSuccess(observation_started_at=NOW, observation_completed_at=NOW, observation_status=ContextObservationStatus.PARTIAL if partial else ContextObservationStatus.COMPLETE_WITHIN_BOUNDS, sections=tuple(values[kind] for kind in ProjectContextSectionKind))


def _bound_context(*, top_level=0, activities=0, milestones=0, dependencies=0, revisions=0, impacts=0):
    """Construct typed boundary vectors; model_construct permits deliberate source-bound overflow."""
    values = {
        kind: ProjectContextSection(
            kind=kind,
            state=SectionNotEstablished() if kind in {
                ProjectContextSectionKind.PROJECT_BASIS,
                ProjectContextSectionKind.EXECUTION,
            } else SectionEmpty(),
        )
        for kind in ProjectContextSectionKind
    }

    def visible_state(count):
        return SectionAvailable.model_construct(
            visible_count=count, observed_at=NOW, truncated=TruncationMetadata(truncated=False),
        )

    execution = [_plan() for _ in range(top_level)]
    if activities or milestones or dependencies:
        execution.append(_plan(
            activities=(_activity(),) * activities,
            milestones=(_milestone(),) * milestones,
            dependencies=(_dependency(),) * dependencies,
        ))
    if execution:
        values[ProjectContextSectionKind.EXECUTION] = ProjectContextSection.model_construct(
            kind=ProjectContextSectionKind.EXECUTION,
            state=visible_state(len(execution)),
            items=tuple(execution),
        )
    if revisions:
        deliverables = tuple(_deliverable() for _ in range(revisions))
        values[ProjectContextSectionKind.DELIVERABLES] = ProjectContextSection.model_construct(
            kind=ProjectContextSectionKind.DELIVERABLES,
            state=visible_state(len(deliverables)),
            items=deliverables,
        )
    if impacts:
        controls = (_control(impacts=(_impact(),) * impacts),)
        values[ProjectContextSectionKind.PROJECT_CONTROLS] = ProjectContextSection.model_construct(
            kind=ProjectContextSectionKind.PROJECT_CONTROLS,
            state=visible_state(len(controls)),
            items=controls,
        )
    return ProjectContextSuccess.model_construct(
        status="success", observation_started_at=NOW, observation_completed_at=NOW,
        observation_status=ContextObservationStatus.COMPLETE_WITHIN_BOUNDS,
        sections=tuple(values[kind] for kind in ProjectContextSectionKind),
    )


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


class _ObservationMemory:
    def __init__(self):
        self.rows = []
        self.reads = 0

    def record_once(self, values):
        for row in self.rows:
            if (row.organization_id, row.project_id, row.workspace_id, row.actor_id,
                    row.method_version, row.catalog_digest, row.source_digest) == (
                    values["organization_id"], values["project_id"], values["workspace_id"],
                    values["actor_id"], values["method_version"], values["catalog_digest"],
                    values["source_digest"]):
                return row
        row = SimpleNamespace(id=UUID(int=len(self.rows) + 1), **values)
        self.rows.append(row)
        return row

    def list_history(self, *, organization_id, project_id, workspace_id, actor_id,
                     after_cutoff, before_cutoff, limit):
        self.reads += 1
        return sorted((row for row in self.rows
                       if row.organization_id == organization_id and row.project_id == project_id
                       and row.workspace_id == workspace_id and row.actor_id == actor_id
                       and after_cutoff <= row.source_cutoff <= before_cutoff),
                      key=lambda row: (row.source_cutoff, row.id))[:limit]


class _HistoryPolicy:
    def __init__(self, allowed=True): self.allowed = allowed
    def authorize(self, **_kwargs): return self.allowed


def test_owner_observation_history_is_prospective_deduplicated_and_score_free():
    actor = CompletenessActor(1, UUID("00000000-0000-0000-0000-000000000001"))
    request = CompletenessAssessmentRequest(project_id=1)
    repository = _ObservationMemory()
    observer = _Observer(_context())
    owner = ProjectCompletenessService(
        observer, clock=lambda: NOW + timedelta(days=2),
        observation_repository=repository, history_authorization=_HistoryPolicy(),
    )
    first = owner.record_authorized_observation(actor=actor, request=request, current_user=_User())
    assert first["outcome"] == "success" and first["observation"]["observation_version"] == 1
    assert first["observation"]["method_version"] == "project_completeness.v1"
    assert len(first["observation"]["classifications"]) == 14
    assert "score" not in first["observation"] and "ratio" not in first["observation"]
    assert len(repository.rows) == 1  # No pre-existing history was manufactured.

    observer.result = observer.result.model_copy(update={
        "observation_started_at": NOW + timedelta(hours=1),
        "observation_completed_at": NOW + timedelta(hours=1),
    })
    duplicate = owner.record_authorized_observation(actor=actor, request=request, current_user=_User())
    assert duplicate["observation"]["id"] == first["observation"]["id"]
    assert len(repository.rows) == 1

    changed = _context(basis_section=_available(
        ProjectContextSectionKind.PROJECT_BASIS, (_basis(purpose=None, version=2),)
    )).model_copy(update={
        "observation_started_at": NOW + timedelta(days=1),
        "observation_completed_at": NOW + timedelta(days=1),
    })
    observer.result = changed
    second = owner.record_authorized_observation(actor=actor, request=request, current_user=_User())
    assert second["outcome"] == "success" and second["observation"]["id"] != first["observation"]["id"]
    assert second["observation"]["source_digest"] != first["observation"]["source_digest"]
    history = owner.list_authorized_observation_history(
        actor=actor, request=request, current_user=_User(), window_days=7,
    )
    assert history["outcome"] == "success"
    assert [row["id"] for row in history["observations"]] == [first["observation"]["id"], second["observation"]["id"]]


def test_owner_history_denies_before_repository_and_suppresses_current_partial_source():
    actor = CompletenessActor(1, UUID("00000000-0000-0000-0000-000000000001"))
    request = CompletenessAssessmentRequest(project_id=1)
    repository = _ObservationMemory()
    policy = _HistoryPolicy(False)
    observer = _Observer(_context())
    owner = ProjectCompletenessService(observer, clock=lambda: NOW,
                                       observation_repository=repository,
                                       history_authorization=policy)
    denied = owner.list_authorized_observation_history(
        actor=actor, request=request, current_user=_User(), window_days=30,
    )
    assert denied == {"outcome": "protected_not_found"}
    assert repository.reads == 0 and observer.calls == []
    policy.allowed = True
    observer.result = _context(protected=(ProjectContextSectionKind.EVIDENCE,))
    result = owner.record_authorized_observation(
        actor=actor, request=request, current_user=_User(),
    )
    assert result["outcome"] == "success"
    assert "source_not_disclosed" in result["observation"]["limitations"]
    history = owner.list_authorized_observation_history(
        actor=actor, request=request, current_user=_User(), window_days=30,
    )
    assert history == {"outcome": "unavailable"} and repository.reads == 0


@pytest.mark.parametrize(
    ("label", "context", "accepted"),
    (
        ("999 top-level", _bound_context(top_level=999), True),
        ("1000 top-level", _bound_context(top_level=1000), True),
        ("1001 top-level", _bound_context(top_level=1001), False),
        ("activities", _bound_context(top_level=800, activities=200), False),
        ("milestones", _bound_context(top_level=950, milestones=50), False),
        ("current revisions", _bound_context(top_level=499, revisions=251), False),
        ("dependencies excluded", _bound_context(top_level=500, dependencies=500), True),
        ("impacts excluded", _bound_context(top_level=900, impacts=100), True),
        ("mixed parents and children", _bound_context(top_level=996, activities=2, milestones=2), False),
    ),
)
def test_patch049_recursive_visible_input_limit_has_exact_domain(label, context, accepted):
    evaluations = []
    service = ProjectCompletenessService(
        _Observer(context), clock=lambda: NOW,
        evaluator=lambda value: evaluations.append(value) or evaluate_project_context(_context(), now=NOW),
    )
    result = service.assess(
        actor=CompletenessActor(1, UUID("00000000-0000-0000-0000-000000000001")),
        request=CompletenessAssessmentRequest(project_id=1), current_user=_User(),
    )
    if accepted:
        assert result.status in {"success", "partial_success"}, label
        assert evaluations == [context]
    else:
        assert result.model_dump() == {"status": "unavailable"}, label
        assert evaluations == []


@pytest.mark.parametrize(
    ("label", "context", "accepted"),
    (
        ("999 expanded", _bound_context(top_level=999), True),
        ("1000 expanded", _bound_context(top_level=1000), True),
        ("1001 expanded", _bound_context(top_level=1001), False),
        ("dependencies included", _bound_context(top_level=500, dependencies=500), False),
        ("impacts included", _bound_context(top_level=900, impacts=100), False),
    ),
)
def test_patch050_same_observation_uses_expanded_visible_input_limit(label, context, accepted):
    import hashlib
    import json

    evaluations = []
    digest = hashlib.sha256(json.dumps(context.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    service = ProjectCompletenessService(
        _Observer(None), clock=lambda: NOW,
        evaluator=lambda value: evaluations.append(value) or evaluate_project_context(_context(), now=NOW),
    )
    result = service.evaluate_authorized_observation(
        actor=CompletenessActor(1, UUID("00000000-0000-0000-0000-000000000001")),
        request=CompletenessAssessmentRequest(project_id=1), context=context,
        context_observation_digest=digest, current_user=_User(),
    )
    if accepted:
        assert result.status in {"success", "partial_success"}, label
        assert evaluations == [context]
    else:
        assert result.model_dump() == {"status": "unavailable"}, label
        assert evaluations == []


def test_partial_and_truncated_context_at_or_below_limit_remain_evaluable():
    partial = _context().model_copy(update={"observation_status": ContextObservationStatus.PARTIAL})
    truncated = _context(truncated=(ProjectContextSectionKind.EXECUTION,))
    for context in (partial, truncated):
        result = ProjectCompletenessService(_Observer(None), clock=lambda: NOW).evaluate_authorized_observation(
            actor=CompletenessActor(1, UUID("00000000-0000-0000-0000-000000000001")),
            request=CompletenessAssessmentRequest(project_id=1), context=context,
            context_observation_digest=__import__("hashlib").sha256(__import__("json").dumps(context.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            current_user=_User(),
        )
        assert result.status == "partial_success"


def _same_observation_result(context, request, evaluations):
    service = ProjectCompletenessService(
        _Observer(None), clock=lambda: NOW,
        evaluator=lambda value: evaluations.append(value) or evaluate_project_context(_context(), now=NOW),
    )
    digest = hashlib.sha256(
        json.dumps(context.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return service.evaluate_authorized_observation(
        actor=CompletenessActor(1, UUID("00000000-0000-0000-0000-000000000001")),
        request=request,
        context=context,
        context_observation_digest=digest,
        current_user=_User(),
    )


@pytest.mark.parametrize("kind", tuple(ProjectContextSectionKind))
def test_each_section_accepts_only_its_exact_mapped_item_class(kind):
    context = _matrix_single_item_context(kind, _matrix_item(kind))
    evaluations = []
    result = _same_observation_result(
        context, CompletenessAssessmentRequest(project_id=1), evaluations,
    )
    assert result.status in {"success", "partial_success"}
    assert evaluations == [context]


@pytest.mark.parametrize("kind", tuple(ProjectContextSectionKind))
def test_each_section_rejects_an_incompatible_typed_item_before_evaluation(kind):
    incompatible = _plan() if kind is ProjectContextSectionKind.PROJECT_BASIS else _basis()
    context = _matrix_single_item_context(kind, incompatible)
    evaluations = []
    result = _same_observation_result(
        context, CompletenessAssessmentRequest(project_id=1), evaluations,
    )
    assert result.model_dump() == {"status": "unavailable"}
    assert evaluations == []


def test_fresh4_project_basis_in_execution_is_payload_free_and_never_evaluated():
    context = _matrix_single_item_context(ProjectContextSectionKind.EXECUTION, _basis())
    evaluations = []
    result = _same_observation_result(
        context, CompletenessAssessmentRequest(project_id=1), evaluations,
    )
    assert result.model_dump() == {"status": "unavailable"}
    assert evaluations == []


def test_incompatible_item_among_valid_siblings_is_not_silently_ignored():
    context = _matrix_context(replacements={
        ProjectContextSectionKind.DELIVERABLES: (_deliverable(), _basis()),
    })
    evaluations = []
    result = _same_observation_result(
        context, CompletenessAssessmentRequest(project_id=1), evaluations,
    )
    assert result.model_dump() == {"status": "unavailable"}
    assert evaluations == []


def test_unknown_runtime_item_type_fails_closed_before_scope_or_evaluation():
    unknown = ProjectContextItem(
        selector="legacy", version=1, standing="active", provenance=PROVENANCE,
        item_kind="legacy",
    )
    context = _matrix_single_item_context(ProjectContextSectionKind.EVIDENCE, unknown)
    evaluations = []
    result = _same_observation_result(
        context, CompletenessAssessmentRequest(project_id=1), evaluations,
    )
    assert result.model_dump() == {"status": "unavailable"}
    assert evaluations == []


@pytest.mark.parametrize(
    ("kind", "item"),
    (
        (ProjectContextSectionKind.EXECUTION, _plan().model_copy(update={"activities": (_basis(),)})),
        (ProjectContextSectionKind.EXECUTION, _plan().model_copy(update={"milestones": (_basis(),)})),
        (ProjectContextSectionKind.EXECUTION, _plan().model_copy(update={"dependencies": (_basis(),)})),
        (ProjectContextSectionKind.EXECUTION, _plan().model_copy(update={"progress": _basis()})),
        (ProjectContextSectionKind.DELIVERABLES, _deliverable().model_copy(update={"current_revision": _basis()})),
        (ProjectContextSectionKind.PROJECT_CONTROLS, _control().model_copy(update={"impacts": (_basis(),)})),
        (ProjectContextSectionKind.ENGINEERING_CONTEXT, _engineering_context().model_copy(update={"payload": _basis()})),
        (ProjectContextSectionKind.PROJECT_BASIS, _basis().model_copy(update={"provenance": {}})),
    ),
)
def test_frozen_nested_shape_invariants_fail_closed(kind, item):
    context = _matrix_single_item_context(kind, item)
    evaluations = []
    result = _same_observation_result(
        context, CompletenessAssessmentRequest(project_id=1), evaluations,
    )
    assert result.model_dump() == {"status": "unavailable"}
    assert evaluations == []


@pytest.mark.parametrize(
    "item",
    (
        _basis(project_id=2),
        _deliverable().model_copy(update={"workspace_id": 2}),
        _basis().model_copy(update={"project_id": True}),
    ),
)
def test_wrong_section_structural_failure_precedes_foreign_or_malformed_scope(item):
    context = _matrix_single_item_context(ProjectContextSectionKind.EXECUTION, item)
    evaluations = []
    result = _same_observation_result(
        context, CompletenessAssessmentRequest(project_id=1, workspace_id=1), evaluations,
    )
    assert result.model_dump() == {"status": "unavailable"}
    assert evaluations == []


def test_wrong_section_structural_failure_precedes_the_visible_input_bound():
    context = _matrix_single_item_context(ProjectContextSectionKind.EXECUTION, _basis())
    sections = list(context.sections)
    execution_index = list(ProjectContextSectionKind).index(ProjectContextSectionKind.EXECUTION)
    sections[execution_index] = ProjectContextSection.model_construct(
        kind=ProjectContextSectionKind.EXECUTION,
        state=SectionAvailable.model_construct(
            visible_count=1_001, observed_at=NOW, truncated=TruncationMetadata(truncated=False),
        ),
        items=(_basis(),) * 1_001,
    )
    malformed = context.model_copy(update={"sections": tuple(sections)})
    evaluations = []
    result = _same_observation_result(
        malformed, CompletenessAssessmentRequest(project_id=1), evaluations,
    )
    assert result.model_dump() == {"status": "unavailable"}
    assert evaluations == []


def test_empty_and_not_disclosed_valid_sections_remain_evaluable():
    empty_context = _context()
    not_disclosed_context = _context(protected=(ProjectContextSectionKind.DELIVERABLES,))
    for context in (empty_context, not_disclosed_context):
        evaluations = []
        result = _same_observation_result(
            context, CompletenessAssessmentRequest(project_id=1), evaluations,
        )
        assert result.status in {"success", "partial_success"}
        assert evaluations == [context]


@pytest.mark.parametrize(
    ("label", "activities", "milestones", "workspace_id", "expected_status"),
    (
        ("valid activity project", (_activity(),), (), None, "success"),
        ("matching activity workspace", (_activity().model_copy(update={"workspace_id": 2}),), (), 2, "success"),
        ("null activity workspace", (_activity(),), (), 2, "success"),
        ("foreign activity project", (_activity().model_copy(update={"project_id": 2}),), (), None, "protected_not_found"),
        ("foreign activity workspace", (_activity().model_copy(update={"workspace_id": 3}),), (), 2, "protected_not_found"),
        ("valid milestone project", (), (_milestone(),), None, "success"),
        ("workspace-neutral milestone", (), (_milestone(),), 2, "success"),
        ("foreign milestone project", (), (_milestone().model_copy(update={"project_id": 2}),), None, "protected_not_found"),
        ("one foreign activity among valid children", (_activity(), _activity().model_copy(update={"project_id": 2})), (), None, "protected_not_found"),
        ("one foreign milestone among valid children", (), (_milestone(), _milestone().model_copy(update={"project_id": 2})), None, "protected_not_found"),
        ("mixed foreign activity and milestone", (_activity().model_copy(update={"project_id": 2}),), (_milestone().model_copy(update={"project_id": 2}),), None, "protected_not_found"),
    ),
)
def test_nested_execution_scope_is_independent_of_the_scoped_plan_parent(
    label, activities, milestones, workspace_id, expected_status,
):
    context = _context(execution=(_plan(activities=activities, milestones=milestones),))
    request = CompletenessAssessmentRequest(project_id=1, workspace_id=workspace_id)

    ordinary_evaluations = []
    ordinary = ProjectCompletenessService(
        _Observer(context), clock=lambda: NOW,
        evaluator=lambda value: ordinary_evaluations.append(value) or evaluate_project_context(_context(), now=NOW),
    ).assess(
        actor=CompletenessActor(1, UUID("00000000-0000-0000-0000-000000000001")),
        request=request,
        current_user=_User(),
    )
    supplied_evaluations = []
    supplied = _same_observation_result(context, request, supplied_evaluations)

    for result, evaluations in ((ordinary, ordinary_evaluations), (supplied, supplied_evaluations)):
        assert result.status == expected_status, label
        assert evaluations == ([context] if expected_status == "success" else []), label


@pytest.mark.parametrize("over_limit", (False, True))
def test_nested_foreign_scope_precedes_the_visible_input_bound(over_limit):
    foreign_activity = _activity().model_copy(update={"project_id": 2})
    if over_limit:
        context = _bound_context(top_level=1000)
        sections = list(context.sections)
        execution_index = list(ProjectContextSectionKind).index(ProjectContextSectionKind.EXECUTION)
        execution = sections[execution_index]
        sections[execution_index] = ProjectContextSection.model_construct(
            kind=ProjectContextSectionKind.EXECUTION,
            state=execution.state.model_copy(
                update={"visible_count": execution.state.visible_count + 1},
            ),
            items=execution.items + (_plan(activities=(foreign_activity,)),),
        )
        context = context.model_copy(update={"sections": tuple(sections)})
    else:
        context = _context(execution=(_plan(activities=(foreign_activity,)),))
    evaluations = []
    result = _same_observation_result(context, CompletenessAssessmentRequest(project_id=1), evaluations)
    assert result.model_dump() == {"status": "protected_not_found"}
    assert evaluations == []


def test_malformed_nested_scope_is_unavailable_not_a_foreign_identity_result():
    malformed_activity = _activity().model_copy(update={"project_id": True})
    context = _context(execution=(_plan(activities=(malformed_activity,)),))
    evaluations = []
    result = _same_observation_result(context, CompletenessAssessmentRequest(project_id=1), evaluations)
    assert result.model_dump() == {"status": "unavailable"}
    assert evaluations == []
