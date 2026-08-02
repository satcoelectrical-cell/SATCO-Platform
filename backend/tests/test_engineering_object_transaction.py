"""Atomic Unit of Work and idempotency tests for Sprint-2."""

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.exceptions.engineering_object import EngineeringObjectIdempotencyConflict
from app.repositories.engineering_object_unit_of_work import (
    SqlAlchemyEngineeringObjectUnitOfWork,
)
from app.repositories.engineering_object_unit_of_work import (
    SqlAlchemyIdempotencyStore,
)


def test_unit_of_work_owns_commit_and_shares_one_session() -> None:
    session = MagicMock()
    with SqlAlchemyEngineeringObjectUnitOfWork(lambda: session) as uow:
        assert uow.engineering_objects.session is session
        assert uow.audit.session is session
        assert uow.domain_events.session is session
        assert uow.idempotency.session is session
        uow.commit()
    session.commit.assert_called_once()


def test_unit_of_work_rolls_back_every_failed_operation() -> None:
    session = MagicMock()
    with pytest.raises(RuntimeError):
        with SqlAlchemyEngineeringObjectUnitOfWork(lambda: session):
            raise RuntimeError("atomic failure")
    session.rollback.assert_called_once()
    session.commit.assert_not_called()


def test_idempotency_conflicting_fingerprint_is_rejected() -> None:
    session = MagicMock()
    session.query.return_value.filter_by.return_value.first.return_value = (
        SimpleNamespace(request_fingerprint="first", status="completed")
    )
    store = SqlAlchemyIdempotencyStore(session)

    with pytest.raises(EngineeringObjectIdempotencyConflict):
        store.find(
            actor_id=1, command_type="CreateEngineeringObject",
            idempotency_id=uuid4(), request_fingerprint="different",
        )


def test_idempotency_retry_returns_recorded_authorized_snapshot() -> None:
    session = MagicMock()
    object_id = uuid4()
    correlation_id = uuid4()
    session.query.return_value.filter_by.return_value.first.return_value = (
        SimpleNamespace(
            request_fingerprint="same",
            status="completed",
            result={
                "object_id": str(object_id),
                "previous_version": 1,
                "version": 2,
                "command_type": "TransferEngineeringObjectSteward",
                "correlation_id": str(correlation_id),
                "authorized_state": {"id": str(object_id), "version": 2},
            },
        )
    )

    outcome = SqlAlchemyIdempotencyStore(session).find(
        actor_id=1,
        command_type="TransferEngineeringObjectSteward",
        idempotency_id=uuid4(),
        request_fingerprint="same",
    )

    assert outcome is not None
    assert outcome.result.version == 2
    assert outcome.authorized_state["version"] == 2
