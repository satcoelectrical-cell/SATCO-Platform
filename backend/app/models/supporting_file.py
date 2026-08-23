"""Supporting File Asset Aggregate and SQLAlchemy persistence records."""
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import BigInteger, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func
from sqlalchemy import JSON

from app.core.database import Base
from app.enums.supporting_file import SupportingFileLifecycle, SupportingFileMediaType
from app.exceptions.supporting_file import SupportingFileInvalidTransition, SupportingFileValidationError, SupportingFileVersionConflict
from app.models.supporting_file_command import MAX_FILE_BYTES, SupportingFileScope, content_digest, opaque_storage_key, safe_filename


class SupportingFileAsset(Base):
    __tablename__ = "supporting_file_assets"
    __table_args__ = (
        CheckConstraint("byte_size BETWEEN 1 AND 26214400", name="ck_supporting_file_size"),
        CheckConstraint("version >= 1", name="ck_supporting_file_version"),
        CheckConstraint("lifecycle IN ('quarantined','available','rejected','withdrawn')", name="ck_supporting_file_lifecycle"),
        CheckConstraint("digest_algorithm='sha256' AND content_digest ~ '^[0-9a-f]{64}$'", name="ck_supporting_file_digest"),
        CheckConstraint("workspace_id IS NULL OR project_id IS NOT NULL", name="ck_supporting_file_workspace_project"),
        UniqueConstraint("storage_key", name="uq_supporting_file_storage_key"),
        Index("ix_supporting_file_scope_order", "organization_id", "project_id", "workspace_id", "uploaded_at", "id"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"))
    safe_filename = Column(String(255), nullable=False)
    safe_ascii_filename = Column(String(120), nullable=False)
    media_type = Column(String(128), nullable=False)
    byte_size = Column(BigInteger, nullable=False)
    digest_algorithm = Column(String(16), nullable=False, default="sha256", server_default="sha256")
    content_digest = Column(String(64), nullable=False)
    storage_key = Column(String(80), nullable=False)
    object_version = Column(String(160), nullable=False)
    uploader_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    lifecycle = Column(String(16), nullable=False, default="quarantined", server_default="quarantined")
    predecessor_asset_id = Column(PGUUID(as_uuid=True), ForeignKey("supporting_file_assets.id", ondelete="RESTRICT"))
    version = Column(Integer, nullable=False, default=1, server_default="1")
    uploaded_at = Column(DateTime(timezone=True), nullable=False)
    scan_requested_at = Column(DateTime(timezone=True), nullable=False)
    scanned_at = Column(DateTime(timezone=True))
    withdrawn_at = Column(DateTime(timezone=True))
    withdrawn_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"))
    withdrawal_reason_code = Column(String(64))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    @classmethod
    def quarantine(cls, *, scope: SupportingFileScope, filename: str, media_type: SupportingFileMediaType, byte_size: int, digest: str, storage_key: str, object_version: str, uploader_id: int, now: datetime, predecessor_asset_id: UUID | None = None):
        if byte_size < 1 or byte_size > MAX_FILE_BYTES or uploader_id < 1 or not object_version:
            raise SupportingFileValidationError("asset metadata is invalid")
        name, ascii_name = safe_filename(filename)
        return cls(id=uuid4(), organization_id=scope.organization_id, project_id=scope.project_id, workspace_id=scope.workspace_id, safe_filename=name, safe_ascii_filename=ascii_name, media_type=SupportingFileMediaType(media_type).value, byte_size=byte_size, digest_algorithm="sha256", content_digest=content_digest(digest), storage_key=opaque_storage_key(storage_key), object_version=object_version, uploader_id=uploader_id, lifecycle=SupportingFileLifecycle.QUARANTINED.value, predecessor_asset_id=predecessor_asset_id, version=1, uploaded_at=now, scan_requested_at=now, created_at=now, updated_at=now)

    def mark_available(self, expected_version: int, now: datetime):
        self._transition(expected_version, SupportingFileLifecycle.AVAILABLE, now)

    def mark_rejected(self, expected_version: int, now: datetime):
        self._transition(expected_version, SupportingFileLifecycle.REJECTED, now)

    def withdraw(self, expected_version: int, actor_id: int, now: datetime, reason_code: str):
        if not reason_code or len(reason_code) > 64:
            raise SupportingFileValidationError("withdrawal reason is invalid")
        self._transition(expected_version, SupportingFileLifecycle.WITHDRAWN, now)
        self.withdrawn_at, self.withdrawn_by_id, self.withdrawal_reason_code = now, actor_id, reason_code

    def _transition(self, expected_version: int, target: SupportingFileLifecycle, now: datetime):
        if self.version != expected_version:
            raise SupportingFileVersionConflict()
        allowed = {SupportingFileLifecycle.QUARANTINED: {SupportingFileLifecycle.AVAILABLE, SupportingFileLifecycle.REJECTED}, SupportingFileLifecycle.AVAILABLE: {SupportingFileLifecycle.WITHDRAWN}}
        current = SupportingFileLifecycle(self.lifecycle)
        if target not in allowed.get(current, set()):
            raise SupportingFileInvalidTransition()
        self.lifecycle, self.version, self.updated_at = target.value, self.version + 1, now
        if target in {SupportingFileLifecycle.AVAILABLE, SupportingFileLifecycle.REJECTED}:
            self.scanned_at = now


class SupportingFileUploadReservation(Base):
    __tablename__ = "supporting_file_upload_reservations"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"))
    storage_key = Column(String(80), nullable=False, unique=True)
    status = Column(String(16), nullable=False, server_default="reserved")
    asset_id = Column(PGUUID(as_uuid=True), ForeignKey("supporting_file_assets.id", ondelete="RESTRICT"), unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class EvidenceSupportingFileLink(Base):
    __tablename__ = "evidence_supporting_file_links"
    evidence_id = Column(PGUUID(as_uuid=True), ForeignKey("evidence.id", ondelete="RESTRICT"), primary_key=True)
    asset_id = Column(PGUUID(as_uuid=True), ForeignKey("supporting_file_assets.id", ondelete="RESTRICT"), primary_key=True)
    organization_id = Column(PGUUID(as_uuid=True), nullable=False)
    project_id = Column(Integer, nullable=False)
    workspace_id = Column(Integer)
    evidence_version = Column(Integer, nullable=False)
    ordinal = Column(Integer, nullable=False)
    linked_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    linked_at = Column(DateTime(timezone=True), nullable=False)
    __table_args__ = (UniqueConstraint("evidence_id", "ordinal", name="uq_evidence_file_ordinal"), CheckConstraint("ordinal BETWEEN 0 AND 9", name="ck_evidence_file_ordinal"))


class SupportingFileScanAttempt(Base):
    """Immutable technical scan history; scanner diagnostics remain protected."""
    __tablename__ = "supporting_file_scan_attempts"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    asset_id = Column(PGUUID(as_uuid=True), ForeignKey("supporting_file_assets.id", ondelete="RESTRICT"), nullable=False)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    expected_asset_version = Column(Integer, nullable=False)
    object_digest = Column(String(64), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    state = Column(String(16), nullable=False)
    engine_id = Column(String(128))
    signature_set_id = Column(String(128))
    correlation_id = Column(PGUUID(as_uuid=True))
    disposition = Column(String(16))
    requested_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("asset_id", "attempt_number", name="uq_supporting_file_scan_attempt_ordinal"),
        CheckConstraint("attempt_number BETWEEN 1 AND 3", name="ck_supporting_file_scan_attempt_ordinal"),
        CheckConstraint("state IN ('requested','completed','failed')", name="ck_supporting_file_scan_attempt_state"),
        CheckConstraint("disposition IS NULL OR disposition IN ('clean','unsafe','indeterminate')", name="ck_supporting_file_scan_attempt_disposition"),
        CheckConstraint("object_digest ~ '^[0-9a-f]{64}$'", name="ck_supporting_file_scan_attempt_digest"),
        CheckConstraint("(state='requested' AND completed_at IS NULL AND disposition IS NULL AND engine_id IS NULL AND signature_set_id IS NULL AND correlation_id IS NULL) OR (state='completed' AND completed_at IS NOT NULL AND disposition IN ('clean','unsafe') AND engine_id IS NOT NULL AND signature_set_id IS NOT NULL AND correlation_id IS NOT NULL) OR (state='failed' AND completed_at IS NOT NULL AND (disposition IS NULL OR disposition='indeterminate') AND ((disposition IS NULL AND engine_id IS NULL AND signature_set_id IS NULL AND correlation_id IS NULL) OR (disposition='indeterminate' AND engine_id IS NOT NULL AND signature_set_id IS NOT NULL AND correlation_id IS NOT NULL)))", name="ck_supporting_file_scan_attempt_state_closure"),
        UniqueConstraint("correlation_id", name="uq_supporting_file_scan_attempt_correlation"),
        Index("ix_supporting_file_scan_attempt_scope", "organization_id", "asset_id", "attempt_number"),
    )


class SupportingFileOutboxRecord(Base):
    __tablename__ = "supporting_file_outbox"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_id = Column(PGUUID(as_uuid=True), nullable=False, unique=True)
    asset_id = Column(PGUUID(as_uuid=True), ForeignKey("supporting_file_assets.id", ondelete="RESTRICT"), nullable=False)
    aggregate_version = Column(Integer, nullable=False)
    event_type = Column(String(96), nullable=False)
    payload = Column(JSON, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SupportingFileIdempotencyRecord(Base):
    __tablename__ = "supporting_file_idempotency"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    operation = Column(String(32), nullable=False)
    idempotency_id = Column(PGUUID(as_uuid=True), nullable=False)
    request_fingerprint = Column(String(64), nullable=False)
    status = Column(String(16), nullable=False, server_default="pending")
    asset_id = Column(PGUUID(as_uuid=True), ForeignKey("supporting_file_assets.id", ondelete="RESTRICT"))
    result = Column(JSON)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    __table_args__ = (UniqueConstraint("organization_id", "actor_id", "operation", "idempotency_id", name="uq_supporting_file_idempotency_scope"), CheckConstraint("status IN ('pending','completed')", name="ck_supporting_file_idempotency_status"))
