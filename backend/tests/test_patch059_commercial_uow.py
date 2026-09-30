from unittest.mock import MagicMock

import pytest

from app.repositories.commercial_entitlement_unit_of_work import (
    CommercialEntitlementUnitOfWork,
    require_repository,
)


def _factory_with_session(session):
    factory = MagicMock()
    factory.return_value = session
    return factory


def test_uow_opens_one_explicit_transaction_and_commit():
    session = MagicMock()
    transaction = MagicMock()
    session.begin.return_value = transaction
    session.in_transaction.return_value = True

    factory = _factory_with_session(session)

    with CommercialEntitlementUnitOfWork(factory) as uow:
        assert uow.session is session
        assert require_repository(uow) is uow.repository

        uow.commit()

        transaction.commit.assert_called_once_with()

    factory.assert_called_once_with()
    session.begin.assert_called_once_with()
    session.close.assert_called_once_with()
    transaction.rollback.assert_not_called()


def test_uow_rolls_back_uncommitted_transaction_on_exit():
    session = MagicMock()
    transaction = MagicMock()
    session.begin.return_value = transaction
    session.in_transaction.return_value = True

    factory = _factory_with_session(session)

    with CommercialEntitlementUnitOfWork(factory):
        pass

    transaction.rollback.assert_called_once_with()
    transaction.commit.assert_not_called()
    session.close.assert_called_once_with()


def test_uow_rolls_back_when_exception_escapes():
    session = MagicMock()
    transaction = MagicMock()
    session.begin.return_value = transaction
    session.in_transaction.return_value = True

    factory = _factory_with_session(session)

    with pytest.raises(RuntimeError, match="boom"):
        with CommercialEntitlementUnitOfWork(factory):
            raise RuntimeError("boom")

    transaction.rollback.assert_called_once_with()
    transaction.commit.assert_not_called()
    session.close.assert_called_once_with()


def test_require_repository_fails_closed_outside_uow():
    factory = MagicMock()
    uow = CommercialEntitlementUnitOfWork(factory)

    with pytest.raises(RuntimeError, match="not active"):
        require_repository(uow)


def test_require_repository_fails_without_active_transaction():
    session = MagicMock()
    transaction = MagicMock()
    session.begin.return_value = transaction
    session.in_transaction.return_value = False

    factory = _factory_with_session(session)

    with CommercialEntitlementUnitOfWork(factory) as uow:
        with pytest.raises(RuntimeError, match="active transaction"):
            require_repository(uow)
