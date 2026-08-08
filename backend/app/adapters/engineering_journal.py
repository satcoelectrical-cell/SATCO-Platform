"""Canonical read adapters for the nonpersistent Engineering Journal."""

from uuid import UUID

from app.enums.engineering_journal import (
    EngineeringJournalNavigationTargetKind,
    EngineeringJournalView,
)
from app.exceptions.engineering_experience_capture import (
    EngineeringExperienceCaptureProtectedNotFound,
)
from app.exceptions.engineering_journal import EngineeringJournalProtectedNotFound
from app.exceptions.project import ProjectForbiddenException
from app.models.engineering_experience_capture_command import (
    EngineeringExperienceCaptureActor,
)
from app.schemas.engineering_journal import (
    EngineeringJournalAuthenticatedActor,
    EngineeringJournalCaptureDetailDTO,
    EngineeringJournalCaptureListItemDTO,
    EngineeringJournalCapturePageResultDTO,
    EngineeringJournalCountDTO,
    EngineeringJournalNavigationDTO,
    EngineeringJournalPresentationDTO,
    EngineeringJournalProjectSelectionItemDTO,
    EngineeringJournalProjectSelectionPageDTO,
    EngineeringJournalReturnContextDTO,
    EngineeringJournalScopeDTO,
)
from app.schemas.project import ProjectSelectionActor
from app.services.engineering_experience_capture_service import (
    EngineeringExperienceCaptureService,
)


def _capture_actor(
    actor: EngineeringJournalAuthenticatedActor,
) -> EngineeringExperienceCaptureActor:
    return EngineeringExperienceCaptureActor(
        actor_id=actor.actor_id,
        organization_id=actor.organization_id,
    )


class EngineeringJournalScopeAuthorizationAdapter:
    """Translate Journal scope requests into canonical Capture authorization."""

    def __init__(self, *, uow_factory, project_service) -> None:
        self._capture_service = EngineeringExperienceCaptureService(
            uow_factory=uow_factory
        )
        self._project_service = project_service

    def authorize_scope(
        self,
        *,
        actor: EngineeringJournalAuthenticatedActor,
        project_id: int | None,
        workspace_id: int | None,
        engineering_object_id: UUID | None,
        view: EngineeringJournalView,
    ) -> EngineeringJournalScopeDTO:
        del view
        if project_id is None:
            if workspace_id is not None or engineering_object_id is not None:
                raise EngineeringJournalProtectedNotFound()
            try:
                self._project_service.authorize_selection_actor(
                    actor=ProjectSelectionActor(
                        actor_id=actor.actor_id,
                        organization_id=actor.organization_id,
                    )
                )
            except ProjectForbiddenException as exc:
                raise EngineeringJournalProtectedNotFound() from exc
            return EngineeringJournalScopeDTO(
                organization_id=actor.organization_id
            )
        try:
            scope = self._capture_service.authorize_read_scope(
                actor=_capture_actor(actor),
                project_id=project_id,
                workspace_id=workspace_id,
                engineering_object_id=engineering_object_id,
            )
        except EngineeringExperienceCaptureProtectedNotFound as exc:
            raise EngineeringJournalProtectedNotFound() from exc
        return EngineeringJournalScopeDTO(
            organization_id=scope.organization_id,
            project_id=scope.project_id,
            workspace_id=scope.workspace_id,
            discipline=scope.discipline,
            engineering_object_id=scope.engineering_object_id,
        )


class EngineeringJournalProjectSelectionAdapter:
    """Adapt the canonical actor-authorized Project selection application read."""

    def __init__(self, project_service) -> None:
        self._project_service = project_service

    def list_authorized(
        self,
        *,
        actor: EngineeringJournalAuthenticatedActor,
        page: int,
        size: int,
    ) -> EngineeringJournalProjectSelectionPageDTO:
        try:
            result = self._project_service.list_authorized_selection(
                actor=ProjectSelectionActor(
                    actor_id=actor.actor_id,
                    organization_id=actor.organization_id,
                ),
                page=page,
                size=size,
            )
        except ProjectForbiddenException as exc:
            raise EngineeringJournalProtectedNotFound() from exc
        return EngineeringJournalProjectSelectionPageDTO(
            items=tuple(
                EngineeringJournalProjectSelectionItemDTO(
                    project_id=item.project_id,
                    display_name=item.display_name,
                )
                for item in result.items
            ),
            page=result.page,
            size=result.size,
            visible_total=result.returned_count,
            has_more=result.has_more,
        )


class EngineeringJournalCaptureReadAdapter:
    """Adapt canonical Capture reads to minimal Journal-owned projections."""

    def __init__(self, *, uow_factory) -> None:
        self._capture_service = EngineeringExperienceCaptureService(
            uow_factory=uow_factory
        )

    def list_authorized(
        self,
        *,
        actor: EngineeringJournalAuthenticatedActor,
        scope: EngineeringJournalScopeDTO,
        lifecycle,
        presentation: EngineeringJournalPresentationDTO,
    ) -> EngineeringJournalCapturePageResultDTO:
        if scope.project_id is None:
            raise EngineeringJournalProtectedNotFound()
        try:
            result = self._capture_service.read_authorized_page(
                actor=_capture_actor(actor),
                project_id=scope.project_id,
                workspace_id=scope.workspace_id,
                engineering_object_id=scope.engineering_object_id,
                lifecycle=lifecycle,
                source_kind=presentation.source_kind,
                discipline=presentation.discipline,
                page=presentation.page,
                size=presentation.size,
            )
        except EngineeringExperienceCaptureProtectedNotFound as exc:
            raise EngineeringJournalProtectedNotFound() from exc
        items = tuple(
            EngineeringJournalCaptureListItemDTO(
                capture_id=item.id,
                project_id=item.project_id,
                workspace_id=item.workspace_id,
                discipline=item.discipline,
                engineering_object_id=item.engineering_object_id,
                source_kind=item.source_kind,
                creator_id=item.creator_id,
                lifecycle=item.lifecycle,
                version=item.version,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in result.items
        )
        return EngineeringJournalCapturePageResultDTO(
            items=items,
            count=EngineeringJournalCountDTO(
                authorized_total=result.authorized_total,
                filtered_total=result.filtered_total,
                visible_total=result.visible_total,
            ),
            presentation=presentation,
        )

    def get_authorized(
        self,
        *,
        actor: EngineeringJournalAuthenticatedActor,
        scope: EngineeringJournalScopeDTO,
        capture_id: UUID,
    ) -> EngineeringJournalCaptureDetailDTO:
        if scope.project_id is None:
            raise EngineeringJournalProtectedNotFound()
        try:
            item = self._capture_service.read_authorized_detail(
                actor=_capture_actor(actor),
                project_id=scope.project_id,
                workspace_id=scope.workspace_id,
                engineering_object_id=scope.engineering_object_id,
                capture_id=capture_id,
            )
        except EngineeringExperienceCaptureProtectedNotFound as exc:
            raise EngineeringJournalProtectedNotFound() from exc
        return EngineeringJournalCaptureDetailDTO(
            capture_id=item.id,
            project_id=item.project_id,
            workspace_id=item.workspace_id,
            discipline=item.discipline,
            engineering_object_id=item.engineering_object_id,
            source_kind=item.source_kind,
            creator_id=item.creator_id,
            lifecycle=item.lifecycle,
            version=item.version,
            created_at=item.created_at,
            updated_at=item.updated_at,
            original_content=item.original_content,
            source_reference=item.source_reference,
            superseded_by_capture_id=item.superseded_by_capture_id,
        )


class EngineeringJournalCaptureNavigationAdapter:
    """Build non-authoritative links that always require destination checks."""

    def new_capture_navigation(
        self,
        *,
        actor: EngineeringJournalAuthenticatedActor,
        scope: EngineeringJournalScopeDTO,
    ) -> EngineeringJournalNavigationDTO:
        del actor
        if scope.project_id is None:
            raise EngineeringJournalProtectedNotFound()
        return EngineeringJournalNavigationDTO(
            target_kind=EngineeringJournalNavigationTargetKind.CANONICAL_CAPABILITY,
            canonical_target_id=scope.project_id,
            return_context=EngineeringJournalReturnContextDTO(
                view=EngineeringJournalView.NEW_CAPTURE,
                project_id=scope.project_id,
                workspace_id=scope.workspace_id,
            ),
            requires_reauthorization=True,
        )

    def capture_navigation(
        self,
        *,
        actor: EngineeringJournalAuthenticatedActor,
        scope: EngineeringJournalScopeDTO,
        capture_id: UUID,
    ) -> EngineeringJournalNavigationDTO:
        del actor
        del scope
        return EngineeringJournalNavigationDTO(
            target_kind=EngineeringJournalNavigationTargetKind.CANONICAL_CAPTURE,
            canonical_target_id=capture_id,
            requires_reauthorization=True,
        )


class EngineeringJournalCapabilityAvailabilityAdapter:
    """Expose only capabilities approved for PATCH-029 composition."""

    _unavailable = frozenset(
        {
            EngineeringJournalView.DRAFTS,
            EngineeringJournalView.UNDER_REVIEW,
            EngineeringJournalView.PUBLISHED,
        }
    )

    def is_available(self, *, view: EngineeringJournalView) -> bool:
        return view not in self._unavailable
