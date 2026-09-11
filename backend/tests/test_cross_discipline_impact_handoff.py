from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import sessionmaker

from app.adapters.cross_discipline_change_impact import ProjectControlChangeImpactAdapter
from app.models.audit_log import AuditLog
from app.models.cross_discipline_intelligence import (
    CrossDisciplineAssessment, CrossDisciplineDisposition,
    CrossDisciplineFinding, CrossDisciplineFindingCurrent,
    CrossDisciplineIdempotency, CrossDisciplineOutbox,
)
from app.models.discipline_package import RegistryRelease
from app.schemas.cross_discipline_intelligence import PotentialImpactRequest
from app.services import cross_discipline_service as service_module
from app.services.cross_discipline_service import CrossDisciplineService


class _Service:
    def __init__(self): self.calls = []
    def create_change_impact(self, **kwargs): self.calls.append(kwargs); return {"outcome": "success", "id": uuid4()}


def test_project_control_adapter_calls_only_the_public_owner_boundary():
    service = _Service()
    result = ProjectControlChangeImpactAdapter(service=service, actor=object()).create_potential(
        project_id=1, workspace_id=None, change_id=uuid4(), change_version=1,
        target_kind="deliverable", target_id=uuid4(), rationale="Advisory handoff", idempotency_key=uuid4(),
    )
    assert result["outcome"] == "success" and len(service.calls) == 1


def test_project_control_adapter_uses_and_closes_a_fresh_owner_application():
    service = _Service()
    closed = []

    class _Application:
        actor = object()
        def __init__(self): self.service = service

    adapter = ProjectControlChangeImpactAdapter(
        application_factory=lambda: (_Application(), lambda: closed.append(True)),
    )
    result = adapter.create_potential(
        project_id=1, workspace_id=None, change_id=uuid4(), change_version=1,
        target_kind="deliverable", target_id=uuid4(), rationale="Advisory handoff", idempotency_key=uuid4(),
    )
    assert result["outcome"] == "success" and closed == [True] and len(service.calls) == 1


class _IdempotentOwner:
    def __init__(self):
        self.calls = []
        self.impacts = {}

    def create_potential(self, **values):
        self.calls.append(values)
        key = values["idempotency_key"]
        self.impacts.setdefault(key, uuid4())
        return {"outcome": "success", "id": self.impacts[key]}


def _handoff_subject(db_session, relationship_domain):
    project = relationship_domain["project"]
    actor = relationship_domain["actors"]["admin"]
    now = datetime.now(timezone.utc)
    if db_session.query(RegistryRelease).filter(RegistryRelease.is_current.is_(True)).one_or_none() is None:
        db_session.add(RegistryRelease(
            registry_digest="9" * 64, release_id="patch-053-handoff",
            core_contract_version=1, is_current=True, manifest_json={"schema_version": 1},
        ))
    assessment = CrossDisciplineAssessment(
        id=uuid4(), organization_id=project.organization_id, project_id=project.id,
        actor_id=actor.id, request_id=uuid4(), purpose="explicit_change_impact",
        rationale="Exercise reconciliation.", correlation_id=uuid4(),
        idempotency_key=uuid4(), combination_id="cross.eic.v1",
        request_digest="a" * 64, scope_digest="b" * 64,
        status="completed_with_findings", completed_at=now,
    )
    finding = CrossDisciplineFinding(
        id=uuid4(), organization_id=project.organization_id, project_id=project.id,
        assessment_id=assessment.id, ordinal=1, rule_id="xdi.eic.explicit_change_path.v1",
        rule_version="1.0.0", rule_digest="c" * 64,
        category="potential_change_impact", subcode="eic.explicit_change_path",
        severity="warning", fingerprint="d" * 64, recurrence_key="e" * 64,
        affected_selector="xdi.sel.v1/electrical/engineering_object/target/power_endpoint",
        payload={}, created_at=now,
    )
    current = CrossDisciplineFindingCurrent(
        organization_id=project.organization_id, project_id=project.id,
        assessment_id=assessment.id, finding_id=finding.id, projection_version=0,
        current_state="open", updated_at=now,
    )
    db_session.add_all((assessment, finding, current))
    db_session.flush()
    data = PotentialImpactRequest(
        assessment_id=assessment.id, finding_id=finding.id, change_id=uuid4(),
        change_version=1, target_id=uuid4(), target_kind="deliverable",
        rationale="Create an advisory potential impact.", correlation_id=uuid4(),
        idempotency_key=uuid4(),
    )
    factory = sessionmaker(
        bind=db_session.connection(), expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    return project, actor, assessment, finding, current, data, factory


def test_three_uow_reconciliation_is_atomic_idempotent_and_freshly_authorized(
    db_session, relationship_domain, monkeypatch,
):
    project, actor, assessment, finding, current, data, factory = _handoff_subject(
        db_session, relationship_domain,
    )
    owner = _IdempotentOwner()
    sessions, authorizations = [], []
    real_authorizer = service_module.SqlAlchemyCrossDisciplineAuthorizer

    class SpyAuthorizer:
        def __init__(self, session):
            self._delegate = real_authorizer(session)
            sessions.append(session)

        def authorize_scope(self, **values):
            authorizations.append((self._delegate.session, values["workspace_ids"]))
            return self._delegate.authorize_scope(**values)

    monkeypatch.setattr(service_module, "SqlAlchemyCrossDisciplineAuthorizer", SpyAuthorizer)
    service = CrossDisciplineService(impact_handoff=owner)
    first = service.handoff_potential_impact(
        session_factory=factory, actor_id=actor.id, actor_role="admin",
        organization_id=project.organization_id, project_id=project.id,
        assessment_id=assessment.id, finding_id=finding.id, data=data,
    )
    assert first["outcome"] == "success" and first["state"] == "reconciled"
    assert len({id(session) for session in sessions}) == 2
    # This focused fixture has no assessment workspaces, so each phase makes
    # its initial and scoped fresh-authority checks against the empty scope.
    assert [workspace_ids for _, workspace_ids in authorizations].count(()) == 4
    handoff = db_session.query(CrossDisciplineIdempotency).filter_by(
        assessment_id=assessment.id, operation="create_potential_impact",
    ).one()
    disposition = db_session.query(CrossDisciplineDisposition).filter_by(
        assessment_id=assessment.id, finding_id=finding.id,
    ).one()
    assert handoff.project_control_impact_id is not None
    assert disposition.action == "confirm"
    assert db_session.query(CrossDisciplineOutbox).filter_by(
        assessment_id=assessment.id,
        event_type="cross_discipline_potential_impact_reconciled",
    ).count() == 1
    assert db_session.query(AuditLog).filter_by(
        entity_uuid=assessment.id,
        action="cross_discipline_potential_impact_reconciled",
    ).count() == 1
    db_session.refresh(current)
    assert current.current_state == "confirmed"
    db_session.expire(assessment)
    assert db_session.get(CrossDisciplineAssessment, assessment.id).aggregate_version == 2

    retry = service.handoff_potential_impact(
        session_factory=factory, actor_id=actor.id, actor_role="admin",
        organization_id=project.organization_id, project_id=project.id,
        assessment_id=assessment.id, finding_id=finding.id, data=data,
    )
    assert retry == first and len(owner.impacts) == 1
    assert db_session.query(CrossDisciplineDisposition).filter_by(assessment_id=assessment.id).count() == 1
    assert db_session.query(CrossDisciplineOutbox).filter_by(assessment_id=assessment.id).count() == 1


def test_phase_three_failure_is_recoverable_without_duplicate_owner_impact(
    db_session, relationship_domain,
):
    project, actor, assessment, finding, _current, data, factory = _handoff_subject(
        db_session, relationship_domain,
    )
    owner = _IdempotentOwner()
    service = CrossDisciplineService(impact_handoff=owner)
    stage_event = service._stage_event
    service._stage_event = lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("phase three failure"))
    failed = service.handoff_potential_impact(
        session_factory=factory, actor_id=actor.id, actor_role="admin",
        organization_id=project.organization_id, project_id=project.id,
        assessment_id=assessment.id, finding_id=finding.id, data=data,
    )
    assert failed == {"outcome": "unavailable", "state": "handoff_link_pending", "advisory": True}
    assert len(owner.impacts) == 1
    assert db_session.query(CrossDisciplineDisposition).filter_by(assessment_id=assessment.id).count() == 0
    service._stage_event = stage_event
    retry = service.handoff_potential_impact(
        session_factory=factory, actor_id=actor.id, actor_role="admin",
        organization_id=project.organization_id, project_id=project.id,
        assessment_id=assessment.id, finding_id=finding.id, data=data,
    )
    assert retry["outcome"] == "success" and len(owner.impacts) == 1
    assert db_session.query(CrossDisciplineDisposition).filter_by(assessment_id=assessment.id).count() == 1
