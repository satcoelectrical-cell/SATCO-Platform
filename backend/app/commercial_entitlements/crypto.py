"""Ed25519 verification and deployment-governed trust store for PATCH-059."""
from __future__ import annotations
import base64, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.commercial_entitlements.canonical import EntitlementEnvelope, canonical_payload_bytes

TRUST_SCHEMA = "satco.commercial-entitlement-trust/v1"

def _b64url(value: str) -> bytes:
    if not value or "=" in value: raise ValueError("unpadded base64url required")
    try: return base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
    except Exception as exc: raise ValueError("invalid base64url") from exc

class TrustKey(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    key_id: str = Field(min_length=1, max_length=120)
    algorithm: str
    public_key_base64url: str
    not_before: datetime
    revoked_at: datetime | None = None

    @field_validator("algorithm")
    @classmethod
    def alg(cls, value: str) -> str:
        if value != "Ed25519": raise ValueError("unsupported algorithm")
        return value

    @field_validator("not_before", "revoked_at")
    @classmethod
    def aware(cls, value: datetime | None) -> datetime | None:
        if value is None: return None
        if value.tzinfo is None or value.utcoffset() is None: raise ValueError("timezone-aware timestamp required")
        return value.astimezone(timezone.utc)

    @field_validator("public_key_base64url")
    @classmethod
    def public_key_length(cls, value: str) -> str:
        if len(_b64url(value)) != 32: raise ValueError("Ed25519 public key must be 32 bytes")
        return value

class TrustStore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)
    schema_id: str = Field(alias="schema")
    keys: tuple[TrustKey, ...]

    @field_validator("schema_id")
    @classmethod
    def schema_exact(cls, value: str) -> str:
        if value != TRUST_SCHEMA: raise ValueError("unsupported trust-store schema")
        return value

    @field_validator("keys")
    @classmethod
    def unique_keys(cls, value: tuple[TrustKey, ...]) -> tuple[TrustKey, ...]:
        if not value or len({k.key_id for k in value}) != len(value): raise ValueError("trust keys must be non-empty and unique")
        return value

    def key(self, key_id: str) -> TrustKey:
        for key in self.keys:
            if key.key_id == key_id: return key
        raise ValueError("untrusted key")

def load_trust_store(path: str | Path) -> TrustStore:
    text = Path(path).read_bytes().decode("utf-8", errors="strict")
    def no_dupes(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in pairs:
            if key in out: raise ValueError(f"duplicate JSON member: {key}")
            out[key] = value
        return out
    return TrustStore.model_validate(json.loads(text, object_pairs_hook=no_dupes))

def verify_envelope(envelope: EntitlementEnvelope, store: TrustStore, *, now: datetime) -> None:
    if now.tzinfo is None or now.utcoffset() is None: raise ValueError("authoritative UTC time required")
    now = now.astimezone(timezone.utc)
    key = store.key(envelope.key_id)
    if now < key.not_before: raise ValueError("key not yet valid")
    if key.revoked_at is not None and key.revoked_at <= now: raise ValueError("key revoked")
    signature = _b64url(envelope.signature)
    if len(signature) != 64: raise ValueError("Ed25519 signature must be 64 bytes")
    try:
        Ed25519PublicKey.from_public_bytes(_b64url(key.public_key_base64url)).verify(signature, canonical_payload_bytes(envelope.payload))
    except InvalidSignature as exc:
        raise ValueError("invalid signature") from exc
