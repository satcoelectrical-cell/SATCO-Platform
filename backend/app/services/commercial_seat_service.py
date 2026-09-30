"""PATCH-059 commercial seat lifecycle and capacity rules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Iterable
from uuid import UUID

from app.commercial_entitlements.state import CommercialEntitlementState as EffectiveEntitlementState
from app.models.commercial_entitlement import CommercialSeatAssignment
from app.repositories.commercial_entitlement_unit_of_work import (
    CommercialEntitlementUnitOfWork,
    require_repository,
)


class CommercialSeatState(StrEnum):
    ASSIGNED = "ASSIGNED"
    RESERVED = "RESERVED"
    RETAINED = "RETAINED"


class CommercialSeatReason(StrEnum):
    ENTITLEMENT_MISSING = "entitlement_missing"
    ENTITLEMENT_NOT_ACTIVE = "entitlement_not_active"
    MEMBERSHIP_REQUIRED = "membership_required"
    MEMBERSHIP_DISABLED = "membership_disabled"
    SEAT_ALREADY_ASSIGNED = "seat_already_assigned"
    SEAT_REQUIRED = "seat_required"
    SEAT_RESERVED = "seat_reserved"
    CAPACITY_REACHED = "capacity_reached"
    OVER_CAPACITY = "over_capacity"
    INVALID_RETAINED_SET = "invalid_retained_set"


class CommercialSeatError(RuntimeError):
    def __init__(self, reason_code: CommercialSeatReason | str) -> None:
        self.reason_code = str(reason_code)
        super().__init__(self.reason_code)


@dataclass(frozen=True)
class SeatMutationResult:
    user_id: int
    state: CommercialSeatState | None
    consuming_count: int
    capacity: int


@dataclass(frozen=True)
class SeatEvaluation:
    user_id: int
    stored_state: CommercialSeatState | None
    effective_state: CommercialSeatState | None
    executable: bool
    reason_code: str | None


@dataclass(frozen=True)
class OverCapacityStatus:
    consuming_count: int
    capacity: int
    over_capacity: bool
    unresolved: bool


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("server time must be timezone-aware")
    return value.astimezone(timezone.utc)


def _effective_entitlement_state(state, now: datetime) -> EffectiveEntitlementState:
    if state.time_untrusted_at is not None:
        return EffectiveEntitlementState.TIME_UNTRUSTED
    if now < state.not_before:
        return EffectiveEntitlementState.INVALID_OR_UNAVAILABLE
    if now <= state.valid_until:
        return EffectiveEntitlementState.ACTIVE
    if now <= state.grace_until:
        return EffectiveEntitlementState.GRACE
    return EffectiveEntitlementState.EXPIRED


def _locked_state(
    uow: CommercialEntitlementUnitOfWork,
    *,
    organization_id: UUID,
    deployment_id: str,
):
    repository = require_repository(uow)
    state = repository.get_state(
        organization_id=organization_id,
        deployment_id=deployment_id,
        lock=True,
    )
    if state is None:
        raise CommercialSeatError(CommercialSeatReason.ENTITLEMENT_MISSING)
    return repository, state


def over_capacity_status(
    uow: CommercialEntitlementUnitOfWork,
    *,
    organization_id: UUID,
    deployment_id: str,
) -> OverCapacityStatus:
    repository, state = _locked_state(
        uow,
        organization_id=organization_id,
        deployment_id=deployment_id,
    )
    seats = repository.list_seats(
        organization_id=organization_id,
        deployment_id=deployment_id,
        lock=True,
    )
    count = len(seats)
    over = count > state.seat_capacity

    # While over capacity, execution remains unresolved until an explicit
    # retained set has been selected. Once count <= capacity, ordinary
    # seat states are again unambiguous.
    unresolved = over and not any(
        seat.state == CommercialSeatState.RETAINED.value for seat in seats
    )

    return OverCapacityStatus(
        consuming_count=count,
        capacity=state.seat_capacity,
        over_capacity=over,
        unresolved=unresolved,
    )


def assign_seat(
    uow: CommercialEntitlementUnitOfWork,
    *,
    organization_id: UUID,
    deployment_id: str,
    user_id: int,
    actor_user_id: int | None,
    observed_now: datetime,
) -> SeatMutationResult:
    now = _utc(observed_now)
    repository, state = _locked_state(
        uow,
        organization_id=organization_id,
        deployment_id=deployment_id,
    )

    if _effective_entitlement_state(state, now) is not EffectiveEntitlementState.ACTIVE:
        raise CommercialSeatError(CommercialSeatReason.ENTITLEMENT_NOT_ACTIVE)

    membership = repository.get_membership(
        organization_id=organization_id,
        user_id=user_id,
        lock=True,
    )
    if membership is None:
        raise CommercialSeatError(CommercialSeatReason.MEMBERSHIP_REQUIRED)
    if not membership.is_enabled:
        raise CommercialSeatError(CommercialSeatReason.MEMBERSHIP_DISABLED)

    existing = repository.get_seat(
        organization_id=organization_id,
        deployment_id=deployment_id,
        user_id=user_id,
        lock=True,
    )

    count = repository.consuming_seats(
        organization_id=organization_id,
        deployment_id=deployment_id,
    )

    if existing is not None:
        # RESERVED never auto-restores merely because membership was enabled.
        # Explicit assignment is the accepted reactivation path.
        if existing.state == CommercialSeatState.RESERVED.value:
            if count > state.seat_capacity:
                raise CommercialSeatError(CommercialSeatReason.OVER_CAPACITY)
            existing.state = CommercialSeatState.ASSIGNED.value
            existing.updated_by_user_id = actor_user_id
            existing.updated_at = now
            repository.session.flush()
            return SeatMutationResult(
                user_id=user_id,
                state=CommercialSeatState.ASSIGNED,
                consuming_count=count,
                capacity=state.seat_capacity,
            )

        raise CommercialSeatError(CommercialSeatReason.SEAT_ALREADY_ASSIGNED)

    if count >= state.seat_capacity:
        reason = (
            CommercialSeatReason.OVER_CAPACITY
            if count > state.seat_capacity
            else CommercialSeatReason.CAPACITY_REACHED
        )
        raise CommercialSeatError(reason)

    seat = CommercialSeatAssignment(
        organization_id=organization_id,
        deployment_id=deployment_id,
        user_id=user_id,
        state=CommercialSeatState.ASSIGNED.value,
        assigned_by_user_id=actor_user_id,
        updated_by_user_id=actor_user_id,
    )
    repository.add_seat(seat)

    return SeatMutationResult(
        user_id=user_id,
        state=CommercialSeatState.ASSIGNED,
        consuming_count=count + 1,
        capacity=state.seat_capacity,
    )


def release_seat(
    uow: CommercialEntitlementUnitOfWork,
    *,
    organization_id: UUID,
    deployment_id: str,
    user_id: int,
) -> SeatMutationResult:
    repository, state = _locked_state(
        uow,
        organization_id=organization_id,
        deployment_id=deployment_id,
    )
    seat = repository.get_seat(
        organization_id=organization_id,
        deployment_id=deployment_id,
        user_id=user_id,
        lock=True,
    )
    if seat is None:
        raise CommercialSeatError(CommercialSeatReason.SEAT_REQUIRED)

    repository.delete_seat(seat)
    count = repository.consuming_seats(
        organization_id=organization_id,
        deployment_id=deployment_id,
    )

    return SeatMutationResult(
        user_id=user_id,
        state=None,
        consuming_count=count,
        capacity=state.seat_capacity,
    )


def evaluate_seat(
    uow: CommercialEntitlementUnitOfWork,
    *,
    organization_id: UUID,
    deployment_id: str,
    user_id: int,
) -> SeatEvaluation:
    repository, state = _locked_state(
        uow,
        organization_id=organization_id,
        deployment_id=deployment_id,
    )
    seat = repository.get_seat(
        organization_id=organization_id,
        deployment_id=deployment_id,
        user_id=user_id,
    )
    if seat is None:
        return SeatEvaluation(
            user_id=user_id,
            stored_state=None,
            effective_state=None,
            executable=False,
            reason_code=CommercialSeatReason.SEAT_REQUIRED.value,
        )

    stored = CommercialSeatState(seat.state)
    membership = repository.get_membership(
        organization_id=organization_id,
        user_id=user_id,
    )

    seats = repository.list_seats(
        organization_id=organization_id,
        deployment_id=deployment_id,
    )
    count = len(seats)

    if count > state.seat_capacity:
        if stored is not CommercialSeatState.RETAINED:
            return SeatEvaluation(
                user_id=user_id,
                stored_state=stored,
                effective_state=stored,
                executable=False,
                reason_code=CommercialSeatReason.OVER_CAPACITY.value,
            )

    if membership is None or not membership.is_enabled:
        return SeatEvaluation(
            user_id=user_id,
            stored_state=stored,
            effective_state=CommercialSeatState.RESERVED,
            executable=False,
            reason_code=CommercialSeatReason.SEAT_RESERVED.value,
        )

    if stored is CommercialSeatState.RESERVED:
        return SeatEvaluation(
            user_id=user_id,
            stored_state=stored,
            effective_state=CommercialSeatState.RESERVED,
            executable=False,
            reason_code=CommercialSeatReason.SEAT_RESERVED.value,
        )

    return SeatEvaluation(
        user_id=user_id,
        stored_state=stored,
        effective_state=stored,
        executable=True,
        reason_code=None,
    )


def retain_seats(
    uow: CommercialEntitlementUnitOfWork,
    *,
    organization_id: UUID,
    deployment_id: str,
    retained_user_ids: Iterable[int],
    actor_user_id: int | None,
    observed_now: datetime,
) -> OverCapacityStatus:
    now = _utc(observed_now)
    repository, state = _locked_state(
        uow,
        organization_id=organization_id,
        deployment_id=deployment_id,
    )
    seats = repository.list_seats(
        organization_id=organization_id,
        deployment_id=deployment_id,
        lock=True,
    )
    count = len(seats)

    if count <= state.seat_capacity:
        raise CommercialSeatError(CommercialSeatReason.INVALID_RETAINED_SET)

    retained = tuple(sorted(set(retained_user_ids)))
    if len(retained) > state.seat_capacity:
        raise CommercialSeatError(CommercialSeatReason.INVALID_RETAINED_SET)

    existing_ids = {seat.user_id for seat in seats}
    if not set(retained).issubset(existing_ids):
        raise CommercialSeatError(CommercialSeatReason.INVALID_RETAINED_SET)

    retained_set = set(retained)

    # The submitted retained_user_ids are an exact replacement set, not an
    # additive selection. Every consuming row is therefore reconciled under
    # the same commercial-state transaction.
    for seat in seats:
        membership = repository.get_membership(
            organization_id=organization_id,
            user_id=seat.user_id,
            lock=True,
        )

        if seat.user_id in retained_set:
            if membership is None or not membership.is_enabled:
                raise CommercialSeatError(
                    CommercialSeatReason.INVALID_RETAINED_SET
                )
            next_state = CommercialSeatState.RETAINED
        elif membership is None or not membership.is_enabled:
            next_state = CommercialSeatState.RESERVED
        else:
            next_state = CommercialSeatState.ASSIGNED

        seat.state = next_state.value
        seat.updated_by_user_id = actor_user_id
        seat.updated_at = now

    repository.session.flush()

    return OverCapacityStatus(
        consuming_count=count,
        capacity=state.seat_capacity,
        over_capacity=True,
        unresolved=not any(
            seat.state == CommercialSeatState.RETAINED.value
            for seat in seats
        ),
    )
