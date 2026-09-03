"""Batch-4 HTTP composition helpers with bounded, scope-bound cursors."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.discipline_package_configuration_service import DisciplinePackageConfigurationService


def get_discipline_package_configuration_service() -> DisciplinePackageConfigurationService:
    return DisciplinePackageConfigurationService(SessionLocal)


def encode_discipline_package_cursor(*, scope: dict[str, object], position: list[str]) -> str:
    payload = {
        "scope": scope,
        "position": position,
        "expires_at": int((datetime.now(timezone.utc) + timedelta(minutes=15)).timestamp()),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(settings.resolved_secret_key().encode("utf-8"), raw, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(raw + signature).decode("ascii").rstrip("=")


def decode_discipline_package_cursor(cursor: str | None, *, scope: dict[str, object]) -> list[str] | None:
    if cursor is None:
        return None
    try:
        encoded = cursor.encode("ascii")
        raw_and_signature = base64.urlsafe_b64decode(encoded + b"=" * (-len(encoded) % 4))
        raw, signature = raw_and_signature[:-32], raw_and_signature[-32:]
        expected = hmac.new(settings.resolved_secret_key().encode("utf-8"), raw, hashlib.sha256).digest()
        payload: Any = json.loads(raw)
        if (
            not hmac.compare_digest(signature, expected)
            or not isinstance(payload, dict)
            or payload.get("scope") != scope
            or not isinstance(payload.get("position"), list)
            or not all(isinstance(item, str) and len(item) <= 128 for item in payload["position"])
            or not isinstance(payload.get("expires_at"), int)
            or payload["expires_at"] < int(datetime.now(timezone.utc).timestamp())
        ):
            raise ValueError
        return payload["position"]
    except (binascii.Error, ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(status_code=422, detail="INVALID_PACKAGE_CONFIGURATION") from None
