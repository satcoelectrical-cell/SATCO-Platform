from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
)

from app.schemas.token import TokenResponse
from app.schemas.onboarding import ClosedOutcome, PasswordChangeRequest
from app.models.organization import Organization

from app.services.user_service import UserService
from app.dependencies.auth import (
    AuthenticatedOrganizationContext,
    get_current_user,
    get_current_user_organization_context,
)
from app.services.onboarding_service import OnboardingService, ProtectedOnboarding


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


    access_token = create_access_token(
        user.id, user.auth_version
    )


    refresh_token = create_refresh_token(
        user.id, user.auth_version
    )


    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
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
