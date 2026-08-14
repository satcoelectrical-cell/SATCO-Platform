"""Ephemeral, advisory-only PATCH-035 application service."""

from __future__ import annotations

from hashlib import sha256
import json
import re
from uuid import uuid4

from app.ai.capture_assistant import canonical_provider_json
from app.enums.ai_capture_assistant import AdviceOutcome, AdviceRefusalCode, ProviderAdviceStatus
from app.exceptions.ai_capture_assistant import (
    AICaptureDependencyUnavailable,
    AICaptureInvalidProviderResponse,
    AICaptureProviderUnavailable,
    AICaptureSourceProtected,
)
from app.ports.ai_capture_assistant import (
    CaptureAdviceDisabled,
    CaptureAdviceInvalidRequest,
    CaptureAdviceProposal,
    CaptureAdviceProtectedNotFound,
    CaptureAdviceRefused,
    CaptureAdviceRequest,
    CaptureAdviceSuccess,
    CaptureAdviceUnavailable,
    CaptureAttribution,
    CopilotActor,
    CopilotAuditRecord,
    CopilotScope,
    ProviderAttribution,
    ProviderCaptureAdviceRequest,
)


_UNSAFE = re.compile(
    r"\b(approve|certify|accept (?:the )?(?:report|design)|admit (?:to )?memory|"
    r"send (?:the )?(?:customer|client)|execute autonomously|mutate)\b",
    re.IGNORECASE,
)
_SAFETY = (
    "Advisory output only; never claim approval, certification, or finality.",
    "Separate observations, assumptions, missing information, and limitations.",
    "Do not invent engineering facts; require Human review.",
)


def _digest(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return sha256(value).hexdigest()


class AICaptureAssistantService:
    def __init__(self, *, source, provider, audit, clock, enabled: bool) -> None:
        self._source = source
        self._provider = provider
        self._audit = audit
        self._clock = clock
        self._enabled = enabled

    @staticmethod
    def _audit_record(request_id, actor, action, outcome, instruction_digest, scope, **values):
        return CopilotAuditRecord(
            request_id=request_id, actor_id=actor.actor_id, action=action,
            outcome=outcome, instruction_digest=instruction_digest,
            context_digest=values.get("context_digest"),
            output_digest=values.get("output_digest"),
            provider_id=values.get("provider_id"), model_id=values.get("model_id"),
            has_workspace_scope=scope.workspace_id is not None,
        )

    def _record(self, record) -> bool:
        try:
            self._audit.record(record)
            return True
        except Exception:
            return False

    def advise_capture(self, actor: CopilotActor, scope: CopilotScope, request: CaptureAdviceRequest):
        if not self._enabled:
            return CaptureAdviceDisabled()
        if (
            not isinstance(actor, CopilotActor) or not isinstance(scope, CopilotScope)
            or not isinstance(request, CaptureAdviceRequest)
            or actor.organization_id != scope.organization_id
        ):
            return CaptureAdviceInvalidRequest()
        instruction = request.human_instruction.strip()
        if not instruction or len(instruction) > 2000 or instruction != request.human_instruction:
            return CaptureAdviceInvalidRequest()
        request_id = uuid4()
        instruction_digest = _digest(instruction)
        if _UNSAFE.search(instruction):
            requested = self._audit_record(
                request_id, actor, "AI_CAPTURE_ADVICE_REQUESTED", "requested",
                instruction_digest, scope,
            )
            refused = self._audit_record(
                request_id, actor, "AI_CAPTURE_ADVICE_REFUSED", "refused",
                instruction_digest, scope,
            )
            if not self._record(requested) or not self._record(refused):
                return CaptureAdviceUnavailable()
            return CaptureAdviceRefused(
                AdviceRefusalCode.UNSAFE_AUTHORITY_REQUEST,
                "Use a governed Human review or approval workflow.",
            )
        try:
            context = self._source.read_authorized(actor, request.capture_id)
        except AICaptureSourceProtected:
            return CaptureAdviceProtectedNotFound()
        except AICaptureDependencyUnavailable:
            return CaptureAdviceUnavailable()
        if (
            context.organization_id != actor.organization_id
            or context.organization_id != scope.organization_id
            or context.project_id != scope.project_id
            or context.workspace_id != scope.workspace_id
        ):
            return CaptureAdviceProtectedNotFound()
        context_digest = _digest(json.dumps({
            "capture_id": str(context.capture_id), "version": context.version,
            "updated_at": context.updated_at.isoformat(),
        }, sort_keys=True, separators=(",", ":")))
        requested = self._audit_record(
            request_id, actor, "AI_CAPTURE_ADVICE_REQUESTED", "requested",
            instruction_digest, scope, context_digest=context_digest,
        )
        if not self._record(requested):
            return CaptureAdviceUnavailable()
        provider_request = ProviderCaptureAdviceRequest(
            1, request_id, request.output_kind, instruction, context, _SAFETY
        )
        try:
            provider_result = self._provider.propose(provider_request)
        except Exception:
            self._record(self._audit_record(
                request_id, actor, "AI_CAPTURE_ADVICE_FAILED", "unavailable",
                instruction_digest, scope, context_digest=context_digest,
            ))
            return CaptureAdviceUnavailable()
        if provider_result.status is ProviderAdviceStatus.REFUSED:
            terminal = self._audit_record(
                request_id, actor, "AI_CAPTURE_ADVICE_REFUSED", "refused",
                instruction_digest, scope, context_digest=context_digest,
                provider_id=provider_result.provider_id, model_id=provider_result.model_id,
            )
            if not self._record(terminal):
                return CaptureAdviceUnavailable()
            return CaptureAdviceRefused(
                provider_result.refusal_code or AdviceRefusalCode.INSUFFICIENT_CONTEXT,
                provider_result.recommended_next_step,
            )
        if provider_result.suggested_text is None:
            return CaptureAdviceUnavailable()
        try:
            generated_at = self._clock.now()
        except Exception:
            self._record(self._audit_record(
                request_id, actor, "AI_CAPTURE_ADVICE_FAILED", "unavailable",
                instruction_digest, scope, context_digest=context_digest,
            ))
            return CaptureAdviceUnavailable()
        proposal = CaptureAdviceProposal(
            True, provider_result.suggested_text, provider_result.observations,
            provider_result.assumptions, provider_result.missing_information,
            provider_result.confidence, provider_result.confidence_rationale,
            provider_result.limitations, provider_result.recommended_next_step,
            CaptureAttribution(
                context.capture_id, context.version, context.project_id,
                context.workspace_id, context.source_kind, context.updated_at,
            ),
            ProviderAttribution(
                provider_result.provider_id, provider_result.model_id,
                provider_result.model_version,
            ), generated_at,
        )
        output_digest = _digest(repr(proposal))
        if not self._record(self._audit_record(
            request_id, actor, "AI_CAPTURE_ADVICE_COMPLETED", "success",
            instruction_digest, scope, context_digest=context_digest,
            output_digest=output_digest, provider_id=provider_result.provider_id,
            model_id=provider_result.model_id,
        )):
            return CaptureAdviceUnavailable()
        return CaptureAdviceSuccess(proposal)
