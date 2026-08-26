from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.project_completeness import (
    ClarificationQuestionV1,
    CompletenessClassification,
    CompletenessInvalidRequest,
    CompletenessObservationStatus,
    CompletenessProtectedNotFound,
    CompletenessUnavailable,
)


def test_closed_enums_and_payload_free_outcomes_are_strict():
    assert {item.value for item in CompletenessClassification} == {
        "present", "missing", "indeterminate", "not_disclosed", "not_applicable",
    }
    assert {item.value for item in CompletenessObservationStatus} == {"complete_within_bounds", "partial"}
    assert CompletenessProtectedNotFound().model_dump() == {"status": "protected_not_found"}
    assert CompletenessInvalidRequest().model_dump() == {"status": "invalid_request"}
    assert CompletenessUnavailable().model_dump() == {"status": "unavailable"}
    with pytest.raises(ValidationError):
        CompletenessProtectedNotFound(detail="forbidden")


def test_question_is_frozen_bounded_and_has_no_task_or_recommendation_fields():
    question = ClarificationQuestionV1(
        question_id="pc.project_basis.purpose.question.v1",
        rule_id="pc.project_basis.purpose",
        text="What governed purpose must be established?",
    )
    with pytest.raises(ValidationError):
        ClarificationQuestionV1(
            question_id="pc.project_basis.purpose.question.v1",
            rule_id="pc.project_basis.purpose", text="x", assignee_id=1,
        )
    with pytest.raises(ValidationError):
        question.text = "changed"


def test_no_human_private_storage_score_or_workflow_contract_field_exists():
    fields = set(ClarificationQuestionV1.model_fields)
    forbidden = {"human_id", "owner_id", "storage_url", "storage_key", "score", "percentage", "task_id", "due_date"}
    assert not fields & forbidden
