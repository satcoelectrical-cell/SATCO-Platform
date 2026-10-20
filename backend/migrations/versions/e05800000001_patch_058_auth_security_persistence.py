"""PATCH-058 authentication and application-security persistence foundation.

Revision ID: e05800000001
Revises: e05600000008
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "e05800000001"
down_revision = "e05600000008"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "auth_refresh_families",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("reuse_detected_at", sa.DateTime(timezone=True)),
        sa.Column("revocation_reason", sa.String(80)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "id",
            "user_id",
            name="uq_auth_refresh_families_id_user",
        ),
    )
    op.create_index(
        "ix_auth_refresh_families_user",
        "auth_refresh_families",
        ["user_id", "created_at"],
    )

    op.create_table(
        "auth_refresh_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "family_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "predecessor_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("selector", sa.String(128), nullable=False),
        sa.Column("secret_verifier", sa.String(64), nullable=False),
        sa.Column("auth_version", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("reuse_detected_at", sa.DateTime(timezone=True)),
        sa.Column("revocation_reason", sa.String(80)),
        sa.Column("device_label", sa.String(200)),
        sa.Column("network_context_key", sa.String(64)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "id",
            "family_id",
            "user_id",
            name="uq_auth_refresh_sessions_id_family_user",
        ),
        sa.ForeignKeyConstraint(
            ["family_id", "user_id"],
            ["auth_refresh_families.id", "auth_refresh_families.user_id"],
            name="fk_auth_refresh_sessions_family_user",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["predecessor_id", "family_id", "user_id"],
            [
                "auth_refresh_sessions.id",
                "auth_refresh_sessions.family_id",
                "auth_refresh_sessions.user_id",
            ],
            name="fk_auth_refresh_sessions_predecessor_lineage",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "char_length(selector) >= 22",
            name="ck_auth_refresh_sessions_selector",
        ),
        sa.CheckConstraint(
            "char_length(secret_verifier) = 64",
            name="ck_auth_refresh_sessions_verifier",
        ),
        sa.CheckConstraint(
            "expires_at > created_at",
            name="ck_auth_refresh_sessions_expiry",
        ),
        sa.CheckConstraint(
            "auth_version >= 1",
            name="ck_auth_refresh_sessions_auth_version",
        ),
    )
    op.create_index(
        "uq_auth_refresh_sessions_selector",
        "auth_refresh_sessions",
        ["selector"],
        unique=True,
    )
    op.create_index(
        "ix_auth_refresh_sessions_user",
        "auth_refresh_sessions",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_auth_refresh_sessions_family",
        "auth_refresh_sessions",
        ["family_id", "created_at"],
    )
    op.create_index(
        "ix_auth_refresh_sessions_expiry",
        "auth_refresh_sessions",
        ["expires_at"],
    )
    op.create_index(
        "ix_auth_refresh_sessions_revoked",
        "auth_refresh_sessions",
        ["revoked_at"],
    )
    op.create_index(
        "uq_auth_refresh_sessions_successor",
        "auth_refresh_sessions",
        ["predecessor_id"],
        unique=True,
        postgresql_where=sa.text("predecessor_id IS NOT NULL"),
    )

    op.create_table(
        "user_totp_authenticators",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("encrypted_secret", sa.String(), nullable=False),
        sa.Column("encryption_nonce", sa.String(), nullable=False),
        sa.Column("key_id", sa.String(120), nullable=False),
        sa.Column("key_version", sa.Integer(), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column("disabled_at", sa.DateTime(timezone=True)),
        sa.Column("last_accepted_counter", sa.Integer()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "key_version >= 1",
            name="ck_user_totp_authenticators_key_version",
        ),
        sa.CheckConstraint(
            "last_accepted_counter IS NULL OR last_accepted_counter >= 0",
            name="ck_user_totp_authenticators_counter",
        ),
    )
    op.create_index(
        "uq_user_totp_authenticators_user",
        "user_totp_authenticators",
        ["user_id"],
        unique=True,
    )

    op.create_table(
        "mfa_recovery_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("generation", sa.Integer(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("code_verifier", sa.String(64), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "user_id",
            "generation",
            "ordinal",
            name="uq_mfa_recovery_codes_generation_ordinal",
        ),
        sa.UniqueConstraint(
            "user_id",
            "generation",
            "code_verifier",
            name="uq_mfa_recovery_codes_generation_verifier",
        ),
        sa.CheckConstraint(
            "char_length(code_verifier) = 64",
            name="ck_mfa_recovery_codes_verifier",
        ),
        sa.CheckConstraint(
            "generation >= 1",
            name="ck_mfa_recovery_codes_generation",
        ),
        sa.CheckConstraint(
            "ordinal >= 1",
            name="ck_mfa_recovery_codes_ordinal",
        ),
    )
    op.create_index(
        "ix_mfa_recovery_codes_user_generation",
        "mfa_recovery_codes",
        ["user_id", "generation"],
    )

    op.create_table(
        "auth_recovery_credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
        ),
        sa.Column("purpose", sa.String(32), nullable=False),
        sa.Column("selector", sa.String(128), nullable=False),
        sa.Column("secret_verifier", sa.String(64), nullable=False),
        sa.Column(
            "issued_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "purpose IN ('account_recovery','mfa_recovery')",
            name="ck_auth_recovery_credentials_purpose",
        ),
        sa.CheckConstraint(
            "char_length(selector) >= 22",
            name="ck_auth_recovery_credentials_selector",
        ),
        sa.CheckConstraint(
            "char_length(secret_verifier) = 64",
            name="ck_auth_recovery_credentials_verifier",
        ),
        sa.CheckConstraint(
            "expires_at > created_at",
            name="ck_auth_recovery_credentials_expiry",
        ),
    )
    op.create_index(
        "uq_auth_recovery_credentials_selector",
        "auth_recovery_credentials",
        ["selector"],
        unique=True,
    )
    op.create_index(
        "ix_auth_recovery_credentials_user",
        "auth_recovery_credentials",
        ["user_id", "purpose"],
    )

    op.create_table(
        "organization_mfa_policies",
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "member_policy",
            sa.String(16),
            nullable=False,
            server_default="optional",
        ),
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
        sa.Column(
            "updated_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "member_policy IN ('optional','required')",
            name="ck_organization_mfa_policies_member_policy",
        ),
        sa.CheckConstraint(
            "version >= 1",
            name="ck_organization_mfa_policies_version",
        ),
    )

    op.create_table(
        "auth_security_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "actor_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("session_id", postgresql.UUID(as_uuid=True)),
        sa.Column("outcome", sa.String(32), nullable=False),
        sa.Column("reason_code", sa.String(80)),
        sa.Column("safe_context", sa.String(500)),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_auth_security_events_user_time",
        "auth_security_events",
        ["user_id", "occurred_at"],
    )
    op.create_index(
        "ix_auth_security_events_org_time",
        "auth_security_events",
        ["organization_id", "occurred_at"],
    )
    op.create_index(
        "ix_auth_security_events_type_time",
        "auth_security_events",
        ["event_type", "occurred_at"],
    )
    op.create_index(
        "ix_auth_security_events_actor_time",
        "auth_security_events",
        ["actor_user_id", "occurred_at"],
    )

    op.create_table(
        "auth_throttle_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("credential_key", sa.String(64), nullable=False),
        sa.Column("network_key", sa.String(64), nullable=False),
        sa.Column(
            "failure_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("blocked_until", sa.DateTime(timezone=True)),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "failure_count >= 0",
            name="ck_auth_throttle_states_failure_count",
        ),
        sa.UniqueConstraint(
            "credential_key",
            "network_key",
            name="uq_auth_throttle_states_scope",
        ),
    )
    op.create_index(
        "ix_auth_throttle_states_updated",
        "auth_throttle_states",
        ["updated_at"],
    )
    op.create_index(
        "ix_auth_throttle_states_blocked_until",
        "auth_throttle_states",
        ["blocked_until"],
    )

    op.execute("""
    GRANT SELECT, INSERT, UPDATE ON auth_refresh_families TO satco_runtime;
    GRANT SELECT, INSERT, UPDATE ON auth_refresh_sessions TO satco_runtime;
    GRANT SELECT, INSERT, UPDATE ON user_totp_authenticators TO satco_runtime;
    GRANT SELECT, INSERT, UPDATE ON mfa_recovery_codes TO satco_runtime;
    GRANT SELECT, INSERT, UPDATE ON auth_recovery_credentials TO satco_runtime;
    GRANT SELECT, INSERT, UPDATE ON organization_mfa_policies TO satco_runtime;
    GRANT SELECT, INSERT ON auth_security_events TO satco_runtime;
    GRANT SELECT, INSERT, UPDATE, DELETE ON auth_throttle_states TO satco_runtime;
    """)


def downgrade():
    protected_tables = (
        "auth_refresh_families",
        "auth_refresh_sessions",
        "user_totp_authenticators",
        "mfa_recovery_codes",
        "auth_recovery_credentials",
        "organization_mfa_policies",
        "auth_security_events",
        "auth_throttle_states",
    )
    bind = op.get_bind()
    for table_name in protected_tables:
        has_rows = bind.execute(
            sa.text(f"SELECT EXISTS (SELECT 1 FROM {table_name})")
        ).scalar_one()
        if has_rows:
            raise RuntimeError(
                f"Cannot discard PATCH-058 security state from {table_name}"
            )

    op.execute("""
    REVOKE ALL ON auth_throttle_states FROM satco_runtime;
    REVOKE ALL ON auth_security_events FROM satco_runtime;
    REVOKE ALL ON organization_mfa_policies FROM satco_runtime;
    REVOKE ALL ON auth_recovery_credentials FROM satco_runtime;
    REVOKE ALL ON mfa_recovery_codes FROM satco_runtime;
    REVOKE ALL ON user_totp_authenticators FROM satco_runtime;
    REVOKE ALL ON auth_refresh_sessions FROM satco_runtime;
    REVOKE ALL ON auth_refresh_families FROM satco_runtime;
    """)

    op.drop_index(
        "ix_auth_throttle_states_blocked_until",
        table_name="auth_throttle_states",
    )
    op.drop_index(
        "ix_auth_throttle_states_updated",
        table_name="auth_throttle_states",
    )
    op.drop_table("auth_throttle_states")

    op.drop_index(
        "ix_auth_security_events_actor_time",
        table_name="auth_security_events",
    )
    op.drop_index(
        "ix_auth_security_events_type_time",
        table_name="auth_security_events",
    )
    op.drop_index(
        "ix_auth_security_events_org_time",
        table_name="auth_security_events",
    )
    op.drop_index(
        "ix_auth_security_events_user_time",
        table_name="auth_security_events",
    )
    op.drop_table("auth_security_events")

    op.drop_table("organization_mfa_policies")

    op.drop_index(
        "ix_auth_recovery_credentials_user",
        table_name="auth_recovery_credentials",
    )
    op.drop_index(
        "uq_auth_recovery_credentials_selector",
        table_name="auth_recovery_credentials",
    )
    op.drop_table("auth_recovery_credentials")

    op.drop_index(
        "ix_mfa_recovery_codes_user_generation",
        table_name="mfa_recovery_codes",
    )
    op.drop_table("mfa_recovery_codes")

    op.drop_index(
        "uq_user_totp_authenticators_user",
        table_name="user_totp_authenticators",
    )
    op.drop_table("user_totp_authenticators")

    op.drop_index(
        "uq_auth_refresh_sessions_successor",
        table_name="auth_refresh_sessions",
    )
    op.drop_index(
        "ix_auth_refresh_sessions_revoked",
        table_name="auth_refresh_sessions",
    )
    op.drop_index(
        "ix_auth_refresh_sessions_expiry",
        table_name="auth_refresh_sessions",
    )
    op.drop_index(
        "ix_auth_refresh_sessions_family",
        table_name="auth_refresh_sessions",
    )
    op.drop_index(
        "ix_auth_refresh_sessions_user",
        table_name="auth_refresh_sessions",
    )
    op.drop_index(
        "uq_auth_refresh_sessions_selector",
        table_name="auth_refresh_sessions",
    )
    op.drop_table("auth_refresh_sessions")

    op.drop_index(
        "ix_auth_refresh_families_user",
        table_name="auth_refresh_families",
    )
    op.drop_table("auth_refresh_families")
