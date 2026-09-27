from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import ValidationError
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, verify_password

from app.schemas.token import TokenResponse
from app.schemas.mfa import (
    MfaLoginChallengeResponse,
    MfaLoginEnrollmentStartRequest,
    MfaLoginEnrollmentStartResponse,
    MfaLoginEnrollmentVerifyResponse,
    MfaLoginVerifyRequest,
    MfaStatusResponse,
    TotpEnrollmentStartResponse,
    TotpEnrollmentVerifyRequest,
    TotpEnrollmentVerifyResponse,
    RecoveryCodeRequest,
    RecoveryCodesResponse,
    StepUpRequest,
    RecoveryIssueRequest,
    RecoveryIssueResponse,
    AccountRecoveryCompleteRequest,
    MfaRecoveryCompleteRequest,
)
from app.schemas.onboarding import ClosedOutcome, PasswordChangeRequest
from app.models.organization import Organization, UserOrganizationMembership
from app.models.user import User

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
from app.services.browser_auth_security_service import BrowserAuthSecurityService
from app.services.mfa_service import MfaRejected, MfaService
from app.services.mfa_login_challenge_service import (
    MfaLoginChallenge,
    MfaLoginChallengeRejected,
    MfaLoginChallengeService,
)
from app.services.auth_throttle_service import AuthThrottleService, ThrottleConfigurationError
from app.services.recovery_service import RecoveryRejected, RecoveryService


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


service = UserService()


def _refresh_max_age(expires_at: datetime) -> int:
    now = datetime.now(timezone.utc)
    return max(0, int((expires_at - now).total_seconds()))


def _selected_membership(
    db: Session,
    user_id: int,
    *,
    lock: bool = False,
) -> UserOrganizationMembership | None:
    query = (
        db.query(UserOrganizationMembership)
        .join(
            Organization,
            Organization.id == UserOrganizationMembership.organization_id,
        )
        .filter(
            UserOrganizationMembership.user_id == user_id,
            UserOrganizationMembership.is_selected.is_(True),
            UserOrganizationMembership.is_enabled.is_(True),
            Organization.is_active.is_(True),
        )
    )
    if lock:
        query = query.with_for_update()
    memberships = query.limit(2).all()
    return memberships[0] if len(memberships) == 1 else None


def _challenge_context(
    db: Session,
    token: str,
    *,
    expected_stage: str,
) -> tuple[MfaLoginChallenge, User]:
    challenge = MfaLoginChallengeService.verify(
        token,
        expected_stage=expected_stage,
    )
    user = (
        db.query(User)
        .filter(User.id == challenge.user_id)
        .with_for_update()
        .one_or_none()
    )
    if (
        user is None
        or not user.is_active
        or user.activation_pending
        or user.auth_version != challenge.auth_version
    ):
        raise MfaLoginChallengeRejected()
    membership = _selected_membership(db, user.id, lock=True)
    if (
        membership is None
        or membership.organization_id != challenge.organization_id
    ):
        raise MfaLoginChallengeRejected()
    return challenge, user


def _issue_browser_session(
    response: Response,
    db: Session,
    user: User,
    challenge: MfaLoginChallenge,
) -> TokenResponse:
    refresh = RefreshSessionService(db).create(user, commit=False)
    MfaLoginChallengeService.mark_consumed(
        db,
        challenge,
        session_id=refresh.session_id,
    )
    db.commit()
    BrowserAuthSecurityService.issue(
        response,
        refresh.credential,
        max_age=_refresh_max_age(refresh.expires_at),
    )
    return TokenResponse(
        access_token=create_access_token(
            user.id,
            user.auth_version,
            session_id=refresh.session_id,
        )
    )


def _mfa_failure(
    db: Session,
    user: User,
    organization_id: UUID,
    network_context: str,
) -> None:
    db.rollback()
    throttle = AuthThrottleService(db)
    try:
        threshold_reached = throttle.record_failure(
            "mfa_login_verification",
            str(user.id),
            network_context,
        )
        if threshold_reached:
            MfaService(db).record_throttle_threshold(user, organization_id)
    except ThrottleConfigurationError:
        db.rollback()


@router.post("/register", status_code=404)
def register_disabled():
    """Disconnected public registration is not a PATCH-041 onboarding path."""
    return {"outcome": "protected_not_found"}


@router.post(
    "/login",
    response_model=TokenResponse | MfaLoginChallengeResponse,
)
def login(
    response: Response,
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


    membership = _selected_membership(db, user.id)
    if membership is None or user.activation_pending:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    mfa_status = MfaService(db).status(user, membership.organization_id)
    if mfa_status.required:
        BrowserAuthSecurityService.clear(response)
        return MfaLoginChallengeResponse(
            challenge=MfaLoginChallengeService.issue(
                user_id=user.id,
                organization_id=membership.organization_id,
                auth_version=user.auth_version,
                stage="verify" if mfa_status.active else "enroll",
            ),
            enrollment_required=not mfa_status.active,
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

    BrowserAuthSecurityService.issue(
        response,
        refresh.credential,
        max_age=_refresh_max_age(refresh.expires_at),
    )

    return TokenResponse(
        access_token=access_token,
    )


@router.post("/login/mfa/verify", response_model=TokenResponse)
def verify_mfa_login(
    data: MfaLoginVerifyRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    network_context = request.client.host if request.client else "unknown"
    try:
        challenge, user = _challenge_context(
            db,
            data.challenge,
            expected_stage="verify",
        )
        status = MfaService(db).status(user, challenge.organization_id)
        if not status.required or not status.active:
            raise MfaLoginChallengeRejected()
        MfaLoginChallengeService.reserve_once(db, challenge)
        throttle = AuthThrottleService(db)
        if throttle.is_blocked(
            "mfa_login_verification",
            str(user.id),
            network_context,
        ):
            db.rollback()
            raise HTTPException(
                status_code=429,
                detail="Invalid authentication credentials",
            )
        MfaService(db).verify_active_totp(
            user,
            challenge.organization_id,
            data.code,
            commit=False,
        )
        throttle.clear(
            "mfa_login_verification",
            str(user.id),
            network_context,
            commit=False,
        )
        return _issue_browser_session(response, db, user, challenge)
    except MfaRejected:
        _mfa_failure(db, user, challenge.organization_id, network_context)
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
        )
    except MfaLoginChallengeRejected:
        db.rollback()
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
        )
    except RefreshRejected:
        db.rollback()
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
        )
    except ThrottleConfigurationError:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Authentication unavailable",
        )


@router.post(
    "/login/mfa/enrollment",
    response_model=MfaLoginEnrollmentStartResponse,
)
def start_mfa_login_enrollment(
    data: MfaLoginEnrollmentStartRequest,
    db: Session = Depends(get_db),
):
    try:
        challenge, user = _challenge_context(
            db,
            data.challenge,
            expected_stage="enroll",
        )
        status = MfaService(db).status(user, challenge.organization_id)
        if not status.required or status.active:
            raise MfaLoginChallengeRejected()
        MfaLoginChallengeService.reserve_once(db, challenge)
        enrollment = MfaService(db).start_enrollment(
            user,
            challenge.organization_id,
            commit=False,
        )
        MfaLoginChallengeService.mark_consumed(db, challenge)
        db.commit()
        return MfaLoginEnrollmentStartResponse(
            challenge=MfaLoginChallengeService.issue(
                user_id=user.id,
                organization_id=challenge.organization_id,
                auth_version=user.auth_version,
                stage="enroll_verify",
            ),
            secret=enrollment.secret,
            provisioning_uri=enrollment.provisioning_uri,
        )
    except (MfaLoginChallengeRejected, MfaRejected):
        db.rollback()
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
        )


@router.post(
    "/login/mfa/enrollment/verify",
    response_model=MfaLoginEnrollmentVerifyResponse,
)
def verify_mfa_login_enrollment(
    data: MfaLoginVerifyRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    network_context = request.client.host if request.client else "unknown"
    try:
        challenge, user = _challenge_context(
            db,
            data.challenge,
            expected_stage="enroll_verify",
        )
        status = MfaService(db).status(user, challenge.organization_id)
        if not status.required or not status.enrolled or status.active:
            raise MfaLoginChallengeRejected()
        MfaLoginChallengeService.reserve_once(db, challenge)
        throttle = AuthThrottleService(db)
        if throttle.is_blocked(
            "mfa_login_verification",
            str(user.id),
            network_context,
        ):
            db.rollback()
            raise HTTPException(
                status_code=429,
                detail="Invalid authentication credentials",
            )
        completed = MfaService(db).verify_enrollment(
            user,
            challenge.organization_id,
            data.code,
            commit=False,
        )
        throttle.clear(
            "mfa_login_verification",
            str(user.id),
            network_context,
            commit=False,
        )
        token = _issue_browser_session(response, db, user, challenge)
        return MfaLoginEnrollmentVerifyResponse(
            access_token=token.access_token,
            recovery_codes=list(completed.recovery_codes),
        )
    except MfaRejected:
        _mfa_failure(db, user, challenge.organization_id, network_context)
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
        )
    except MfaLoginChallengeRejected:
        db.rollback()
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
        )
    except RefreshRejected:
        db.rollback()
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
        )
    except ThrottleConfigurationError:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Authentication unavailable",
        )



@router.post("/refresh", response_model=TokenResponse)
def refresh_session(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    BrowserAuthSecurityService.require_csrf(request)

    try:
        credential = BrowserAuthSecurityService.refresh_credential(request)
        user, refresh = RefreshSessionService(db).rotate(credential)
    except RefreshRejected:
        db.rollback()
        BrowserAuthSecurityService.clear(response)
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
        )

    BrowserAuthSecurityService.issue(
        response,
        refresh.credential,
        max_age=_refresh_max_age(refresh.expires_at),
    )

    return TokenResponse(
        access_token=create_access_token(
            user.id,
            user.auth_version,
            session_id=refresh.session_id,
        ),
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
    request: Request,
    response: Response,
    auth: AuthenticatedSessionContext = Depends(get_current_session_context),
    db: Session = Depends(get_db),
):
    BrowserAuthSecurityService.require_csrf(request)
    RefreshSessionService(db).revoke_current(auth.user, auth.session.id)
    BrowserAuthSecurityService.clear(response)
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


@router.post("/admin/users/{user_id}/recovery", response_model=RecoveryIssueResponse)
def issue_security_recovery(
    user_id: int,
    data: RecoveryIssueRequest,
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
        issued = RecoveryService(db).issue(actor=auth.user, target=target, organization_id=context.organization_id, purpose=data.purpose)
    except RecoveryRejected:
        db.rollback()
        raise HTTPException(status_code=404, detail="Protected resource not found")
    return RecoveryIssueResponse(recovery_credential=issued.credential, expires_at=issued.expires_at)


@router.post("/recovery/account/complete", response_model=ClosedOutcome)
def complete_account_recovery(data: AccountRecoveryCompleteRequest, request: Request, db: Session = Depends(get_db)):
    network_context = request.client.host if request.client else "unknown"
    throttle = AuthThrottleService(db)
    identity = data.recovery_credential.partition(".")[0]
    try:
        if throttle.is_blocked("recovery_verification", identity, network_context):
            raise HTTPException(status_code=429, detail="Invalid or expired recovery credential")
        RecoveryService(db).recover_account(data.recovery_credential, data.new_password)
        throttle.clear("recovery_verification", identity, network_context)
    except RecoveryRejected:
        db.rollback()
        try:
            throttle.record_failure("recovery_verification", identity, network_context)
        except ThrottleConfigurationError:
            db.rollback()
        raise HTTPException(status_code=400, detail="Invalid or expired recovery credential")
    except (OSError, ThrottleConfigurationError):
        db.rollback()
        raise HTTPException(status_code=503, detail="Recovery unavailable")
    return {"outcome": "success"}


@router.post("/recovery/mfa/complete", response_model=ClosedOutcome)
def complete_mfa_recovery(data: MfaRecoveryCompleteRequest, request: Request, db: Session = Depends(get_db)):
    network_context = request.client.host if request.client else "unknown"
    throttle = AuthThrottleService(db)
    identity = data.recovery_credential.partition(".")[0]
    try:
        if throttle.is_blocked("recovery_verification", identity, network_context):
            raise HTTPException(status_code=429, detail="Invalid or expired recovery credential")
        RecoveryService(db).recover_mfa(data.recovery_credential)
        throttle.clear("recovery_verification", identity, network_context)
    except RecoveryRejected:
        db.rollback()
        try:
            throttle.record_failure("recovery_verification", identity, network_context)
        except ThrottleConfigurationError:
            db.rollback()
        raise HTTPException(status_code=400, detail="Invalid or expired recovery credential")
    except (OSError, ThrottleConfigurationError):
        db.rollback()
        raise HTTPException(status_code=503, detail="Recovery unavailable")
    return {"outcome": "success"}
