from types import SimpleNamespace
from uuid import uuid4
from pathlib import Path

from app.schemas.engineering_execution_plan import EstablishExecutionPlanRequest, ExecutionActor
from app.services.engineering_execution_plan_service import EngineeringExecutionPlanService
from test_execution_plan_service import ORG, Repository, Uow


class DenyAuthorization:
    def get_project(self, **kwargs): return SimpleNamespace(id=7, organization_id=ORG, status="in_progress", owner_id=4, primary_assignee_id=None)
    def can_read(self, **kwargs): return False
    def can_mutate(self, **kwargs): return False


class NeverFoundation:
    def is_established(self, **kwargs): raise AssertionError("authorization must precede Foundation disclosure")


def test_denied_mutation_is_payload_free_and_does_not_read_foundation():
    service=EngineeringExecutionPlanService(uow_factory=lambda:Uow(Repository()),authorization=DenyAuthorization(),foundation=NeverFoundation())
    result=service.establish(project_id=7,data=EstablishExecutionPlanRequest(expected_plan_version=0,rationale="Human rationale"),actor=ExecutionActor(actor_id=4,organization_id=ORG),idempotency_key=uuid4())
    assert result.model_dump() == {"outcome":"protected_not_found"}


def test_transport_is_thin_and_owns_no_session_repository_or_policy():
    source = Path(__file__).parents[1].joinpath("app/api/v1/routers/engineering_execution_plan.py").read_text()
    forbidden = ("sqlalchemy", "Session", "repository", "unit_of_work", "SqlAlchemyExecutionPlanAuthorization")
    assert not any(value in source for value in forbidden)
    assert "get_engineering_execution_plan_application" in source
