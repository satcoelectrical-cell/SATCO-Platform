"""Thin authenticated transport for PATCH-034 Organizational Memory V1."""

from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import ConfigDict, Field, StrictBool, StrictInt, StrictStr, model_validator
from pydantic.dataclasses import dataclass as pydantic_dataclass

from app.dependencies.organizational_memory import (
    OrganizationalMemoryApplication,
    get_organizational_memory_application,
)
from app.exceptions.organizational_memory import (
    OrganizationalMemoryValidationError,
)
from app.models.organizational_memory_command import (
    AcceptedReportSource,
    AdmitAcceptedReport,
    CreateMemorySuccessor,
    GetActiveMemory,
    InspectMemoryHistory,
    ListActiveMemory,
    MemoryCommandMetadata,
    MemoryScope,
    SupersedeMemory,
    WithdrawMemory,
)
from app.schemas.organizational_memory import (
    AdmitResultSchema,
    CreateSuccessorResultSchema,
    GetActiveResultSchema,
    InspectHistoryResultSchema,
    ListActiveResultSchema,
    SupersedeResultSchema,
    WithdrawResultSchema,
)


class OrganizationalMemoryRoute(APIRoute):
    """Translate transport validation to the closed payload-free result."""

    def get_route_handler(self):
        original = super().get_route_handler()

        async def handler(request: Request):
            try:
                return await original(request)
            except RequestValidationError:
                return JSONResponse(
                    status_code=422, content={"outcome": "invalid_request"}
                )
            except OrganizationalMemoryValidationError:
                return JSONResponse(
                    status_code=422, content={"outcome": "invalid_request"}
                )

        return handler


router = APIRouter(
    prefix="/organizational-memory",
    tags=["Organizational Memory"],
    route_class=OrganizationalMemoryRoute,
)
CorrelationId = Annotated[UUID, Header(alias="X-Correlation-ID")]
IdempotencyId = Annotated[UUID, Header(alias="Idempotency-Key")]
PositiveInt = Annotated[StrictInt, Field(gt=0)]
Reason = Annotated[StrictStr, Field(min_length=1, max_length=2000)]
Digest = Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]


@pydantic_dataclass(config=ConfigDict(extra="forbid"))
class AdmissionBody:
    report_id: UUID
    accepted_aggregate_version: PositiveInt
    accepted_snapshot_digest: Digest
    workspace_id: PositiveInt
    project_id: PositiveInt | None
    admission_rationale: Reason
    authority_rationale: Reason
    audience_actor_ids: tuple[PositiveInt, ...] = Field(default=(), max_length=100)
    reuse_restrictions: tuple[Reason, ...] = Field(default=(), max_length=32)

    @model_validator(mode="after")
    def exact_audience_contract(self):
        if tuple(sorted(set(self.audience_actor_ids))) != self.audience_actor_ids:
            raise ValueError("audience must be unique and sorted")
        return self


@pydantic_dataclass(config=ConfigDict(extra="forbid"))
class SuccessorBody(AdmissionBody):
    predecessor_memory_id: UUID = Field()


@pydantic_dataclass(config=ConfigDict(extra="forbid"))
class WithdrawalBody:
    expected_version: PositiveInt
    reason: Reason
    authority_rationale: Reason


@pydantic_dataclass(config=ConfigDict(extra="forbid"))
class SupersessionBody:
    replacement_memory_id: UUID
    expected_predecessor_version: PositiveInt
    expected_replacement_version: PositiveInt
    reason: Reason
    authority_rationale: Reason


def _metadata(app, correlation_id, idempotency_id, rationale):
    return MemoryCommandMetadata(
        app.actor, correlation_id, uuid4(), idempotency_id, rationale
    )


def _source(body):
    return AcceptedReportSource(
        body.report_id,
        body.accepted_aggregate_version,
        body.accepted_snapshot_digest,
    )


def _scope(app, workspace_id, project_id):
    return MemoryScope(app.actor.organization_id, workspace_id, project_id)


@router.post("/admissions", response_model=AdmitResultSchema)
def admit(
    body: AdmissionBody,
    correlation_id: CorrelationId,
    idempotency_id: IdempotencyId,
    application: OrganizationalMemoryApplication = Depends(
        get_organizational_memory_application
    ),
):
    return application.service.admit(AdmitAcceptedReport(
        _metadata(application, correlation_id, idempotency_id,
                  body.authority_rationale),
        _source(body), _scope(application, body.workspace_id, body.project_id),
        body.audience_actor_ids, body.reuse_restrictions,
        body.admission_rationale,
    ))


@router.get("/{memory_id}", response_model=GetActiveResultSchema)
def get_active(
    memory_id: UUID,
    include_provenance: bool = Query(False),
    reuse_intent: bool = Query(False),
    application: OrganizationalMemoryApplication = Depends(
        get_organizational_memory_application
    ),
):
    return application.service.get_active(
        application.actor,
        GetActiveMemory(memory_id, include_provenance, reuse_intent),
    )


@router.get("", response_model=ListActiveResultSchema)
def list_active(
    workspace_id: Annotated[int, Query(gt=0)],
    project_id: Annotated[int | None, Query(gt=0)] = None,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
    continuation: Annotated[str | None, Query(min_length=1, max_length=4096)] = None,
    application: OrganizationalMemoryApplication = Depends(
        get_organizational_memory_application
    ),
):
    return application.service.list_active(
        application.actor,
        ListActiveMemory(
            _scope(application, workspace_id, project_id),
            page_size,
            continuation,
        ),
    )


@router.get("/{memory_id}/history", response_model=InspectHistoryResultSchema)
def inspect_history(
    memory_id: UUID,
    include_predecessor: bool = Query(False),
    include_replacement: bool = Query(False),
    include_provenance: bool = Query(False),
    application: OrganizationalMemoryApplication = Depends(
        get_organizational_memory_application
    ),
):
    return application.service.inspect_history(
        application.actor,
        InspectMemoryHistory(
            memory_id, include_predecessor, include_replacement,
            include_provenance,
        ),
    )


@router.post("/{predecessor_memory_id}/successors",
             response_model=CreateSuccessorResultSchema)
def create_successor(
    predecessor_memory_id: UUID,
    body: SuccessorBody,
    correlation_id: CorrelationId,
    idempotency_id: IdempotencyId,
    application: OrganizationalMemoryApplication = Depends(
        get_organizational_memory_application
    ),
):
    if predecessor_memory_id != body.predecessor_memory_id:
        return {"outcome": "invalid_request"}
    return application.service.create_successor(CreateMemorySuccessor(
        _metadata(application, correlation_id, idempotency_id,
                  body.authority_rationale),
        _source(body), _scope(application, body.workspace_id, body.project_id),
        body.audience_actor_ids, body.reuse_restrictions,
        body.admission_rationale, predecessor_memory_id,
    ))


@router.post("/{memory_id}/withdrawal", response_model=WithdrawResultSchema)
def withdraw(
    memory_id: UUID,
    body: WithdrawalBody,
    correlation_id: CorrelationId,
    idempotency_id: IdempotencyId,
    application: OrganizationalMemoryApplication = Depends(
        get_organizational_memory_application
    ),
):
    return application.service.withdraw(WithdrawMemory(
        _metadata(application, correlation_id, idempotency_id,
                  body.authority_rationale),
        memory_id, body.expected_version, body.reason,
    ))


@router.post("/{predecessor_memory_id}/supersession",
             response_model=SupersedeResultSchema)
def supersede(
    predecessor_memory_id: UUID,
    body: SupersessionBody,
    correlation_id: CorrelationId,
    idempotency_id: IdempotencyId,
    application: OrganizationalMemoryApplication = Depends(
        get_organizational_memory_application
    ),
):
    return application.service.supersede(SupersedeMemory(
        _metadata(application, correlation_id, idempotency_id,
                  body.authority_rationale),
        predecessor_memory_id, body.replacement_memory_id,
        body.expected_predecessor_version, body.expected_replacement_version,
        body.reason,
    ))
