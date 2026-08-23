"""Closed Supporting File application boundary protocols."""
from dataclasses import dataclass
from datetime import datetime
from typing import BinaryIO, Protocol
from uuid import UUID
from app.models.supporting_file import SupportingFileAsset, SupportingFileScanAttempt
from app.models.supporting_file_command import SupportingFileHistoricalBasisV1


class SupportingFileRepository(Protocol):
    def add(self, asset: SupportingFileAsset) -> None: ...
    def get_scoped(self, asset_id: UUID, organization_id: UUID) -> SupportingFileAsset | None: ...
    def list_scoped(self, *, organization_id: UUID, project_id: int, workspace_id: int | None, lifecycle: str | None, limit: int) -> list[SupportingFileAsset]: ...
    def persist_expected_version(self, asset: SupportingFileAsset, expected_version: int) -> bool: ...
    def get_idempotency(self, *, organization_id: UUID, actor_id: int, operation: str, idempotency_id: UUID): ...
    def stage_idempotency(self, record) -> None: ...
    def next_scan_attempt_number(self, *, asset_id: UUID) -> int: ...
    def stage_scan_attempt(self, record: SupportingFileScanAttempt) -> None: ...
    def complete_scan_attempt(self, record: SupportingFileScanAttempt, *, disposition: str | None, completed_at: datetime, failed: bool = False, engine_id: str | None = None, signature_set_id: str | None = None, correlation_id: UUID | None = None) -> None: ...
    def get_scan_attempt(self, *, attempt_id: UUID, for_update: bool = False) -> SupportingFileScanAttempt | None: ...
    def get_latest_scan_attempt(self, *, asset_id: UUID, for_update: bool = False) -> SupportingFileScanAttempt | None: ...
    def list_candidates(self, *, organization_id: UUID, project_id: int, workspace_id: int | None, lifecycle: str | None, anchor: tuple[datetime, UUID] | None, limit: int) -> list[SupportingFileAsset]: ...


class SupportingFileObjectStore(Protocol):
    """Exact-key-only object storage; no list or public URL operation exists."""
    def put_private(self, *, key: str, content: BinaryIO, media_type: str) -> "SupportingFileObjectReceipt": ...
    def head_exact(self, key: str, version: str) -> "SupportingFileObjectReceipt | None": ...
    def open_exact(self, key: str, version: str) -> BinaryIO: ...
    def delete_exact(self, key: str, version: str) -> None: ...


@dataclass(frozen=True, slots=True)
class SupportingFileObjectReceipt:
    key: str
    version: str
    byte_size: int
    sha256: str


@dataclass(frozen=True, slots=True)
class SupportingFileScanResult:
    disposition: str
    scanned_at: datetime
    engine_id: str
    signature_set_id: str
    correlation_id: UUID


@dataclass(frozen=True, slots=True)
class SupportingFileScannerPrincipal:
    principal_id: str


@dataclass(frozen=True, slots=True)
class RecordSupportingFileScan:
    principal: SupportingFileScannerPrincipal
    asset_id: UUID
    asset_version: int
    attempt_id: UUID
    object_fingerprint: str
    disposition: str
    engine_id: str
    signature_set_id: str
    observed_at: datetime
    correlation_id: UUID


class SupportingFileScanner(Protocol):
    def scan_exact(self, *, key: str, version: str, sha256: str) -> SupportingFileScanResult: ...


class SupportingFileAuthorization(Protocol):
    def require_mutation(self, *, actor_id: int, organization_id: UUID, project_id: int, workspace_id: int | None) -> None: ...
    def require_read(self, *, actor_id: int, organization_id: UUID, project_id: int, workspace_id: int | None) -> None: ...
    def require_withdraw(self, *, actor_id: int, organization_id: UUID, project_id: int, workspace_id: int | None, uploader_id: int) -> None: ...


class SupportingFileUnitOfWork(Protocol):
    repository: SupportingFileRepository
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


class SupportingFileHistoricalResolver(Protocol):
    def resolve(self, *args, **kwargs): ...

class SupportingFileEvidenceCollaborator(Protocol):
    def authorize_and_lock_for_evidence(self, *, actor_id: int, organization_id: UUID, project_id: int, workspace_id: int | None, asset_ids: tuple[UUID, ...]) -> tuple[SupportingFileHistoricalBasisV1, ...]: ...
    def authorize_historical_for_evidence(self, *, actor_id: int, evidence_id: UUID, organization_id: UUID, project_id: int, workspace_id: int | None, historical: tuple[SupportingFileHistoricalBasisV1, ...]) -> tuple[SupportingFileHistoricalBasisV1, ...]: ...


class SupportingFileTechnicalReportCollaborator(Protocol):
    """Caller-Session boundary for exact Evidence-linked file history."""

    def resolve_for_evidence(self, *, evidence_id: UUID, organization_id: UUID, project_id: int, workspace_id: int | None, lock: bool) -> tuple[SupportingFileHistoricalBasisV1, ...]: ...
