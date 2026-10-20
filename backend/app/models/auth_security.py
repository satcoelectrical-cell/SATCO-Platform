"""PATCH-058 authentication and application-security persistence."""

from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.sql import func

from app.core.database import Base


class AuthRefreshFamily(Base):
    __tablename__ = "auth_refresh_families"
    __table_args__ = (
        UniqueConstraint(
            "id",
            "user_id",
            name="uq_auth_refresh_families_id_user",
        ),
        Index(
            "ix_auth_refresh_families_user",
            "user_id",
            "created_at",
        ),
    )

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    reuse_detected_at = Column(DateTime(timezone=True), nullable=True)
    revocation_reason = Column(String(80), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class AuthRefreshSession(Base):
    __tablename__ = "auth_refresh_sessions"
    __table_args__ = (
        UniqueConstraint(
            "id",
            "family_id",
            "user_id",
            name="uq_auth_refresh_sessions_id_family_user",
        ),
        ForeignKeyConstraint(
            ["family_id", "user_id"],
            ["auth_refresh_families.id", "auth_refresh_families.user_id"],
            name="fk_auth_refresh_sessions_family_user",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["predecessor_id", "family_id", "user_id"],
            [
                "auth_refresh_sessions.id",
                "auth_refresh_sessions.family_id",
                "auth_refresh_sessions.user_id",
            ],
            name="fk_auth_refresh_sessions_predecessor_lineage",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "char_length(selector) >= 22",
            name="ck_auth_refresh_sessions_selector",
        ),
        CheckConstraint(
            "char_length(secret_verifier) = 64",
            name="ck_auth_refresh_sessions_verifier",
        ),
        CheckConstraint(
            "expires_at > created_at",
            name="ck_auth_refresh_sessions_expiry",
        ),
        CheckConstraint(
            "auth_version >= 1",
            name="ck_auth_refresh_sessions_auth_version",
        ),
        Index(
            "uq_auth_refresh_sessions_selector",
            "selector",
            unique=True,
        ),
        Index(
            "ix_auth_refresh_sessions_user",
            "user_id",
            "created_at",
        ),
        Index(
            "ix_auth_refresh_sessions_family",
            "family_id",
            "created_at",
        ),
        Index(
            "ix_auth_refresh_sessions_expiry",
            "expires_at",
        ),
        Index(
            "ix_auth_refresh_sessions_revoked",
            "revoked_at",
        ),
        Index(
            "uq_auth_refresh_sessions_successor",
            "predecessor_id",
            unique=True,
            postgresql_where=text("predecessor_id IS NOT NULL"),
        ),
    )

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    family_id = Column(
        PostgreSQLUUID(as_uuid=True),
        nullable=False,
    )
    predecessor_id = Column(
        PostgreSQLUUID(as_uuid=True),
        nullable=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    selector = Column(String(128), nullable=False)
    secret_verifier = Column(String(64), nullable=False)
    auth_version = Column(Integer, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    consumed_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    reuse_detected_at = Column(DateTime(timezone=True), nullable=True)
    revocation_reason = Column(String(80), nullable=True)
    device_label = Column(String(200), nullable=True)
    network_context_key = Column(String(64), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class UserTotpAuthenticator(Base):
    __tablename__ = "user_totp_authenticators"
    __table_args__ = (
        CheckConstraint(
            "key_version >= 1",
            name="ck_user_totp_authenticators_key_version",
        ),
        CheckConstraint(
            "last_accepted_counter IS NULL OR last_accepted_counter >= 0",
            name="ck_user_totp_authenticators_counter",
        ),
        Index(
            "uq_user_totp_authenticators_user",
            "user_id",
            unique=True,
        ),
    )

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    encrypted_secret = Column(String, nullable=False)
    encryption_nonce = Column(String, nullable=False)
    key_id = Column(String(120), nullable=False)
    key_version = Column(Integer, nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    disabled_at = Column(DateTime(timezone=True), nullable=True)
    last_accepted_counter = Column(Integer, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class MfaRecoveryCode(Base):
    __tablename__ = "mfa_recovery_codes"
    __table_args__ = (
        CheckConstraint(
            "char_length(code_verifier) = 64",
            name="ck_mfa_recovery_codes_verifier",
        ),
        UniqueConstraint(
            "user_id",
            "generation",
            "ordinal",
            name="uq_mfa_recovery_codes_generation_ordinal",
        ),
        UniqueConstraint(
            "user_id",
            "generation",
            "code_verifier",
            name="uq_mfa_recovery_codes_generation_verifier",
        ),
        CheckConstraint(
            "generation >= 1",
            name="ck_mfa_recovery_codes_generation",
        ),
        CheckConstraint(
            "ordinal >= 1",
            name="ck_mfa_recovery_codes_ordinal",
        ),
        Index(
            "ix_mfa_recovery_codes_user_generation",
            "user_id",
            "generation",
        ),
    )

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    generation = Column(Integer, nullable=False)
    ordinal = Column(Integer, nullable=False)
    code_verifier = Column(String(64), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class AuthRecoveryCredential(Base):
    __tablename__ = "auth_recovery_credentials"
    __table_args__ = (
        CheckConstraint(
            "purpose IN ('account_recovery','mfa_recovery')",
            name="ck_auth_recovery_credentials_purpose",
        ),
        CheckConstraint(
            "char_length(selector) >= 22",
            name="ck_auth_recovery_credentials_selector",
        ),
        CheckConstraint(
            "char_length(secret_verifier) = 64",
            name="ck_auth_recovery_credentials_verifier",
        ),
        CheckConstraint(
            "expires_at > created_at",
            name="ck_auth_recovery_credentials_expiry",
        ),
        Index(
            "uq_auth_recovery_credentials_selector",
            "selector",
            unique=True,
        ),
        Index(
            "ix_auth_recovery_credentials_user",
            "user_id",
            "purpose",
        ),
    )

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=True,
    )
    purpose = Column(String(32), nullable=False)
    selector = Column(String(128), nullable=False)
    secret_verifier = Column(String(64), nullable=False)
    issued_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class OrganizationMfaPolicy(Base):
    __tablename__ = "organization_mfa_policies"
    __table_args__ = (
        CheckConstraint(
            "member_policy IN ('optional','required')",
            name="ck_organization_mfa_policies_member_policy",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_organization_mfa_policies_version",
        ),
    )

    organization_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    member_policy = Column(
        String(16),
        nullable=False,
        default="optional",
        server_default="optional",
    )
    version = Column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    updated_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class AuthSecurityEvent(Base):
    __tablename__ = "auth_security_events"
    __table_args__ = (
        Index(
            "ix_auth_security_events_user_time",
            "user_id",
            "occurred_at",
        ),
        Index(
            "ix_auth_security_events_org_time",
            "organization_id",
            "occurred_at",
        ),
        Index(
            "ix_auth_security_events_type_time",
            "event_type",
            "occurred_at",
        ),
        Index(
            "ix_auth_security_events_actor_time",
            "actor_user_id",
            "occurred_at",
        ),
    )

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type = Column(String(80), nullable=False)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    organization_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    session_id = Column(
        PostgreSQLUUID(as_uuid=True),
        nullable=True,
    )
    outcome = Column(String(32), nullable=False)
    reason_code = Column(String(80), nullable=True)
    safe_context = Column(String(500), nullable=True)
    occurred_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class AuthThrottleState(Base):
    __tablename__ = "auth_throttle_states"
    __table_args__ = (
        CheckConstraint(
            "failure_count >= 0",
            name="ck_auth_throttle_states_failure_count",
        ),
        UniqueConstraint(
            "credential_key",
            "network_key",
            name="uq_auth_throttle_states_scope",
        ),
        Index(
            "ix_auth_throttle_states_updated",
            "updated_at",
        ),
        Index(
            "ix_auth_throttle_states_blocked_until",
            "blocked_until",
        ),
    )

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    credential_key = Column(String(64), nullable=False)
    network_key = Column(String(64), nullable=False)
    failure_count = Column(Integer, nullable=False, default=0, server_default="0")
    window_started_at = Column(DateTime(timezone=True), nullable=False)
    blocked_until = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
