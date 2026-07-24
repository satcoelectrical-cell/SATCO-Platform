from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.core.database import Base

from sqlalchemy.orm import relationship

class Customer(Base):
    __tablename__ = "customers"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String,
        nullable=False
    )

    company = Column(
        String,
        nullable=True
    )

    phone = Column(
        String,
        nullable=True
    )

    email = Column(
        String,
        nullable=True
    )

    contacts = relationship(
    "Contact",
    back_populates="customer",
    cascade="all, delete-orphan",
)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )