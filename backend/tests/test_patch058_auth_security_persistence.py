from pathlib import Path

from app.models.auth_security import (
    AuthRecoveryCredential,
    AuthRefreshFamily,
    AuthRefreshSession,
    AuthSecurityEvent,
    AuthThrottleState,
    MfaRecoveryCode,
    OrganizationMfaPolicy,
    UserTotpAuthenticator,
)


MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "e05800000001_patch_058_auth_security_persistence.py"
)


def test_patch058_security_tables_are_registered():
    models = (
        AuthRefreshFamily,
        AuthRefreshSession,
        UserTotpAuthenticator,
        MfaRecoveryCode,
        AuthRecoveryCredential,
        OrganizationMfaPolicy,
        AuthSecurityEvent,
        AuthThrottleState,
    )

    assert {model.__tablename__ for model in models} == {
        "auth_refresh_families",
        "auth_refresh_sessions",
        "user_totp_authenticators",
        "mfa_recovery_codes",
        "auth_recovery_credentials",
        "organization_mfa_policies",
        "auth_security_events",
        "auth_throttle_states",
    }


def test_refresh_persistence_never_contains_raw_refresh_secret():
    columns = set(AuthRefreshSession.__table__.columns.keys())

    assert "secret_verifier" in columns
    assert "selector" in columns
    assert "secret" not in columns
    assert "refresh_token" not in columns
    assert "token" not in columns


def test_totp_persistence_never_contains_plaintext_secret():
    columns = set(UserTotpAuthenticator.__table__.columns.keys())

    assert "encrypted_secret" in columns
    assert "encryption_nonce" in columns
    assert "key_id" in columns
    assert "key_version" in columns
    assert "secret" not in columns


def test_recovery_code_persistence_uses_verifier_only():
    columns = set(MfaRecoveryCode.__table__.columns.keys())

    assert "code_verifier" in columns
    assert "code" not in columns
    assert "raw_code" not in columns


def test_recovery_credential_persistence_uses_selector_and_verifier():
    columns = set(AuthRecoveryCredential.__table__.columns.keys())

    assert "selector" in columns
    assert "secret_verifier" in columns
    assert "secret" not in columns
    assert "token" not in columns


def test_member_mfa_policy_is_organization_owned():
    table = OrganizationMfaPolicy.__table__

    assert list(table.primary_key.columns.keys()) == ["organization_id"]
    assert "member_policy" in table.columns
    assert "version" in table.columns


def test_security_events_are_separate_from_generic_audit():
    assert AuthSecurityEvent.__tablename__ == "auth_security_events"
    assert "event_type" in AuthSecurityEvent.__table__.columns
    assert "outcome" in AuthSecurityEvent.__table__.columns
    assert "safe_context" in AuthSecurityEvent.__table__.columns


def test_throttle_scope_does_not_store_raw_credential_identity():
    columns = set(AuthThrottleState.__table__.columns.keys())

    assert "credential_key" in columns
    assert "network_key" in columns
    assert "username" not in columns
    assert "email" not in columns
    assert "credential" not in columns


def test_patch058_migration_has_exact_parent_and_runtime_grants():
    source = MIGRATION.read_text(encoding="utf-8")

    assert 'revision = "e05800000001"' in source
    assert 'down_revision = "e05600000008"' in source

    for table in (
        "auth_refresh_sessions",
        "user_totp_authenticators",
        "mfa_recovery_codes",
        "auth_recovery_credentials",
        "organization_mfa_policies",
        "auth_security_events",
        "auth_throttle_states",
    ):
        assert f'"{table}"' in source

    assert "GRANT SELECT, INSERT, UPDATE ON auth_refresh_sessions TO satco_runtime" in source
    assert "GRANT SELECT, INSERT ON auth_security_events TO satco_runtime" in source
    assert "GRANT SELECT, INSERT, UPDATE, DELETE ON auth_throttle_states TO satco_runtime" in source


def test_refresh_lineage_has_single_successor_constraint():
    names = {
        item.name
        for item in AuthRefreshSession.__table__.indexes
        if item.name is not None
    }

    assert "uq_auth_refresh_sessions_successor" in names
    assert "uq_auth_refresh_sessions_selector" in names



def test_refresh_family_is_authoritative_persistence_boundary():
    family = AuthRefreshFamily.__table__
    session = AuthRefreshSession.__table__

    assert "user_id" in family.columns
    assert "revoked_at" in family.columns
    assert "reuse_detected_at" in family.columns
    assert "revocation_reason" in family.columns

    foreign_keys = {
        fk.target_fullname
        for fk in session.c.family_id.foreign_keys
    }
    assert "auth_refresh_families.id" in foreign_keys


def test_refresh_session_network_context_is_non_raw_key():
    columns = set(AuthRefreshSession.__table__.columns.keys())

    assert "network_context_key" in columns
    assert "network_context" not in columns


def test_member_mfa_policy_version_is_constrained():
    names = {
        constraint.name
        for constraint in OrganizationMfaPolicy.__table__.constraints
        if constraint.name is not None
    }

    assert "ck_organization_mfa_policies_version" in names


def test_recovery_selector_has_minimum_length_constraint():
    names = {
        constraint.name
        for constraint in AuthRecoveryCredential.__table__.constraints
        if constraint.name is not None
    }

    assert "ck_auth_recovery_credentials_selector" in names


def test_migration_has_security_state_downgrade_guard():
    source = MIGRATION.read_text(encoding="utf-8")

    assert "Cannot discard PATCH-058 security state" in source
    assert '"auth_refresh_families"' in source

def test_refresh_cleanup_paths_are_indexed():
    names = {
        item.name
        for item in AuthRefreshSession.__table__.indexes
        if item.name is not None
    }

    assert "ix_auth_refresh_sessions_expiry" in names
    assert "ix_auth_refresh_sessions_revoked" in names


def test_recovery_code_verifier_is_unique_within_generation():
    names = {
        constraint.name
        for constraint in MfaRecoveryCode.__table__.constraints
        if constraint.name is not None
    }

    assert "uq_mfa_recovery_codes_generation_verifier" in names


def test_security_event_actor_time_is_indexed():
    names = {
        item.name
        for item in AuthSecurityEvent.__table__.indexes
        if item.name is not None
    }

    assert "ix_auth_security_events_actor_time" in names


def test_throttle_blocked_until_is_indexed():
    names = {
        item.name
        for item in AuthThrottleState.__table__.indexes
        if item.name is not None
    }

    assert "ix_auth_throttle_states_blocked_until" in names



def test_refresh_session_family_user_identity_is_database_bound():
    family = AuthRefreshFamily.__table__
    session = AuthRefreshSession.__table__

    family_constraints = {c.name for c in family.constraints if c.name}
    session_constraints = {c.name for c in session.constraints if c.name}

    assert "uq_auth_refresh_families_id_user" in family_constraints
    assert "uq_auth_refresh_sessions_id_family_user" in session_constraints
    assert "fk_auth_refresh_sessions_family_user" in session_constraints


def test_refresh_predecessor_lineage_is_database_bound_to_same_family_and_user():
    session = AuthRefreshSession.__table__
    constraints = {c.name: c for c in session.constraints if c.name}

    constraint = constraints["fk_auth_refresh_sessions_predecessor_lineage"]

    local_columns = tuple(element.parent.name for element in constraint.elements)
    remote_columns = tuple(
        f"{element.column.table.name}.{element.column.name}"
        for element in constraint.elements
    )

    assert local_columns == ("predecessor_id", "family_id", "user_id")
    assert remote_columns == (
        "auth_refresh_sessions.id",
        "auth_refresh_sessions.family_id",
        "auth_refresh_sessions.user_id",
    )
