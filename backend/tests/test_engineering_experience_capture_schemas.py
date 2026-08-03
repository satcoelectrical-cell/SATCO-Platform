from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.engineering_experience_capture import (
    EngineeringExperienceCaptureCreate,
    EngineeringExperienceCaptureFilter,
    SupersedeEngineeringExperienceCaptureRequest,
    WithdrawEngineeringExperienceCaptureRequest,
)


def test_create_schema_accepts_bounded_explicit_fields():
    data = EngineeringExperienceCaptureCreate(
        project_id=1,
        workspace_id=2,
        engineering_object_id=uuid4(),
        source_kind="observation",
        original_content="Observed condition",
        source_reference="field-note-1",
    )
    assert data.project_id == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("organization_id", uuid4()),
        ("creator_id", 7),
        ("discipline", "electrical"),
        ("lifecycle", "captured"),
        ("version", 1),
        ("approved", True),
        ("provider", "model"),
    ],
)
def test_create_schema_rejects_trusted_or_out_of_scope_fields(field, value):
    payload = {
        "project_id": 1,
        "source_kind": "question",
        "original_content": "What is the required set point?",
        field: value,
    }
    with pytest.raises(ValidationError):
        EngineeringExperienceCaptureCreate(**payload)


def test_object_reference_requires_workspace():
    with pytest.raises(ValidationError):
        EngineeringExperienceCaptureCreate(
            project_id=1,
            engineering_object_id=uuid4(),
            source_kind="observation",
            original_content="Observed condition",
        )


def test_commands_require_positive_version_and_bounded_rationale():
    with pytest.raises(ValidationError):
        WithdrawEngineeringExperienceCaptureRequest(expected_version=0, rationale="withdraw")
    with pytest.raises(ValidationError):
        SupersedeEngineeringExperienceCaptureRequest(
            expected_version=1,
            replacement_capture_id=uuid4(),
            rationale="x" * 1_001,
        )


def test_filter_is_closed_and_controlled():
    filters = EngineeringExperienceCaptureFilter(lifecycle="captured", source_kind="assumption")
    assert filters.lifecycle.value == "captured"
    with pytest.raises(ValidationError):
        EngineeringExperienceCaptureFilter(search="pump")
