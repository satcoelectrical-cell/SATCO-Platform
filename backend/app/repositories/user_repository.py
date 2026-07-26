from sqlalchemy.orm import Session

from app.models.user import User
from app.permissions.roles import Role
from app.schemas.user import UserRegistration


class UserRepository:


    def get_by_email(
        self,
        db: Session,
        email: str,
    ):
        return (
            db.query(User)
            .filter(User.email == email)
            .first()
        )


    def get_by_username(
        self,
        db: Session,
        username: str,
    ):
        return (
            db.query(User)
            .filter(User.username == username)
            .first()
        )


    def create(
        self,
        db: Session,
        user: UserRegistration,
        hashed_password: str,
        role: Role,
    ):
        validated_role = Role.from_value(role)

        db_user = User(
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=validated_role.value,
            hashed_password=hashed_password,
        )


        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return db_user
