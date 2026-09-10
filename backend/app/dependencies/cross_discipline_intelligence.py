"""Request-scoped PATCH-053 composition and signed cursors."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal, get_db
from app.dependencies.auth import (
    AuthenticatedOrganizationContext, get_current_user_organization_context,
)
from app.repositories.cross_discipline_repository import CrossDisciplineRepository
from app.services.cross_discipline_service import CrossDisciplineService


@dataclass(slots=True)
class CrossDisciplineApplication:
    context: AuthenticatedOrganizationContext
    db: Session
    repository: CrossDisciplineRepository
    service: CrossDisciplineService
    session_factory: object


def get_cross_discipline_application(
    context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context),
    db: Session = Depends(get_db),
) -> CrossDisciplineApplication:
    return CrossDisciplineApplication(
        context, db, CrossDisciplineRepository(db), CrossDisciplineService(),
        SessionLocal,
    )


def encode_cross_discipline_cursor(*, scope: dict, position: list[str]) -> str:
    body = {
        "scope": scope, "position": position,
        "expires_at": int((datetime.now(timezone.utc) + timedelta(minutes=15)).timestamp()),
    }
    raw = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    signature = hmac.new(settings.resolved_secret_key().encode(), raw, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(raw + signature).decode().rstrip("=")


def decode_cross_discipline_cursor(cursor: str | None, *, scope: dict):
    if cursor is None:
        return None
    try:
        encoded = cursor.encode("ascii")
        combined = base64.urlsafe_b64decode(encoded + b"=" * (-len(encoded) % 4))
        if len(combined) < 33:
            raise ValueError
        raw, signature = combined[:-32], combined[-32:]
        expected = hmac.new(settings.resolved_secret_key().encode(), raw, hashlib.sha256).digest()
        value = json.loads(raw)
        if (
            not hmac.compare_digest(signature, expected)
            or value.get("scope") != scope
            or value.get("expires_at", 0) < int(datetime.now(timezone.utc).timestamp())
            or not isinstance(value.get("position"), list)
            or not all(isinstance(item, str) and len(item) <= 128 for item in value["position"])
        ):
            raise ValueError
        return value["position"]
    except Exception as error:
        raise HTTPException(status_code=422, detail="INVALID_CROSS_DISCIPLINE_CURSOR") from error
