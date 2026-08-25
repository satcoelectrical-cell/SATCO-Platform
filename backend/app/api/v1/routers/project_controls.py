"""Thin authenticated PATCH-047 Project Control transport."""
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from app.dependencies.project_control import ProjectControlApplication, get_project_control_application
from app.schemas.project_control import (
    ChangeCommand, ConfirmImpactCommand, ControlTransitionCommand, DecisionCommand,
    ImpactCommand, IssueCommand, RiskCommand, SupersedeChangeCommand,
)


class ProjectControlRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()
        async def handler(request: Request):
            try:
                return await original(request)
            except RequestValidationError:
                return JSONResponse(status_code=422, content={"outcome": "invalid_request"})
        return handler


router = APIRouter(prefix="/projects/{project_id}/controls", tags=["Project Controls"], route_class=ProjectControlRoute)
_kinds = frozenset({"risk", "issue", "decision", "change"})


def _result(result):
    outcome = getattr(result, "outcome", "success")
    status = {"protected_not_found": 404, "invalid_request": 422, "version_conflict": 409, "idempotency_conflict": 409, "unavailable": 503}.get(outcome)
    return JSONResponse(status_code=status, content=result.model_dump(mode="json")) if status else result


def _kind_or_invalid(kind):
    canonical = kind[:-1] if kind.endswith("s") else kind
    return canonical if canonical in _kinds else None


@router.get("/{kind}")
def list_controls(project_id: int, kind: str, app: ProjectControlApplication = Depends(get_project_control_application)):
    canonical = _kind_or_invalid(kind)
    return _result(app.service.list(kind=canonical or "unknown", project_id=project_id, actor=app.actor))


@router.get("/{kind}/{control_id}")
def get_control(project_id: int, kind: str, control_id: UUID, app: ProjectControlApplication = Depends(get_project_control_application)):
    canonical = _kind_or_invalid(kind)
    return _result(app.service.get(kind=canonical or "unknown", control_id=control_id, project_id=project_id, actor=app.actor))


@router.get("/{kind}/{control_id}/history")
def control_history(project_id: int, kind: str, control_id: UUID, app: ProjectControlApplication = Depends(get_project_control_application)):
    canonical = _kind_or_invalid(kind)
    return _result(app.service.history(kind=canonical or "unknown", control_id=control_id, project_id=project_id, actor=app.actor))


@router.post("/risks")
def create_risk(project_id: int, data: RiskCommand, idempotency_key: UUID = Header(alias="Idempotency-Key"), app: ProjectControlApplication = Depends(get_project_control_application)):
    return _result(app.service.create_risk(project_id=project_id, data=data, actor=app.actor, idempotency_key=idempotency_key))


@router.post("/issues")
def create_issue(project_id: int, data: IssueCommand, idempotency_key: UUID = Header(alias="Idempotency-Key"), app: ProjectControlApplication = Depends(get_project_control_application)):
    return _result(app.service.create_issue(project_id=project_id, data=data, actor=app.actor, idempotency_key=idempotency_key))


@router.post("/decisions")
def create_decision(project_id: int, data: DecisionCommand, idempotency_key: UUID = Header(alias="Idempotency-Key"), app: ProjectControlApplication = Depends(get_project_control_application)):
    return _result(app.service.create_decision(project_id=project_id, data=data, actor=app.actor, idempotency_key=idempotency_key))


@router.post("/changes")
def create_change(project_id: int, data: ChangeCommand, idempotency_key: UUID = Header(alias="Idempotency-Key"), app: ProjectControlApplication = Depends(get_project_control_application)):
    return _result(app.service.create_change(project_id=project_id, data=data, actor=app.actor, idempotency_key=idempotency_key))


@router.post("/decisions/{control_id}/successors")
def create_decision_successor(project_id: int, control_id: UUID, data: DecisionCommand, idempotency_key: UUID = Header(alias="Idempotency-Key"), app: ProjectControlApplication = Depends(get_project_control_application)):
    return _result(app.service.create_decision_successor(decision_id=control_id, data=data, actor=app.actor, idempotency_key=idempotency_key, project_id=project_id))


@router.post("/changes/{control_id}/successors")
def create_change_successor(project_id: int, control_id: UUID, data: ChangeCommand, idempotency_key: UUID = Header(alias="Idempotency-Key"), app: ProjectControlApplication = Depends(get_project_control_application)):
    return _result(app.service.create_change_successor(change_id=control_id, data=data, actor=app.actor, idempotency_key=idempotency_key, project_id=project_id))


@router.post("/changes/{control_id}/supersessions")
def supersede_change(project_id: int, control_id: UUID, data: SupersedeChangeCommand, idempotency_key: UUID = Header(alias="Idempotency-Key"), app: ProjectControlApplication = Depends(get_project_control_application)):
    return _result(app.service.supersede_change(predecessor_id=control_id, data=data, actor=app.actor, idempotency_key=idempotency_key, project_id=project_id))


@router.post("/changes/{change_id}/impacts")
def create_change_impact(project_id: int, change_id: UUID, data: ImpactCommand, idempotency_key: UUID = Header(alias="Idempotency-Key"), app: ProjectControlApplication = Depends(get_project_control_application)):
    if data.change_id != change_id:
        return JSONResponse(status_code=422, content={"outcome": "invalid_request"})
    return _result(app.service.create_change_impact(data=data, actor=app.actor, idempotency_key=idempotency_key, project_id=project_id))


@router.post("/impacts/{impact_id}/confirmations")
def confirm_change_impact(project_id: int, impact_id: UUID, data: ConfirmImpactCommand, idempotency_key: UUID = Header(alias="Idempotency-Key"), app: ProjectControlApplication = Depends(get_project_control_application)):
    return _result(app.service.confirm_change_impact(impact_id=impact_id, data=data, actor=app.actor, idempotency_key=idempotency_key, project_id=project_id))


@router.post("/{kind}/{control_id}/transitions")
def transition_control(project_id: int, kind: str, control_id: UUID, data: ControlTransitionCommand, idempotency_key: UUID = Header(alias="Idempotency-Key"), app: ProjectControlApplication = Depends(get_project_control_application)):
    canonical = _kind_or_invalid(kind)
    method = getattr(app.service, f"transition_{canonical}", None) if canonical else None
    return _result(method(**{f"{canonical}_id": control_id, "data": data, "actor": app.actor, "idempotency_key": idempotency_key, "project_id": project_id}) if method else app.service.get(kind="unknown", control_id=control_id, actor=app.actor))
