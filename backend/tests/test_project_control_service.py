from uuid import UUID, uuid4

from app.models.customer import Customer
from app.models.organization import Organization
from app.models.project import Project
from app.adapters.project_control_targets import TargetProtected
from app.models.project_control import ProjectChange, ProjectChangeImpact, ProjectControlIdempotency, ProjectDecision, ProjectIssue, ProjectIssueHistory, ProjectRisk, ProjectRiskHistory
from app.repositories.project_control_unit_of_work import SqlAlchemyProjectControlUnitOfWork
from app.schemas.project_control import ChangeCommand, ConfirmImpactCommand, ControlActor, ControlTransitionCommand, ImpactCommand, SupersedeChangeCommand, DecisionCommand, IssueCommand, RiskCommand
from app.services.project_control_service import ProjectControlService
from conftest import create_user
from app.permissions.roles import Role


class Authorization:
    def can_read(self, *, actor, project): return project.organization_id == actor.organization_id and project.owner_id == actor.actor_id
    def can_mutate(self, *, actor, project): return self.can_read(actor=actor, project=project)


class Targets:
    def __init__(self, denied=False): self.denied=denied; self.calls=[]
    def authorize_exact(self, **kwargs):
        self.calls.append(kwargs)
        if self.denied: raise TargetProtected()


def domain(db_session, targets=None):
    organization_id=uuid4()
    db_session.add(Organization(id=organization_id, name=f"PATCH-047 Controls {organization_id.hex[:8]}", slug=f"patch-047-{organization_id.hex[:8]}", is_active=True)); db_session.flush()
    owner = create_user(db_session, username=f"control-{uuid4().hex[:8]}", role=Role.ENGINEER)
    customer = Customer(name=f"Control {uuid4().hex[:8]}", organization_id=organization_id)
    db_session.add(customer); db_session.flush()
    project = Project(organization_id=organization_id, project_code=f"SAT-PRJ-2097-{customer.id + 7000:04d}", name="Controls", customer_id=customer.id, owner_id=owner.id, status="new", priority="medium", progress=0)
    db_session.add(project); db_session.commit()
    actor = ControlActor(actor_id=owner.id, organization_id=organization_id)
    service = ProjectControlService(uow_factory=lambda: SqlAlchemyProjectControlUnitOfWork(db_session), authorization=Authorization(), target_authorization=targets)
    return service, actor, project


def risk(): return RiskCommand(statement="Pump availability risk", category="operations", likelihood="high", impact="high", rationale="Human records uncertain future impact")
def issue(): return IssueCommand(statement="Observed wiring defect", observed_context="Inspection found a loose terminal", severity="high", rationale="Human records current observed problem")
def decision(predecessor_id=None): return DecisionCommand(statement="Use guarded terminal design", rationale="Human engineering choice", predecessor_id=predecessor_id)
def change(predecessor_id=None): return ChangeCommand(statement="Cable route changes after field observation", rationale="Human records changed engineering condition", predecessor_id=predecessor_id)


def test_risk_lifecycle_history_replay_and_conflict(db_session):
    service, actor, project = domain(db_session); key = uuid4()
    created = service.create_risk(project_id=project.id, data=risk(), actor=actor, idempotency_key=key)
    assert created.outcome == "success"
    assert service.create_risk(project_id=project.id, data=risk(), actor=actor, idempotency_key=key) == created
    changed = service.transition_risk(risk_id=created.id, actor=actor, idempotency_key=uuid4(), data=ControlTransitionCommand(target_standing="treated", rationale="Human treatment disposition", expected_version=1))
    assert changed.outcome == "success" and changed.version == 2
    assert db_session.query(ProjectRiskHistory).filter_by(risk_id=created.id).count() == 2
    assert db_session.query(ProjectControlIdempotency).filter_by(project_id=project.id).count() == 2


def test_issue_is_not_execution_blocker_and_is_project_protected(db_session):
    service, actor, project = domain(db_session)
    created = service.create_issue(project_id=project.id, data=issue(), actor=actor, idempotency_key=uuid4())
    resolved = service.transition_issue(issue_id=created.id, actor=actor, idempotency_key=uuid4(), data=ControlTransitionCommand(target_standing="resolved", rationale="Human resolution disposition", expected_version=1))
    assert resolved.outcome == "success" and db_session.query(ProjectIssueHistory).filter_by(issue_id=created.id).count() == 2
    assert db_session.query(ProjectIssue).filter_by(id=created.id).one().disposition == "Human resolution disposition"
    other = ControlActor(actor_id=actor.actor_id, organization_id=uuid4())
    assert service.get(kind="issue", control_id=created.id, actor=other).outcome == "protected_not_found"


def test_human_decision_successor_preserves_predecessor_and_no_overwrite(db_session):
    service, actor, project = domain(db_session)
    first = service.create_decision(project_id=project.id, data=decision(), actor=actor, idempotency_key=uuid4())
    successor = service.create_decision_successor(decision_id=first.id, data=decision(first.id), actor=actor, idempotency_key=uuid4())
    assert successor.outcome == "success"
    original = db_session.query(ProjectDecision).filter_by(id=first.id).one()
    replacement = db_session.query(ProjectDecision).filter_by(id=successor.id).one()
    assert original.statement == "Use guarded terminal design" and replacement.predecessor_id == first.id
    assert service.transition_decision(decision_id=first.id, actor=actor, idempotency_key=uuid4(), data=ControlTransitionCommand(target_standing="accepted", rationale="Human accepts recorded decision", expected_version=1)).outcome == "success"


def test_idempotency_conflict_and_cross_scope_creation_are_closed(db_session):
    service, actor, project = domain(db_session); key = uuid4()
    assert service.create_risk(project_id=project.id, data=risk(), actor=actor, idempotency_key=key).outcome == "success"
    changed = RiskCommand(statement="Different risk", category="operations", likelihood="low", impact="low", rationale="Different request")
    assert service.create_risk(project_id=project.id, data=changed, actor=actor, idempotency_key=key).outcome == "idempotency_conflict"
    assert service.create_risk(project_id=999999, data=risk(), actor=actor, idempotency_key=uuid4()).outcome == "protected_not_found"


def test_project_scoped_current_and_history_reads_are_bounded_and_protected(db_session):
    service, actor, project = domain(db_session)
    created = service.create_issue(project_id=project.id, data=issue(), actor=actor, idempotency_key=uuid4())
    listed = service.list(kind="issue", project_id=project.id, actor=actor)
    history = service.history(kind="issue", control_id=created.id, project_id=project.id, actor=actor)
    assert listed.outcome == "success" and listed.visible_count == 1 and listed.items[0].id == created.id
    assert history.outcome == "success" and history.visible_count == 1 and history.items[0].aggregate_version == 1
    assert service.get(kind="issue", control_id=created.id, project_id=project.id + 1, actor=actor).outcome == "protected_not_found"
    assert service.transition_issue(issue_id=created.id, project_id=project.id + 1, data=ControlTransitionCommand(target_standing="resolved", rationale="Human resolution", expected_version=1), actor=actor, idempotency_key=uuid4()).outcome == "protected_not_found"


def test_change_successor_and_explicit_supersession_preserve_predecessor(db_session):
    service, actor, project = domain(db_session)
    first=service.create_change(project_id=project.id,data=change(),actor=actor,idempotency_key=uuid4())
    assert first.outcome=="success"
    assert service.create_change(project_id=project.id,data=change(first.id),actor=actor,idempotency_key=uuid4()).outcome=="invalid_request"
    successor=service.create_change_successor(change_id=first.id,data=change(first.id),actor=actor,idempotency_key=uuid4())
    assert successor.outcome=="success"
    assert db_session.query(ProjectChange).filter_by(id=first.id).one().standing=="recorded"
    result=service.supersede_change(predecessor_id=first.id,data=SupersedeChangeCommand(successor_id=successor.id,expected_predecessor_version=1,rationale="Human explicitly supersedes predecessor"),actor=actor,idempotency_key=uuid4())
    assert result.outcome=="success"
    assert db_session.query(ProjectChange).filter_by(id=first.id).one().standing=="withdrawn"
    assert db_session.query(ProjectChange).filter_by(id=successor.id).one().standing=="recorded"


def test_potential_impact_requires_explicit_human_confirmation_and_replays(db_session):
    targets=Targets(); service, actor, project=domain(db_session,targets)
    recorded=service.create_change(project_id=project.id,data=change(),actor=actor,idempotency_key=uuid4())
    command=ImpactCommand(change_id=recorded.id,target_kind="activity",target_id=uuid4(),statement="Activity may be affected",rationale="Human records potential impact",expected_version=1)
    key=uuid4(); potential=service.create_change_impact(data=command,actor=actor,idempotency_key=key)
    assert potential.outcome=="success" and potential.standing=="potential"
    assert service.create_change_impact(data=command,actor=actor,idempotency_key=key)==potential
    stored=db_session.query(ProjectChangeImpact).filter_by(id=potential.id).one()
    assert stored.standing=="potential" and stored.confirmed_by_id is None and len(targets.calls)==1
    confirmed=service.confirm_change_impact(impact_id=potential.id,data=ConfirmImpactCommand(expected_change_version=1,rationale="Human confirms engineering impact"),actor=actor,idempotency_key=uuid4())
    assert confirmed.outcome=="success" and confirmed.standing=="confirmed"
    assert db_session.query(ProjectChangeImpact).filter_by(id=potential.id).one().confirmed_by_id==actor.actor_id


def test_duplicate_impact_and_competing_confirmation_have_one_winner(db_session):
    targets=Targets(); service,actor,project=domain(db_session,targets)
    recorded=service.create_change(project_id=project.id,data=change(),actor=actor,idempotency_key=uuid4())
    command=ImpactCommand(change_id=recorded.id,target_kind="milestone",target_id=uuid4(),statement="Milestone may be affected",rationale="Human potential impact",expected_version=1)
    potential=service.create_change_impact(data=command,actor=actor,idempotency_key=uuid4())
    assert service.create_change_impact(data=command,actor=actor,idempotency_key=uuid4()).outcome=="version_conflict"
    first=service.confirm_change_impact(impact_id=potential.id,data=ConfirmImpactCommand(expected_change_version=1,rationale="Human confirms impact"),actor=actor,idempotency_key=uuid4())
    second=service.confirm_change_impact(impact_id=potential.id,data=ConfirmImpactCommand(expected_change_version=1,rationale="Competing confirmation"),actor=actor,idempotency_key=uuid4())
    assert first.outcome=="success" and second.outcome=="invalid_request"
def test_graph_control_summaries_are_exact_and_exclude_protected_text(db_session):
    """The canonical owner, not Project Context, projects safe control facts."""
    service, actor, project = domain(db_session)
    created = {
        "risk": service.create_risk(project_id=project.id, data=risk(), actor=actor, idempotency_key=uuid4()),
        "issue": service.create_issue(project_id=project.id, data=issue(), actor=actor, idempotency_key=uuid4()),
        "decision": service.create_decision(project_id=project.id, data=decision(), actor=actor, idempotency_key=uuid4()),
        "change": service.create_change(project_id=project.id, data=change(), actor=actor, idempotency_key=uuid4()),
    }
    for kind, record in created.items():
        result = service.get_control_graph_summary(kind=kind, actor=actor, project_id=project.id, control_id=record.id)
        assert result.id == record.id
        assert not ({"statement", "rationale", "owner_id", "accepted_by_id", "confirmed_by_id"} & set(result.model_fields))


def test_project_control_incident_read_is_exact_for_successor_and_impact(db_session):
    targets=Targets();service,actor,project=domain(db_session,targets)
    first=service.create_change(project_id=project.id,data=change(),actor=actor,idempotency_key=uuid4())
    successor=service.create_change_successor(change_id=first.id,data=change(first.id),actor=actor,idempotency_key=uuid4())
    target_id=uuid4();impact=service.create_change_impact(data=ImpactCommand(change_id=successor.id,target_kind="activity",target_id=target_id,statement="Bounded effect",rationale="Human records",expected_version=1),actor=actor,idempotency_key=uuid4())
    change_page=service.list_authorized_incident_graph_links(actor=actor,project_id=project.id,selector_kind="change",selector_id=successor.id)
    assert {item.relationship for item in change_page.items}=={"change_successor","change_impact"}
    target_page=service.list_authorized_incident_graph_links(actor=actor,project_id=project.id,selector_kind="activity",selector_id=target_id)
    assert len(target_page.items)==1 and target_page.items[0].source_id==impact.id
