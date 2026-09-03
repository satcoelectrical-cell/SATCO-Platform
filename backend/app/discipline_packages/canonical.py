"""NFC, deterministic canonical JSON and semantically distinct SHA-256 digests."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
import hashlib
import json
import math
import unicodedata
from typing import Any

from pydantic import BaseModel

from app.discipline_packages.identity import (
    CombinationDigest,
    DescriptorDigest,
    ProfileDigest,
    RegistryDigest,
    SelectedDescriptorSetDigest,
)
from app.exceptions.discipline_package import DisciplinePackageError, DisciplinePackageReasonCode


def _normalise(value: Any) -> Any:
    if value is None or isinstance(value, float):
        raise DisciplinePackageError(DisciplinePackageReasonCode.INVALID_DESCRIPTOR)
    if isinstance(value, str):
        if unicodedata.normalize("NFC", value) != value:
            raise DisciplinePackageError(DisciplinePackageReasonCode.INVALID_DESCRIPTOR)
        return value
    if isinstance(value, (bool, int)):
        return value
    if isinstance(value, Enum):
        return _normalise(value.value)
    # Digest wrappers are distinct at the contract boundary but their canonical
    # representation is precisely the accepted stable hexadecimal value.
    if isinstance(value, (RegistryDigest, DescriptorDigest, SelectedDescriptorSetDigest, ProfileDigest, CombinationDigest)):
        return str(value)
    if isinstance(value, BaseModel):
        return _normalise(value.model_dump(mode="python", exclude_none=True))
    if is_dataclass(value):
        return _normalise(asdict(value))
    if isinstance(value, dict):
        normalised: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str or unicodedata.normalize("NFC", key) != key or key in normalised:
                raise DisciplinePackageError(DisciplinePackageReasonCode.INVALID_DESCRIPTOR)
            normalised[key] = _normalise(item)
        return normalised
    if isinstance(value, (list, tuple)):
        return [_normalise(item) for item in value]
    if hasattr(value, "value") and type(getattr(value, "value")) is str:
        return _normalise(value.value)
    raise DisciplinePackageError(DisciplinePackageReasonCode.INVALID_DESCRIPTOR)


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize strictly valid data with stable Unicode-codepoint key order."""

    payload = _normalise(value)
    result = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return result


def _digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def descriptor_digest(value: Any) -> DescriptorDigest:
    return DescriptorDigest(_digest(value))


def selected_descriptor_set_digest(value: Any) -> SelectedDescriptorSetDigest:
    return SelectedDescriptorSetDigest(_digest(_sorted_members(value)))


def combination_digest(value: Any) -> CombinationDigest:
    return CombinationDigest(_digest(_sorted_members(value)))


def profile_digest(value: Any) -> ProfileDigest:
    payload = _normalise(value)
    if not isinstance(payload, dict) or "combinations" not in payload:
        raise DisciplinePackageError(DisciplinePackageReasonCode.INVALID_DESCRIPTOR)
    combinations = []
    for combination in payload["combinations"]:
        members = _sorted_members(combination["members"])
        combinations.append({"combination_digest": str(combination_digest(members)), "members": members})
    payload["combinations"] = sorted(combinations, key=lambda item: item["combination_digest"])
    return ProfileDigest(_digest(payload))


def registry_digest(value: Any) -> RegistryDigest:
    return RegistryDigest(_digest(value))


def _sorted_members(value: Any) -> list[dict[str, Any]]:
    members = _normalise(value)
    if not isinstance(members, list):
        raise DisciplinePackageError(DisciplinePackageReasonCode.INVALID_DESCRIPTOR)
    try:
        sorted_members = sorted(
            members,
            key=lambda item: (item["package_key"], item["package_version"], item["descriptor_digest"]),
        )
    except (KeyError, TypeError):
        raise DisciplinePackageError(DisciplinePackageReasonCode.INVALID_DESCRIPTOR) from None
    identities = [(item["package_key"], item["package_version"]) for item in sorted_members]
    if len(identities) != len(set(identities)):
        raise DisciplinePackageError(DisciplinePackageReasonCode.INVALID_DESCRIPTOR)
    return sorted_members
