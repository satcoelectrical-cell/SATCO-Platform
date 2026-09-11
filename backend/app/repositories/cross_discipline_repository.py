"""Scoped PATCH-053 persistence queries. This repository never commits."""

from sqlalchemy import and_, func, or_, select, update

from app.models.cross_discipline_intelligence import (
    CrossDisciplineAssessment, CrossDisciplineDisposition,
    CrossDisciplineFinding, CrossDisciplineFindingCurrent,
    CrossDisciplineIdempotency, CrossDisciplineLineage,
    CrossDisciplineSnapshot, CrossDisciplineAssessmentWorkspace,
)


class CrossDisciplineRepository:
    def __init__(self, session):
        self.session = session

    def get_assessment(self, assessment_id, organization_id, project_id, *, lock=False):
        stmt = select(CrossDisciplineAssessment).where(
            CrossDisciplineAssessment.id == assessment_id,
            CrossDisciplineAssessment.organization_id == organization_id,
            CrossDisciplineAssessment.project_id == project_id,
        )
        return self.session.scalar(stmt.with_for_update() if lock else stmt)

    def list_assessments(self, *, organization_id, project_id, limit, before=None):
        stmt = select(CrossDisciplineAssessment).where(
            CrossDisciplineAssessment.organization_id == organization_id,
            CrossDisciplineAssessment.project_id == project_id,
        )
        if before is not None:
            completed_at, identity = before
            stmt = stmt.where(or_(
                CrossDisciplineAssessment.completed_at < completed_at,
                and_(CrossDisciplineAssessment.completed_at == completed_at, CrossDisciplineAssessment.id < identity),
            ))
        return tuple(self.session.scalars(stmt.order_by(
            CrossDisciplineAssessment.completed_at.desc(),
            CrossDisciplineAssessment.id.desc(),
        ).limit(limit + 1)))

    def snapshot(self, *, assessment_id, organization_id, project_id):
        return self.session.scalar(select(CrossDisciplineSnapshot).where(
            CrossDisciplineSnapshot.assessment_id == assessment_id,
            CrossDisciplineSnapshot.organization_id == organization_id,
            CrossDisciplineSnapshot.project_id == project_id,
        ))

    def assessment_workspace_ids(self, *, assessment_id, organization_id, project_id):
        return tuple(self.session.scalars(select(
            CrossDisciplineAssessmentWorkspace.workspace_id,
        ).where(
            CrossDisciplineAssessmentWorkspace.assessment_id == assessment_id,
            CrossDisciplineAssessmentWorkspace.organization_id == organization_id,
            CrossDisciplineAssessmentWorkspace.project_id == project_id,
        ).order_by(CrossDisciplineAssessmentWorkspace.workspace_id)))

    def next_disposition_sequence(self, assessment_id):
        return int(self.session.scalar(select(
            func.coalesce(func.max(CrossDisciplineDisposition.sequence), 0) + 1,
        ).where(CrossDisciplineDisposition.assessment_id == assessment_id)))

    def findings(self, *, assessment_id, organization_id, project_id, limit=100, after_ordinal=None):
        stmt = select(CrossDisciplineFinding).where(
            CrossDisciplineFinding.assessment_id == assessment_id,
            CrossDisciplineFinding.organization_id == organization_id,
            CrossDisciplineFinding.project_id == project_id,
        )
        if after_ordinal is not None:
            stmt = stmt.where(CrossDisciplineFinding.ordinal > after_ordinal)
        return tuple(self.session.scalars(stmt.order_by(CrossDisciplineFinding.ordinal).limit(limit + 1)))

    def finding(self, *, assessment_id, finding_id, organization_id, project_id, lock=False):
        stmt = select(CrossDisciplineFinding).where(
            CrossDisciplineFinding.id == finding_id,
            CrossDisciplineFinding.assessment_id == assessment_id,
            CrossDisciplineFinding.organization_id == organization_id,
            CrossDisciplineFinding.project_id == project_id,
        )
        return self.session.scalar(stmt.with_for_update() if lock else stmt)

    def current_view(self, *, assessment_id, finding_id, organization_id, project_id, lock=False):
        stmt = select(CrossDisciplineFindingCurrent).where(
            CrossDisciplineFindingCurrent.finding_id == finding_id,
            CrossDisciplineFindingCurrent.assessment_id == assessment_id,
            CrossDisciplineFindingCurrent.organization_id == organization_id,
            CrossDisciplineFindingCurrent.project_id == project_id,
        )
        return self.session.scalar(stmt.with_for_update() if lock else stmt)

    def dispositions(self, *, assessment_id, finding_id, organization_id, project_id, limit=100, after_sequence=None):
        stmt = select(CrossDisciplineDisposition).where(
            CrossDisciplineDisposition.assessment_id == assessment_id,
            CrossDisciplineDisposition.finding_id == finding_id,
            CrossDisciplineDisposition.organization_id == organization_id,
            CrossDisciplineDisposition.project_id == project_id,
        )
        if after_sequence is not None:
            stmt = stmt.where(CrossDisciplineDisposition.sequence > after_sequence)
        return tuple(self.session.scalars(stmt.order_by(CrossDisciplineDisposition.sequence).limit(limit + 1)))

    def lineage(self, *, assessment_id, organization_id, project_id, direction, limit=100):
        column = CrossDisciplineLineage.predecessor_id if direction == "successors" else CrossDisciplineLineage.successor_id
        return tuple(self.session.scalars(select(CrossDisciplineLineage).where(
            column == assessment_id,
            CrossDisciplineLineage.organization_id == organization_id,
            CrossDisciplineLineage.project_id == project_id,
        ).order_by(CrossDisciplineLineage.created_at, CrossDisciplineLineage.id).limit(limit + 1)))

    def lineage_edges(self, *, organization_id, project_id):
        return tuple(self.session.execute(select(
            CrossDisciplineLineage.predecessor_id,
            CrossDisciplineLineage.successor_id,
        ).where(
            CrossDisciplineLineage.organization_id == organization_id,
            CrossDisciplineLineage.project_id == project_id,
        )).tuples())

    def get_idempotency(self, *, organization_id, project_id, actor_id, operation, idempotency_key, lock=False):
        stmt = select(CrossDisciplineIdempotency).where(
            CrossDisciplineIdempotency.organization_id == organization_id,
            CrossDisciplineIdempotency.project_id == project_id,
            CrossDisciplineIdempotency.actor_id == actor_id,
            CrossDisciplineIdempotency.operation == operation,
            CrossDisciplineIdempotency.idempotency_key == idempotency_key,
        )
        return self.session.scalar(stmt.with_for_update() if lock else stmt)

    def handoff_by_key(self, *, handoff_key, organization_id, project_id, lock=False):
        stmt = select(CrossDisciplineIdempotency).where(
            CrossDisciplineIdempotency.handoff_key == handoff_key,
            CrossDisciplineIdempotency.organization_id == organization_id,
            CrossDisciplineIdempotency.project_id == project_id,
        )
        return self.session.scalar(stmt.with_for_update() if lock else stmt)

    def increment_root_version(self, *, assessment_id, organization_id, project_id, expected_version):
        result = self.session.execute(update(CrossDisciplineAssessment).where(
            CrossDisciplineAssessment.id == assessment_id,
            CrossDisciplineAssessment.organization_id == organization_id,
            CrossDisciplineAssessment.project_id == project_id,
            CrossDisciplineAssessment.aggregate_version == expected_version,
        ).values(aggregate_version=expected_version + 1))
        return result.rowcount == 1

    def add(self, row):
        self.session.add(row)

    def flush(self):
        self.session.flush()
