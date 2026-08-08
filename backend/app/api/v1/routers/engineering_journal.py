"""Thin HTTP boundary for the read-only Engineering Journal."""

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.adapters.engineering_journal import (
    EngineeringJournalCapabilityAvailabilityAdapter,
    EngineeringJournalCaptureNavigationAdapter,
    EngineeringJournalCaptureReadAdapter,
    EngineeringJournalProjectSelectionAdapter,
    EngineeringJournalScopeAuthorizationAdapter,
)
from app.core.database import SessionLocal, get_db
from app.dependencies.auth import (
    AuthenticatedOrganizationContext,
    get_current_user_organization_context,
)
from app.enums.engineering_experience_capture import EngineeringExperienceSourceKind
from app.enums.engineering_journal import (
    EngineeringJournalPresentationLayout,
    EngineeringJournalPresentationSort,
    EngineeringJournalView,
)
from app.exceptions.engineering_journal import (
    EngineeringJournalInvalidPresentationCriteria,
)
from app.repositories.engineering_experience_capture_unit_of_work import (
    SqlAlchemyEngineeringExperienceCaptureUnitOfWork,
)
from app.schemas.engineering_journal import (
    EngineeringJournalAuthenticatedActor,
    EngineeringJournalCaptureDetailDTO,
    EngineeringJournalPresentationDTO,
    EngineeringJournalWorkspaceDTO,
)
from app.services.engineering_journal_service import EngineeringJournalService
from app.services.project_service import ProjectService


router = APIRouter(prefix="/api/v1/engineering-journal", tags=["Engineering Journal"])


@dataclass(frozen=True, slots=True)
class EngineeringJournalApplication:
    """Request-scoped Journal orchestration and trusted actor context."""

    service: EngineeringJournalService
    actor: EngineeringJournalAuthenticatedActor


def get_engineering_journal_application(
    organization: AuthenticatedOrganizationContext = Depends(
        get_current_user_organization_context
    ),
    db: Session = Depends(get_db),
) -> EngineeringJournalApplication:
    """Compose canonical adapters without exposing their private transaction boundary."""

    actor = EngineeringJournalAuthenticatedActor(
        actor_id=organization.user.id,
        organization_id=organization.organization_id,
    )
    uow_factory = lambda: SqlAlchemyEngineeringExperienceCaptureUnitOfWork(
        SessionLocal
    )
    project_service = ProjectService(db)
    service = EngineeringJournalService(
        scope_authorization=EngineeringJournalScopeAuthorizationAdapter(
            uow_factory=uow_factory,
            project_service=project_service,
        ),
        project_selection=EngineeringJournalProjectSelectionAdapter(project_service),
        capture_read=EngineeringJournalCaptureReadAdapter(uow_factory=uow_factory),
        capture_navigation=EngineeringJournalCaptureNavigationAdapter(),
        capability_availability=EngineeringJournalCapabilityAvailabilityAdapter(),
    )
    return EngineeringJournalApplication(service=service, actor=actor)


ProjectId = Annotated[int | None, Query(gt=0)]
WorkspaceId = Annotated[int | None, Query(gt=0)]
ProjectPage = Annotated[int, Query(ge=1)]
ProjectSize = Annotated[int, Query(ge=1, le=100)]
Page = Annotated[int, Query(ge=1)]
Size = Annotated[int, Query(ge=1, le=100)]

_WORKSPACE_QUERY_FIELDS = frozenset(
    {
        "project_id",
        "workspace_id",
        "engineering_object_id",
        "source_kind",
        "discipline",
        "page",
        "size",
        "project_page",
        "project_size",
        "sort",
        "layout",
    }
)
_DETAIL_QUERY_FIELDS = frozenset(
    {"project_id", "workspace_id", "engineering_object_id"}
)


def _validate_query(request: Request, allowed: frozenset[str]) -> None:
    """Reject ambiguous or unapproved scalar presentation criteria."""

    if any(key not in allowed for key in request.query_params):
        raise EngineeringJournalInvalidPresentationCriteria()
    if any(len(request.query_params.getlist(key)) != 1 for key in request.query_params):
        raise EngineeringJournalInvalidPresentationCriteria()


def _validate_scope(
    *,
    project_id: int | None,
    workspace_id: int | None,
    engineering_object_id: UUID | None,
) -> None:
    """Enforce transport-level scope coherence before application orchestration."""

    if project_id is None and (
        workspace_id is not None or engineering_object_id is not None
    ):
        raise EngineeringJournalInvalidPresentationCriteria()
    if engineering_object_id is not None and workspace_id is None:
        raise EngineeringJournalInvalidPresentationCriteria()


def _workspace(
    *,
    request: Request,
    view: EngineeringJournalView,
    application: EngineeringJournalApplication,
    project_id: int | None,
    workspace_id: int | None,
    engineering_object_id: UUID | None,
    source_kind: EngineeringExperienceSourceKind | None,
    discipline: str | None,
    page: int,
    size: int,
    project_page: int,
    project_size: int,
    sort: EngineeringJournalPresentationSort,
    layout: EngineeringJournalPresentationLayout,
) -> EngineeringJournalWorkspaceDTO:
    _validate_query(request, _WORKSPACE_QUERY_FIELDS)
    _validate_scope(
        project_id=project_id,
        workspace_id=workspace_id,
        engineering_object_id=engineering_object_id,
    )
    presentation = EngineeringJournalPresentationDTO(
        sort=sort,
        source_kind=source_kind,
        discipline=discipline,
        page=page,
        size=size,
        layout=layout,
    )
    return application.service.workspace(
        actor=application.actor,
        view=view,
        project_id=project_id,
        workspace_id=workspace_id,
        engineering_object_id=engineering_object_id,
        presentation=presentation,
        project_page=project_page,
        project_size=project_size,
    )


@router.get("", response_model=EngineeringJournalWorkspaceDTO)
def read_engineering_journal(
    request: Request,
    project_id: ProjectId = None,
    workspace_id: WorkspaceId = None,
    engineering_object_id: UUID | None = Query(None),
    source_kind: EngineeringExperienceSourceKind | None = Query(None),
    discipline: str | None = Query(None, min_length=1),
    page: Page = 1,
    size: Size = 20,
    project_page: ProjectPage = 1,
    project_size: ProjectSize = 20,
    sort: EngineeringJournalPresentationSort = Query(
        EngineeringJournalPresentationSort.CREATED_AT_DESC
    ),
    layout: EngineeringJournalPresentationLayout = Query(
        EngineeringJournalPresentationLayout.LIST
    ),
    application: EngineeringJournalApplication = Depends(
        get_engineering_journal_application
    ),
) -> EngineeringJournalWorkspaceDTO:
    """Return the default Inbox workspace or its Project-less shell."""

    return _workspace(
        request=request,
        view=EngineeringJournalView.INBOX,
        application=application,
        project_id=project_id,
        workspace_id=workspace_id,
        engineering_object_id=engineering_object_id,
        source_kind=source_kind,
        discipline=discipline,
        page=page,
        size=size,
        project_page=project_page,
        project_size=project_size,
        sort=sort,
        layout=layout,
    )


@router.get("/views/{view}", response_model=EngineeringJournalWorkspaceDTO)
def read_engineering_journal_view(
    view: EngineeringJournalView,
    request: Request,
    project_id: ProjectId = None,
    workspace_id: WorkspaceId = None,
    engineering_object_id: UUID | None = Query(None),
    source_kind: EngineeringExperienceSourceKind | None = Query(None),
    discipline: str | None = Query(None, min_length=1),
    page: Page = 1,
    size: Size = 20,
    project_page: ProjectPage = 1,
    project_size: ProjectSize = 20,
    sort: EngineeringJournalPresentationSort = Query(
        EngineeringJournalPresentationSort.CREATED_AT_DESC
    ),
    layout: EngineeringJournalPresentationLayout = Query(
        EngineeringJournalPresentationLayout.LIST
    ),
    application: EngineeringJournalApplication = Depends(
        get_engineering_journal_application
    ),
) -> EngineeringJournalWorkspaceDTO:
    """Return one approved Journal view after fresh authorization."""

    return _workspace(
        request=request,
        view=view,
        application=application,
        project_id=project_id,
        workspace_id=workspace_id,
        engineering_object_id=engineering_object_id,
        source_kind=source_kind,
        discipline=discipline,
        page=page,
        size=size,
        project_page=project_page,
        project_size=project_size,
        sort=sort,
        layout=layout,
    )


@router.get(
    "/captures/{capture_id}",
    response_model=EngineeringJournalCaptureDetailDTO,
)
def read_engineering_journal_capture(
    capture_id: UUID,
    request: Request,
    project_id: Annotated[int, Query(gt=0)],
    workspace_id: WorkspaceId = None,
    engineering_object_id: UUID | None = Query(None),
    application: EngineeringJournalApplication = Depends(
        get_engineering_journal_application
    ),
) -> EngineeringJournalCaptureDetailDTO:
    """Return separately authorized canonical Capture detail fields."""

    _validate_query(request, _DETAIL_QUERY_FIELDS)
    _validate_scope(
        project_id=project_id,
        workspace_id=workspace_id,
        engineering_object_id=engineering_object_id,
    )
    return application.service.detail(
        actor=application.actor,
        capture_id=capture_id,
        project_id=project_id,
        workspace_id=workspace_id,
        engineering_object_id=engineering_object_id,
    )
