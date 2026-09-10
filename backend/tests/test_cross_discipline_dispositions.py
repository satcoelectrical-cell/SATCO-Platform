import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from app.discipline_packages.cross_discipline.canonical import digest
from app.models.cross_discipline_intelligence import (
    CrossDisciplineAssessment, CrossDisciplineAssessmentWorkspace,
    CrossDisciplineFinding, CrossDisciplineSnapshot,
)
from app.models.project_control import ProjectDecision
from app.schemas.cross_discipline_intelligence import DispositionAppend
from app.services.cross_discipline_service import (
    CrossDisciplineService, InvalidDisposition, TRANSITIONS, VersionConflict,
    disposition_transition,
)


EXPECTED = {
    "open": {"acknowledge", "confirm", "reject_not_applicable", "dispute", "require_reassessment", "supersede"},
    "acknowledged": {"confirm", "reject_not_applicable", "dispute", "require_reassessment", "supersede"},
    "confirmed": {"accept_risk", "declare_resolution", "dispute", "require_reassessment", "supersede"},
    "rejected_not_applicable": {"require_reassessment", "supersede"},
    "risk_accepted": {"declare_resolution", "require_reassessment", "supersede"},
    "resolution_declared": {"require_reassessment", "supersede"},
    "disputed": {"confirm", "reject_not_applicable", "require_reassessment", "supersede"},
    "reassessment_required": {"supersede"},
    "superseded": set(),
}


def test_exact_transition_matrix_is_closed():
    assert {state: set(actions) for state, actions in TRANSITIONS.items()} == EXPECTED


def test_action_evidence_and_version_requirements():
    with pytest.raises(InvalidDisposition):
        disposition_transition(current_state="confirmed", action="accept_risk", assessment_version=1, expected_assessment_version=1, view_version=0, expected_view_version=0)
    with pytest.raises(InvalidDisposition):
        disposition_transition(current_state="confirmed", action="declare_resolution", assessment_version=1, expected_assessment_version=1, view_version=0, expected_view_version=0)
    with pytest.raises(VersionConflict):
        disposition_transition(current_state="open", action="confirm", assessment_version=2, expected_assessment_version=1, view_version=0, expected_view_version=0)


def test_superseded_is_terminal():
    with pytest.raises(VersionConflict):
        disposition_transition(current_state="superseded", action="confirm", assessment_version=2, expected_assessment_version=2, view_version=1, expected_view_version=1)


def test_disposition_append_is_atomic_idempotent_and_versions_current_view(db_session, relationship_domain):
    project = relationship_domain["project"]
    actor = relationship_domain["actors"]["admin"]
    workspaces = tuple(sorted((
        relationship_domain["provider_workspace"],
        relationship_domain["consumer_workspace"],
    ), key=lambda item: item.id))
    relationship_domain["provider_workspace"].canonical_discipline_id = "instrumentation"
    now = datetime.now(timezone.utc)
    assessment_id, execution_id, snapshot_id, finding_id = uuid4(), uuid4(), uuid4(), uuid4()
    db_session.add(CrossDisciplineAssessment(
        id=assessment_id, organization_id=project.organization_id,
        project_id=project.id, actor_id=actor.id, request_id=uuid4(),
        purpose="interface_assessment", rationale="Retained finding fixture.",
        correlation_id=uuid4(), idempotency_key=uuid4(),
        combination_id="cross.ei.v1", request_digest="1" * 64,
        scope_digest="2" * 64, status="completed_with_findings",
        aggregate_version=1, created_at=now, completed_at=now,
    ))
    snapshot_payload = {"result_digest": "3" * 64}
    db_session.add(CrossDisciplineSnapshot(
        organization_id=project.organization_id, project_id=project.id,
        assessment_id=assessment_id, execution_id=execution_id,
        snapshot_id=snapshot_id, registry_digest="4" * 64,
        definition_digest="5" * 64, source_manifest_digest="6" * 64,
        finding_set_digest="7" * 64,
        snapshot_digest=digest(snapshot_payload, "satco:cross-discipline-snapshot:v1"),
        result_digest="3" * 64, observed_through=now, completed_at=now,
        payload=snapshot_payload,
    ))
    for ordinal, workspace in enumerate(workspaces):
        package_key = workspace.canonical_discipline_id or workspace.discipline
        db_session.add(CrossDisciplineAssessmentWorkspace(
            organization_id=project.organization_id, project_id=project.id,
            assessment_id=assessment_id, workspace_id=workspace.id,
            package_key=package_key, discipline_id=package_key,
            role=f"participant_{ordinal}", binding_revision=1,
            binding_digest=digest({"workspace_id": workspace.id}, "test"),
        ))
    db_session.add(CrossDisciplineFinding(
        id=finding_id, organization_id=project.organization_id,
        project_id=project.id, assessment_id=assessment_id, ordinal=0,
        rule_id="test.rule", rule_version="1", rule_digest="8" * 64,
        category="inconsistent", subcode="test",
        severity="major", fingerprint="9" * 64,
        recurrence_key="a" * 64, affected_selector="test",
        payload={"provenance": {}}, created_at=now,
    ))
    db_session.flush()
    factory = sessionmaker(
        bind=db_session.connection(), expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    data = DispositionAppend(
        action="acknowledge", expected_assessment_version=1,
        expected_current_view_version=0, rationale="Reviewed by the owner.",
        correlation_id=uuid4(), idempotency_key=uuid4(),
    )
    service = CrossDisciplineService()
    first = service.append_disposition(
        session_factory=factory, actor_id=actor.id, actor_role="admin",
        organization_id=project.organization_id, project_id=project.id,
        assessment_id=assessment_id, finding_id=finding_id, data=data,
    )
    second = service.append_disposition(
        session_factory=factory, actor_id=actor.id, actor_role="admin",
        organization_id=project.organization_id, project_id=project.id,
        assessment_id=assessment_id, finding_id=finding_id, data=data,
    )
    assert first == second
    assert first["outcome"] == "success"
    assert first["assessment_version"] == 2
    assert first["current_view_version"] == 1

    confirm = service.append_disposition(
        session_factory=factory, actor_id=actor.id, actor_role="admin",
        organization_id=project.organization_id, project_id=project.id,
        assessment_id=assessment_id, finding_id=finding_id,
        data=DispositionAppend(
            action="confirm", expected_assessment_version=2,
            expected_current_view_version=1, rationale="Confirm the advisory condition.",
            correlation_id=uuid4(), idempotency_key=uuid4(),
        ),
    )
    assert confirm["current_state"] == "confirmed"
    rejected_risk = service.append_disposition(
        session_factory=factory, actor_id=actor.id, actor_role="admin",
        organization_id=project.organization_id, project_id=project.id,
        assessment_id=assessment_id, finding_id=finding_id,
        data=DispositionAppend(
            action="accept_risk", expected_assessment_version=3,
            expected_current_view_version=2, rationale="Unverified decision reference.",
            correlation_id=uuid4(), idempotency_key=uuid4(),
            accepted_decision_id=uuid4(),
        ),
    )
    assert rejected_risk == {"outcome": "invalid_request", "reason_code": "accepted_decision_required"}
    accepted = ProjectDecision(
        organization_id=project.organization_id, project_id=project.id,
        version=1, created_by_id=actor.id, updated_by_id=actor.id,
        created_at=now, updated_at=now, statement="Accepted risk basis.",
        rationale="Authorized human decision.", alternatives=[], standing="accepted",
        accepted_by_id=actor.id, accepted_at=now,
    )
    db_session.add(accepted)
    db_session.flush()
    accepted_risk = service.append_disposition(
        session_factory=factory, actor_id=actor.id, actor_role="admin",
        organization_id=project.organization_id, project_id=project.id,
        assessment_id=assessment_id, finding_id=finding_id,
        data=DispositionAppend(
            action="accept_risk", expected_assessment_version=3,
            expected_current_view_version=2, rationale="Apply accepted decision.",
            correlation_id=uuid4(), idempotency_key=uuid4(),
            accepted_decision_id=accepted.id,
        ),
    )
    assert accepted_risk["current_state"] == "risk_accepted"
