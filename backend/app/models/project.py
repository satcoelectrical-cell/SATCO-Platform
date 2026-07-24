from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String

from sqlalchemy.orm import relationship

from app.core.database import Base
from app.enums import ProjectStatus


class Project(Base):
    __tablename__ = "projects"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String,
        nullable=False,
    )

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False,
    )

    status = Column(
        String,
        default=ProjectStatus.NEW.value,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    customer = relationship(
        "Customer",
        back_populates="projects",
    )
