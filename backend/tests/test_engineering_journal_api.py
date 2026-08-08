"""Sprint 3 transport and integration evidence for the Engineering Journal."""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID

from fastapi.testclient import TestClient

from app.api.v1.routers.engineering_journal import (
    EngineeringJournalApplication,
    get_engineering_journal_application,
)
from app.dependencies.auth import AuthenticatedOrganizationContext
from app.enums.engineering_experience_capture import (
    EngineeringExperienceCaptureLifecycle,
    EngineeringExperienceSourceKind,
)
from app.enums.engineering_journal import (
    EngineeringJournalPresentationLayout,
    EngineeringJournalPresentationSort,
    EngineeringJournalView,
    EngineeringJournalViewAvailability,
    EngineeringJournalWorkspaceResultState,
)
from app.exceptions.engineering_journal import EngineeringJournalProtectedNotFound
from app.main import app
from app.schemas.engineering_journal import (
    EngineeringJournalAuthenticatedActor,
    EngineeringJournalCaptureDetailDTO,
    EngineeringJournalCaptureListItemDTO,
    EngineeringJournalCountDTO,
    EngineeringJournalEmptyStateDTO,
    EngineeringJournalMemberViewDTO,
    EngineeringJournalPresentationDTO,
    EngineeringJournalProjectSelectionPageDTO,
    EngineeringJournalScopeDTO,
    EngineeringJournalUnavailableViewDTO,
    EngineeringJournalWorkspaceDTO,
)


ORGANIZATION_ID = UUID("02900000-0000-4000-8000-000000000001")
CAPTURE_ID = UUID("02900000-0000-4000-8000-000000000002")
ACTOR = EngineeringJournalAuthenticatedActor(
    actor_id=7, organization_id=ORGANIZATION_ID
)
NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _presentation(page: int = 1, size: int = 20):
    return EngineeringJournalPresentationDTO(page=page, size=size)


def _item(lifecycle=EngineeringExperienceCaptureLifecycle.CAPTURED):
    return EngineeringJournalCaptureListItemDTO(
        capture_id=CAPTURE_ID,
        project_id=1,
        workspace_id=2,
        discipline="electrical",
        source_kind=EngineeringExperienceSourceKind.OBSERVATION,
        creator_id=7,
        lifecycle=lifecycle,
        version=1,
        created_at=NOW,
        updated_at=NOW,
    )


def _workspace(view=EngineeringJournalView.INBOX, page=1, size=20):
    presentation = _presentation(page, size)
    item = _item(
        EngineeringExperienceCaptureLifecycle.SUPERSEDED
        if view == EngineeringJournalView.SUPERSEDED
        else EngineeringExperienceCaptureLifecycle.CAPTURED
    )
    content = EngineeringJournalMemberViewDTO(
        items=(item,),
        count=EngineeringJournalCountDTO(
            authorized_total=1, filtered_total=1, visible_total=1
        ),
        presentation=presentation,
    )
    return EngineeringJournalWorkspaceDTO(
        view=view,
        availability=EngineeringJournalViewAvailability.AVAILABLE,
        result_state=EngineeringJournalWorkspaceResultState.CONTENT,
        scope=EngineeringJournalScopeDTO(
            organization_id=ORGANIZATION_ID,
            project_id=1,
            workspace_id=2,
            discipline="electrical",
        ),
        view_content=content,
        presentation=presentation,
        canonical_freshness=1,
    )


def _projectless_workspace(view=EngineeringJournalView.INBOX):
    presentation = _presentation()
    empty = EngineeringJournalEmptyStateDTO(
        result_state=EngineeringJournalWorkspaceResultState.AUTHORIZED_EMPTY,
        semantic_category="project_selection_required",
        presentation_criteria_active=False,
    )
    return EngineeringJournalWorkspaceDTO(
        view=view,
        availability=EngineeringJournalViewAvailability.AVAILABLE,
        result_state=EngineeringJournalWorkspaceResultState.AUTHORIZED_EMPTY,
        scope=EngineeringJournalScopeDTO(organization_id=ORGANIZATION_ID),
        view_content=empty,
        presentation=presentation,
        project_selection=EngineeringJournalProjectSelectionPageDTO(
            items=(), page=1, size=20, visible_total=0, has_more=False
        ),
    )


def _unavailable(view=EngineeringJournalView.DRAFTS):
    presentation = _presentation()
    empty = EngineeringJournalEmptyStateDTO(
        result_state=EngineeringJournalWorkspaceResultState.CAPABILITY_UNAVAILABLE,
        semantic_category="capability_unavailable",
        presentation_criteria_active=False,
    )
    content = EngineeringJournalUnavailableViewDTO(
        availability=EngineeringJournalViewAvailability.UNAVAILABLE,
        empty_state=empty,
    )
    return EngineeringJournalWorkspaceDTO(
        view=view,
        availability=EngineeringJournalViewAvailability.UNAVAILABLE,
        result_state=EngineeringJournalWorkspaceResultState.CAPABILITY_UNAVAILABLE,
        scope=EngineeringJournalScopeDTO(
            organization_id=ORGANIZATION_ID, project_id=1
        ),
        view_content=content,
        presentation=presentation,
    )


def _detail():
    return EngineeringJournalCaptureDetailDTO(
        **_item().model_dump(),
        original_content="Authorized detail",
        source_reference="REF-1",
    )


class FakeJournalService:
    def __init__(self):
        self.workspace_calls = []
        self.detail_calls = []

    def workspace(self, **values):
        self.workspace_calls.append(values)
        view = values["view"]
        if view in {
            EngineeringJournalView.DRAFTS,
            EngineeringJournalView.UNDER_REVIEW,
            EngineeringJournalView.PUBLISHED,
        }:
            return _unavailable(view)
        if values["project_id"] is None:
            return _projectless_workspace(view)
        presentation = values["presentation"]
        return _workspace(view, presentation.page, presentation.size)

    def detail(self, **values):
        self.detail_calls.append(values)
        return _detail()


def _client(service=None):
    service = service or FakeJournalService()
    app.dependency_overrides[get_engineering_journal_application] = lambda: (
        EngineeringJournalApplication(service=service, actor=ACTOR)
    )
    return TestClient(app), service


def test_registered_transport_exposes_exact_three_read_operations():
    expected = {
        ("/api/v1/engineering-journal", "get"),
        ("/api/v1/engineering-journal/views/{view}", "get"),
        ("/api/v1/engineering-journal/captures/{capture_id}", "get"),
    }
    actual = {
        (path, method)
        for path, contract in app.openapi()["paths"].items()
        if path.startswith("/api/v1/engineering-journal")
        for method in contract
    }
    assert actual == expected


def test_default_read_returns_projectless_workspace_shell():
    client, service = _client()
    try:
        response = client.get("/api/v1/engineering-journal")
        assert response.status_code == 200
        body = response.json()
        assert body["view"] == "inbox"
        assert body["result_state"] == "authorized_empty"
        assert body["project_selection"]["visible_total"] == 0
        assert service.workspace_calls[0]["project_id"] is None
    finally:
        app.dependency_overrides.clear()


def test_selected_view_maps_bounded_presentation_and_protected_counts():
    client, service = _client()
    try:
        response = client.get(
            "/api/v1/engineering-journal/views/superseded",
            params={
                "project_id": 1,
                "workspace_id": 2,
                "page": 2,
                "size": 5,
                "source_kind": "observation",
                "sort": "created_at_desc",
                "layout": "list",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["view"] == "superseded"
        assert body["view_content"]["count"] == {
            "authorized_total": 1,
            "filtered_total": 1,
            "visible_total": 1,
            "is_authoritative_for_scope": True,
        }
        call = service.workspace_calls[0]
        assert call["presentation"].page == 2
        assert call["presentation"].size == 5
        assert call["presentation"].source_kind == "observation"
    finally:
        app.dependency_overrides.clear()


def test_unavailable_view_is_successful_http_200_without_members_or_counts():
    client, _ = _client()
    try:
        response = client.get(
            "/api/v1/engineering-journal/views/drafts", params={"project_id": 1}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["result_state"] == "capability_unavailable"
        assert body["availability"] == "unavailable"
        assert "items" not in body["view_content"]
        assert "count" not in body["view_content"]
    finally:
        app.dependency_overrides.clear()


def test_detail_uses_separate_authorized_projection_and_scope():
    client, service = _client()
    try:
        response = client.get(
            f"/api/v1/engineering-journal/captures/{CAPTURE_ID}",
            params={"project_id": 1, "workspace_id": 2},
        )
        assert response.status_code == 200
        assert response.json()["original_content"] == "Authorized detail"
        assert service.detail_calls[0]["capture_id"] == CAPTURE_ID
        assert service.detail_calls[0]["project_id"] == 1
    finally:
        app.dependency_overrides.clear()


def test_protected_not_found_has_stable_equivalent_transport_outcome():
    class ProtectedService(FakeJournalService):
        def workspace(self, **_values):
            raise EngineeringJournalProtectedNotFound()

        def detail(self, **_values):
            raise EngineeringJournalProtectedNotFound()

    client, _ = _client(ProtectedService())
    try:
        list_response = client.get(
            "/api/v1/engineering-journal", params={"project_id": 1}
        )
        detail_response = client.get(
            f"/api/v1/engineering-journal/captures/{CAPTURE_ID}",
            params={"project_id": 1},
        )
        assert list_response.status_code == detail_response.status_code == 404
        assert list_response.json() == detail_response.json()
        assert list_response.json()["error"]["code"] == "ENGINEERING_JOURNAL_NOT_FOUND"
    finally:
        app.dependency_overrides.clear()


def test_transport_rejects_unknown_repeated_and_incoherent_criteria():
    client, service = _client()
    try:
        responses = (
            client.get("/api/v1/engineering-journal?project_id=1&project_id=2"),
            client.get("/api/v1/engineering-journal?organization_id=x"),
            client.get("/api/v1/engineering-journal?workspace_id=2"),
            client.get(
                "/api/v1/engineering-journal",
                params={"project_id": 1, "engineering_object_id": str(CAPTURE_ID)},
            ),
        )
        assert all(response.status_code == 422 for response in responses)
        assert not service.workspace_calls
    finally:
        app.dependency_overrides.clear()


def test_transport_prohibits_commands_refresh_and_navigation_routes():
    client, _ = _client()
    try:
        assert client.post("/api/v1/engineering-journal", json={}).status_code == 405
        assert client.put("/api/v1/engineering-journal", json={}).status_code == 405
        assert client.patch("/api/v1/engineering-journal", json={}).status_code == 405
        assert client.delete("/api/v1/engineering-journal").status_code == 405
        assert client.get("/api/v1/engineering-journal/refresh").status_code in {404, 422}
        assert client.get("/api/v1/engineering-journal/navigation").status_code in {404, 422}
        assert client.post("/api/v1/engineering-journal/captures", json={}).status_code in {404, 405}
    finally:
        app.dependency_overrides.clear()


def test_request_scoped_composition_builds_distinct_services_from_trusted_context():
    organization = AuthenticatedOrganizationContext(
        user=SimpleNamespace(id=7), organization_id=ORGANIZATION_ID
    )
    db = SimpleNamespace()
    first = get_engineering_journal_application(organization=organization, db=db)
    second = get_engineering_journal_application(organization=organization, db=db)
    assert first is not second
    assert first.service is not second.service
    assert first.actor == second.actor == ACTOR
    assert not hasattr(first.service, "commit")
    assert not hasattr(first.service, "rollback")


def test_errors_and_logs_exclude_unapproved_plaintext(caplog):
    marker = "JOURNAL-PROTECTED-PLAINTEXT-MARKER"
    client, service = _client()
    try:
        response = client.get(
            "/api/v1/engineering-journal", params={"content": marker}
        )
        assert response.status_code == 422
        assert marker not in response.text
        assert marker not in caplog.text
        assert not service.workspace_calls
    finally:
        app.dependency_overrides.clear()


def test_transport_defaults_are_closed_and_bounded():
    client, service = _client()
    try:
        response = client.get(
            "/api/v1/engineering-journal", params={"project_id": 1}
        )
        assert response.status_code == 200
        presentation = service.workspace_calls[0]["presentation"]
        assert presentation.sort == EngineeringJournalPresentationSort.CREATED_AT_DESC
        assert presentation.layout == EngineeringJournalPresentationLayout.LIST
        assert presentation.page == 1
        assert presentation.size == 20
        assert client.get(
            "/api/v1/engineering-journal", params={"project_id": 1, "size": 101}
        ).status_code == 422
    finally:
        app.dependency_overrides.clear()
