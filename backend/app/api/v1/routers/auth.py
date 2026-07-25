from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
)

from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import TokenResponse

from app.services.user_service import UserService
from app.dependencies.auth import get_current_user_id


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


service = UserService()


@router.post(
    "/register",
    response_model=UserResponse,
)
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    try:
        return service.register(
            db,
            user,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    username: str,
    password: str,
    db: Session = Depends(get_db),
):

    user = service.authenticate(
        db,
        username,
        password,
    )


    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )


    access_token = create_access_token(
        user.id
    )


    refresh_token = create_refresh_token(
        user.id
    )


    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )



@router.get("/me")
def get_me(
    user_id: str = Depends(get_current_user_id),
):
    return {
        "user_id": user_id,
        "message": "Authenticated successfully",
    }
