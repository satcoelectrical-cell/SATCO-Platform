"""Tenant-bounded persistence operations for Document Intelligence."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.document_intelligence import (
    CandidateSourceLocatorLink,
    DocumentAnalysisRun,
    DocumentEngineeringCandidate,
    DocumentIntelligenceIdempotency,
    DocumentPromotionReceipt,
    SourceLocatorRecord,
)


class DocumentIntelligenceRepository:
    def __init__(self, session: Session):
        self.session = session

    def add_run(self, run: DocumentAnalysisRun) -> None:
        self.session.add(run)

    def get_run(self, *, run_id: UUID, organization_id: UUID):
        return self.session.query(DocumentAnalysisRun).filter_by(
            id=run_id, organization_id=organization_id,
        ).first()

    def list_runs(self, *, organization_id: UUID, project_id: int,
                  workspace_id: int | None):
        query = self.session.query(DocumentAnalysisRun).filter_by(
            organization_id=organization_id, project_id=project_id,
        )
        if workspace_id is not None:
            query = query.filter(DocumentAnalysisRun.workspace_id == workspace_id)
        return query.order_by(
            DocumentAnalysisRun.created_at.desc(), DocumentAnalysisRun.id.desc()
        ).all()

    def idempotency(self, *, organization_id: UUID, actor_id: int,
                    operation: str, idempotency_id: UUID):
        return self.session.query(DocumentIntelligenceIdempotency).filter_by(
            organization_id=organization_id, actor_id=actor_id,
            operation=operation, idempotency_id=idempotency_id,
        ).first()

    def list_candidates(self, *, run_id: UUID):
        return self.session.query(DocumentEngineeringCandidate).filter_by(
            analysis_run_id=run_id,
        ).order_by(DocumentEngineeringCandidate.ordinal.asc()).all()

    def get_candidate(self, *, candidate_id: UUID, run_id: UUID,
                      for_update: bool = False):
        query = self.session.query(DocumentEngineeringCandidate).filter_by(
            id=candidate_id, analysis_run_id=run_id,
        )
        if for_update:
            query = query.with_for_update()
        return query.first()

    def candidate_locators(self, *, candidate_ids: tuple[UUID, ...]):
        if not candidate_ids:
            return []
        return self.session.query(
            CandidateSourceLocatorLink, SourceLocatorRecord,
        ).join(
            SourceLocatorRecord,
            SourceLocatorRecord.id == CandidateSourceLocatorLink.source_locator_id,
        ).filter(
            CandidateSourceLocatorLink.candidate_id.in_(candidate_ids),
        ).order_by(
            CandidateSourceLocatorLink.candidate_id.asc(),
            CandidateSourceLocatorLink.ordinal.asc(),
        ).all()

    def promotion_receipt(self, *, candidate_id: UUID, candidate_version: int):
        return self.session.query(DocumentPromotionReceipt).filter_by(
            candidate_id=candidate_id, candidate_version=candidate_version,
        ).first()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
