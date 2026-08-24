from app.models.audit_log import AuditLog
from app.repositories.engineering_deliverable_repository import EngineeringDeliverableRepository


class SqlAlchemyEngineeringDeliverableUnitOfWork:
    def __init__(self, session): self.session=session; self.repository=EngineeringDeliverableRepository(session)
    def __enter__(self): return self
    def __exit__(self, kind, value, traceback):
        if kind is not None: self.rollback()
    def stage_audit(self, *, actor_id, project_id, operation, details):
        self.session.add(AuditLog(user_id=actor_id, action=operation, entity="ENGINEERING_DELIVERABLE", entity_id=project_id, details=details))
    def commit(self): self.session.commit()
    def rollback(self): self.session.rollback()
