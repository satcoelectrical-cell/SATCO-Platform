from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy import DateTime

from app.core.database import Base


class User(Base):

    __tablename__ = "users"


    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )


    email = Column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )


    username = Column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )


    hashed_password = Column(
        String,
        nullable=False,
    )


    full_name = Column(
        String,
        nullable=True,
    )


    role = Column(
        String,
        default="engineer",
        nullable=False,
    )


    is_active = Column(
        Boolean,
        default=True,
    )

    activation_pending = Column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )

    auth_version = Column(
        Integer,
        default=1,
        server_default="1",
        nullable=False,
    )

    version = Column(
        Integer,
        default=1,
        server_default="1",
        nullable=False,
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )
