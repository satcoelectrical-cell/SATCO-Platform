from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token

from app.schemas.token import RefreshRequest, TokenResponse
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
