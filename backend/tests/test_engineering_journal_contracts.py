"""PATCH-029 Sprint 1 contract and architecture evidence."""

import ast
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.enums.engineering_experience_capture import (
    EngineeringExperienceCaptureLifecycle,
    EngineeringExperienceSourceKind,
)
from app.enums.engineering_journal import (
    EngineeringJournalNavigationTargetKind,
    EngineeringJournalPresentationLayout,
    EngineeringJournalPresentationSort,
    EngineeringJournalView,
    EngineeringJournalViewAvailability,
    EngineeringJournalWorkspaceResultState,
)
from app.exceptions.engineering_journal import (
    EngineeringJournalInvalidPresentationCriteria,
    EngineeringJournalProtectedNotFound,
)
from app.schemas.engineering_journal import (
    EngineeringJournalAuthenticatedActor,
    EngineeringJournalCaptureDetailDTO,
    EngineeringJournalCaptureListItemDTO,
    EngineeringJournalCapturePageResultDTO,
    EngineeringJournalCountDTO,
    EngineeringJournalEmptyStateDTO,
    EngineeringJournalMemberViewDTO,
    EngineeringJournalNavigationDTO,
    EngineeringJournalNewCaptureViewDTO,
    EngineeringJournalPresentationDTO,
    EngineeringJournalProjectSelectionItemDTO,
    EngineeringJournalProjectSelectionPageDTO,
    EngineeringJournalReturnContextDTO,
    EngineeringJournalScopeDTO,
    EngineeringJournalUnavailableViewDTO,
    EngineeringJournalWorkspaceDTO,
)


NOW = datetime(2026, 8, 3, tzinfo=timezone.utc)


def _item(*, version: int = 1) -> EngineeringJournalCaptureListItemDTO:
    return EngineeringJournalCaptureListItemDTO(
        capture_id=uuid4(),
        project_id=1,
        workspace_id=2,
        discipline="industrial_automation",
        engineering_object_id=uuid4(),
        source_kind=EngineeringExperienceSourceKind.OBSERVATION,
        creator_id=3,
        lifecycle=EngineeringExperienceCaptureLifecycle.CAPTURED,
        version=version,
        created_at=NOW,
        updated_at=NOW,
    )


def _presentation(**values) -> EngineeringJournalPresentationDTO:
    return EngineeringJournalPresentationDTO(**values)


def _count(
    *, authorized: int = 1, filtered: int = 1, visible: int = 1
) -> EngineeringJournalCountDTO:
    return EngineeringJournalCountDTO(
        authorized_total=authorized,
        filtered_total=filtered,
        visible_total=visible,
    )


def test_closed_vocabularies_are_exact() -> None:
    assert {item.value for item in EngineeringJournalView} == {
        "new_capture",
        "inbox",
        "drafts",
        "under_review",
        "published",
        "superseded",
    }
    assert {item.value for item in EngineeringJournalViewAvailability} == {
        "available",
        "unavailable",
    }
    assert {item.value for item in EngineeringJournalWorkspaceResultState} == {
        "content",
        "authorized_empty",
        "filtered_empty",
        "capability_unavailable",
    }
    assert {item.value for item in EngineeringJournalNavigationTargetKind} == {
        "journal_view",
        "canonical_capture",
        "canonical_capability",
    }
    assert [item.value for item in EngineeringJournalPresentationSort] == [
        "created_at_desc"
    ]
    assert [item.value for item in EngineeringJournalPresentationLayout] == ["list"]


def test_actor_is_minimal_strict_and_immutable() -> None:
    actor = EngineeringJournalAuthenticatedActor(
        actor_id=1, organization_id=uuid4()
    )
    assert set(type(actor).model_fields) == {"actor_id", "organization_id"}
    with pytest.raises(ValidationError):
        EngineeringJournalAuthenticatedActor(
            actor_id=1, organization_id=uuid4(), role="admin"
        )
    with pytest.raises(ValidationError):
        actor.actor_id = 2


def test_projectless_scope_rejects_all_subordinate_context() -> None:
    organization_id = uuid4()
    scope = EngineeringJournalScopeDTO(organization_id=organization_id)
    assert scope.project_id is None
    for values in (
        {"workspace_id": 1},
        {"discipline": "electrical"},
        {"engineering_object_id": uuid4()},
    ):
        with pytest.raises(ValidationError):
            EngineeringJournalScopeDTO(organization_id=organization_id, **values)


def test_engineering_object_scope_requires_workspace() -> None:
    with pytest.raises(ValidationError):
        EngineeringJournalScopeDTO(
            organization_id=uuid4(),
            project_id=1,
            engineering_object_id=uuid4(),
        )


def test_project_selection_is_bounded_and_has_no_total_field() -> None:
    page = EngineeringJournalProjectSelectionPageDTO(
        items=(
            EngineeringJournalProjectSelectionItemDTO(
                project_id=1, display_name="Project A"
            ),
        ),
        page=1,
        size=20,
        visible_total=1,
        has_more=True,
    )
    assert "total" not in type(page).model_fields
    assert page.visible_total == 1
    with pytest.raises(ValidationError):
        EngineeringJournalProjectSelectionPageDTO(
            items=page.items,
            page=1,
            size=20,
            visible_total=0,
            has_more=False,
        )
    with pytest.raises(ValidationError):
        EngineeringJournalProjectSelectionPageDTO(
            items=(), page=1, size=101, visible_total=0, has_more=False
        )


def test_list_projection_excludes_detail_and_authority_fields() -> None:
    forbidden = {
        "original_content",
        "source_reference",
        "rationale",
        "allowed_actions",
        "journal_id",
        "journal_lifecycle",
        "review_state",
        "publication_standing",
        "organizational_memory_standing",
    }
    assert forbidden.isdisjoint(EngineeringJournalCaptureListItemDTO.model_fields)
    with pytest.raises(ValidationError):
        EngineeringJournalCaptureListItemDTO(
            **_item().model_dump(), original_content="protected"
        )


def test_detail_projection_is_separate_and_strict() -> None:
    item = _item()
    detail = EngineeringJournalCaptureDetailDTO(
        **item.model_dump(),
        original_content="Authorized engineering experience",
        source_reference=None,
        superseded_by_capture_id=None,
    )
    assert detail.original_content.startswith("Authorized")
    assert "original_content" not in EngineeringJournalCaptureListItemDTO.model_fields


@pytest.mark.parametrize(
    "values",
    (
        {"authorized_total": 1, "filtered_total": 2, "visible_total": 1},
        {"authorized_total": 2, "filtered_total": 1, "visible_total": 2},
        {"authorized_total": -1, "filtered_total": 0, "visible_total": 0},
    ),
)
def test_count_rejects_incoherent_totals(values) -> None:
    with pytest.raises(ValidationError):
        EngineeringJournalCountDTO(**values)


def test_page_binds_visible_total_to_items() -> None:
    with pytest.raises(ValidationError):
        EngineeringJournalCapturePageResultDTO(
            items=(_item(),),
            count=_count(authorized=2, filtered=2, visible=0),
            presentation=_presentation(),
        )


def test_no_filter_requires_filtered_total_to_equal_authorized_total() -> None:
    with pytest.raises(ValidationError):
        EngineeringJournalCapturePageResultDTO(
            items=(_item(),),
            count=_count(authorized=2, filtered=1, visible=1),
            presentation=_presentation(),
        )


def test_active_filter_allows_distinct_filtered_total() -> None:
    page = EngineeringJournalCapturePageResultDTO(
        items=(_item(),),
        count=_count(authorized=2, filtered=1, visible=1),
        presentation=_presentation(discipline="industrial_automation"),
    )
    assert page.count.filtered_total == 1


def test_member_view_binds_visible_total_to_returned_items() -> None:
    with pytest.raises(ValidationError):
        EngineeringJournalMemberViewDTO(
            items=(_item(),),
            count=_count(authorized=2, filtered=2, visible=0),
            presentation=_presentation(),
        )


def test_member_view_enforces_no_filter_count_semantics() -> None:
    with pytest.raises(ValidationError):
        EngineeringJournalMemberViewDTO(
            items=(_item(),),
            count=_count(authorized=2, filtered=1, visible=1),
            presentation=_presentation(),
        )
    filtered = EngineeringJournalMemberViewDTO(
        items=(_item(),),
        count=_count(authorized=2, filtered=1, visible=1),
        presentation=_presentation(discipline="industrial_automation"),
    )
    assert filtered.count.filtered_total == 1


def test_member_view_rejects_empty_member_content() -> None:
    with pytest.raises(ValidationError):
        EngineeringJournalMemberViewDTO(
            items=(),
            count=_count(authorized=0, filtered=0, visible=0),
            presentation=_presentation(),
        )


def test_presentation_contract_is_closed_and_bounded() -> None:
    presentation = _presentation()
    assert presentation.page == 1
    assert presentation.size == 20
    assert presentation.sort == EngineeringJournalPresentationSort.CREATED_AT_DESC
    assert presentation.layout == EngineeringJournalPresentationLayout.LIST
    for values in (
        {"page": 0},
        {"size": 0},
        {"size": 101},
        {"sort": "updated_at_desc"},
        {"layout": "grid"},
        {"grouping": "creator"},
        {"free_text": "secret"},
    ):
        with pytest.raises(ValidationError):
            EngineeringJournalPresentationDTO(**values)


def test_navigation_requires_correct_target_and_reauthorization() -> None:
    capture_id = uuid4()
    navigation = EngineeringJournalNavigationDTO(
        target_kind=EngineeringJournalNavigationTargetKind.CANONICAL_CAPTURE,
        canonical_target_id=capture_id,
        requires_reauthorization=True,
    )
    assert navigation.canonical_target_id == capture_id
    with pytest.raises(ValidationError):
        EngineeringJournalNavigationDTO(
            target_kind=EngineeringJournalNavigationTargetKind.CANONICAL_CAPTURE,
            canonical_target_id=capture_id,
            requires_reauthorization=False,
        )
    with pytest.raises(ValidationError):
        EngineeringJournalNavigationDTO(
            target_kind=EngineeringJournalNavigationTargetKind.JOURNAL_VIEW,
            requires_reauthorization=False,
        )


def test_return_context_rejects_workspace_without_project() -> None:
    with pytest.raises(ValidationError):
        EngineeringJournalReturnContextDTO(
            view=EngineeringJournalView.INBOX, workspace_id=1
        )


def test_unavailable_view_cannot_carry_members_or_counts() -> None:
    empty = EngineeringJournalEmptyStateDTO(
        result_state=EngineeringJournalWorkspaceResultState.CAPABILITY_UNAVAILABLE,
        semantic_category="capability_unavailable",
        presentation_criteria_active=False,
    )
    unavailable = EngineeringJournalUnavailableViewDTO(
        availability=EngineeringJournalViewAvailability.UNAVAILABLE,
        empty_state=empty,
    )
    assert "items" not in type(unavailable).model_fields
    assert "count" not in type(unavailable).model_fields


def test_projectless_workspace_has_no_members_counts_or_freshness() -> None:
    selection = EngineeringJournalProjectSelectionPageDTO(
        items=(), page=1, size=20, visible_total=0, has_more=False
    )
    empty = EngineeringJournalEmptyStateDTO(
        result_state=EngineeringJournalWorkspaceResultState.AUTHORIZED_EMPTY,
        semantic_category="project_selection_required",
        presentation_criteria_active=False,
    )
    workspace = EngineeringJournalWorkspaceDTO(
        view=EngineeringJournalView.INBOX,
        availability=EngineeringJournalViewAvailability.AVAILABLE,
        result_state=EngineeringJournalWorkspaceResultState.AUTHORIZED_EMPTY,
        scope=EngineeringJournalScopeDTO(organization_id=uuid4()),
        view_content=empty,
        presentation=_presentation(),
        project_selection=selection,
    )
    assert workspace.canonical_freshness is None
    with pytest.raises(ValidationError):
        EngineeringJournalWorkspaceDTO(
            **workspace.model_dump(exclude={"canonical_freshness"}),
            canonical_freshness=1,
        )


def test_member_workspace_requires_project_and_exact_freshness() -> None:
    first = _item(version=2)
    second = _item(version=4)
    member_view = EngineeringJournalMemberViewDTO(
        items=(first, second),
        count=_count(authorized=2, filtered=2, visible=2),
        presentation=_presentation(),
    )
    workspace = EngineeringJournalWorkspaceDTO(
        view=EngineeringJournalView.INBOX,
        availability=EngineeringJournalViewAvailability.AVAILABLE,
        result_state=EngineeringJournalWorkspaceResultState.CONTENT,
        scope=EngineeringJournalScopeDTO(
            organization_id=uuid4(), project_id=1
        ),
        view_content=member_view,
        presentation=_presentation(),
        canonical_freshness=4,
    )
    assert workspace.canonical_freshness == 4
    with pytest.raises(ValidationError):
        EngineeringJournalWorkspaceDTO(
            **workspace.model_dump(exclude={"canonical_freshness"}),
            canonical_freshness=3,
        )


def test_inbox_rejects_non_captured_members() -> None:
    superseded = _item().model_copy(
        update={"lifecycle": EngineeringExperienceCaptureLifecycle.SUPERSEDED}
    )
    members = EngineeringJournalMemberViewDTO(
        items=(superseded,),
        count=_count(),
        presentation=_presentation(),
    )
    with pytest.raises(ValidationError):
        EngineeringJournalWorkspaceDTO(
            view=EngineeringJournalView.INBOX,
            availability=EngineeringJournalViewAvailability.AVAILABLE,
            result_state=EngineeringJournalWorkspaceResultState.CONTENT,
            scope=EngineeringJournalScopeDTO(
                organization_id=uuid4(), project_id=1
            ),
            view_content=members,
            presentation=_presentation(),
            canonical_freshness=1,
        )


def test_superseded_rejects_non_superseded_members() -> None:
    members = EngineeringJournalMemberViewDTO(
        items=(_item(),), count=_count(), presentation=_presentation()
    )
    with pytest.raises(ValidationError):
        EngineeringJournalWorkspaceDTO(
            view=EngineeringJournalView.SUPERSEDED,
            availability=EngineeringJournalViewAvailability.AVAILABLE,
            result_state=EngineeringJournalWorkspaceResultState.CONTENT,
            scope=EngineeringJournalScopeDTO(
                organization_id=uuid4(), project_id=1
            ),
            view_content=members,
            presentation=_presentation(),
            canonical_freshness=1,
        )


@pytest.mark.parametrize(
    "result_state",
    (
        EngineeringJournalWorkspaceResultState.AUTHORIZED_EMPTY,
        EngineeringJournalWorkspaceResultState.FILTERED_EMPTY,
        EngineeringJournalWorkspaceResultState.CAPABILITY_UNAVAILABLE,
    ),
)
def test_non_content_states_reject_member_content(result_state) -> None:
    members = EngineeringJournalMemberViewDTO(
        items=(_item(),), count=_count(), presentation=_presentation()
    )
    with pytest.raises(ValidationError):
        EngineeringJournalWorkspaceDTO(
            view=EngineeringJournalView.INBOX,
            availability=EngineeringJournalViewAvailability.AVAILABLE,
            result_state=result_state,
            scope=EngineeringJournalScopeDTO(
                organization_id=uuid4(), project_id=1
            ),
            view_content=members,
            presentation=_presentation(),
            canonical_freshness=1,
        )


def test_new_capture_is_navigation_only_without_count_or_members() -> None:
    content = EngineeringJournalNewCaptureViewDTO(
        availability=EngineeringJournalViewAvailability.AVAILABLE,
        navigation=EngineeringJournalNavigationDTO(
            target_kind=(
                EngineeringJournalNavigationTargetKind.CANONICAL_CAPABILITY
            ),
            canonical_target_id=1,
            requires_reauthorization=True,
        ),
    )
    workspace = EngineeringJournalWorkspaceDTO(
        view=EngineeringJournalView.NEW_CAPTURE,
        availability=EngineeringJournalViewAvailability.AVAILABLE,
        result_state=EngineeringJournalWorkspaceResultState.CONTENT,
        scope=EngineeringJournalScopeDTO(organization_id=uuid4(), project_id=1),
        view_content=content,
        presentation=_presentation(),
    )
    assert "items" not in type(workspace.view_content).model_fields
    assert "count" not in type(workspace.view_content).model_fields

    members = EngineeringJournalMemberViewDTO(
        items=(_item(),), count=_count(), presentation=_presentation()
    )
    with pytest.raises(ValidationError):
        EngineeringJournalWorkspaceDTO(
            view=EngineeringJournalView.NEW_CAPTURE,
            availability=EngineeringJournalViewAvailability.AVAILABLE,
            result_state=EngineeringJournalWorkspaceResultState.CONTENT,
            scope=EngineeringJournalScopeDTO(
                organization_id=uuid4(), project_id=1
            ),
            view_content=members,
            presentation=_presentation(),
            canonical_freshness=1,
        )


def test_capability_unavailable_is_successful_workspace_state() -> None:
    empty = EngineeringJournalEmptyStateDTO(
        result_state=EngineeringJournalWorkspaceResultState.CAPABILITY_UNAVAILABLE,
        semantic_category="capability_unavailable",
        presentation_criteria_active=False,
    )
    unavailable = EngineeringJournalUnavailableViewDTO(
        availability=EngineeringJournalViewAvailability.UNAVAILABLE,
        empty_state=empty,
    )
    workspace = EngineeringJournalWorkspaceDTO(
        view=EngineeringJournalView.DRAFTS,
        availability=EngineeringJournalViewAvailability.UNAVAILABLE,
        result_state=EngineeringJournalWorkspaceResultState.CAPABILITY_UNAVAILABLE,
        scope=EngineeringJournalScopeDTO(organization_id=uuid4(), project_id=1),
        view_content=unavailable,
        presentation=_presentation(),
    )
    assert workspace.result_state == (
        EngineeringJournalWorkspaceResultState.CAPABILITY_UNAVAILABLE
    )
    assert "count" not in type(workspace.view_content).model_fields


def test_stable_exceptions_are_disclosure_safe() -> None:
    cases = (
        (
            EngineeringJournalProtectedNotFound(),
            404,
            "ENGINEERING_JOURNAL_NOT_FOUND",
        ),
        (
            EngineeringJournalInvalidPresentationCriteria(),
            422,
            "ENGINEERING_JOURNAL_INVALID_PRESENTATION_CRITERIA",
        ),
    )
    for error, status_code, code in cases:
        assert error.status_code == status_code
        assert error.code == code
        assert "select " not in error.message.lower()
        assert "organization_id" not in error.message


def test_capability_unavailable_is_not_an_error_contract() -> None:
    from app.exceptions import engineering_journal

    assert not hasattr(
        engineering_journal, "EngineeringJournalCapabilityUnavailable"
    )


def test_journal_contract_modules_have_no_forbidden_dependencies() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    relative_paths = (
        "app/enums/engineering_journal.py",
        "app/schemas/engineering_journal.py",
        "app/ports/engineering_journal.py",
        "app/exceptions/engineering_journal.py",
    )
    forbidden_roots = {
        "fastapi",
        "sqlalchemy",
        "alembic",
        "app.repositories",
    }
    for relative_path in relative_paths:
        tree = ast.parse((backend_root / relative_path).read_text())
        imports = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        imports.update(
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        )
        assert not any(
            imported == forbidden or imported.startswith(f"{forbidden}.")
            for imported in imports
            for forbidden in forbidden_roots
        )


def test_qg6_and_qg7_no_domain_or_persistence_boundary() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    assert not (backend_root / "app/models/engineering_journal.py").exists()
    assert not (
        backend_root / "app/repositories/engineering_journal_repository.py"
    ).exists()
    assert not (
        backend_root / "app/repositories/engineering_journal_unit_of_work.py"
    ).exists()
    assert not list((backend_root / "migrations").rglob("*journal*"))
    assert not hasattr(__import__("app.enums.engineering_journal", fromlist=["x"]), "EngineeringJournalLifecycle")
