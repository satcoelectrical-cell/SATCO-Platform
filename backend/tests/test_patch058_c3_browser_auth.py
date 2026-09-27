from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException, Request, Response

from app.services.browser_auth_security_service import (
    AUTH_COOKIE_PATH,
    BrowserAuthSecurityService,
    CSRF_COOKIE_PATH,
    CSRF_COOKIE_NAME,
    CSRF_HEADER_NAME,
    REFRESH_COOKIE_NAME,
)


def _request(
    *,
    cookies: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> Request:
    raw_headers = [
        (key.lower().encode(), value.encode())
        for key, value in (headers or {}).items()
    ]
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/auth/refresh",
        "headers": raw_headers,
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "scheme": "http",
        "query_string": b"",
    }
    request = Request(scope)
    request._cookies = cookies or {}
    return request


def _set_cookie_headers(response: Response) -> list[str]:
    return [
        value.decode()
        for key, value in response.raw_headers
        if key.lower() == b"set-cookie"
    ]


def test_issue_sets_refresh_http_only_and_csrf_non_http_only(monkeypatch):
    monkeypatch.setattr(
        "app.services.browser_auth_security_service.settings.SATCO_ENVIRONMENT",
        "development",
    )
    response = Response()

    csrf = BrowserAuthSecurityService.issue(
        response,
        "selector.secret",
        max_age=600,
    )

    headers = _set_cookie_headers(response)
    refresh = next(item for item in headers if item.startswith(f"{REFRESH_COOKIE_NAME}="))
    csrf_cookie = next(item for item in headers if item.startswith(f"{CSRF_COOKIE_NAME}="))

    assert "HttpOnly" in refresh
    assert "SameSite=lax" in refresh
    assert f"Path={AUTH_COOKIE_PATH}" in refresh
    assert "Max-Age=600" in refresh
    assert "Secure" not in refresh

    assert "HttpOnly" not in csrf_cookie
    assert "SameSite=lax" in csrf_cookie
    assert f"Path={CSRF_COOKIE_PATH}" in csrf_cookie
    assert "Max-Age=600" in csrf_cookie
    assert csrf


def test_production_cookies_are_secure(monkeypatch):
    monkeypatch.setattr(
        "app.services.browser_auth_security_service.settings.SATCO_ENVIRONMENT",
        "production",
    )
    response = Response()

    BrowserAuthSecurityService.issue(
        response,
        "selector.secret",
        max_age=600,
    )

    assert all("Secure" in item for item in _set_cookie_headers(response))


def test_refresh_credential_is_read_only_from_cookie():
    request = _request(cookies={REFRESH_COOKIE_NAME: "selector.secret"})
    assert BrowserAuthSecurityService.refresh_credential(request) == "selector.secret"


def test_missing_refresh_cookie_is_closed():
    with pytest.raises(HTTPException) as exc:
        BrowserAuthSecurityService.refresh_credential(_request())
    assert exc.value.status_code == 401


def test_csrf_requires_matching_double_submit_value(monkeypatch):
    monkeypatch.setattr(
        "app.services.browser_auth_security_service.settings.SATCO_ENVIRONMENT",
        "development",
    )
    monkeypatch.setattr(
        "app.services.browser_auth_security_service.settings.SATCO_ALLOWED_ORIGINS",
        "",
    )
    request = _request(
        cookies={CSRF_COOKIE_NAME: "csrf-value"},
        headers={CSRF_HEADER_NAME: "csrf-value"},
    )
    BrowserAuthSecurityService.require_csrf(request)


@pytest.mark.parametrize(
    ("cookie_value", "header_value"),
    [
        ("csrf-value", None),
        (None, "csrf-value"),
        ("csrf-value", "different"),
    ],
)
def test_csrf_rejects_absent_or_mismatched_values(
    monkeypatch,
    cookie_value,
    header_value,
):
    monkeypatch.setattr(
        "app.services.browser_auth_security_service.settings.SATCO_ENVIRONMENT",
        "development",
    )
    monkeypatch.setattr(
        "app.services.browser_auth_security_service.settings.SATCO_ALLOWED_ORIGINS",
        "",
    )

    cookies = {CSRF_COOKIE_NAME: cookie_value} if cookie_value else {}
    headers = {CSRF_HEADER_NAME: header_value} if header_value else {}

    with pytest.raises(HTTPException) as exc:
        BrowserAuthSecurityService.require_csrf(
            _request(cookies=cookies, headers=headers)
        )

    assert exc.value.status_code == 403


def test_production_requires_allowed_origin(monkeypatch):
    monkeypatch.setattr(
        "app.services.browser_auth_security_service.settings.SATCO_ENVIRONMENT",
        "production",
    )
    monkeypatch.setattr(
        "app.services.browser_auth_security_service.settings.SATCO_ALLOWED_ORIGINS",
        "https://satco.example",
    )

    rejected = _request(
        cookies={CSRF_COOKIE_NAME: "csrf"},
        headers={
            CSRF_HEADER_NAME: "csrf",
            "Origin": "https://evil.example",
        },
    )
    with pytest.raises(HTTPException) as exc:
        BrowserAuthSecurityService.require_csrf(rejected)
    assert exc.value.status_code == 403

    accepted = _request(
        cookies={CSRF_COOKIE_NAME: "csrf"},
        headers={
            CSRF_HEADER_NAME: "csrf",
            "Origin": "https://satco.example",
        },
    )
    BrowserAuthSecurityService.require_csrf(accepted)


def test_clear_expires_both_cookies(monkeypatch):
    monkeypatch.setattr(
        "app.services.browser_auth_security_service.settings.SATCO_ENVIRONMENT",
        "development",
    )
    response = Response()

    BrowserAuthSecurityService.clear(response)

    headers = _set_cookie_headers(response)
    assert any(item.startswith(f"{REFRESH_COOKIE_NAME}=") for item in headers)
    assert any(item.startswith(f"{CSRF_COOKIE_NAME}=") for item in headers)
    assert all("Max-Age=0" in item for item in headers)
    refresh = next(item for item in headers if item.startswith(f"{REFRESH_COOKIE_NAME}="))
    csrf_cookie = next(item for item in headers if item.startswith(f"{CSRF_COOKIE_NAME}="))
    assert f"Path={AUTH_COOKIE_PATH}" in refresh
    assert f"Path={CSRF_COOKIE_PATH}" in csrf_cookie
