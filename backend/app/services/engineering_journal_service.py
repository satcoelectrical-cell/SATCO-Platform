"""Read-only application composition for the Engineering Journal."""

from uuid import UUID

from app.enums.engineering_experience_capture import (
    EngineeringExperienceCaptureLifecycle,
)
from app.enums.engineering_journal import (
    EngineeringJournalView,
    EngineeringJournalViewAvailability,
    EngineeringJournalWorkspaceResultState,
)
from app.schemas.engineering_journal import (
    EngineeringJournalAuthenticatedActor,
    EngineeringJournalCaptureDetailDTO,
    EngineeringJournalEmptyStateDTO,
    EngineeringJournalMemberViewDTO,
    EngineeringJournalNavigationDTO,
    EngineeringJournalNewCaptureViewDTO,
    EngineeringJournalPresentationDTO,
    EngineeringJournalUnavailableViewDTO,
    EngineeringJournalWorkspaceDTO,
)
from app.ports.engineering_journal import (
    EngineeringJournalCapabilityAvailabilityPort,
    EngineeringJournalCaptureNavigationPort,
    EngineeringJournalCaptureReadPort,
    EngineeringJournalProjectSelectionPort,
    EngineeringJournalScopeAuthorizationPort,
)


class EngineeringJournalService:
    """Compose authorized canonical reads without owning state or transactions."""

    def __init__(
        self,
        *,
        scope_authorization: EngineeringJournalScopeAuthorizationPort,
        project_selection: EngineeringJournalProjectSelectionPort,
        capture_read: EngineeringJournalCaptureReadPort,
        capture_navigation: EngineeringJournalCaptureNavigationPort,
        capability_availability: EngineeringJournalCapabilityAvailabilityPort,
    ) -> None:
        self._scope_authorization = scope_authorization
        self._project_selection = project_selection
        self._capture_read = capture_read
        self._capture_navigation = capture_navigation
        self._capability_availability = capability_availability

    def workspace(
        self,
        *,
        actor: EngineeringJournalAuthenticatedActor,
        view: EngineeringJournalView,
        project_id: int | None = None,
        workspace_id: int | None = None,
        engineering_object_id: UUID | None = None,
        presentation: EngineeringJournalPresentationDTO | None = None,
        project_page: int = 1,
        project_size: int = 20,
    ) -> EngineeringJournalWorkspaceDTO:
        """Compose one fresh authorized Journal workspace projection."""

        presentation = presentation or EngineeringJournalPresentationDTO()
        scope = self._scope_authorization.authorize_scope(
            actor=actor,
            project_id=project_id,
            workspace_id=workspace_id,
            engineering_object_id=engineering_object_id,
            view=view,
        )
        if scope.project_id is None:
            choices = self._project_selection.list_authorized(
                actor=actor, page=project_page, size=project_size
            )
            if not self._capability_availability.is_available(view=view):
                empty = EngineeringJournalEmptyStateDTO(
                    result_state=(
                        EngineeringJournalWorkspaceResultState.CAPABILITY_UNAVAILABLE
                    ),
                    semantic_category="capability_unavailable",
                    presentation_criteria_active=presentation.filter_active,
                )
                unavailable = EngineeringJournalUnavailableViewDTO(
                    availability=EngineeringJournalViewAvailability.UNAVAILABLE,
                    empty_state=empty,
                )
                return EngineeringJournalWorkspaceDTO(
                    view=view,
                    availability=EngineeringJournalViewAvailability.UNAVAILABLE,
                    result_state=(
                        EngineeringJournalWorkspaceResultState.CAPABILITY_UNAVAILABLE
                    ),
                    scope=scope,
                    view_content=unavailable,
                    presentation=presentation,
                    project_selection=choices,
                )
            empty = EngineeringJournalEmptyStateDTO(
                result_state=EngineeringJournalWorkspaceResultState.AUTHORIZED_EMPTY,
                semantic_category="project_selection_required",
                presentation_criteria_active=presentation.filter_active,
            )
            return EngineeringJournalWorkspaceDTO(
                view=view,
                availability=EngineeringJournalViewAvailability.AVAILABLE,
                result_state=EngineeringJournalWorkspaceResultState.AUTHORIZED_EMPTY,
                scope=scope,
                view_content=empty,
                presentation=presentation,
                project_selection=choices,
            )

        if not self._capability_availability.is_available(view=view):
            empty = EngineeringJournalEmptyStateDTO(
                result_state=(
                    EngineeringJournalWorkspaceResultState.CAPABILITY_UNAVAILABLE
                ),
                semantic_category="capability_unavailable",
                presentation_criteria_active=presentation.filter_active,
            )
            unavailable = EngineeringJournalUnavailableViewDTO(
                availability=EngineeringJournalViewAvailability.UNAVAILABLE,
                empty_state=empty,
            )
            return EngineeringJournalWorkspaceDTO(
                view=view,
                availability=EngineeringJournalViewAvailability.UNAVAILABLE,
                result_state=(
                    EngineeringJournalWorkspaceResultState.CAPABILITY_UNAVAILABLE
                ),
                scope=scope,
                view_content=unavailable,
                presentation=presentation,
            )

        if view == EngineeringJournalView.NEW_CAPTURE:
            navigation = self._capture_navigation.new_capture_navigation(
                actor=actor, scope=scope
            )
            content = EngineeringJournalNewCaptureViewDTO(
                availability=EngineeringJournalViewAvailability.AVAILABLE,
                navigation=navigation,
            )
            return EngineeringJournalWorkspaceDTO(
                view=view,
                availability=EngineeringJournalViewAvailability.AVAILABLE,
                result_state=EngineeringJournalWorkspaceResultState.CONTENT,
                scope=scope,
                view_content=content,
                navigation=(navigation,),
                presentation=presentation,
            )

        lifecycle = {
            EngineeringJournalView.INBOX: (
                EngineeringExperienceCaptureLifecycle.CAPTURED
            ),
            EngineeringJournalView.SUPERSEDED: (
                EngineeringExperienceCaptureLifecycle.SUPERSEDED
            ),
        }[view]
        page = self._capture_read.list_authorized(
            actor=actor,
            scope=scope,
            lifecycle=lifecycle,
            presentation=presentation,
        )
        if not page.items:
            state = (
                EngineeringJournalWorkspaceResultState.FILTERED_EMPTY
                if presentation.filter_active and page.count.authorized_total > 0
                else EngineeringJournalWorkspaceResultState.AUTHORIZED_EMPTY
            )
            empty = EngineeringJournalEmptyStateDTO(
                result_state=state,
                semantic_category=state.value,
                presentation_criteria_active=presentation.filter_active,
            )
            return EngineeringJournalWorkspaceDTO(
                view=view,
                availability=EngineeringJournalViewAvailability.AVAILABLE,
                result_state=state,
                scope=scope,
                view_content=empty,
                presentation=presentation,
            )

        member_view = EngineeringJournalMemberViewDTO(
            items=page.items,
            count=page.count,
            presentation=presentation,
        )
        navigation = tuple(
            self._capture_navigation.capture_navigation(
                actor=actor, scope=scope, capture_id=item.capture_id
            )
            for item in page.items
        )
        return EngineeringJournalWorkspaceDTO(
            view=view,
            availability=EngineeringJournalViewAvailability.AVAILABLE,
            result_state=EngineeringJournalWorkspaceResultState.CONTENT,
            scope=scope,
            view_content=member_view,
            navigation=navigation,
            presentation=presentation,
            canonical_freshness=max(item.version for item in page.items),
        )

    def detail(
        self,
        *,
        actor: EngineeringJournalAuthenticatedActor,
        capture_id: UUID,
        project_id: int,
        workspace_id: int | None = None,
        engineering_object_id: UUID | None = None,
    ) -> EngineeringJournalCaptureDetailDTO:
        """Reauthorize scope and item before returning detail-only fields."""

        scope = self._scope_authorization.authorize_scope(
            actor=actor,
            project_id=project_id,
            workspace_id=workspace_id,
            engineering_object_id=engineering_object_id,
            view=EngineeringJournalView.INBOX,
        )
        return self._capture_read.get_authorized(
            actor=actor, scope=scope, capture_id=capture_id
        )

    def refresh(self, **values) -> EngineeringJournalWorkspaceDTO:
        """Re-run complete authorization and composition; retain no authority."""

        return self.workspace(**values)

    def capture_navigation(
        self,
        *,
        actor: EngineeringJournalAuthenticatedActor,
        capture_id: UUID,
        project_id: int,
        workspace_id: int | None = None,
        engineering_object_id: UUID | None = None,
    ) -> EngineeringJournalNavigationDTO:
        """Reauthorize target detail before issuing non-authoritative navigation."""

        scope = self._scope_authorization.authorize_scope(
            actor=actor,
            project_id=project_id,
            workspace_id=workspace_id,
            engineering_object_id=engineering_object_id,
            view=EngineeringJournalView.INBOX,
        )
        self._capture_read.get_authorized(
            actor=actor, scope=scope, capture_id=capture_id
        )
        return self._capture_navigation.capture_navigation(
            actor=actor, scope=scope, capture_id=capture_id
        )
