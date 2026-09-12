"""Transaction boundary for standards mutation, AuditLog, outbox and idempotency."""

from __future__ import annotations

from contextlib import AbstractContextManager

from sqlalchemy.orm import Session


class StandardsUnitOfWork(AbstractContextManager):
    def __init__(self, session: Session) -> None:
        self.session = session

    def __enter__(self): return self
    def commit(self) -> None: self.session.commit()
    def rollback(self) -> None: self.session.rollback()
    def __exit__(self, exc_type, exc, traceback):
        if exc_type: self.session.rollback()
        return False
