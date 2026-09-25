"""PATCH-058 server-authoritative refresh-session service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.auth_security import AuthRefreshFamily, AuthRefreshSession, AuthSecurityEvent
from app.models.organization import Organization, UserOrganizationMembership
from app.models.user import User


class RefreshRejected(Exception):
    """Protected refresh failure with no externally inferential detail."""


@dataclass(frozen=True, slots=True)
class IssuedRefreshCredential:
    session_id: UUID
    credential: str
    expires_at: datetime


class RefreshSessionService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _selector() -> str:
        return secrets.token_urlsafe(18)

    @staticmethod
    def _secret() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def _credential(selector: str, secret: str) -> str:
        return f"{selector}.{secret}"

    @staticmethod
    def _split(credential: str) -> tuple[str, str]:
        try:
            selector, secret = credential.split(".", 1)
        except ValueError as exc:
            raise RefreshRejected() from exc
        if len(selector) < 22 or len(secret) < 43:
            raise RefreshRejected()
        return selector, secret

    @staticmethod
    def _key() -> bytes:
        key = settings.resolved_refresh_verifier_key()
        if len(key) < 32:
            raise RefreshRejected()
        return key.encode("utf-8")

    @classmethod
    def _verifier(cls, secret: str) -> str:
        return hmac.new(cls._key(), secret.encode("utf-8"), hashlib.sha256).hexdigest()

    @classmethod
    def _verify(cls, secret: str, verifier: str) -> bool:
        return hmac.compare_digest(cls._verifier(secret), verifier)

    def _active_membership(self, user_id: int) -> UserOrganizationMembership | None:
        return (
            self.db.query(UserOrganizationMembership)
            .join(Organization, Organization.id == UserOrganizationMembership.organization_id)
            .filter(
                UserOrganizationMembership.user_id == user_id,
                UserOrganizationMembership.is_selected.is_(True),
                UserOrganizationMembership.is_enabled.is_(True),
                Organization.is_active.is_(True),
            )
            .limit(2)
            .one_or_none()
        )

    def _security_event(
        self,
        *,
        event_type: str,
        user_id: int,
        session_id: UUID,
        outcome: str,
        reason_code: str | None = None,
    ) -> None:
        self.db.add(
            AuthSecurityEvent(
                event_type=event_type,
                user_id=user_id,
                actor_user_id=user_id,
                session_id=session_id,
                outcome=outcome,
                reason_code=reason_code,
            )
        )
        self.db.flush()

    def _new_session(
        self,
        *,
        family_id: UUID,
        user: User,
        predecessor_id: UUID | None = None,
    ) -> IssuedRefreshCredential:
        selector = self._selector()
        secret = self._secret()
        now = self._now()
        expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        session = AuthRefreshSession(
            id=uuid4(),
            family_id=family_id,
            predecessor_id=predecessor_id,
            user_id=user.id,
            selector=selector,
            secret_verifier=self._verifier(secret),
            auth_version=user.auth_version,
            expires_at=expires_at,
        )
        self.db.add(session)
        self.db.flush()
        return IssuedRefreshCredential(
            session_id=session.id,
            credential=self._credential(selector, secret),
            expires_at=expires_at,
        )

    def create(self, user: User) -> IssuedRefreshCredential:
        if not user.is_active or user.activation_pending or self._active_membership(user.id) is None:
            raise RefreshRejected()
        family = AuthRefreshFamily(id=uuid4(), user_id=user.id)
        self.db.add(family)
        self.db.flush()
        issued = self._new_session(family_id=family.id, user=user)
        self.db.commit()
        return issued

    def rotate(self, credential: str) -> tuple[User, IssuedRefreshCredential]:
        selector, secret = self._split(credential)
        session = (
            self.db.query(AuthRefreshSession)
            .filter(AuthRefreshSession.selector == selector)
            .with_for_update()
            .one_or_none()
        )
        if session is None or not self._verify(secret, session.secret_verifier):
            raise RefreshRejected()

        family = (
            self.db.query(AuthRefreshFamily)
            .filter(AuthRefreshFamily.id == session.family_id)
            .with_for_update()
            .one_or_none()
        )
        if family is None:
            raise RefreshRejected()

        now = self._now()
        if session.consumed_at is not None:
            family.reuse_detected_at = now
            family.revoked_at = family.revoked_at or now
            family.revocation_reason = "refresh_reuse"
            session.reuse_detected_at = now
            (
                self.db.query(AuthRefreshSession)
                .filter(
                    AuthRefreshSession.family_id == family.id,
                    AuthRefreshSession.revoked_at.is_(None),
                )
                .update(
                    {
                        AuthRefreshSession.revoked_at: now,
                        AuthRefreshSession.revocation_reason: "refresh_reuse",
                    },
                    synchronize_session=False,
                )
            )
            self._security_event(
                event_type="refresh_reuse_detected",
                user_id=session.user_id,
                session_id=session.id,
                outcome="rejected",
                reason_code="consumed_credential_reuse",
            )
            self.db.commit()
            raise RefreshRejected()

        if (
            session.revoked_at is not None
            or family.revoked_at is not None
            or session.expires_at <= now
        ):
            raise RefreshRejected()

        user = (
            self.db.query(User)
            .filter(User.id == session.user_id)
            .with_for_update()
            .one_or_none()
        )
        if (
            user is None
            or not user.is_active
            or user.activation_pending
            or user.auth_version != session.auth_version
            or self._active_membership(session.user_id) is None
        ):
            self.db.rollback()
            raise RefreshRejected()

        session.consumed_at = now
        successor = self._new_session(
            family_id=family.id,
            user=user,
            predecessor_id=session.id,
        )
        self._security_event(
            event_type="refresh_rotation",
            user_id=user.id,
            session_id=successor.session_id,
            outcome="success",
            reason_code="rotated",
        )
        self.db.commit()
        return user, successor

    def list_active(self, user: User) -> list[AuthRefreshSession]:
        now = self._now()
        return (
            self.db.query(AuthRefreshSession)
            .join(AuthRefreshFamily, AuthRefreshFamily.id == AuthRefreshSession.family_id)
            .filter(
                AuthRefreshSession.user_id == user.id,
                AuthRefreshSession.revoked_at.is_(None),
                AuthRefreshSession.consumed_at.is_(None),
                AuthRefreshSession.expires_at > now,
                AuthRefreshFamily.revoked_at.is_(None),
            )
            .order_by(AuthRefreshSession.created_at.desc(), AuthRefreshSession.id.desc())
            .all()
        )

    def revoke_current(self, user: User, session_id: UUID, *, actor_user_id: int | None = None) -> None:
        session = (
            self.db.query(AuthRefreshSession)
            .filter(AuthRefreshSession.id == session_id, AuthRefreshSession.user_id == user.id)
            .with_for_update()
            .one_or_none()
        )
        if session is None:
            raise RefreshRejected()
        now = self._now()
        if session.revoked_at is None:
            session.revoked_at = now
            session.revocation_reason = "current_session_logout"
        self.db.add(AuthSecurityEvent(
            event_type="current_session_revocation", user_id=user.id,
            actor_user_id=actor_user_id or user.id, session_id=session.id,
            outcome="success", reason_code="human_logout",
        ))
        self.db.commit()

    def revoke_all(self, user: User, *, actor_user_id: int | None = None, reason: str = "all_sessions_logout") -> int:
        now = self._now()
        active = (
            self.db.query(AuthRefreshSession)
            .filter(AuthRefreshSession.user_id == user.id, AuthRefreshSession.revoked_at.is_(None))
            .with_for_update()
            .all()
        )
        for session in active:
            session.revoked_at = now
            session.revocation_reason = reason
        families = (
            self.db.query(AuthRefreshFamily)
            .filter(AuthRefreshFamily.user_id == user.id, AuthRefreshFamily.revoked_at.is_(None))
            .with_for_update()
            .all()
        )
        for family in families:
            family.revoked_at = now
            family.revocation_reason = reason
        self.db.add(AuthSecurityEvent(
            event_type="all_session_revocation" if actor_user_id in (None, user.id) else "admin_session_revocation",
            user_id=user.id, actor_user_id=actor_user_id or user.id,
            outcome="success", reason_code=reason,
        ))
        self.db.commit()
        return len(active)

    def revoke_target(self, actor: User, target: User) -> int:
        if actor.role != "admin" or actor.id == target.id:
            raise RefreshRejected()
        return self.revoke_all(target, actor_user_id=actor.id, reason="administrator_revocation")

    def has_recent_authentication(self, session: AuthRefreshSession, *, minutes: int = 10) -> bool:
        family = self.db.get(AuthRefreshFamily, session.family_id)
        if family is None:
            return False
        latest_step_up = (
            self.db.query(AuthSecurityEvent.occurred_at)
            .filter(
                AuthSecurityEvent.session_id == session.id,
                AuthSecurityEvent.user_id == session.user_id,
                AuthSecurityEvent.event_type == "step_up_success",
                AuthSecurityEvent.outcome == "success",
            )
            .order_by(AuthSecurityEvent.occurred_at.desc())
            .limit(1)
            .scalar()
        )
        trusted_at = latest_step_up or family.created_at
        if trusted_at is None:
            return False
        if trusted_at.tzinfo is None:
            trusted_at = trusted_at.replace(tzinfo=timezone.utc)
        return trusted_at >= self._now() - timedelta(minutes=minutes)

    def has_recent_step_up(self, session: AuthRefreshSession, *, minutes: int = 10) -> bool:
        latest_step_up = (
            self.db.query(AuthSecurityEvent.occurred_at)
            .filter(
                AuthSecurityEvent.session_id == session.id,
                AuthSecurityEvent.user_id == session.user_id,
                AuthSecurityEvent.event_type == "step_up_success",
                AuthSecurityEvent.outcome == "success",
            )
            .order_by(AuthSecurityEvent.occurred_at.desc())
            .limit(1)
            .scalar()
        )
        if latest_step_up is None:
            return False
        if latest_step_up.tzinfo is None:
            latest_step_up = latest_step_up.replace(tzinfo=timezone.utc)
        return latest_step_up >= self._now() - timedelta(minutes=minutes)

    def record_step_up(self, user: User, session: AuthRefreshSession) -> None:
        self.db.add(AuthSecurityEvent(
            event_type="step_up_success", user_id=user.id, actor_user_id=user.id,
            session_id=session.id, outcome="success", reason_code="recent_authentication",
        ))
        self.db.commit()
