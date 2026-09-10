"""Strict transport contracts for the 15 PATCH-053 Batch-1 operations."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.enums.cross_discipline_intelligence import (
    AssessmentPurpose, DispositionAction, FindingCategory, FindingSeverity,
)


class XDIModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=True)


class PageQuery(XDIModel):
    cursor: str | None = Field(default=None, max_length=2048)
    limit: int = Field(default=50, ge=1, le=100)


class ScopeSelection(XDIModel):
    workspace_ids: tuple[int, ...] = Field(min_length=1, max_length=12)
    combination_id: str = Field(min_length=1, max_length=128)
    interface_definition_ids: tuple[str, ...] = Field(default=(), max_length=16)
    endpoint_selectors: tuple[str, ...] = Field(default=(), max_length=128)
    purpose: AssessmentPurpose = AssessmentPurpose.INTERFACE_ASSESSMENT
    project_change_id: int | None = Field(default=None, ge=1)
    project_change_version: int | None = Field(default=None, ge=1)

    @field_validator("workspace_ids")
    @classmethod
    def sorted_unique_workspaces(cls, value):
        if tuple(sorted(set(value))) != value or any(item < 1 for item in value):
            raise ValueError("workspace_ids must be sorted unique positive integers")
        return value

    @field_validator("interface_definition_ids", "endpoint_selectors")
    @classmethod
    def sorted_unique_tokens(cls, value):
        if tuple(sorted(set(value))) != value:
            raise ValueError("values must be sorted and unique")
        return value

    @model_validator(mode="after")
    def change_contract(self):
        present = self.project_change_id is not None or self.project_change_version is not None
        if (self.project_change_id is None) != (self.project_change_version is None):
            raise ValueError("Change identity and version are paired")
        if self.purpose == AssessmentPurpose.EXPLICIT_CHANGE_IMPACT and not present:
            raise ValueError("explicit change purpose requires Change identity")
        if self.purpose != AssessmentPurpose.EXPLICIT_CHANGE_IMPACT and present:
            raise ValueError("Change identity is forbidden for this purpose")
        return self


class AssessmentCreate(XDIModel):
    scope: ScopeSelection
    rationale: str = Field(min_length=1, max_length=4000)
    correlation_id: UUID
    causation_id: UUID | None = None
    idempotency_key: UUID


class EligibilityQuery(XDIModel):
    scope: ScopeSelection


class ClosedResult(XDIModel):
    outcome: Literal[
        "success", "protected_not_found", "invalid_request", "version_conflict",
        "idempotency_conflict", "indeterminate", "unavailable",
    ]
    reason_code: str | None = None


class ReadinessResult(XDIModel):
    state: Literal["ready", "not_ready", "unavailable", "protected_not_found"]
    reason_codes: tuple[str, ...] = ()
    definition_digest: str | None = None


class EligibilityResult(XDIModel):
    state: Literal["eligible", "ineligible", "indeterminate", "unavailable", "protected_not_found"]
    reason_codes: tuple[str, ...] = ()
    definition_digest: str | None = None


class AssessmentSummary(XDIModel):
    assessment_id: UUID
    aggregate_version: int = Field(ge=1)
    status: Literal["completed_no_findings", "completed_with_findings", "indeterminate", "unavailable"]
    reason_code: str | None = None
    result_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    completed_at: datetime


class AssessmentView(AssessmentSummary):
    organization_id: UUID
    project_id: int
    execution_id: UUID
    snapshot_id: UUID
    snapshot_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    definition_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    workspace_ids: tuple[int, ...]
    advisory: Literal[True] = True


class FindingView(XDIModel):
    finding_id: UUID
    assessment_id: UUID
    ordinal: int = Field(ge=0, le=255)
    category: FindingCategory
    subcode: str
    severity: FindingSeverity
    fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    recurrence_key: str = Field(pattern=r"^[0-9a-f]{64}$")
    current_state: str = "open"
    allowed_actions: tuple[DispositionAction, ...] = ()
    provenance: dict[str, Any] = Field(default_factory=dict)
    advisory: Literal[True] = True


class AssessmentPage(XDIModel):
    items: tuple[AssessmentSummary, ...]
    next_cursor: str | None = None


class FindingPage(XDIModel):
    items: tuple[FindingView, ...]
    next_cursor: str | None = None


class DispositionAppend(XDIModel):
    action: DispositionAction
    expected_assessment_version: int = Field(ge=1)
    expected_current_view_version: int = Field(ge=0)
    rationale: str = Field(min_length=1, max_length=4000)
    correlation_id: UUID
    causation_id: UUID | None = None
    idempotency_key: UUID
    accepted_decision_id: UUID | None = None
    changed_source_references: tuple[str, ...] = Field(default=(), max_length=64)
    successor_assessment_id: UUID | None = None
    successor_finding_id: UUID | None = None
    supersedes_disposition_id: UUID | None = None


class DispositionView(XDIModel):
    disposition_id: UUID
    sequence: int = Field(ge=1)
    action: DispositionAction
    resulting_view_state: str
    actor_id: int
    rationale: str
    occurred_at: datetime
    view_version: int = Field(ge=1)


class DispositionPage(XDIModel):
    items: tuple[DispositionView, ...]
    next_cursor: str | None = None


class VerificationQuery(XDIModel):
    expected_snapshot_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    correlation_id: UUID


class VerificationResult(XDIModel):
    outcome: Literal["verified", "mismatch", "unavailable", "protected_not_found"]
    reason_code: str | None = None
    snapshot_digest: str | None = None
    result_digest: str | None = None


class ReassessmentCreate(XDIModel):
    scope: ScopeSelection
    expected_predecessor_version: int = Field(ge=1)
    rationale: str = Field(min_length=1, max_length=4000)
    correlation_id: UUID
    idempotency_key: UUID
    declare_supersession: bool = False


class SupersessionCreate(XDIModel):
    successor_assessment_id: UUID
    expected_predecessor_version: int = Field(ge=1)
    expected_successor_version: int = Field(ge=1)
    rationale: str = Field(min_length=1, max_length=4000)
    correlation_id: UUID
    idempotency_key: UUID


class LineageView(XDIModel):
    lineage_id: UUID
    kind: Literal["reassessment_of", "supersedes"]
    predecessor_id: UUID
    successor_id: UUID
    occurred_at: datetime


class LineagePage(XDIModel):
    items: tuple[LineageView, ...]
    next_cursor: str | None = None


class DependencyExplanation(XDIModel):
    assessment_id: UUID
    finding_id: UUID
    path: tuple[dict[str, str], ...] = Field(max_length=4)
    advisory: Literal[True] = True
