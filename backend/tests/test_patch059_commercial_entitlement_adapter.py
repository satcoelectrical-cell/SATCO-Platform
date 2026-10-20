from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID

import pytest

import app.adapters.commercial_entitlement as adapter_module
from app.adapters.commercial_entitlement import CommercialEntitlementAdapter
from app.enums.discipline_package import EntitlementDecision, EntitlementOperation
from app.ports.discipline_package import EntitlementRequest
from app.services.commercial_entitlement_service import (
    TrustedTimeDecision,
    TrustedTimeEvaluation,
)


ORG = UUID("00000000-0000-4000-8000-000000000001")
NOW = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)


def request(operation=EntitlementOperation.EXECUTE, package_key="electrical"):
    return EntitlementRequest(
        trusted_organization_id=ORG,
        trusted_deployment_id="satco-production",
        package_key=package_key,
        entitlement_key=package_key,
        operation=operation,
    )


def test_historical_read_is_commercially_permitted_without_current_seat() -> None:
    adapter = CommercialEntitlementAdapter(session_factory=lambda: None)
    assert (
        adapter.evaluate(request(EntitlementOperation.HISTORICAL_READ))
        is EntitlementDecision.PERMITTED
    )


def test_configure_execute_fail_closed_without_authenticated_user() -> None:
    adapter = CommercialEntitlementAdapter(session_factory=lambda: None)
    assert adapter.evaluate(request()) is EntitlementDecision.UNAVAILABLE


@pytest.mark.parametrize(
    ("now_offset", "package_key", "seat_executable", "expected"),
    [
        (timedelta(0), "electrical", True, EntitlementDecision.PERMITTED),
        (timedelta(0), "instrumentation", True, EntitlementDecision.DENIED),
        (timedelta(days=2), "electrical", True, EntitlementDecision.DENIED),
        (timedelta(0), "electrical", False, EntitlementDecision.DENIED),
    ],
)
def test_active_expired_package_and_seat_matrix(
    monkeypatch,
    now_offset,
    package_key,
    seat_executable,
    expected,
) -> None:
    state = SimpleNamespace(
        package_keys=["electrical"],
        not_before=NOW - timedelta(days=1),
        valid_until=NOW + timedelta(days=1),
        grace_until=NOW + timedelta(days=1, hours=12),
        last_trusted_time=NOW,
        time_untrusted_at=None,
    )

    repository = SimpleNamespace(get_state=lambda **kwargs: state)

    class FakeUow:
        def __init__(self, factory):
            self.repository = repository
            self.session = SimpleNamespace(in_transaction=lambda: True)
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def commit(self):
            pass

    monkeypatch.setattr(adapter_module, "CommercialEntitlementUnitOfWork", FakeUow)
    monkeypatch.setattr(
        adapter_module,
        "evaluate_seat",
        lambda *args, **kwargs: SimpleNamespace(executable=seat_executable),
    )

    adapter = CommercialEntitlementAdapter(
        session_factory=lambda: None,
        user_id=42,
        now=lambda: NOW + now_offset,
    )

    assert adapter.evaluate(request(package_key=package_key)) is expected


@pytest.mark.parametrize(
    ("proof_time", "seat_executable", "expected"),
    [
        (NOW - timedelta(days=2), True, EntitlementDecision.PERMITTED),
        (NOW - timedelta(days=1), True, EntitlementDecision.PERMITTED),
        (NOW - timedelta(hours=12), True, EntitlementDecision.DENIED),
        (None, True, EntitlementDecision.DENIED),
        (NOW - timedelta(days=2), False, EntitlementDecision.DENIED),
    ],
)
def test_grace_execute_requires_preexpiry_current_enablement_proof_and_seat(
    monkeypatch,
    proof_time,
    seat_executable,
    expected,
) -> None:
    valid_until = NOW - timedelta(days=1)
    state = SimpleNamespace(
        package_keys=["electrical"],
        not_before=NOW - timedelta(days=3),
        valid_until=valid_until,
        grace_until=NOW + timedelta(days=1),
        last_trusted_time=NOW,
        time_untrusted_at=None,
    )
    proof = (
        None
        if proof_time is None
        else SimpleNamespace(configured_before=proof_time)
    )

    class Repository:
        def get_state(self, **kwargs):
            return state

        def get_configuration_proof(self, **kwargs):
            assert kwargs == {
                "organization_id": ORG,
                "deployment_id": "satco-production",
                "package_key": "electrical",
            }
            return proof

    repository = Repository()

    class FakeUow:
        def __init__(self, factory):
            self.repository = repository
            self.session = SimpleNamespace(in_transaction=lambda: True)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def commit(self):
            pass

    monkeypatch.setattr(
        adapter_module,
        "CommercialEntitlementUnitOfWork",
        FakeUow,
    )
    monkeypatch.setattr(
        adapter_module,
        "evaluate_seat",
        lambda *args, **kwargs: SimpleNamespace(
            executable=seat_executable
        ),
    )

    adapter = CommercialEntitlementAdapter(
        session_factory=lambda: None,
        user_id=42,
        now=lambda: NOW,
    )

    assert adapter.evaluate(request()) is expected


def test_grace_historical_read_remains_independent_of_proof_and_seat() -> None:
    adapter = CommercialEntitlementAdapter(
        session_factory=lambda: (_ for _ in ()).throw(
            AssertionError("historical read must not open commercial UoW")
        ),
        user_id=None,
    )

    assert (
        adapter.evaluate(request(EntitlementOperation.HISTORICAL_READ))
        is EntitlementDecision.PERMITTED
    )

def test_time_untrusted_fails_closed(monkeypatch) -> None:
    state = SimpleNamespace(
        package_keys=["electrical"],
        not_before=NOW - timedelta(days=1),
        valid_until=NOW + timedelta(days=1),
        grace_until=NOW + timedelta(days=2),
        last_trusted_time=NOW,
        time_untrusted_at=None,
    )
    commits = []

    repository = SimpleNamespace(get_state=lambda **kwargs: state)

    class FakeUow:
        def __init__(self, factory):
            self.repository = repository
            self.session = SimpleNamespace(in_transaction=lambda: True)
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def commit(self):
            commits.append(True)

    monkeypatch.setattr(adapter_module, "CommercialEntitlementUnitOfWork", FakeUow)
    monkeypatch.setattr(
        adapter_module,
        "evaluate_trusted_time",
        lambda **kwargs: TrustedTimeEvaluation(
            decision=TrustedTimeDecision.TIME_UNTRUSTED,
            effective_time=NOW,
            should_persist_checkpoint=False,
        ),
    )

    adapter = CommercialEntitlementAdapter(
        session_factory=lambda: None,
        user_id=42,
        now=lambda: NOW - timedelta(minutes=10),
    )

    assert adapter.evaluate(request()) is EntitlementDecision.UNAVAILABLE
    assert state.time_untrusted_at == NOW - timedelta(minutes=10)
    assert commits == [True]


PACKAGE_COMBINATIONS = (
    ("electrical",),
    ("instrumentation",),
    ("control_automation",),
    ("electrical", "instrumentation"),
    ("electrical", "control_automation"),
    ("instrumentation", "control_automation"),
    ("electrical", "instrumentation", "control_automation"),
)


@pytest.mark.parametrize("package_keys", PACKAGE_COMBINATIONS)
def test_all_seven_commercial_package_combinations_are_exact_and_restrictive(
    monkeypatch,
    package_keys,
) -> None:
    state = SimpleNamespace(
        package_keys=list(package_keys),
        not_before=NOW - timedelta(days=1),
        valid_until=NOW + timedelta(days=1),
        grace_until=NOW + timedelta(days=2),
        last_trusted_time=NOW,
        time_untrusted_at=None,
    )

    class Repository:
        def get_state(self, **kwargs):
            return state

    repository = Repository()

    class FakeUow:
        def __init__(self, factory):
            self.repository = repository
            self.session = SimpleNamespace(in_transaction=lambda: True)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def commit(self):
            pass

    monkeypatch.setattr(
        adapter_module,
        "CommercialEntitlementUnitOfWork",
        FakeUow,
    )
    monkeypatch.setattr(
        adapter_module,
        "evaluate_seat",
        lambda *args, **kwargs: SimpleNamespace(executable=True),
    )

    adapter = CommercialEntitlementAdapter(
        session_factory=lambda: None,
        user_id=42,
        now=lambda: NOW,
    )

    universe = {
        "electrical",
        "instrumentation",
        "control_automation",
    }

    for package_key in universe:
        decision = adapter.evaluate(
            EntitlementRequest(
                trusted_organization_id=ORG,
                trusted_deployment_id="satco-production",
                package_key=package_key,
                entitlement_key=package_key,
                operation=EntitlementOperation.EXECUTE,
            )
        )

        expected = (
            EntitlementDecision.PERMITTED
            if package_key in package_keys
            else EntitlementDecision.DENIED
        )
        assert decision is expected
