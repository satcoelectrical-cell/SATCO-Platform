"""Request composition and signed pagination for Batch-1 standards operations."""

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
from app.core.database import get_db
from app.dependencies.auth import AuthenticatedOrganizationContext, get_current_user_organization_context
from app.repositories.standards_repository import StandardsRepository
from app.services.standards_service import StandardsService
from app.standards.providers import platform_catalog_admin_ids


@dataclass(slots=True)
class StandardsApplication:
    context: AuthenticatedOrganizationContext
    db: Session
    repository: StandardsRepository
    service: StandardsService


def get_standards_application(context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context), db: Session = Depends(get_db)) -> StandardsApplication:
    repository = StandardsRepository(db)
    return StandardsApplication(context=context, db=db, repository=repository, service=StandardsService(db, repository))


def is_organization_standards_admin(application: StandardsApplication) -> bool:
    return application.context.user.role == "admin"


def is_platform_catalog_admin(application: StandardsApplication) -> bool:
    return application.context.user.role == "admin" and application.context.user.id in platform_catalog_admin_ids()


def encode_standards_cursor(*, scope: dict, position: str) -> str:
    body = {"scope": scope, "position": position, "expires_at": int((datetime.now(timezone.utc) + timedelta(minutes=15)).timestamp())}
    raw = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    signature = hmac.new(settings.resolved_secret_key().encode(), raw, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(raw + signature).decode().rstrip("=")


def decode_standards_cursor(cursor: str | None, *, scope: dict) -> str | None:
    if cursor is None: return None
    try:
        raw_and_signature = base64.urlsafe_b64decode(cursor.encode("ascii") + b"=" * (-len(cursor) % 4))
        raw, signature = raw_and_signature[:-32], raw_and_signature[-32:]
        value = json.loads(raw)
        valid = len(raw_and_signature) >= 33 and hmac.compare_digest(signature, hmac.new(settings.resolved_secret_key().encode(), raw, hashlib.sha256).digest())
        if not valid or value.get("scope") != scope or value.get("expires_at", 0) < int(datetime.now(timezone.utc).timestamp()) or not isinstance(value.get("position"), str): raise ValueError
        return value["position"]
    except Exception as error:
        raise HTTPException(status_code=422, detail="INVALID_REQUEST") from error
