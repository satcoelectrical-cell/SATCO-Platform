"""Provider-neutral bounded HTTPS adapter for PATCH-035."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from enum import Enum
import json
import re
from urllib.request import Request, urlopen
from uuid import UUID

from app.exceptions.ai_capture_assistant import AICaptureProviderUnavailable, AICaptureInvalidProviderResponse
from app.ports.ai_capture_assistant import ProviderCaptureAdviceRequest, ProviderCaptureAdviceResponseV1
from app.schemas.ai_capture_assistant import ProviderCaptureAdviceResponseSchema


_AUTHORITY_CLAIM = re.compile(r"\b(approved|certified|final|automatically accepted)\b", re.IGNORECASE)


def _json_value(value):
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, Enum):
        return value.value
    raise TypeError(f"unsupported canonical value: {type(value)!r}")


def canonical_provider_json(request: ProviderCaptureAdviceRequest) -> bytes:
    payload = json.dumps(
        asdict(request), default=_json_value, sort_keys=True,
        separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")
    if len(payload) > 16_384:
        raise AICaptureProviderUnavailable()
    return payload


class ProviderNeutralCaptureAssistant:
    def __init__(self, *, endpoint: str, api_key: str, timeout_seconds: float = 30.0, opener=urlopen) -> None:
        if not endpoint.startswith("https://") or not api_key or not (0 < timeout_seconds <= 30):
            raise ValueError("provider configuration is invalid")
        self._endpoint = endpoint
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._opener = opener

    def propose(self, request: ProviderCaptureAdviceRequest) -> ProviderCaptureAdviceResponseV1:
        body = canonical_provider_json(request)
        http_request = Request(
            self._endpoint, data=body, method="POST",
            headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"},
        )
        try:
            with self._opener(http_request, timeout=self._timeout) as response:
                raw = response.read(32_769)
        except Exception as exc:
            raise AICaptureProviderUnavailable() from exc
        if len(raw) > 32_768:
            raise AICaptureProviderUnavailable()
        try:
            parsed = ProviderCaptureAdviceResponseSchema.model_validate_json(raw)
        except Exception as exc:
            raise AICaptureInvalidProviderResponse() from exc
        provider_text = (
            *((parsed.suggested_text,) if parsed.suggested_text else ()),
            *parsed.observations,
            *parsed.assumptions,
            *parsed.missing_information,
            parsed.confidence_rationale,
            *parsed.limitations,
            parsed.recommended_next_step,
        )
        if any(_AUTHORITY_CLAIM.search(value) for value in provider_text):
            raise AICaptureInvalidProviderResponse()
        return ProviderCaptureAdviceResponseV1(
            status=parsed.status, suggested_text=parsed.suggested_text,
            observations=parsed.observations, assumptions=parsed.assumptions,
            missing_information=parsed.missing_information, confidence=parsed.confidence,
            confidence_rationale=parsed.confidence_rationale, limitations=parsed.limitations,
            recommended_next_step=parsed.recommended_next_step, refusal_code=parsed.refusal_code,
            provider_id=parsed.provider_id, model_id=parsed.model_id,
            model_version=parsed.model_version,
        )
