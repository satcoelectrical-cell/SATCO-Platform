from sqlalchemy.orm import Session

from app.core.security import (
    hash_password,
    verify_password,
)

from app.permissions.roles import Role
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserRegistration


# Unknown identities must perform the same password-hash work as known users.
# This value is process-local, never persisted, and is not an authentication
# credential for any account.
_UNKNOWN_USER_PASSWORD_HASH = hash_password("satco-unknown-user-dummy-password")


class UserService:

    def __init__(self):
        self.repository = UserRepository()


    def register(
        self,
        db: Session,
        user: UserRegistration,
    ):

        if self.repository.get_by_email(
            db,
            user.email,
        ):
            raise ValueError(
                "Email already exists"
            )


        if self.repository.get_by_username(
            db,
            user.username,
        ):
            raise ValueError(
                "Username already exists"
            )


        hashed = hash_password(
            user.password
        )


        return self.repository.create(
            db,
            user,
            hashed,
            Role.ENGINEER,
        )


    def authenticate(
        self,
        db: Session,
        username: str,
        password: str,
    ):

        user = self.repository.get_by_username(
            db,
            username,
        )


        if not user:
            verify_password(
                password,
                _UNKNOWN_USER_PASSWORD_HASH,
            )
            return None


        if not verify_password(
            password,
            user.hashed_password,
        ):
            return None


        if not user.is_active:
            return None


        return user
