"""Strict SATCO commercial-entitlement v1 parsing and canonical payload bytes."""
from __future__ import annotations
import json
import re
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SCHEMA = "satco.commercial-entitlement/v1"
PACKAGE_KEYS = frozenset({"electrical", "instrumentation", "control_automation"})
MAX_GRACE = timedelta(days=30)
_CANONICAL_UTC_SECOND = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

class EntitlementPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: int
    entitlement_id: UUID
    revision: int = Field(ge=1, le=9007199254740991)
    organization_id: UUID
    deployment_id: str = Field(min_length=1, max_length=200)
    issuer: str = Field(min_length=1, max_length=200)
    issued_at: datetime
    not_before: datetime
    valid_until: datetime
    grace_until: datetime
    package_keys: tuple[str, ...]
    seat_capacity: int = Field(ge=1, le=9007199254740991)
    support_until: datetime | None = None
    baseline_release_sequence: int = Field(ge=1, le=9007199254740991)
    max_release_sequence: int = Field(ge=1, le=9007199254740991)

    @field_validator("schema_version")
    @classmethod
    def schema_is_v1(cls, value: int) -> int:
        if value != 1: raise ValueError("schema_version must be 1")
        return value

    @field_validator("issued_at", "not_before", "valid_until", "grace_until", "support_until")
    @classmethod
    def utc_datetime(cls, value: datetime | None) -> datetime | None:
        if value is None: return None
        if value.tzinfo is None or value.utcoffset() is None: raise ValueError("timezone-aware UTC required")
        return value.astimezone(timezone.utc)

    @field_validator("package_keys")
    @classmethod
    def closed_packages(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value or len(set(value)) != len(value) or any(x not in PACKAGE_KEYS for x in value):
            raise ValueError("package_keys must be a unique non-empty supported set")
        if tuple(sorted(value)) != value:
            raise ValueError("package_keys must use canonical sorted order")
        return value

    @model_validator(mode="after")
    def bounds(self) -> "EntitlementPayload":
        if not (self.issued_at <= self.not_before <= self.valid_until <= self.grace_until):
            raise ValueError("invalid entitlement temporal ordering")
        if self.grace_until - self.valid_until > MAX_GRACE: raise ValueError("grace exceeds 30 days")
        if self.max_release_sequence < self.baseline_release_sequence: raise ValueError("invalid release range")
        return self

class EntitlementEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)
    schema_id: str = Field(alias="schema")
    key_id: str = Field(min_length=1, max_length=120)
    payload: EntitlementPayload
    signature: str = Field(min_length=1, max_length=200)

    @field_validator("schema_id")
    @classmethod
    def schema_exact(cls, value: str) -> str:
        if value != SCHEMA: raise ValueError("unsupported entitlement schema")
        return value

def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out: raise ValueError(f"duplicate JSON member: {key}")
        out[key] = value
    return out

def parse_envelope(raw: bytes) -> EntitlementEnvelope:
    text = raw.decode("utf-8", errors="strict")
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-I-JSON number: {value}")
    value = json.loads(text, object_pairs_hook=_no_duplicates, parse_constant=reject_constant)
    if not isinstance(value, dict): raise ValueError("entitlement envelope must be an object")
    payload = value.get("payload")
    if not isinstance(payload, dict): raise ValueError("entitlement payload must be an object")
    for name in ("issued_at", "not_before", "valid_until", "grace_until"):
        if not isinstance(payload.get(name), str) or not _CANONICAL_UTC_SECOND.fullmatch(payload[name]):
            raise ValueError(f"{name} must use canonical UTC-second format")
    support = payload.get("support_until")
    if support is not None and (not isinstance(support, str) or not _CANONICAL_UTC_SECOND.fullmatch(support)):
        raise ValueError("support_until must use canonical UTC-second format")
    for name in ("entitlement_id", "organization_id"):
        raw_uuid = payload.get(name)
        if not isinstance(raw_uuid, str) or str(UUID(raw_uuid)) != raw_uuid:
            raise ValueError(f"{name} must use canonical UUID form")
    return EntitlementEnvelope.model_validate(value)

def _wire_payload(payload: EntitlementPayload) -> dict[str, Any]:
    def ts(v: datetime | None) -> str | None:
        if v is None: return None
        return v.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return {
        "baseline_release_sequence": payload.baseline_release_sequence,
        "deployment_id": payload.deployment_id,
        "entitlement_id": str(payload.entitlement_id),
        "grace_until": ts(payload.grace_until),
        "issued_at": ts(payload.issued_at),
        "issuer": payload.issuer,
        "max_release_sequence": payload.max_release_sequence,
        "not_before": ts(payload.not_before),
        "organization_id": str(payload.organization_id),
        "package_keys": list(payload.package_keys),
        "revision": payload.revision,
        "schema_version": payload.schema_version,
        "seat_capacity": payload.seat_capacity,
        "support_until": ts(payload.support_until),
        "valid_until": ts(payload.valid_until),
    }

def canonical_payload_bytes(payload: EntitlementPayload) -> bytes:
    return json.dumps(_wire_payload(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")

def canonical_payload_digest(payload: EntitlementPayload) -> str:
    return sha256(canonical_payload_bytes(payload)).hexdigest()
