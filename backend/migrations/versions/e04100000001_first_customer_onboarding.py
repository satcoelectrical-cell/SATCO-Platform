"""PATCH-041 first-customer onboarding foundation.

Revision ID: e04100000001
Revises: e03800000001
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e04100000001"
down_revision: str | None = "e03800000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LEGACY_ORGANIZATION_ID = "7e7c9d7a-7693-4f75-9bc5-3ef7bf528281"


def upgrade() -> None:
    op.add_column("organizations", sa.Column("name", sa.String(200), nullable=True))
    op.add_column("organizations", sa.Column("slug", sa.String(80), nullable=True))
    op.execute(
        f"UPDATE organizations SET name='SATCO Engineering', slug='satco-engineering' "
        f"WHERE id='{LEGACY_ORGANIZATION_ID}'::uuid"
    )
    op.execute(
        "UPDATE organizations SET name='Legacy Organization ' || left(id::text,8), "
        "slug='legacy-' || replace(id::text,'-','') WHERE name IS NULL OR slug IS NULL"
    )
    op.create_index("uq_organizations_name_ci", "organizations", [sa.text("lower(name)")], unique=True, postgresql_where=sa.text("name IS NOT NULL"))
    op.create_index("uq_organizations_slug_ci", "organizations", [sa.text("lower(slug)")], unique=True, postgresql_where=sa.text("slug IS NOT NULL"))
    op.create_check_constraint("ck_organizations_profile_pair", "organizations", "(name IS NULL) = (slug IS NULL)")
    op.add_column("users", sa.Column("activation_pending", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("auth_version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("users", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("user_organization_memberships", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.create_check_constraint("ck_users_auth_version_positive", "users", "auth_version > 0")
    op.create_check_constraint("ck_users_version_positive", "users", "version > 0")
    op.create_check_constraint("ck_user_org_memberships_version_positive", "user_organization_memberships", "version > 0")
    op.create_table(
        "account_action_credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purpose", sa.String(16), nullable=False),
        sa.Column("token_digest", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("issued_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("purpose IN ('activation','reset')", name="ck_account_action_credentials_purpose"),
        sa.CheckConstraint("char_length(token_digest)=64", name="ck_account_action_credentials_digest"),
        sa.CheckConstraint("expires_at > created_at", name="ck_account_action_credentials_expiry"),
        sa.CheckConstraint("NOT (used_at IS NOT NULL AND revoked_at IS NOT NULL)", name="ck_account_action_credentials_terminal"),
    )
    op.create_index("uq_account_action_credentials_digest", "account_action_credentials", ["token_digest"], unique=True)
    op.create_index("ix_account_action_credentials_user_purpose", "account_action_credentials", ["user_id", "purpose"])
    op.create_index("uq_account_action_credentials_live_user_purpose", "account_action_credentials", ["user_id", "purpose"], unique=True, postgresql_where=sa.text("used_at IS NULL AND revoked_at IS NULL"))
    op.create_table(
        "onboarding_idempotency",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scope", sa.String(80), nullable=False),
        sa.Column("operation", sa.String(32), nullable=False),
        sa.Column("idempotency_key", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("safe_result", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("scope", "operation", "idempotency_key", name="uq_onboarding_idempotency_scope_operation_key"),
        sa.CheckConstraint("char_length(request_fingerprint)=64", name="ck_onboarding_idempotency_fingerprint"),
    )
    op.execute("REVOKE ALL ON account_action_credentials FROM PUBLIC")
    op.execute("REVOKE ALL ON onboarding_idempotency FROM PUBLIC")
    op.execute("DO $$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='satco_runtime') THEN GRANT SELECT,INSERT,UPDATE,DELETE ON account_action_credentials,onboarding_idempotency TO satco_runtime; GRANT SELECT,INSERT,UPDATE ON organizations,users,user_organization_memberships TO satco_runtime; REVOKE UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER ON audit_logs FROM satco_runtime; GRANT SELECT,INSERT ON audit_logs TO satco_runtime; END IF; END $$")


def downgrade() -> None:
    op.drop_table("onboarding_idempotency")
    op.drop_table("account_action_credentials")
    op.drop_constraint("ck_user_org_memberships_version_positive", "user_organization_memberships", type_="check")
    op.drop_constraint("ck_users_version_positive", "users", type_="check")
    op.drop_constraint("ck_users_auth_version_positive", "users", type_="check")
    op.drop_column("user_organization_memberships", "version")
    op.drop_column("users", "version")
    op.drop_column("users", "auth_version")
    op.drop_column("users", "activation_pending")
    op.drop_constraint("ck_organizations_profile_pair", "organizations", type_="check")
    op.drop_index("uq_organizations_slug_ci", table_name="organizations")
    op.drop_index("uq_organizations_name_ci", table_name="organizations")
    op.drop_column("organizations", "slug")
    op.drop_column("organizations", "name")
