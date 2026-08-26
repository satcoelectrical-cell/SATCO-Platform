"""Typed, implementation-free inward ports for PATCH-032."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from app.exceptions.technical_report import TechnicalReportValidationError
from app.models.technical_report import TechnicalReport
from app.models.technical_report_command import (
    HistoricalBasis,
    TechnicalReportActor,
    TechnicalReportCommandResult,
    TechnicalReportDomainEvent,
    TechnicalReportProvenanceEntry,
)
from app.enums.technical_report import TechnicalReportLifecycle, TechnicalReportPurpose


@dataclass(frozen=True, slots=True)
class TechnicalReportScope:
    organization_id: UUID
    workspace_id: int
    project_id: int | None


class TechnicalReportHistoricalOperation(StrEnum):
    """Closed command contexts permitted to resolve protected source history."""

    CREATE_DRAFT = "create_draft"
    REVISE_DRAFT = "revise_draft"
    ACCEPT_EXACT_DRAFT = "accept_exact_draft"
    CREATE_SUCCESSOR = "create_successor"
    REQUEST_AI_PROPOSAL = "request_ai_proposal"


@dataclass(frozen=True, slots=True)
class CreateDraftHistoricalAuthority:
    operation: TechnicalReportHistoricalOperation = field(
        default=TechnicalReportHistoricalOperation.CREATE_DRAFT, init=False
    )


@dataclass(frozen=True, slots=True)
class ReviseDraftHistoricalAuthority:
    report_id: UUID
    owner_id: int
    operation: TechnicalReportHistoricalOperation = field(
        default=TechnicalReportHistoricalOperation.REVISE_DRAFT, init=False
    )


@dataclass(frozen=True, slots=True)
class AcceptExactDraftHistoricalAuthority:
    report_id: UUID
    owner_id: int
    operation: TechnicalReportHistoricalOperation = field(
        default=TechnicalReportHistoricalOperation.ACCEPT_EXACT_DRAFT, init=False
    )


@dataclass(frozen=True, slots=True)
class CreateSuccessorHistoricalAuthority:
    predecessor_report_id: UUID
    copy_protected_inputs: bool
    operation: TechnicalReportHistoricalOperation = field(
        default=TechnicalReportHistoricalOperation.CREATE_SUCCESSOR, init=False
    )


@dataclass(frozen=True, slots=True)
class RequestAIProposalHistoricalAuthority:
    report_id: UUID
    owner_id: int
    operation: TechnicalReportHistoricalOperation = field(
        default=TechnicalReportHistoricalOperation.REQUEST_AI_PROPOSAL, init=False
    )


TechnicalReportHistoricalAuthority = (
    CreateDraftHistoricalAuthority
    | ReviseDraftHistoricalAuthority
    | AcceptExactDraftHistoricalAuthority
    | CreateSuccessorHistoricalAuthority
    | RequestAIProposalHistoricalAuthority
)


@dataclass(frozen=True, slots=True)
class TechnicalReportReadCriteria:
    scope: TechnicalReportScope
    page: int
    size: int
    purpose: TechnicalReportPurpose | None = None
    lifecycle: TechnicalReportLifecycle | None = None


@dataclass(frozen=True, slots=True)
class TechnicalReportReadItem:
    report_id: UUID
    version: int


@dataclass(frozen=True, slots=True)
class TechnicalReportReadPage:
    items: tuple[TechnicalReportReadItem, ...]
    total: int
    page: int
    size: int


@dataclass(frozen=True, slots=True)
class AcceptedTechnicalReportSummary:
    """Bounded owner-produced cross-domain read projection.

    It deliberately omits report content, provenance, Humans and storage data.
    """
    report_id: UUID
    workspace_id: int
    project_id: int | None
    version: int
    accepted_digest: str
    accepted_at: datetime
    purpose: TechnicalReportPurpose


@dataclass(frozen=True, slots=True)
class AcceptedTechnicalReportSummaryPage:
    items: tuple[AcceptedTechnicalReportSummary, ...]
    page: int
    size: int
    has_more: bool


@dataclass(frozen=True, slots=True)
class TechnicalReportAuthorizationRequest:
    actor: TechnicalReportActor
    operation: str
    scope: TechnicalReportScope
    report_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class TechnicalReportReferenceRequest:
    actor: TechnicalReportActor
    scope: TechnicalReportScope
    reference_type: str
    reference_id: UUID | int


@dataclass(frozen=True, slots=True)
class TechnicalReportHistoricalRequest:
    actor: TechnicalReportActor
    scope: TechnicalReportScope
    authority: TechnicalReportHistoricalAuthority
    source_type: str
    source_id: UUID
    source_version: int

    def __post_init__(self) -> None:
        if not isinstance(
            self.authority,
            (
                CreateDraftHistoricalAuthority,
                ReviseDraftHistoricalAuthority,
                AcceptExactDraftHistoricalAuthority,
                CreateSuccessorHistoricalAuthority,
                RequestAIProposalHistoricalAuthority,
            ),
        ):
            raise TypeError("historical authority context is invalid")


@dataclass(frozen=True, slots=True)
class TechnicalReportAIRequest:
    actor: TechnicalReportActor
    report_id: UUID
    authorized_context: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TechnicalReportAIProposal:
    proposal_text: str
    attribution: str


@dataclass(frozen=True, slots=True)
class TechnicalReportAuditRecord:
    actor_id: int
    organization_id: UUID
    report_id: UUID
    operation: str
    command_id: UUID
    correlation_id: UUID
    occurred_at: datetime


class TechnicalReportRejectionReason(StrEnum):
    NON_OWNER_ACCEPTANCE = "non_owner_acceptance"
    CROSS_ORGANIZATION = "cross_organization"
    AI_AUTHORITY_ATTEMPT = "ai_authority_attempt"
    ACCEPTED_STATE_MUTATION = "accepted_state_mutation"


@dataclass(frozen=True, slots=True)
class TechnicalReportRejectionAuditRecord:
    actor_id: int
    organization_id: UUID
    operation: str
    reason: TechnicalReportRejectionReason
    report_id: UUID | None
    command_id: UUID | None
    correlation_id: UUID
    occurred_at: datetime

    def __post_init__(self) -> None:
        if isinstance(self.actor_id, bool) or not isinstance(self.actor_id, int) or self.actor_id <= 0:
            raise TechnicalReportValidationError("actor_id is invalid")
        for name in ("organization_id", "correlation_id"):
            if not isinstance(getattr(self, name), UUID):
                raise TechnicalReportValidationError(f"{name} is invalid")
        for name in ("report_id", "command_id"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, UUID):
                raise TechnicalReportValidationError(f"{name} is invalid")
        if (
            not isinstance(self.occurred_at, datetime)
            or self.occurred_at.tzinfo is None
            or self.occurred_at.utcoffset() is None
        ):
            raise TechnicalReportValidationError("occurred_at must be timezone-aware")
        if (
            not isinstance(self.operation, str)
            or self.operation != self.operation.strip()
            or not self.operation
            or "\n" in self.operation
            or "\r" in self.operation
            or len(self.operation) > 128
        ):
            raise TechnicalReportValidationError("rejection Audit operation is invalid")
        operation = self.operation
        if operation not in {
            "CreateTechnicalReportDraft",
            "ReviseTechnicalReportDraft",
            "AcceptExactTechnicalReportDraft",
            "CreateTechnicalReportSuccessor",
        }:
            raise TechnicalReportValidationError(
                "rejection Audit operation is invalid"
            )
        try:
            reason = TechnicalReportRejectionReason(self.reason)
        except (TypeError, ValueError) as exc:
            raise TechnicalReportValidationError(
                "rejection Audit reason is invalid"
            ) from exc
        object.__setattr__(self, "operation", operation)
        object.__setattr__(self, "reason", reason)


@dataclass(frozen=True, slots=True)
class TechnicalReportIdempotencyKey:
    organization_id: UUID
    actor_id: int
    command_type: str
    idempotency_id: UUID


@dataclass(frozen=True, slots=True)
class TechnicalReportFinalRecheckRequest:
    actor: TechnicalReportActor
    scope: TechnicalReportScope
    report_id: UUID
    owner_id: int
    expected_version: int
    expected_draft_revision_id: UUID
    sources: tuple[TechnicalReportHistoricalRequest, ...]


class TechnicalReportRepository(Protocol):
    def add(self, report: TechnicalReport) -> None: ...
    def get_scoped(self, report_id: UUID, organization_id: UUID) -> TechnicalReport | None: ...
    def persist_draft_expected_version(self, report: TechnicalReport, expected_version: int) -> bool: ...
    def persist_acceptance_expected_version(self, report: TechnicalReport, expected_version: int) -> bool: ...
    def list_scoped(self, criteria: TechnicalReportReadCriteria) -> TechnicalReportReadPage: ...
    def list_successors_scoped(self, predecessor_id: UUID, criteria: TechnicalReportReadCriteria) -> TechnicalReportReadPage: ...
    def provenance_for_report(self, report_id: UUID) -> tuple[TechnicalReportProvenanceEntry, ...]: ...
    def list_graph_provenance_links(self, *, scope: TechnicalReportScope, source_kind: str, source_id: UUID, limit: int) -> tuple["TechnicalReportGraphProvenanceLink", ...]: ...

@dataclass(frozen=True, slots=True)
class TechnicalReportGraphProvenanceLink:
    report_id: UUID
    entry_id: UUID
    source_kind: str
    source_id: UUID
    report_version: int
    accepted_at: datetime


class TechnicalReportAuthorizationPolicy(Protocol):
    def require(self, request: TechnicalReportAuthorizationRequest) -> None: ...


class TechnicalReportReferenceValidator(Protocol):
    def validate(self, request: TechnicalReportReferenceRequest) -> None: ...


class TechnicalReportHistoricalResolver(Protocol):
    def resolve(self, request: TechnicalReportHistoricalRequest) -> HistoricalBasis: ...


class TechnicalReportDraftAssistant(Protocol):
    def propose(self, request: TechnicalReportAIRequest) -> TechnicalReportAIProposal: ...


class TechnicalReportAuditRecorder(Protocol):
    def record(self, record: TechnicalReportAuditRecord) -> None: ...


class TechnicalReportRejectionAuditRecorder(Protocol):
    def record_rejection(self, record: TechnicalReportRejectionAuditRecord) -> None: ...


class TechnicalReportDomainEventRecorder(Protocol):
    def record(self, events: tuple[TechnicalReportDomainEvent, ...]) -> None: ...


class TechnicalReportIdempotencyStore(Protocol):
    def find(self, key: TechnicalReportIdempotencyKey, request_fingerprint: str) -> TechnicalReportCommandResult | None: ...
    def reserve(self, key: TechnicalReportIdempotencyKey, request_fingerprint: str) -> None: ...
    def record_result(self, key: TechnicalReportIdempotencyKey, result: TechnicalReportCommandResult) -> None: ...


class TechnicalReportClock(Protocol):
    def now(self) -> datetime: ...


class TechnicalReportFinalRecheckPolicy(Protocol):
    def require_current(self, request: TechnicalReportFinalRecheckRequest) -> None: ...


class TechnicalReportUnitOfWork(Protocol):
    technical_reports: TechnicalReportRepository
    authorization: TechnicalReportAuthorizationPolicy
    references: TechnicalReportReferenceValidator
    historical: TechnicalReportHistoricalResolver
    audit: TechnicalReportAuditRecorder
    domain_events: TechnicalReportDomainEventRecorder
    idempotency: TechnicalReportIdempotencyStore
    final_recheck: TechnicalReportFinalRecheckPolicy
    rejection_audit: TechnicalReportRejectionAuditRecorder
    def __enter__(self) -> TechnicalReportUnitOfWork: ...
    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: object | None) -> bool | None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
