"""PATCH-055 governed retention HTTP boundary."""
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import StreamingResponse

from app.dependencies.auth import AuthenticatedOrganizationContext, get_current_user_organization_context
from app.dependencies.retention import get_retention_service
from app.schemas.retention import (ApplyRetentionPolicyRequestV1, CreateRetentionExportRequestV1,
    CreateRetentionRecoveryRequestV1, PlaceRetentionHoldRequestV1, RetentionExportResponseV1,
    RetentionRecoveryResponseV1,
    RecordDispositionDecisionRequestV1, ReleaseRetentionHoldRequestV1, RetentionMutationResponseV1,
    RetentionStateResponseV1, EvidenceWorkbenchResponseV1)
from app.services.retention_service import (RetentionConflict, RetentionIndeterminate, RetentionInvalidRequest,
    RetentionNotPermitted, RetentionProtectedNotFound, RetentionService, RetentionUnavailable)

router = APIRouter(tags=["Retention"])
IdempotencyId = Annotated[UUID, Header(alias="Idempotency-Key")]
CorrelationId = Annotated[UUID, Header(alias="X-Correlation-ID")]

@dataclass(frozen=True, slots=True)
class RetentionApplication:
    service: RetentionService
    actor_id: int
    organization_id: UUID

def get_retention_application(
    service: RetentionService = Depends(get_retention_service),
    organization: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context),
) -> RetentionApplication:
    return RetentionApplication(service, organization.user.id, organization.organization_id)

def _translate(exc: Exception) -> HTTPException:
    if isinstance(exc, RetentionProtectedNotFound): return HTTPException(404, detail="protected_not_found")
    if isinstance(exc, RetentionNotPermitted): return HTTPException(403, detail="not_permitted")
    if isinstance(exc, RetentionConflict): return HTTPException(409, detail="conflict")
    if isinstance(exc, RetentionInvalidRequest): return HTTPException(422, detail="invalid_request")
    if isinstance(exc, RetentionUnavailable): return HTTPException(503, detail="unavailable")
    if isinstance(exc, RetentionIndeterminate): return HTTPException(503, detail="unavailable")
    raise exc

@router.get("/projects/{project_id}/evidence-workbench", response_model=EvidenceWorkbenchResponseV1)
def get_evidence_workbench(project_id: int, workspace_id: int | None = None, limit: int = 20, app: RetentionApplication = Depends(get_retention_application)):
    try:
        return app.service.get_evidence_workbench(organization_id=app.organization_id, actor_id=app.actor_id, project_id=project_id, workspace_id=workspace_id, limit=limit)
    except Exception as exc: raise _translate(exc) from exc

@router.get("/retention/{subject_kind}/{subject_id}", response_model=RetentionStateResponseV1)
def get_retention_state(subject_kind: str, subject_id: UUID, app: RetentionApplication = Depends(get_retention_application)):
    try:
        return app.service.get_state(organization_id=app.organization_id, actor_id=app.actor_id, subject_kind=subject_kind, subject_id=subject_id)
    except Exception as exc: raise _translate(exc) from exc

@router.post("/retention/{subject_kind}/{subject_id}/policy", response_model=RetentionMutationResponseV1)
def apply_retention_policy(subject_kind: str, subject_id: UUID, data: ApplyRetentionPolicyRequestV1,
    idempotency_key: IdempotencyId, correlation_id: CorrelationId, app: RetentionApplication = Depends(get_retention_application)):
    try:
        return app.service.apply_policy(organization_id=app.organization_id, actor_id=app.actor_id, subject_kind=subject_kind,
            subject_id=subject_id, data=data, idempotency_key=idempotency_key, correlation_id=correlation_id)
    except Exception as exc: raise _translate(exc) from exc

@router.post("/retention/{subject_kind}/{subject_id}/holds", response_model=RetentionMutationResponseV1)
def place_retention_hold(subject_kind: str, subject_id: UUID, data: PlaceRetentionHoldRequestV1,
    idempotency_key: IdempotencyId, correlation_id: CorrelationId, app: RetentionApplication = Depends(get_retention_application)):
    try:
        return app.service.place_hold(organization_id=app.organization_id, actor_id=app.actor_id, subject_kind=subject_kind,
            subject_id=subject_id, data=data, idempotency_key=idempotency_key, correlation_id=correlation_id, authority_context="human")
    except Exception as exc: raise _translate(exc) from exc

@router.post("/retention/{subject_kind}/{subject_id}/holds/{hold_id}/release", response_model=RetentionMutationResponseV1)
def release_retention_hold(subject_kind: str, subject_id: UUID, hold_id: UUID, data: ReleaseRetentionHoldRequestV1,
    idempotency_key: IdempotencyId, correlation_id: CorrelationId, app: RetentionApplication = Depends(get_retention_application)):
    # Stable hold identity is path-bound; service resolves the current active revision under the subject.
    try:
        return app.service.release_hold(organization_id=app.organization_id, actor_id=app.actor_id, subject_kind=subject_kind,
            subject_id=subject_id, hold_id=hold_id, data=data, idempotency_key=idempotency_key, correlation_id=correlation_id, authority_context="human")
    except HTTPException: raise
    except Exception as exc: raise _translate(exc) from exc

@router.post("/retention/{subject_kind}/{subject_id}/disposition-decisions", response_model=RetentionMutationResponseV1)
def record_retention_disposition(subject_kind: str, subject_id: UUID, data: RecordDispositionDecisionRequestV1,
    idempotency_key: IdempotencyId, correlation_id: CorrelationId, app: RetentionApplication = Depends(get_retention_application)):
    try:
        return app.service.record_disposition_decision(organization_id=app.organization_id, actor_id=app.actor_id,
            subject_kind=subject_kind, subject_id=subject_id, data=data, idempotency_key=idempotency_key, correlation_id=correlation_id)
    except Exception as exc: raise _translate(exc) from exc


@router.post("/retention-exports", response_model=RetentionExportResponseV1, status_code=status.HTTP_202_ACCEPTED)
def create_retention_export(data: CreateRetentionExportRequestV1, idempotency_key: IdempotencyId, correlation_id: CorrelationId, app: RetentionApplication = Depends(get_retention_application)):
    try:
        return app.service.create_export(organization_id=app.organization_id, actor_id=app.actor_id, data=data, idempotency_key=idempotency_key, correlation_id=correlation_id)
    except Exception as exc: raise _translate(exc) from exc

@router.get("/retention-exports/{export_id}", response_model=RetentionExportResponseV1)
def get_retention_export(export_id: UUID, app: RetentionApplication = Depends(get_retention_application)):
    try:
        return app.service.get_export_status(organization_id=app.organization_id, actor_id=app.actor_id, export_id=export_id)
    except Exception as exc: raise _translate(exc) from exc

@router.get("/retention-exports/{export_id}/content")
def get_retention_export_content(export_id: UUID, app: RetentionApplication = Depends(get_retention_application)):
    try:
        stream = app.service.open_export_content(organization_id=app.organization_id, actor_id=app.actor_id, export_id=export_id)
        def chunks():
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                yield chunk
        return StreamingResponse(chunks(), media_type="application/zip", headers={
            "Content-Disposition": f'attachment; filename="retention-export-{export_id}.zip"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
        })
    except Exception as exc: raise _translate(exc) from exc

@router.post("/retention-recoveries", response_model=RetentionRecoveryResponseV1, status_code=status.HTTP_202_ACCEPTED)
def create_retention_recovery(data: CreateRetentionRecoveryRequestV1, idempotency_key: IdempotencyId, correlation_id: CorrelationId, app: RetentionApplication = Depends(get_retention_application)):
    try:
        return app.service.create_recovery(organization_id=app.organization_id, actor_id=app.actor_id, data=data, idempotency_key=idempotency_key, correlation_id=correlation_id)
    except Exception as exc: raise _translate(exc) from exc

@router.get("/retention-recoveries/{recovery_id}", response_model=RetentionRecoveryResponseV1)
def get_retention_recovery(recovery_id: UUID, app: RetentionApplication = Depends(get_retention_application)):
    try:
        return app.service.get_recovery_status(organization_id=app.organization_id, actor_id=app.actor_id, recovery_id=recovery_id)
    except Exception as exc: raise _translate(exc) from exc
