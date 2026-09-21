"""Approved Evidence HTTP boundary."""
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, get_db
from app.dependencies.auth import AuthenticatedOrganizationContext, get_current_user_organization_context
from app.dependencies.supporting_file import get_supporting_file_application
from app.exceptions.evidence import EvidenceProtectedNotFound
from app.models.evidence_command import EvidenceActor
from app.repositories.evidence_unit_of_work import SqlAlchemyEvidenceAuthorizationPolicy, SqlAlchemyEvidenceUnitOfWork, SqlAlchemyEvidenceValidator, UtcEvidenceClock
from app.schemas.evidence import EvidenceAvailabilityPageResponse, EvidenceCreate, EvidenceFilter, EvidenceListResponse, EvidenceResponse, LinkEvidenceSupportingFilesRequest, TransitionEvidenceLifecycleRequest
from app.services.evidence_service import EvidenceService
from app.services.evidence_availability_service import EvidenceAvailabilityIncomplete, EvidenceAvailabilityService

router=APIRouter(tags=["Evidence"])
CorrelationId=Annotated[UUID,Header(alias="X-Correlation-ID")]
IdempotencyId=Annotated[UUID,Header(alias="Idempotency-Key")]
@dataclass(frozen=True,slots=True)
class EvidenceApplication: service:EvidenceService; actor:EvidenceActor
def get_evidence_application(db:Session=Depends(get_db),organization:AuthenticatedOrganizationContext=Depends(get_current_user_organization_context)):
    return EvidenceApplication(EvidenceService(uow_factory=lambda:SqlAlchemyEvidenceUnitOfWork(SessionLocal),authorization=SqlAlchemyEvidenceAuthorizationPolicy(db),validator=SqlAlchemyEvidenceValidator(db),clock=UtcEvidenceClock()),EvidenceActor(organization.user.id,organization.organization_id))
@router.post("/evidence",response_model=EvidenceResponse,status_code=status.HTTP_201_CREATED)
def create_evidence(data:EvidenceCreate,correlation_id:CorrelationId,idempotency_id:IdempotencyId,app:EvidenceApplication=Depends(get_evidence_application)): return app.service.create(data=data,actor=app.actor,correlation_id=correlation_id,idempotency_id=idempotency_id)
@router.get("/evidence/{evidence_id}",response_model=EvidenceResponse)
def read_evidence(evidence_id:UUID,app:EvidenceApplication=Depends(get_evidence_application)): return app.service.get(evidence_id,app.actor)
@router.get("/projects/{project_id}/evidence",response_model=EvidenceListResponse)
def list_evidence(project_id:int,page:int=Query(1,ge=1),size:int=Query(20,ge=1,le=100),workspace_id:int|None=Query(None,gt=0),app:EvidenceApplication=Depends(get_evidence_application)):
    return app.service.list(project_id=project_id,filters=EvidenceFilter(workspace_id=workspace_id),page=page,size=size,actor=app.actor)

@router.get("/projects/{project_id}/evidence/availability", response_model=EvidenceAvailabilityPageResponse)
def list_evidence_availability(
    project_id: int, source_cutoff: datetime, workspace_id: int | None = Query(None, gt=0),
    page_size: int = Query(20, ge=1, le=50),
    cursor: str | None = Query(None, min_length=1, max_length=4096),
    db: Session = Depends(get_db),
    organization: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context),
):
    files = get_supporting_file_application(db, organization)
    service = EvidenceAvailabilityService(
        uow_factory=lambda: SqlAlchemyEvidenceUnitOfWork(SessionLocal),
        authorization=SqlAlchemyEvidenceAuthorizationPolicy(db),
        availability_reader=files.service, clock=UtcEvidenceClock(),
    )
    try:
        page = service.list_page(
            actor=EvidenceActor(organization.user.id, organization.organization_id),
            project_id=project_id, workspace_id=workspace_id,
            source_cutoff=source_cutoff, page_size=page_size, cursor=cursor,
        )
    except EvidenceProtectedNotFound as exc:
        raise HTTPException(status_code=404, detail="protected_not_found") from exc
    except EvidenceAvailabilityIncomplete as exc:
        raise HTTPException(status_code=503, detail="availability_traversal_incomplete") from exc
    return EvidenceAvailabilityPageResponse.model_validate(page, from_attributes=True)
@router.post("/evidence/{evidence_id}/lifecycle-transitions",response_model=EvidenceResponse)
def transition_evidence_lifecycle(evidence_id:UUID,data:TransitionEvidenceLifecycleRequest,correlation_id:CorrelationId,idempotency_id:IdempotencyId,app:EvidenceApplication=Depends(get_evidence_application)): return app.service.transition_lifecycle(evidence_id,data,app.actor,correlation_id,idempotency_id)

@router.post("/evidence/{evidence_id}/supporting-files", response_model=EvidenceResponse)
def link_evidence_supporting_files(evidence_id:UUID,data:LinkEvidenceSupportingFilesRequest,correlation_id:CorrelationId,idempotency_id:IdempotencyId,app:EvidenceApplication=Depends(get_evidence_application)):
    return app.service.link_supporting_files(evidence_id,data,app.actor,correlation_id,idempotency_id)
