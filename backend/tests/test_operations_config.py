import json

import pytest

from app.core.config import Settings
from app.core.operations import ProductionConfigurationError, validate_production_settings


def production_settings(manifest_path: str, **overrides) -> Settings:
    parent = __import__("pathlib").Path(manifest_path).parent
    scanner_token = str(parent / "scanner-token")
    object_access = str(parent / "object-access")
    object_secret = str(parent / "object-secret")
    parent.joinpath("scanner-token").write_text("s" * 40, encoding="utf-8")
    parent.joinpath("object-access").write_text("access-key", encoding="utf-8")
    parent.joinpath("object-secret").write_text("o" * 40, encoding="utf-8")
    values = {
        "SATCO_ENVIRONMENT": "production",
        "SECRET_KEY": "a" * 40,
        "SATCO_RELEASE_MANIFEST_PATH": manifest_path,
        "SATCO_PUBLIC_URL": "https://satco.example",
        "SATCO_TRUSTED_HOSTS": "satco.example",
        "SATCO_ALLOWED_ORIGINS": "https://satco.example",
        "SATCO_EXPECTED_ALEMBIC_HEAD": "e04500000001",
        "SATCO_PERSISTENCE_GUARD_VERSION": "v1",
        "SATCO_OBJECT_HEALTH_URL": "https://ops.internal/object-health",
        "SATCO_OBJECT_HEALTH_CA_FILE": "/private/test/monitor-ca.pem",
        "SUPPORTING_FILE_SCANNER_ENDPOINT": "https://scanner.internal/scan",
        "SUPPORTING_FILE_SCANNER_TOKEN_FILE": scanner_token,
        "SUPPORTING_FILE_OBJECT_ENDPOINT": "https://objects.internal",
        "SUPPORTING_FILE_OBJECT_BUCKET": "satco-private",
        "SUPPORTING_FILE_OBJECT_REGION": "local-1",
        "SUPPORTING_FILE_OBJECT_ACCESS_KEY_FILE": object_access,
        "SUPPORTING_FILE_OBJECT_SECRET_KEY_FILE": object_secret,
        "SATCO_BACKUP_POLICY_ID": "backup-v1",
        "SATCO_BACKUP_ENCRYPTION_KEY_REFERENCE": "key-ref-v1",
        "SATCO_MONITORING_TOKEN": "m" * 40,
        "SATCO_OPS_MODE_FILE": "/private/test/mode.json",
        "SATCO_OPS_MODE_HMAC_KEY_FILE": "/private/test/mode-key",
    }
    values.update(overrides)
    return Settings(**values)


def manifest(path):
    path.write_text(json.dumps({
        "release_id": "r1", "git_commit": "abcdef0",
        "backend_image_digest": "sha256:" + "a" * 64, "frontend_asset_digest": "sha256:" + "b" * 64,
        "expected_alembic_head": "e04500000001", "configuration_schema_version": "v1",
        "migration_artifact_digest": "sha256:" + "c" * 64, "dependency_lock_digest": "sha256:" + "d" * 64,
        "package_lock_digest": "sha256:" + "e" * 64,
        "sbom_reference": "sbom", "scan_evidence_reference": "scan",
        "created_at": "2026-08-20T00:00:00+00:00",
        "signing_approver_evidence_reference": "approval-1",
    }), encoding="utf-8")


def test_production_configuration_accepts_complete_safe_values(tmp_path):
    path = tmp_path / "manifest.json"
    manifest(path)
    validate_production_settings(production_settings(str(path)))


@pytest.mark.parametrize("override", [
    {"SECRET_KEY": "CHANGE_THIS_SECRET_KEY"},
    {"SATCO_TRUSTED_HOSTS": "*"},
    {"SATCO_ALLOWED_ORIGINS": "*"},
    {"SATCO_OBJECT_HEALTH_URL": "http://unsafe"},
    {"SUPPORTING_FILE_SCANNER_ENDPOINT": "http://unsafe"},
    {"SUPPORTING_FILE_OBJECT_ENDPOINT": "http://unsafe"},
    {"SATCO_BACKUP_POLICY_ID": ""},
    {"SATCO_OPS_MODE_FILE": ""},
    {"COPILOT_ENABLED": True, "COPILOT_PROVIDER_ENDPOINT": "", "COPILOT_PROVIDER_API_KEY": ""},
])
def test_production_configuration_rejects_unsafe_values(tmp_path, override):
    path = tmp_path / "manifest.json"
    manifest(path)
    with pytest.raises(ProductionConfigurationError):
        validate_production_settings(production_settings(str(path), **override))


def test_bootstrap_requires_secret_and_window(tmp_path):
    path = tmp_path / "manifest.json"
    manifest(path)
    with pytest.raises(ProductionConfigurationError):
        validate_production_settings(production_settings(
            str(path), SATCO_BOOTSTRAP_ENABLED=True, PLATFORM_BOOTSTRAP_KEY="a" * 40
        ))


def test_application_secret_files_are_the_values_consumed_by_runtime(tmp_path):
    signing = tmp_path / "signing"
    bootstrap = tmp_path / "bootstrap"
    signing.write_text("s" * 40, encoding="utf-8")
    bootstrap.write_text("b" * 40, encoding="utf-8")
    configured = Settings(
        SECRET_KEY_FILE=str(signing),
        PLATFORM_BOOTSTRAP_KEY_FILE=str(bootstrap),
    )
    assert configured.SECRET_KEY == "s" * 40
    assert configured.PLATFORM_BOOTSTRAP_KEY == "b" * 40
