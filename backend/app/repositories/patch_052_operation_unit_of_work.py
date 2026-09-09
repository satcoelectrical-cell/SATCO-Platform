"""One fresh outer transaction for PATCH-052 package mutations."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from app.core.database import (
    DisciplinePackageGuardMode,
    acquire_discipline_package_registry_guard,
)
from app.models.audit_log import AuditLog
from app.repositories.engineering_deliverable_repository import (
    EngineeringDeliverableRepository,
)
from app.repositories.engineering_identifier_repository import (
    SqlAlchemyEngineeringIdentifierRepository,
)
from app.repositories.package_input_binding_repository import PackageInputBindingRepository


class Patch052OperationUnitOfWork:
    """Own every package write, commit, rollback, and Session lifetime."""

    def __init__(self, factory: sessionmaker):
        self._factory = factory
        self.session: Session | None = None

    def __enter__(self) -> "Patch052OperationUnitOfWork":
        self.session = self._factory()
        self.session.begin()
        self.identifiers = SqlAlchemyEngineeringIdentifierRepository(self.session)
        self.deliverables = EngineeringDeliverableRepository(self.session)
        self.bindings = PackageInputBindingRepository(self.session)
        # Canonical Deliverable staging code uses this established name.
        self.repository = self.deliverables
        return self

    def acquire_registry_guard(self) -> None:
        if self.session is None:
            raise RuntimeError("unit of work is not active")
        acquire_discipline_package_registry_guard(
            self.session, DisciplinePackageGuardMode.SHARED,
        )

    def stage_audit(
        self, *, actor_id: int, project_id: int, operation: str, details: dict,
    ) -> None:
        if self.session is None:
            raise RuntimeError("unit of work is not active")
        self.session.add(AuditLog(
            user_id=actor_id,
            action=operation,
            entity="ENGINEERING_DELIVERABLE",
            entity_id=project_id,
            details=details,
        ))

    def commit(self) -> None:
        if self.session is None:
            raise RuntimeError("unit of work is not active")
        self.session.commit()

    def rollback(self) -> None:
        if self.session is not None:
            self.session.rollback()

    def __exit__(self, exc_type, exc, traceback) -> None:
        assert self.session is not None
        try:
            if exc_type is not None or self.session.in_transaction():
                self.session.rollback()
        finally:
            self.session.close()
