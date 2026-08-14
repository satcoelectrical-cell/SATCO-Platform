from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.enums.ai_capture_assistant import AdviceConfidence, AdviceOutputKind, ProviderAdviceStatus
from app.ports.ai_capture_assistant import CopilotActor, CopilotScope
from app.schemas.ai_capture_assistant import CaptureAdviceRequestSchema, ProviderCaptureAdviceResponseSchema


def test_actor_scope_and_request_are_closed():
    organization_id = uuid4()
    assert CopilotActor(1, organization_id).organization_id == organization_id
    assert CopilotScope(organization_id, 2, None).project_id == 2
    request = CaptureAdviceRequestSchema(
        capture_id=uuid4(), project_id=2, human_instruction="Clarify this observation."
    )
    assert request.output_kind is AdviceOutputKind.CAPTURE_REFINEMENT
    with pytest.raises(ValidationError):
        CaptureAdviceRequestSchema(capture_id=uuid4(), project_id=2, human_instruction="x", extra=True)


def test_provider_result_rejects_wrong_shape_duplicates_and_missing_limitations():
    base = dict(
        schema_version=1, status=ProviderAdviceStatus.SUCCESS, suggested_text="Suggested wording",
        observations=("Observed A",), assumptions=(), missing_information=(),
        confidence=AdviceConfidence.MEDIUM, confidence_rationale="Source is current.",
        limitations=("Human review required.",), recommended_next_step="Review.",
        refusal_code=None, provider_id="p", model_id="m", model_version="1",
    )
    ProviderCaptureAdviceResponseSchema.model_validate(base)
    for changes in (
        {"limitations": ()},
        {"observations": ("same", "same")},
        {"status": ProviderAdviceStatus.REFUSED, "suggested_text": "bad", "refusal_code": "insufficient_context"},
    ):
        with pytest.raises(ValidationError):
            ProviderCaptureAdviceResponseSchema.model_validate(base | changes)


def test_human_instruction_is_not_silently_normalized_and_identifiers_are_safe():
    request = CaptureAdviceRequestSchema(
        capture_id=uuid4(), project_id=2, human_instruction="  Human wording  "
    )
    assert request.human_instruction == "  Human wording  "
    base = dict(
        schema_version=1, status=ProviderAdviceStatus.SUCCESS,
        suggested_text="Suggested", observations=(), assumptions=(),
        missing_information=(), confidence=AdviceConfidence.LOW,
        confidence_rationale="Limited context", limitations=("Review",),
        recommended_next_step="Review", refusal_code=None,
        provider_id="provider", model_id="model", model_version="1",
    )
    with pytest.raises(ValidationError):
        ProviderCaptureAdviceResponseSchema.model_validate(base | {"provider_id": "source content here"})
