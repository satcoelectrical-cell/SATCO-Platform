from uuid import UUID

import pytest

from app.repositories.commercial_entitlement_repository import (
    commercial_advisory_lock_key,
)


def test_commercial_advisory_lock_golden_vectors_are_frozen():
    assert commercial_advisory_lock_key(
        UUID("00000000-0000-0000-0000-000000000001"),
        "satco-production",
    ) == 3311186576240453320

    assert commercial_advisory_lock_key(
        UUID("12345678-1234-5678-1234-567812345678"),
        "deployment-a",
    ) == 2649421229396425912


def test_commercial_advisory_lock_is_deterministic():
    organization_id = UUID(
        "12345678-1234-5678-1234-567812345678"
    )

    first = commercial_advisory_lock_key(
        organization_id,
        "deployment-a",
    )
    second = commercial_advisory_lock_key(
        organization_id,
        "deployment-a",
    )

    assert first == second


def test_commercial_advisory_lock_is_domain_sensitive():
    organization_a = UUID(
        "12345678-1234-5678-1234-567812345678"
    )
    organization_b = UUID(
        "12345678-1234-5678-1234-567812345679"
    )

    baseline = commercial_advisory_lock_key(
        organization_a,
        "deployment-a",
    )

    assert commercial_advisory_lock_key(
        organization_b,
        "deployment-a",
    ) != baseline

    assert commercial_advisory_lock_key(
        organization_a,
        "deployment-b",
    ) != baseline


def test_commercial_advisory_lock_is_signed_postgresql_bigint():
    value = commercial_advisory_lock_key(
        UUID("ffffffff-ffff-4fff-8fff-ffffffffffff"),
        "satco-production",
    )

    assert -(2**63) <= value <= 2**63 - 1


@pytest.mark.parametrize(
    ("organization_id", "deployment_id", "error"),
    (
        (
            "not-a-uuid",
            "deployment-a",
            TypeError,
        ),
        (
            UUID("12345678-1234-5678-1234-567812345678"),
            "",
            ValueError,
        ),
    ),
)
def test_commercial_advisory_lock_rejects_noncanonical_inputs(
    organization_id,
    deployment_id,
    error,
):
    with pytest.raises(error):
        commercial_advisory_lock_key(
            organization_id,
            deployment_id,
        )


def test_postgresql_advisory_lock_is_transaction_scoped():
    from sqlalchemy import create_engine, text

    from app.core.database import DATABASE_URL

    engine = create_engine(DATABASE_URL)

    organization_id = UUID(
        "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    )
    deployment_id = "patch059-lock-transaction-test"

    lock_key = commercial_advisory_lock_key(
        organization_id,
        deployment_id,
    )

    connection_a = engine.connect()
    connection_b = engine.connect()

    transaction_a = connection_a.begin()
    transaction_b = connection_b.begin()

    try:
        acquired_a = connection_a.execute(
            text("SELECT pg_try_advisory_xact_lock(:key)"),
            {"key": lock_key},
        ).scalar_one()

        assert acquired_a is True

        acquired_b_while_a_open = connection_b.execute(
            text("SELECT pg_try_advisory_xact_lock(:key)"),
            {"key": lock_key},
        ).scalar_one()

        assert acquired_b_while_a_open is False

        transaction_a.commit()

        acquired_b_after_a_commit = connection_b.execute(
            text("SELECT pg_try_advisory_xact_lock(:key)"),
            {"key": lock_key},
        ).scalar_one()

        assert acquired_b_after_a_commit is True

        transaction_b.commit()
    finally:
        if transaction_a.is_active:
            transaction_a.rollback()
        if transaction_b.is_active:
            transaction_b.rollback()

        connection_a.close()
        connection_b.close()
        engine.dispose()


def test_repository_initial_path_acquires_expected_advisory_lock():
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    from app.core.database import DATABASE_URL
    from app.repositories.commercial_entitlement_repository import (
        CommercialEntitlementRepository,
    )

    engine = create_engine(DATABASE_URL)
    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    organization_id = UUID(
        "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    )
    deployment_id = "patch059-first-activation-lock-test"

    expected_key = commercial_advisory_lock_key(
        organization_id,
        deployment_id,
    )

    session = session_factory()

    try:
        with session.begin():
            repository = CommercialEntitlementRepository(session)

            state = repository.lock_state_or_acquire_initial_lock(
                organization_id=organization_id,
                deployment_id=deployment_id,
            )

            assert state is None

            held = session.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM pg_locks
                        WHERE locktype = 'advisory'
                          AND pid = pg_backend_pid()
                          AND granted
                    )
                    """
                )
            ).scalar_one()

            assert held is True

            competing_connection = engine.connect()
            competing_transaction = competing_connection.begin()

            try:
                competing_acquired = competing_connection.execute(
                    text("SELECT pg_try_advisory_xact_lock(:key)"),
                    {"key": expected_key},
                ).scalar_one()

                assert competing_acquired is False
            finally:
                competing_transaction.rollback()
                competing_connection.close()
    finally:
        session.close()
        engine.dispose()
