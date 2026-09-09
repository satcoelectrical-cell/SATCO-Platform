"""Bounded, authorization-first Engineering Identifier HTTP API."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status

from app.dependencies.engineering_identifier import (
    EngineeringIdentifierApplication,
    get_engineering_identifier_application,
)
from app.schemas.engineering_identifier import (
    CreateEngineeringIdentifierRequest,
    EngineeringIdentifierHistoryResponse,
    EngineeringIdentifierResponse,
    EngineeringIdentifierSetResponse,
    ReassignPrimaryIdentifierRequest,
    ReplaceEngineeringIdentifierRequest,
    WithdrawEngineeringIdentifierRequest,
)


router = APIRouter(tags=["Engineering Identifiers"])
CorrelationId = Annotated[UUID, Header(alias="X-Correlation-ID")]
IdempotencyKey = Annotated[UUID, Header(alias="Idempotency-Key")]


def _identity(application):
    return application.context.user.id, application.context.organization_id


@router.get("/engineering-objects/{object_id}/identifiers", response_model=EngineeringIdentifierSetResponse)
def current_identifier_set(object_id: UUID, application: EngineeringIdentifierApplication = Depends(get_engineering_identifier_application)):
    actor_id, organization_id = _identity(application)
    return EngineeringIdentifierSetResponse(items=application.service.current_set(actor_id=actor_id, organization_id=organization_id, object_id=object_id))


@router.get("/engineering-objects/{object_id}/identifier-history", response_model=EngineeringIdentifierHistoryResponse)
def identifier_history(object_id: UUID, limit: int = Query(50, ge=1, le=100), cursor: str | None = Query(None, max_length=1024), application: EngineeringIdentifierApplication = Depends(get_engineering_identifier_application)):
    actor_id, organization_id = _identity(application)
    items, next_cursor = application.service.history(actor_id=actor_id, organization_id=organization_id, object_id=object_id, limit=limit, cursor=cursor)
    return EngineeringIdentifierHistoryResponse(items=items, next_cursor=next_cursor)


@router.post("/engineering-objects/{object_id}/identifiers", response_model=EngineeringIdentifierResponse, status_code=status.HTTP_201_CREATED)
def create_identifier(object_id: UUID, data: CreateEngineeringIdentifierRequest, correlation_id: CorrelationId, idempotency_key: IdempotencyKey, application: EngineeringIdentifierApplication = Depends(get_engineering_identifier_application)):
    actor_id, organization_id = _identity(application)
    return application.service.create(actor_id=actor_id, organization_id=organization_id, object_id=object_id, data=data, correlation_id=correlation_id, idempotency_key=idempotency_key)


@router.post("/engineering-identifiers/{identifier_id}/replacements", response_model=EngineeringIdentifierResponse, status_code=status.HTTP_201_CREATED)
def replace_identifier(identifier_id: UUID, data: ReplaceEngineeringIdentifierRequest, correlation_id: CorrelationId, idempotency_key: IdempotencyKey, application: EngineeringIdentifierApplication = Depends(get_engineering_identifier_application)):
    actor_id, organization_id = _identity(application)
    return application.service.replace(actor_id=actor_id, organization_id=organization_id, identifier_id=identifier_id, data=data, correlation_id=correlation_id, idempotency_key=idempotency_key)


@router.post("/engineering-identifiers/{identifier_id}/withdrawals", response_model=EngineeringIdentifierResponse)
def withdraw_identifier(identifier_id: UUID, data: WithdrawEngineeringIdentifierRequest, correlation_id: CorrelationId, idempotency_key: IdempotencyKey, application: EngineeringIdentifierApplication = Depends(get_engineering_identifier_application)):
    actor_id, organization_id = _identity(application)
    return application.service.withdraw(actor_id=actor_id, organization_id=organization_id, identifier_id=identifier_id, expected_version=data.expected_identifier_version, rationale=data.rationale, correlation_id=correlation_id, idempotency_key=idempotency_key)


@router.post("/engineering-objects/{object_id}/identifier-primary-reassignments", response_model=EngineeringIdentifierSetResponse)
def reassign_primary_identifier(object_id: UUID, data: ReassignPrimaryIdentifierRequest, correlation_id: CorrelationId, idempotency_key: IdempotencyKey, application: EngineeringIdentifierApplication = Depends(get_engineering_identifier_application)):
    actor_id, organization_id = _identity(application)
    return EngineeringIdentifierSetResponse(items=application.service.reassign_primary(actor_id=actor_id, organization_id=organization_id, object_id=object_id, data=data, correlation_id=correlation_id, idempotency_key=idempotency_key))
