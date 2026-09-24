"""PATCH-058 Checkpoint B1 TOTP enrollment and recovery-code foundation."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import secrets
import time
from uuid import UUID, uuid4

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import pyotp
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.auth_security import (
    AuthSecurityEvent,
    MfaRecoveryCode,
    OrganizationMfaPolicy,
    UserTotpAuthenticator,
)
from app.models.user import User


class MfaRejected(Exception):
    """Fail-closed MFA outcome without secret-bearing detail."""


@dataclass(frozen=True, slots=True)
class MfaStatus:
    required: bool
    enrolled: bool
    active: bool


@dataclass(frozen=True, slots=True)
class EnrollmentStart:
    secret: str
    provisioning_uri: str


@dataclass(frozen=True, slots=True)
class EnrollmentComplete:
    recovery_codes: tuple[str, ...]


class MfaService:
    _TOTP_DIGITS = 6
    _TOTP_INTERVAL = 30
    _TOTP_WINDOW = 1
    _RECOVERY_COUNT = 10

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _b64e(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).decode("ascii")

    @staticmethod
    def _b64d(value: str) -> bytes:
        try:
            return base64.urlsafe_b64decode(value.encode("ascii"))
        except (ValueError, UnicodeError) as exc:
            raise MfaRejected() from exc

    @staticmethod
    def _active_key() -> bytes:
        try:
            value = settings.resolved_totp_encryption_key()
            key = base64.urlsafe_b64decode(value.encode("ascii"))
        except (OSError, ValueError, UnicodeError) as exc:
            raise MfaRejected() from exc
        if len(key) != 32:
            raise MfaRejected()
        return key

    @staticmethod
    def _recovery_key() -> bytes:
        try:
            value = settings.resolved_recovery_code_verifier_key()
        except OSError as exc:
            raise MfaRejected() from exc
        if len(value) < 32:
            raise MfaRejected()
        return value.encode("utf-8")

    @staticmethod
    def _aad(user_id: int, key_id: str, key_version: int) -> bytes:
        return f"satco:totp:{user_id}:{key_id}:{key_version}".encode("utf-8")

    @classmethod
    def _encrypt_secret(cls, user_id: int, secret: str) -> tuple[str, str, str, int]:
        key_id = settings.TOTP_ENCRYPTION_KEY_ID
        key_version = settings.TOTP_ENCRYPTION_KEY_VERSION
        if not key_id or key_version < 1:
            raise MfaRejected()
        nonce = secrets.token_bytes(12)
        ciphertext = AESGCM(cls._active_key()).encrypt(
            nonce,
            secret.encode("ascii"),
            cls._aad(user_id, key_id, key_version),
        )
        return cls._b64e(ciphertext), cls._b64e(nonce), key_id, key_version

    @classmethod
    def _key_for_authenticator(cls, authenticator: UserTotpAuthenticator) -> bytes:
        if authenticator.key_id == settings.TOTP_ENCRYPTION_KEY_ID:
            return cls._active_key()
        try:
            previous = settings.resolved_totp_previous_keys()
            encoded = previous[authenticator.key_id]
            key = base64.urlsafe_b64decode(encoded.encode("ascii"))
        except (OSError, KeyError, ValueError, UnicodeError) as exc:
            raise MfaRejected() from exc
        if len(key) != 32:
            raise MfaRejected()
        return key

    @classmethod
    def _decrypt_secret(cls, authenticator: UserTotpAuthenticator) -> str:
        try:
            plaintext = AESGCM(cls._key_for_authenticator(authenticator)).decrypt(
                cls._b64d(authenticator.encryption_nonce),
                cls._b64d(authenticator.encrypted_secret),
                cls._aad(
                    authenticator.user_id,
                    authenticator.key_id,
                    authenticator.key_version,
                ),
            )
            return plaintext.decode("ascii")
        except (ValueError, UnicodeError) as exc:
            raise MfaRejected() from exc

    @classmethod
    def _matching_counter(cls, secret: str, code: str) -> int | None:
        if len(code) != cls._TOTP_DIGITS or not code.isdecimal():
            return None
        totp = pyotp.TOTP(
            secret,
            digits=cls._TOTP_DIGITS,
            interval=cls._TOTP_INTERVAL,
            digest=hashlib.sha1,
        )
        current = int(time.time()) // cls._TOTP_INTERVAL
        for counter in range(current - cls._TOTP_WINDOW, current + cls._TOTP_WINDOW + 1):
            if counter >= 0 and hmac.compare_digest(totp.at(counter * cls._TOTP_INTERVAL), code):
                return counter
        return None

    @classmethod
    def _recovery_verifier(cls, code: str) -> str:
        return hmac.new(
            cls._recovery_key(),
            code.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _event(
        self,
        *,
        event_type: str,
        user_id: int,
        organization_id: UUID,
        outcome: str,
        reason_code: str,
    ) -> None:
        self.db.add(
            AuthSecurityEvent(
                id=uuid4(),
                event_type=event_type,
                user_id=user_id,
                actor_user_id=user_id,
                organization_id=organization_id,
                outcome=outcome,
                reason_code=reason_code,
            )
        )

    def record_throttle_threshold(self, user: User, organization_id: UUID) -> None:
        self._event(
            event_type="auth_throttle_threshold",
            user_id=user.id,
            organization_id=organization_id,
            outcome="blocked",
            reason_code="mfa_verification_threshold",
        )
        self.db.commit()

    def status(self, user: User, organization_id: UUID) -> MfaStatus:
        policy = self.db.get(OrganizationMfaPolicy, organization_id)
        required = user.role == "admin" or (
            policy is not None and policy.member_policy == "required"
        )
        authenticator = (
            self.db.query(UserTotpAuthenticator)
            .filter(UserTotpAuthenticator.user_id == user.id)
            .one_or_none()
        )
        enrolled = authenticator is not None and authenticator.disabled_at is None
        active = enrolled and authenticator.verified_at is not None
        return MfaStatus(required=required, enrolled=enrolled, active=active)

    def start_enrollment(self, user: User, organization_id: UUID) -> EnrollmentStart:
        authenticator = (
            self.db.query(UserTotpAuthenticator)
            .filter(UserTotpAuthenticator.user_id == user.id)
            .with_for_update()
            .one_or_none()
        )
        if authenticator is not None and authenticator.verified_at is not None and authenticator.disabled_at is None:
            raise MfaRejected()

        secret = pyotp.random_base32(length=32)
        encrypted, nonce, key_id, key_version = self._encrypt_secret(user.id, secret)
        if authenticator is None:
            authenticator = UserTotpAuthenticator(
                id=uuid4(),
                user_id=user.id,
                encrypted_secret=encrypted,
                encryption_nonce=nonce,
                key_id=key_id,
                key_version=key_version,
            )
            self.db.add(authenticator)
        else:
            authenticator.encrypted_secret = encrypted
            authenticator.encryption_nonce = nonce
            authenticator.key_id = key_id
            authenticator.key_version = key_version
            authenticator.verified_at = None
            authenticator.disabled_at = None
            authenticator.last_accepted_counter = None

        self._event(
            event_type="mfa_enrollment_started",
            user_id=user.id,
            organization_id=organization_id,
            outcome="success",
            reason_code="totp_pending_verification",
        )
        self.db.commit()
        issuer = settings.PROJECT_NAME.replace(" ", "")
        uri = pyotp.TOTP(
            secret,
            digits=self._TOTP_DIGITS,
            interval=self._TOTP_INTERVAL,
            digest=hashlib.sha1,
        ).provisioning_uri(name=user.email, issuer_name=issuer)
        return EnrollmentStart(secret=secret, provisioning_uri=uri)

    def verify_enrollment(
        self,
        user: User,
        organization_id: UUID,
        code: str,
    ) -> EnrollmentComplete:
        authenticator = (
            self.db.query(UserTotpAuthenticator)
            .filter(UserTotpAuthenticator.user_id == user.id)
            .with_for_update()
            .one_or_none()
        )
        if authenticator is None or authenticator.disabled_at is not None or authenticator.verified_at is not None:
            raise MfaRejected()

        secret = self._decrypt_secret(authenticator)
        counter = self._matching_counter(secret, code)
        if counter is None or (
            authenticator.last_accepted_counter is not None
            and counter <= authenticator.last_accepted_counter
        ):
            raise MfaRejected()

        authenticator.last_accepted_counter = counter
        authenticator.verified_at = self._now()
        current_generation = (
            self.db.query(func.max(MfaRecoveryCode.generation))
            .filter(MfaRecoveryCode.user_id == user.id)
            .scalar()
            or 0
        )
        generation = current_generation + 1
        raw_codes: list[str] = []
        for ordinal in range(1, self._RECOVERY_COUNT + 1):
            code_value = secrets.token_urlsafe(18)
            raw_codes.append(code_value)
            self.db.add(
                MfaRecoveryCode(
                    id=uuid4(),
                    user_id=user.id,
                    generation=generation,
                    ordinal=ordinal,
                    code_verifier=self._recovery_verifier(code_value),
                )
            )

        self._event(
            event_type="mfa_enrollment_verified",
            user_id=user.id,
            organization_id=organization_id,
            outcome="success",
            reason_code="totp_active",
        )
        self._event(
            event_type="mfa_recovery_codes_generated",
            user_id=user.id,
            organization_id=organization_id,
            outcome="success",
            reason_code="initial_generation",
        )
        self.db.commit()
        return EnrollmentComplete(recovery_codes=tuple(raw_codes))

    def consume_recovery_code(self, user: User, organization_id: UUID, code: str) -> None:
        verifier = self._recovery_verifier(code)
        recovery = (
            self.db.query(MfaRecoveryCode)
            .filter(
                MfaRecoveryCode.user_id == user.id,
                MfaRecoveryCode.code_verifier == verifier,
                MfaRecoveryCode.used_at.is_(None),
            )
            .with_for_update()
            .one_or_none()
        )
        if recovery is None:
            raise MfaRejected()
        latest = self.db.query(func.max(MfaRecoveryCode.generation)).filter(MfaRecoveryCode.user_id == user.id).scalar()
        if latest is None or recovery.generation != latest:
            raise MfaRejected()
        recovery.used_at = self._now()
        self._event(event_type="mfa_recovery_code_used", user_id=user.id, organization_id=organization_id, outcome="success", reason_code="single_use_consumed")
        self.db.commit()

    def regenerate_recovery_codes(self, user: User, organization_id: UUID) -> tuple[str, ...]:
        authenticator = (
            self.db.query(UserTotpAuthenticator)
            .filter(UserTotpAuthenticator.user_id == user.id)
            .with_for_update()
            .one_or_none()
        )
        if authenticator is None or authenticator.disabled_at is not None or authenticator.verified_at is None:
            raise MfaRejected()
        existing = self.db.query(MfaRecoveryCode).filter(MfaRecoveryCode.user_id == user.id, MfaRecoveryCode.used_at.is_(None)).with_for_update().all()
        now = self._now()
        for item in existing:
            item.used_at = now
        current_generation = self.db.query(func.max(MfaRecoveryCode.generation)).filter(MfaRecoveryCode.user_id == user.id).scalar() or 0
        generation = current_generation + 1
        raw_codes = []
        for ordinal in range(1, self._RECOVERY_COUNT + 1):
            value = secrets.token_urlsafe(18)
            raw_codes.append(value)
            self.db.add(MfaRecoveryCode(id=uuid4(), user_id=user.id, generation=generation, ordinal=ordinal, code_verifier=self._recovery_verifier(value)))
        self._event(event_type="mfa_recovery_codes_generated", user_id=user.id, organization_id=organization_id, outcome="success", reason_code="regenerated")
        self.db.commit()
        return tuple(raw_codes)

    def verify_active_totp(self, user: User, organization_id: UUID, code: str) -> None:
        authenticator = (
            self.db.query(UserTotpAuthenticator)
            .filter(UserTotpAuthenticator.user_id == user.id)
            .with_for_update()
            .one_or_none()
        )
        if authenticator is None or authenticator.disabled_at is not None or authenticator.verified_at is None:
            raise MfaRejected()
        secret = self._decrypt_secret(authenticator)
        counter = self._matching_counter(secret, code)
        if counter is None or (authenticator.last_accepted_counter is not None and counter <= authenticator.last_accepted_counter):
            raise MfaRejected()
        authenticator.last_accepted_counter = counter
        self._event(event_type="mfa_verification", user_id=user.id, organization_id=organization_id, outcome="success", reason_code="active_totp")
        self.db.commit()
