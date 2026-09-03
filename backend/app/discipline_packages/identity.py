"""Distinct, immutable PATCH-051 Core identity and provenance value objects."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import ClassVar

from app.exceptions.discipline_package import DisciplinePackageError, DisciplinePackageReasonCode


_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_PROFILE_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_ENTITLEMENT_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_.-]{0,127}$")
_RELEASE_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,63}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_SEMVER = re.compile(
    r"^(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})"
    r"(?:-([0-9A-Za-z-]{1,16}(?:\.[0-9A-Za-z-]{1,16})*))?$"
)


@dataclass(frozen=True, slots=True)
class _StringIdentity:
    value: str

    _pattern: ClassVar[re.Pattern[str]] = _IDENTIFIER

    def __post_init__(self) -> None:
        if type(self.value) is not str or not self._pattern.fullmatch(self.value):
            raise DisciplinePackageError(DisciplinePackageReasonCode.INVALID_IDENTITY)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class DisciplineId(_StringIdentity):
    """Core catalog identity; only six values are Workspace-selectable."""

    _pattern: ClassVar[re.Pattern[str]] = _IDENTIFIER


@dataclass(frozen=True, slots=True)
class PackageKey(_StringIdentity):
    _pattern: ClassVar[re.Pattern[str]] = _IDENTIFIER


@dataclass(frozen=True, slots=True)
class CompatibilityProfileId(_StringIdentity):
    _pattern: ClassVar[re.Pattern[str]] = _PROFILE_IDENTIFIER


@dataclass(frozen=True, slots=True)
class EntitlementKey(_StringIdentity):
    _pattern: ClassVar[re.Pattern[str]] = _ENTITLEMENT_IDENTIFIER


@dataclass(frozen=True, slots=True)
class RegistryReleaseId(_StringIdentity):
    _pattern: ClassVar[re.Pattern[str]] = _RELEASE_IDENTIFIER


@dataclass(frozen=True, slots=True)
class _DigestIdentity:
    value: str

    def __post_init__(self) -> None:
        if type(self.value) is not str or not _DIGEST.fullmatch(self.value):
            raise DisciplinePackageError(DisciplinePackageReasonCode.INVALID_IDENTITY)

    def __str__(self) -> str:
        return self.value


class RegistryDigest(_DigestIdentity):
    pass


class DescriptorDigest(_DigestIdentity):
    pass


class SelectedDescriptorSetDigest(_DigestIdentity):
    pass


class ProfileDigest(_DigestIdentity):
    pass


class CombinationDigest(_DigestIdentity):
    pass


@dataclass(frozen=True, slots=True)
class CoreContractVersion:
    value: int

    def __post_init__(self) -> None:
        if type(self.value) is not int or not 1 <= self.value <= 32767:
            raise DisciplinePackageError(DisciplinePackageReasonCode.INVALID_IDENTITY)

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True, slots=True)
class PackageVersion:
    value: str

    def __post_init__(self) -> None:
        match = _SEMVER.fullmatch(self.value) if type(self.value) is str else None
        if not match:
            raise DisciplinePackageError(DisciplinePackageReasonCode.INVALID_IDENTITY)
        prerelease = match.group(4)
        if prerelease:
            for identifier in prerelease.split("."):
                if identifier.isdigit() and len(identifier) > 1 and identifier.startswith("0"):
                    raise DisciplinePackageError(DisciplinePackageReasonCode.INVALID_IDENTITY)

    @property
    def sort_key(self) -> tuple[int, int, int, int, tuple[tuple[int, str], ...]]:
        match = _SEMVER.fullmatch(self.value)
        assert match is not None
        prerelease = match.group(4)
        parts = () if prerelease is None else tuple(
            (0, f"{int(item):010d}") if item.isdigit() else (1, item)
            for item in prerelease.split(".")
        )
        return (int(match.group(1)), int(match.group(2)), int(match.group(3)), 1 if prerelease is None else 0, parts)

    def __str__(self) -> str:
        return self.value


WORKSPACE_SELECTABLE_DISCIPLINES = frozenset(
    {
        DisciplineId("electrical"),
        DisciplineId("instrumentation"),
        DisciplineId("control_automation"),
        DisciplineId("mechanical"),
        DisciplineId("civil"),
        DisciplineId("process"),
    }
)
CORE_ONLY_DISCIPLINES = frozenset({DisciplineId("shared_engineering")})
CORE_CONTRACT_V1 = CoreContractVersion(1)
