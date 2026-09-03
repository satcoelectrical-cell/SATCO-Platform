"""PostgreSQL-only guard and fresh-UoW foundations for PATCH-051."""

import os

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

from app.core.database import (
    PACKAGE_REGISTRY_GUARD_CONTRACT,
    PACKAGE_REGISTRY_GUARD_NAMESPACE,
    DisciplinePackageGuardMode,
    acquire_discipline_package_registry_guard,
)
from app.repositories.discipline_package_unit_of_work import DisciplinePackageUnitOfWork


def test_governed_advisory_guard_contract_is_fixed():
    assert (PACKAGE_REGISTRY_GUARD_NAMESPACE, PACKAGE_REGISTRY_GUARD_CONTRACT) == (1396790339, 51)
    assert DisciplinePackageGuardMode.SHARED.value == "shared"
    assert DisciplinePackageGuardMode.EXCLUSIVE.value == "exclusive"


def test_postgresql_guard_uses_local_timeout_before_lock_and_shared_sessions_coexist():
    """Two independent connections exercise the actual fixed advisory key."""
    engine = create_engine(os.environ["TEST_DATABASE_URL"], pool_pre_ping=True)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    seen: list[str] = []

    def observe(_connection, _cursor, statement, _parameters, _context, _executemany):
        normalized = statement.strip().lower()
        if "lock_timeout" in normalized or "pg_advisory_xact_lock" in normalized:
            seen.append(normalized)

    event.listen(engine, "before_cursor_execute", observe)
    first = DisciplinePackageUnitOfWork(factory)
    second = DisciplinePackageUnitOfWork(factory)
    try:
        first.__enter__()
        first.acquire_guard(DisciplinePackageGuardMode.SHARED)
        second.__enter__()
        second.acquire_guard(DisciplinePackageGuardMode.SHARED)
        assert first.session is not None and second.session is not None
        assert first.session.connection().connection.driver_connection is not second.session.connection().connection.driver_connection
        assert first.session.scalar(text("SHOW lock_timeout")) == "5s"
        assert second.session.scalar(text("SHOW lock_timeout")) == "5s"
        assert "set local lock_timeout = '5s'" in seen[0]
        assert "pg_advisory_xact_lock_shared" in seen[1]
        assert "set local lock_timeout = '5s'" in seen[2]
        assert "pg_advisory_xact_lock_shared" in seen[3]
    finally:
        if second.session is not None:
            second.rollback()
            second.__exit__(None, None, None)
        if first.session is not None:
            first.rollback()
            first.__exit__(None, None, None)
        event.remove(engine, "before_cursor_execute", observe)
        engine.dispose()

def test_each_unit_of_work_attempt_creates_a_fresh_session():
    """Retry callers receive a distinct Session; no transaction state leaks."""
    engine = create_engine(os.environ["TEST_DATABASE_URL"], pool_pre_ping=True)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    first = DisciplinePackageUnitOfWork(factory)
    second = DisciplinePackageUnitOfWork(factory)
    try:
        first.__enter__()
        first.acquire_guard(DisciplinePackageGuardMode.SHARED)
        assert first.session is not None
        first_session_id = id(first.session)
        first.rollback()
        first.__exit__(None, None, None)

        second.__enter__()
        second.acquire_guard(DisciplinePackageGuardMode.SHARED)
        assert second.session is not None
        assert id(second.session) != first_session_id
        assert second.session.scalar(text("SHOW lock_timeout")) == "5s"
    finally:
        if second.session is not None:
            second.rollback()
            second.__exit__(None, None, None)
        engine.dispose()
