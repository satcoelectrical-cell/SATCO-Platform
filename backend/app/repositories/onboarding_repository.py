"""No-commit persistence collaborator for PATCH-041."""

from datetime import datetime
from hashlib import sha256
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.onboarding import AccountActionCredential, OnboardingIdempotency
from app.models.organization import Organization, UserOrganizationMembership
from app.models.user import User


class OnboardingRepository:
    def __init__(self, db: Session):
        self.db = db

    def organization_by_slug(self, slug: str, *, lock: bool = False):
        query = self.db.query(Organization).filter(func.lower(Organization.slug) == slug.lower())
        return (query.with_for_update() if lock else query).one_or_none()

    def user_by_identity(self, username: str, email: str):
        return self.db.query(User).filter(
            (func.lower(User.username) == username.lower()) | (func.lower(User.email) == email.lower())
        ).first()

    def user_by_username(self, username: str):
        return self.db.query(User).filter(func.lower(User.username) == username.lower()).one_or_none()

    def membership(self, organization_id: UUID, user_id: int, *, lock: bool = False):
        query = self.db.query(UserOrganizationMembership).filter_by(organization_id=organization_id, user_id=user_id)
        return (query.with_for_update() if lock else query).one_or_none()

    def memberships_for_user(self, user_id: int) -> int:
        return self.db.query(UserOrganizationMembership).filter_by(user_id=user_id).count()

    def members(self, organization_id: UUID):
        return self.db.query(User, UserOrganizationMembership).join(
            UserOrganizationMembership, UserOrganizationMembership.user_id == User.id
        ).filter(UserOrganizationMembership.organization_id == organization_id).order_by(func.lower(User.username), User.id).limit(100).all()

    def active_admin_count(self, organization_id: UUID) -> int:
        rows = self.db.query(User.id).join(UserOrganizationMembership).filter(
            UserOrganizationMembership.organization_id == organization_id,
            UserOrganizationMembership.is_enabled.is_(True),
            User.is_active.is_(True),
            User.role == "admin",
        ).order_by(User.id).with_for_update(of=User).all()
        return len(rows)

    def credential_by_token(self, token: str, *, lock: bool = True):
        digest = sha256(token.encode()).hexdigest()
        query = self.db.query(AccountActionCredential).filter(AccountActionCredential.token_digest == digest)
        return (query.with_for_update() if lock else query).one_or_none()

    def revoke_live_credentials(self, user_id: int, purpose: str, now: datetime):
        self.db.query(AccountActionCredential).filter(
            AccountActionCredential.user_id == user_id,
            AccountActionCredential.purpose == purpose,
            AccountActionCredential.used_at.is_(None),
            AccountActionCredential.revoked_at.is_(None),
        ).update({"revoked_at": now}, synchronize_session=False)

    def idempotency(self, scope: str, operation: str, key: UUID):
        return self.db.query(OnboardingIdempotency).filter_by(scope=scope, operation=operation, idempotency_key=key).one_or_none()

    def audit(self, *, actor_id: int | None, action: str, entity: str, entity_id: int | None = None, entity_uuid: UUID | None = None, details: dict | None = None):
        self.db.add(AuditLog(user_id=actor_id, action=action, entity=entity, entity_id=entity_id, entity_uuid=entity_uuid, details=details or {}))
