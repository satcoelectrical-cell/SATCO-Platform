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

    def _keys(self, operation: str, credential_identity: str, network_context: str) -> tuple[str, str]:
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
        credential_key, network_key = self._keys(
            operation, credential_identity, network_context
        )
        state = (
            self.db.query(AuthThrottleState)
            .filter(
                AuthThrottleState.credential_key == credential_key,
                AuthThrottleState.network_key == network_key,
            )
            .with_for_update()
            .one_or_none()
        )
        return bool(state and state.blocked_until and state.blocked_until > now)

    def record_failure(self, operation: str, credential_identity: str, network_context: str) -> bool:
        now = self._now()
        credential_key, network_key = self._keys(
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
        self.db.commit()
        return threshold_reached

    def clear(self, operation: str, credential_identity: str, network_context: str) -> None:
        credential_key, network_key = self._keys(
            operation, credential_identity, network_context
        )
        (
            self.db.query(AuthThrottleState)
            .filter(
                AuthThrottleState.credential_key == credential_key,
                AuthThrottleState.network_key == network_key,
            )
            .delete(synchronize_session=False)
        )
        self.db.commit()
