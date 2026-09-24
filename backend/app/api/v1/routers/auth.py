from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token

from app.schemas.token import RefreshRequest, TokenResponse
from app.schemas.mfa import (
    MfaStatusResponse,
    TotpEnrollmentStartResponse,
    TotpEnrollmentVerifyRequest,
    TotpEnrollmentVerifyResponse,
)
from app.schemas.onboarding import ClosedOutcome, PasswordChangeRequest
from app.models.organization import Organization

from app.services.user_service import UserService
from app.dependencies.auth import (
    AuthenticatedOrganizationContext,
    get_current_user,
    get_current_user_organization_context,
)
from app.services.onboarding_service import OnboardingService, ProtectedOnboarding
from app.services.refresh_session_service import RefreshRejected, RefreshSessionService
from app.services.mfa_service import MfaRejected, MfaService
from app.services.auth_throttle_service import AuthThrottleService, ThrottleConfigurationError


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


service = UserService()


@router.post("/register", status_code=404)
def register_disabled():
    """Disconnected public registration is not a PATCH-041 onboarding path."""
    return {"outcome": "protected_not_found"}


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):

    user = service.authenticate(
        db,
        form_data.username,
        form_data.password,
    )


    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )


    try:
        refresh = RefreshSessionService(db).create(user)
    except RefreshRejected:
        db.rollback()
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    access_token = create_access_token(
        user.id,
        user.auth_version,
        session_id=refresh.session_id,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh.credential,
    )



@router.post("/refresh", response_model=TokenResponse)
def refresh_session(
    data: RefreshRequest,
    db: Session = Depends(get_db),
):
    try:
        user, refresh = RefreshSessionService(db).rotate(data.refresh_token)
    except RefreshRejected:
        db.rollback()
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
        )
    return TokenResponse(
        access_token=create_access_token(
            user.id,
            user.auth_version,
            session_id=refresh.session_id,
        ),
        refresh_token=refresh.credential,
    )


@router.get("/me")
def get_me(
    context: AuthenticatedOrganizationContext = Depends(
        get_current_user_organization_context
    ),
    db: Session = Depends(get_db),
):
    organization = db.get(Organization, context.organization_id)
    if organization is None or not organization.is_active:
        raise HTTPException(status_code=404, detail="Protected resource not found")
    return {
        "user_id": str(context.user.id),
        "username": context.user.username,
        "full_name": context.user.full_name,
        "role": context.user.role,
        "organization": {
            "id": str(context.organization_id),
            "name": organization.name,
            "slug": organization.slug,
        },
    }


@router.post("/change-password", response_model=ClosedOutcome)
async def change_password(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        data = PasswordChangeRequest.model_validate(await request.json())
        OnboardingService(db).change_password(
            current_user, data.current_password, data.new_password
        )
        return {"outcome": "success"}
    except (ProtectedOnboarding, ValidationError, ValueError, TypeError):
        db.rollback()
        return {"outcome": "invalid_request"}


@router.get("/mfa/status", response_model=MfaStatusResponse)
def mfa_status(
    context: AuthenticatedOrganizationContext = Depends(
        get_current_user_organization_context
    ),
    db: Session = Depends(get_db),
):
    status = MfaService(db).status(context.user, context.organization_id)
    return MfaStatusResponse(
        required=status.required,
        enrolled=status.enrolled,
        active=status.active,
    )


@router.post("/mfa/totp/enrollment", response_model=TotpEnrollmentStartResponse)
def start_totp_enrollment(
    context: AuthenticatedOrganizationContext = Depends(
        get_current_user_organization_context
    ),
    db: Session = Depends(get_db),
):
    try:
        enrollment = MfaService(db).start_enrollment(
            context.user, context.organization_id
        )
    except MfaRejected:
        db.rollback()
        raise HTTPException(status_code=409, detail="MFA enrollment unavailable")
    return TotpEnrollmentStartResponse(
        secret=enrollment.secret,
        provisioning_uri=enrollment.provisioning_uri,
    )


@router.post(
    "/mfa/totp/enrollment/verify",
    response_model=TotpEnrollmentVerifyResponse,
)
def verify_totp_enrollment(
    request: Request,
    data: TotpEnrollmentVerifyRequest,
    context: AuthenticatedOrganizationContext = Depends(
        get_current_user_organization_context
    ),
    db: Session = Depends(get_db),
):
    network_context = request.client.host if request.client else "unknown"
    throttle = AuthThrottleService(db)
    identity = str(context.user.id)
    try:
        if throttle.is_blocked("mfa_verification", identity, network_context):
            raise HTTPException(status_code=429, detail="Invalid MFA verification")
        completed = MfaService(db).verify_enrollment(
            context.user, context.organization_id, data.code
        )
        throttle.clear("mfa_verification", identity, network_context)
    except MfaRejected:
        db.rollback()
        try:
            threshold_reached = throttle.record_failure(
                "mfa_verification", identity, network_context
            )
            if threshold_reached:
                MfaService(db).record_throttle_threshold(
                    context.user, context.organization_id
                )
        except ThrottleConfigurationError:
            db.rollback()
        raise HTTPException(status_code=400, detail="Invalid MFA verification")
    except ThrottleConfigurationError:
        db.rollback()
        raise HTTPException(status_code=503, detail="MFA verification unavailable")
    return TotpEnrollmentVerifyResponse(
        recovery_codes=list(completed.recovery_codes)
    )
