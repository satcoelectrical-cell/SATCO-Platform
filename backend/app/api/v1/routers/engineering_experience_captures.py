"""Approved HTTP boundary for Universal Engineering Capture."""

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status

from app.core.database import SessionLocal
from app.dependencies.auth import (
    AuthenticatedOrganizationContext,
    get_current_user_organization_context,
)
from app.enums.engineering_experience_capture import (
    EngineeringExperienceCaptureLifecycle,
    EngineeringExperienceSourceKind,
)
from app.models.engineering_experience_capture_command import (
    EngineeringExperienceCaptureActor,
)
from app.repositories.engineering_experience_capture_unit_of_work import (
    SqlAlchemyEngineeringExperienceCaptureUnitOfWork,
)
from app.schemas.engineering_experience_capture import (
    EngineeringExperienceCaptureCreate,
    EngineeringExperienceCaptureFilter,
    EngineeringExperienceCaptureListResponse,
    EngineeringExperienceCaptureResponse,
    EngineeringExperienceCaptureSupersessionChainResponse,
    SupersedeEngineeringExperienceCaptureRequest,
    WithdrawEngineeringExperienceCaptureRequest,
)
from app.services.engineering_experience_capture_service import (
    EngineeringExperienceCaptureService,
)


router = APIRouter(tags=["Engineering Experience Captures"])
CorrelationId = Annotated[UUID, Header(alias="X-Correlation-ID")]
IdempotencyId = Annotated[UUID, Header(alias="Idempotency-Key")]


@dataclass(frozen=True, slots=True)
class EngineeringExperienceCaptureApplication:
    service: EngineeringExperienceCaptureService
    actor: EngineeringExperienceCaptureActor


def get_engineering_experience_capture_application(
    organization: AuthenticatedOrganizationContext = Depends(
        get_current_user_organization_context
    ),
) -> EngineeringExperienceCaptureApplication:
    actor = EngineeringExperienceCaptureActor(
        actor_id=organization.user.id,
        organization_id=organization.organization_id,
    )
    service = EngineeringExperienceCaptureService(
        uow_factory=lambda: SqlAlchemyEngineeringExperienceCaptureUnitOfWork(SessionLocal)
    )
    return EngineeringExperienceCaptureApplication(service=service, actor=actor)


@router.post(
    "/engineering-experience-captures",
    response_model=EngineeringExperienceCaptureResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_capture(
    data: EngineeringExperienceCaptureCreate,
    correlation_id: CorrelationId,
    idempotency_id: IdempotencyId,
    application: EngineeringExperienceCaptureApplication = Depends(
        get_engineering_experience_capture_application
    ),
):
    return application.service.create(
        data=data, actor=application.actor, correlation_id=correlation_id,
        idempotency_id=idempotency_id,
    )


@router.get(
    "/engineering-experience-captures/{capture_id}",
    response_model=EngineeringExperienceCaptureResponse,
)
def read_capture(
    capture_id: UUID,
    application: EngineeringExperienceCaptureApplication = Depends(
        get_engineering_experience_capture_application
    ),
):
    return application.service.get(capture_id, application.actor)


def _filters(lifecycle, source_kind, creator_id, engineering_object_id):
    return EngineeringExperienceCaptureFilter(
        lifecycle=lifecycle, source_kind=source_kind, creator_id=creator_id,
        engineering_object_id=engineering_object_id,
    )


@router.get(
    "/projects/{project_id}/engineering-experience-captures",
    response_model=EngineeringExperienceCaptureListResponse,
)
def list_project_captures(
    project_id: int,
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
    lifecycle: EngineeringExperienceCaptureLifecycle | None = Query(None),
    source_kind: EngineeringExperienceSourceKind | None = Query(None),
    creator_id: int | None = Query(None, gt=0),
    engineering_object_id: UUID | None = Query(None),
    application: EngineeringExperienceCaptureApplication = Depends(
        get_engineering_experience_capture_application
    ),
):
    return application.service.list_project(
        project_id, _filters(lifecycle, source_kind, creator_id, engineering_object_id),
        page, size, application.actor,
    )


@router.get(
    "/engineering-workspaces/{workspace_id}/engineering-experience-captures",
    response_model=EngineeringExperienceCaptureListResponse,
)
def list_workspace_captures(
    workspace_id: int,
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
    lifecycle: EngineeringExperienceCaptureLifecycle | None = Query(None),
    source_kind: EngineeringExperienceSourceKind | None = Query(None),
    creator_id: int | None = Query(None, gt=0),
    engineering_object_id: UUID | None = Query(None),
    application: EngineeringExperienceCaptureApplication = Depends(
        get_engineering_experience_capture_application
    ),
):
    return application.service.list_workspace(
        workspace_id, _filters(lifecycle, source_kind, creator_id, engineering_object_id),
        page, size, application.actor,
    )


@router.post(
    "/engineering-experience-captures/{capture_id}/withdraw",
    response_model=EngineeringExperienceCaptureResponse,
)
def withdraw_capture(
    capture_id: UUID, data: WithdrawEngineeringExperienceCaptureRequest,
    correlation_id: CorrelationId, idempotency_id: IdempotencyId,
    application: EngineeringExperienceCaptureApplication = Depends(
        get_engineering_experience_capture_application
    ),
):
    return application.service.withdraw(
        capture_id, data, application.actor, correlation_id, idempotency_id,
    )


@router.post(
    "/engineering-experience-captures/{capture_id}/supersede",
    response_model=EngineeringExperienceCaptureResponse,
)
def supersede_capture(
    capture_id: UUID, data: SupersedeEngineeringExperienceCaptureRequest,
    correlation_id: CorrelationId, idempotency_id: IdempotencyId,
    application: EngineeringExperienceCaptureApplication = Depends(
        get_engineering_experience_capture_application
    ),
):
    return application.service.supersede(
        capture_id, data, application.actor, correlation_id, idempotency_id,
    )


@router.get(
    "/engineering-experience-captures/{capture_id}/supersession-chain",
    response_model=EngineeringExperienceCaptureSupersessionChainResponse,
)
def read_supersession_chain(
    capture_id: UUID,
    application: EngineeringExperienceCaptureApplication = Depends(
        get_engineering_experience_capture_application
    ),
):
    return application.service.supersession_chain(capture_id, application.actor)
