"""PATCH-041 Organization/User onboarding application service."""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import re
import secrets
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models.onboarding import AccountActionCredential, OnboardingIdempotency
from app.models.organization import Organization, UserOrganizationMembership
from app.models.user import User
from app.repositories.onboarding_repository import OnboardingRepository
from app.schemas.onboarding import MemberSummary, OrganizationSummary


class ProtectedOnboarding(Exception):
    pass


class OnboardingConflict(Exception):
    pass


def _now():
    return datetime.now(timezone.utc)


def _fingerprint(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()


def _clean(value: str, *, lower: bool = False) -> str:
    result = " ".join(value.strip().split())
    return result.lower() if lower else result


def _valid_email(value: str) -> bool:
    return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value))


class OnboardingService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = OnboardingRepository(db)

    @staticmethod
    def organization_summary(item: Organization) -> OrganizationSummary:
        return OrganizationSummary(id=item.id, name=item.name or "Organization", slug=item.slug or f"organization-{str(item.id)[:8]}", is_active=item.is_active)

    @staticmethod
    def member_summary(user: User, membership: UserOrganizationMembership) -> MemberSummary:
        return MemberSummary(
            user_id=user.id, username=user.username, email=user.email,
            full_name=user.full_name, role=user.role,
            account_active=user.is_active, activation_pending=user.activation_pending,
            membership_enabled=membership.is_enabled,
            membership_selected=membership.is_selected,
            version=max(user.version, membership.version),
        )

    def _issue(self, *, organization_id: UUID, user: User, purpose: str, issuer_id: int | None):
        now = _now()
        self.repo.revoke_live_credentials(user.id, purpose, now)
        token = secrets.token_urlsafe(32)
        lifetime = timedelta(hours=settings.ACCOUNT_ACTIVATION_EXPIRE_HOURS) if purpose == "activation" else timedelta(minutes=settings.ACCOUNT_RESET_EXPIRE_MINUTES)
        self.db.add(AccountActionCredential(
            id=uuid4(), organization_id=organization_id, user_id=user.id,
            purpose=purpose, token_digest=sha256(token.encode()).hexdigest(),
            expires_at=now + lifetime, issued_by_user_id=issuer_id,
        ))
        return token

    def _replay(self, scope: str, operation: str, key: UUID, fingerprint: str):
        prior = self.repo.idempotency(scope, operation, key)
        if not prior:
            return None
        if prior.request_fingerprint != fingerprint:
            raise OnboardingConflict()
        return prior.safe_result

    def _record_idempotency(self, scope: str, operation: str, key: UUID, fingerprint: str, safe_result: dict):
        self.db.add(OnboardingIdempotency(scope=scope, operation=operation, idempotency_key=key, request_fingerprint=fingerprint, safe_result=safe_result))

    def bootstrap(self, data, idempotency_key: UUID):
        payload = data.model_dump(); fp = _fingerprint(payload)
        replay = self._replay("platform", "bootstrap", idempotency_key, fp)
        if replay:
            org = self.repo.organization_by_slug(replay["organization_slug"])
            membership = self.repo.membership(org.id, replay["user_id"]) if org else None
            user = self.db.get(User, replay["user_id"])
            if not org or not user or not membership: raise ProtectedOnboarding()
            return self.organization_summary(org), self.member_summary(user, membership), None, True
        name = _clean(data.organization_name); slug = _clean(data.organization_slug, lower=True)
        username = _clean(data.admin_username); email = _clean(data.admin_email, lower=True)
        if not _valid_email(email) or self.repo.organization_by_slug(slug) or self.repo.user_by_identity(username, email): raise OnboardingConflict()
        org = Organization(id=uuid4(), name=name, slug=slug, is_active=True)
        user = User(email=email, username=username, full_name=_clean(data.admin_full_name) if data.admin_full_name else None, role="admin", hashed_password=hash_password(secrets.token_urlsafe(32)), is_active=False, activation_pending=True, auth_version=1, version=1)
        self.db.add_all([org, user]); self.db.flush()
        membership = UserOrganizationMembership(user_id=user.id, organization_id=org.id, is_enabled=True, is_selected=True, version=1)
        self.db.add(membership); token = self._issue(organization_id=org.id, user=user, purpose="activation", issuer_id=None)
        self.repo.audit(actor_id=None, action="ONBOARDING_ORGANIZATION_BOOTSTRAPPED", entity="ORGANIZATION", entity_uuid=org.id, details={"initial_admin_user_id": user.id, "organization_slug": slug})
        self._record_idempotency("platform", "bootstrap", idempotency_key, fp, {"organization_slug": slug, "user_id": user.id})
        self._commit()
        return self.organization_summary(org), self.member_summary(user, membership), token, False

    def provision(self, organization: Organization, actor: User, data, idempotency_key: UUID):
        payload = data.model_dump(); fp = _fingerprint(payload); scope = str(organization.id)
        replay = self._replay(scope, "provision", idempotency_key, fp)
        if replay:
            user = self.db.get(User, replay["user_id"]); membership = self.repo.membership(organization.id, replay["user_id"])
            if not user or not membership: raise ProtectedOnboarding()
            return self.member_summary(user, membership), None, True
        username = _clean(data.username); email = _clean(data.email, lower=True)
        if not _valid_email(email) or self.repo.user_by_identity(username, email): raise OnboardingConflict()
        user = User(email=email, username=username, full_name=_clean(data.full_name) if data.full_name else None, role=data.role, hashed_password=hash_password(secrets.token_urlsafe(32)), is_active=False, activation_pending=True, auth_version=1, version=1)
        self.db.add(user); self.db.flush()
        membership = UserOrganizationMembership(user_id=user.id, organization_id=organization.id, is_enabled=True, is_selected=True, version=1)
        self.db.add(membership); token = self._issue(organization_id=organization.id, user=user, purpose="activation", issuer_id=actor.id)
        self.repo.audit(actor_id=actor.id, action="ONBOARDING_MEMBER_PROVISIONED", entity="USER", entity_id=user.id, details={"role": data.role})
        self._record_idempotency(scope, "provision", idempotency_key, fp, {"user_id": user.id})
        self._commit()
        return self.member_summary(user, membership), token, False

    def complete_credential(self, *, token: str, new_password: str, purpose: str):
        credential = self.repo.credential_by_token(token)
        now = _now()
        if not credential or credential.purpose != purpose or credential.used_at or credential.revoked_at or credential.expires_at <= now:
            raise ProtectedOnboarding()
        user = self.db.query(User).filter(User.id == credential.user_id).with_for_update().one_or_none()
        membership = self.repo.membership(credential.organization_id, credential.user_id, lock=True)
        org = self.db.query(Organization).filter(Organization.id == credential.organization_id).with_for_update().one_or_none()
        if not user or not membership or not membership.is_enabled or not org or not org.is_active: raise ProtectedOnboarding()
        if purpose == "activation" and not user.activation_pending: raise ProtectedOnboarding()
        user.hashed_password = hash_password(new_password); user.is_active = True; user.activation_pending = False
        user.auth_version += 1; user.version += 1; credential.used_at = now
        self.repo.audit(actor_id=user.id, action=f"ONBOARDING_{purpose.upper()}_COMPLETED", entity="USER", entity_id=user.id, details={"auth_version": user.auth_version})
        self._commit()

    def change_password(self, user: User, current_password: str, new_password: str):
        locked = self.db.query(User).filter(User.id == user.id).with_for_update().one()
        if not verify_password(current_password, locked.hashed_password): raise ProtectedOnboarding()
        locked.hashed_password = hash_password(new_password); locked.auth_version += 1; locked.version += 1
        self.repo.audit(actor_id=user.id, action="ONBOARDING_PASSWORD_CHANGED", entity="USER", entity_id=user.id, details={"auth_version": locked.auth_version})
        self._commit()

    def list_members(self, organization_id: UUID):
        return [self.member_summary(user, membership) for user, membership in self.repo.members(organization_id)]

    def mutate_member(self, organization_id: UUID, actor: User, target_id: int, data, idempotency_key: UUID):
        operation = f"member_change:{target_id}"
        fingerprint = _fingerprint(data.model_dump())
        replay = self._replay(str(organization_id), operation, idempotency_key, fingerprint)
        if replay:
            membership = self.repo.membership(organization_id, replay["user_id"])
            target = self.db.get(User, replay["user_id"])
            if not membership or not target:
                raise ProtectedOnboarding()
            return self.member_summary(target, membership), True
        membership = self.repo.membership(organization_id, target_id, lock=True)
        target = self.db.query(User).filter(User.id == target_id).with_for_update().one_or_none()
        if not membership or not target or self.repo.memberships_for_user(target_id) != 1: raise ProtectedOnboarding()
        if max(target.version, membership.version) != data.expected_version: raise OnboardingConflict()
        removes_admin = target.role == "admin" and ((data.role is not None and data.role != "admin") or data.membership_enabled is False or data.account_active is False)
        if target.id == actor.id and removes_admin: raise ProtectedOnboarding()
        if removes_admin and self.repo.active_admin_count(organization_id) <= 1: raise ProtectedOnboarding()
        if data.role is not None: target.role = data.role
        if data.membership_enabled is not None:
            membership.is_enabled = data.membership_enabled
            membership.is_selected = data.membership_enabled
        if data.account_active is not None:
            if target.activation_pending and data.account_active: raise ProtectedOnboarding()
            target.is_active = data.account_active; target.auth_version += 1
        target.version += 1; membership.version += 1
        self.repo.audit(actor_id=actor.id, action="ONBOARDING_MEMBER_CHANGED", entity="USER", entity_id=target.id, details={"role": target.role, "account_active": target.is_active, "membership_enabled": membership.is_enabled})
        self._record_idempotency(str(organization_id), operation, idempotency_key, fingerprint, {"user_id": target.id})
        self._commit()
        return self.member_summary(target, membership), False

    def issue_reset(self, organization_id: UUID, actor_id: int | None, target_id: int, idempotency_key: UUID, *, scope: str | None = None, operation: str | None = None):
        idempotency_scope = scope or str(organization_id)
        idempotency_operation = operation or f"reset:{target_id}"
        fingerprint = _fingerprint({"organization_id": organization_id, "target_id": target_id})
        replay = self._replay(idempotency_scope, idempotency_operation, idempotency_key, fingerprint)
        if replay:
            membership = self.repo.membership(organization_id, replay["user_id"])
            user = self.db.get(User, replay["user_id"])
            if not membership or not user:
                raise ProtectedOnboarding()
            return self.member_summary(user, membership), None, True
        membership = self.repo.membership(organization_id, target_id, lock=True)
        user = self.db.query(User).filter(User.id == target_id).with_for_update().one_or_none()
        org = self.db.get(Organization, organization_id)
        if not membership or not membership.is_enabled or not user or user.activation_pending or not org or not org.is_active: raise ProtectedOnboarding()
        token = self._issue(organization_id=organization_id, user=user, purpose="reset", issuer_id=actor_id)
        self.repo.audit(actor_id=actor_id, action="ONBOARDING_RESET_ISSUED", entity="USER", entity_id=user.id, details={"purpose": "reset"})
        self._record_idempotency(idempotency_scope, idempotency_operation, idempotency_key, fingerprint, {"user_id": user.id})
        self._commit(); return self.member_summary(user, membership), token, False

    def platform_reset(self, slug: str, username: str, idempotency_key: UUID):
        org = self.repo.organization_by_slug(_clean(slug, lower=True), lock=True)
        user = self.repo.user_by_username(_clean(username))
        if not org or not user: raise ProtectedOnboarding()
        return self.issue_reset(org.id, None, user.id, idempotency_key, scope="platform", operation="platform_reset")

    def _commit(self):
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise OnboardingConflict() from exc
