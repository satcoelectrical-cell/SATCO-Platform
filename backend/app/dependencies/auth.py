from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.models.organization import Organization
from app.models.organization import UserOrganizationMembership
from app.exceptions.organization_context import ActiveOrganizationContextRequired
from app.permissions.roles import Role


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


@dataclass(frozen=True, slots=True)
class AuthenticatedOrganizationContext:
    """Trusted current User and server-derived Organization scope."""

    user: User
    organization_id: UUID


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:

    try:
        payload = decode_token(token)

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user = (
            db.query(User)
            .filter(User.id == int(user_id))
            .first()
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user",
            )

        if payload.get("av", 1) != user.auth_version:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

        return user

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


def get_current_user_id(
    current_user: User = Depends(get_current_user),
) -> str:
    return str(current_user.id)


def get_current_user_organization_context(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AuthenticatedOrganizationContext:
    """Resolve one selected, enabled membership in an active Organization."""

    memberships = (
        db.query(UserOrganizationMembership)
        .join(
            Organization,
            Organization.id
            == UserOrganizationMembership.organization_id,
        )
        .filter(
            UserOrganizationMembership.user_id == current_user.id,
            UserOrganizationMembership.is_selected.is_(True),
            UserOrganizationMembership.is_enabled.is_(True),
            Organization.is_active.is_(True),
        )
        .limit(2)
        .all()
    )
    if len(memberships) != 1:
        raise ActiveOrganizationContextRequired()
    return AuthenticatedOrganizationContext(
        user=current_user,
        organization_id=memberships[0].organization_id,
    )



def require_role(*roles: str | Role):
    validated_roles = {
        Role.from_value(role).value
        for role in roles
    }

    def role_checker(
        current_user: User = Depends(get_current_user),
    ):

        if current_user.role not in validated_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )

        return current_user

    return role_checker
from dataclasses import dataclass
from uuid import UUID
