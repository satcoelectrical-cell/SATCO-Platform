from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from app.dependencies.engineering_deliverable import EngineeringDeliverableApplication, get_engineering_deliverable_application
from app.schemas.engineering_deliverable import CreateDeliverableRequest, CreateRevisionRequest, TransitionRevisionRequest, UpdateDeliverableRequest


class DeliverableRoute(APIRoute):
    def get_route_handler(self):
        original=super().get_route_handler()
        async def handler(request:Request):
            try:return await original(request)
            except (RequestValidationError,ValueError): return JSONResponse(status_code=422,content={"outcome":"invalid_request"})
        return handler


router=APIRouter(prefix="/projects/{project_id}/deliverables",tags=["Engineering Deliverables"],route_class=DeliverableRoute)
def _result(result):
    status={"protected_not_found":404,"invalid_request":422,"version_conflict":409,"idempotency_conflict":409,"unavailable":503}.get(getattr(result,"outcome","success"))
    return JSONResponse(status_code=status,content=result.model_dump(mode="json")) if status else result

@router.get("")
def list_deliverables(project_id:int,app:EngineeringDeliverableApplication=Depends(get_engineering_deliverable_application)): return _result(app.service.list(project_id=project_id,actor=app.actor))
@router.post("")
def create_deliverable(project_id:int,data:CreateDeliverableRequest,idempotency_key:UUID=Header(alias="Idempotency-Key"),app:EngineeringDeliverableApplication=Depends(get_engineering_deliverable_application)): return _result(app.service.create(project_id=project_id,data=data,actor=app.actor,idempotency_key=idempotency_key))
@router.get("/{deliverable_id}")
def get_deliverable(project_id:int,deliverable_id:UUID,app:EngineeringDeliverableApplication=Depends(get_engineering_deliverable_application)): return _result(app.service.get(project_id=project_id,deliverable_id=deliverable_id,actor=app.actor))
@router.put("/{deliverable_id}")
def update_deliverable(project_id:int,deliverable_id:UUID,data:UpdateDeliverableRequest,idempotency_key:UUID=Header(alias="Idempotency-Key"),app:EngineeringDeliverableApplication=Depends(get_engineering_deliverable_application)): return _result(app.service.update(project_id=project_id,deliverable_id=deliverable_id,data=data,actor=app.actor,idempotency_key=idempotency_key))
@router.get("/{deliverable_id}/revisions")
def revision_history(project_id:int,deliverable_id:UUID,app:EngineeringDeliverableApplication=Depends(get_engineering_deliverable_application)): return _result(app.service.history(project_id=project_id,deliverable_id=deliverable_id,actor=app.actor))
@router.post("/{deliverable_id}/revisions")
def create_revision(project_id:int,deliverable_id:UUID,data:CreateRevisionRequest,idempotency_key:UUID=Header(alias="Idempotency-Key"),app:EngineeringDeliverableApplication=Depends(get_engineering_deliverable_application)): return _result(app.service.create_revision(project_id=project_id,deliverable_id=deliverable_id,data=data,actor=app.actor,idempotency_key=idempotency_key))
@router.post("/{deliverable_id}/revisions/{revision_id}/transitions")
def transition_revision(project_id:int,deliverable_id:UUID,revision_id:UUID,data:TransitionRevisionRequest,idempotency_key:UUID=Header(alias="Idempotency-Key"),app:EngineeringDeliverableApplication=Depends(get_engineering_deliverable_application)): return _result(app.service.transition_revision(project_id=project_id,deliverable_id=deliverable_id,revision_id=revision_id,data=data,actor=app.actor,idempotency_key=idempotency_key))
