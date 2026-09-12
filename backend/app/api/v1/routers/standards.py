"""CAT-01..05 and RGT-01..03 only. No source or material-content endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import JSONResponse

from app.dependencies.standards import StandardsApplication, decode_standards_cursor, encode_standards_cursor, get_standards_application, is_organization_standards_admin, is_platform_catalog_admin
from app.models.standards import StandardEdition
from app.schemas.standards import RightsBindingReplace, RightsRevocation, StandardEditionCreate, StandardIdentityCreate, StandingObservationCreate
from app.services.standards_service import StandardsError

router = APIRouter(tags=["Standards"])


def _protected(): return JSONResponse(status_code=404, content={"outcome": "protected_not_found"})
def _error(error: StandardsError): return JSONResponse(status_code=error.status, content={"outcome": error.code.lower(), "reason_code": error.code})
def _idempotency(key: str | None) -> str:
    if not key: raise StandardsError("INVALID_REQUEST", 422)
    return key


@router.get("/standards", operation_id="list_standards")
def list_standards(q: str | None = Query(None, max_length=120), scope: str | None = Query(None, pattern="^(global_trusted|organization_private)$"), cursor: str | None = Query(None, max_length=2048), page_size: int = Query(20, ge=1, le=100), application: StandardsApplication = Depends(get_standards_application)):
    cursor_scope = {"route": "CAT-01", "organization_id": str(application.context.organization_id), "q": q, "scope": scope, "page_size": page_size}
    position = decode_standards_cursor(cursor, scope=cursor_scope)
    rows = application.repository.list_identities(application.context.organization_id, query=q, scope=scope, limit=page_size, before=UUID(position) if position else None)
    visible = rows[:page_size]
    return {"items": [application.service._identity_payload(row) for row in visible], "next_cursor": encode_standards_cursor(scope=cursor_scope, position=str(visible[-1].id)) if len(rows) > page_size and visible else None}


@router.get("/standards/{standard_id}", operation_id="get_standard")
def get_standard(standard_id: UUID, application: StandardsApplication = Depends(get_standards_application)):
    row = application.repository.get_identity(standard_id, application.context.organization_id)
    if row is None: return _protected()
    editions = [application.service._edition_payload(item) for item in application.db.query(StandardEdition).filter_by(standard_identity_id=row.id).order_by(StandardEdition.created_at).all()]
    return {**application.service._identity_payload(row), "editions": editions}


@router.post("/standards", operation_id="register_standard", status_code=201)
def register_standard(data: StandardIdentityCreate, idempotency_key: str | None = Header(None, alias="Idempotency-Key", max_length=160), application: StandardsApplication = Depends(get_standards_application)):
    if data.catalog_scope.value == "global_trusted":
        if not is_platform_catalog_admin(application): return _protected()
    elif not is_organization_standards_admin(application): return _protected()
    try: status, body = application.service.register_identity(actor_id=application.context.user.id, organization_id=application.context.organization_id, data=data, idempotency_key=_idempotency(idempotency_key)); return JSONResponse(status_code=status, content=body)
    except StandardsError as error: application.db.rollback(); return _error(error)


@router.post("/standards/{standard_id}/editions", operation_id="create_standard_edition", status_code=201)
def create_standard_edition(standard_id: UUID, data: StandardEditionCreate, idempotency_key: str | None = Header(None, alias="Idempotency-Key", max_length=160), application: StandardsApplication = Depends(get_standards_application)):
    identity = application.repository.get_identity(standard_id, application.context.organization_id)
    if identity is None or (identity.catalog_scope == "global_trusted" and not is_platform_catalog_admin(application)) or (identity.catalog_scope == "organization_private" and not is_organization_standards_admin(application)): return _protected()
    try: status, body = application.service.create_edition(actor_id=application.context.user.id, organization_id=application.context.organization_id, identity_id=standard_id, data=data, idempotency_key=_idempotency(idempotency_key)); return JSONResponse(status_code=status, content=body)
    except StandardsError as error: application.db.rollback(); return _error(error)


@router.post("/standards/{standard_id}/editions/{edition_id}/standing-observations", operation_id="observe_standard_edition_standing", status_code=201)
def observe_standard_edition_standing(standard_id: UUID, edition_id: UUID, data: StandingObservationCreate, idempotency_key: str | None = Header(None, alias="Idempotency-Key", max_length=160), application: StandardsApplication = Depends(get_standards_application)):
    identity = application.repository.get_identity(standard_id, application.context.organization_id)
    if identity is None or (identity.catalog_scope == "global_trusted" and not is_platform_catalog_admin(application)) or (identity.catalog_scope == "organization_private" and not is_organization_standards_admin(application)): return _protected()
    try: status, body = application.service.observe_standing(actor_id=application.context.user.id, organization_id=application.context.organization_id, identity_id=standard_id, edition_id=edition_id, data=data, idempotency_key=_idempotency(idempotency_key)); return JSONResponse(status_code=status, content=body)
    except StandardsError as error: application.db.rollback(); return _error(error)


@router.get("/organizations/current/standard-rights", operation_id="list_standard_rights")
def list_standard_rights(cursor: str | None = Query(None, max_length=2048), page_size: int = Query(20, ge=1, le=20), source_provider_id: str | None = Query(None, max_length=80), application: StandardsApplication = Depends(get_standards_application)):
    if not is_organization_standards_admin(application): return _protected()
    cursor_scope = {"route": "RGT-01", "organization_id": str(application.context.organization_id), "provider": source_provider_id, "page_size": page_size}
    position = decode_standards_cursor(cursor, scope=cursor_scope)
    rows = application.repository.list_rights(application.context.organization_id, provider_id=source_provider_id, limit=page_size, before=UUID(position) if position else None)
    visible = rows[:page_size]
    return {"items": [application.service._rights_payload(row) for row in visible], "next_cursor": encode_standards_cursor(scope=cursor_scope, position=str(visible[-1].id)) if len(rows) > page_size and visible else None}


@router.put("/organizations/current/standard-rights/{edition_id}/{source_provider_id}", operation_id="replace_standard_rights")
def replace_standard_rights(edition_id: UUID, source_provider_id: str, data: RightsBindingReplace, idempotency_key: str | None = Header(None, alias="Idempotency-Key", max_length=160), application: StandardsApplication = Depends(get_standards_application)):
    if not is_organization_standards_admin(application): return _protected()
    try: status, body = application.service.replace_rights(actor_id=application.context.user.id, organization_id=application.context.organization_id, edition_id=edition_id, provider_id=source_provider_id, data=data, idempotency_key=_idempotency(idempotency_key)); return JSONResponse(status_code=status, content=body)
    except StandardsError as error: application.db.rollback(); return _error(error)


@router.post("/organizations/current/standard-rights/{rights_binding_id}/revocations", operation_id="revoke_standard_rights", status_code=201)
def revoke_standard_rights(rights_binding_id: UUID, data: RightsRevocation, idempotency_key: str | None = Header(None, alias="Idempotency-Key", max_length=160), application: StandardsApplication = Depends(get_standards_application)):
    if not is_organization_standards_admin(application): return _protected()
    try: status, body = application.service.revoke_rights(actor_id=application.context.user.id, organization_id=application.context.organization_id, binding_id=rights_binding_id, data=data, idempotency_key=_idempotency(idempotency_key)); return JSONResponse(status_code=status, content=body)
    except StandardsError as error: application.db.rollback(); return _error(error)
