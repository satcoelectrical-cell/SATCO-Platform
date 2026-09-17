"""Scoped PATCH-055 retention persistence queries; never commits."""
from sqlalchemy import select, update

from app.enums.retention import RetentionSubjectKind
from app.models.evidence import Evidence
from app.models.retention import (
    RetentionDispositionDecision,
    RetentionHold,
    RetentionExport,
    RetentionExportSubject,
    RetentionIdempotency,
    RetentionRecord,
    RetentionRecovery,
)
from app.models.retention_command import RetentionSubject
from app.models.supporting_file import SupportingFileAsset
from app.models.technical_report import TechnicalReportProvenanceRecord, TechnicalReportRecord


class SqlAlchemyRetentionRepository:
    def __init__(self, session):
        self.session = session

    def resolve_subject(self, *, organization_id, subject_kind, subject_id, lock=False):
        kind = RetentionSubjectKind(subject_kind)
        model = Evidence if kind is RetentionSubjectKind.EVIDENCE else SupportingFileAsset
        stmt = select(model).where(model.id == subject_id, model.organization_id == organization_id)
        row = self.session.scalar(stmt.with_for_update() if lock else stmt)
        if row is None or row.project_id is None:
            return None
        subject = RetentionSubject(kind, row.id, row.organization_id, row.project_id, row.workspace_id)
        return subject, int(row.version)

    def get_current_record(self, *, subject, lock=False):
        stmt = select(RetentionRecord).where(
            RetentionRecord.organization_id == subject.organization_id,
            RetentionRecord.subject_kind == subject.subject_kind.value,
            RetentionRecord.subject_id == subject.subject_id,
            RetentionRecord.is_current.is_(True),
        )
        return self.session.scalar(stmt.with_for_update() if lock else stmt)

    def get_record_by_id(self, *, subject, record_id):
        stmt = select(RetentionRecord).where(
            RetentionRecord.id == record_id,
            RetentionRecord.organization_id == subject.organization_id,
            RetentionRecord.project_id == subject.project_id,
            RetentionRecord.subject_kind == subject.subject_kind.value,
            RetentionRecord.subject_id == subject.subject_id,
        )
        if subject.workspace_id is None:
            stmt = stmt.where(RetentionRecord.workspace_id.is_(None))
        else:
            stmt = stmt.where(
                RetentionRecord.workspace_id == subject.workspace_id
            )
        return self.session.scalar(stmt)

    def get_active_hold(self, *, subject, lock=False):
        stmt = select(RetentionHold).where(
            RetentionHold.organization_id == subject.organization_id,
            RetentionHold.subject_kind == subject.subject_kind.value,
            RetentionHold.subject_id == subject.subject_id,
            RetentionHold.is_current.is_(True),
            RetentionHold.status == "active",
        )
        return self.session.scalar(stmt.with_for_update() if lock else stmt)

    def get_hold_revision(self, *, subject, hold_id, version):
        stmt = select(RetentionHold).where(
            RetentionHold.hold_id == hold_id,
            RetentionHold.version == version,
            RetentionHold.organization_id == subject.organization_id,
            RetentionHold.project_id == subject.project_id,
            RetentionHold.subject_kind == subject.subject_kind.value,
            RetentionHold.subject_id == subject.subject_id,
        )
        if subject.workspace_id is None:
            stmt = stmt.where(RetentionHold.workspace_id.is_(None))
        else:
            stmt = stmt.where(
                RetentionHold.workspace_id == subject.workspace_id
            )
        return self.session.scalar(stmt)

    def get_latest_hold(self, *, subject):
        stmt = select(RetentionHold).where(
            RetentionHold.organization_id == subject.organization_id,
            RetentionHold.subject_kind == subject.subject_kind.value,
            RetentionHold.subject_id == subject.subject_id,
            RetentionHold.is_current.is_(True),
        ).order_by(RetentionHold.placed_at.desc(), RetentionHold.version.desc())
        return self.session.scalars(stmt).first()

    def get_latest_decision(self, *, retention_record_id):
        stmt = select(RetentionDispositionDecision).where(
            RetentionDispositionDecision.retention_record_id == retention_record_id,
        ).order_by(RetentionDispositionDecision.decided_at.desc(), RetentionDispositionDecision.id.desc())
        return self.session.scalars(stmt).first()

    def get_decision_by_request_digest(self, *, retention_record_id, request_digest):
        stmt = select(RetentionDispositionDecision).where(
            RetentionDispositionDecision.retention_record_id == retention_record_id,
            RetentionDispositionDecision.request_digest == request_digest,
        ).order_by(RetentionDispositionDecision.decided_at.desc(), RetentionDispositionDecision.id.desc())
        return self.session.scalars(stmt).first()

    def close_current_record(self, *, record_id, expected_version):
        result = self.session.execute(update(RetentionRecord).where(
            RetentionRecord.id == record_id,
            RetentionRecord.version == expected_version,
            RetentionRecord.is_current.is_(True),
        ).values(is_current=False))
        return result.rowcount == 1

    def close_hold_revision(self, *, row_id, expected_version):
        result = self.session.execute(update(RetentionHold).where(
            RetentionHold.row_id == row_id,
            RetentionHold.version == expected_version,
            RetentionHold.is_current.is_(True),
        ).values(is_current=False))
        return result.rowcount == 1

    def get_supporting_file_asset(self, *, subject, lock=False):
        if subject.subject_kind is not RetentionSubjectKind.SUPPORTING_FILE:
            return None
        stmt = select(SupportingFileAsset).where(
            SupportingFileAsset.id == subject.subject_id,
            SupportingFileAsset.organization_id == subject.organization_id,
            SupportingFileAsset.project_id == subject.project_id,
        )
        if subject.workspace_id is None:
            stmt = stmt.where(SupportingFileAsset.workspace_id.is_(None))
        else:
            stmt = stmt.where(SupportingFileAsset.workspace_id == subject.workspace_id)
        return self.session.scalar(stmt.with_for_update() if lock else stmt)

    def get_export(self, *, organization_id, export_id, lock=False):
        stmt = select(RetentionExport).where(
            RetentionExport.id == export_id,
            RetentionExport.organization_id == organization_id,
        )
        return self.session.scalar(stmt.with_for_update() if lock else stmt)

    def list_export_subjects(self, *, export_id):
        stmt = select(RetentionExportSubject).where(
            RetentionExportSubject.export_id == export_id,
        ).order_by(RetentionExportSubject.ordinal.asc())
        return tuple(self.session.scalars(stmt).all())

    def get_recovery(self, *, organization_id, recovery_id, lock=False):
        stmt = select(RetentionRecovery).where(
            RetentionRecovery.id == recovery_id,
            RetentionRecovery.organization_id == organization_id,
        )
        return self.session.scalar(stmt.with_for_update() if lock else stmt)

    def get_idempotency(self, *, organization_id, actor_id, operation, idempotency_key, lock=False):
        stmt = select(RetentionIdempotency).where(
            RetentionIdempotency.organization_id == organization_id,
            RetentionIdempotency.actor_user_id == actor_id,
            RetentionIdempotency.operation == operation,
            RetentionIdempotency.idempotency_key == idempotency_key,
        )
        return self.session.scalar(stmt.with_for_update() if lock else stmt)

    def add(self, row):
        self.session.add(row)

    def flush(self):
        self.session.flush()

    def list_workbench_evidence(self, *, organization_id, project_id, workspace_id, limit):
        stmt = select(Evidence).where(Evidence.organization_id == organization_id, Evidence.project_id == project_id)
        if workspace_id is not None: stmt = stmt.where(Evidence.workspace_id == workspace_id)
        return list(self.session.scalars(stmt.order_by(Evidence.created_at.desc(), Evidence.id).limit(limit)))

    def get_workbench_replacement(self, *, organization_id, project_id, workspace_id, replacement_evidence_id):
        if replacement_evidence_id is None: return None
        stmt = select(Evidence).where(Evidence.id == replacement_evidence_id, Evidence.organization_id == organization_id, Evidence.project_id == project_id)
        if workspace_id is not None: stmt = stmt.where(Evidence.workspace_id == workspace_id)
        return self.session.scalar(stmt)

    def list_workbench_predecessors(self, *, organization_id, project_id, workspace_id, evidence_id, limit=32):
        stmt = select(Evidence).where(Evidence.organization_id == organization_id, Evidence.project_id == project_id, Evidence.replacement_evidence_id == evidence_id)
        if workspace_id is not None: stmt = stmt.where(Evidence.workspace_id == workspace_id)
        return list(self.session.scalars(stmt.order_by(Evidence.updated_at, Evidence.id).limit(limit)))

    def list_workbench_files(self, *, organization_id, project_id, workspace_id, limit):
        stmt = select(SupportingFileAsset).where(SupportingFileAsset.organization_id == organization_id, SupportingFileAsset.project_id == project_id, SupportingFileAsset.lifecycle == "available")
        if workspace_id is not None: stmt = stmt.where(SupportingFileAsset.workspace_id.in_([None, workspace_id]))
        return list(self.session.scalars(stmt.order_by(SupportingFileAsset.uploaded_at.desc(), SupportingFileAsset.id).limit(limit)))

    def list_accepted_report_reliance(self, *, organization_id, project_id, workspace_id, evidence_id, limit=32):
        stmt = (select(TechnicalReportProvenanceRecord, TechnicalReportRecord)
            .join(TechnicalReportRecord, TechnicalReportRecord.id == TechnicalReportProvenanceRecord.technical_report_id)
            .where(TechnicalReportProvenanceRecord.evidence_id == evidence_id, TechnicalReportRecord.organization_id == organization_id, TechnicalReportRecord.project_id == project_id, TechnicalReportRecord.lifecycle == "accepted"))
        if workspace_id is not None: stmt = stmt.where(TechnicalReportRecord.workspace_id == workspace_id)
        return list(self.session.execute(stmt.order_by(TechnicalReportRecord.accepted_at, TechnicalReportRecord.id).limit(limit)).all())
