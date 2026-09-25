"""PATCH-058 server-authoritative bootstrap security qualification."""

from datetime import datetime, timezone
import hmac

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.auth_security import AuthSecurityEvent
from app.models.onboarding import OnboardingIdempotency
from app.services.auth_throttle_service import AuthThrottleService, ThrottleConfigurationError


class BootstrapRejected(Exception):
    pass


class BootstrapUnavailable(Exception):
    pass


class BootstrapSecurityService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _window_end() -> datetime:
        raw = settings.SATCO_BOOTSTRAP_WINDOW_END.strip()
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except (TypeError, ValueError) as exc:
            raise BootstrapUnavailable() from exc
        if parsed.tzinfo is None:
            raise BootstrapUnavailable()
        return parsed.astimezone(timezone.utc)

    def _completed(self) -> bool:
        latest_completion = (
            self.db.query(func.max(OnboardingIdempotency.created_at))
            .filter(
                OnboardingIdempotency.scope == "platform",
                OnboardingIdempotency.operation == "bootstrap",
            )
            .scalar()
        )
        if latest_completion is None:
            return False
        latest_reenable = (
            self.db.query(func.max(AuthSecurityEvent.occurred_at))
            .filter(
                AuthSecurityEvent.event_type == "bootstrap_reenabled",
                AuthSecurityEvent.outcome == "success",
            )
            .scalar()
        )
        return latest_reenable is None or latest_reenable <= latest_completion

    def reenable(
        self,
        *,
        actor_user_id: int,
        organization_id,
        session_id,
        supplied_secret: str,
        network_context: str,
    ) -> None:
        # Re-enable is deliberately dual-authority: recent authenticated Human
        # administration is enforced by the route and the bounded deployment
        # bootstrap secret/window is re-qualified here. Organization role alone
        # is never sufficient to reopen the platform bootstrap boundary.
        self.qualify(supplied_secret, network_context, require_eligible=False)
        if not self._completed():
            raise BootstrapRejected()
        self.db.add(
            AuthSecurityEvent(
                event_type="bootstrap_reenabled",
                actor_user_id=actor_user_id,
                organization_id=organization_id,
                session_id=session_id,
                outcome="success",
                reason_code="human_admin_reenable",
                safe_context="bounded_bootstrap_reenable",
                occurred_at=datetime.now(timezone.utc),
            )
        )
        self.db.commit()

    def _event(self, outcome: str, reason: str) -> None:
        self.db.add(
            AuthSecurityEvent(
                event_type="bootstrap_qualification",
                outcome=outcome,
                reason_code=reason,
                safe_context="platform_bootstrap",
            )
        )
        self.db.commit()

    def qualify(self, supplied_secret: str, network_context: str, *, require_eligible: bool) -> None:
        # Configuration is part of authorization, not merely startup documentation.
        if not settings.SATCO_BOOTSTRAP_ENABLED:
            self._event("rejected", "disabled")
            raise BootstrapRejected()
        try:
            expected = settings.resolved_bootstrap_key()
        except OSError as exc:
            raise BootstrapUnavailable() from exc
        if len(expected) < 32:
            raise BootstrapUnavailable()
        if self._window_end() <= datetime.now(timezone.utc):
            self._event("rejected", "outside_window")
            raise BootstrapRejected()

        throttle = AuthThrottleService(self.db)
        identity = "platform_bootstrap"
        try:
            if throttle.is_blocked("bootstrap_authentication", identity, network_context):
                self._event("rejected", "throttled")
                raise BootstrapRejected()
            if not hmac.compare_digest(supplied_secret, expected):
                threshold = throttle.record_failure("bootstrap_authentication", identity, network_context)
                if threshold:
                    self._event("rejected", "throttle_threshold")
                raise BootstrapRejected()
            if require_eligible:
                # Serialize the one-time platform bootstrap decision and keep the
                # transaction-scoped lock until OnboardingService commits the
                # bootstrap completion marker. This closes the concurrent-first-
                # bootstrap race without adding a parallel persistence model.
                self.db.execute(text("SELECT pg_advisory_xact_lock(580058)"))
                if self._completed():
                    self._event("rejected", "completed")
                    raise BootstrapRejected()
            throttle.clear(
                "bootstrap_authentication",
                identity,
                network_context,
                commit=False,
            )
        except ThrottleConfigurationError as exc:
            self.db.rollback()
            raise BootstrapUnavailable() from exc
