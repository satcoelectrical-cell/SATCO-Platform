"""PATCH-055 retention-governance schema primitives."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.enums.retention import (
    DispositionDecision,
    DispositionEligibility,
    ExportStatus,
    HoldStatus,
    RecoveryStatus,
    RetentionMode,
    RetentionPolicySource,
    RetentionSubjectKind,
)


class RetentionSubjectV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject_kind: RetentionSubjectKind
    subject_id: UUID
    organization_id: UUID
    project_id: int = Field(ge=1)
    workspace_id: int | None = Field(default=None, ge=1)


class ApplyRetentionPolicyRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    retention_mode: RetentionMode
    retention_until: datetime | None = None
    policy_source: RetentionPolicySource
    basis_code: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[a-z0-9_.-]+$",
    )
    rationale: str | None = Field(default=None, max_length=2000)
    expected_version: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_retention_shape(self):
        if self.retention_mode is RetentionMode.RETAIN_INDEFINITELY:
            if self.retention_until is not None:
                raise ValueError(
                    "retain_indefinitely requires null retention_until"
                )
        else:
            if self.retention_until is None:
                raise ValueError("retain_until requires retention_until")
            if (
                self.retention_until.tzinfo is None
                or self.retention_until.utcoffset() is None
            ):
                raise ValueError("retention_until must be timezone-aware")
        return self


class PlaceRetentionHoldRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason_code: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[a-z0-9_.-]+$",
    )
    rationale: str = Field(min_length=1, max_length=2000)
    authority_reference: str = Field(min_length=1, max_length=512)
    expected_version: int = Field(ge=1)


class ReleaseRetentionHoldRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    release_rationale: str = Field(min_length=1, max_length=2000)
    expected_version: int = Field(ge=1)


class RecordDispositionDecisionRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["retain", "approve_disposition"]
    reason: str = Field(min_length=1, max_length=2000)
    retention_record_id: UUID
    subject_version_snapshot: int = Field(ge=1)
    expected_version: int = Field(ge=1)


class RetentionStateResponseV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    retention_record_id: UUID | None
    subject: RetentionSubjectV1
    retention_mode: RetentionMode | None
    retention_until: datetime | None
    policy_basis_code: str | None
    basis_rationale: str | None
    policy_source: RetentionPolicySource | None
    hold_status: HoldStatus | None
    active_hold_id: UUID | None
    active_hold_version: int | None = Field(default=None, ge=1)
    disposition_eligibility: DispositionEligibility
    disposition_decision: DispositionDecision
    version: int | None
    predecessor_record_id: UUID | None
    record_digest: str | None


class RetentionMutationResponseV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: Literal["success"]
    state: RetentionStateResponseV1


class RetentionExportSubjectV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject: RetentionSubjectV1
    subject_version: int | None = Field(default=None, ge=1)


class CreateRetentionExportRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subjects: list[RetentionExportSubjectV1] = Field(min_length=1, max_length=32)
    purpose: str = Field(min_length=1, max_length=1000)
    format: Literal["zip_v1"] = "zip_v1"


class RetentionExportResponseV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    export_id: UUID
    status: ExportStatus
    requested_at: datetime
    completed_at: datetime | None = None
    aggregate_digest: str | None = None
    byte_count: int | None = Field(default=None, ge=0)


class CreateRetentionRecoveryRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject: RetentionSubjectV1


class RetentionRecoveryResponseV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recovery_id: UUID
    status: RecoveryStatus
    requested_at: datetime
    completed_at: datetime | None = None
    expected_digest: str | None = None
    verified_digest: str | None = None


class ProtectedOutcomeV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: Literal[
        "success",
        "invalid_request",
        "protected_not_found",
        "conflict",
        "not_permitted",
        "unavailable",
        "indeterminate",
    ]
    detail: str | None = None


class EvidenceWorkbenchRelianceV1(BaseModel):
    model_config = ConfigDict(extra="forbid")
    report_id: UUID
    evidence_version: int = Field(ge=1)
    report_version: int = Field(ge=1)
    accepted_at: datetime

class EvidenceWorkbenchEvidenceV1(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evidence_id: UUID
    lifecycle: str
    source_standing: str
    supported_fact: str
    version: int = Field(ge=1)
    replacement_evidence_id: UUID | None = None
    predecessor_evidence_ids: tuple[UUID, ...] = ()
    reliance: tuple[EvidenceWorkbenchRelianceV1, ...] = ()
    retention_state: RetentionStateResponseV1 | None = None

class EvidenceWorkbenchFileV1(BaseModel):
    model_config = ConfigDict(extra="forbid")
    asset_id: UUID
    safe_filename: str
    lifecycle: str
    version: int = Field(ge=1)

class EvidenceWorkbenchResponseV1(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: int = Field(ge=1)
    workspace_id: int | None = Field(default=None, ge=1)
    evidence: tuple[EvidenceWorkbenchEvidenceV1, ...] = ()
    supporting_files: tuple[EvidenceWorkbenchFileV1, ...] = ()
    visible_count: int = Field(ge=0)
