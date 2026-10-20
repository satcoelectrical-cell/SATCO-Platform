"""Explicit transaction boundary for PATCH-059 commercial mutations."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from app.repositories.commercial_entitlement_repository import (
    CommercialEntitlementRepository,
)


class CommercialEntitlementUnitOfWork:
    """Own exactly one SQLAlchemy Session/transaction per mutation attempt."""

    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory
        self.session: Session | None = None
        self.repository: CommercialEntitlementRepository | None = None
        self._transaction = None

    def __enter__(self) -> "CommercialEntitlementUnitOfWork":
        if self.session is not None:
            raise RuntimeError(
                "commercial entitlement unit of work is already active"
            )

        self.session = self._session_factory()
        self._transaction = self.session.begin()
        self._transaction.__enter__()

        self.repository = CommercialEntitlementRepository(self.session)
        return self

    def commit(self) -> None:
        if self.session is None or self._transaction is None:
            raise RuntimeError(
                "commercial entitlement unit of work is not active"
            )

        self._transaction.commit()
        self._transaction = None

    def rollback(self) -> None:
        if self.session is None:
            raise RuntimeError(
                "commercial entitlement unit of work is not active"
            )

        if self._transaction is not None:
            self._transaction.rollback()
            self._transaction = None

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if self._transaction is not None:
                self._transaction.rollback()
                self._transaction = None
        finally:
            if self.session is not None:
                self.session.close()

            self.repository = None
            self.session = None


def require_repository(
    uow: CommercialEntitlementUnitOfWork,
) -> CommercialEntitlementRepository:
    """Return the active repository or fail closed outside a UoW."""
    if uow.repository is None or uow.session is None:
        raise RuntimeError(
            "commercial entitlement unit of work is not active"
        )

    if not uow.session.in_transaction():
        raise RuntimeError(
            "commercial entitlement mutation requires an active transaction"
        )

    return uow.repository
