"""Exact, source-qualified legacy identity translation; never fuzzy matching."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LegacySourceContract(str, Enum):
    WORKSPACE = "workspace"
    EKG = "ekg"
    OBJECT_RELATIONSHIP = "object_relationship"
    GUIDANCE = "guidance"
    OBJECT_FAMILY = "object_family"


class LegacyDisposition(str, Enum):
    CANONICAL_DISCIPLINE = "canonical_discipline"
    TAXONOMY_ONLY = "taxonomy_only"
    ADVISORY_CATEGORY_ONLY = "advisory_category_only"
    CORE_RESERVED = "core_reserved"
    UNRESOLVED = "legacy_unresolved"


@dataclass(frozen=True, slots=True)
class CanonicalLegacyIdentity:
    source_contract: LegacySourceContract
    raw_value: str
    canonical_discipline_id: str | None
    disposition: LegacyDisposition
    eligible_package_key: str | None


@dataclass(frozen=True, slots=True)
class UnresolvedLegacyIdentity:
    source_contract: LegacySourceContract
    raw_value: str
    disposition: LegacyDisposition = LegacyDisposition.UNRESOLVED


_WORKSPACE = {
    "electrical": ("electrical", "electrical"),
    "instrumentation": ("instrumentation", "instrumentation"),
    "control": ("control_automation", "control_automation"),
    "mechanical": ("mechanical", None),
    "civil": ("civil", None),
    "process": ("process", None),
}


def translate_legacy_identity(
    source_contract: LegacySourceContract | str,
    raw_value: str,
) -> CanonicalLegacyIdentity | UnresolvedLegacyIdentity:
    """Translate only accepted exact source/value pairs, preserving raw text."""

    try:
        source = LegacySourceContract(source_contract)
    except ValueError:
        return UnresolvedLegacyIdentity(LegacySourceContract.WORKSPACE, raw_value)
    if type(raw_value) is not str:
        return UnresolvedLegacyIdentity(source, raw_value if isinstance(raw_value, str) else "")
    if source is LegacySourceContract.WORKSPACE and raw_value in _WORKSPACE:
        discipline_id, package_key = _WORKSPACE[raw_value]
        return CanonicalLegacyIdentity(source, raw_value, discipline_id, LegacyDisposition.CANONICAL_DISCIPLINE, package_key)
    if source is LegacySourceContract.EKG and raw_value == "industrial_automation":
        return CanonicalLegacyIdentity(source, raw_value, "control_automation", LegacyDisposition.CANONICAL_DISCIPLINE, None)
    if source is LegacySourceContract.EKG and raw_value == "shared_engineering":
        return CanonicalLegacyIdentity(source, raw_value, "shared_engineering", LegacyDisposition.CORE_RESERVED, None)
    if source is LegacySourceContract.OBJECT_RELATIONSHIP and raw_value == "automation":
        return CanonicalLegacyIdentity(source, raw_value, None, LegacyDisposition.TAXONOMY_ONLY, None)
    if source is LegacySourceContract.GUIDANCE and raw_value == "automation_and_control":
        return CanonicalLegacyIdentity(source, raw_value, None, LegacyDisposition.ADVISORY_CATEGORY_ONLY, None)
    if source is LegacySourceContract.OBJECT_FAMILY and raw_value == "shared":
        return CanonicalLegacyIdentity(source, raw_value, None, LegacyDisposition.TAXONOMY_ONLY, None)
    return UnresolvedLegacyIdentity(source, raw_value)
