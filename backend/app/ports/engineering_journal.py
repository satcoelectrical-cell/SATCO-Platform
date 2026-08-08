"""Inward-owned read ports for Engineering Journal composition."""

from typing import Protocol
from uuid import UUID

from app.enums.engineering_experience_capture import (
    EngineeringExperienceCaptureLifecycle,
)
from app.enums.engineering_journal import EngineeringJournalView
from app.schemas.engineering_journal import (
    EngineeringJournalAuthenticatedActor,
    EngineeringJournalCaptureDetailDTO,
    EngineeringJournalCapturePageResultDTO,
    EngineeringJournalNavigationDTO,
    EngineeringJournalPresentationDTO,
    EngineeringJournalProjectSelectionPageDTO,
    EngineeringJournalScopeDTO,
)


class EngineeringJournalScopeAuthorizationPort(Protocol):
    """Authorize and resolve one immutable Journal scope."""

    def authorize_scope(
        self,
        *,
        actor: EngineeringJournalAuthenticatedActor,
        project_id: int | None,
        workspace_id: int | None,
        engineering_object_id: UUID | None,
        view: EngineeringJournalView,
    ) -> EngineeringJournalScopeDTO: ...


class EngineeringJournalProjectSelectionPort(Protocol):
    """Return only bounded actor-authorized canonical Project choices."""

    def list_authorized(
        self,
        *,
        actor: EngineeringJournalAuthenticatedActor,
        page: int,
        size: int,
    ) -> EngineeringJournalProjectSelectionPageDTO: ...


class EngineeringJournalCaptureReadPort(Protocol):
    """Read authorized canonical Capture projections without write authority."""

    def list_authorized(
        self,
        *,
        actor: EngineeringJournalAuthenticatedActor,
        scope: EngineeringJournalScopeDTO,
        lifecycle: EngineeringExperienceCaptureLifecycle,
        presentation: EngineeringJournalPresentationDTO,
    ) -> EngineeringJournalCapturePageResultDTO: ...

    def get_authorized(
        self,
        *,
        actor: EngineeringJournalAuthenticatedActor,
        scope: EngineeringJournalScopeDTO,
        capture_id: UUID,
    ) -> EngineeringJournalCaptureDetailDTO: ...


class EngineeringJournalCaptureNavigationPort(Protocol):
    """Build non-authoritative canonical navigation after authorization."""

    def new_capture_navigation(
        self,
        *,
        actor: EngineeringJournalAuthenticatedActor,
        scope: EngineeringJournalScopeDTO,
    ) -> EngineeringJournalNavigationDTO: ...

    def capture_navigation(
        self,
        *,
        actor: EngineeringJournalAuthenticatedActor,
        scope: EngineeringJournalScopeDTO,
        capture_id: UUID,
    ) -> EngineeringJournalNavigationDTO: ...


class EngineeringJournalCapabilityAvailabilityPort(Protocol):
    """Report architecture-controlled capability availability."""

    def is_available(self, *, view: EngineeringJournalView) -> bool: ...
