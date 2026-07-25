from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class UserService:

    def __init__(self):

        self.repository = UserRepository()


    def register(
        self,
        db: Session,
        user: UserCreate,
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
        )
