from uuid import UUID, uuid4

from app.schemas.engineering_execution_plan import EstablishExecutionPlanRequest, ExecutionActor
from test_execution_plan_service import ORG, Foundation, Repository, Uow, Authorization
from app.services.engineering_execution_plan_service import EngineeringExecutionPlanService
from types import SimpleNamespace


def test_idempotency_fingerprint_conflict_does_not_commit_second_mutation():
    repository=Repository(); uow=Uow(repository); project=SimpleNamespace(id=7, organization_id=ORG, status="in_progress", owner_id=4, primary_assignee_id=None)
    service=EngineeringExecutionPlanService(uow_factory=lambda:uow, authorization=Authorization(project), foundation=Foundation()); actor=ExecutionActor(actor_id=4,organization_id=ORG); key=uuid4()
    assert service.establish(project_id=7,data=EstablishExecutionPlanRequest(expected_plan_version=0,rationale="First Human rationale"),actor=actor,idempotency_key=key).outcome == "success"
    conflict=service.establish(project_id=7,data=EstablishExecutionPlanRequest(expected_plan_version=0,rationale="Different Human rationale"),actor=actor,idempotency_key=key)
    assert conflict.outcome == "idempotency_conflict" and len(repository.idempotency) == 1
    stored = repository.idempotency[0].replay_json
    assert stored["schema"] == "execution.idempotency.v1" and stored["operation"] == "establish_plan"
    assert "rationale" not in str(stored) and stored["result"]["outcome"] == "success"
