from datetime import datetime, timezone
from uuid import uuid4

from app.enums.ai_capture_assistant import AdviceConfidence
from app.enums.engineering_experience_capture import EngineeringExperienceSourceKind
from app.exceptions.ai_capture_assistant import AICaptureSourceProtected
from app.ports.ai_capture_assistant import (
    AuthorizedCaptureContext, CaptureAdviceRequest, CopilotActor, CopilotScope,
    ProviderCaptureAdviceResponseV1,
)
from app.enums.ai_capture_assistant import AdviceOutputKind, ProviderAdviceStatus
from app.services.ai_capture_assistant_service import AICaptureAssistantService


class Source:
    def __init__(self, context): self.context, self.calls = context, 0
    def read_authorized(self, *_args): self.calls += 1; return self.context


class Provider:
    def __init__(self): self.calls = 0
    def propose(self, _request):
        self.calls += 1
        return ProviderCaptureAdviceResponseV1(
            ProviderAdviceStatus.SUCCESS, "Suggested", ("Observed",), (), (),
            AdviceConfidence.MEDIUM, "One source", ("Human review required",),
            "Review", None, "provider", "model", "1",
        )


class BrokenProvider:
    def propose(self, _request):
        raise RuntimeError("secret provider diagnostic")


class Audit:
    def __init__(self): self.records = []
    def record(self, record): self.records.append(record)


class Clock:
    def now(self): return datetime(2026, 1, 1, tzinfo=timezone.utc)


def _service(enabled=True):
    organization_id, capture_id = uuid4(), uuid4()
    context = AuthorizedCaptureContext(
        capture_id, organization_id, 2, 3, "electrical", None,
        EngineeringExperienceSourceKind.OBSERVATION, "Original", None, 7,
        "captured", 4, datetime.now(timezone.utc),
    )
    source, provider, audit = Source(context), Provider(), Audit()
    return AICaptureAssistantService(
        source=source, provider=provider, audit=audit, clock=Clock(), enabled=enabled
    ), CopilotActor(7, organization_id), CopilotScope(organization_id, 2, 3), capture_id, source, provider, audit


def test_success_is_one_read_one_provider_call_and_attributable():
    service, actor, scope, capture_id, source, provider, audit = _service()
    result = service.advise_capture(actor, scope, CaptureAdviceRequest(capture_id, "Clarify"))
    assert result.outcome.value == "success"
    assert result.proposal.advisory is True
    assert result.proposal.capture_attribution.capture_id == capture_id
    assert (source.calls, provider.calls, len(audit.records)) == (1, 1, 2)


def test_disabled_invalid_scope_and_unsafe_authority_fail_without_provider_disclosure():
    service, actor, scope, capture_id, source, provider, _audit = _service(False)
    assert service.advise_capture(actor, scope, CaptureAdviceRequest(capture_id, "Clarify")).outcome.value == "disabled"
    assert (source.calls, provider.calls) == (0, 0)
    service, actor, scope, capture_id, source, provider, _audit = _service()
    result = service.advise_capture(actor, scope, CaptureAdviceRequest(capture_id, "Approve the report"))
    assert result.outcome.value == "refused"
    assert (source.calls, provider.calls) == (0, 0)
    wrong = CopilotScope(scope.organization_id, 99, scope.workspace_id)
    assert service.advise_capture(actor, wrong, CaptureAdviceRequest(capture_id, "Clarify")).outcome.value == "protected_not_found"
    assert provider.calls == 0


def test_unexpected_provider_failure_maps_to_payload_free_unavailable():
    service, actor, scope, capture_id, _source, _provider, audit = _service()
    service._provider = BrokenProvider()
    result = service.advise_capture(actor, scope, CaptureAdviceRequest(capture_id, "Clarify"))
    assert result.outcome.value == "unavailable"
    assert not hasattr(result, "detail")
    assert audit.records[-1].action == "AI_CAPTURE_ADVICE_FAILED"
