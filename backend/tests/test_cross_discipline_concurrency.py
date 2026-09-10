import pytest

from app.ports.cross_discipline_intelligence import ProtectedResourceError
from app.repositories.cross_discipline_unit_of_work import retryable_database_error
from app.services.cross_discipline_service import RetryExhausted, run_with_fresh_retries


class DatabaseError(RuntimeError):
    def __init__(self, state):
        self.pgcode = state


@pytest.mark.parametrize("state", ("40001", "40P01", "55P03"))
def test_retryable_states_use_fresh_authorization_and_three_total_attempts(state):
    sessions = []
    authorizations = []
    def attempt(number):
        sessions.append(object())
        raise DatabaseError(state)
    with pytest.raises(RetryExhausted):
        run_with_fresh_retries(attempt, authorize=authorizations.append)
    assert len(sessions) == 3
    assert len({id(item) for item in sessions}) == 3
    assert authorizations == [1, 2, 3]


def test_unknown_integrity_state_is_not_retried():
    calls = []
    with pytest.raises(DatabaseError):
        run_with_fresh_retries(
            lambda attempt: (calls.append(attempt), (_ for _ in ()).throw(DatabaseError("23503")))[1],
            authorize=lambda _attempt: None,
        )
    assert calls == [1]


def test_authorization_revocation_stops_before_retry_disclosure():
    def attempt(number):
        if number == 1:
            raise DatabaseError("40001")
        return "must-not-return"
    with pytest.raises(ProtectedResourceError):
        run_with_fresh_retries(
            attempt,
            authorize=lambda number: (_ for _ in ()).throw(ProtectedResourceError()) if number == 2 else None,
        )
