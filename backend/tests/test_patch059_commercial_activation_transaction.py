import base64
import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import sessionmaker

from app.commercial_entitlements.canonical import (
    EntitlementPayload,
    canonical_payload_bytes,
    parse_envelope,
)
from app.commercial_entitlements.crypto import TrustKey, TrustStore
from app.core.database import DATABASE_URL
from app.models.commercial_entitlement import (
    CommercialEntitlementActivation,
    CommercialEntitlementState,
)
from app.models.organization import Organization
from app.repositories.commercial_entitlement_unit_of_work import (
    CommercialEntitlementUnitOfWork,
)
from app.services.commercial_entitlement_service import (
    RevisionDecision,
    activate_entitlement,
)


UTC = timezone.utc
ORG = UUID("05900000-0000-4000-8000-000000000001")
DEPLOYMENT = "patch059-b2-transaction-test"
NOW = datetime(2026, 9, 30, 6, 0, tzinfo=UTC)

ENTITLEMENT_1 = UUID("05900000-0000-4000-8000-000000000101")
ENTITLEMENT_2 = UUID("05900000-0000-4000-8000-000000000102")
ENTITLEMENT_CONFLICT = UUID(
    "05900000-0000-4000-8000-000000000103"
)


def _b64u(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _crypto():
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    store = TrustStore(
        schema="satco.commercial-entitlement-trust/v1",
        keys=(
            TrustKey(
                key_id="patch059-b2-test-key",
                algorithm="Ed25519",
                public_key_base64url=_b64u(public),
                not_before=NOW - timedelta(days=1),
                revoked_at=None,
            ),
        ),
    )
    return private, store


def _payload(
    *,
    entitlement_id: UUID,
    revision: int,
    seat_capacity: int = 5,
) -> EntitlementPayload:
    return EntitlementPayload(
        schema_version=1,
        entitlement_id=entitlement_id,
        revision=revision,
        organization_id=ORG,
        deployment_id=DEPLOYMENT,
        issuer="SATCO",
        issued_at=NOW,
        not_before=NOW,
        valid_until=NOW + timedelta(days=20),
        grace_until=NOW + timedelta(days=30),
        package_keys=("electrical", "instrumentation"),
        seat_capacity=seat_capacity,
        support_until=None,
        baseline_release_sequence=1,
        max_release_sequence=10,
    )


def _envelope(
    private: Ed25519PrivateKey,
    payload: EntitlementPayload,
):
    signature = private.sign(canonical_payload_bytes(payload))
    raw = json.dumps(
        {
            "schema": "satco.commercial-entitlement/v1",
            "key_id": "patch059-b2-test-key",
            "payload": json.loads(canonical_payload_bytes(payload)),
            "signature": _b64u(signature),
        },
        separators=(",", ":"),
    ).encode()
    return parse_envelope(raw)


def _activate(
    factory,
    *,
    envelope,
    store,
    observed_now,
):
    with CommercialEntitlementUnitOfWork(factory) as uow:
        result = activate_entitlement(
            uow=uow,
            envelope=envelope,
            trust_store=store,
            expected_organization_id=ORG,
            expected_deployment_id=DEPLOYMENT,
            actor_user_id=None,
            correlation_id="patch059-b2-qualification",
            observed_now=observed_now,
        )
        uow.commit()
        return result


def _cleanup(engine):
    with engine.begin() as connection:
        connection.execute(
            delete(CommercialEntitlementActivation).where(
                CommercialEntitlementActivation.organization_id == ORG,
                CommercialEntitlementActivation.deployment_id == DEPLOYMENT,
            )
        )
        connection.execute(
            delete(CommercialEntitlementState).where(
                CommercialEntitlementState.organization_id == ORG,
                CommercialEntitlementState.deployment_id == DEPLOYMENT,
            )
        )
        connection.execute(
            delete(Organization).where(Organization.id == ORG)
        )


def test_transactional_activation_revision_and_time_durability():
    engine = create_engine(DATABASE_URL)
    factory = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    _cleanup(engine)

    try:
        with engine.begin() as connection:
            connection.execute(
                Organization.__table__.insert().values(
                    id=ORG,
                    name="PATCH-059 B2 Qualification",
                    slug="patch059-b2-qualification",
                    is_active=True,
                )
            )

        private, store = _crypto()

        initial = _payload(
            entitlement_id=ENTITLEMENT_1,
            revision=1,
        )
        result = _activate(
            factory,
            envelope=_envelope(private, initial),
            store=store,
            observed_now=NOW + timedelta(hours=1),
        )

        assert result.accepted is True
        assert result.decision is RevisionDecision.INITIAL
        assert result.state_advanced is True

        successor = _payload(
            entitlement_id=ENTITLEMENT_2,
            revision=2,
            seat_capacity=7,
        )
        result = _activate(
            factory,
            envelope=_envelope(private, successor),
            store=store,
            observed_now=NOW + timedelta(hours=2),
        )

        assert result.accepted is True
        assert result.decision is RevisionDecision.SUCCESSOR
        assert result.state_advanced is True

        result = _activate(
            factory,
            envelope=_envelope(private, successor),
            store=store,
            observed_now=NOW + timedelta(hours=2, minutes=1),
        )

        assert result.accepted is True
        assert result.decision is RevisionDecision.IDEMPOTENT
        assert result.state_advanced is False

        rollback = _payload(
            entitlement_id=ENTITLEMENT_1,
            revision=1,
        )
        result = _activate(
            factory,
            envelope=_envelope(private, rollback),
            store=store,
            observed_now=NOW + timedelta(hours=2, minutes=2),
        )

        assert result.accepted is False
        assert result.reason_code == "rollback_detected"
        assert result.state_advanced is False

        conflict = _payload(
            entitlement_id=ENTITLEMENT_CONFLICT,
            revision=2,
            seat_capacity=9,
        )
        result = _activate(
            factory,
            envelope=_envelope(private, conflict),
            store=store,
            observed_now=NOW + timedelta(hours=2, minutes=3),
        )

        assert result.accepted is False
        assert result.reason_code == "same_revision_conflict"
        assert result.state_advanced is False

        with factory() as session:
            state = session.scalar(
                select(CommercialEntitlementState).where(
                    CommercialEntitlementState.organization_id == ORG,
                    CommercialEntitlementState.deployment_id == DEPLOYMENT,
                )
            )

            assert state is not None
            assert state.accepted_revision == 2
            assert state.entitlement_id == ENTITLEMENT_2
            assert state.seat_capacity == 7

            reasons = tuple(
                session.scalars(
                    select(
                        CommercialEntitlementActivation.reason_code
                    )
                    .where(
                        CommercialEntitlementActivation.organization_id
                        == ORG,
                        CommercialEntitlementActivation.deployment_id
                        == DEPLOYMENT,
                    )
                    .order_by(
                        CommercialEntitlementActivation.accepted_at,
                        CommercialEntitlementActivation.id,
                    )
                )
            )

            assert "rollback_detected" in reasons
            assert "same_revision_conflict" in reasons

            trusted_before = state.last_trusted_time

        backward_now = trusted_before - timedelta(
            minutes=5,
            seconds=1,
        )

        result = _activate(
            factory,
            envelope=_envelope(private, successor),
            store=store,
            observed_now=backward_now,
        )

        assert result.accepted is False
        assert result.reason_code == "time_untrusted"
        assert result.state_advanced is False

        with factory() as session:
            state = session.scalar(
                select(CommercialEntitlementState).where(
                    CommercialEntitlementState.organization_id == ORG,
                    CommercialEntitlementState.deployment_id == DEPLOYMENT,
                )
            )

            assert state is not None
            assert state.accepted_revision == 2
            assert state.entitlement_id == ENTITLEMENT_2
            assert state.seat_capacity == 7
            assert state.last_trusted_time == trusted_before
            assert state.time_untrusted_at == backward_now

            time_untrusted_history = session.scalar(
                select(CommercialEntitlementActivation)
                .where(
                    CommercialEntitlementActivation.organization_id
                    == ORG,
                    CommercialEntitlementActivation.deployment_id
                    == DEPLOYMENT,
                    CommercialEntitlementActivation.reason_code
                    == "time_untrusted",
                )
            )

            assert time_untrusted_history is not None

        later_result = _activate(
            factory,
            envelope=_envelope(private, successor),
            store=store,
            observed_now=trusted_before + timedelta(hours=1),
        )

        assert later_result.accepted is False
        assert later_result.reason_code == "time_untrusted"
        assert later_result.state_advanced is False

        with factory() as session:
            state = session.scalar(
                select(CommercialEntitlementState).where(
                    CommercialEntitlementState.organization_id == ORG,
                    CommercialEntitlementState.deployment_id == DEPLOYMENT,
                )
            )

            assert state is not None
            assert state.time_untrusted_at == backward_now
            assert state.accepted_revision == 2
            assert state.entitlement_id == ENTITLEMENT_2

    finally:
        _cleanup(engine)
        engine.dispose()


def test_concurrent_successors_preserve_highest_revision():
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    engine = create_engine(DATABASE_URL)
    factory = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    _cleanup(engine)

    try:
        with engine.begin() as connection:
            connection.execute(
                Organization.__table__.insert().values(
                    id=ORG,
                    name="PATCH-059 B2 Concurrency Qualification",
                    slug="patch059-b2-concurrency-qualification",
                    is_active=True,
                )
            )

        private, store = _crypto()

        initial = _payload(
            entitlement_id=ENTITLEMENT_1,
            revision=1,
        )

        initial_result = _activate(
            factory,
            envelope=_envelope(private, initial),
            store=store,
            observed_now=NOW + timedelta(hours=1),
        )

        assert initial_result.accepted is True
        assert initial_result.decision is RevisionDecision.INITIAL

        revision_2_id = UUID(
            "05900000-0000-4000-8000-000000000202"
        )
        revision_3_id = UUID(
            "05900000-0000-4000-8000-000000000203"
        )

        revision_2 = _payload(
            entitlement_id=revision_2_id,
            revision=2,
            seat_capacity=6,
        )
        revision_3 = _payload(
            entitlement_id=revision_3_id,
            revision=3,
            seat_capacity=8,
        )

        envelope_2 = _envelope(private, revision_2)
        envelope_3 = _envelope(private, revision_3)

        barrier = Barrier(2)

        def candidate(envelope, observed_now):
            barrier.wait(timeout=5)

            return _activate(
                factory,
                envelope=envelope,
                store=store,
                observed_now=observed_now,
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_2 = executor.submit(
                candidate,
                envelope_2,
                NOW + timedelta(hours=2),
            )
            future_3 = executor.submit(
                candidate,
                envelope_3,
                NOW + timedelta(hours=2),
            )

            result_2 = future_2.result(timeout=10)
            result_3 = future_3.result(timeout=10)

        results = {
            result_2.revision: result_2,
            result_3.revision: result_3,
        }

        assert results[3].accepted is True
        assert results[3].decision is RevisionDecision.SUCCESSOR

        assert results[2].decision in {
            RevisionDecision.SUCCESSOR,
            RevisionDecision.ROLLBACK_DETECTED,
        }

        if results[2].decision is RevisionDecision.SUCCESSOR:
            assert results[2].accepted is True
        else:
            assert results[2].accepted is False
            assert results[2].reason_code == "rollback_detected"

        with factory() as session:
            state = session.scalar(
                select(CommercialEntitlementState).where(
                    CommercialEntitlementState.organization_id == ORG,
                    CommercialEntitlementState.deployment_id
                    == DEPLOYMENT,
                )
            )

            assert state is not None
            assert state.accepted_revision == 3
            assert state.entitlement_id == revision_3_id
            assert state.seat_capacity == 8

            accepted_revisions = tuple(
                session.scalars(
                    select(
                        CommercialEntitlementActivation.revision
                    ).where(
                        CommercialEntitlementActivation.organization_id
                        == ORG,
                        CommercialEntitlementActivation.deployment_id
                        == DEPLOYMENT,
                        CommercialEntitlementActivation.outcome
                        == "ACCEPTED",
                    )
                )
            )

            assert 1 in accepted_revisions
            assert 3 in accepted_revisions

    finally:
        _cleanup(engine)
        engine.dispose()
