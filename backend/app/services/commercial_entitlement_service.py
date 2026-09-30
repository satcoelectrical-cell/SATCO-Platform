"""PATCH-059 commercial entitlement activation and trusted-time rules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from uuid import UUID

from app.commercial_entitlements.canonical import EntitlementPayload


TRUSTED_TIME_BACKWARD_TOLERANCE = timedelta(minutes=5)


class RevisionDecision(StrEnum):
    INITIAL = "initial"
    SUCCESSOR = "successor"
    IDEMPOTENT = "idempotent"
    ROLLBACK_DETECTED = "rollback_detected"
    SAME_REVISION_CONFLICT = "same_revision_conflict"


class TrustedTimeDecision(StrEnum):
    TRUSTED = "trusted"
    TIME_UNTRUSTED = "time_untrusted"


@dataclass(frozen=True)
class RevisionEvaluation:
    decision: RevisionDecision
    should_advance_state: bool


@dataclass(frozen=True)
class TrustedTimeEvaluation:
    decision: TrustedTimeDecision
    effective_time: datetime
    should_persist_checkpoint: bool


def evaluate_revision(
    *,
    current_revision: int | None,
    current_entitlement_id: UUID | None,
    current_digest: str | None,
    incoming_revision: int,
    incoming_entitlement_id: UUID,
    incoming_digest: str,
) -> RevisionEvaluation:
    """Apply the frozen PATCH-059 revision/anti-rollback contract."""

    if incoming_revision < 1:
        raise ValueError("incoming revision must be positive")

    if current_revision is None:
        if current_entitlement_id is not None or current_digest is not None:
            raise ValueError("incomplete current revision state")

        return RevisionEvaluation(
            decision=RevisionDecision.INITIAL,
            should_advance_state=True,
        )

    if current_revision < 1:
        raise ValueError("current revision must be positive")

    if current_entitlement_id is None or current_digest is None:
        raise ValueError("incomplete current revision state")

    if incoming_revision < current_revision:
        return RevisionEvaluation(
            decision=RevisionDecision.ROLLBACK_DETECTED,
            should_advance_state=False,
        )

    if incoming_revision > current_revision:
        return RevisionEvaluation(
            decision=RevisionDecision.SUCCESSOR,
            should_advance_state=True,
        )

    if (
        incoming_entitlement_id == current_entitlement_id
        and incoming_digest == current_digest
    ):
        return RevisionEvaluation(
            decision=RevisionDecision.IDEMPOTENT,
            should_advance_state=False,
        )

    return RevisionEvaluation(
        decision=RevisionDecision.SAME_REVISION_CONFLICT,
        should_advance_state=False,
    )


def evaluate_trusted_time(
    *,
    observed_now: datetime,
    last_trusted_time: datetime | None,
    time_untrusted_at: datetime | None,
) -> TrustedTimeEvaluation:
    """Apply the durable monotonic trusted-time rule.

    Once TIME_UNTRUSTED has been recorded, ordinary evaluation cannot clear it.
    """

    observed_now = _utc(observed_now, "observed_now")

    if time_untrusted_at is not None:
        _utc(time_untrusted_at, "time_untrusted_at")

        effective = (
            observed_now
            if last_trusted_time is None
            else max(
                observed_now,
                _utc(last_trusted_time, "last_trusted_time"),
            )
        )

        return TrustedTimeEvaluation(
            decision=TrustedTimeDecision.TIME_UNTRUSTED,
            effective_time=effective,
            should_persist_checkpoint=False,
        )

    if last_trusted_time is None:
        return TrustedTimeEvaluation(
            decision=TrustedTimeDecision.TRUSTED,
            effective_time=observed_now,
            should_persist_checkpoint=True,
        )

    trusted = _utc(last_trusted_time, "last_trusted_time")

    if observed_now < trusted - TRUSTED_TIME_BACKWARD_TOLERANCE:
        return TrustedTimeEvaluation(
            decision=TrustedTimeDecision.TIME_UNTRUSTED,
            effective_time=trusted,
            should_persist_checkpoint=False,
        )

    effective = max(observed_now, trusted)

    return TrustedTimeEvaluation(
        decision=TrustedTimeDecision.TRUSTED,
        effective_time=effective,
        should_persist_checkpoint=observed_now > trusted,
    )


def entitlement_temporal_state(
    payload: EntitlementPayload,
    *,
    trusted_now: datetime,
) -> str:
    """Return the frozen ACTIVE/GRACE/EXPIRED temporal state."""

    now = _utc(trusted_now, "trusted_now")

    if now < payload.not_before:
        return "not_yet_valid"

    if now <= payload.valid_until:
        return "active"

    if now <= payload.grace_until:
        return "grace"

    return "expired"


def _utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")

    return value.astimezone(timezone.utc)


# ---------------------------------------------------------------------------
# Transactional activation
# ---------------------------------------------------------------------------

from app.commercial_entitlements.canonical import (
    EntitlementEnvelope,
    canonical_payload_digest,
)
from app.commercial_entitlements.crypto import TrustStore, verify_envelope
from app.models.commercial_entitlement import (
    CommercialEntitlementActivation,
    CommercialEntitlementState as CommercialEntitlementStateModel,
)
from app.repositories.commercial_entitlement_unit_of_work import (
    CommercialEntitlementUnitOfWork,
    require_repository,
)


@dataclass(frozen=True)
class ActivationResult:
    decision: RevisionDecision
    entitlement_id: UUID
    revision: int
    canonical_payload_digest: str
    temporal_state: str
    state_advanced: bool
    accepted: bool = True
    reason_code: str | None = None


class CommercialEntitlementActivationError(RuntimeError):
    """Stable fail-closed activation rejection."""

    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


def activate_entitlement(
    *,
    uow: CommercialEntitlementUnitOfWork,
    envelope: EntitlementEnvelope,
    trust_store: TrustStore,
    expected_organization_id: UUID,
    expected_deployment_id: str,
    actor_user_id: int | None,
    correlation_id: str | None,
    observed_now: datetime,
) -> ActivationResult:
    """Verify and atomically activate a PATCH-059 entitlement.

    The caller owns authorization/reauthentication. This service owns
    cryptographic verification, binding, anti-rollback, trusted time and
    persistence semantics.
    """

    now = _utc(observed_now, "observed_now")

    try:
        verify_envelope(
            envelope,
            trust_store,
            now=now,
        )
    except ValueError as exc:
        raise CommercialEntitlementActivationError(
            _verification_reason(exc)
        ) from exc

    payload = envelope.payload

    if payload.organization_id != expected_organization_id:
        raise CommercialEntitlementActivationError(
            "organization_mismatch"
        )

    if payload.deployment_id != expected_deployment_id:
        raise CommercialEntitlementActivationError(
            "deployment_mismatch"
        )

    if now < payload.not_before:
        raise CommercialEntitlementActivationError(
            "not_yet_valid"
        )

    repository = require_repository(uow)

    current = repository.lock_state_or_acquire_initial_lock(
        organization_id=expected_organization_id,
        deployment_id=expected_deployment_id,
    )

    digest = canonical_payload_digest(payload)

    revision = evaluate_revision(
        current_revision=(
            None if current is None else current.accepted_revision
        ),
        current_entitlement_id=(
            None if current is None else current.entitlement_id
        ),
        current_digest=(
            None
            if current is None
            else current.canonical_payload_digest
        ),
        incoming_revision=payload.revision,
        incoming_entitlement_id=payload.entitlement_id,
        incoming_digest=digest,
    )

    if revision.decision is RevisionDecision.ROLLBACK_DETECTED:
        repository.add_activation(
            _activation_history(
                payload=payload,
                digest=digest,
                key_id=envelope.key_id,
                actor_user_id=actor_user_id,
                correlation_id=correlation_id,
                outcome="REJECTED",
                reason_code="rollback_detected",
                accepted_at=now,
            )
        )
        return ActivationResult(
            decision=revision.decision,
            entitlement_id=payload.entitlement_id,
            revision=payload.revision,
            canonical_payload_digest=digest,
            temporal_state="invalid_or_unavailable",
            state_advanced=False,
            accepted=False,
            reason_code="rollback_detected",
        )

    if revision.decision is RevisionDecision.SAME_REVISION_CONFLICT:
        repository.add_activation(
            _activation_history(
                payload=payload,
                digest=digest,
                key_id=envelope.key_id,
                actor_user_id=actor_user_id,
                correlation_id=correlation_id,
                outcome="REJECTED",
                reason_code="same_revision_conflict",
                accepted_at=now,
            )
        )
        return ActivationResult(
            decision=revision.decision,
            entitlement_id=payload.entitlement_id,
            revision=payload.revision,
            canonical_payload_digest=digest,
            temporal_state="invalid_or_unavailable",
            state_advanced=False,
            accepted=False,
            reason_code="same_revision_conflict",
        )

    if current is None:
        trusted_time = evaluate_trusted_time(
            observed_now=now,
            last_trusted_time=None,
            time_untrusted_at=None,
        )
    else:
        trusted_time = evaluate_trusted_time(
            observed_now=now,
            last_trusted_time=current.last_trusted_time,
            time_untrusted_at=current.time_untrusted_at,
        )

    if trusted_time.decision is TrustedTimeDecision.TIME_UNTRUSTED:
        if current is not None and current.time_untrusted_at is None:
            current.time_untrusted_at = now

        repository.add_activation(
            _activation_history(
                payload=payload,
                digest=digest,
                key_id=envelope.key_id,
                actor_user_id=actor_user_id,
                correlation_id=correlation_id,
                outcome="REJECTED",
                reason_code="time_untrusted",
                accepted_at=now,
            )
        )

        return ActivationResult(
            decision=revision.decision,
            entitlement_id=payload.entitlement_id,
            revision=payload.revision,
            canonical_payload_digest=digest,
            temporal_state="time_untrusted",
            state_advanced=False,
            accepted=False,
            reason_code="time_untrusted",
        )

    if revision.decision is RevisionDecision.IDEMPOTENT:
        if (
            current is not None
            and trusted_time.should_persist_checkpoint
        ):
            current.last_trusted_time = trusted_time.effective_time

        repository.add_activation(
            _activation_history(
                payload=payload,
                digest=digest,
                key_id=envelope.key_id,
                actor_user_id=actor_user_id,
                correlation_id=correlation_id,
                outcome="IDEMPOTENT",
                reason_code=None,
                accepted_at=now,
            )
        )

        return ActivationResult(
            decision=revision.decision,
            entitlement_id=payload.entitlement_id,
            revision=payload.revision,
            canonical_payload_digest=digest,
            temporal_state=entitlement_temporal_state(
                payload,
                trusted_now=trusted_time.effective_time,
            ),
            state_advanced=False,
        )

    if current is None:
        current = CommercialEntitlementStateModel(
            organization_id=payload.organization_id,
            deployment_id=payload.deployment_id,
            entitlement_id=payload.entitlement_id,
            accepted_revision=payload.revision,
            canonical_payload_digest=digest,
            key_id=envelope.key_id,
            issuer=payload.issuer,
            issued_at=payload.issued_at,
            not_before=payload.not_before,
            valid_until=payload.valid_until,
            grace_until=payload.grace_until,
            support_until=payload.support_until,
            package_keys=list(payload.package_keys),
            seat_capacity=payload.seat_capacity,
            baseline_release_sequence=payload.baseline_release_sequence,
            max_release_sequence=payload.max_release_sequence,
            last_trusted_time=trusted_time.effective_time,
            accepted_at=now,
            accepted_by_user_id=actor_user_id,
            time_untrusted_at=None,
            version=1,
        )
        repository.add_state(current)
    else:
        current.entitlement_id = payload.entitlement_id
        current.accepted_revision = payload.revision
        current.canonical_payload_digest = digest
        current.key_id = envelope.key_id
        current.issuer = payload.issuer
        current.issued_at = payload.issued_at
        current.not_before = payload.not_before
        current.valid_until = payload.valid_until
        current.grace_until = payload.grace_until
        current.support_until = payload.support_until
        current.package_keys = list(payload.package_keys)
        current.seat_capacity = payload.seat_capacity
        current.baseline_release_sequence = (
            payload.baseline_release_sequence
        )
        current.max_release_sequence = payload.max_release_sequence
        current.last_trusted_time = trusted_time.effective_time
        current.accepted_at = now
        current.accepted_by_user_id = actor_user_id
        current.version = int(current.version or 0) + 1

    repository.add_activation(
        _activation_history(
            payload=payload,
            digest=digest,
            key_id=envelope.key_id,
            actor_user_id=actor_user_id,
            correlation_id=correlation_id,
            outcome="ACCEPTED",
            reason_code=None,
            accepted_at=now,
        )
    )

    return ActivationResult(
        decision=revision.decision,
        entitlement_id=payload.entitlement_id,
        revision=payload.revision,
        canonical_payload_digest=digest,
        temporal_state=entitlement_temporal_state(
            payload,
            trusted_now=trusted_time.effective_time,
        ),
        state_advanced=True,
    )


def _activation_history(
    *,
    payload: EntitlementPayload,
    digest: str,
    key_id: str,
    actor_user_id: int | None,
    correlation_id: str | None,
    outcome: str,
    reason_code: str | None,
    accepted_at: datetime,
) -> CommercialEntitlementActivation:
    return CommercialEntitlementActivation(
        organization_id=payload.organization_id,
        deployment_id=payload.deployment_id,
        entitlement_id=payload.entitlement_id,
        revision=payload.revision,
        canonical_payload_digest=digest,
        key_id=key_id,
        outcome=outcome,
        reason_code=reason_code,
        accepted_at=accepted_at,
        actor_user_id=actor_user_id,
        correlation_id=correlation_id,
    )


def _verification_reason(exc: ValueError) -> str:
    message = str(exc)

    if "invalid signature" in message:
        return "invalid_signature"

    if "untrusted key" in message:
        return "untrusted_key"

    if "key revoked" in message:
        return "revoked_key"

    if "key not yet valid" in message:
        return "untrusted_key"

    return "invalid_signature"
