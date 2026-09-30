"""PATCH-059 commercial entitlement persistence and deterministic locking."""

from __future__ import annotations

import hashlib
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.commercial_entitlement import (
    CommercialEntitlementActivation,
    CommercialEntitlementState,
    CommercialSeatAssignment,
)
from app.models.organization import UserOrganizationMembership


# Domain-separated, versioned namespace. This string is part of the
# PATCH-059 persisted concurrency contract and must not be changed casually.
_COMMERCIAL_LOCK_NAMESPACE = b"SATCO:PATCH-059:commercial-entitlement-lock:v1\0"


def commercial_advisory_lock_key(
    organization_id: uuid.UUID,
    deployment_id: str,
) -> int:
    """Return the deterministic signed PostgreSQL bigint advisory-lock key.

    Contract:
      SHA-256(
          fixed PATCH-059 namespace
          || canonical 16-byte Organization UUID
          || SHA-256(UTF-8 deployment identifier)
      )

    The first 8 digest bytes are interpreted as a signed big-endian int64.
    Python hash() is deliberately prohibited.
    """
    if not isinstance(organization_id, uuid.UUID):
        raise TypeError("organization_id must be UUID")
    if not isinstance(deployment_id, str) or not deployment_id:
        raise ValueError("deployment_id must be a non-empty string")

    deployment_digest = hashlib.sha256(
        deployment_id.encode("utf-8")
    ).digest()

    material = (
        _COMMERCIAL_LOCK_NAMESPACE
        + organization_id.bytes
        + deployment_digest
    )
    digest = hashlib.sha256(material).digest()

    return int.from_bytes(digest[:8], byteorder="big", signed=True)


class CommercialEntitlementRepository:
    """Session-bound persistence adapter for PATCH-059 commercial state."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def acquire_commercial_lock(
        self,
        *,
        organization_id: uuid.UUID,
        deployment_id: str,
    ) -> int:
        """Acquire the transaction-scoped PostgreSQL commercial lock."""
        lock_key = commercial_advisory_lock_key(
            organization_id,
            deployment_id,
        )
        self.session.execute(
            select(func.pg_advisory_xact_lock(lock_key))
        )
        return lock_key

    def get_state(
        self,
        *,
        organization_id: uuid.UUID,
        deployment_id: str,
        lock: bool = False,
    ) -> CommercialEntitlementState | None:
        statement = select(CommercialEntitlementState).where(
            CommercialEntitlementState.organization_id == organization_id,
            CommercialEntitlementState.deployment_id == deployment_id,
        )
        if lock:
            statement = statement.with_for_update()
        return self.session.scalar(statement)

    def lock_state_or_acquire_initial_lock(
        self,
        *,
        organization_id: uuid.UUID,
        deployment_id: str,
    ) -> CommercialEntitlementState | None:
        """Serialize existing and first-activation mutation paths.

        Existing state is protected by SELECT ... FOR UPDATE.

        When the state does not yet exist, a deterministic transaction-scoped
        advisory lock is acquired and the state is re-read under FOR UPDATE.
        """
        state = self.get_state(
            organization_id=organization_id,
            deployment_id=deployment_id,
            lock=True,
        )
        if state is not None:
            return state

        self.acquire_commercial_lock(
            organization_id=organization_id,
            deployment_id=deployment_id,
        )

        return self.get_state(
            organization_id=organization_id,
            deployment_id=deployment_id,
            lock=True,
        )

    def add_state(
        self,
        state: CommercialEntitlementState,
    ) -> CommercialEntitlementState:
        self.session.add(state)
        self.session.flush()
        return state

    def add_activation(
        self,
        activation: CommercialEntitlementActivation,
    ) -> CommercialEntitlementActivation:
        self.session.add(activation)
        self.session.flush()
        return activation

    def get_seat(
        self,
        *,
        organization_id: uuid.UUID,
        deployment_id: str,
        user_id: int,
        lock: bool = False,
    ) -> CommercialSeatAssignment | None:
        statement = select(CommercialSeatAssignment).where(
            CommercialSeatAssignment.organization_id == organization_id,
            CommercialSeatAssignment.deployment_id == deployment_id,
            CommercialSeatAssignment.user_id == user_id,
        )
        if lock:
            statement = statement.with_for_update()
        return self.session.scalar(statement)

    def consuming_seats(
        self,
        *,
        organization_id: uuid.UUID,
        deployment_id: str,
    ) -> int:
        statement = select(func.count()).select_from(
            CommercialSeatAssignment
        ).where(
            CommercialSeatAssignment.organization_id == organization_id,
            CommercialSeatAssignment.deployment_id == deployment_id,
        )
        return int(self.session.scalar(statement) or 0)

    def list_seats(
        self,
        *,
        organization_id: uuid.UUID,
        deployment_id: str,
        lock: bool = False,
    ) -> tuple[CommercialSeatAssignment, ...]:
        statement = (
            select(CommercialSeatAssignment)
            .where(
                CommercialSeatAssignment.organization_id == organization_id,
                CommercialSeatAssignment.deployment_id == deployment_id,
            )
            .order_by(CommercialSeatAssignment.user_id)
        )
        if lock:
            statement = statement.with_for_update()
        return tuple(self.session.scalars(statement))

    def get_membership(
        self,
        *,
        organization_id: uuid.UUID,
        user_id: int,
        lock: bool = False,
    ) -> UserOrganizationMembership | None:
        statement = select(UserOrganizationMembership).where(
            UserOrganizationMembership.organization_id == organization_id,
            UserOrganizationMembership.user_id == user_id,
        )
        if lock:
            statement = statement.with_for_update()
        return self.session.scalar(statement)

    def add_seat(
        self,
        seat: CommercialSeatAssignment,
    ) -> CommercialSeatAssignment:
        self.session.add(seat)
        self.session.flush()
        return seat

    def delete_seat(self, seat: CommercialSeatAssignment) -> None:
        self.session.delete(seat)
        self.session.flush()
