"""Batch-2 opaque client handles and sealed provider-token envelopes."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings


class OpaqueAuthorizedHandleUnavailable(RuntimeError):
    """Raised rather than issuing a material handle before Batch 2 authorization."""


class OpaqueAuthorizedHandleInvalid(OpaqueAuthorizedHandleUnavailable):
    """One safe failure for forged, stale, expired, or wrongly-bound handles."""


def _key(label: str) -> bytes:
    return hashlib.sha256((settings.resolved_secret_key() + ":standards:" + label).encode()).digest()


def issue_handle(*, actor_id: int, organization_id: str, project_id: int, operation: str,
                 resource_id: str, edition_id: str, rights_binding_id: str,
                 rights_version: int, rights_digest: str, purpose: str, provider_id: str,
                 source_location: str, integrity_digest: str,
                 expires_at: datetime | None = None) -> str:
    """Issue a signed, compact, non-content-bearing Batch-2 handle (max 15 min)."""
    now = datetime.now(timezone.utc)
    expires_at = expires_at or now + timedelta(minutes=15)
    if (expires_at > now + timedelta(minutes=15) or not operation or rights_version < 1
            or not purpose or len(purpose) > 80 or not provider_id or len(provider_id) > 80
            or not source_location or len(source_location) > 500
            or len(integrity_digest) != 64):
        raise ValueError("invalid handle context")
    payload = {"v": 1, "a": actor_id, "o": organization_id, "p": project_id,
               "op": operation, "r": resource_id, "e": edition_id,
               "rb": rights_binding_id, "rv": rights_version, "rd": rights_digest,
               "pu": purpose, "pr": provider_id, "sl": source_location,
               "si": integrity_digest,
               "exp": int(expires_at.timestamp())}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    mac = hmac.new(_key("opaque-handle:v1"), raw, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(raw + mac).decode().rstrip("=")


def verify_handle(value: str, *, actor_id: int, organization_id: str, project_id: int,
                  operation: str, resource_id: str, edition_id: str,
                  rights_binding_id: str, rights_version: int, rights_digest: str,
                  purpose: str, provider_id: str, source_location: str,
                  integrity_digest: str) -> dict[str, Any]:
    try:
        if len(value) > 2048:
            raise ValueError
        raw = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
        body, supplied = raw[:-32], raw[-32:]
        expected = hmac.new(_key("opaque-handle:v1"), body, hashlib.sha256).digest()
        payload = json.loads(body)
        required = {"v": 1, "a": actor_id, "o": organization_id, "p": project_id,
                    "op": operation, "r": resource_id, "e": edition_id,
                    "rb": rights_binding_id, "rv": rights_version, "rd": rights_digest,
                    "pu": purpose, "pr": provider_id, "sl": source_location,
                    "si": integrity_digest}
        if (not hmac.compare_digest(supplied, expected) or set(payload) != set(required) | {"exp"}
                or any(payload.get(k) != v for k, v in required.items())
                or type(payload["exp"]) is not int or payload["exp"] <= int(datetime.now(timezone.utc).timestamp())):
            raise ValueError
        return payload
    except Exception as error:
        raise OpaqueAuthorizedHandleInvalid("invalid authorized handle") from error


def seal_provider_token(token: str, *, provider_id: str, organization_id: str, project_id: int) -> bytes:
    if not token or len(token.encode()) > 4096:
        raise ValueError("invalid provider token")
    nonce = os.urandom(12)
    aad = f"provider-token:v1:{provider_id}:{organization_id}:{project_id}".encode()
    return nonce + AESGCM(_key("provider-token:v1")).encrypt(nonce, token.encode(), aad)


def open_provider_token(sealed: bytes, *, provider_id: str, organization_id: str, project_id: int) -> str:
    try:
        if len(sealed) < 29 or len(sealed) > 8192:
            raise ValueError
        aad = f"provider-token:v1:{provider_id}:{organization_id}:{project_id}".encode()
        return AESGCM(_key("provider-token:v1")).decrypt(sealed[:12], sealed[12:], aad).decode("utf-8")
    except Exception as error:
        raise OpaqueAuthorizedHandleInvalid("invalid provider token") from error
