"""Thin PATCH-041 bootstrap and Organization administration transport."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import (
    AuthenticatedOrganizationContext,
    AuthenticatedSessionContext,
    get_current_session_context,
    get_current_user_organization_context,
)
from app.models.organization import Organization
from app.schemas.onboarding import (
    BootstrapOrganizationRequest, ClosedOutcome, CredentialCompletionRequest,
    IssuedCredentialResult, MemberListResult, MemberMutationRequest,
    PlatformResetRequest, ProvisionMemberRequest,
)
from app.services.bootstrap_security_service import BootstrapRejected, BootstrapSecurityService, BootstrapUnavailable
from app.services.mfa_service import MfaService
from app.services.onboarding_service import OnboardingConflict, OnboardingService, ProtectedOnboarding
from app.services.refresh_session_service import RefreshSessionService

router = APIRouter(tags=["First-Customer Onboarding"])
IdempotencyKey = Annotated[str, Header(alias="Idempotency-Key")]
BootstrapKey = Annotated[str, Header(alias="X-SATCO-Bootstrap-Key")]



def _admin_context(context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context)):
    if context.user.role != "admin":
        raise HTTPException(status_code=404, detail="Protected resource not found")
    return context


def _issued(call):
    try:
        organization, member, token, replayed = call()
        return IssuedCredentialResult(outcome="success", organization=organization, member=member, one_time_token=token, replayed=replayed)
    except OnboardingConflict:
        return IssuedCredentialResult(outcome="version_conflict")
    except ProtectedOnboarding:
        return IssuedCredentialResult(outcome="protected_not_found")


@router.post("/platform/bootstrap/organizations", response_model=IssuedCredentialResult, response_model_exclude_none=True, response_model_exclude_defaults=True)
async def bootstrap_organization(request: Request, idempotency_key: IdempotencyKey, bootstrap_key: BootstrapKey, db: Session = Depends(get_db)):
    try:
        BootstrapSecurityService(db).qualify(
            bootstrap_key,
            request.client.host if request.client else "unknown",
            require_eligible=True,
        )
        data = BootstrapOrganizationRequest.model_validate(await request.json())
        key = UUID(idempotency_key)
    except BootstrapRejected:
        return IssuedCredentialResult(outcome="protected_not_found")
    except BootstrapUnavailable:
        raise HTTPException(status_code=503, detail="Bootstrap unavailable")
    except (ValidationError, ValueError, TypeError):
        return IssuedCredentialResult(outcome="invalid_request")
    return _issued(lambda: OnboardingService(db).bootstrap(data, key))


@router.post("/platform/bootstrap/resets", response_model=IssuedCredentialResult, response_model_exclude_none=True, response_model_exclude_defaults=True)
async def platform_reset(request: Request, idempotency_key: IdempotencyKey, bootstrap_key: BootstrapKey, db: Session = Depends(get_db)):
    try:
        BootstrapSecurityService(db).qualify(
            bootstrap_key,
            request.client.host if request.client else "unknown",
            require_eligible=True,
        )
        data = PlatformResetRequest.model_validate(await request.json())
        member, token, replayed = OnboardingService(db).platform_reset(data.organization_slug, data.username, UUID(idempotency_key))
        return IssuedCredentialResult(outcome="success", member=member, one_time_token=token, replayed=replayed)
    except BootstrapRejected:
        return IssuedCredentialResult(outcome="protected_not_found")
    except BootstrapUnavailable:
        raise HTTPException(status_code=503, detail="Bootstrap unavailable")
    except (ValidationError, ValueError, TypeError):
        return IssuedCredentialResult(outcome="invalid_request")
    except ProtectedOnboarding:
        db.rollback(); return IssuedCredentialResult(outcome="protected_not_found")


def _complete(data: CredentialCompletionRequest, purpose: str, db: Session):
    try:
        OnboardingService(db).complete_credential(token=data.token, new_password=data.new_password, purpose=purpose)
        return ClosedOutcome(outcome="success")
    except ProtectedOnboarding:
        db.rollback(); return ClosedOutcome(outcome="invalid_request")


@router.post("/auth/activate", response_model=ClosedOutcome)
async def activate(request: Request, db: Session = Depends(get_db)):
    try:
        return _complete(CredentialCompletionRequest.model_validate(await request.json()), "activation", db)
    except (ValidationError, ValueError, TypeError):
        return ClosedOutcome(outcome="invalid_request")


@router.post("/auth/reset", response_model=ClosedOutcome)
async def reset(request: Request, db: Session = Depends(get_db)):
    try:
        return _complete(CredentialCompletionRequest.model_validate(await request.json()), "reset", db)
    except (ValidationError, ValueError, TypeError):
        return ClosedOutcome(outcome="invalid_request")


@router.get("/organization-admin/members", response_model=MemberListResult)
def list_members(context=Depends(_admin_context), db: Session = Depends(get_db)):
    return MemberListResult(outcome="success", items=OnboardingService(db).list_members(context.organization_id))


@router.post("/organization-admin/bootstrap/re-enable", response_model=ClosedOutcome)
def reenable_bootstrap(
    request: Request,
    bootstrap_key: BootstrapKey,
    context=Depends(_admin_context),
    auth: AuthenticatedSessionContext = Depends(get_current_session_context),
    db: Session = Depends(get_db),
):
    if auth.user.id != context.user.id:
        raise HTTPException(status_code=404, detail="Protected resource not found")
    # Bootstrap re-enable is stronger than ordinary recent-auth: mandatory
    # administrator MFA must be active and this exact session must have a
    # recent successful step-up. A fresh password-only session is insufficient.
    if not MfaService(db).status(context.user, context.organization_id).active:
        raise HTTPException(status_code=403, detail="MFA assurance required")
    if not RefreshSessionService(db).has_recent_step_up(auth.session):
        raise HTTPException(status_code=403, detail="Recent authentication required")
    try:
        BootstrapSecurityService(db).reenable(
            actor_user_id=context.user.id,
            organization_id=context.organization_id,
            session_id=auth.session.id,
            supplied_secret=bootstrap_key,
            network_context=request.client.host if request.client else "unknown",
        )
    except BootstrapRejected:
        db.rollback()
        return ClosedOutcome(outcome="protected_not_found")
    except BootstrapUnavailable:
        db.rollback()
        raise HTTPException(status_code=503, detail="Bootstrap unavailable")
    return ClosedOutcome(outcome="success")


@router.post("/organization-admin/members", response_model=IssuedCredentialResult, response_model_exclude_none=True, response_model_exclude_defaults=True)
async def provision_member(request: Request, idempotency_key: IdempotencyKey, context=Depends(_admin_context), db: Session = Depends(get_db)):
    organization = db.get(Organization, context.organization_id)
    if not organization or not organization.is_active:
        return IssuedCredentialResult(outcome="protected_not_found")
    try:
        data = ProvisionMemberRequest.model_validate(await request.json())
        member, token, replayed = OnboardingService(db).provision(organization, context.user, data, UUID(idempotency_key))
        return IssuedCredentialResult(outcome="success", organization=OnboardingService.organization_summary(organization), member=member, one_time_token=token, replayed=replayed)
    except (ValidationError, ValueError, TypeError):
        return IssuedCredentialResult(outcome="invalid_request")
    except OnboardingConflict:
        db.rollback(); return IssuedCredentialResult(outcome="version_conflict")
    except ProtectedOnboarding:
        db.rollback(); return IssuedCredentialResult(outcome="protected_not_found")


@router.patch("/organization-admin/members/{user_id}", response_model=IssuedCredentialResult, response_model_exclude_none=True, response_model_exclude_defaults=True)
async def mutate_member(user_id: int, request: Request, idempotency_key: IdempotencyKey, context=Depends(_admin_context), db: Session = Depends(get_db)):
    try:
        data = MemberMutationRequest.model_validate(await request.json())
        member, replayed = OnboardingService(db).mutate_member(context.organization_id, context.user, user_id, data, UUID(idempotency_key))
        return IssuedCredentialResult(outcome="success", member=member, replayed=replayed)
    except (ValidationError, ValueError, TypeError):
        return IssuedCredentialResult(outcome="invalid_request")
    except OnboardingConflict:
        db.rollback(); return IssuedCredentialResult(outcome="version_conflict")
    except ProtectedOnboarding:
        db.rollback(); return IssuedCredentialResult(outcome="protected_not_found")


@router.post("/organization-admin/members/{user_id}/reset", response_model=IssuedCredentialResult, response_model_exclude_none=True, response_model_exclude_defaults=True)
def issue_reset(user_id: int, idempotency_key: IdempotencyKey, context=Depends(_admin_context), db: Session = Depends(get_db)):
    try:
        member, token, replayed = OnboardingService(db).issue_reset(context.organization_id, context.user.id, user_id, UUID(idempotency_key))
        return IssuedCredentialResult(outcome="success", member=member, one_time_token=token, replayed=replayed)
    except (ValueError, TypeError):
        return IssuedCredentialResult(outcome="invalid_request")
    except ProtectedOnboarding:
        db.rollback(); return IssuedCredentialResult(outcome="protected_not_found")
