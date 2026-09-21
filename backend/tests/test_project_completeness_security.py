import hashlib
import json
from datetime import datetime, timezone
from uuid import UUID

from app.ports.project_completeness import CompletenessActor, CompletenessAssessmentRequest
from app.schemas.project_completeness import CompletenessProtectedNotFound, CompletenessUnavailable
from app.schemas.project_context import (
    AuthorityClassification, ContextObservationStatus, ExecutionActivityItem,
    ExecutionPlanItem, ExecutionProgressItem, FactProvenance, ProjectBasisItem,
    ProjectContextProtectedNotFound, ProjectContextSection, ProjectContextSectionKind,
    ProjectContextSuccess, SectionAvailable, SectionEmpty, SectionNotDisclosed,
    TemporalClassification, TruncationMetadata,
)
from app.services.project_completeness_service import ProjectCompletenessService


class User:
    id = 1


class ProtectedObserver:
    def observe(self, **kwargs):
        return ProjectContextProtectedNotFound()


class ExplodingObserver:
    def observe(self, **kwargs):
        raise RuntimeError("private owner failure")


def _actor():
    return CompletenessActor(1, UUID("00000000-0000-0000-0000-000000000001"))


NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
PROVENANCE = FactProvenance(
    owner_kind="project_foundation", selector="basis", observed_at=NOW,
    authority_class=AuthorityClassification.HUMAN_AUTHORITATIVE,
    temporal_class=TemporalClassification.CURRENT,
)


def _available(kind, items):
    return ProjectContextSection(
        kind=kind, items=items,
        state=SectionAvailable(
            visible_count=len(items), observed_at=NOW,
            truncated=TruncationMetadata(truncated=False),
        ),
    )


def _scoped_context(*, basis_project_id=1, activity_project_id=1, activity_workspace_id=None):
    basis = ProjectBasisItem(
        selector="basis", version=1, standing="active", provenance=PROVENANCE,
        project_id=basis_project_id, foundation_established=True, purpose="Purpose",
        engineering_basis="Basis", current_stage="verification", ordered_in_scope=("scope",),
        completion_basis="Completion", required_project_inputs=("input",),
    )
    activity = ExecutionActivityItem(
        activity_id=UUID("00000000-0000-4000-8000-000000000011"),
        plan_id=UUID("00000000-0000-4000-8000-000000000001"),
        project_id=activity_project_id, workspace_id=activity_workspace_id,
        title="Activity", ordinal=1, standing="active", version=1, blocker_present=True,
    )
    plan = ExecutionPlanItem(
        selector="plan", version=1, standing="active", provenance=PROVENANCE,
        plan_id=UUID("00000000-0000-4000-8000-000000000001"), project_id=1,
        plan_version=1, activities=(activity,), milestones=(),
        progress=ExecutionProgressItem(numerator=0, denominator=1, percent=0),
    )
    sections = []
    for kind in ProjectContextSectionKind:
        if kind is ProjectContextSectionKind.PROJECT_BASIS:
            sections.append(_available(kind, (basis,)))
        elif kind is ProjectContextSectionKind.EXECUTION:
            sections.append(_available(kind, (plan,)))
        else:
            sections.append(ProjectContextSection(kind=kind, state=SectionEmpty()))
    return ProjectContextSuccess(
        observation_started_at=NOW, observation_completed_at=NOW,
        observation_status=ContextObservationStatus.COMPLETE_WITHIN_BOUNDS,
        sections=tuple(sections),
    )


def _same_observation_result(context, request, evaluations):
    digest = hashlib.sha256(
        json.dumps(context.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return ProjectCompletenessService(
        ExplodingObserver(), evaluator=lambda value: evaluations.append(value),
    ).evaluate_authorized_observation(
        actor=_actor(), request=request, context=context,
        context_observation_digest=digest, current_user=User(),
    )


def test_protected_upstream_result_is_payload_free_and_does_not_disclose_scope():
    result = ProjectCompletenessService(ProtectedObserver()).assess(
        actor=_actor(),
        request=CompletenessAssessmentRequest(project_id=1, workspace_id=2),
        current_user=User(),
    )
    assert isinstance(result, CompletenessProtectedNotFound)
    assert result.model_dump() == {"status": "protected_not_found"}


def test_owner_exception_is_payload_free_unavailable_without_foreign_details():
    result = ProjectCompletenessService(ExplodingObserver()).assess(
        actor=_actor(),
        request=CompletenessAssessmentRequest(project_id=1),
        current_user=User(),
    )
    assert isinstance(result, CompletenessUnavailable)
    assert result.model_dump() == {"status": "unavailable"}


def test_trusted_request_contract_rejects_client_scope_shaping():
    for kwargs in (
        {"project_id": 0},
        {"project_id": 1, "workspace_id": 0},
        {"project_id": True},
    ):
        try:
            CompletenessAssessmentRequest(**kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid trusted request was accepted")


def test_not_disclosed_same_observation_has_no_count_or_selector_disclosure():
    context = ProjectContextSuccess(
        observation_started_at=__import__("datetime").datetime(2026, 1, 1, tzinfo=__import__("datetime").timezone.utc),
        observation_completed_at=__import__("datetime").datetime(2026, 1, 1, tzinfo=__import__("datetime").timezone.utc),
        observation_status=ContextObservationStatus.PARTIAL,
        sections=tuple(ProjectContextSection(kind=kind, state=SectionNotDisclosed()) for kind in ProjectContextSectionKind),
    )
    digest = __import__("hashlib").sha256(__import__("json").dumps(context.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    result = ProjectCompletenessService(ExplodingObserver()).evaluate_authorized_observation(
        actor=_actor(), request=CompletenessAssessmentRequest(project_id=1), context=context,
        context_observation_digest=digest, current_user=User(),
    )
    assert result.status == "partial_success"
    serialized = result.model_dump_json().lower()
    assert all(value not in serialized for value in ("count", "selector", "hidden", "remainder"))


def test_top_level_and_nested_foreign_scope_results_are_payload_free_and_silent():
    top_level_evaluations = []
    top_level = _same_observation_result(
        _scoped_context(basis_project_id=2),
        CompletenessAssessmentRequest(project_id=1),
        top_level_evaluations,
    )
    workspace_evaluations = []
    nested_workspace = _same_observation_result(
        _scoped_context(activity_workspace_id=3),
        CompletenessAssessmentRequest(project_id=1, workspace_id=2),
        workspace_evaluations,
    )
    for result, evaluations, forbidden in (
        (top_level, top_level_evaluations, "2"),
        (nested_workspace, workspace_evaluations, "3"),
    ):
        assert result.model_dump() == {"status": "protected_not_found"}
        assert evaluations == []
        assert forbidden not in result.model_dump_json()


def test_structural_failure_precedes_foreign_scope_without_disclosing_it():
    context = _scoped_context()
    sections = list(context.sections)
    execution_index = list(ProjectContextSectionKind).index(ProjectContextSectionKind.EXECUTION)
    foreign_basis = sections[0].items[0].model_copy(update={"project_id": 2})
    sections[execution_index] = ProjectContextSection.model_construct(
        kind=ProjectContextSectionKind.EXECUTION,
        state=SectionAvailable.model_construct(
            visible_count=1, observed_at=NOW, truncated=TruncationMetadata(truncated=False),
        ),
        items=(foreign_basis,),
    )
    malformed = context.model_copy(update={"sections": tuple(sections)})
    evaluations = []
    result = _same_observation_result(
        malformed, CompletenessAssessmentRequest(project_id=1), evaluations,
    )
    assert result.model_dump() == {"status": "unavailable"}
    assert evaluations == []
    assert "2" not in result.model_dump_json()
