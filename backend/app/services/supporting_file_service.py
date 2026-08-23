"""Supporting File data-plane orchestration with no transport ownership."""
import base64
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from io import BytesIO
import json
import os
from uuid import UUID, uuid4
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.adapters.supporting_file_object_store import new_opaque_object_key
from app.adapters.supporting_file_scanner import SCANNER_PRINCIPAL_ID
from app.enums.supporting_file import SupportingFileMediaType, SupportingFileScanDisposition
from app.exceptions.supporting_file import SupportingFileIntegrityError, SupportingFileProtectedNotFound, SupportingFileScannerUnavailable, SupportingFileValidationError
from app.models.supporting_file import EvidenceSupportingFileLink, SupportingFileAsset, SupportingFileUploadReservation, SupportingFileIdempotencyRecord, SupportingFileOutboxRecord, SupportingFileScanAttempt
from app.models.supporting_file_command import MAX_FILE_BYTES, SupportingFileActor, SupportingFileMetadata, SupportingFileScope, bounded_stream_identity, content_digest, safe_filename, verified_media_type, verified_stream_media_type
from app.models.supporting_file_command import SupportingFileHistoricalBasisV1
from app.core.config import settings
from app.ports.supporting_file import RecordSupportingFileScan, SupportingFileAuthorization, SupportingFileObjectStore, SupportingFileScanner, SupportingFileScannerPrincipal, SupportingFileUnitOfWork


class SupportingFileService:
    def __init__(self, *, uow: SupportingFileUnitOfWork, objects: SupportingFileObjectStore, scanner: SupportingFileScanner, authorization: SupportingFileAuthorization):
        self.uow, self.objects, self.scanner, self.authorization = uow, objects, scanner, authorization

    def _stage_success(self, *, actor_id, operation, idempotency_id, fingerprint, asset, now, correlation_id):
        """Stage capability-owned success evidence in the same UoW, never after commit."""
        if idempotency_id is None or fingerprint is None: return
        existing = self.uow.repository.get_idempotency(organization_id=asset.organization_id, actor_id=actor_id, operation=operation, idempotency_id=idempotency_id)
        if existing is not None:
            if existing.request_fingerprint != fingerprint: raise SupportingFileIntegrityError("idempotency conflict")
            if existing.status == "completed": return existing
            existing.status, existing.asset_id, existing.result, existing.updated_at = "completed", asset.id, {"asset_id": str(asset.id), "version": asset.version}, now
            record = existing
        else:
            record = SupportingFileIdempotencyRecord(id=uuid4(), organization_id=asset.organization_id, actor_id=actor_id, operation=operation, idempotency_id=idempotency_id, request_fingerprint=fingerprint, status="completed", asset_id=asset.id, result={"asset_id": str(asset.id), "version": asset.version})
            self.uow.repository.stage_idempotency(record)
        self.uow.repository.stage_outbox(SupportingFileOutboxRecord(id=uuid4(), event_id=uuid4(), asset_id=asset.id, aggregate_version=asset.version, event_type=f"SupportingFile{operation.title()}", payload={"asset_id": str(asset.id), "version": asset.version}, occurred_at=now))
        self.uow.repository.stage_audit(
            actor_id=actor_id, asset_id=asset.id,
            action={"finalize_upload": "SUPPORTING_FILE_UPLOAD_FINALIZED", "withdraw": "WITHDRAWN"}[operation],
            occurred_at=now, organization_id=asset.organization_id,
            version=asset.version, correlation_id=correlation_id,
        )

    @staticmethod
    def _require_scanner_principal(principal: SupportingFileScannerPrincipal) -> None:
        if not isinstance(principal, SupportingFileScannerPrincipal) or principal.principal_id != SCANNER_PRINCIPAL_ID:
            raise SupportingFileProtectedNotFound()

    def _stage_scan_evidence(self, *, asset, attempt, now):
        self.uow.repository.stage_outbox(SupportingFileOutboxRecord(
            id=uuid4(), event_id=uuid4(), asset_id=asset.id,
            aggregate_version=asset.version,
            event_type=("SupportingFileScanRecorded" if attempt.disposition is not None else "SupportingFileScanFailed"),
            payload={"asset_id": str(asset.id), "version": asset.version,
                     "attempt_id": str(attempt.id), "attempt_number": attempt.attempt_number,
                     "disposition": attempt.disposition},
            occurred_at=now,
        ))
        self.uow.repository.stage_audit(
            actor_id=None, asset_id=asset.id,
            action=("SCAN_REJECTED" if attempt.disposition == "unsafe" else "SCAN_AVAILABLE" if attempt.disposition == "clean" else "SCAN_RETRY"), occurred_at=now,
            organization_id=asset.organization_id, version=asset.version,
            principal_id=SCANNER_PRINCIPAL_ID,
            correlation_id=attempt.correlation_id,
        )

    def _apply_scan_result(self, request: RecordSupportingFileScan, *, commit: bool) -> SupportingFileAsset:
        self._require_scanner_principal(request.principal)
        if (
            not isinstance(request.asset_version, int)
            or request.asset_version < 1
            or not isinstance(request.object_fingerprint, str)
            or len(request.object_fingerprint) != 64
            or any(ch not in "0123456789abcdef" for ch in request.object_fingerprint)
            or request.disposition not in {item.value for item in SupportingFileScanDisposition}
            or not isinstance(request.engine_id, str)
            or not 1 <= len(request.engine_id) <= 128
            or request.engine_id.strip() != request.engine_id
            or not isinstance(request.signature_set_id, str)
            or not 1 <= len(request.signature_set_id) <= 128
            or request.signature_set_id.strip() != request.signature_set_id
            or not isinstance(request.observed_at, datetime)
            or request.observed_at.tzinfo is None
            or not isinstance(request.correlation_id, UUID)
            or request.correlation_id.int == 0
        ):
            raise SupportingFileProtectedNotFound()
        attempt = self.uow.repository.get_scan_attempt(attempt_id=request.attempt_id, for_update=True)
        if attempt is None or attempt.asset_id != request.asset_id:
            raise SupportingFileProtectedNotFound()
        asset = self.uow.repository.get_scoped(request.asset_id, attempt.organization_id)
        latest = self.uow.repository.get_latest_scan_attempt(asset_id=request.asset_id, for_update=True)
        if asset is None or latest is None:
            raise SupportingFileProtectedNotFound()
        exact = (
            attempt.expected_asset_version == request.asset_version
            and attempt.object_digest == request.object_fingerprint
            and attempt.id == latest.id
        )
        if not exact:
            raise SupportingFileProtectedNotFound()
        if attempt.state in {"completed", "failed"}:
            duplicate = (
                attempt.disposition == request.disposition
                and attempt.engine_id == request.engine_id
                and attempt.signature_set_id == request.signature_set_id
                and attempt.correlation_id == request.correlation_id
                and attempt.completed_at == request.observed_at
            )
            if duplicate:
                if commit:
                    self.uow.commit()
                return asset
            raise SupportingFileIntegrityError("conflicting scanner result")
        if (
            attempt.state != "requested"
            or asset.version != request.asset_version
            or asset.content_digest != request.object_fingerprint
            or asset.lifecycle != "quarantined"
        ):
            raise SupportingFileProtectedNotFound()
        failed = request.disposition == SupportingFileScanDisposition.INDETERMINATE.value
        self.uow.repository.complete_scan_attempt(
            attempt, disposition=request.disposition,
            completed_at=request.observed_at, failed=failed,
            engine_id=request.engine_id,
            signature_set_id=request.signature_set_id,
            correlation_id=request.correlation_id,
        )
        if request.disposition == SupportingFileScanDisposition.CLEAN.value:
            asset.mark_available(request.asset_version, request.observed_at)
        elif request.disposition == SupportingFileScanDisposition.UNSAFE.value:
            asset.mark_rejected(request.asset_version, request.observed_at)
        if asset.version != request.asset_version and not self.uow.repository.persist_expected_version(asset, request.asset_version):
            raise SupportingFileIntegrityError("concurrent asset transition")
        self._stage_scan_evidence(asset=asset, attempt=attempt, now=request.observed_at)
        if commit:
            self.uow.commit()
        return asset
    def record_scan_result(self, request: RecordSupportingFileScan) -> SupportingFileAsset:
        try:
            return self._apply_scan_result(request, commit=True)
        except Exception:
            self.uow.rollback()
            raise

    def retry_scan(self, *, principal: SupportingFileScannerPrincipal, asset_id: UUID, expected_asset_version: int, expected_attempt_number: int, now: datetime | None = None) -> SupportingFileAsset:
        """Create exactly one next durable attempt, then invoke and record it."""
        self._require_scanner_principal(principal)
        now = now or datetime.now(timezone.utc)
        latest = self.uow.repository.get_latest_scan_attempt(asset_id=asset_id, for_update=True)
        if latest is None:
            raise SupportingFileProtectedNotFound()
        asset = self.uow.repository.get_scoped(asset_id, latest.organization_id)
        if (
            asset is None or asset.lifecycle != "quarantined"
            or asset.version != expected_asset_version
            or latest.state != "failed" or latest.attempt_number != expected_attempt_number
            or latest.attempt_number >= 3
            or latest.object_digest != asset.content_digest
        ):
            raise SupportingFileProtectedNotFound()
        attempt = SupportingFileScanAttempt(
            id=uuid4(), asset_id=asset.id, organization_id=asset.organization_id,
            expected_asset_version=asset.version,
            object_digest=asset.content_digest,
            attempt_number=latest.attempt_number + 1,
            state="requested", requested_at=now,
        )
        try:
            self.uow.repository.stage_scan_attempt(attempt)
            self.uow.repository.stage_outbox(SupportingFileOutboxRecord(
                id=uuid4(), event_id=uuid4(), asset_id=asset.id,
                aggregate_version=asset.version,
                event_type="SupportingFileScanRequested",
                payload={"asset_id": str(asset.id), "version": asset.version,
                         "attempt_id": str(attempt.id),
                         "attempt_number": attempt.attempt_number},
                occurred_at=now,
            ))
            self.uow.repository.stage_audit(
                actor_id=None, asset_id=asset.id,
                action="SCAN_RETRY", occurred_at=now,
                organization_id=asset.organization_id, version=asset.version,
                principal_id=SCANNER_PRINCIPAL_ID,
            )
            self.uow.commit()
        except SQLAlchemyError:
            self.uow.rollback()
            raise SupportingFileIntegrityError("concurrent scan retry") from None
        except Exception:
            self.uow.rollback()
            raise
        try:
            scan = self.scanner.scan_exact(
                key=asset.storage_key, version=asset.object_version,
                sha256=asset.content_digest,
            )
        except SupportingFileScannerUnavailable:
            try:
                attempt = self.uow.repository.get_scan_attempt(attempt_id=attempt.id, for_update=True)
                self.uow.repository.complete_scan_attempt(
                    attempt, disposition=None, completed_at=now, failed=True,
                )
                self._stage_scan_evidence(asset=asset, attempt=attempt, now=now)
                self.uow.commit()
                return asset
            except Exception:
                self.uow.rollback()
                raise
        return self.record_scan_result(RecordSupportingFileScan(
            principal=principal, asset_id=asset.id, asset_version=asset.version,
            attempt_id=attempt.id, object_fingerprint=asset.content_digest,
            disposition=scan.disposition, engine_id=scan.engine_id,
            signature_set_id=scan.signature_set_id,
            observed_at=scan.scanned_at, correlation_id=scan.correlation_id,
        ))

    def reserve_upload(self, *, actor_id: int, scope: SupportingFileScope, now: datetime | None = None) -> SupportingFileUploadReservation:
        now = now or datetime.now(timezone.utc)
        self.authorization.require_mutation(actor_id=actor_id, organization_id=scope.organization_id, project_id=scope.project_id, workspace_id=scope.workspace_id)
        reservation = SupportingFileUploadReservation(id=uuid4(), actor_id=actor_id, organization_id=scope.organization_id, project_id=scope.project_id, workspace_id=scope.workspace_id, storage_key=new_opaque_object_key(), status="reserved", expires_at=now + timedelta(minutes=15), created_at=now)
        self.uow.repository.add_reservation(reservation)
        self.uow.commit()
        return reservation

    def finalize_upload(self, *, actor_id: int, reservation_id: UUID, scope: SupportingFileScope, filename: str, media_type: SupportingFileMediaType, content, expected_digest: str, rationale: str, correlation_id: UUID, idempotency_id: UUID, request_fingerprint: str, predecessor_asset_id: UUID | None = None, now: datetime | None = None) -> SupportingFileAsset:
        now = now or datetime.now(timezone.utc)
        SupportingFileMetadata(
            SupportingFileActor(actor_id, scope.organization_id),
            correlation_id, idempotency_id, rationale,
        )
        self.authorization.require_mutation(actor_id=actor_id, organization_id=scope.organization_id, project_id=scope.project_id, workspace_id=scope.workspace_id)
        reservation = self.uow.repository.get_reservation(reservation_id, scope.organization_id)
        if reservation is None or reservation.actor_id != actor_id or reservation.project_id != scope.project_id or reservation.workspace_id != scope.workspace_id:
            raise SupportingFileProtectedNotFound()
        if idempotency_id is not None:
            if not request_fingerprint or len(request_fingerprint) != 64:
                raise SupportingFileValidationError("idempotency fingerprint is invalid")
            prior = self.uow.repository.get_idempotency(organization_id=scope.organization_id, actor_id=actor_id, operation="finalize_upload", idempotency_id=idempotency_id)
            if prior is not None:
                if prior.request_fingerprint != request_fingerprint:
                    raise SupportingFileIntegrityError("idempotency conflict")
                if prior.status == "completed" and prior.asset_id is not None:
                    replay = self.uow.repository.get_scoped(prior.asset_id, scope.organization_id)
                    if replay is None or replay.project_id != scope.project_id or replay.workspace_id != scope.workspace_id:
                        raise SupportingFileProtectedNotFound()
                    return replay
                raise SupportingFileIntegrityError("idempotency operation pending")
            try:
                self.uow.repository.stage_idempotency(SupportingFileIdempotencyRecord(id=uuid4(), organization_id=scope.organization_id, actor_id=actor_id, operation="finalize_upload", idempotency_id=idempotency_id, request_fingerprint=request_fingerprint, status="pending"))
            except IntegrityError:
                self.uow.rollback()
                prior = self.uow.repository.get_idempotency(organization_id=scope.organization_id, actor_id=actor_id, operation="finalize_upload", idempotency_id=idempotency_id)
                if prior is None or prior.request_fingerprint != request_fingerprint or prior.status != "completed" or prior.asset_id is None:
                    raise SupportingFileIntegrityError("idempotency concurrency conflict")
                replay = self.uow.repository.get_scoped(prior.asset_id, scope.organization_id)
                if replay is None or replay.project_id != scope.project_id or replay.workspace_id != scope.workspace_id:
                    raise SupportingFileProtectedNotFound()
                return replay
        if reservation.status != "reserved" or reservation.expires_at <= now:
            raise SupportingFileProtectedNotFound()
        stream = BytesIO(content) if isinstance(content, bytes) else content
        byte_size, measured_digest = bounded_stream_identity(stream)
        safe_filename(filename); expected_digest = content_digest(expected_digest)
        if measured_digest != expected_digest:
            raise SupportingFileIntegrityError("content digest mismatch")
        media_type = verified_stream_media_type(stream, SupportingFileMediaType(media_type))
        if predecessor_asset_id is not None:
            predecessor = self.uow.repository.get_scoped(predecessor_asset_id, scope.organization_id)
            if predecessor is None or predecessor.project_id != scope.project_id or predecessor.workspace_id != scope.workspace_id or predecessor.lifecycle not in {"available", "withdrawn"}:
                raise SupportingFileProtectedNotFound()
        receipt = self.objects.put_private(key=reservation.storage_key, content=stream, media_type=SupportingFileMediaType(media_type).value)
        if receipt.key != reservation.storage_key or receipt.byte_size != byte_size or receipt.sha256 != expected_digest:
            self.objects.delete_exact(receipt.key, receipt.version)
            raise SupportingFileIntegrityError("object receipt does not match upload")
        asset = SupportingFileAsset.quarantine(scope=scope, filename=filename, media_type=media_type, byte_size=receipt.byte_size, digest=receipt.sha256, storage_key=receipt.key, object_version=receipt.version, uploader_id=actor_id, now=now, predecessor_asset_id=predecessor_asset_id)
        try:
            self.uow.repository.add(asset)
            attempt = SupportingFileScanAttempt(
                id=uuid4(), asset_id=asset.id, organization_id=asset.organization_id,
                expected_asset_version=asset.version, object_digest=asset.content_digest,
                attempt_number=self.uow.repository.next_scan_attempt_number(asset_id=asset.id),
                state="requested", requested_at=now,
            )
            self.uow.repository.stage_scan_attempt(attempt)
            try:
                scan = self.scanner.scan_exact(key=receipt.key, version=receipt.version, sha256=receipt.sha256)
            except SupportingFileScannerUnavailable:
                # Preserve the exact private object and DB reservation for a
                # later, bounded scanner/reconciliation attempt; never promote.
                self.uow.repository.complete_scan_attempt(attempt, disposition=None, completed_at=now, failed=True)
                self._stage_scan_evidence(asset=asset, attempt=attempt, now=now)
                self.uow.repository.bind_reservation_asset(reservation, asset, "uploaded")
                self._stage_success(actor_id=actor_id, operation="finalize_upload", idempotency_id=idempotency_id, fingerprint=request_fingerprint, asset=asset, now=now, correlation_id=correlation_id)
                self.uow.commit()
                return asset
            if scan.disposition not in {item.value for item in SupportingFileScanDisposition}:
                self.uow.repository.complete_scan_attempt(attempt, disposition=None, completed_at=now, failed=True)
                self._stage_scan_evidence(asset=asset, attempt=attempt, now=now)
                self.uow.repository.bind_reservation_asset(reservation, asset, "uploaded")
                self._stage_success(actor_id=actor_id, operation="finalize_upload", idempotency_id=idempotency_id, fingerprint=request_fingerprint, asset=asset, now=now, correlation_id=correlation_id)
                self.uow.commit()
                return asset
            asset = self._apply_scan_result(RecordSupportingFileScan(
                principal=SupportingFileScannerPrincipal(SCANNER_PRINCIPAL_ID),
                asset_id=asset.id, asset_version=asset.version,
                attempt_id=attempt.id, object_fingerprint=asset.content_digest,
                disposition=scan.disposition, engine_id=scan.engine_id,
                signature_set_id=scan.signature_set_id,
                observed_at=scan.scanned_at, correlation_id=scan.correlation_id,
            ), commit=False)
            status = "consumed" if asset.lifecycle == "available" else "failed" if asset.lifecycle == "rejected" else "uploaded"
            self.uow.repository.bind_reservation_asset(reservation, asset, status)
            self._stage_success(actor_id=actor_id, operation="finalize_upload", idempotency_id=idempotency_id, fingerprint=request_fingerprint, asset=asset, now=now, correlation_id=correlation_id)
            self.uow.commit()
            return asset
        except Exception:
            self.uow.rollback()
            raise

    def withdraw(self, *, actor_id: int, scope: SupportingFileScope, asset_id: UUID, expected_version: int, rationale: str, correlation_id: UUID, idempotency_id: UUID, request_fingerprint: str, now: datetime | None = None) -> SupportingFileAsset:
        now = now or datetime.now(timezone.utc)
        SupportingFileMetadata(
            SupportingFileActor(actor_id, scope.organization_id),
            correlation_id, idempotency_id, rationale,
        )
        self.authorization.require_read(actor_id=actor_id, organization_id=scope.organization_id, project_id=scope.project_id, workspace_id=scope.workspace_id)
        asset = self.uow.repository.get_scoped(asset_id, scope.organization_id)
        if asset is None or asset.project_id != scope.project_id or asset.workspace_id != scope.workspace_id:
            raise SupportingFileProtectedNotFound()
        self.authorization.require_withdraw(actor_id=actor_id, organization_id=scope.organization_id, project_id=scope.project_id, workspace_id=scope.workspace_id, uploader_id=asset.uploader_id)
        asset.withdraw(expected_version, actor_id, now, "human_withdrawal")
        if not self.uow.repository.persist_expected_version(asset, expected_version):
            self.uow.rollback(); raise SupportingFileIntegrityError("concurrent asset transition")
        self._stage_success(actor_id=actor_id, operation="withdraw", idempotency_id=idempotency_id, fingerprint=request_fingerprint, asset=asset, now=now, correlation_id=correlation_id)
        self.uow.commit()
        return asset

    def get_metadata(self, *, actor_id: int, scope: SupportingFileScope, asset_id: UUID) -> SupportingFileAsset:
        self.authorization.require_read(actor_id=actor_id, organization_id=scope.organization_id, project_id=scope.project_id, workspace_id=scope.workspace_id)
        asset = self.uow.repository.get_scoped(asset_id, scope.organization_id)
        if asset is None or asset.project_id != scope.project_id or asset.workspace_id not in {None, scope.workspace_id}:
            raise SupportingFileProtectedNotFound()
        return asset

    def list_metadata(self, *, actor_id: int, scope: SupportingFileScope, lifecycle: str | None, limit: int, continuation: str | None, now: datetime | None = None):
        if not 1 <= limit <= 50:
            raise SupportingFileValidationError("list limit is invalid")
        self.authorization.require_read(actor_id=actor_id, organization_id=scope.organization_id, project_id=scope.project_id, workspace_id=scope.workspace_id)
        now = now or datetime.now(timezone.utc)
        anchor = self._decode_continuation(actor_id, scope, lifecycle, limit, continuation, now)
        candidates = self.uow.repository.list_candidates(
            organization_id=scope.organization_id, project_id=scope.project_id,
            workspace_id=scope.workspace_id, lifecycle=lifecycle,
            anchor=anchor, limit=limit + 1,
        )
        visible = tuple(candidates[:limit])
        token = None
        if len(candidates) > limit and visible:
            last = visible[-1]
            token = self._encode_continuation(
                actor_id, scope, lifecycle, limit,
                (last.uploaded_at, last.id), now,
            )
        return visible, token

    def open_active(self, *, actor_id: int, scope: SupportingFileScope, asset_id: UUID):
        asset = self.get_metadata(actor_id=actor_id, scope=scope, asset_id=asset_id)
        if asset.lifecycle != "available":
            raise SupportingFileProtectedNotFound()
        receipt = self.objects.head_exact(asset.storage_key, asset.object_version)
        if receipt is None or (receipt.byte_size, receipt.sha256) != (asset.byte_size, asset.content_digest):
            raise SupportingFileIntegrityError("canonical object is unavailable")
        return asset, self.objects.open_exact(asset.storage_key, asset.object_version)

    def open_historical(self, *, actor_id: int, scope: SupportingFileScope, basis: SupportingFileHistoricalBasisV1):
        self.authorization.require_read(actor_id=actor_id, organization_id=scope.organization_id, project_id=scope.project_id, workspace_id=scope.workspace_id)
        asset = self.uow.repository.get_scoped(basis.asset_id, scope.organization_id)
        if (
            asset is None or basis.organization_id != scope.organization_id
            or basis.project_id != scope.project_id
            or basis.workspace_id not in {None, scope.workspace_id}
            or asset.id != basis.asset_id or asset.version < basis.asset_version
            or asset.project_id != basis.project_id
            or asset.workspace_id != basis.workspace_id
            or asset.safe_filename != basis.safe_filename
            or asset.media_type != basis.media_type.value
            or asset.byte_size != basis.byte_size
            or asset.content_digest != basis.content_digest
            or asset.object_version == ""
        ):
            raise SupportingFileProtectedNotFound()
        receipt = self.objects.head_exact(asset.storage_key, asset.object_version)
        if receipt is None or (receipt.byte_size, receipt.sha256) != (basis.byte_size, basis.content_digest):
            raise SupportingFileIntegrityError("historical object is unavailable")
        stream = self.objects.open_exact(asset.storage_key, asset.object_version)
        now = datetime.now(timezone.utc)
        try:
            self.uow.repository.stage_audit(
                actor_id=actor_id, asset_id=asset.id,
                action="HISTORICAL_DOWNLOAD", occurred_at=now,
                organization_id=asset.organization_id,
                version=basis.asset_version,
            )
            self.uow.commit()
        except Exception:
            self.uow.rollback()
            raise SupportingFileIntegrityError(
                "historical retrieval audit is unavailable"
            ) from None
        return asset, stream

    @staticmethod
    def _token_key():
        return sha256((settings.SECRET_KEY + ":supporting-file-list:v1").encode()).digest()

    def _encode_continuation(self, actor_id, scope, lifecycle, limit, anchor, now):
        payload = json.dumps({
            "v": "supporting-file-list.v1", "actor": actor_id,
            "organization": str(scope.organization_id), "project": scope.project_id,
            "workspace": scope.workspace_id, "lifecycle": lifecycle, "limit": limit,
            "anchor_at": anchor[0].astimezone(timezone.utc).isoformat(timespec="microseconds"),
            "anchor_id": str(anchor[1]), "expires": int((now + timedelta(minutes=15)).timestamp()),
        }, sort_keys=True, separators=(",", ":")).encode()
        nonce = os.urandom(12)
        return base64.urlsafe_b64encode(nonce + AESGCM(self._token_key()).encrypt(nonce, payload, b"supporting-file-list.v1")).decode().rstrip("=")

    def _decode_continuation(self, actor_id, scope, lifecycle, limit, token, now):
        if token is None:
            return None
        try:
            raw = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
            if base64.urlsafe_b64encode(raw).decode().rstrip("=") != token:
                raise ValueError
            payload = json.loads(AESGCM(self._token_key()).decrypt(raw[:12], raw[12:], b"supporting-file-list.v1"))
            expected = ("supporting-file-list.v1", actor_id, str(scope.organization_id), scope.project_id, scope.workspace_id, lifecycle, limit)
            actual = tuple(payload[name] for name in ("v", "actor", "organization", "project", "workspace", "lifecycle", "limit"))
            if actual != expected or set(payload) != {"v","actor","organization","project","workspace","lifecycle","limit","anchor_at","anchor_id","expires"} or payload["expires"] <= int(now.timestamp()):
                raise ValueError
            timestamp = datetime.fromisoformat(payload["anchor_at"])
            if timestamp.tzinfo is None:
                raise ValueError
            return timestamp, UUID(payload["anchor_id"])
        except Exception:
            raise SupportingFileValidationError("continuation is invalid") from None


class SqlAlchemySupportingFileEvidenceCollaborator:
    """Same-Session canonical lock/read boundary used only by Evidence."""

    def __init__(self, session: Session):
        self.session = session

    def authorize_and_lock_for_evidence(self, *, actor_id: int, organization_id: UUID, project_id: int, workspace_id: int | None, asset_ids: tuple[UUID, ...]):
        if actor_id < 1 or not 1 <= len(asset_ids) <= 10 or len(set(asset_ids)) != len(asset_ids) or asset_ids != tuple(sorted(asset_ids, key=str)):
            raise SupportingFileProtectedNotFound()
        assets = self.session.query(SupportingFileAsset).filter(
            SupportingFileAsset.id.in_(asset_ids),
            SupportingFileAsset.organization_id == organization_id,
        ).order_by(SupportingFileAsset.id).with_for_update().all()
        if len(assets) != len(asset_ids) or any(
            asset.lifecycle != "available" or asset.project_id != project_id
            or asset.workspace_id not in {None, workspace_id}
            for asset in assets
        ):
            raise SupportingFileProtectedNotFound()
        return tuple(_historical_basis(asset) for asset in assets)

    def authorize_historical_for_evidence(
        self, *, actor_id: int, evidence_id: UUID, organization_id: UUID,
        project_id: int, workspace_id: int | None,
        historical: tuple[SupportingFileHistoricalBasisV1, ...],
    ) -> tuple[SupportingFileHistoricalBasisV1, ...]:
        if (
            actor_id < 1 or not 1 <= len(historical) <= 10
            or any(type(item) is not SupportingFileHistoricalBasisV1 for item in historical)
        ):
            raise SupportingFileProtectedNotFound()
        expected_ids = tuple(item.asset_id for item in historical)
        if expected_ids != tuple(sorted(set(expected_ids), key=str)):
            raise SupportingFileProtectedNotFound()
        links = self.session.query(EvidenceSupportingFileLink).filter_by(
            evidence_id=evidence_id,
            organization_id=organization_id,
            project_id=project_id,
            workspace_id=workspace_id,
        ).order_by(EvidenceSupportingFileLink.asset_id).all()
        if tuple(link.asset_id for link in links) != expected_ids:
            raise SupportingFileProtectedNotFound()
        actual = self.authorize_and_lock_for_evidence(
            actor_id=actor_id, organization_id=organization_id,
            project_id=project_id, workspace_id=workspace_id,
            asset_ids=expected_ids,
        )
        if actual != historical:
            raise SupportingFileProtectedNotFound()
        return actual


class SqlAlchemySupportingFileTechnicalReportCollaborator:
    """Resolve exact linked Asset history without Report owning file persistence."""

    def __init__(self, session: Session):
        self.session = session

    def resolve_for_evidence(
        self, *, evidence_id: UUID, organization_id: UUID, project_id: int,
        workspace_id: int | None, lock: bool,
    ) -> tuple[SupportingFileHistoricalBasisV1, ...]:
        links = self.session.query(EvidenceSupportingFileLink).filter_by(
            evidence_id=evidence_id,
            organization_id=organization_id,
            project_id=project_id,
            workspace_id=workspace_id,
        ).order_by(EvidenceSupportingFileLink.asset_id).all()
        if not links:
            return ()
        ids = tuple(link.asset_id for link in links)
        if not 1 <= len(ids) <= 10 or ids != tuple(sorted(set(ids), key=str)):
            raise SupportingFileProtectedNotFound()
        query = self.session.query(SupportingFileAsset).filter(
            SupportingFileAsset.id.in_(ids),
            SupportingFileAsset.organization_id == organization_id,
        ).order_by(SupportingFileAsset.id)
        if lock:
            query = query.with_for_update()
        assets = query.all()
        if len(assets) != len(ids) or any(
            asset.lifecycle != "available" or asset.project_id != project_id
            or asset.workspace_id not in {None, workspace_id}
            for asset in assets
        ):
            raise SupportingFileProtectedNotFound()
        return tuple(_historical_basis(asset) for asset in assets)


def _historical_basis(asset: SupportingFileAsset) -> SupportingFileHistoricalBasisV1:
    return SupportingFileHistoricalBasisV1(
        1, "supporting_file", asset.id, asset.version,
        asset.organization_id, asset.project_id, asset.workspace_id,
        asset.safe_filename, asset.media_type, asset.byte_size,
        asset.digest_algorithm, asset.content_digest, asset.uploader_id,
        asset.uploaded_at, asset.predecessor_asset_id,
    )
