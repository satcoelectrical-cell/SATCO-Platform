"""Approved Evidence HTTP boundary."""
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, get_db
from app.dependencies.auth import AuthenticatedOrganizationContext, get_current_user_organization_context
from app.models.evidence_command import EvidenceActor
from app.repositories.evidence_unit_of_work import SqlAlchemyEvidenceAuthorizationPolicy, SqlAlchemyEvidenceUnitOfWork, SqlAlchemyEvidenceValidator, UtcEvidenceClock
from app.schemas.evidence import EvidenceCreate, EvidenceFilter, EvidenceListResponse, EvidenceResponse, TransitionEvidenceLifecycleRequest
from app.services.evidence_service import EvidenceService

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
@router.post("/evidence/{evidence_id}/lifecycle-transitions",response_model=EvidenceResponse)
def transition_evidence_lifecycle(evidence_id:UUID,data:TransitionEvidenceLifecycleRequest,correlation_id:CorrelationId,idempotency_id:IdempotencyId,app:EvidenceApplication=Depends(get_evidence_application)): return app.service.transition_lifecycle(evidence_id,data,app.actor,correlation_id,idempotency_id)
