"""PATCH-058 browser authentication transport security."""

import hmac
import secrets

from fastapi import HTTPException, Request, Response

from app.core.config import settings


REFRESH_COOKIE_NAME = "satco_refresh"
CSRF_COOKIE_NAME = "satco_csrf"
CSRF_HEADER_NAME = "X-CSRF-Token"

# Restrict the credential to the authentication surface. The auth router is
# mounted directly at /auth in the current application topology, and refresh
# and logout are sibling endpoints beneath that bounded surface.
AUTH_COOKIE_PATH = "/auth"
# The SPA must read the non-secret double-submit value while it is rendered on
# application routes such as /login and /.  Keeping this at /auth would make
# document.cookie omit it outside that path and prevent refresh/logout calls.
CSRF_COOKIE_PATH = "/"


class BrowserAuthSecurityService:
    @staticmethod
    def _secure_cookie() -> bool:
        return settings.SATCO_ENVIRONMENT == "production"

    @staticmethod
    def _allowed_origins() -> set[str]:
        return {
            value.strip().rstrip("/")
            for value in settings.SATCO_ALLOWED_ORIGINS.split(",")
            if value.strip()
        }

    @classmethod
    def issue(
        cls,
        response: Response,
        refresh_credential: str,
        *,
        max_age: int,
    ) -> str:
        csrf_value = secrets.token_urlsafe(32)

        response.set_cookie(
            key=REFRESH_COOKIE_NAME,
            value=refresh_credential,
            max_age=max_age,
            httponly=True,
            secure=cls._secure_cookie(),
            samesite="lax",
            path=AUTH_COOKIE_PATH,
        )
        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=csrf_value,
            max_age=max_age,
            httponly=False,
            secure=cls._secure_cookie(),
            samesite="lax",
            path=CSRF_COOKIE_PATH,
        )
        return csrf_value

    @classmethod
    def clear(cls, response: Response) -> None:
        response.delete_cookie(
            REFRESH_COOKIE_NAME,
            path=AUTH_COOKIE_PATH,
            secure=cls._secure_cookie(),
            httponly=True,
            samesite="lax",
        )
        response.delete_cookie(
            CSRF_COOKIE_NAME,
            path=CSRF_COOKIE_PATH,
            secure=cls._secure_cookie(),
            httponly=False,
            samesite="lax",
        )

    @classmethod
    def refresh_credential(cls, request: Request) -> str:
        credential = request.cookies.get(REFRESH_COOKIE_NAME)
        if not credential:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
            )
        return credential

    @classmethod
    def require_csrf(cls, request: Request) -> None:
        origin = request.headers.get("origin")
        allowed_origins = cls._allowed_origins()

        if settings.SATCO_ENVIRONMENT == "production":
            if not origin or origin.rstrip("/") not in allowed_origins:
                raise HTTPException(
                    status_code=403,
                    detail="Invalid request origin",
                )
        elif origin and allowed_origins and origin.rstrip("/") not in allowed_origins:
            raise HTTPException(
                status_code=403,
                detail="Invalid request origin",
            )

        cookie_value = request.cookies.get(CSRF_COOKIE_NAME)
        header_value = request.headers.get(CSRF_HEADER_NAME)

        if (
            not cookie_value
            or not header_value
            or not hmac.compare_digest(cookie_value, header_value)
        ):
            raise HTTPException(
                status_code=403,
                detail="Invalid CSRF token",
            )
