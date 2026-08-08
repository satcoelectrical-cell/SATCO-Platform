"""Strict, immutable, transport-neutral Engineering Journal projections."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

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


class EngineeringJournalDTO(BaseModel):
    """Base contract for immutable Journal application projections."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class EngineeringJournalAuthenticatedActor(EngineeringJournalDTO):
    """Minimum trusted identity context owned by the Journal boundary."""

    actor_id: int = Field(gt=0)
    organization_id: UUID


class EngineeringJournalScopeDTO(EngineeringJournalDTO):
    """Authorized canonical context for one Journal composition request."""

    organization_id: UUID
    project_id: int | None = Field(default=None, gt=0)
    workspace_id: int | None = Field(default=None, gt=0)
    discipline: str | None = Field(default=None, min_length=1)
    engineering_object_id: UUID | None = None

    @model_validator(mode="after")
    def validate_scope_hierarchy(self) -> "EngineeringJournalScopeDTO":
        """Prevent subordinate context when the Project shell is unselected."""

        if self.project_id is None and any(
            value is not None
            for value in (
                self.workspace_id,
                self.discipline,
                self.engineering_object_id,
            )
        ):
            raise ValueError("Project-less scope cannot contain subordinate context")
        if self.engineering_object_id is not None and self.workspace_id is None:
            raise ValueError("Engineering Object context requires Workspace context")
        return self


class EngineeringJournalProjectSelectionItemDTO(EngineeringJournalDTO):
    """Minimal presentation of one actor-authorized canonical Project."""

    project_id: int = Field(gt=0)
    display_name: str = Field(min_length=1, max_length=200)


class EngineeringJournalProjectSelectionPageDTO(EngineeringJournalDTO):
    """Bounded Project choices without a hidden or global total."""

    items: tuple[EngineeringJournalProjectSelectionItemDTO, ...] = Field(
        max_length=100
    )
    page: int = Field(ge=1)
    size: int = Field(ge=1, le=100)
    visible_total: int = Field(ge=0, le=100)
    has_more: bool

    @model_validator(mode="after")
    def validate_visible_total(self) -> "EngineeringJournalProjectSelectionPageDTO":
        """Bind disclosed page count exactly to returned authorized choices."""

        if self.visible_total != len(self.items):
            raise ValueError("visible_total must equal returned Project choices")
        if len(self.items) > self.size:
            raise ValueError("Project choices exceed requested page size")
        return self


class EngineeringJournalPresentationDTO(EngineeringJournalDTO):
    """Closed temporary presentation criteria for PATCH-029."""

    sort: EngineeringJournalPresentationSort = (
        EngineeringJournalPresentationSort.CREATED_AT_DESC
    )
    source_kind: EngineeringExperienceSourceKind | None = None
    discipline: str | None = Field(default=None, min_length=1)
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    layout: EngineeringJournalPresentationLayout = (
        EngineeringJournalPresentationLayout.LIST
    )

    @property
    def filter_active(self) -> bool:
        """Return whether an approved temporary filter is active."""

        return self.source_kind is not None or self.discipline is not None


class EngineeringJournalCaptureListItemDTO(EngineeringJournalDTO):
    """Minimal authorized Capture projection safe for Journal lists."""

    capture_id: UUID
    project_id: int = Field(gt=0)
    workspace_id: int | None = Field(default=None, gt=0)
    discipline: str | None = Field(default=None, min_length=1)
    engineering_object_id: UUID | None = None
    source_kind: EngineeringExperienceSourceKind
    creator_id: int | None = Field(default=None, gt=0)
    lifecycle: EngineeringExperienceCaptureLifecycle
    version: int = Field(gt=0)
    created_at: datetime
    updated_at: datetime


class EngineeringJournalCaptureDetailDTO(EngineeringJournalCaptureListItemDTO):
    """Separately authorized Capture detail projection."""

    original_content: str = Field(min_length=1, max_length=10_000)
    source_reference: str | None = Field(default=None, min_length=1, max_length=512)
    creator_id: int = Field(gt=0)
    superseded_by_capture_id: UUID | None = None


class EngineeringJournalCountDTO(EngineeringJournalDTO):
    """Protected three-level count projection for an authorized result page."""

    authorized_total: int = Field(ge=0)
    filtered_total: int = Field(ge=0)
    visible_total: int = Field(ge=0, le=100)
    is_authoritative_for_scope: Literal[True] = True

    @model_validator(mode="after")
    def validate_count_order(self) -> "EngineeringJournalCountDTO":
        """Reject incoherent protected totals."""

        if self.filtered_total > self.authorized_total:
            raise ValueError("filtered_total cannot exceed authorized_total")
        if self.visible_total > self.filtered_total:
            raise ValueError("visible_total cannot exceed filtered_total")
        return self


class EngineeringJournalCapturePageResultDTO(EngineeringJournalDTO):
    """One bounded authorized Journal page with coherent count semantics."""

    items: tuple[EngineeringJournalCaptureListItemDTO, ...] = Field(max_length=100)
    count: EngineeringJournalCountDTO
    presentation: EngineeringJournalPresentationDTO

    @model_validator(mode="after")
    def validate_page(self) -> "EngineeringJournalCapturePageResultDTO":
        """Bind page members and no-filter totals to the accepted contract."""

        if self.count.visible_total != len(self.items):
            raise ValueError("visible_total must equal returned Capture items")
        if len(self.items) > self.presentation.size:
            raise ValueError("Capture items exceed requested page size")
        if (
            not self.presentation.filter_active
            and self.count.filtered_total != self.count.authorized_total
        ):
            raise ValueError(
                "filtered_total must equal authorized_total without filters"
            )
        return self


class EngineeringJournalEmptyStateDTO(EngineeringJournalDTO):
    """Safe successful empty or unavailable presentation metadata."""

    result_state: Literal[
        EngineeringJournalWorkspaceResultState.AUTHORIZED_EMPTY,
        EngineeringJournalWorkspaceResultState.FILTERED_EMPTY,
        EngineeringJournalWorkspaceResultState.CAPABILITY_UNAVAILABLE,
    ]
    semantic_category: str = Field(min_length=1, max_length=100)
    presentation_criteria_active: bool
    recovery_navigation: tuple["EngineeringJournalNavigationDTO", ...] = ()


class EngineeringJournalReturnContextDTO(EngineeringJournalDTO):
    """Minimal non-authoritative context for a safe Journal return."""

    view: EngineeringJournalView
    project_id: int | None = Field(default=None, gt=0)
    workspace_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_return_context(self) -> "EngineeringJournalReturnContextDTO":
        """Reject a Workspace return without canonical Project context."""

        if self.workspace_id is not None and self.project_id is None:
            raise ValueError("Workspace return context requires Project context")
        return self


class EngineeringJournalNavigationDTO(EngineeringJournalDTO):
    """Non-authoritative navigation metadata requiring destination checks."""

    target_kind: EngineeringJournalNavigationTargetKind
    canonical_target_id: UUID | int | None = None
    target_view: EngineeringJournalView | None = None
    return_context: EngineeringJournalReturnContextDTO | None = None
    requires_reauthorization: bool

    @model_validator(mode="after")
    def validate_target(self) -> "EngineeringJournalNavigationDTO":
        """Keep navigation target shapes deterministic and non-authoritative."""

        if self.target_kind == EngineeringJournalNavigationTargetKind.JOURNAL_VIEW:
            if self.target_view is None or self.canonical_target_id is not None:
                raise ValueError("Journal-view navigation requires only target_view")
        elif self.canonical_target_id is None:
            raise ValueError("Canonical navigation requires a target identifier")
        if (
            self.target_kind
            in {
                EngineeringJournalNavigationTargetKind.CANONICAL_CAPTURE,
                EngineeringJournalNavigationTargetKind.CANONICAL_CAPABILITY,
            }
            and not self.requires_reauthorization
        ):
            raise ValueError("Canonical navigation requires reauthorization")
        return self


class EngineeringJournalNewCaptureViewDTO(EngineeringJournalDTO):
    """Action-oriented navigation to canonical Universal Capture creation."""

    availability: Literal[EngineeringJournalViewAvailability.AVAILABLE]
    navigation: EngineeringJournalNavigationDTO


class EngineeringJournalMemberViewDTO(EngineeringJournalDTO):
    """Authorized member-bearing Inbox or Superseded projection."""

    items: tuple[EngineeringJournalCaptureListItemDTO, ...] = Field(max_length=100)
    count: EngineeringJournalCountDTO
    presentation: EngineeringJournalPresentationDTO

    @model_validator(mode="after")
    def validate_members_and_count(self) -> "EngineeringJournalMemberViewDTO":
        """Bind protected totals to the returned authorized member page."""

        if not self.items:
            raise ValueError("Member view requires at least one Capture member")
        if self.count.visible_total != len(self.items):
            raise ValueError("visible_total must equal returned Capture items")
        if len(self.items) > self.presentation.size:
            raise ValueError("Capture items exceed requested page size")
        if (
            not self.presentation.filter_active
            and self.count.filtered_total != self.count.authorized_total
        ):
            raise ValueError(
                "filtered_total must equal authorized_total without filters"
            )
        return self


class EngineeringJournalUnavailableViewDTO(EngineeringJournalDTO):
    """Explicit absence of an approved canonical downstream capability."""

    availability: Literal[EngineeringJournalViewAvailability.UNAVAILABLE]
    empty_state: EngineeringJournalEmptyStateDTO

    @model_validator(mode="after")
    def validate_unavailable_state(self) -> "EngineeringJournalUnavailableViewDTO":
        """Require the non-authoritative capability-unavailable state."""

        if (
            self.empty_state.result_state
            != EngineeringJournalWorkspaceResultState.CAPABILITY_UNAVAILABLE
        ):
            raise ValueError("Unavailable view requires capability_unavailable")
        return self


EngineeringJournalViewContent = Annotated[
    EngineeringJournalNewCaptureViewDTO
    | EngineeringJournalMemberViewDTO
    | EngineeringJournalUnavailableViewDTO
    | EngineeringJournalEmptyStateDTO,
    Field(union_mode="left_to_right"),
]


class EngineeringJournalWorkspaceDTO(EngineeringJournalDTO):
    """Complete authorized, noncanonical Journal workspace projection."""

    view: EngineeringJournalView
    availability: EngineeringJournalViewAvailability
    result_state: EngineeringJournalWorkspaceResultState
    scope: EngineeringJournalScopeDTO
    view_content: EngineeringJournalViewContent
    navigation: tuple[EngineeringJournalNavigationDTO, ...] = ()
    presentation: EngineeringJournalPresentationDTO
    canonical_freshness: int | None = Field(default=None, gt=0)
    project_selection: EngineeringJournalProjectSelectionPageDTO | None = None

    @model_validator(mode="after")
    def validate_workspace(self) -> "EngineeringJournalWorkspaceDTO":
        """Enforce Project-less, availability, membership, and freshness rules."""

        projectless = self.scope.project_id is None
        if projectless:
            if self.project_selection is None:
                raise ValueError("Project-less shell requires Project selection")
            if isinstance(self.view_content, EngineeringJournalMemberViewDTO):
                raise ValueError("Project-less shell cannot contain Capture members")
            if self.canonical_freshness is not None:
                raise ValueError("Project-less shell has no Capture freshness")
        elif self.project_selection is not None:
            raise ValueError("Selected Project scope cannot contain Project choices")

        member_content = isinstance(
            self.view_content, EngineeringJournalMemberViewDTO
        )
        empty_content = isinstance(self.view_content, EngineeringJournalEmptyStateDTO)
        unavailable_content = isinstance(
            self.view_content, EngineeringJournalUnavailableViewDTO
        )
        new_capture_content = isinstance(
            self.view_content, EngineeringJournalNewCaptureViewDTO
        )

        if self.result_state in {
            EngineeringJournalWorkspaceResultState.AUTHORIZED_EMPTY,
            EngineeringJournalWorkspaceResultState.FILTERED_EMPTY,
            EngineeringJournalWorkspaceResultState.CAPABILITY_UNAVAILABLE,
        } and member_content:
            raise ValueError("Non-content workspace state cannot contain members")
        if self.result_state == EngineeringJournalWorkspaceResultState.CONTENT:
            if not (member_content or new_capture_content):
                raise ValueError("Content state requires content-bearing view")

        if self.view == EngineeringJournalView.NEW_CAPTURE:
            if not new_capture_content:
                raise ValueError("New Capture requires navigation-only content")
            if self.result_state != EngineeringJournalWorkspaceResultState.CONTENT:
                raise ValueError("New Capture requires content result state")
        elif new_capture_content:
            raise ValueError("New Capture content cannot represent another view")

        if member_content:
            expected_lifecycle = {
                EngineeringJournalView.INBOX: (
                    EngineeringExperienceCaptureLifecycle.CAPTURED
                ),
                EngineeringJournalView.SUPERSEDED: (
                    EngineeringExperienceCaptureLifecycle.SUPERSEDED
                ),
            }.get(self.view)
            if expected_lifecycle is None:
                raise ValueError("Selected Journal view cannot contain members")
            if any(
                item.lifecycle != expected_lifecycle
                for item in self.view_content.items
            ):
                raise ValueError("Capture lifecycle is incompatible with Journal view")

        if self.availability == EngineeringJournalViewAvailability.UNAVAILABLE:
            if self.result_state != EngineeringJournalWorkspaceResultState.CAPABILITY_UNAVAILABLE:
                raise ValueError("Unavailable capability requires unavailable result state")
            if not unavailable_content:
                raise ValueError("Unavailable capability requires unavailable view content")
        elif unavailable_content:
            raise ValueError("Unavailable content requires unavailable availability")

        if self.result_state == EngineeringJournalWorkspaceResultState.CAPABILITY_UNAVAILABLE:
            if not unavailable_content:
                raise ValueError("Unavailable result requires unavailable view content")
        elif empty_content and (
            self.view_content.result_state != self.result_state
        ):
            raise ValueError("Empty-state content must match workspace result state")

        items: tuple[EngineeringJournalCaptureListItemDTO, ...] = ()
        if member_content:
            items = self.view_content.items
        expected_freshness = max((item.version for item in items), default=None)
        if self.canonical_freshness != expected_freshness:
            raise ValueError("canonical_freshness must match returned Capture versions")
        return self


EngineeringJournalEmptyStateDTO.model_rebuild()
