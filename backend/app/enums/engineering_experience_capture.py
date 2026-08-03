"""Controlled vocabularies for Engineering Experience Capture."""

from enum import StrEnum


class EngineeringExperienceCaptureLifecycle(StrEnum):
    CAPTURED = "captured"
    WITHDRAWN = "withdrawn"
    SUPERSEDED = "superseded"


class EngineeringExperienceSourceKind(StrEnum):
    OBSERVATION = "observation"
    QUESTION = "question"
    ASSUMPTION = "assumption"
    RATIONALE = "rationale"
    DISCUSSION_NOTE = "discussion_note"
    CORRESPONDENCE_NOTE = "correspondence_note"
    FIELD_NOTE = "field_note"
    REVIEW_NOTE = "review_note"
    OUTCOME = "outcome"
    LESSON_CANDIDATE = "lesson_candidate"
    EXTERNAL_RECORD_NOTE = "external_record_note"
