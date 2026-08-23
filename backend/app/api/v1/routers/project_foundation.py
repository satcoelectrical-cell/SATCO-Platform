from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from app.dependencies.project_foundation import ProjectFoundationApplication, get_project_foundation_application
from app.enums.project_foundation import ProjectInputSourceKind
from app.schemas.project_foundation import (
    CreateProjectInputRequest, PutProjectFoundationRequest, ReorderProjectInputsRequest,
    TransitionProjectInputRequest, TransitionProjectStageRequest, UpdateProjectInputRequest,
)


class ProjectFoundationRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()
        async def handler(request: Request):
            try:
                return await original(request)
            except RequestValidationError:
                return JSONResponse(status_code=422, content={"outcome": "invalid_request"})
        return handler


router = APIRouter(tags=["Project Foundation"], route_class=ProjectFoundationRoute)


@router.get("/projects/{project_id}/foundation")
def get_project_foundation(project_id: int, app: ProjectFoundationApplication = Depends(get_project_foundation_application)):
    return app.service.get(project_id=project_id, actor=app.actor)


@router.put("/projects/{project_id}/foundation")
def put_project_foundation(project_id: int, data: PutProjectFoundationRequest, app: ProjectFoundationApplication = Depends(get_project_foundation_application)):
    return app.service.put(project_id=project_id, data=data, actor=app.actor)


@router.post("/projects/{project_id}/foundation/inputs")
def create_project_input(project_id: int, data: CreateProjectInputRequest, app: ProjectFoundationApplication = Depends(get_project_foundation_application)):
    return app.service.create_input(project_id=project_id, data=data, actor=app.actor)


@router.post("/projects/{project_id}/foundation/inputs/reorder")
def reorder_project_inputs(project_id: int, data: ReorderProjectInputsRequest, app: ProjectFoundationApplication = Depends(get_project_foundation_application)):
    return app.service.reorder_inputs(project_id=project_id, data=data, actor=app.actor)


@router.put("/projects/{project_id}/foundation/inputs/{input_id}")
def update_project_input(project_id: int, input_id: UUID, data: UpdateProjectInputRequest, app: ProjectFoundationApplication = Depends(get_project_foundation_application)):
    return app.service.update_input(project_id=project_id, input_id=input_id, data=data, actor=app.actor)


@router.post("/projects/{project_id}/foundation/inputs/{input_id}/transitions")
def transition_project_input(project_id: int, input_id: UUID, data: TransitionProjectInputRequest, app: ProjectFoundationApplication = Depends(get_project_foundation_application)):
    return app.service.transition_input(project_id=project_id, input_id=input_id, data=data, actor=app.actor)


@router.post("/projects/{project_id}/foundation/stage-transitions")
def transition_project_stage(project_id: int, data: TransitionProjectStageRequest, app: ProjectFoundationApplication = Depends(get_project_foundation_application)):
    return app.service.transition_stage(project_id=project_id, data=data, actor=app.actor)


@router.get("/projects/{project_id}/foundation/source-candidates")
def list_project_input_source_candidates(
    project_id: int, kind: ProjectInputSourceKind = Query(...),
    workspace_id: int | None = Query(None, gt=0), limit: int = Query(50, ge=1, le=50),
    app: ProjectFoundationApplication = Depends(get_project_foundation_application),
):
    return app.service.list_source_candidates(project_id=project_id, kind=kind, workspace_id=workspace_id, limit=limit, actor=app.actor)
