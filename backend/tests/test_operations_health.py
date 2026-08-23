import json
import os
import subprocess
from pathlib import Path

from app.core import operations

from app.core.config import Settings
from app.core.operations import ensure_governed_write_allowed, readiness_snapshot, GovernedWriteBlocked


ROOT = Path(__file__).resolve().parents[2]


def test_non_production_is_ready_without_production_profile():
    snapshot = readiness_snapshot(Settings(SATCO_ENVIRONMENT="development"))
    assert snapshot.ready is True
    assert snapshot.mode == "normal"


def test_recovery_mode_blocks_governed_writes_and_is_not_ready(tmp_path):
    mode = tmp_path / "mode.json"
    mode.write_text(json.dumps({"mode": "RECOVERY_PROTECTION_DEGRADED"}), encoding="utf-8")
    settings = Settings(SATCO_ENVIRONMENT="development", SATCO_OPS_MODE_FILE=str(mode))
    snapshot = readiness_snapshot(settings)
    assert snapshot.ready is False
    try:
        ensure_governed_write_allowed(settings, "POST")
    except GovernedWriteBlocked:
        pass
    else:
        raise AssertionError("governed write unexpectedly allowed")
    ensure_governed_write_allowed(settings, "GET")


def test_production_readiness_requires_database_and_non_content_health(tmp_path, monkeypatch):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({
        "release_id": "r", "git_commit": "abcdef0",
        "backend_image_digest": "sha256:" + "a" * 64, "frontend_asset_digest": "sha256:" + "b" * 64,
        "expected_alembic_head": "e04400000001", "configuration_schema_version": "v1",
        "migration_artifact_digest": "sha256:" + "c" * 64, "dependency_lock_digest": "sha256:" + "d" * 64,
        "package_lock_digest": "sha256:" + "e" * 64,
        "sbom_reference": "s", "scan_evidence_reference": "scan",
        "created_at": "2026-08-20T00:00:00+00:00",
        "signing_approver_evidence_reference": "approval-1",
    }), encoding="utf-8")
    mode = tmp_path / "mode.json"
    mode_key = tmp_path / "mode-key"
    mode_key.write_text("test-mode-key", encoding="utf-8")
    scanner_token = tmp_path / "scanner-token"
    scanner_token.write_text("s" * 40, encoding="utf-8")
    object_access_key = tmp_path / "object-access-key"
    object_access_key.write_text("test-access-key", encoding="utf-8")
    object_secret_key = tmp_path / "object-secret-key"
    object_secret_key.write_text("o" * 40, encoding="utf-8")
    subprocess.run(
        ["sh", str(ROOT / "ops/scripts/set-ops-mode.sh"), "normal"],
        check=True,
        env=os.environ
        | {
            "SATCO_OPS_MODE_FILE": str(mode),
            "SATCO_OPS_MODE_HMAC_KEY_FILE": str(mode_key),
        },
    )
    settings = Settings(
        SATCO_ENVIRONMENT="production", SECRET_KEY="a" * 40,
        SATCO_RELEASE_MANIFEST_PATH=str(manifest), SATCO_PUBLIC_URL="https://satco.example",
        SATCO_TRUSTED_HOSTS="satco.example", SATCO_ALLOWED_ORIGINS="https://satco.example",
        SATCO_EXPECTED_ALEMBIC_HEAD="e04400000001", SATCO_PERSISTENCE_GUARD_VERSION="v1",
        SATCO_OBJECT_HEALTH_URL="https://ops.internal/health", SATCO_BACKUP_POLICY_ID="b",
        SATCO_OBJECT_HEALTH_CA_FILE="/private/test/monitor-ca.pem",
        SUPPORTING_FILE_SCANNER_ENDPOINT="https://scanner.internal/scan",
        SUPPORTING_FILE_SCANNER_TOKEN_FILE=str(scanner_token),
        SUPPORTING_FILE_OBJECT_ENDPOINT="https://objects.internal",
        SUPPORTING_FILE_OBJECT_BUCKET="satco-supporting-files",
        SUPPORTING_FILE_OBJECT_REGION="test-region-1",
        SUPPORTING_FILE_OBJECT_ACCESS_KEY_FILE=str(object_access_key),
        SUPPORTING_FILE_OBJECT_SECRET_KEY_FILE=str(object_secret_key),
        SATCO_BACKUP_ENCRYPTION_KEY_REFERENCE="k",
        SATCO_MONITORING_TOKEN="m" * 40,
        SATCO_OPS_MODE_FILE=str(mode),
        SATCO_OPS_MODE_HMAC_KEY_FILE=str(mode_key),
    )
    monkeypatch.setattr(operations, "_database_ready", lambda _settings: True)
    monkeypatch.setattr(operations, "_object_health_ready", lambda _settings: True)
    assert readiness_snapshot(settings).ready is True
    monkeypatch.setattr(operations, "_object_health_ready", lambda _settings: False)
    assert readiness_snapshot(settings).ready is False
    monkeypatch.setattr(operations, "_object_health_ready", lambda _settings: True)
    monkeypatch.setattr(operations, "_database_ready", lambda _settings: False)
    assert readiness_snapshot(settings).ready is False
