from app.models.audit_log import AuditLog
from app.repositories.project_foundation_repository import ProjectFoundationRepository


class SqlAlchemyProjectFoundationUnitOfWork:
    def __init__(self, session):
        self.session = session
        self.repository = ProjectFoundationRepository(session)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        if exc_type is not None:
            self.rollback()

    def stage_audit(self, *, actor_id: int, project_id: int, operation: str, details: dict) -> None:
        self.session.add(AuditLog(
            user_id=actor_id,
            action=operation,
            entity="PROJECT_FOUNDATION",
            entity_id=project_id,
            details=details,
        ))

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
