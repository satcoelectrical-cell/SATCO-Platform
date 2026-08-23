"""Thin protected HTTP transport for PATCH-043 Supporting Files."""

from hashlib import sha256
import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Header, Query, Request, UploadFile, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.routing import APIRoute

from app.dependencies.supporting_file import (
    SupportingFileApplication,
    SupportingFileScannerApplication,
    get_supporting_file_application,
    get_supporting_file_scanner_application,
)
from app.enums.supporting_file import SupportingFileLifecycle, SupportingFileMediaType
from app.exceptions.supporting_file import (
    SupportingFileIntegrityError, SupportingFileInvalidTransition,
    SupportingFileProtectedNotFound, SupportingFileScannerUnavailable,
    SupportingFileValidationError, SupportingFileVersionConflict,
)
from app.models.supporting_file_command import SupportingFileScope, bounded_stream_identity
from app.ports.supporting_file import RecordSupportingFileScan
from app.schemas.supporting_file import (
    SupportingFileListResponse, SupportingFileResponse,
    SupportingFileScanResultRequest, SupportingFileWithdrawalRequest,
)


def _outcome(code: str, http_status: int):
    return JSONResponse(status_code=http_status, content={"outcome": code})


class SupportingFileRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()

        async def handler(request: Request):
            try:
                return await original(request)
            except RequestValidationError:
                return _outcome("invalid_request", 422)
            except SupportingFileProtectedNotFound:
                return _outcome("protected_not_found", 404)
            except SupportingFileValidationError:
                return _outcome("invalid_request", 422)
            except (SupportingFileVersionConflict, SupportingFileInvalidTransition):
                return _outcome("conflict", 409)
            except (SupportingFileIntegrityError, SupportingFileScannerUnavailable):
                return _outcome("unavailable", 503)

        return handler


router = APIRouter(tags=["Supporting Files"], route_class=SupportingFileRoute)
IdempotencyId = Annotated[UUID, Header(alias="Idempotency-Key")]
CorrelationId = Annotated[UUID, Header(alias="X-Correlation-ID")]


def _scope(app, project_id, workspace_id):
    return SupportingFileScope(app.organization_id, project_id, workspace_id)


def _dto(asset):
    return SupportingFileResponse(
        id=asset.id, organization_id=asset.organization_id,
        project_id=asset.project_id, workspace_id=asset.workspace_id,
        safe_filename=asset.safe_filename, media_type=asset.media_type,
        byte_size=asset.byte_size, digest_algorithm=asset.digest_algorithm,
        content_digest=asset.content_digest, lifecycle=asset.lifecycle,
        version=asset.version, uploader_id=asset.uploader_id,
        uploaded_at=asset.uploaded_at, scanned_at=asset.scanned_at,
        predecessor_asset_id=asset.predecessor_asset_id,
        allowed_actions=("download", "withdraw") if asset.lifecycle == "available" else (),
    )


@router.post("/supporting-files/uploads", response_model=SupportingFileResponse,
             status_code=status.HTTP_201_CREATED)
async def upload_supporting_file(
    file: UploadFile = File(...), project_id: int = Form(..., gt=0),
    workspace_id: int | None = Form(None, gt=0),
    predecessor_asset_id: UUID | None = Form(None),
    rationale: str = Form(..., min_length=1, max_length=2000),
    idempotency_id: IdempotencyId = ...,
    correlation_id: CorrelationId = ...,
    app: SupportingFileApplication = Depends(get_supporting_file_application),
):
    byte_size, digest = bounded_stream_identity(file.file)
    try:
        media_type = SupportingFileMediaType(file.content_type or "")
    except ValueError:
        return _outcome("invalid_request", 422)
    scope = _scope(app, project_id, workspace_id)
    reservation = app.service.reserve_upload(actor_id=app.actor_id, scope=scope)
    fingerprint = sha256(json.dumps({
        "project_id": project_id, "workspace_id": workspace_id,
        "predecessor_asset_id": None if predecessor_asset_id is None else str(predecessor_asset_id),
        "filename": file.filename, "media_type": media_type.value,
        "byte_size": byte_size, "digest": digest, "rationale": rationale,
    }, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return _dto(app.service.finalize_upload(
        actor_id=app.actor_id, reservation_id=reservation.id, scope=scope,
        filename=file.filename or "attachment", media_type=media_type,
        content=file.file, expected_digest=digest,
        rationale=rationale, correlation_id=correlation_id,
        predecessor_asset_id=predecessor_asset_id,
        idempotency_id=idempotency_id, request_fingerprint=fingerprint,
    ))


@router.get("/projects/{project_id}/supporting-files", response_model=SupportingFileListResponse)
def list_supporting_files(
    project_id: int, workspace_id: int | None = Query(None, gt=0),
    lifecycle: SupportingFileLifecycle | None = None,
    limit: int = Query(20, ge=1, le=50),
    continuation: str | None = Query(None, min_length=1, max_length=4096),
    app: SupportingFileApplication = Depends(get_supporting_file_application),
):
    items, token = app.service.list_metadata(
        actor_id=app.actor_id, scope=_scope(app, project_id, workspace_id),
        lifecycle=None if lifecycle is None else lifecycle.value,
        limit=limit, continuation=continuation,
    )
    return SupportingFileListResponse(
        items=[_dto(item) for item in items], visible_count=len(items),
        continuation=token,
    )


@router.get("/supporting-files/{asset_id}", response_model=SupportingFileResponse)
def get_supporting_file(
    asset_id: UUID, project_id: int = Query(..., gt=0),
    workspace_id: int | None = Query(None, gt=0),
    app: SupportingFileApplication = Depends(get_supporting_file_application),
):
    return _dto(app.service.get_metadata(
        actor_id=app.actor_id, scope=_scope(app, project_id, workspace_id),
        asset_id=asset_id,
    ))


@router.get("/supporting-files/{asset_id}/download")
def download_supporting_file(
    asset_id: UUID, project_id: int = Query(..., gt=0),
    workspace_id: int | None = Query(None, gt=0),
    app: SupportingFileApplication = Depends(get_supporting_file_application),
):
    asset, stream = app.service.open_active(
        actor_id=app.actor_id, scope=_scope(app, project_id, workspace_id),
        asset_id=asset_id,
    )
    return StreamingResponse(
        stream, media_type=asset.media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{asset.safe_ascii_filename}"',
            "Content-Length": str(asset.byte_size),
            "X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store",
        },
    )


@router.post("/supporting-files/{asset_id}/withdrawals", response_model=SupportingFileResponse)
def withdraw_supporting_file(
    asset_id: UUID, data: SupportingFileWithdrawalRequest,
    project_id: int = Query(..., gt=0), workspace_id: int | None = Query(None, gt=0),
    idempotency_id: IdempotencyId = ...,
    correlation_id: CorrelationId = ...,
    app: SupportingFileApplication = Depends(get_supporting_file_application),
):
    fingerprint = sha256(json.dumps({
        "asset_id": str(asset_id), "expected_version": data.expected_version,
        "rationale": data.rationale,
    }, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return _dto(app.service.withdraw(
        actor_id=app.actor_id, scope=_scope(app, project_id, workspace_id),
        asset_id=asset_id, expected_version=data.expected_version,
        rationale=data.rationale, correlation_id=correlation_id,
        idempotency_id=idempotency_id,
        request_fingerprint=fingerprint,
    ))


@router.post("/internal/supporting-files/scan-results", include_in_schema=False)
def record_scan_result(
    data: SupportingFileScanResultRequest,
    app: SupportingFileScannerApplication = Depends(
        get_supporting_file_scanner_application
    ),
):
    asset = app.service.record_scan_result(RecordSupportingFileScan(
        principal=app.principal, **data.model_dump(),
    ))
    return {"outcome": "accepted", "asset_version": asset.version}
