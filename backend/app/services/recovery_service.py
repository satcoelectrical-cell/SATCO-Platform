"""PATCH-058 Human-controlled account and MFA recovery lifecycle."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.auth_security import AuthRecoveryCredential, AuthSecurityEvent, MfaRecoveryCode, UserTotpAuthenticator
from app.models.organization import UserOrganizationMembership
from app.models.user import User
from app.services.refresh_session_service import RefreshSessionService


class RecoveryRejected(Exception):
    pass


@dataclass(frozen=True, slots=True)
class IssuedRecovery:
    credential: str
    expires_at: datetime


class RecoveryService:
    _LIFETIME = timedelta(minutes=15)

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _key() -> bytes:
        value = settings.resolved_recovery_code_verifier_key()
        if len(value) < 32:
            raise RecoveryRejected()
        return value.encode("utf-8")

    @classmethod
    def _verifier(cls, secret: str) -> str:
        return hmac.new(cls._key(), secret.encode("utf-8"), hashlib.sha256).hexdigest()

    @staticmethod
    def _parse(value: str) -> tuple[str, str]:
        selector, separator, secret = value.partition(".")
        if not separator or len(selector) < 22 or len(secret) < 32:
            raise RecoveryRejected()
        return selector, secret

    def issue(self, *, actor: User, target: User, organization_id: UUID, purpose: str) -> IssuedRecovery:
        if actor.role != "admin" or purpose not in {"account_recovery", "mfa_recovery"}:
            raise RecoveryRejected()
        membership = (
            self.db.query(UserOrganizationMembership)
            .filter(
                UserOrganizationMembership.user_id == target.id,
                UserOrganizationMembership.organization_id == organization_id,
                UserOrganizationMembership.is_enabled.is_(True),
            )
            .one_or_none()
        )
        if membership is None or not target.is_active or target.activation_pending:
            raise RecoveryRejected()
        now = self._now()
        for old in (
            self.db.query(AuthRecoveryCredential)
            .filter(
                AuthRecoveryCredential.user_id == target.id,
                AuthRecoveryCredential.organization_id == organization_id,
                AuthRecoveryCredential.purpose == purpose,
                AuthRecoveryCredential.used_at.is_(None),
                AuthRecoveryCredential.revoked_at.is_(None),
            )
            .with_for_update()
            .all()
        ):
            old.revoked_at = now
        selector = secrets.token_urlsafe(18)
        secret = secrets.token_urlsafe(32)
        expires = now + self._LIFETIME
        self.db.add(AuthRecoveryCredential(
            id=uuid4(), user_id=target.id, organization_id=organization_id,
            purpose=purpose, selector=selector, secret_verifier=self._verifier(secret),
            issued_by_user_id=actor.id, expires_at=expires,
        ))
        self.db.add(AuthSecurityEvent(
            event_type="recovery_credential_issued", user_id=target.id,
            actor_user_id=actor.id, organization_id=organization_id,
            outcome="success", reason_code=purpose,
        ))
        self.db.commit()
        return IssuedRecovery(f"{selector}.{secret}", expires)

    def _consume(self, credential: str, purpose: str) -> tuple[AuthRecoveryCredential, User]:
        selector, secret = self._parse(credential)
        row = (
            self.db.query(AuthRecoveryCredential)
            .filter(AuthRecoveryCredential.selector == selector)
            .with_for_update()
            .one_or_none()
        )
        now = self._now()
        if (
            row is None or row.purpose != purpose or row.used_at is not None
            or row.revoked_at is not None or row.expires_at <= now
            or not hmac.compare_digest(row.secret_verifier, self._verifier(secret))
        ):
            raise RecoveryRejected()
        user = self.db.query(User).filter(User.id == row.user_id).with_for_update().one_or_none()
        membership = self.db.query(UserOrganizationMembership).filter(
            UserOrganizationMembership.user_id == row.user_id,
            UserOrganizationMembership.organization_id == row.organization_id,
            UserOrganizationMembership.is_enabled.is_(True),
        ).one_or_none()
        if user is None or membership is None or not user.is_active or user.activation_pending:
            raise RecoveryRejected()
        row.used_at = now
        return row, user

    def recover_account(self, credential: str, new_password: str) -> None:
        row, user = self._consume(credential, "account_recovery")
        user.hashed_password = hash_password(new_password)
        user.auth_version += 1
        user.version += 1
        RefreshSessionService(self.db).revoke_all(user, actor_user_id=row.issued_by_user_id, reason="account_recovery")
        self.db.add(AuthSecurityEvent(
            event_type="account_recovery", user_id=user.id, actor_user_id=row.issued_by_user_id,
            organization_id=row.organization_id, outcome="success", reason_code="credential_consumed",
        ))
        self.db.commit()

    def recover_mfa(self, credential: str) -> None:
        row, user = self._consume(credential, "mfa_recovery")
        now = self._now()
        authenticator = self.db.query(UserTotpAuthenticator).filter(UserTotpAuthenticator.user_id == user.id).with_for_update().one_or_none()
        if authenticator is not None and authenticator.disabled_at is None:
            authenticator.disabled_at = now
        for code in self.db.query(MfaRecoveryCode).filter(MfaRecoveryCode.user_id == user.id, MfaRecoveryCode.used_at.is_(None)).with_for_update().all():
            code.used_at = now
        user.auth_version += 1
        user.version += 1
        RefreshSessionService(self.db).revoke_all(user, actor_user_id=row.issued_by_user_id, reason="mfa_recovery")
        self.db.add(AuthSecurityEvent(
            event_type="mfa_recovery", user_id=user.id, actor_user_id=row.issued_by_user_id,
            organization_id=row.organization_id, outcome="success", reason_code="factor_reset_requires_enrollment",
        ))
        self.db.commit()
