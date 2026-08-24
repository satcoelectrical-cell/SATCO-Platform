from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

from app.schemas.engineering_execution_plan import (
    CreateExecutionActivityRequest, EstablishExecutionPlanRequest,
    ExecutionActor, TransitionExecutionActivityRequest,
)
from app.services.engineering_execution_plan_service import EngineeringExecutionPlanService


ORG = UUID("02810000-0000-4000-8000-000000000001")


class Repository:
    def __init__(self): self.plan = None; self.activities=[]; self.milestones=[]; self.dependencies=[]; self.idempotency=[]; self.revisions=[]
    def get_plan(self, **kwargs): return self.plan
    def get_activity(self, *, activity_id, **kwargs): return next((row for row in self.activities if row.id == activity_id), None)
    def get_idempotency(self, **kwargs): return next((row for row in self.idempotency if row.operation == kwargs["operation"] and row.idempotency_key == kwargs["idempotency_key"]), None)
    def add(self, item):
        name = item.__class__.__name__
        if name == "EngineeringExecutionPlan": self.plan = item
        elif name == "EngineeringExecutionActivity": self.activities.append(item)
        elif name == "EngineeringExecutionIdempotency": self.idempotency.append(item)
    def flush(self): pass
    def load_plan_children(self, **kwargs): return self.activities, self.milestones, self.dependencies
    def append_revision(self, **kwargs): self.revisions.append((kwargs["plan"].version, kwargs["rationale"]))
    def replace_dependencies(self, *, edges, **kwargs): self.dependencies=[SimpleNamespace(predecessor_activity_id=a, dependent_activity_id=b) for a,b in edges]
    def replace_milestone_links(self, **kwargs): pass


class Uow:
    def __init__(self, repository): self.repository=repository; self.committed=False; self.audits=[]
    def __enter__(self): return self
    def __exit__(self, *_): return False
    def stage_audit(self, **kwargs): self.audits.append(kwargs)
    def commit(self): self.committed=True
    def rollback(self): pass


class Authorization:
    def __init__(self, project): self.project=project
    def get_project(self, **kwargs): return self.project
    def can_read(self, **kwargs): return True
    def can_mutate(self, **kwargs): return True
    def validate_workspace(self, **kwargs): return True
    def validate_responsible_user(self, **kwargs): return True


class Foundation:
    def is_established(self, **kwargs): return True


def service():
    repository=Repository(); uow=Uow(repository)
    project=SimpleNamespace(id=7, organization_id=ORG, status="in_progress", owner_id=4, primary_assignee_id=None)
    return EngineeringExecutionPlanService(uow_factory=lambda:uow, authorization=Authorization(project), foundation=Foundation()), repository, uow


def test_establish_create_and_transition_are_explicit_human_execution_facts():
    app, repository, uow = service(); actor=ExecutionActor(actor_id=4, organization_id=ORG)
    established=app.establish(project_id=7, data=EstablishExecutionPlanRequest(expected_plan_version=0, rationale="Human establishes execution basis"), actor=actor, idempotency_key=uuid4())
    assert established.outcome == "success" and repository.revisions == [(1, "Human establishes execution basis")]
    created=app.create_activity(project_id=7, data=CreateExecutionActivityRequest(expected_plan_version=1,title="Prepare motor schedule",description=None,ordinal=0,workspace_id=None,responsible_user_id=None,target_date=None,completion_basis="Human reviews schedule basis",rationale="Human adds engineering activity"),actor=actor,idempotency_key=uuid4())
    assert created.standing == "planned" and created.plan_version == 2
    ready=app.transition_activity(project_id=7,activity_id=created.activity_id,data=TransitionExecutionActivityRequest(expected_activity_version=1,target_standing="ready",rationale="Dependencies are ready"),actor=actor,idempotency_key=uuid4())
    assert ready.standing == "ready" and ready.activity_version == 2
    assert all("rationale" not in audit["details"] for audit in uow.audits)


def test_stale_version_is_conflict_and_replay_is_stable_after_later_state():
    app, repository, _ = service(); actor=ExecutionActor(actor_id=4, organization_id=ORG); plan_key=uuid4()
    app.establish(project_id=7,data=EstablishExecutionPlanRequest(expected_plan_version=0,rationale="Human establishes"),actor=actor,idempotency_key=plan_key)
    replay=app.establish(project_id=7,data=EstablishExecutionPlanRequest(expected_plan_version=0,rationale="Human establishes"),actor=actor,idempotency_key=plan_key)
    assert replay.outcome == "success" and replay.plan_version == 1
