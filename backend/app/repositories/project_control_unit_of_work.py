from app.repositories.project_control_repository import ProjectControlRepository
from app.models.audit_log import AuditLog
class SqlAlchemyProjectControlUnitOfWork:
    def __init__(self,session): self.session=session; self.repository=ProjectControlRepository(session)
    def __enter__(self): return self
    def __exit__(self,exc_type,*_):
        if exc_type is not None: self.rollback()
        self.session.close()
    def stage_audit(self,*,actor_id,project_id,operation,control_id,details):
        self.session.add(AuditLog(user_id=actor_id,action=operation,entity="PROJECT_CONTROL",entity_id=project_id,entity_uuid=control_id,details=details))
    def stage_idempotency(self,record): self.session.add(record)
    def stage_outbox(self,record): self.session.add(record)
    def commit(self): self.session.commit()
    def rollback(self): self.session.rollback()
