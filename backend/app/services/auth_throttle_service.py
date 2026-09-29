"""PATCH-058 bounded PostgreSQL-backed authentication throttling."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
from uuid import uuid4

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.auth_security import AuthThrottleState


class ThrottleConfigurationError(Exception):
    pass


class AuthThrottleService:
    PRIMARY_AUTHENTICATION = "primary_authentication"
    MFA_LOGIN_VERIFICATION = "mfa_login_verification"
    MFA_VERIFICATION = "mfa_verification"
    RECOVERY_VERIFICATION = "recovery_verification"
    STEP_UP_VERIFICATION = "step_up_verification"
    PASSWORD_CHANGE_VERIFICATION = "password_change_verification"
    MFA_RECOVERY_CODE_VERIFICATION = "mfa_recovery_code_verification"

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _key() -> bytes:
        try:
            value = settings.resolved_auth_throttle_key()
        except OSError as exc:
            raise ThrottleConfigurationError() from exc
        if len(value) < 32:
            raise ThrottleConfigurationError()
        return value.encode("utf-8")

    @classmethod
    def _digest(cls, namespace: str, value: str) -> str:
        return hmac.new(
            cls._key(),
            f"{namespace}:{value}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def scope_keys(
        self,
        operation: str,
        credential_identity: str,
        network_context: str,
    ) -> tuple[str, str]:
        """Return only non-reversible keys suitable for a signed continuation."""

        normalized = credential_identity.strip().casefold()
        network = network_context.strip() or "unknown"
        return (
            self._digest("credential", f"{operation}:{normalized}"),
            self._digest("network", network),
        )

    def _locked_state(self, credential_key: str, network_key: str, now: datetime) -> AuthThrottleState:
        statement = (
            insert(AuthThrottleState)
            .values(
                id=uuid4(),
                credential_key=credential_key,
                network_key=network_key,
                failure_count=0,
                window_started_at=now,
            )
            .on_conflict_do_nothing(
                index_elements=[
                    AuthThrottleState.credential_key,
                    AuthThrottleState.network_key,
                ]
            )
        )
        self.db.execute(statement)
        return (
            self.db.query(AuthThrottleState)
            .filter(
                AuthThrottleState.credential_key == credential_key,
                AuthThrottleState.network_key == network_key,
            )
            .with_for_update()
            .one()
        )

    def is_blocked(self, operation: str, credential_identity: str, network_context: str) -> bool:
        now = self._now()
        credential_key, network_key = self.scope_keys(
            operation, credential_identity, network_context
        )
        # Upserting before locking closes the first-attempt race: concurrent
        # requests cannot all observe an absent row and bypass the limit.
        state = self._locked_state(credential_key, network_key, now)
        return bool(state.blocked_until and state.blocked_until > now)

    def record_failure(
        self,
        operation: str,
        credential_identity: str,
        network_context: str,
        *,
        commit: bool = True,
    ) -> bool:
        now = self._now()
        credential_key, network_key = self.scope_keys(
            operation, credential_identity, network_context
        )
        state = self._locked_state(credential_key, network_key, now)
        window = timedelta(seconds=settings.AUTH_THROTTLE_WINDOW_SECONDS)
        if state.window_started_at + window <= now:
            state.window_started_at = now
            state.failure_count = 0
            state.blocked_until = None
        state.failure_count += 1
        threshold = settings.AUTH_THROTTLE_FAILURE_THRESHOLD
        threshold_reached = state.failure_count == threshold
        if state.failure_count >= threshold:
            exponent = min(state.failure_count - threshold, 8)
            delay = min(
                60 * (2**exponent),
                settings.AUTH_THROTTLE_MAX_BACKOFF_SECONDS,
            )
            state.blocked_until = now + timedelta(seconds=delay)
        if commit:
            self.db.commit()
        else:
            self.db.flush()
        return threshold_reached

    def clear_keys(
        self,
        credential_key: str,
        network_key: str,
        *,
        commit: bool = True,
    ) -> None:
        if (
            len(credential_key) != 64
            or len(network_key) != 64
            or any(character not in "0123456789abcdef" for character in credential_key)
            or any(character not in "0123456789abcdef" for character in network_key)
        ):
            raise ThrottleConfigurationError()
        (
            self.db.query(AuthThrottleState)
            .filter(
                AuthThrottleState.credential_key == credential_key,
                AuthThrottleState.network_key == network_key,
            )
            .delete(synchronize_session=False)
        )
        if commit:
            self.db.commit()
        else:
            self.db.flush()

    def clear(
        self,
        operation: str,
        credential_identity: str,
        network_context: str,
        *,
        commit: bool = True,
    ) -> None:
        credential_key, network_key = self.scope_keys(
            operation, credential_identity, network_context
        )
        self.clear_keys(
            credential_key,
            network_key,
            commit=commit,
        )
