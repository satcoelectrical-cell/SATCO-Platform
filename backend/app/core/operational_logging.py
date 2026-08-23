"""Bounded, redacted JSON operational logging for PATCH-042."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone


_ALLOWED = frozenset({"event_code", "correlation_id", "component", "release_id", "outcome", "duration_ms", "actor_id"})
_FORBIDDEN = ("secret", "token", "password", "authorization", "cookie", "content", "object", "body", "prompt", "response")


def safe_operational_event(event_code: str, **fields: object) -> str:
    payload: dict[str, object] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_code": event_code[:64],
    }
    for key, value in fields.items():
        if key not in _ALLOWED or any(word in key.lower() for word in _FORBIDDEN):
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            payload[key] = str(value)[:128] if isinstance(value, str) else value
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    logging.getLogger("satco.operations").info(encoded)
    return encoded
