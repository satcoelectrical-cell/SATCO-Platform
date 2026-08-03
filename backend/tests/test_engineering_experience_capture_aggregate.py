from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.enums.engineering_experience_capture import EngineeringExperienceSourceKind
from app.models.engineering_experience_capture import EngineeringExperienceCapture
from app.models.engineering_experience_capture_command import (
    CreateEngineeringExperienceCapture,
    EngineeringExperienceCaptureActor,
    EngineeringExperienceCaptureContentRejected,
    EngineeringExperienceCaptureContextRejected,
    EngineeringExperienceCaptureMetadata,
    EngineeringExperienceCaptureSupersessionRejected,
    EngineeringExperienceCaptureTransitionRejected,
    EngineeringExperienceCaptureVersionMismatch,
    SupersedeEngineeringExperienceCapture,
    WithdrawEngineeringExperienceCapture,
)


NOW = datetime(2026, 8, 2, tzinfo=timezone.utc)


def metadata(actor_id=7, organization_id=None, rationale="capture submitted"):
    actor = EngineeringExperienceCaptureActor(actor_id, organization_id or uuid4())
    return EngineeringExperienceCaptureMetadata(actor, rationale, uuid4(), uuid4(), uuid4())


def create_command(meta=None, **overrides):
    meta = meta or metadata()
    values = {
        "metadata": meta,
        "organization_id": meta.actor.organization_id,
        "project_id": 11,
        "workspace_id": None,
        "discipline": None,
        "engineering_object_id": None,
        "source_kind": EngineeringExperienceSourceKind.OBSERVATION,
        "original_content": "  Pump vibration observed.\r\nNeeds review.  ",
        "source_reference": "  field-log-17  ",
        "creator_id": meta.actor.actor_id,
    }
    values.update(overrides)
    return CreateEngineeringExperienceCapture(**values)


def make_capture(**overrides):
    return EngineeringExperienceCapture.create(create_command(**overrides), NOW)[0]


def test_create_normalizes_and_preserves_original_capture_contract():
    capture, result = EngineeringExperienceCapture.create(create_command(), NOW)
    assert capture.original_content == "Pump vibration observed.\nNeeds review."
    assert capture.source_reference == "field-log-17"
    assert capture.lifecycle == "captured"
    assert capture.version == 1
    assert result.previous_version is None
    assert result.events[0].event_type == "EngineeringExperienceCaptured"
    assert "original_content" not in result.events[0].payload
    assert "source_reference" not in result.events[0].payload


@pytest.mark.parametrize("content", ["", "   ", "bad\x00text", "x" * 10_001])
def test_create_rejects_invalid_content(content):
    with pytest.raises(EngineeringExperienceCaptureContentRejected):
        make_capture(original_content=content)


def test_create_rejects_untrusted_scope_and_incoherent_context():
    meta = metadata()
    with pytest.raises(EngineeringExperienceCaptureContextRejected):
        make_capture(meta=meta, organization_id=uuid4())
    with pytest.raises(EngineeringExperienceCaptureContextRejected):
        make_capture(workspace_id=None, discipline="electrical")
    with pytest.raises(EngineeringExperienceCaptureContextRejected):
        make_capture(workspace_id=8, discipline=None)


def test_withdraw_increments_once_and_is_terminal():
    capture = make_capture()
    meta = metadata(capture.creator_id, capture.organization_id, "no longer applicable")
    result = capture.withdraw(WithdrawEngineeringExperienceCapture(meta, capture.id, 1), NOW)
    assert capture.lifecycle == "withdrawn"
    assert capture.version == 2
    assert result.previous_version == 1
    with pytest.raises(EngineeringExperienceCaptureTransitionRejected):
        capture.withdraw(WithdrawEngineeringExperienceCapture(meta, capture.id, 2), NOW)


def test_supersede_sets_distinct_replacement_and_increments_once():
    capture = make_capture()
    replacement_id = uuid4()
    meta = metadata(capture.creator_id, capture.organization_id, "corrected expression")
    result = capture.supersede(
        SupersedeEngineeringExperienceCapture(meta, capture.id, 1, replacement_id),
        NOW,
    )
    assert capture.lifecycle == "superseded"
    assert capture.superseded_by_capture_id == replacement_id
    assert capture.version == 2
    assert result.events[0].payload["replacement_capture_id"] == replacement_id


def test_supersede_rejects_self_and_stale_version_without_state_change():
    capture = make_capture()
    meta = metadata(capture.creator_id, capture.organization_id, "correction")
    with pytest.raises(EngineeringExperienceCaptureSupersessionRejected):
        capture.supersede(SupersedeEngineeringExperienceCapture(meta, capture.id, 1, capture.id), NOW)
    assert capture.lifecycle == "captured"
    assert capture.version == 1
    with pytest.raises(EngineeringExperienceCaptureVersionMismatch):
        capture.withdraw(WithdrawEngineeringExperienceCapture(meta, capture.id, 9), NOW)
    assert capture.version == 1


def test_original_content_and_provenance_have_no_mutation_command():
    capture = make_capture()
    assert not hasattr(capture, "update")
    assert not hasattr(capture, "delete")
    assert not hasattr(capture, "edit_content")
