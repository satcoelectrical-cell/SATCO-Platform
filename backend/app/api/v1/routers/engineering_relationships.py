"""HTTP transport for the approved PATCH-026 application boundary."""

from dataclasses import dataclass
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.dependencies.auth import (
    AuthenticatedOrganizationContext,
    get_current_user_organization_context,
)
from app.enums import EngineeringAuthorityStanding
from app.enums import EngineeringRelationshipLifecycle, RelationshipFamily
from app.enums import RelationshipType
from app.models.engineering_relationship_command import (
    AuthenticatedRelationshipActor, RelationshipAuthorizationContext,
)
from app.repositories.engineering_relationship_repository import (
    SqlAlchemyEngineeringRelationshipRepository,
)
from app.repositories.engineering_relationship_unit_of_work import (
    SqlAlchemyEngineeringRelationshipUnitOfWork,
    SqlAlchemyRelationshipAuthorizationPolicy,
    SqlAlchemyRelationshipValidator,
    UtcRelationshipClock,
)
from app.repositories.evidence_unit_of_work import SqlAlchemyEvidenceValidator
from app.schemas.engineering_relationship import (
    ApproveEngineeringRelationshipRequest,
    DisputeEngineeringRelationshipRequest,
    EngineeringRelationshipCreate,
    EngineeringRelationshipFilter,
    EngineeringRelationshipListResponse,
    EngineeringRelationshipResponse,
    EngineeringRelationshipTraversal,
    EngineeringRelationshipTraversalResponse,
    RejectEngineeringRelationshipRequest,
    ReviewEngineeringRelationshipRequest,
    SubmitEngineeringRelationshipForReviewRequest,
    TransferEngineeringRelationshipStewardRequest,
    TransitionEngineeringRelationshipLifecycleRequest,
)
from app.services.engineering_relationship_service import (
    EngineeringRelationshipService,
)


class EngineeringRelationshipRoute(APIRoute):
    """Map transport validation to the stable PATCH-026 error contract."""

    def get_route_handler(self):
        original = super().get_route_handler()

        async def handler(request: Request):
            try:
                return await original(request)
            except RequestValidationError:
                return JSONResponse(
                    status_code=422,
                    content={
                        "success": False,
                        "error": {
                            "code": "ENGINEERING_RELATIONSHIP_VALIDATION_ERROR",
                            "message": "Engineering Relationship validation failed",
                        },
                    },
                )

        return handler


router = APIRouter(
    tags=["Engineering Relationships"],
    route_class=EngineeringRelationshipRoute,
)
CorrelationId = Annotated[UUID, Header(alias="X-Correlation-ID")]
IdempotencyId = Annotated[UUID, Header(alias="Idempotency-Key")]


@dataclass(frozen=True, slots=True)
class EngineeringRelationshipApplication:
    service: EngineeringRelationshipService
    actor: AuthenticatedRelationshipActor


def get_engineering_relationship_application(
    db: Session = Depends(get_db),
    organization: AuthenticatedOrganizationContext = Depends(
        get_current_user_organization_context
    ),
) -> EngineeringRelationshipApplication:
    """Build request dependencies only from trusted authentication context."""

    actor = AuthenticatedRelationshipActor(
        actor_id=organization.user.id,
        organization_id=organization.organization_id,
    )
    repository = SqlAlchemyEngineeringRelationshipRepository(db)
    evidence = SqlAlchemyEvidenceValidator(db)
    validator = SqlAlchemyRelationshipValidator(db, repository, evidence)
    service = EngineeringRelationshipService(
        uow_factory=lambda: SqlAlchemyEngineeringRelationshipUnitOfWork(
            SessionLocal
        ),
        authorization=SqlAlchemyRelationshipAuthorizationPolicy(db),
        validator=validator,
        clock=UtcRelationshipClock(),
    )
    return EngineeringRelationshipApplication(service=service, actor=actor)


def _context(operation: str, **scope: object):
    return RelationshipAuthorizationContext(operation=operation, scope=scope)


@router.post(
    "/engineering-relationships", response_model=EngineeringRelationshipResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_engineering_relationship(
    data: EngineeringRelationshipCreate,
    correlation_id: CorrelationId,
    idempotency_id: IdempotencyId,
    application: EngineeringRelationshipApplication = Depends(
        get_engineering_relationship_application
    ),
):
    return application.service.create(
        data=data, actor=application.actor,
        context=_context(
            "CreateEngineeringRelationship",
            source_object_id=data.source_object_id,
            target_object_id=data.target_object_id,
        ), correlation_id=correlation_id, idempotency_id=idempotency_id,
    )


@router.get(
    "/engineering-relationships/{relationship_id}",
    response_model=EngineeringRelationshipResponse,
)
def read_engineering_relationship(
    relationship_id: UUID,
    application: EngineeringRelationshipApplication = Depends(
        get_engineering_relationship_application
    ),
):
    return application.service.get(
        relationship_id, application.actor,
        _context("ReadEngineeringRelationship", relationship_id=relationship_id),
    )


def _filters(*, relationship_family, relationship_type, lifecycle,
             authority_standing, direction, workspace_id):
    return EngineeringRelationshipFilter(
        relationship_family=relationship_family,
        relationship_type=relationship_type, lifecycle=lifecycle,
        authority_standing=authority_standing, direction=direction,
        workspace_id=workspace_id,
    )


@router.get(
    "/engineering-objects/{object_id}/relationships",
    response_model=EngineeringRelationshipListResponse,
)
def list_engineering_relationships(
    object_id: UUID, page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    relationship_family: RelationshipFamily | None = Query(None),
    relationship_type: RelationshipType | None = Query(None),
    lifecycle: EngineeringRelationshipLifecycle | None = Query(None),
    authority_standing: EngineeringAuthorityStanding | None = Query(None),
    direction: Literal["incoming", "outgoing", "both"] = Query("both"),
    workspace_id: int | None = Query(None, gt=0),
    application: EngineeringRelationshipApplication = Depends(
        get_engineering_relationship_application
    ),
):
    filters = _filters(
        relationship_family=relationship_family,
        relationship_type=relationship_type, lifecycle=lifecycle,
        authority_standing=authority_standing, direction=direction,
        workspace_id=workspace_id,
    )
    return application.service.list_for_endpoint(
        object_id=object_id, filters=filters, page=page, size=size,
        actor=application.actor,
        context=_context("ListEngineeringRelationships", object_id=object_id),
    )


def _traversal(*, relationship_family, relationship_type, lifecycle,
               authority_standing, direction, workspace_id, max_depth,
               max_results, continuation_token):
    return EngineeringRelationshipTraversal(
        relationship_family=relationship_family,
        relationship_type=relationship_type, lifecycle=lifecycle,
        authority_standing=authority_standing, direction=direction,
        workspace_id=workspace_id, max_depth=max_depth,
        max_results=max_results, continuation_token=continuation_token,
    )


def _traversal_query(
    relationship_family: RelationshipFamily | None,
    relationship_type: RelationshipType | None,
    lifecycle: EngineeringRelationshipLifecycle | None,
    authority_standing: EngineeringAuthorityStanding | None,
    direction: Literal["incoming", "outgoing", "both"],
    workspace_id: int | None, max_depth: int, max_results: int,
    continuation_token: str | None,
):
    return _traversal(
        relationship_family=relationship_family,
        relationship_type=relationship_type, lifecycle=lifecycle,
        authority_standing=authority_standing, direction=direction,
        workspace_id=workspace_id, max_depth=max_depth,
        max_results=max_results, continuation_token=continuation_token,
    )


@router.get(
    "/engineering-objects/{object_id}/relationship-neighborhood",
    response_model=EngineeringRelationshipTraversalResponse,
)
def relationship_neighborhood(
    object_id: UUID,
    relationship_family: RelationshipFamily | None = Query(None),
    relationship_type: RelationshipType | None = Query(None),
    lifecycle: EngineeringRelationshipLifecycle | None = Query(None),
    authority_standing: EngineeringAuthorityStanding | None = Query(None),
    direction: Literal["incoming", "outgoing", "both"] = Query("both"),
    workspace_id: int | None = Query(None, gt=0),
    max_depth: int = Query(1, ge=1, le=5),
    max_results: int = Query(20, ge=1, le=100),
    continuation_token: str | None = Query(None, max_length=2048),
    application: EngineeringRelationshipApplication = Depends(
        get_engineering_relationship_application
    ),
):
    traversal = _traversal_query(
        relationship_family, relationship_type, lifecycle,
        authority_standing, direction, workspace_id, max_depth,
        max_results, continuation_token,
    )
    return application.service.neighborhood(
        object_id=object_id, traversal=traversal, actor=application.actor,
        context=_context("TraverseEngineeringRelationships", object_id=object_id),
    )


@router.get(
    "/engineering-objects/{object_id}/relationship-paths",
    response_model=EngineeringRelationshipTraversalResponse,
)
def relationship_paths(
    object_id: UUID, target_object_id: UUID = Query(...),
    relationship_family: RelationshipFamily | None = Query(None),
    relationship_type: RelationshipType | None = Query(None),
    lifecycle: EngineeringRelationshipLifecycle | None = Query(None),
    authority_standing: EngineeringAuthorityStanding | None = Query(None),
    direction: Literal["incoming", "outgoing", "both"] = Query("both"),
    workspace_id: int | None = Query(None, gt=0),
    max_depth: int = Query(1, ge=1, le=5),
    max_results: int = Query(20, ge=1, le=100),
    continuation_token: str | None = Query(None, max_length=2048),
    application: EngineeringRelationshipApplication = Depends(
        get_engineering_relationship_application
    ),
):
    traversal = _traversal_query(
        relationship_family, relationship_type, lifecycle,
        authority_standing, direction, workspace_id, max_depth,
        max_results, continuation_token,
    )
    return application.service.path(
        object_id=object_id, target_object_id=target_object_id,
        traversal=traversal, actor=application.actor,
        context=_context("FindEngineeringRelationshipPath", object_id=object_id),
    )


def _mutation(application, relationship_id, data, correlation_id,
              idempotency_id, operation, method):
    return getattr(application.service, method)(
        relationship_id, data, application.actor,
        _context(operation, relationship_id=relationship_id),
        correlation_id, idempotency_id,
    )


def _command_route(path, request_model, operation, method):
    async def endpoint(
        relationship_id: UUID, data: request_model,
        correlation_id: CorrelationId, idempotency_id: IdempotencyId,
        application: EngineeringRelationshipApplication = Depends(
            get_engineering_relationship_application
        ),
    ):
        return _mutation(
            application, relationship_id, data, correlation_id,
            idempotency_id, operation, method,
        )
    endpoint.__name__ = method
    router.post(path, response_model=EngineeringRelationshipResponse)(endpoint)


for _path, _model, _operation, _method in (
    ("/engineering-relationships/{relationship_id}/submissions", SubmitEngineeringRelationshipForReviewRequest, "SubmitEngineeringRelationshipForReview", "submit_for_review"),
    ("/engineering-relationships/{relationship_id}/reviews", ReviewEngineeringRelationshipRequest, "ReviewEngineeringRelationship", "review"),
    ("/engineering-relationships/{relationship_id}/approvals", ApproveEngineeringRelationshipRequest, "ApproveEngineeringRelationship", "approve"),
    ("/engineering-relationships/{relationship_id}/disputes", DisputeEngineeringRelationshipRequest, "DisputeEngineeringRelationship", "dispute"),
    ("/engineering-relationships/{relationship_id}/rejections", RejectEngineeringRelationshipRequest, "RejectEngineeringRelationship", "reject"),
    ("/engineering-relationships/{relationship_id}/lifecycle-transitions", TransitionEngineeringRelationshipLifecycleRequest, "TransitionEngineeringRelationshipLifecycle", "transition_lifecycle"),
    ("/engineering-relationships/{relationship_id}/steward-transfers", TransferEngineeringRelationshipStewardRequest, "TransferEngineeringRelationshipSteward", "transfer_steward"),
):
    _command_route(_path, _model, _operation, _method)
