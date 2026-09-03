"""Explicit outer transaction owner for Batch-2 Registry operations."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from app.core.database import DisciplinePackageGuardMode, acquire_discipline_package_registry_guard
from app.repositories.discipline_package_repository import DisciplinePackageRepository


class DisciplinePackageUnitOfWork:
    """A small UoW that exposes one same-connection Session per attempt."""

    def __init__(self, factory: sessionmaker):
        self._factory = factory
        self.session: Session | None = None
        self.repository: DisciplinePackageRepository | None = None

    def __enter__(self) -> "DisciplinePackageUnitOfWork":
        self.session = self._factory()
        self.session.begin()
        self.repository = DisciplinePackageRepository(self.session)
        return self

    def acquire_guard(self, mode: DisciplinePackageGuardMode) -> None:
        if self.session is None:
            raise RuntimeError("unit of work is not active")
        acquire_discipline_package_registry_guard(self.session, mode)

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
            if exc_type is not None:
                self.session.rollback()
            elif self.session.in_transaction():
                self.session.rollback()
        finally:
            self.session.close()
