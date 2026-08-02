"""HTTP transport for the approved EngineeringObject application boundary."""

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.dependencies.auth import (
    AuthenticatedOrganizationContext,
    get_current_user_organization_context,
)
from app.enums import (
    EngineeringAuthorityStanding,
    EngineeringDiscipline,
    EngineeringLifecycle,
    EngineeringObjectFamily,
    EngineeringObjectType,
)
from app.models.engineering_object_command import (
    AuthenticatedActor,
    AuthorizationContext,
)
from app.repositories.engineering_object_unit_of_work import (
    SqlAlchemyAuthorizationPolicy,
    SqlAlchemyEngineeringObjectUnitOfWork,
    SqlAlchemyReferenceValidator,
    UtcClock,
)
from app.schemas.engineering_object import (
    EngineeringObjectCreate,
    EngineeringObjectFilter,
    EngineeringObjectListResponse,
    EngineeringObjectResponse,
    ReclassifyEngineeringObjectRequest,
    TransferEngineeringObjectStewardRequest,
    TransitionEngineeringObjectAuthorityRequest,
    TransitionEngineeringObjectLifecycleRequest,
)
from app.services.engineering_object_service import EngineeringObjectService


router = APIRouter(tags=["Engineering Objects"])

CorrelationId = Annotated[UUID, Header(alias="X-Correlation-ID")]
IdempotencyId = Annotated[UUID, Header(alias="Idempotency-Key")]


@dataclass(frozen=True, slots=True)
class EngineeringObjectApplication:
    """Request-scoped service with its trusted authenticated actor."""

    service: EngineeringObjectService
    actor: AuthenticatedActor


def get_engineering_object_application(
    db: Session = Depends(get_db),
    organization: AuthenticatedOrganizationContext = Depends(
        get_current_user_organization_context
    ),
) -> EngineeringObjectApplication:
    """Build application dependencies from server-trusted authentication."""

    actor = AuthenticatedActor(
        actor_id=organization.user.id,
        organization_id=organization.organization_id,
    )
    service = EngineeringObjectService(
        uow_factory=lambda: SqlAlchemyEngineeringObjectUnitOfWork(SessionLocal),
        authorization=SqlAlchemyAuthorizationPolicy(db),
        references=SqlAlchemyReferenceValidator(db),
        clock=UtcClock(),
    )
    return EngineeringObjectApplication(service=service, actor=actor)


def _context(operation: str, **scope: object) -> AuthorizationContext:
    """Create operation-specific authorization context from trusted routing."""

    return AuthorizationContext(operation=operation, scope=scope)


@router.post(
    "/engineering-objects",
    response_model=EngineeringObjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_engineering_object(
    data: EngineeringObjectCreate,
    correlation_id: CorrelationId,
    idempotency_id: IdempotencyId,
    application: EngineeringObjectApplication = Depends(
        get_engineering_object_application
    ),
) -> EngineeringObjectResponse:
    return application.service.create(
        data=data,
        actor=application.actor,
        context=_context("CreateEngineeringObject", project_id=data.project_id),
        correlation_id=correlation_id,
        idempotency_id=idempotency_id,
    )


@router.get(
    "/engineering-objects/{object_id}",
    response_model=EngineeringObjectResponse,
)
def read_engineering_object(
    object_id: UUID,
    application: EngineeringObjectApplication = Depends(
        get_engineering_object_application
    ),
) -> EngineeringObjectResponse:
    return application.service.get(
        object_id,
        application.actor,
        _context("ReadEngineeringObject", object_id=object_id),
    )


@router.get(
    "/projects/{project_id}/engineering-objects",
    response_model=EngineeringObjectListResponse,
)
def list_engineering_objects(
    project_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    workspace_id: int | None = Query(None, gt=0),
    family: EngineeringObjectFamily | None = Query(None),
    discipline: EngineeringDiscipline | None = Query(None),
    object_type: EngineeringObjectType | None = Query(None),
    lifecycle: EngineeringLifecycle | None = Query(None),
    authority_standing: EngineeringAuthorityStanding | None = Query(None),
    application: EngineeringObjectApplication = Depends(
        get_engineering_object_application
    ),
) -> EngineeringObjectListResponse:
    filters = EngineeringObjectFilter(
        workspace_id=workspace_id,
        family=family,
        discipline=discipline,
        object_type=object_type,
        lifecycle=lifecycle,
        authority_standing=authority_standing,
    )
    return application.service.list(
        project_id=project_id,
        filters=filters,
        page=page,
        size=size,
        actor=application.actor,
        context=_context("ListEngineeringObjects", project_id=project_id),
    )


def _mutation(
    *, application: EngineeringObjectApplication, object_id: UUID,
    data: object, operation: str, correlation_id: UUID,
    idempotency_id: UUID, method: str,
) -> EngineeringObjectResponse:
    return getattr(application.service, method)(
        object_id,
        data,
        application.actor,
        _context(operation, object_id=object_id),
        correlation_id,
        idempotency_id,
    )


@router.post(
    "/engineering-objects/{object_id}/reclassifications",
    response_model=EngineeringObjectResponse,
)
def reclassify_engineering_object(
    object_id: UUID, data: ReclassifyEngineeringObjectRequest,
    correlation_id: CorrelationId, idempotency_id: IdempotencyId,
    application: EngineeringObjectApplication = Depends(
        get_engineering_object_application
    ),
) -> EngineeringObjectResponse:
    return _mutation(
        application=application, object_id=object_id, data=data,
        operation="ReclassifyEngineeringObject", method="reclassify",
        correlation_id=correlation_id, idempotency_id=idempotency_id,
    )


@router.post(
    "/engineering-objects/{object_id}/lifecycle-transitions",
    response_model=EngineeringObjectResponse,
)
def transition_engineering_object_lifecycle(
    object_id: UUID, data: TransitionEngineeringObjectLifecycleRequest,
    correlation_id: CorrelationId, idempotency_id: IdempotencyId,
    application: EngineeringObjectApplication = Depends(
        get_engineering_object_application
    ),
) -> EngineeringObjectResponse:
    return _mutation(
        application=application, object_id=object_id, data=data,
        operation="TransitionEngineeringObjectLifecycle",
        method="transition_lifecycle", correlation_id=correlation_id,
        idempotency_id=idempotency_id,
    )


@router.post(
    "/engineering-objects/{object_id}/authority-transitions",
    response_model=EngineeringObjectResponse,
)
def transition_engineering_object_authority(
    object_id: UUID, data: TransitionEngineeringObjectAuthorityRequest,
    correlation_id: CorrelationId, idempotency_id: IdempotencyId,
    application: EngineeringObjectApplication = Depends(
        get_engineering_object_application
    ),
) -> EngineeringObjectResponse:
    return _mutation(
        application=application, object_id=object_id, data=data,
        operation="TransitionEngineeringObjectAuthority",
        method="transition_authority", correlation_id=correlation_id,
        idempotency_id=idempotency_id,
    )


@router.post(
    "/engineering-objects/{object_id}/steward-transfers",
    response_model=EngineeringObjectResponse,
)
def transfer_engineering_object_steward(
    object_id: UUID, data: TransferEngineeringObjectStewardRequest,
    correlation_id: CorrelationId, idempotency_id: IdempotencyId,
    application: EngineeringObjectApplication = Depends(
        get_engineering_object_application
    ),
) -> EngineeringObjectResponse:
    return _mutation(
        application=application, object_id=object_id, data=data,
        operation="TransferEngineeringObjectSteward",
        method="transfer_steward", correlation_id=correlation_id,
        idempotency_id=idempotency_id,
    )
