from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from app.dependencies.engineering_execution_plan import EngineeringExecutionPlanApplication, get_engineering_execution_plan_application
from app.schemas.engineering_execution_plan import (
    CreateExecutionActivityRequest, CreateExecutionMilestoneRequest, EstablishExecutionPlanRequest,
    ReplaceExecutionDependenciesRequest, TransitionExecutionActivityRequest,
    UpdateExecutionActivityRequest, UpdateExecutionMilestoneRequest,
)


class ExecutionPlanRoute(APIRoute):
    """Collapse malformed transport input to the accepted closed outcome."""
    def get_route_handler(self):
        original = super().get_route_handler()
        async def handler(request: Request):
            try:
                return await original(request)
            except RequestValidationError:
                return JSONResponse(status_code=422, content={"outcome": "invalid_request"})
        return handler


router = APIRouter(prefix="/projects/{project_id}/execution-plan", tags=["Engineering Execution Plan"], route_class=ExecutionPlanRoute)


def _result(result):
    outcome = getattr(result, "outcome", "success")
    statuses = {"protected_not_found": 404, "invalid_request": 422, "version_conflict": 409, "idempotency_conflict": 409, "unavailable": 503}
    if outcome in statuses:
        return JSONResponse(status_code=statuses[outcome], content=result.model_dump(mode="json"))
    return result


@router.get("")
def get_execution_plan(project_id: int, app: EngineeringExecutionPlanApplication = Depends(get_engineering_execution_plan_application)):
    return _result(app.service.get(project_id=project_id, actor=app.actor))


@router.put("")
def establish_execution_plan(project_id: int, data: EstablishExecutionPlanRequest, idempotency_key: UUID = Header(alias="Idempotency-Key"), app: EngineeringExecutionPlanApplication = Depends(get_engineering_execution_plan_application)):
    return _result(app.service.establish(project_id=project_id, data=data, actor=app.actor, idempotency_key=idempotency_key))


@router.post("/activities")
def create_execution_activity(project_id: int, data: CreateExecutionActivityRequest, idempotency_key: UUID = Header(alias="Idempotency-Key"), app: EngineeringExecutionPlanApplication = Depends(get_engineering_execution_plan_application)):
    return _result(app.service.create_activity(project_id=project_id, data=data, actor=app.actor, idempotency_key=idempotency_key))


@router.put("/activities/{activity_id}")
def update_execution_activity(project_id: int, activity_id: UUID, data: UpdateExecutionActivityRequest, idempotency_key: UUID = Header(alias="Idempotency-Key"), app: EngineeringExecutionPlanApplication = Depends(get_engineering_execution_plan_application)):
    return _result(app.service.update_activity(project_id=project_id, activity_id=activity_id, data=data, actor=app.actor, idempotency_key=idempotency_key))


@router.post("/activities/{activity_id}/transitions")
def transition_execution_activity(project_id: int, activity_id: UUID, data: TransitionExecutionActivityRequest, idempotency_key: UUID = Header(alias="Idempotency-Key"), app: EngineeringExecutionPlanApplication = Depends(get_engineering_execution_plan_application)):
    return _result(app.service.transition_activity(project_id=project_id, activity_id=activity_id, data=data, actor=app.actor, idempotency_key=idempotency_key))


@router.put("/dependencies")
def replace_execution_dependencies(project_id: int, data: ReplaceExecutionDependenciesRequest, idempotency_key: UUID = Header(alias="Idempotency-Key"), app: EngineeringExecutionPlanApplication = Depends(get_engineering_execution_plan_application)):
    return _result(app.service.replace_dependencies(project_id=project_id, data=data, actor=app.actor, idempotency_key=idempotency_key))


@router.post("/milestones")
def create_execution_milestone(project_id: int, data: CreateExecutionMilestoneRequest, idempotency_key: UUID = Header(alias="Idempotency-Key"), app: EngineeringExecutionPlanApplication = Depends(get_engineering_execution_plan_application)):
    return _result(app.service.create_milestone(project_id=project_id, data=data, actor=app.actor, idempotency_key=idempotency_key))


@router.put("/milestones/{milestone_id}")
def update_execution_milestone(project_id: int, milestone_id: UUID, data: UpdateExecutionMilestoneRequest, idempotency_key: UUID = Header(alias="Idempotency-Key"), app: EngineeringExecutionPlanApplication = Depends(get_engineering_execution_plan_application)):
    return _result(app.service.update_milestone(project_id=project_id, milestone_id=milestone_id, data=data, actor=app.actor, idempotency_key=idempotency_key))
