"""Supporting File persistence without transaction or policy ownership."""
from uuid import UUID
from sqlalchemy import and_, or_, update
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.models.supporting_file import SupportingFileAsset, SupportingFileUploadReservation, SupportingFileIdempotencyRecord, SupportingFileOutboxRecord, SupportingFileScanAttempt


class SqlAlchemySupportingFileRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, asset: SupportingFileAsset) -> None:
        self.session.add(asset)
        self.session.flush()

    def get_scoped(self, asset_id: UUID, organization_id: UUID):
        return self.session.query(SupportingFileAsset).filter_by(id=asset_id, organization_id=organization_id).first()

    def list_scoped(self, *, organization_id: UUID, project_id: int, workspace_id: int | None, lifecycle: str | None, limit: int):
        query = self.session.query(SupportingFileAsset).filter_by(organization_id=organization_id, project_id=project_id)
        if workspace_id is not None:
            query = query.filter(SupportingFileAsset.workspace_id == workspace_id)
        if lifecycle is not None:
            query = query.filter(SupportingFileAsset.lifecycle == lifecycle)
        return query.order_by(SupportingFileAsset.uploaded_at.desc(), SupportingFileAsset.id.asc()).limit(limit).all()

    def list_candidates(self, *, organization_id: UUID, project_id: int, workspace_id: int | None, lifecycle: str | None, anchor, limit: int):
        query = self.session.query(SupportingFileAsset).filter(
            SupportingFileAsset.organization_id == organization_id,
            SupportingFileAsset.project_id == project_id,
        )
        if workspace_id is not None:
            query = query.filter(
                or_(SupportingFileAsset.workspace_id.is_(None),
                    SupportingFileAsset.workspace_id == workspace_id)
            )
        if lifecycle is not None:
            query = query.filter(SupportingFileAsset.lifecycle == lifecycle)
        if anchor is not None:
            uploaded_at, asset_id = anchor
            query = query.filter(or_(
                SupportingFileAsset.uploaded_at < uploaded_at,
                and_(SupportingFileAsset.uploaded_at == uploaded_at,
                     SupportingFileAsset.id > asset_id),
            ))
        return query.order_by(
            SupportingFileAsset.uploaded_at.desc(), SupportingFileAsset.id.asc()
        ).limit(limit).all()

    def persist_expected_version(self, asset: SupportingFileAsset, expected_version: int) -> bool:
        values = dict(lifecycle=asset.lifecycle, version=asset.version, scanned_at=asset.scanned_at, withdrawn_at=asset.withdrawn_at, withdrawn_by_id=asset.withdrawn_by_id, withdrawal_reason_code=asset.withdrawal_reason_code, updated_at=asset.updated_at)
        with self.session.no_autoflush:
            result = self.session.execute(
                update(SupportingFileAsset)
                .where(SupportingFileAsset.id == asset.id, SupportingFileAsset.version == expected_version)
                .values(**values)
                .execution_options(synchronize_session=False)
            )
        if result.rowcount == 1:
            self.session.expire(asset)
        self.session.flush()
        return result.rowcount == 1

    def add_reservation(self, reservation: SupportingFileUploadReservation) -> None:
        self.session.add(reservation)
        self.session.flush()

    def get_reservation(self, reservation_id: UUID, organization_id: UUID) -> SupportingFileUploadReservation | None:
        return self.session.query(SupportingFileUploadReservation).filter_by(
            id=reservation_id, organization_id=organization_id,
        ).first()

    def bind_reservation_asset(self, reservation: SupportingFileUploadReservation, asset: SupportingFileAsset, status: str) -> None:
        reservation.asset_id = asset.id
        reservation.status = status
        self.session.flush()

    def get_idempotency(self, *, organization_id: UUID, actor_id: int, operation: str, idempotency_id: UUID) -> SupportingFileIdempotencyRecord | None:
        return self.session.query(SupportingFileIdempotencyRecord).filter_by(organization_id=organization_id, actor_id=actor_id, operation=operation, idempotency_id=idempotency_id).first()

    def stage_idempotency(self, record: SupportingFileIdempotencyRecord) -> None:
        self.session.add(record); self.session.flush()

    def next_scan_attempt_number(self, *, asset_id: UUID) -> int:
        latest = self.session.query(SupportingFileScanAttempt.attempt_number).filter_by(asset_id=asset_id).order_by(SupportingFileScanAttempt.attempt_number.desc()).first()
        return 1 if latest is None else latest[0] + 1

    def get_scan_attempt(self, *, attempt_id: UUID, for_update: bool = False):
        query = self.session.query(SupportingFileScanAttempt).filter_by(id=attempt_id)
        if for_update:
            query = query.with_for_update()
        return query.first()

    def get_latest_scan_attempt(self, *, asset_id: UUID, for_update: bool = False):
        query = self.session.query(SupportingFileScanAttempt).filter_by(asset_id=asset_id).order_by(SupportingFileScanAttempt.attempt_number.desc())
        if for_update:
            query = query.with_for_update()
        return query.first()

    def stage_scan_attempt(self, record: SupportingFileScanAttempt) -> None:
        self.session.add(record); self.session.flush()

    def complete_scan_attempt(self, record: SupportingFileScanAttempt, *, disposition: str | None, completed_at, failed: bool = False, engine_id: str | None = None, signature_set_id: str | None = None, correlation_id: UUID | None = None) -> None:
        record.state = "failed" if failed else "completed"
        record.disposition = disposition
        record.engine_id = engine_id
        record.signature_set_id = signature_set_id
        record.correlation_id = correlation_id
        record.completed_at = completed_at
        self.session.flush()

    def stage_outbox(self, record: SupportingFileOutboxRecord) -> None:
        self.session.add(record); self.session.flush()

    def stage_audit(self, *, actor_id: int | None, asset_id: UUID, action: str, occurred_at, organization_id: UUID, version: int, principal_id: str | None = None, correlation_id: UUID | None = None) -> None:
        self.session.add(AuditLog(user_id=actor_id, action=action, entity="SUPPORTING_FILE", entity_uuid=asset_id,
                                  details={"organization_id": str(organization_id), "version": version,
                                           **({"principal_id": principal_id} if principal_id else {}),
                                           **({"correlation_id": str(correlation_id)} if correlation_id else {})},
                                  created_at=occurred_at))
        self.session.flush()
