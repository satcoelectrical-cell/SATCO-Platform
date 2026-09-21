"""Derived-only PATCH-056 snapshot and next-action persistence."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.engineering_performance import (
    EngineeringNextActionProjection, EngineeringPerformanceSnapshot,
)


class EngineeringPerformanceRepository:
    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def _workspace(query, column, workspace_id):
        return query.filter(column.is_(None) if workspace_id is None else column == workspace_id)

    def find_snapshot(self, *, organization_id, project_id, workspace_id,
                      actor_id, indicator_id, indicator_version, window_start,
                      window_end, source_digest, calculation_version):
        query = self.session.query(EngineeringPerformanceSnapshot).filter_by(
            organization_id=organization_id, project_id=project_id,
            actor_id=actor_id, indicator_id=indicator_id,
            indicator_version=indicator_version, window_start=window_start,
            window_end=window_end, source_digest=source_digest,
            calculation_version=calculation_version,
        )
        return self._workspace(query, EngineeringPerformanceSnapshot.workspace_id,
                               workspace_id).one_or_none()

    def add_snapshot(self, row):
        self.session.add(row)
        self.session.flush()

    def list_snapshots(self, *, organization_id, project_id, workspace_id,
                       actor_id, after: datetime, indicator_id: str | None,
                       limit: int):
        query = self.session.query(EngineeringPerformanceSnapshot).filter(
            EngineeringPerformanceSnapshot.organization_id == organization_id,
            EngineeringPerformanceSnapshot.project_id == project_id,
            EngineeringPerformanceSnapshot.actor_id == actor_id,
            EngineeringPerformanceSnapshot.observed_at >= after,
        )
        query = self._workspace(query, EngineeringPerformanceSnapshot.workspace_id,
                                workspace_id)
        if indicator_id is not None:
            query = query.filter(EngineeringPerformanceSnapshot.indicator_id == indicator_id)
        return query.order_by(
            EngineeringPerformanceSnapshot.observed_at,
            EngineeringPerformanceSnapshot.indicator_id,
            EngineeringPerformanceSnapshot.id,
        ).limit(limit).all()

    def get_snapshot(self, *, snapshot_id: UUID, organization_id, project_id,
                     workspace_id, actor_id):
        query = self.session.query(EngineeringPerformanceSnapshot).filter_by(
            id=snapshot_id, organization_id=organization_id,
            project_id=project_id, actor_id=actor_id,
        )
        return self._workspace(query, EngineeringPerformanceSnapshot.workspace_id,
                               workspace_id).one_or_none()

    def list_actions(self, *, organization_id, project_id, workspace_id,
                     actor_id, lock: bool = False):
        query = self.session.query(EngineeringNextActionProjection).filter_by(
            organization_id=organization_id, project_id=project_id,
            actor_id=actor_id,
        )
        query = self._workspace(query, EngineeringNextActionProjection.workspace_id,
                                workspace_id)
        if lock:
            query = query.with_for_update()
        return query.order_by(
            EngineeringNextActionProjection.first_seen_at,
            EngineeringNextActionProjection.action_key,
        ).all()

    def add_action(self, row):
        self.session.add(row)
        self.session.flush()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
