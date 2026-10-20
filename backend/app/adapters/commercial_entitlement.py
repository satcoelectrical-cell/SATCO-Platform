"""PATCH-059 commercial implementation of the PATCH-051 entitlement seam."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable

from sqlalchemy.orm import sessionmaker

from app.enums.discipline_package import EntitlementDecision, EntitlementOperation
from app.ports.discipline_package import EntitlementRequest
from app.repositories.commercial_entitlement_unit_of_work import (
    CommercialEntitlementUnitOfWork,
    require_repository,
)
from app.services.commercial_entitlement_service import (
    TrustedTimeDecision,
    evaluate_trusted_time,
)
from app.services.commercial_seat_service import evaluate_seat


_TRUSTED_TIME_CHECKPOINT_INTERVAL = timedelta(minutes=5)


@dataclass(frozen=True, slots=True)
class CommercialEntitlementAdapter:
    """Restrictive commercial predicate; it never grants resource authority."""

    session_factory: sessionmaker
    user_id: int | None = None
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc)

    def evaluate(self, request: EntitlementRequest) -> EntitlementDecision:
        # Historical access is a separate commercial predicate. Canonical
        # historical resource authorization must already have succeeded.
        if request.operation is EntitlementOperation.HISTORICAL_READ:
            return EntitlementDecision.PERMITTED

        if self.user_id is None:
            return EntitlementDecision.UNAVAILABLE

        try:
            with CommercialEntitlementUnitOfWork(self.session_factory) as uow:
                repository = require_repository(uow)
                state = repository.get_state(
                    organization_id=request.trusted_organization_id,
                    deployment_id=request.trusted_deployment_id,
                    lock=True,
                )
                if state is None:
                    return EntitlementDecision.UNAVAILABLE

                observed_now = self.now()
                trusted = evaluate_trusted_time(
                    observed_now=observed_now,
                    last_trusted_time=state.last_trusted_time,
                    time_untrusted_at=state.time_untrusted_at,
                )

                if trusted.decision is TrustedTimeDecision.TIME_UNTRUSTED:
                    if state.time_untrusted_at is None:
                        state.time_untrusted_at = observed_now
                        uow.commit()
                    return EntitlementDecision.UNAVAILABLE

                persist_trusted_checkpoint = (
                    trusted.should_persist_checkpoint
                    and trusted.effective_time - state.last_trusted_time
                    >= _TRUSTED_TIME_CHECKPOINT_INTERVAL
                )
                if persist_trusted_checkpoint:
                    state.last_trusted_time = trusted.effective_time

                effective_now = trusted.effective_time

                if effective_now < state.not_before:
                    return EntitlementDecision.UNAVAILABLE

                if effective_now > state.grace_until:
                    return EntitlementDecision.DENIED

                if request.package_key not in tuple(state.package_keys):
                    return EntitlementDecision.DENIED

                # GRACE EXECUTE is continuity-only. It requires durable
                # proof that the current Organization-package enablement epoch
                # began no later than this entitlement's valid-until boundary.
                # The proof is restrictive only; canonical resource/package
                # configuration authority must already have succeeded.
                if effective_now > state.valid_until:
                    if request.operation is not EntitlementOperation.EXECUTE:
                        return EntitlementDecision.DENIED

                    proof = repository.get_configuration_proof(
                        organization_id=request.trusted_organization_id,
                        deployment_id=request.trusted_deployment_id,
                        package_key=request.package_key,
                    )
                    if (
                        proof is None
                        or proof.configured_before > state.valid_until
                    ):
                        if persist_trusted_checkpoint:
                            uow.commit()
                        return EntitlementDecision.DENIED

                seat = evaluate_seat(
                    uow,
                    organization_id=request.trusted_organization_id,
                    deployment_id=request.trusted_deployment_id,
                    user_id=self.user_id,
                )
                if not seat.executable:
                    if persist_trusted_checkpoint:
                        uow.commit()
                    return EntitlementDecision.DENIED

                if persist_trusted_checkpoint:
                    uow.commit()
                return EntitlementDecision.PERMITTED
        except Exception:
            # Commercial enforcement is fail closed. Public reason mapping is
            # owned by the bounded API/service layer, not this narrow seam.
            return EntitlementDecision.UNAVAILABLE
