"""Purpose-bound, one-time continuation for password-qualified MFA login."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
from uuid import UUID, uuid4

from jose import JWTError, jwt
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.auth_security import AuthSecurityEvent


class MfaLoginChallengeRejected(Exception):
    """Fail-closed continuation rejection without externally useful detail."""


@dataclass(frozen=True, slots=True)
class MfaLoginChallenge:
    user_id: int
    organization_id: UUID
    auth_version: int
    stage: str
    jti: UUID


class MfaLoginChallengeService:
    PURPOSE = "mfa_login"
    STAGES = frozenset({"verify", "enroll", "enroll_verify"})
    TTL_SECONDS = 5 * 60

    @classmethod
    def issue(
        cls,
        *,
        user_id: int,
        organization_id: UUID,
        auth_version: int,
        stage: str,
    ) -> str:
        if user_id < 1 or auth_version < 1 or stage not in cls.STAGES:
            raise MfaLoginChallengeRejected()
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "org": str(organization_id),
            "type": cls.PURPOSE,
            "stage": stage,
            "av": auth_version,
            "iat": now,
            "exp": now + timedelta(seconds=cls.TTL_SECONDS),
            "jti": str(uuid4()),
            "iss": settings.ACCESS_TOKEN_ISSUER,
            "aud": settings.ACCESS_TOKEN_AUDIENCE,
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @classmethod
    def verify(cls, token: str, *, expected_stage: str) -> MfaLoginChallenge:
        if expected_stage not in cls.STAGES:
            raise MfaLoginChallengeRejected()
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                issuer=settings.ACCESS_TOKEN_ISSUER,
                audience=settings.ACCESS_TOKEN_AUDIENCE,
                options={
                    "require_sub": True,
                    "require_iat": True,
                    "require_exp": True,
                    "require_jti": True,
                    "require_iss": True,
                    "require_aud": True,
                },
            )
            subject = payload["sub"]
            user_id = int(subject)
            organization_id = UUID(payload["org"])
            auth_version = payload["av"]
            stage = payload["stage"]
            jti = UUID(payload["jti"])
            issued_at = int(payload["iat"])
            expires_at = int(payload["exp"])
        except (JWTError, KeyError, TypeError, ValueError) as exc:
            raise MfaLoginChallengeRejected() from exc

        now = int(datetime.now(timezone.utc).timestamp())
        if (
            payload.get("type") != cls.PURPOSE
            or not isinstance(subject, str)
            or str(user_id) != subject
            or user_id < 1
            or isinstance(auth_version, bool)
            or not isinstance(auth_version, int)
            or auth_version < 1
            or stage != expected_stage
            or expires_at <= issued_at
            or expires_at - issued_at > cls.TTL_SECONDS
            or issued_at > now + 30
        ):
            raise MfaLoginChallengeRejected()

        return MfaLoginChallenge(
            user_id=user_id,
            organization_id=organization_id,
            auth_version=auth_version,
            stage=stage,
            jti=jti,
        )

    @staticmethod
    def _fingerprint(challenge: MfaLoginChallenge) -> str:
        digest = hashlib.sha256(
            f"satco:mfa-login:{challenge.jti}".encode("ascii")
        ).hexdigest()
        return f"challenge_sha256={digest}"

    @staticmethod
    def _advisory_lock_id(challenge: MfaLoginChallenge) -> int:
        digest = hashlib.sha256(challenge.jti.bytes).digest()
        return int.from_bytes(digest[:8], "big") & ((1 << 63) - 1)

    @classmethod
    def reserve_once(cls, db: Session, challenge: MfaLoginChallenge) -> None:
        """Serialize and reject reuse until the caller's transaction completes."""

        db.execute(select(func.pg_advisory_xact_lock(cls._advisory_lock_id(challenge))))
        consumed = (
            db.query(AuthSecurityEvent.id)
            .filter(
                AuthSecurityEvent.event_type == "mfa_login_challenge_consumed",
                AuthSecurityEvent.safe_context == cls._fingerprint(challenge),
            )
            .first()
        )
        if consumed is not None:
            raise MfaLoginChallengeRejected()

    @classmethod
    def mark_consumed(
        cls,
        db: Session,
        challenge: MfaLoginChallenge,
        *,
        session_id: UUID | None = None,
    ) -> None:
        db.add(
            AuthSecurityEvent(
                event_type="mfa_login_challenge_consumed",
                user_id=challenge.user_id,
                actor_user_id=challenge.user_id,
                organization_id=challenge.organization_id,
                session_id=session_id,
                outcome="success",
                reason_code=challenge.stage,
                safe_context=cls._fingerprint(challenge),
            )
        )
