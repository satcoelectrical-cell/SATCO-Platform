"""Canonical, non-AI standard identity and command digest functions."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import date, datetime
from enum import Enum
from uuid import UUID

NORMALIZATION_VERSION = "satco_standard_key_nfkc_casefold_v1"
_DASHES = str.maketrans({char: "-" for char in "‐‑‒–—―−﹘﹣－"})
_WHITESPACE = re.compile(r"\s+", flags=re.UNICODE)


def normalize_standard_key(value: str) -> str:
    """NFKC, dash-map, Unicode-space normalization and casefold, preserving punctuation."""
    if not isinstance(value, str):
        raise ValueError("standard key must be text")
    normalized = unicodedata.normalize("NFKC", value).translate(_DASHES)
    normalized = _WHITESPACE.sub(" ", normalized).strip().casefold()
    if not normalized or "\x00" in normalized:
        raise ValueError("standard key is empty or unsafe")
    return normalized


def _jsonable(value: object) -> object:
    if isinstance(value, Enum): return value.value
    if isinstance(value, UUID): return str(value)
    if isinstance(value, (datetime, date)): return value.isoformat()
    if isinstance(value, dict): return {str(k): _jsonable(v) for k, v in sorted(value.items())}
    if isinstance(value, (tuple, list)): return [_jsonable(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)): return value
    raise ValueError("unsupported canonical value")


def canonical_json(value: object) -> str:
    return json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
