"""Durable Identifier idempotency and outbox records."""

from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.core.database import Base


class EngineeringIdentifierIdempotency(Base):
    __tablename__ = "engineering_identifier_idempotency"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), primary_key=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), primary_key=True)
    operation = Column(String(64), primary_key=True)
    idempotency_key = Column(UUID(as_uuid=True), primary_key=True)
    request_fingerprint = Column(String(64), nullable=False)
    identifier_id = Column(UUID(as_uuid=True), ForeignKey("engineering_identifiers.identifier_id", ondelete="RESTRICT"))
    result = Column(JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class EngineeringIdentifierOutbox(Base):
    __tablename__ = "engineering_identifier_outbox"
    __table_args__ = (UniqueConstraint("identifier_id", "aggregate_version", name="uq_engineering_identifier_outbox_version"),)

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    identifier_id = Column(UUID(as_uuid=True), ForeignKey("engineering_identifiers.identifier_id", ondelete="RESTRICT"), nullable=False)
    aggregate_version = Column(Integer, nullable=False)
    event_type = Column(String(64), nullable=False)
    payload = Column(JSONB, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    published_at = Column(DateTime(timezone=True))
