from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import HTTPException

from app.api.v1.routers import commercial_entitlements as api
from app.services.commercial_seat_service import (
    CommercialSeatError,
    CommercialSeatReason,
    CommercialSeatState,
    OverCapacityStatus,
    SeatEvaluation,
    SeatListEvaluation,
    SeatMutationResult,
)


ORG = UUID("05900000-0000-4000-8000-000000000001")


def _admin():
    return SimpleNamespace(
        organization=SimpleNamespace(
            organization_id=ORG,
            user=SimpleNamespace(id=59),
        )
    )


class FakeRepository:
    def __init__(self):
        self.user_ids = None

    def list_membership_users(self, *, organization_id, user_ids):
        assert organization_id == ORG
        self.user_ids = user_ids
        return (
            SimpleNamespace(id=101, full_name="Seat User A"),
            SimpleNamespace(id=102, full_name=None),
        )


class FakeUow:
    instances = []

    def __init__(self, factory):
        self.factory = factory
        self.session = object()
        self.repository = FakeRepository()
        self.committed = False
        type(self).instances.append(self)

    def __enter__(self):
        return self

    def commit(self):
        self.committed = True

    def __exit__(self, exc_type, exc, tb):
        return None


@pytest.fixture(autouse=True)
def _wire(monkeypatch):
    FakeUow.instances.clear()
    monkeypatch.setattr(
        api.settings,
        "SATCO_DEPLOYMENT_ID",
        "satco-production",
    )
    monkeypatch.setattr(api, "CommercialEntitlementUnitOfWork", FakeUow)
    monkeypatch.setattr(api, "SessionLocal", object())
    monkeypatch.setattr(api, "require_repository", lambda uow: uow.repository)


def test_get_seats_uses_canonical_batch_evaluation_and_scoped_display_names(
    monkeypatch,
):
    captured = {}

    def evaluate(uow, **kwargs):
        captured.update(kwargs)
        return SeatListEvaluation(
            capacity=2,
            consuming_count=2,
            over_capacity=False,
            seats=(
                SeatEvaluation(
                    user_id=101,
                    stored_state=CommercialSeatState.ASSIGNED,
                    effective_state=CommercialSeatState.ASSIGNED,
                    executable=True,
                    reason_code=None,
                ),
                SeatEvaluation(
                    user_id=102,
                    stored_state=CommercialSeatState.ASSIGNED,
                    effective_state=CommercialSeatState.RESERVED,
                    executable=False,
                    reason_code="seat_reserved",
                ),
            ),
        )

    monkeypatch.setattr(api, "list_seat_evaluations", evaluate)

    response = api.list_current_commercial_seats(admin=_admin())

    assert captured == {
        "organization_id": ORG,
        "deployment_id": "satco-production",
    }
    assert response.capacity == 2
    assert response.consuming_count == 2
    assert response.over_capacity is False
    assert [seat.user_id for seat in response.seats] == [101, 102]
    assert response.seats[0].display_name == "Seat User A"
    assert response.seats[0].executable is True
    assert response.seats[1].state == "RESERVED"
    assert response.seats[1].display_name is None
    assert FakeUow.instances[0].repository.user_ids == (101, 102)


def test_assign_stages_safe_audit_before_commit(monkeypatch):
    events = []

    def assign(uow, **kwargs):
        assert kwargs["organization_id"] == ORG
        assert kwargs["deployment_id"] == "satco-production"
        assert kwargs["user_id"] == 101
        assert kwargs["actor_user_id"] == 59
        return SeatMutationResult(
            user_id=101,
            state=CommercialSeatState.ASSIGNED,
            consuming_count=1,
            capacity=5,
        )

    def audit(session, user_id, action, entity, entity_id=None, details=None):
        events.append(("audit", user_id, action, entity, entity_id, details))

    monkeypatch.setattr(api, "assign_seat", assign)
    monkeypatch.setattr(api, "stage_audit_log", audit)

    response = api.assign_current_commercial_seat(user_id=101, admin=_admin())

    assert response.state == "ASSIGNED"
    assert FakeUow.instances[0].committed is True
    assert events[0][1:5] == (
        59,
        "seat_assigned",
        "COMMERCIAL_SEAT",
        101,
    )
    assert events[0][5] == {
        "organization_id": str(ORG),
        "deployment_id": "satco-production",
        "outcome": "ASSIGNED",
        "consuming_count": 1,
        "capacity": 5,
    }


def test_audit_failure_prevents_seat_commit(monkeypatch):
    monkeypatch.setattr(
        api,
        "assign_seat",
        lambda *args, **kwargs: SeatMutationResult(
            user_id=101,
            state=CommercialSeatState.ASSIGNED,
            consuming_count=1,
            capacity=5,
        ),
    )
    monkeypatch.setattr(
        api,
        "stage_audit_log",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("audit")),
    )

    with pytest.raises(RuntimeError, match="audit"):
        api.assign_current_commercial_seat(user_id=101, admin=_admin())

    assert FakeUow.instances[0].committed is False


def test_assign_hides_cross_organization_or_missing_membership(monkeypatch):
    monkeypatch.setattr(
        api,
        "assign_seat",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            CommercialSeatError(CommercialSeatReason.MEMBERSHIP_REQUIRED)
        ),
    )

    with pytest.raises(HTTPException) as exc:
        api.assign_current_commercial_seat(user_id=999, admin=_admin())

    assert exc.value.status_code == 404
    assert exc.value.detail == "Protected resource not found"
    assert FakeUow.instances[0].committed is False


def test_release_response_allows_null_state_and_commits_audit(monkeypatch):
    monkeypatch.setattr(
        api,
        "release_seat",
        lambda *args, **kwargs: SeatMutationResult(
            user_id=101,
            state=None,
            consuming_count=0,
            capacity=5,
        ),
    )
    monkeypatch.setattr(api, "stage_audit_log", lambda *args, **kwargs: None)

    response = api.release_current_commercial_seat(
        user_id=101,
        admin=_admin(),
    )

    assert response.state is None
    assert response.consuming_count == 0
    assert FakeUow.instances[0].committed is True


def test_retained_request_is_exact_replacement_and_audited(monkeypatch):
    captured = {}
    audits = []

    def retain(uow, **kwargs):
        captured.update(kwargs)
        return OverCapacityStatus(
            consuming_count=3,
            capacity=1,
            over_capacity=True,
            unresolved=False,
        )

    monkeypatch.setattr(api, "retain_seats", retain)
    monkeypatch.setattr(
        api,
        "stage_audit_log",
        lambda *args, **kwargs: audits.append((args, kwargs)),
    )

    response = api.retain_current_commercial_seats(
        request=api.CommercialSeatRetainedRequest(user_ids=[102]),
        admin=_admin(),
    )

    assert captured["retained_user_ids"] == [102]
    assert captured["actor_user_id"] == 59
    assert response.over_capacity is True
    assert response.unresolved is False
    assert FakeUow.instances[0].committed is True
    assert audits[0][1]["details"]["retained_count"] == 1
    assert "user_ids" not in audits[0][1]["details"]


def test_seat_routes_are_declared_with_bounded_response_models():
    routes = {
        (route.path, next(iter(route.methods))): route
        for route in api.router.routes
        if route.path.startswith("/organizations/current/commercial-seats")
    }

    assert set(routes) == {
        ("/organizations/current/commercial-seats", "GET"),
        ("/organizations/current/commercial-seats/{user_id}", "POST"),
        ("/organizations/current/commercial-seats/{user_id}", "DELETE"),
        ("/organizations/current/commercial-seats/retained", "PUT"),
    }
    assert routes[
        ("/organizations/current/commercial-seats/{user_id}", "DELETE")
    ].response_model is api.CommercialSeatMutationResponse
