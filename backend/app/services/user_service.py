from sqlalchemy.orm import Session

from app.core.security import (
    hash_password,
    verify_password,
)

from app.permissions.roles import Role
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserRegistration


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
            return None


        if not verify_password(
            password,
            user.hashed_password,
        ):
            return None


        if not user.is_active:
            return None


        return user
