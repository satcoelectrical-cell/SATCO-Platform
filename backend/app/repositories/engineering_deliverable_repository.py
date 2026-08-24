from sqlalchemy.orm import Session

from app.models.engineering_deliverable import EngineeringDeliverable, EngineeringDeliverableRevision, EngineeringDeliverableIdempotency


class EngineeringDeliverableRepository:
    """No-commit persistence boundary for deliverable control."""
    def __init__(self, session: Session): self.session = session
    def get(self, *, deliverable_id, organization_id, lock=False):
        query = self.session.query(EngineeringDeliverable).filter_by(id=deliverable_id, organization_id=organization_id)
        return (query.with_for_update() if lock else query).first()
    def get_current_revision(self, *, deliverable, lock=False):
        query = self.session.query(EngineeringDeliverableRevision).filter_by(deliverable_id=deliverable.id, sequence=deliverable.current_revision_sequence)
        return (query.with_for_update() if lock else query).first()
    def list(self, *, organization_id, project_id, limit=100):
        return self.session.query(EngineeringDeliverable).filter_by(organization_id=organization_id, project_id=project_id).order_by(EngineeringDeliverable.target_date.asc().nullslast(), EngineeringDeliverable.code, EngineeringDeliverable.id).limit(limit).all()
    def revisions(self, *, deliverable_id):
        return self.session.query(EngineeringDeliverableRevision).filter_by(deliverable_id=deliverable_id).order_by(EngineeringDeliverableRevision.sequence).all()
    def get_idempotency(self, *, organization_id, actor_id, operation, idempotency_key, lock=True):
        query = self.session.query(EngineeringDeliverableIdempotency).filter_by(organization_id=organization_id, actor_id=actor_id, operation=operation, idempotency_key=idempotency_key)
        return (query.with_for_update() if lock else query).first()
    def add(self, value): self.session.add(value)
    def flush(self): self.session.flush()
