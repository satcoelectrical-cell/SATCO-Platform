import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.ai.capture_assistant import ProviderNeutralCaptureAssistant, canonical_provider_json
from app.enums.ai_capture_assistant import AdviceOutputKind
from app.enums.engineering_experience_capture import EngineeringExperienceSourceKind
from app.exceptions.ai_capture_assistant import AICaptureInvalidProviderResponse
from app.ports.ai_capture_assistant import AuthorizedCaptureContext, ProviderCaptureAdviceRequest


def _request():
    return ProviderCaptureAdviceRequest(
        1, uuid4(), AdviceOutputKind.CAPTURE_REFINEMENT, "Clarify",
        AuthorizedCaptureContext(
            uuid4(), uuid4(), 2, 3, "electrical", None,
            EngineeringExperienceSourceKind.OBSERVATION, "Original", None,
            9, "captured", 1, datetime.now(timezone.utc),
        ),
        ("Advisory only",),
    )


class Response:
    def __init__(self, value): self.value = value
    def __enter__(self): return self
    def __exit__(self, *args): return None
    def read(self, _limit): return json.dumps(self.value).encode()


def _payload(text="Suggested wording"):
    return dict(
        schema_version=1, status="success", suggested_text=text,
        observations=["Observed"], assumptions=[], missing_information=[],
        confidence="medium", confidence_rationale="Bounded source",
        limitations=["Human review required"], recommended_next_step="Review",
        refusal_code=None, provider_id="test", model_id="model", model_version="1",
    )


def test_canonical_request_and_valid_provider_response():
    request = _request()
    assert canonical_provider_json(request) == canonical_provider_json(request)
    provider = ProviderNeutralCaptureAssistant(
        endpoint="https://provider.invalid/advice", api_key="secret",
        opener=lambda *_args, **_kwargs: Response(_payload()),
    )
    assert provider.propose(request).suggested_text == "Suggested wording"


def test_authority_claim_and_malformed_output_fail_closed():
    unsafe_limitation = _payload()
    unsafe_limitation["limitations"] = ["Automatically accepted"]
    for payload in (_payload("This is approved."), unsafe_limitation, {"status": "success"}):
        provider = ProviderNeutralCaptureAssistant(
            endpoint="https://provider.invalid/advice", api_key="secret",
            opener=lambda *_args, _payload=payload, **_kwargs: Response(_payload),
        )
        with pytest.raises(AICaptureInvalidProviderResponse):
            provider.propose(_request())
