"""PATCH-041 account-action credential persistence."""

from uuid import uuid4

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, JSON, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.sql import func

from app.core.database import Base


class AccountActionCredential(Base):
    __tablename__ = "account_action_credentials"
    __table_args__ = (
        CheckConstraint("purpose IN ('activation','reset')", name="ck_account_action_credentials_purpose"),
        CheckConstraint("char_length(token_digest) = 64", name="ck_account_action_credentials_digest"),
        CheckConstraint("expires_at > created_at", name="ck_account_action_credentials_expiry"),
        CheckConstraint("NOT (used_at IS NOT NULL AND revoked_at IS NOT NULL)", name="ck_account_action_credentials_terminal"),
        Index("uq_account_action_credentials_digest", "token_digest", unique=True),
        Index("ix_account_action_credentials_user_purpose", "user_id", "purpose"),
        Index("uq_account_action_credentials_live_user_purpose", "user_id", "purpose", unique=True, postgresql_where=text("used_at IS NULL AND revoked_at IS NULL")),
    )

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    purpose = Column(String(16), nullable=False)
    token_digest = Column(String(64), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    issued_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class OnboardingIdempotency(Base):
    __tablename__ = "onboarding_idempotency"
    __table_args__ = (
        UniqueConstraint("scope", "operation", "idempotency_key", name="uq_onboarding_idempotency_scope_operation_key"),
        CheckConstraint("char_length(request_fingerprint)=64", name="ck_onboarding_idempotency_fingerprint"),
    )

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    scope = Column(String(80), nullable=False)
    operation = Column(String(32), nullable=False)
    idempotency_key = Column(PostgreSQLUUID(as_uuid=True), nullable=False)
    request_fingerprint = Column(String(64), nullable=False)
    safe_result = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
