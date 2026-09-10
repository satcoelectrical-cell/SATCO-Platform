from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from collections.abc import Mapping
from typing import Any
from uuid import UUID

from .contracts import FindingIdentityInputV1, QuantityV1, RangeV1, SourceIdentityV1

_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_TOKEN = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


def canonical_decimal(value: Decimal | str | int) -> str:
    if isinstance(value, bool): raise ValueError("boolean is not decimal")
    value = Decimal(str(value))
    if not value.is_finite(): raise ValueError("non-finite decimal")
    with localcontext() as ctx:
        ctx.prec = 28; ctx.rounding = ROUND_HALF_EVEN
        value = +value
    if -value.as_tuple().exponent > 9: raise ValueError("decimal scale exceeds 9")
    text = format(value.normalize(), "f")
    if text in {"-0", ""}: text = "0"
    digits = len(text.replace("-", "").replace(".", "").lstrip("0")) or 1
    if digits > 18: raise ValueError("decimal precision exceeds 18")
    return text


def canonical_time(value: datetime) -> str:
    if value.tzinfo is None: raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _normal(value: Any) -> Any:
    if isinstance(value, float): raise ValueError("binary float is forbidden")
    if isinstance(value, UUID):
        text = str(value)
        if text != text.lower(): raise ValueError("UUID must be canonical lowercase")
        return text
    if isinstance(value, Decimal): return canonical_decimal(value)
    if isinstance(value, datetime): return canonical_time(value)
    if isinstance(value, date): return value.isoformat()
    if isinstance(value, QuantityV1):
        return {"dimension": value.dimension, "magnitude": canonical_decimal(value.magnitude), "source_unit": value.source_unit, "canonical_magnitude": canonical_decimal(value.canonical_magnitude)}
    if isinstance(value, RangeV1): return {"lower": _normal(value.lower), "upper": _normal(value.upper), "lower_inclusive": value.lower_inclusive, "upper_inclusive": value.upper_inclusive}
    if isinstance(value, SourceIdentityV1): return {"owner_kind": value.owner_kind, "owner_id": value.owner_id, "revision_kind": value.revision_kind, "revision": value.revision, "projection_digest": value.projection_digest}
    if is_dataclass(value): return _normal(asdict(value))
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, (list, tuple)):
        return [_normal(item) for item in value]
    if isinstance(value, Mapping):
        normalized = {}
        for key, item in value.items():
            if not isinstance(key, str): raise ValueError("canonical object keys must be strings")
            canonical_key = unicodedata.normalize("NFC", key)
            if canonical_key in normalized: raise ValueError("duplicate canonical object key")
            normalized[canonical_key] = _normal(item)
        return normalized
    if value is None or isinstance(value, (bool, int)): return value
    raise ValueError("unsupported canonical value")


def canonical_json(value: Any) -> bytes:
    return json.dumps(_normal(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: Any, prefix: str | None = None) -> str:
    raw = canonical_json(value)
    if prefix is not None: raw = prefix.encode("ascii") + b"\0" + raw
    return hashlib.sha256(raw).hexdigest()


def normalize_token(value: str) -> str:
    if not 1 <= len(value) <= 128 or not _TOKEN.fullmatch(value):
        raise ValueError("invalid machine token")
    return value


_UNITS = {
    "electric_potential": {"mV": (Decimal("0.001"), Decimal(0)), "V": (Decimal(1), Decimal(0)), "kV": (Decimal(1000), Decimal(0))},
    "electric_current": {"mA": (Decimal("0.001"), Decimal(0)), "A": (Decimal(1), Decimal(0))},
    "frequency": {"Hz": (Decimal(1), Decimal(0))}, "power": {"W": (Decimal(1), Decimal(0)), "kW": (Decimal(1000), Decimal(0)), "MW": (Decimal(1000000), Decimal(0))},
    "pressure": {"Pa": (Decimal(1), Decimal(0)), "kPa": (Decimal(1000), Decimal(0)), "MPa": (Decimal(1000000), Decimal(0)), "bar": (Decimal(100000), Decimal(0))},
    "temperature": {"K": (Decimal(1), Decimal(0)), "degC": (Decimal(1), Decimal("273.15"))},
    "time": {"ms": (Decimal("0.001"), Decimal(0)), "s": (Decimal(1), Decimal(0))}, "ratio": {"one": (Decimal(1), Decimal(0)), "percent": (Decimal("0.01"), Decimal(0))},
}


def normalize_quantity(dimension: str, magnitude: Decimal | str | int, unit: str) -> QuantityV1:
    if dimension not in _UNITS or unit not in _UNITS[dimension]: raise ValueError("unsupported_value")
    factor, offset = _UNITS[dimension][unit]
    raw = Decimal(canonical_decimal(magnitude))
    with localcontext() as ctx:
        ctx.prec = 28; ctx.rounding = ROUND_HALF_EVEN
        result = +(raw * factor + offset)
    return QuantityV1(dimension, raw, unit, Decimal(canonical_decimal(result)))


def canonical_set(values: tuple[Any, ...] | list[Any] | frozenset[Any]) -> tuple[Any, ...]:
    if len(values) > 64: raise ValueError("resource_limit_exceeded")
    indexed = {canonical_json(item): item for item in values}
    if len(indexed) != len(values): raise ValueError("set members must be unique")
    kinds = {type(item) for item in values}
    if len(kinds) > 1: raise ValueError("set members must be homogeneous")
    return tuple(indexed[key] for key in sorted(indexed))


def finding_fingerprint(value: FindingIdentityInputV1) -> str:
    sources = tuple(sorted(value.sources, key=lambda x: (x.owner_kind, x.owner_id.encode(), x.revision_kind, x.revision, x.projection_digest)))
    payload = {
        "assessment_execution_id": value.assessment_execution_id, "assessment_snapshot_id": value.assessment_snapshot_id,
        "category": value.category, "subcode": value.subcode,
        "rule": (value.rule_id, value.rule_version, value.rule_digest),
        "interface": (value.interface_definition_id, value.interface_version, value.interface_digest, value.occurrence_key),
        "affected_selector": value.affected_selector, "sources": sources,
        "attestation_digests": tuple(sorted(value.attestation_digests)), "commitment": value.commitment, "change": value.change,
        "package_configuration": (value.registry_digest, value.combination_id, value.project_configuration_revision, tuple(sorted(value.workspace_binding_revisions))),
        "canonicalization_id": "cross_discipline.canonical_json.v1",
    }
    return digest(payload, "satco:cross-discipline-finding:v1")


def recurrence_key(value: FindingIdentityInputV1) -> str:
    payload = {"category": value.category, "subcode": value.subcode, "rule": (value.rule_id, value.rule_version, value.rule_digest), "interface": (value.interface_definition_id, value.interface_version, value.interface_digest, value.occurrence_key), "affected_selector": value.affected_selector, "canonicalization_id": "cross_discipline.canonical_json.v1"}
    return digest(payload, "satco:cross-discipline-recurrence:v1")
