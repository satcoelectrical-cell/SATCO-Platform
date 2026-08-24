from app.models.audit_log import AuditLog
from app.repositories.engineering_execution_plan_repository import EngineeringExecutionPlanRepository


class SqlAlchemyEngineeringExecutionPlanUnitOfWork:
    def __init__(self, session):
        self.session = session
        self.repository = EngineeringExecutionPlanRepository(session)

    def __enter__(self): return self
    def __exit__(self, exc_type, exc, traceback):
        if exc_type is not None: self.rollback()

    def stage_audit(self, *, actor_id: int, project_id: int, operation: str, details: dict) -> None:
        self.session.add(AuditLog(user_id=actor_id, action=operation, entity="ENGINEERING_EXECUTION_PLAN", entity_id=project_id, details=details))

    def commit(self): self.session.commit()
    def rollback(self): self.session.rollback()
