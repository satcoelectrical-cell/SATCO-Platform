from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from jose import JWTError, jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(
    subject: str | Any,
    auth_version: int = 1,
    session_id: UUID | str | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {
        "sub": str(subject),
        "type": "access",
        "iat": now,
        "exp": expire,
        "jti": str(uuid4()),
        "iss": settings.ACCESS_TOKEN_ISSUER,
        "aud": settings.ACCESS_TOKEN_AUDIENCE,
        "av": auth_version,
        "sid": str(session_id or uuid4()),
    }
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
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
    except JWTError as exc:
        raise JWTError("Invalid token") from exc
