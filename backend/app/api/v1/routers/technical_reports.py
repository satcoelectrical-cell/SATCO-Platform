"""Thin HTTP transport and request-scoped composition for PATCH-032."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from app.core.database import SessionLocal
from app.dependencies.auth import AuthenticatedOrganizationContext, get_current_user_organization_context
from app.enums.technical_report import TechnicalReportLifecycle, TechnicalReportPurpose
from app.exceptions.technical_report import (
    TechnicalReportAcceptedImmutable, TechnicalReportAssistantUnavailable,
    TechnicalReportAuthorizationDenied, TechnicalReportException,
    TechnicalReportHistoricalBasisIncomplete, TechnicalReportIdempotencyConflict,
    TechnicalReportIntegrityMismatch, TechnicalReportInvalidLifecycle,
    TechnicalReportInvalidLineage, TechnicalReportValidationError,
    TechnicalReportVersionConflict,
)
from app.models.technical_report_command import (
    AcceptExactTechnicalReportDraft, AcceptanceConfirmation,
    CreateTechnicalReportDraft, CreateTechnicalReportSuccessor,
    PreliminaryQualification, ReviseTechnicalReportDraft, TechnicalReportActor,
    TechnicalReportCommandMetadata, TechnicalReportContent, canonical_json,
)
from app.ports.technical_report import TechnicalReportReadCriteria, TechnicalReportScope
from app.repositories.technical_report_unit_of_work import SqlAlchemyTechnicalReportUnitOfWork
from app.schemas.technical_report import (
    PreliminaryQualificationSchema, TechnicalReportAIProposalRequest,
    TechnicalReportAIProposalResponse, TechnicalReportAcceptRequest,
    TechnicalReportAcceptedDetail, TechnicalReportAcceptedSnapshotSchema,
    TechnicalReportContentSchema, TechnicalReportCreateRequest,
    TechnicalReportCreateSuccessorRequest, TechnicalReportDraftDetail,
    TechnicalReportFilter, TechnicalReportLineageResponse,
    TechnicalReportListResponse, TechnicalReportProvenanceSchema,
    TechnicalReportReviseDraftRequest, TechnicalReportSummary,
)
from app.services.technical_report_service import TechnicalReportService
from app.adapters.technical_report_capture_source import TechnicalReportCaptureSourceAdapter
from app.api.v1.routers.engineering_experience_captures import (
    EngineeringExperienceCaptureApplication,
    get_engineering_experience_capture_application,
)
from app.schemas.technical_report import TechnicalReportCaptureSourceCandidateList


_MAPPINGS = (
    (TechnicalReportValidationError, 422),
    (TechnicalReportHistoricalBasisIncomplete, 422),
    (TechnicalReportIntegrityMismatch, 422),
    (TechnicalReportAuthorizationDenied, 404),
    (TechnicalReportInvalidLifecycle, 409),
    (TechnicalReportAcceptedImmutable, 409),
    (TechnicalReportVersionConflict, 409),
    (TechnicalReportIdempotencyConflict, 409),
    (TechnicalReportInvalidLineage, 409),
    (TechnicalReportAssistantUnavailable, 503),
)


def _error(http_status, code):
    return JSONResponse(
        status_code=http_status,
        content={"success": False, "error": {"code": code, "message": code}},
    )


class TechnicalReportRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()
        async def handler(request: Request):
            try:
                return await original(request)
            except RequestValidationError:
                return _error(422, "TECHNICAL_REPORT_VALIDATION_ERROR")
            except TechnicalReportException as exc:
                code = "TECHNICAL_REPORT_NOT_FOUND" if isinstance(exc, TechnicalReportAuthorizationDenied) else exc.code
                return _error(next((status for kind, status in _MAPPINGS if isinstance(exc, kind)), 500), code)
        return handler


router = APIRouter(tags=["Technical Reports"], route_class=TechnicalReportRoute)
CorrelationId = Annotated[UUID, Header(alias="X-Correlation-ID")]
IdempotencyId = Annotated[UUID, Header(alias="Idempotency-Key")]


class _UtcClock:
    def now(self): return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class TechnicalReportApplication:
    service: TechnicalReportService
    actor: TechnicalReportActor


def get_technical_report_application(
    context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context),
):
    actor = TechnicalReportActor(context.user.id, context.organization_id)
    return TechnicalReportApplication(
        TechnicalReportService(lambda: SqlAlchemyTechnicalReportUnitOfWork(SessionLocal), _UtcClock()), actor
    )


def _metadata(app, rationale, correlation, idempotency):
    return TechnicalReportCommandMetadata(app.actor, rationale, correlation, idempotency, uuid4())


def _content(value): return TechnicalReportContent(**value.model_dump())
def _qualification(value): return PreliminaryQualification(**value.model_dump())
def _provenance(values): return tuple(value.to_domain() for value in values)


def _provenance_dto(value):
    payload = json.loads(canonical_json(value))
    if "source_category" not in payload["locator"]:
        payload["locator"]["locator_type"] = {
            "external_or_human": "external_or_human", "standard": "standard", "contextual": "contextual"
        }[payload["source_type"]]
    return TechnicalReportProvenanceSchema.model_validate(payload)


def _summary(report):
    return TechnicalReportSummary(
        id=report.id, organization_id=report.organization_id,
        workspace_id=report.workspace_id, project_id=report.project_id,
        owner_id=report.owner_id, purpose=report.purpose,
        lifecycle=report.lifecycle, version=report.version,
        draft_revision_id=report.draft_revision_id,
        is_preliminary=report.qualification.is_preliminary,
        predecessor_report_id=report.predecessor_report_id,
        created_at=report.created_at, updated_at=report.updated_at,
        allowed_actions=getattr(report, "allowed_actions", ()),
    )


def _draft(report):
    return TechnicalReportDraftDetail(
        **_summary(report).model_dump(),
        content=TechnicalReportContentSchema.model_validate(asdict(report.content)),
        qualification=PreliminaryQualificationSchema.model_validate(asdict(report.qualification)),
        provenance=[_provenance_dto(item) for item in report.provenance],
    )


def _accepted(report):
    snapshot, record = report.accepted_snapshot, report.acceptance_record
    if snapshot is None or record is None: raise TechnicalReportInvalidLifecycle()
    dto = TechnicalReportAcceptedSnapshotSchema(
        report_id=snapshot.report_id, purpose=snapshot.purpose,
        organization_id=snapshot.organization_id, workspace_id=snapshot.workspace_id,
        project_id=snapshot.project_id,
        content=TechnicalReportContentSchema.model_validate(asdict(snapshot.content)),
        qualification=PreliminaryQualificationSchema.model_validate(asdict(snapshot.qualification)),
        provenance=[_provenance_dto(item) for item in snapshot.provenance],
        accepted_draft_revision_id=snapshot.accepted_draft_revision.revision_id,
        accepted_aggregate_version=snapshot.accepted_aggregate_version,
        accepted_by_id=snapshot.accepted_by_id, accepted_at=snapshot.accepted_at,
        predecessor_report_id=snapshot.predecessor_report_id,
        integrity_digest=snapshot.integrity_digest,
    )
    return TechnicalReportAcceptedDetail(
        **_summary(report).model_dump(), accepted_snapshot=dto,
        accepted_by_id=record.accepted_by_id, accepted_at=record.accepted_at,
        accepted_draft_revision_id=record.accepted_draft_revision.revision_id,
        accepted_aggregate_version=record.accepted_aggregate_version,
    )


def _detail(report):
    return _accepted(report) if report.lifecycle is TechnicalReportLifecycle.ACCEPTED else _draft(report)


@router.post("/technical-reports", status_code=status.HTTP_201_CREATED,
             response_model=TechnicalReportDraftDetail)
def create_report(data: TechnicalReportCreateRequest, correlation_id: CorrelationId,
                  idempotency_id: IdempotencyId,
                  app: TechnicalReportApplication = Depends(get_technical_report_application)):
    command = CreateTechnicalReportDraft(
        _metadata(app, "Create Technical Report draft", correlation_id, idempotency_id),
        app.actor.organization_id, data.workspace_id, data.project_id,
        app.actor.actor_id, data.purpose, _content(data.content),
        _qualification(data.qualification), _provenance(data.provenance),
    )
    return _detail(app.service.create_draft(command).report)


@router.get(
    "/technical-reports/capture-source-candidates",
    response_model=TechnicalReportCaptureSourceCandidateList,
)
def list_capture_source_candidates(
    project_id: int = Query(..., gt=0),
    workspace_id: int = Query(..., gt=0),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=20),
    capture_app: EngineeringExperienceCaptureApplication = Depends(
        get_engineering_experience_capture_application
    ),
):
    return TechnicalReportCaptureSourceAdapter(capture_app.service).list_candidates(
        actor=capture_app.actor,
        project_id=project_id,
        workspace_id=workspace_id,
        page=page,
        size=size,
    )


@router.get("/technical-reports/{report_id}",
            response_model=TechnicalReportDraftDetail | TechnicalReportAcceptedDetail)
def get_report(report_id: UUID, app: TechnicalReportApplication = Depends(get_technical_report_application)):
    return _detail(app.service.get_report(app.actor, report_id))


@router.get("/technical-reports", response_model=TechnicalReportListResponse)
def list_reports(workspace_id: int = Query(..., gt=0), project_id: int | None = Query(None, gt=0),
                 purpose: TechnicalReportPurpose | None = Query(None), lifecycle: TechnicalReportLifecycle | None = Query(None),
                 page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
                 app: TechnicalReportApplication = Depends(get_technical_report_application)):
    filters = TechnicalReportFilter(workspace_id=workspace_id, project_id=project_id, purpose=purpose, lifecycle=lifecycle, page=page, size=size)
    criteria = TechnicalReportReadCriteria(TechnicalReportScope(app.actor.organization_id, filters.workspace_id, filters.project_id), filters.page, filters.size, filters.purpose, filters.lifecycle)
    result = app.service.list_report_details(app.actor, criteria)
    return TechnicalReportListResponse(items=[_summary(item) for item in result.items], total=result.total, page=result.page, size=result.size)


@router.post("/technical-reports/{report_id}/draft-revisions",
             response_model=TechnicalReportDraftDetail)
def revise_report(report_id: UUID, data: TechnicalReportReviseDraftRequest,
                  correlation_id: CorrelationId, idempotency_id: IdempotencyId,
                  app: TechnicalReportApplication = Depends(get_technical_report_application)):
    command = ReviseTechnicalReportDraft(_metadata(app, data.rationale, correlation_id, idempotency_id), report_id, data.expected_version, data.expected_draft_revision_id, _content(data.content), _qualification(data.qualification), _provenance(data.provenance))
    return _detail(app.service.revise_draft(command).report)


@router.post("/technical-reports/{report_id}/acceptance",
             response_model=TechnicalReportAcceptedDetail)
def accept_report(report_id: UUID, data: TechnicalReportAcceptRequest,
                  correlation_id: CorrelationId, idempotency_id: IdempotencyId,
                  app: TechnicalReportApplication = Depends(get_technical_report_application)):
    command = AcceptExactTechnicalReportDraft(_metadata(app, data.rationale, correlation_id, idempotency_id), report_id, AcceptanceConfirmation(data.expected_version, data.exact_draft_revision_id, data.confirmed))
    return _detail(app.service.accept_exact_draft(command).report)


@router.post("/technical-reports/{report_id}/successors",
             status_code=status.HTTP_201_CREATED,
             response_model=TechnicalReportDraftDetail)
def create_successor(report_id: UUID, data: TechnicalReportCreateSuccessorRequest,
                     correlation_id: CorrelationId, idempotency_id: IdempotencyId,
                     app: TechnicalReportApplication = Depends(get_technical_report_application)):
    command = CreateTechnicalReportSuccessor(_metadata(app, data.rationale, correlation_id, idempotency_id), report_id, data.expected_predecessor_version, data.workspace_id, data.project_id, data.purpose, _content(data.content), _qualification(data.qualification), _provenance(data.provenance), tuple(data.selected_copy_references))
    return _detail(app.service.create_successor(command).report)


@router.get("/technical-reports/{report_id}/lineage", response_model=TechnicalReportLineageResponse)
def get_lineage(report_id: UUID, page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
                app: TechnicalReportApplication = Depends(get_technical_report_application)):
    result = app.service.retrieve_lineage_details(app.actor, report_id, page=page, size=size)
    return TechnicalReportLineageResponse(subject=_summary(result.subject), predecessor=None if result.predecessor is None else _summary(result.predecessor), successors=TechnicalReportListResponse(items=[_summary(item) for item in result.successors.items], total=result.successors.total, page=result.successors.page, size=result.successors.size))


@router.post("/technical-reports/{report_id}/ai-draft-proposals", response_model=TechnicalReportAIProposalResponse)
def ai_proposal(report_id: UUID, data: TechnicalReportAIProposalRequest,
                app: TechnicalReportApplication = Depends(get_technical_report_application)):
    result = app.service.request_ai_proposal(app.actor, report_id, expected_version=data.expected_version, expected_draft_revision_id=data.expected_draft_revision_id, human_instruction=data.human_instruction, selected_source_entry_ids=tuple(data.selected_source_entry_ids))
    return TechnicalReportAIProposalResponse(proposal_text=result.proposal_text, attribution=result.attribution)
