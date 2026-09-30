from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker

from app.models.commercial_entitlement import (
    CommercialEntitlementActivation,
    CommercialEntitlementState,
    CommercialSeatAssignment,
)
from app.models.organization import Organization, UserOrganizationMembership
from app.models.user import User
from app.repositories.commercial_entitlement_unit_of_work import (
    CommercialEntitlementUnitOfWork,
)
from app.services.commercial_seat_service import (
    CommercialSeatError,
    CommercialSeatReason,
    CommercialSeatState,
    assign_seat,
    evaluate_seat,
    release_seat,
    retain_seats,
    over_capacity_status,
)


ORG_ID = UUID("05900000-0000-4000-8000-000000000031")
DEPLOYMENT_ID = "patch059-b3-seat-transaction-test"
NOW = datetime(2026, 9, 30, 6, 0, tzinfo=timezone.utc)


def _engine_and_factory():
    import os

    url = os.environ["TEST_DATABASE_URL"]
    assert "127.0.0.1:55432" in url
    assert url.endswith("/satco_platform_patch02022_test")

    engine = create_engine(url, future=True)
    return engine, sessionmaker(bind=engine, expire_on_commit=False, future=True)


def _cleanup(factory):
    with factory() as session:
        session.execute(
            delete(CommercialSeatAssignment).where(
                CommercialSeatAssignment.organization_id == ORG_ID,
                CommercialSeatAssignment.deployment_id == DEPLOYMENT_ID,
            )
        )
        session.execute(
            delete(CommercialEntitlementActivation).where(
                CommercialEntitlementActivation.organization_id == ORG_ID,
                CommercialEntitlementActivation.deployment_id == DEPLOYMENT_ID,
            )
        )
        session.execute(
            delete(CommercialEntitlementState).where(
                CommercialEntitlementState.organization_id == ORG_ID,
                CommercialEntitlementState.deployment_id == DEPLOYMENT_ID,
            )
        )

        memberships = session.query(UserOrganizationMembership).filter(
            UserOrganizationMembership.organization_id == ORG_ID
        ).all()
        user_ids = [row.user_id for row in memberships]

        for row in memberships:
            session.delete(row)

        if user_ids:
            session.query(User).filter(User.id.in_(user_ids)).delete(
                synchronize_session=False
            )

        session.execute(delete(Organization).where(Organization.id == ORG_ID))
        session.commit()


def _create_user(session, suffix: str) -> User:
    token = uuid4().hex
    user = User(
        email=f"patch059-b3-{suffix}-{token}@example.test",
        username=f"p059b3_{suffix}_{token[:12]}",
        hashed_password="not-used-by-this-test",
        role="engineer",
        is_active=True,
        activation_pending=True,
    )
    session.add(user)
    session.flush()

    membership = session.get(
        UserOrganizationMembership,
        (user.id, ORG_ID),
    )
    if membership is None:
        membership = UserOrganizationMembership(
            user_id=user.id,
            organization_id=ORG_ID,
            is_enabled=True,
            is_selected=False,
            version=1,
        )
        session.add(membership)
    else:
        membership.is_enabled = True

    session.flush()
    return user


def _seed(factory, capacity: int = 1):
    with factory() as session:
        session.add(
            Organization(
                id=ORG_ID,
                name="PATCH-059 B3 Seat Test",
                slug=f"patch059-b3-{uuid4().hex[:12]}",
                is_active=True,
            )
        )
        session.flush()

        user_a = _create_user(session, "a")
        user_b = _create_user(session, "b")

        state = CommercialEntitlementState(
            organization_id=ORG_ID,
            deployment_id=DEPLOYMENT_ID,
            entitlement_id=uuid4(),
            accepted_revision=1,
            canonical_payload_digest="a" * 64,
            key_id="patch059-b3-key",
            issuer="patch059-test",
            issued_at=NOW - timedelta(days=2),
            not_before=NOW - timedelta(days=1),
            valid_until=NOW + timedelta(days=1),
            grace_until=NOW + timedelta(days=2),
            support_until=None,
            package_keys=["instrumentation"],
            seat_capacity=capacity,
            baseline_release_sequence=1,
            max_release_sequence=10,
            last_trusted_time=NOW,
            accepted_at=NOW,
            accepted_by_user_id=None,
            time_untrusted_at=None,
            version=1,
        )
        session.add(state)
        session.commit()

        return user_a.id, user_b.id


def _assign(factory, user_id: int):
    with CommercialEntitlementUnitOfWork(factory) as uow:
        try:
            result = assign_seat(
                uow,
                organization_id=ORG_ID,
                deployment_id=DEPLOYMENT_ID,
                user_id=user_id,
                actor_user_id=None,
                observed_now=NOW,
            )
            uow.commit()
            return ("accepted", result.user_id)
        except CommercialSeatError as exc:
            uow.rollback()
            return ("rejected", exc.reason_code)


def test_concurrent_last_seat_assignment_allows_exactly_one_winner():
    engine, factory = _engine_and_factory()
    _cleanup(factory)

    try:
        user_a, user_b = _seed(factory, capacity=1)
        barrier = Barrier(2)

        def worker(user_id: int):
            barrier.wait()
            return _assign(factory, user_id)

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(worker, (user_a, user_b)))

        accepted = [item for item in results if item[0] == "accepted"]
        rejected = [item for item in results if item[0] == "rejected"]

        assert len(accepted) == 1
        assert len(rejected) == 1
        assert rejected[0][1] == CommercialSeatReason.CAPACITY_REACHED.value

        with factory() as session:
            seats = session.query(CommercialSeatAssignment).filter(
                CommercialSeatAssignment.organization_id == ORG_ID,
                CommercialSeatAssignment.deployment_id == DEPLOYMENT_ID,
            ).all()

            assert len(seats) == 1
            assert seats[0].state == CommercialSeatState.ASSIGNED.value
            assert seats[0].user_id == accepted[0][1]
    finally:
        _cleanup(factory)
        engine.dispose()


def test_disabled_membership_is_reserved_effective_and_reenable_is_not_automatic():
    engine, factory = _engine_and_factory()
    _cleanup(factory)

    try:
        user_a, _ = _seed(factory, capacity=2)

        assert _assign(factory, user_a)[0] == "accepted"

        with factory() as session:
            membership = session.get(
                UserOrganizationMembership,
                (user_a, ORG_ID),
            )
            membership.is_enabled = False
            session.commit()

        with CommercialEntitlementUnitOfWork(factory) as uow:
            evaluation = evaluate_seat(
                uow,
                organization_id=ORG_ID,
                deployment_id=DEPLOYMENT_ID,
                user_id=user_a,
            )
            assert evaluation.executable is False
            assert evaluation.effective_state is CommercialSeatState.RESERVED
            assert evaluation.reason_code == CommercialSeatReason.SEAT_RESERVED.value
            uow.rollback()

        # Materialize RESERVED as the bounded reconciliation/admin-read
        # representation permitted by IDS.
        with factory() as session:
            seat = session.get(
                CommercialSeatAssignment,
                (ORG_ID, DEPLOYMENT_ID, user_a),
            )
            seat.state = CommercialSeatState.RESERVED.value
            session.commit()

        with factory() as session:
            membership = session.get(
                UserOrganizationMembership,
                (user_a, ORG_ID),
            )
            membership.is_enabled = True
            session.commit()

        # Re-enabling canonical membership alone must not restore execution.
        with CommercialEntitlementUnitOfWork(factory) as uow:
            evaluation = evaluate_seat(
                uow,
                organization_id=ORG_ID,
                deployment_id=DEPLOYMENT_ID,
                user_id=user_a,
            )
            assert evaluation.executable is False
            assert evaluation.stored_state is CommercialSeatState.RESERVED
            assert evaluation.reason_code == CommercialSeatReason.SEAT_RESERVED.value
            uow.rollback()

        # Explicit accepted seat mutation reactivates it.
        assert _assign(factory, user_a) == ("accepted", user_a)

        with CommercialEntitlementUnitOfWork(factory) as uow:
            evaluation = evaluate_seat(
                uow,
                organization_id=ORG_ID,
                deployment_id=DEPLOYMENT_ID,
                user_id=user_a,
            )
            assert evaluation.executable is True
            assert evaluation.stored_state is CommercialSeatState.ASSIGNED
            uow.rollback()
    finally:
        _cleanup(factory)
        engine.dispose()


def test_release_deletes_only_commercial_seat_not_membership():
    engine, factory = _engine_and_factory()
    _cleanup(factory)

    try:
        user_a, _ = _seed(factory, capacity=2)
        assert _assign(factory, user_a)[0] == "accepted"

        with CommercialEntitlementUnitOfWork(factory) as uow:
            result = release_seat(
                uow,
                organization_id=ORG_ID,
                deployment_id=DEPLOYMENT_ID,
                user_id=user_a,
            )
            uow.commit()

        assert result.state is None

        with factory() as session:
            assert session.get(
                CommercialSeatAssignment,
                (ORG_ID, DEPLOYMENT_ID, user_a),
            ) is None

            membership = session.get(
                UserOrganizationMembership,
                (user_a, ORG_ID),
            )
            assert membership is not None
            assert membership.is_enabled is True
    finally:
        _cleanup(factory)
        engine.dispose()


def test_capacity_reduction_retained_selection_is_exact_replacement():
    engine, factory = _engine_and_factory()
    _cleanup(factory)

    try:
        user_a, user_b = _seed(factory, capacity=2)

        assert _assign(factory, user_a)[0] == "accepted"
        assert _assign(factory, user_b)[0] == "accepted"

        # Simulate an accepted higher entitlement revision reducing capacity.
        # Activation behavior itself is qualified in B2; this test isolates the
        # B3 seat-state contract after the accepted capacity change.
        with factory() as session:
            state = session.get(
                CommercialEntitlementState,
                (ORG_ID, DEPLOYMENT_ID),
            )
            state.seat_capacity = 1
            state.accepted_revision = 2
            session.commit()

        # Before explicit remediation no ordinary ASSIGNED seat may execute.
        with CommercialEntitlementUnitOfWork(factory) as uow:
            eval_a = evaluate_seat(
                uow,
                organization_id=ORG_ID,
                deployment_id=DEPLOYMENT_ID,
                user_id=user_a,
            )
            eval_b = evaluate_seat(
                uow,
                organization_id=ORG_ID,
                deployment_id=DEPLOYMENT_ID,
                user_id=user_b,
            )
            assert eval_a.executable is False
            assert eval_b.executable is False
            assert eval_a.reason_code == CommercialSeatReason.OVER_CAPACITY.value
            assert eval_b.reason_code == CommercialSeatReason.OVER_CAPACITY.value
            uow.rollback()

        # First exact retained selection: A only.
        with CommercialEntitlementUnitOfWork(factory) as uow:
            status = retain_seats(
                uow,
                organization_id=ORG_ID,
                deployment_id=DEPLOYMENT_ID,
                retained_user_ids=[user_a],
                actor_user_id=None,
                observed_now=NOW,
            )
            uow.commit()

        assert status.over_capacity is True
        assert status.unresolved is False
        assert status.consuming_count == 2
        assert status.capacity == 1

        with CommercialEntitlementUnitOfWork(factory) as uow:
            eval_a = evaluate_seat(
                uow,
                organization_id=ORG_ID,
                deployment_id=DEPLOYMENT_ID,
                user_id=user_a,
            )
            eval_b = evaluate_seat(
                uow,
                organization_id=ORG_ID,
                deployment_id=DEPLOYMENT_ID,
                user_id=user_b,
            )
            assert eval_a.executable is True
            assert eval_a.stored_state is CommercialSeatState.RETAINED
            assert eval_b.executable is False
            assert eval_b.stored_state is CommercialSeatState.ASSIGNED
            assert eval_b.reason_code == CommercialSeatReason.OVER_CAPACITY.value
            uow.rollback()

        # Replace the exact retained set with B only. A MUST be demoted;
        # retained selections must never accumulate across submissions.
        with CommercialEntitlementUnitOfWork(factory) as uow:
            status = retain_seats(
                uow,
                organization_id=ORG_ID,
                deployment_id=DEPLOYMENT_ID,
                retained_user_ids=[user_b],
                actor_user_id=None,
                observed_now=NOW,
            )
            uow.commit()

        assert status.over_capacity is True
        assert status.unresolved is False

        with CommercialEntitlementUnitOfWork(factory) as uow:
            eval_a = evaluate_seat(
                uow,
                organization_id=ORG_ID,
                deployment_id=DEPLOYMENT_ID,
                user_id=user_a,
            )
            eval_b = evaluate_seat(
                uow,
                organization_id=ORG_ID,
                deployment_id=DEPLOYMENT_ID,
                user_id=user_b,
            )

            assert eval_a.stored_state is CommercialSeatState.ASSIGNED
            assert eval_a.executable is False
            assert eval_a.reason_code == CommercialSeatReason.OVER_CAPACITY.value

            assert eval_b.stored_state is CommercialSeatState.RETAINED
            assert eval_b.executable is True
            assert eval_b.reason_code is None
            uow.rollback()

        # Releasing the non-retained consuming seat resolves over-capacity
        # without deleting or altering canonical membership.
        with CommercialEntitlementUnitOfWork(factory) as uow:
            release_seat(
                uow,
                organization_id=ORG_ID,
                deployment_id=DEPLOYMENT_ID,
                user_id=user_a,
            )
            uow.commit()

        with CommercialEntitlementUnitOfWork(factory) as uow:
            eval_b = evaluate_seat(
                uow,
                organization_id=ORG_ID,
                deployment_id=DEPLOYMENT_ID,
                user_id=user_b,
            )
            assert eval_b.executable is True
            assert eval_b.stored_state is CommercialSeatState.RETAINED
            uow.rollback()

        with factory() as session:
            membership_a = session.get(
                UserOrganizationMembership,
                (user_a, ORG_ID),
            )
            membership_b = session.get(
                UserOrganizationMembership,
                (user_b, ORG_ID),
            )
            assert membership_a is not None
            assert membership_b is not None
            assert membership_a.is_enabled is True
            assert membership_b.is_enabled is True

    finally:
        _cleanup(factory)
        engine.dispose()


def test_empty_exact_retained_set_remains_fail_closed_and_unresolved():
    engine, factory = _engine_and_factory()
    _cleanup(factory)

    try:
        user_a, user_b = _seed(factory, capacity=2)

        assert _assign(factory, user_a)[0] == "accepted"
        assert _assign(factory, user_b)[0] == "accepted"

        with factory() as session:
            state = session.get(
                CommercialEntitlementState,
                (ORG_ID, DEPLOYMENT_ID),
            )
            state.seat_capacity = 1
            state.accepted_revision = 2
            session.commit()

        # An exact empty retained set is contract-valid because its size is
        # <= capacity. It selects no runtime winner, so remediation remains
        # unresolved and every consuming seat must stay non-executable.
        with CommercialEntitlementUnitOfWork(factory) as uow:
            status = retain_seats(
                uow,
                organization_id=ORG_ID,
                deployment_id=DEPLOYMENT_ID,
                retained_user_ids=[],
                actor_user_id=None,
                observed_now=NOW,
            )
            uow.commit()

        assert status.over_capacity is True
        assert status.unresolved is True
        assert status.consuming_count == 2
        assert status.capacity == 1

        with CommercialEntitlementUnitOfWork(factory) as uow:
            eval_a = evaluate_seat(
                uow,
                organization_id=ORG_ID,
                deployment_id=DEPLOYMENT_ID,
                user_id=user_a,
            )
            eval_b = evaluate_seat(
                uow,
                organization_id=ORG_ID,
                deployment_id=DEPLOYMENT_ID,
                user_id=user_b,
            )
            status = over_capacity_status(
                uow,
                organization_id=ORG_ID,
                deployment_id=DEPLOYMENT_ID,
            )

            assert eval_a.stored_state is CommercialSeatState.ASSIGNED
            assert eval_b.stored_state is CommercialSeatState.ASSIGNED
            assert eval_a.executable is False
            assert eval_b.executable is False
            assert eval_a.reason_code == CommercialSeatReason.OVER_CAPACITY.value
            assert eval_b.reason_code == CommercialSeatReason.OVER_CAPACITY.value
            assert status.over_capacity is True
            assert status.unresolved is True
            uow.rollback()

    finally:
        _cleanup(factory)
        engine.dispose()
