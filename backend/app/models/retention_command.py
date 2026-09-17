"""PATCH-055 retention domain primitives and deterministic digest helpers."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID

from app.enums.retention import (
    DispositionDecision,
    DispositionEligibility,
    HoldStatus,
    RetentionMode,
    RetentionPolicySource,
    RetentionSubjectKind,
)


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime must be timezone-aware")
        return value.astimezone(timezone.utc).isoformat()
    if is_dataclass(value):
        return _canonical_value(asdict(value))
    if isinstance(value, dict):
        return {str(k): _canonical_value(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_canonical_value(v) for v in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(
        _canonical_value(value),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def sha256_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class RetentionSubject:
    subject_kind: RetentionSubjectKind
    subject_id: UUID
    organization_id: UUID
    project_id: int
    workspace_id: int | None = None

    def __post_init__(self) -> None:
        if self.project_id < 1:
            raise ValueError("project_id must be positive")
        if self.workspace_id is not None and self.workspace_id < 1:
            raise ValueError("workspace_id must be positive")


@dataclass(frozen=True, slots=True)
class RetentionBasis:
    mode: RetentionMode
    policy_source: RetentionPolicySource
    policy_basis_code: str
    basis_rationale: str | None
    retain_until: datetime | None

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z0-9_.-]{1,64}", self.policy_basis_code):
            raise ValueError("policy_basis_code must match [a-z0-9_.-]{1,64}")
        if self.basis_rationale is not None and len(self.basis_rationale) > 2000:
            raise ValueError("basis_rationale exceeds 2000 characters")
        if self.mode is RetentionMode.RETAIN_INDEFINITELY:
            if self.retain_until is not None:
                raise ValueError("retain_indefinitely requires null retain_until")
        else:
            if self.retain_until is None:
                raise ValueError("retain_until mode requires retain_until")
            if self.retain_until.tzinfo is None or self.retain_until.utcoffset() is None:
                raise ValueError("retain_until must be timezone-aware")


@dataclass(frozen=True, slots=True)
class RetentionGovernanceHeadV1:
    retention_record_id: UUID
    subject: RetentionSubject
    retention_mode: RetentionMode
    retention_until: datetime | None
    policy_basis_code: str
    basis_rationale: str | None
    policy_source: RetentionPolicySource
    hold_status: HoldStatus | None
    active_hold_id: UUID | None
    active_hold_version: int | None
    disposition_eligibility: DispositionEligibility
    disposition_decision: DispositionDecision
    version: int
    predecessor_record_id: UUID | None
    created_by_user_id: int
    created_at: datetime
    record_digest: str

    def __post_init__(self) -> None:
        if self.version < 1:
            raise ValueError("version must be positive")
        if self.active_hold_version is not None and self.active_hold_version < 1:
            raise ValueError("active_hold_version must be positive")
        if self.created_by_user_id < 1:
            raise ValueError("created_by_user_id must be positive")
        if not re.fullmatch(r"[0-9a-f]{64}", self.record_digest):
            raise ValueError("record_digest must be lowercase SHA-256 hex")
