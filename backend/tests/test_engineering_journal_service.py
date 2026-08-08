"""PATCH-029 Sprint 2 Engineering Journal application composition tests."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.enums.engineering_experience_capture import (
    EngineeringExperienceCaptureLifecycle,
    EngineeringExperienceSourceKind,
)
from app.enums.engineering_journal import (
    EngineeringJournalNavigationTargetKind,
    EngineeringJournalView,
    EngineeringJournalViewAvailability,
    EngineeringJournalWorkspaceResultState,
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
    EngineeringJournalScopeDTO,
)
from app.services.engineering_journal_service import EngineeringJournalService


NOW = datetime(2026, 8, 8, tzinfo=timezone.utc)


def _actor():
    return EngineeringJournalAuthenticatedActor(
        actor_id=1, organization_id=uuid4()
    )


def _item(lifecycle=EngineeringExperienceCaptureLifecycle.CAPTURED, version=1):
    return EngineeringJournalCaptureListItemDTO(
        capture_id=uuid4(),
        project_id=10,
        workspace_id=20,
        discipline="industrial_automation",
        engineering_object_id=uuid4(),
        source_kind=EngineeringExperienceSourceKind.OBSERVATION,
        creator_id=1,
        lifecycle=lifecycle,
        version=version,
        created_at=NOW,
        updated_at=NOW,
    )


class ScopePort:
    def __init__(self):
        self.calls = 0

    def authorize_scope(self, *, actor, project_id, workspace_id,
                        engineering_object_id, view):
        self.calls += 1
        return EngineeringJournalScopeDTO(
            organization_id=actor.organization_id,
            project_id=project_id,
            workspace_id=workspace_id,
            discipline="industrial_automation" if workspace_id else None,
            engineering_object_id=engineering_object_id,
        )


class SelectionPort:
    def __init__(self):
        self.calls = []

    def list_authorized(self, *, actor, page, size):
        self.calls.append((actor, page, size))
        return EngineeringJournalProjectSelectionPageDTO(
            items=(
                EngineeringJournalProjectSelectionItemDTO(
                    project_id=10, display_name="Authorized Project"
                ),
            ),
            page=page,
            size=size,
            visible_total=1,
            has_more=page == 1,
        )


class CapturePort:
    def __init__(self, items=(), authorized_total=0, filtered_total=0):
        self.items = tuple(items)
        self.authorized_total = authorized_total
        self.filtered_total = filtered_total
        self.list_calls = []
        self.detail_calls = []

    def list_authorized(self, *, actor, scope, lifecycle, presentation):
        self.list_calls.append((actor, scope, lifecycle, presentation))
        return EngineeringJournalCapturePageResultDTO(
            items=self.items,
            count=EngineeringJournalCountDTO(
                authorized_total=self.authorized_total,
                filtered_total=self.filtered_total,
                visible_total=len(self.items),
            ),
            presentation=presentation,
        )

    def get_authorized(self, *, actor, scope, capture_id):
        self.detail_calls.append((actor, scope, capture_id))
        item = _item()
        return EngineeringJournalCaptureDetailDTO(
            **item.model_dump(),
            original_content="Authorized detail",
            source_reference=None,
            superseded_by_capture_id=None,
        )


class NavigationPort:
    def __init__(self):
        self.capture_calls = []
        self.new_calls = 0

    def new_capture_navigation(self, *, actor, scope):
        self.new_calls += 1
        return EngineeringJournalNavigationDTO(
            target_kind=EngineeringJournalNavigationTargetKind.CANONICAL_CAPABILITY,
            canonical_target_id=scope.project_id,
            requires_reauthorization=True,
        )

    def capture_navigation(self, *, actor, scope, capture_id):
        self.capture_calls.append(capture_id)
        return EngineeringJournalNavigationDTO(
            target_kind=EngineeringJournalNavigationTargetKind.CANONICAL_CAPTURE,
            canonical_target_id=capture_id,
            requires_reauthorization=True,
        )


class AvailabilityPort:
    def is_available(self, *, view):
        return view not in {
            EngineeringJournalView.DRAFTS,
            EngineeringJournalView.UNDER_REVIEW,
            EngineeringJournalView.PUBLISHED,
        }


def _service(capture=None, availability=None):
    scope = ScopePort()
    selection = SelectionPort()
    capture = capture or CapturePort()
    navigation = NavigationPort()
    service = EngineeringJournalService(
        scope_authorization=scope,
        project_selection=selection,
        capture_read=capture,
        capture_navigation=navigation,
        capability_availability=availability or AvailabilityPort(),
    )
    return service, scope, selection, capture, navigation


def test_projectless_shell_is_bounded_and_reads_no_capture() -> None:
    service, _, selection, capture, _ = _service()
    workspace = service.workspace(
        actor=_actor(),
        view=EngineeringJournalView.INBOX,
        project_page=2,
        project_size=100,
    )
    assert workspace.scope.project_id is None
    assert workspace.project_selection.has_more is False
    assert selection.calls[0][1:] == (2, 100)
    assert capture.list_calls == []


def test_project_selection_never_automatically_selects_a_project() -> None:
    service, _, _, _, _ = _service()
    workspace = service.workspace(actor=_actor(), view=EngineeringJournalView.INBOX)
    assert workspace.scope.project_id is None
    assert workspace.result_state == EngineeringJournalWorkspaceResultState.AUTHORIZED_EMPTY


def test_projectless_future_view_remains_explicitly_unavailable() -> None:
    service, _, _, capture, _ = _service()
    workspace = service.workspace(
        actor=_actor(), view=EngineeringJournalView.DRAFTS
    )
    assert workspace.availability == EngineeringJournalViewAvailability.UNAVAILABLE
    assert workspace.project_selection is not None
    assert capture.list_calls == []


def test_partial_capture_capability_degradation_fabricates_no_members() -> None:
    class UnavailableCapture:
        def is_available(self, *, view):
            del view
            return False

    service, _, _, capture, _ = _service(availability=UnavailableCapture())
    workspace = service.workspace(
        actor=_actor(), view=EngineeringJournalView.INBOX, project_id=10
    )
    assert workspace.availability == EngineeringJournalViewAvailability.UNAVAILABLE
    assert capture.list_calls == []
    assert "count" not in type(workspace.view_content).model_fields


def test_inbox_uses_only_captured_canonical_members() -> None:
    item = _item()
    service, _, _, capture, _ = _service(CapturePort((item,), 1, 1))
    workspace = service.workspace(
        actor=_actor(), view=EngineeringJournalView.INBOX, project_id=10
    )
    assert workspace.view_content.items == (item,)
    assert capture.list_calls[0][2] == EngineeringExperienceCaptureLifecycle.CAPTURED


def test_superseded_uses_only_superseded_canonical_members() -> None:
    item = _item(EngineeringExperienceCaptureLifecycle.SUPERSEDED)
    service, _, _, capture, _ = _service(CapturePort((item,), 1, 1))
    service.workspace(
        actor=_actor(), view=EngineeringJournalView.SUPERSEDED, project_id=10
    )
    assert capture.list_calls[0][2] == EngineeringExperienceCaptureLifecycle.SUPERSEDED


@pytest.mark.parametrize(
    "view",
    (
        EngineeringJournalView.DRAFTS,
        EngineeringJournalView.UNDER_REVIEW,
        EngineeringJournalView.PUBLISHED,
    ),
)
def test_future_views_are_explicitly_unavailable_without_capture_reads(view) -> None:
    service, _, _, capture, _ = _service()
    workspace = service.workspace(actor=_actor(), view=view, project_id=10)
    assert workspace.availability == EngineeringJournalViewAvailability.UNAVAILABLE
    assert workspace.result_state == EngineeringJournalWorkspaceResultState.CAPABILITY_UNAVAILABLE
    assert capture.list_calls == []
    assert "count" not in type(workspace.view_content).model_fields


def test_new_capture_is_navigation_only_and_invokes_no_command() -> None:
    service, _, _, capture, navigation = _service()
    workspace = service.workspace(
        actor=_actor(), view=EngineeringJournalView.NEW_CAPTURE, project_id=10
    )
    assert navigation.new_calls == 1
    assert capture.list_calls == []
    assert "items" not in type(workspace.view_content).model_fields


def test_authorized_empty_and_filtered_empty_are_distinct() -> None:
    service, _, _, _, _ = _service(CapturePort((), 0, 0))
    empty = service.workspace(
        actor=_actor(), view=EngineeringJournalView.INBOX, project_id=10
    )
    assert empty.result_state == EngineeringJournalWorkspaceResultState.AUTHORIZED_EMPTY

    service, _, _, _, _ = _service(CapturePort((), 3, 0))
    filtered = service.workspace(
        actor=_actor(),
        view=EngineeringJournalView.INBOX,
        project_id=10,
        presentation=EngineeringJournalPresentationDTO(
            source_kind=EngineeringExperienceSourceKind.FIELD_NOTE
        ),
    )
    assert filtered.result_state == EngineeringJournalWorkspaceResultState.FILTERED_EMPTY


def test_counts_navigation_order_and_freshness_use_returned_page_only() -> None:
    first = _item(version=2)
    second = _item(version=5)
    service, _, _, _, navigation = _service(CapturePort((first, second), 9, 9))
    workspace = service.workspace(
        actor=_actor(), view=EngineeringJournalView.INBOX, project_id=10
    )
    assert workspace.view_content.count.authorized_total == 9
    assert workspace.view_content.count.visible_total == 2
    assert workspace.canonical_freshness == 5
    assert navigation.capture_calls == [first.capture_id, second.capture_id]


def test_detail_navigation_and_refresh_reauthorize() -> None:
    service, scope, _, capture, _ = _service()
    actor = _actor()
    capture_id = uuid4()
    detail = service.detail(
        actor=actor, capture_id=capture_id, project_id=10, workspace_id=20
    )
    service.capture_navigation(
        actor=actor, capture_id=capture_id, project_id=10, workspace_id=20
    )
    service.refresh(actor=actor, view=EngineeringJournalView.INBOX)
    assert detail.original_content == "Authorized detail"
    assert scope.calls == 3
    assert len(capture.detail_calls) == 2
