"""Accepted inward/outward Protocols for PATCH-034 Organizational Memory."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from types import TracebackType
from typing import Protocol
from uuid import UUID

from app.models.organizational_memory import OrganizationalMemory
from app.models.organizational_memory_command import (
    AcceptedReportReadResult,
    AcceptedReportSource,
    ActiveMemoryCriteria,
    AdmitResult,
    AdmitAcceptedReport,
    CreateSuccessorResult,
    CreateMemorySuccessor,
    GetActiveResult,
    GetActiveMemory,
    InspectHistoryResult,
    InspectMemoryHistory,
    ListActiveResult,
    ListActiveMemory,
    MemoryActor,
    MemoryAuditRecord,
    MemoryAuthorizationRequest,
    MemoryFinalRecheckRequest,
    MemoryIdempotencyKey,
    MemoryIdempotencyLookup,
    MemoryOutboxRecord,
    MemoryProvenanceAuthorizationRequest,
    MemoryProvenanceAuthorizationResult,
    MemoryRejectionAuditRecord,
    MemoryStandingHistoryRecord,
    MemoryStoredResultV1,
    SupersedeResult,
    SupersedeMemory,
    WithdrawResult,
    WithdrawMemory,
)
from app.exceptions.organizational_memory import OrganizationalMemoryValidationError


@dataclass(frozen=True, slots=True)
class MemoryCandidatePage:
    items: tuple[OrganizationalMemory, ...]
    has_more: bool

    def __post_init__(self) -> None:
        if not isinstance(self.items, tuple) or len(self.items) > 101 or any(type(item) is not OrganizationalMemory for item in self.items):
            raise OrganizationalMemoryValidationError("candidate page items are invalid")
        if type(self.has_more) is not bool:
            raise OrganizationalMemoryValidationError("candidate page has_more must be boolean")


class AcceptedReportReader(Protocol):
    def read_authorized_accepted(self, actor: MemoryActor, source: AcceptedReportSource) -> AcceptedReportReadResult: ...


class MemoryProvenanceAuthorizer(Protocol):
    def authorize_and_resolve(self, request: MemoryProvenanceAuthorizationRequest) -> MemoryProvenanceAuthorizationResult: ...
    def authorize_logical_operation(
        self,
        requests: tuple[MemoryProvenanceAuthorizationRequest, ...],
    ) -> MemoryProvenanceAuthorizationResult: ...


class OrganizationalMemoryRepository(Protocol):
    def add(self, memory: OrganizationalMemory) -> None: ...
    def get_scoped(self, memory_id: UUID, organization_id: UUID) -> OrganizationalMemory | None: ...
    def get_by_source(self, source: AcceptedReportSource, organization_id: UUID) -> OrganizationalMemory | None: ...
    def lock_scoped(self, memory_id: UUID, organization_id: UUID) -> OrganizationalMemory | None: ...
    def lock_pair_scoped(self, first_id: UUID, second_id: UUID, organization_id: UUID) -> tuple[OrganizationalMemory, OrganizationalMemory] | None: ...
    def persist_standing_expected_version(self, memory: OrganizationalMemory, expected_version: int) -> bool: ...
    def list_active(self, criteria: ActiveMemoryCriteria) -> MemoryCandidatePage: ...
    def append_history(self, record: MemoryStandingHistoryRecord) -> None: ...


class MemoryAuthorizationPolicy(Protocol):
    def require(
        self, request: MemoryAuthorizationRequest,
        source_owner_id: int | None = None,
    ) -> None: ...


class MemoryFinalRecheckPolicy(Protocol):
    def require_current(
        self, request: MemoryFinalRecheckRequest,
        source_owner_id: int | None = None,
    ) -> None: ...


class MemoryAuditRecorder(Protocol):
    def record(self, record: MemoryAuditRecord) -> None: ...


class MemoryRejectionAuditRecorder(Protocol):
    def permit_after_authoritative_rollback(self) -> None: ...
    def record_rejection(self, record: MemoryRejectionAuditRecord) -> None: ...


class MemoryDomainEventRecorder(Protocol):
    def record(self, records: tuple[MemoryOutboxRecord, ...]) -> None: ...


class MemoryIdempotencyStore(Protocol):
    def find(self, key: MemoryIdempotencyKey) -> MemoryIdempotencyLookup: ...
    def reserve(self, key: MemoryIdempotencyKey, request_fingerprint: str) -> None: ...
    def record_result(self, key: MemoryIdempotencyKey, request_fingerprint: str, result: MemoryStoredResultV1) -> None: ...


class MemoryClock(Protocol):
    def now(self) -> datetime: ...


class OrganizationalMemoryUnitOfWork(Protocol):
    memories: OrganizationalMemoryRepository
    authorization: MemoryAuthorizationPolicy
    final_recheck: MemoryFinalRecheckPolicy
    audit: MemoryAuditRecorder
    domain_events: MemoryDomainEventRecorder
    idempotency: MemoryIdempotencyStore
    rejection_audit: MemoryRejectionAuditRecorder
    def __enter__(self) -> "OrganizationalMemoryUnitOfWork": ...
    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None) -> bool | None: ...
    def flush(self) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


class OrganizationalMemoryService(Protocol):
    def admit(self, command: AdmitAcceptedReport) -> AdmitResult: ...
    def get_active(self, actor: MemoryActor, request: GetActiveMemory) -> GetActiveResult: ...
    def list_active(self, actor: MemoryActor, request: ListActiveMemory) -> ListActiveResult: ...
    def inspect_history(self, actor: MemoryActor, request: InspectMemoryHistory) -> InspectHistoryResult: ...
    def create_successor(self, command: CreateMemorySuccessor) -> CreateSuccessorResult: ...
    def withdraw(self, command: WithdrawMemory) -> WithdrawResult: ...
    def supersede(self, command: SupersedeMemory) -> SupersedeResult: ...
