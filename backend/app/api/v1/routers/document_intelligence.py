"""Protected customer API for Document Intelligence."""

from typing import Annotated
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from fastapi.routing import APIRoute

from app.dependencies.document_intelligence import (
    DocumentIntelligenceApplication,
    DocumentIntelligenceSourceApplication,
    get_document_intelligence_application,
    get_document_intelligence_source_application,
    process_document_analysis_job,
)
from app.schemas.document_intelligence import (
    CandidateReviewRequest,
    DocumentAnalysisCreate,
    DocumentAnalysisListResponse,
    DocumentAnalysisRetryRequest,
    DocumentAnalysisSummary,
    EngineeringCandidateListResponse,
    EngineeringCandidate,
    DocumentPromotionRequest,
    DocumentPromotionResponse,
    DocumentCorrelationRequest,
    DocumentCorrelationEvaluation,
    DocumentCorrelationPage,
    DocumentFindingPage,
    DocumentReportDraftRequest,
    DocumentReportDraftResponse,
)
from app.services.document_intelligence_service import (
    DocumentIntelligenceConflict,
    DocumentIntelligenceInvalidRequest,
    DocumentIntelligenceProtectedNotFound,
    DocumentIntelligenceUnavailable,
)
from app.api.v1.routers.technical_reports import (
    TechnicalReportApplication,
    get_technical_report_application,
)


def _outcome(code: str, status_code: int):
    return JSONResponse(status_code=status_code, content={"outcome": code})


class DocumentIntelligenceRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()

        async def handler(request: Request):
            try:
                return await original(request)
            except RequestValidationError:
                return _outcome("invalid_request", 422)
            except DocumentIntelligenceProtectedNotFound:
                return _outcome("protected_not_found", 404)
            except DocumentIntelligenceInvalidRequest:
                return _outcome("invalid_request", 422)
            except DocumentIntelligenceConflict:
                return _outcome("version_conflict", 409)
            except DocumentIntelligenceUnavailable:
                return _outcome("unavailable", 503)

        return handler


router = APIRouter(tags=["Document Intelligence"], route_class=DocumentIntelligenceRoute)
IdempotencyId = Annotated[UUID, Header(alias="Idempotency-Key")]
CorrelationId = Annotated[UUID, Header(alias="X-Correlation-ID")]


@router.post(
    "/projects/{project_id}/document-analyses",
    response_model=DocumentAnalysisSummary,
    status_code=201,
)
def create_analysis(
    project_id: int, data: DocumentAnalysisCreate,
    idempotency_id: IdempotencyId, correlation_id: CorrelationId,
    background_tasks: BackgroundTasks,
    app: DocumentIntelligenceApplication = Depends(
        get_document_intelligence_application
    ),
):
    result = app.service.create(
        project_id=project_id, data=data, user=app.context.user,
        organization_id=app.context.organization_id,
        idempotency_id=idempotency_id, correlation_id=correlation_id,
    )
    background_tasks.add_task(process_document_analysis_job, result.analysis_run_id)
    return result


@router.get(
    "/projects/{project_id}/document-analyses",
    response_model=DocumentAnalysisListResponse,
)
def list_analyses(
    project_id: int, workspace_id: int | None = Query(None, gt=0),
    app: DocumentIntelligenceApplication = Depends(
        get_document_intelligence_application
    ),
):
    return app.service.list(
        project_id=project_id, workspace_id=workspace_id,
        user=app.context.user, organization_id=app.context.organization_id,
    )


@router.get(
    "/projects/{project_id}/document-analyses/{run_id}",
    response_model=DocumentAnalysisSummary,
)
def get_analysis(
    project_id: int, run_id: UUID,
    app: DocumentIntelligenceApplication = Depends(
        get_document_intelligence_application
    ),
):
    return app.service.get(
        project_id=project_id, run_id=run_id, user=app.context.user,
        organization_id=app.context.organization_id,
    )


@router.get(
    "/projects/{project_id}/document-analyses/{run_id}/candidates",
    response_model=EngineeringCandidateListResponse,
)
def list_candidates(
    project_id: int, run_id: UUID,
    app: DocumentIntelligenceApplication = Depends(
        get_document_intelligence_application
    ),
):
    return app.service.list_candidates(
        project_id=project_id, run_id=run_id, user=app.context.user,
        organization_id=app.context.organization_id,
    )


@router.post(
    "/projects/{project_id}/document-analyses/{run_id}/candidates/{candidate_id}/reviews",
    response_model=EngineeringCandidate,
)
def review_candidate(
    project_id: int, run_id: UUID, candidate_id: UUID,
    data: CandidateReviewRequest,
    idempotency_id: IdempotencyId, correlation_id: CorrelationId,
    app: DocumentIntelligenceApplication = Depends(
        get_document_intelligence_application
    ),
):
    return app.service.review_candidate(
        project_id=project_id, run_id=run_id, candidate_id=candidate_id,
        data=data, user=app.context.user,
        organization_id=app.context.organization_id,
        idempotency_id=idempotency_id, correlation_id=correlation_id,
    )


@router.post(
    "/projects/{project_id}/document-analyses/{run_id}/candidates/{candidate_id}/promotions",
    response_model=DocumentPromotionResponse,
    status_code=201,
)
def promote_candidate(
    project_id: int, run_id: UUID, candidate_id: UUID,
    data: DocumentPromotionRequest,
    idempotency_id: IdempotencyId, correlation_id: CorrelationId,
    app: DocumentIntelligenceApplication = Depends(
        get_document_intelligence_application
    ),
):
    return app.service.promote_candidate(
        project_id=project_id, run_id=run_id, candidate_id=candidate_id,
        data=data, user=app.context.user,
        organization_id=app.context.organization_id,
        idempotency_id=idempotency_id, correlation_id=correlation_id,
    )


@router.post(
    "/projects/{project_id}/document-correlations",
    response_model=DocumentCorrelationEvaluation,
    status_code=201,
)
def correlate_documents(
    project_id: int, data: DocumentCorrelationRequest,
    idempotency_id: IdempotencyId, correlation_id: CorrelationId,
    app: DocumentIntelligenceApplication = Depends(
        get_document_intelligence_application
    ),
):
    return app.service.correlate_documents(
        project_id=project_id, data=data, user=app.context.user,
        organization_id=app.context.organization_id,
        idempotency_id=idempotency_id, correlation_id=correlation_id,
    )


@router.get(
    "/projects/{project_id}/document-correlations",
    response_model=DocumentCorrelationPage,
)
def list_document_correlations(
    project_id: int, workspace_id: int | None = Query(None, gt=0),
    app: DocumentIntelligenceApplication = Depends(
        get_document_intelligence_application
    ),
):
    return app.service.list_correlations(
        project_id=project_id, workspace_id=workspace_id,
        user=app.context.user, organization_id=app.context.organization_id,
    )


@router.get(
    "/projects/{project_id}/document-findings",
    response_model=DocumentFindingPage,
)
def list_document_findings(
    project_id: int, workspace_id: int | None = Query(None, gt=0),
    app: DocumentIntelligenceApplication = Depends(
        get_document_intelligence_application
    ),
):
    return app.service.list_findings(
        project_id=project_id, workspace_id=workspace_id,
        user=app.context.user, organization_id=app.context.organization_id,
    )


@router.post(
    "/projects/{project_id}/document-findings/report-drafts",
    response_model=DocumentReportDraftResponse,
    status_code=201,
)
def create_document_report_draft(
    project_id: int, data: DocumentReportDraftRequest,
    idempotency_id: IdempotencyId, correlation_id: CorrelationId,
    app: DocumentIntelligenceApplication = Depends(
        get_document_intelligence_application
    ),
    report_app: TechnicalReportApplication = Depends(
        get_technical_report_application
    ),
):
    return app.service.create_document_report_draft(
        project_id=project_id, data=data, user=app.context.user,
        organization_id=app.context.organization_id,
        idempotency_id=idempotency_id, correlation_id=correlation_id,
        report_service=report_app.service, report_actor=report_app.actor,
    )


@router.get("/projects/{project_id}/document-analyses/{run_id}/source")
def open_analysis_source(
    project_id: int, run_id: UUID,
    app: DocumentIntelligenceSourceApplication = Depends(
        get_document_intelligence_source_application
    ),
):
    run, byte_size, stream = app.service.open_source(
        project_id=project_id, run_id=run_id, user=app.context.user,
        organization_id=app.context.organization_id, objects=app.objects,
    )
    return StreamingResponse(
        stream,
        media_type="application/pdf",
        headers={
            "Content-Length": str(byte_size),
            "Content-Disposition": (
                "inline; filename*=UTF-8''" + quote(run.safe_filename, safe="")
            ),
            "ETag": f'"sha256:{run.source_content_digest}"',
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "sandbox",
        },
    )


@router.post(
    "/projects/{project_id}/document-analyses/{run_id}/retries",
    response_model=DocumentAnalysisSummary,
)
def retry_analysis(
    project_id: int, run_id: UUID, data: DocumentAnalysisRetryRequest,
    idempotency_id: IdempotencyId, correlation_id: CorrelationId,
    background_tasks: BackgroundTasks,
    app: DocumentIntelligenceApplication = Depends(
        get_document_intelligence_application
    ),
):
    result = app.service.retry(
        project_id=project_id, run_id=run_id,
        expected_version=data.expected_version, user=app.context.user,
        organization_id=app.context.organization_id,
        idempotency_id=idempotency_id, correlation_id=correlation_id,
    )
    background_tasks.add_task(process_document_analysis_job, result.analysis_run_id)
    return result
