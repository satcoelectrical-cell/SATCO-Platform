"""Closed presentation vocabularies for the Engineering Journal."""

from enum import StrEnum


class EngineeringJournalView(StrEnum):
    """The six presentation views authorized by PATCH-029."""

    NEW_CAPTURE = "new_capture"
    INBOX = "inbox"
    DRAFTS = "drafts"
    UNDER_REVIEW = "under_review"
    PUBLISHED = "published"
    SUPERSEDED = "superseded"


class EngineeringJournalViewAvailability(StrEnum):
    """Whether the canonical capability behind a view is available."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class EngineeringJournalWorkspaceResultState(StrEnum):
    """Successful presentation states; protected not found is not one."""

    CONTENT = "content"
    AUTHORIZED_EMPTY = "authorized_empty"
    FILTERED_EMPTY = "filtered_empty"
    CAPABILITY_UNAVAILABLE = "capability_unavailable"


class EngineeringJournalNavigationTargetKind(StrEnum):
    """Authorized kinds of non-authoritative navigation metadata."""

    JOURNAL_VIEW = "journal_view"
    CANONICAL_CAPTURE = "canonical_capture"
    CANONICAL_CAPABILITY = "canonical_capability"


class EngineeringJournalPresentationSort(StrEnum):
    """Closed temporary ordering contract for PATCH-029."""

    CREATED_AT_DESC = "created_at_desc"


class EngineeringJournalPresentationLayout(StrEnum):
    """Closed temporary layout contract for PATCH-029."""

    LIST = "list"
