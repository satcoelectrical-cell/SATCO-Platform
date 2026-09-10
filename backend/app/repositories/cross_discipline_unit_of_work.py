"""Fresh-session Unit of Work and exact retry classification."""

from app.core.database import DisciplinePackageGuardMode, acquire_discipline_package_registry_guard

from .cross_discipline_repository import CrossDisciplineRepository


RETRYABLE_SQLSTATES = frozenset({"40001", "40P01", "55P03"})
RETRYABLE_UNIQUE_CONSTRAINTS = frozenset({
    "uq_xdi_assessment_idempotency", "uq_xdi_idempotency_scope",
    "uq_xdi_lineage_operation",
})


def retryable_database_error(error):
    original = getattr(error, "orig", error)
    sqlstate = getattr(original, "pgcode", None) or getattr(original, "sqlstate", None)
    if sqlstate in RETRYABLE_SQLSTATES:
        return True
    if sqlstate != "23505":
        return False
    diagnostic = getattr(original, "diag", None)
    return getattr(diagnostic, "constraint_name", None) in RETRYABLE_UNIQUE_CONSTRAINTS


class CrossDisciplineUnitOfWork:
    def __init__(self, factory):
        self._factory = factory
        self.session = None
        self.repository = None
        self.commits = 0

    def __enter__(self):
        self.session = self._factory()
        self.session.begin()
        acquire_discipline_package_registry_guard(self.session, DisciplinePackageGuardMode.SHARED)
        self.repository = CrossDisciplineRepository(self.session)
        return self

    def __exit__(self, exc_type, _exc, _traceback):
        try:
            if exc_type is not None and self.session is not None:
                self.session.rollback()
        finally:
            if self.session is not None:
                self.session.close()
        return False

    def commit(self):
        self.session.commit()
        self.commits += 1

    def rollback(self):
        self.session.rollback()
