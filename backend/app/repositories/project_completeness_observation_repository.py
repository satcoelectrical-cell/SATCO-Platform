"""Storage only for prospective Project Completeness owner observations."""

from uuid import uuid4

from sqlalchemy.dialects.postgresql import insert

from app.models.project_completeness_observation import ProjectCompletenessObservation


class ProjectCompletenessObservationRepository:
    def __init__(self, db):
        self.db = db

    def record_once(self, values: dict):
        statement = insert(ProjectCompletenessObservation).values(id=uuid4(), **values)
        self.db.execute(statement.on_conflict_do_nothing())
        self.db.commit()
        return self.db.query(ProjectCompletenessObservation).filter(
            ProjectCompletenessObservation.organization_id == values["organization_id"],
            ProjectCompletenessObservation.project_id == values["project_id"],
            ProjectCompletenessObservation.workspace_id.is_(None)
            if values["workspace_id"] is None else
            ProjectCompletenessObservation.workspace_id == values["workspace_id"],
            ProjectCompletenessObservation.actor_id == values["actor_id"],
            ProjectCompletenessObservation.method_version == values["method_version"],
            ProjectCompletenessObservation.catalog_digest == values["catalog_digest"],
            ProjectCompletenessObservation.source_digest == values["source_digest"],
        ).one()

    def list_history(self, *, organization_id, project_id, workspace_id, actor_id,
                     after_cutoff, before_cutoff, limit=1001):
        return self.db.query(ProjectCompletenessObservation).filter(
            ProjectCompletenessObservation.organization_id == organization_id,
            ProjectCompletenessObservation.project_id == project_id,
            ProjectCompletenessObservation.workspace_id.is_(None)
            if workspace_id is None else
            ProjectCompletenessObservation.workspace_id == workspace_id,
            ProjectCompletenessObservation.actor_id == actor_id,
            ProjectCompletenessObservation.source_cutoff >= after_cutoff,
            ProjectCompletenessObservation.source_cutoff <= before_cutoff,
        ).order_by(
            ProjectCompletenessObservation.source_cutoff,
            ProjectCompletenessObservation.id,
        ).limit(limit).all()
