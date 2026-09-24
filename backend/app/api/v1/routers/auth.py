from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, verify_password

from app.schemas.token import RefreshRequest, TokenResponse
from app.schemas.mfa import (
    MfaStatusResponse,
    TotpEnrollmentStartResponse,
    TotpEnrollmentVerifyRequest,
    TotpEnrollmentVerifyResponse,
    RecoveryCodeRequest,
    RecoveryCodesResponse,
    StepUpRequest,
)
from app.schemas.onboarding import ClosedOutcome, PasswordChangeRequest
from app.models.organization import Organization, UserOrganizationMembership

from app.services.user_service import UserService
from app.dependencies.auth import (
    AuthenticatedOrganizationContext,
    get_current_user,
    get_current_user_organization_context,
    get_current_session_context,
    AuthenticatedSessionContext,
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


@router.get("/sessions")
def list_sessions(
    auth: AuthenticatedSessionContext = Depends(get_current_session_context),
    db: Session = Depends(get_db),
):
    sessions = RefreshSessionService(db).list_active(auth.user)
    return {"sessions": [
        {
            "id": str(item.id),
            "current": item.id == auth.session.id,
            "created_at": item.created_at,
            "expires_at": item.expires_at,
            "device_label": item.device_label,
        }
        for item in sessions
    ]}


@router.post("/logout", response_model=ClosedOutcome)
def logout_current(
    auth: AuthenticatedSessionContext = Depends(get_current_session_context),
    db: Session = Depends(get_db),
):
    RefreshSessionService(db).revoke_current(auth.user, auth.session.id)
    return {"outcome": "success"}


@router.post("/step-up", response_model=ClosedOutcome)
def step_up(
    data: StepUpRequest,
    context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context),
    auth: AuthenticatedSessionContext = Depends(get_current_session_context),
    db: Session = Depends(get_db),
):
    if context.user.id != auth.user.id or not verify_password(data.password, auth.user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    mfa = MfaService(db)
    status = mfa.status(auth.user, context.organization_id)
    if status.required or status.active:
        if not data.totp_code:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        try:
            mfa.verify_active_totp(auth.user, context.organization_id, data.totp_code)
        except MfaRejected:
            db.rollback()
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    RefreshSessionService(db).record_step_up(auth.user, auth.session)
    return {"outcome": "success"}


@router.post("/logout-all", response_model=ClosedOutcome)
def logout_all(
    auth: AuthenticatedSessionContext = Depends(get_current_session_context),
    db: Session = Depends(get_db),
):
    sessions = RefreshSessionService(db)
    if not sessions.has_recent_authentication(auth.session):
        raise HTTPException(status_code=403, detail="Recent authentication required")
    sessions.revoke_all(auth.user)
    return {"outcome": "success"}


@router.post("/mfa/recovery-code/use", response_model=ClosedOutcome)
def use_recovery_code(
    data: RecoveryCodeRequest,
    context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context),
    db: Session = Depends(get_db),
):
    try:
        MfaService(db).consume_recovery_code(context.user, context.organization_id, data.code)
    except MfaRejected:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid recovery credential")
    return {"outcome": "success"}


@router.post("/mfa/recovery-codes/regenerate", response_model=RecoveryCodesResponse)
def regenerate_recovery_codes(
    context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context),
    auth: AuthenticatedSessionContext = Depends(get_current_session_context),
    db: Session = Depends(get_db),
):
    sessions = RefreshSessionService(db)
    if not sessions.has_recent_authentication(auth.session):
        raise HTTPException(status_code=403, detail="Recent authentication required")
    try:
        codes = MfaService(db).regenerate_recovery_codes(context.user, context.organization_id)
    except MfaRejected:
        db.rollback()
        raise HTTPException(status_code=409, detail="MFA recovery unavailable")
    return RecoveryCodesResponse(recovery_codes=list(codes))


@router.post("/admin/users/{user_id}/sessions/revoke", response_model=ClosedOutcome)
def admin_revoke_user_sessions(
    user_id: int,
    context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context),
    auth: AuthenticatedSessionContext = Depends(get_current_session_context),
    db: Session = Depends(get_db),
):
    if auth.user.role != "admin" or context.user.id != auth.user.id:
        raise HTTPException(status_code=403, detail="Permission denied")
    sessions = RefreshSessionService(db)
    if not sessions.has_recent_authentication(auth.session):
        raise HTTPException(status_code=403, detail="Recent authentication required")
    target = (
        db.query(type(auth.user))
        .join(UserOrganizationMembership, UserOrganizationMembership.user_id == type(auth.user).id)
        .filter(
            type(auth.user).id == user_id,
            UserOrganizationMembership.organization_id == context.organization_id,
            UserOrganizationMembership.is_enabled.is_(True),
        )
        .one_or_none()
    )
    if target is None:
        raise HTTPException(status_code=404, detail="Protected resource not found")
    try:
        sessions.revoke_target(auth.user, target)
    except RefreshRejected:
        db.rollback()
        raise HTTPException(status_code=403, detail="Permission denied")
    return {"outcome": "success"}
