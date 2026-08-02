"""Minimal Organization identity and authenticated membership scope."""

from uuid import uuid4

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey
from sqlalchemy import Index, Integer, text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    is_active = Column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now(),
    )


class UserOrganizationMembership(Base):
    __tablename__ = "user_organization_memberships"
    __table_args__ = (
        CheckConstraint(
            "NOT is_selected OR is_enabled",
            name="ck_user_org_memberships_selected_enabled",
        ),
        Index(
            "uq_user_org_memberships_selected_user",
            "user_id",
            unique=True,
            postgresql_where=text("is_selected"),
        ),
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    organization_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    is_enabled = Column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    is_selected = Column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now(),
    )

    user = relationship("User")
    organization = relationship("Organization")
