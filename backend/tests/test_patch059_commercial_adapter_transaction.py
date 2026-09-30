from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import sessionmaker

from app.adapters.commercial_entitlement import CommercialEntitlementAdapter
from app.enums.discipline_package import EntitlementDecision, EntitlementOperation
from app.models.commercial_entitlement import (
    CommercialEntitlementState,
    CommercialSeatAssignment,
)
from app.models.organization import Organization, UserOrganizationMembership
from app.models.user import User
from app.ports.discipline_package import EntitlementRequest


UTC = timezone.utc
ORG_ID = UUID("05900000-0000-4000-8000-000000000041")
DEPLOYMENT_ID = "patch059-c1-adapter-transaction-test"
NOW = datetime(2026, 9, 30, 6, 0, tzinfo=UTC)
OBSERVED_NOW = NOW + timedelta(minutes=10)


def _engine_and_factory():
    import os

    url = os.environ["TEST_DATABASE_URL"]
    assert "127.0.0.1:55432" in url
    assert url.endswith("/satco_platform_patch02022_test")

    engine = create_engine(url, future=True)
    return engine, sessionmaker(
        bind=engine,
        expire_on_commit=False,
        future=True,
    )


def _cleanup(factory):
    with factory() as session:
        session.execute(
            delete(CommercialSeatAssignment).where(
                CommercialSeatAssignment.organization_id == ORG_ID,
                CommercialSeatAssignment.deployment_id == DEPLOYMENT_ID,
            )
        )
        session.execute(
            delete(CommercialEntitlementState).where(
                CommercialEntitlementState.organization_id == ORG_ID,
                CommercialEntitlementState.deployment_id == DEPLOYMENT_ID,
            )
        )

        memberships = (
            session.query(UserOrganizationMembership)
            .filter(UserOrganizationMembership.organization_id == ORG_ID)
            .all()
        )
        user_ids = [row.user_id for row in memberships]

        for membership in memberships:
            session.delete(membership)

        session.flush()

        if user_ids:
            session.query(User).filter(User.id.in_(user_ids)).delete(
                synchronize_session=False
            )

        session.execute(
            delete(Organization).where(Organization.id == ORG_ID)
        )
        session.commit()


def _seed(factory) -> int:
    with factory() as session:
        session.add(
            Organization(
                id=ORG_ID,
                name="PATCH-059 C1 Adapter Transaction Test",
                slug=f"patch059-c1-adapter-{uuid4().hex[:12]}",
                is_active=True,
            )
        )
        session.flush()

        token = uuid4().hex
        user = User(
            email=f"patch059-c1-adapter-{token}@example.test",
            username=f"p059c1_adapter_{token[:12]}",
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

        session.add(
            CommercialEntitlementState(
                organization_id=ORG_ID,
                deployment_id=DEPLOYMENT_ID,
                entitlement_id=uuid4(),
                accepted_revision=1,
                canonical_payload_digest="b" * 64,
                key_id="patch059-c1-key",
                issuer="patch059-test",
                issued_at=NOW - timedelta(days=2),
                not_before=NOW - timedelta(days=1),
                valid_until=NOW + timedelta(days=1),
                grace_until=NOW + timedelta(days=2),
                support_until=None,
                package_keys=["instrumentation"],
                seat_capacity=1,
                baseline_release_sequence=1,
                max_release_sequence=10,
                last_trusted_time=NOW,
                accepted_at=NOW,
                accepted_by_user_id=None,
                time_untrusted_at=None,
                version=1,
            )
        )
        session.flush()

        session.add(
            CommercialSeatAssignment(
                organization_id=ORG_ID,
                deployment_id=DEPLOYMENT_ID,
                user_id=user.id,
                state="ASSIGNED",
                assigned_at=NOW,
                assigned_by_user_id=None,
                updated_at=NOW,
                updated_by_user_id=None,
            )
        )

        session.commit()
        return user.id


def test_adapter_persists_trusted_checkpoint_only_after_real_seat_evaluation():
    engine, factory = _engine_and_factory()
    _cleanup(factory)

    try:
        user_id = _seed(factory)

        adapter = CommercialEntitlementAdapter(
            session_factory=factory,
            user_id=user_id,
            now=lambda: OBSERVED_NOW,
        )

        request = EntitlementRequest(
            trusted_organization_id=ORG_ID,
            trusted_deployment_id=DEPLOYMENT_ID,
            package_key="instrumentation",
            entitlement_key="instrumentation",
            operation=EntitlementOperation.EXECUTE,
        )

        decision = adapter.evaluate(request)

        # A premature checkpoint commit would terminate the UoW transaction.
        # evaluate_seat() then calls require_repository() and the adapter would
        # fail closed instead of reaching PERMITTED.
        assert decision is EntitlementDecision.PERMITTED

        with factory() as session:
            state = session.scalar(
                select(CommercialEntitlementState).where(
                    CommercialEntitlementState.organization_id == ORG_ID,
                    CommercialEntitlementState.deployment_id == DEPLOYMENT_ID,
                )
            )

            assert state is not None
            assert state.last_trusted_time == OBSERVED_NOW

            seat = session.get(
                CommercialSeatAssignment,
                (ORG_ID, DEPLOYMENT_ID, user_id),
            )
            assert seat is not None
            assert seat.state == "ASSIGNED"

            membership = session.get(
                UserOrganizationMembership,
                (user_id, ORG_ID),
            )
            assert membership is not None
            assert membership.is_enabled is True

    finally:
        _cleanup(factory)
        engine.dispose()
