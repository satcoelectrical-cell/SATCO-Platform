from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from .database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(
        String,
        nullable=False
    )

    customer = Column(
        String,
        nullable=True
    )

    status = Column(
        String,
        default="new"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )