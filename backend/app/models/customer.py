from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    organization_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "organizations.id",
            name="fk_customers_organization_id_organizations",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    name = Column(
        String(200),
        nullable=False
    )

    company = Column(
        String(200),
        nullable=True
    )

    phone = Column(
        String(64),
        nullable=True
    )

    email = Column(
        String(320),
        nullable=True
    )

    contacts = relationship(
        "Contact",
        back_populates="customer",
    )
    
    projects = relationship(
        "Project",
        back_populates="customer",
    )

    organization = relationship("Organization")

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
