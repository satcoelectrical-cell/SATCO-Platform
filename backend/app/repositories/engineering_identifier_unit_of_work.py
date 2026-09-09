"""One-session ADR-025 Unit of Work."""

from app.repositories.engineering_identifier_repository import SqlAlchemyEngineeringIdentifierRepository


class SqlAlchemyEngineeringIdentifierUnitOfWork:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    def __enter__(self):
        self.session = self._session_factory()
        self.identifiers = SqlAlchemyEngineeringIdentifierRepository(self.session)
        return self

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self.session.rollback()
        self.session.close()
