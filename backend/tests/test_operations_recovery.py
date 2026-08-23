import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.core.config import Settings
from app.core.operations import ensure_governed_write_allowed, GovernedWriteBlocked


ROOT = Path(__file__).resolve().parents[2]


def test_ops_mode_script_signs_degraded_mode(tmp_path):
    mode = tmp_path / "mode.json"
    key = tmp_path / "key"
    key.write_text("test-key", encoding="utf-8")
    environment = os.environ | {
        "SATCO_OPS_MODE_FILE": str(mode),
        "SATCO_OPS_MODE_HMAC_KEY_FILE": str(key),
    }
    subprocess.run(["sh", str(ROOT / "ops/scripts/set-ops-mode.sh"), "RECOVERY_PROTECTION_DEGRADED"], check=True, env=environment)
    assert json.loads(mode.read_text(encoding="utf-8"))["mode"] == "RECOVERY_PROTECTION_DEGRADED"
    assert (tmp_path / "write-blocked").read_text(encoding="utf-8") == "blocked\n"
    (tmp_path / "write-blocked").unlink()
    subprocess.run(["sh", str(ROOT / "ops/scripts/set-ops-mode.sh"), "reconcile"], check=True, env=environment)
    assert json.loads(mode.read_text(encoding="utf-8"))["mode"] == "RECOVERY_PROTECTION_DEGRADED"
    assert (tmp_path / "write-blocked").read_text(encoding="utf-8") == "blocked\n"
    with __import__("pytest").raises(GovernedWriteBlocked):
        ensure_governed_write_allowed(Settings(SATCO_OPS_MODE_FILE=str(mode), SATCO_OPS_MODE_HMAC_KEY_FILE=str(key)), "POST")
    subprocess.run(["sh", str(ROOT / "ops/scripts/set-ops-mode.sh"), "normal"], check=True, env=environment)
    assert not (tmp_path / "write-blocked").exists()


def test_rollback_refuses_unsupported_schema_rollback(tmp_path):
    result = subprocess.run(
        ["sh", str(ROOT / "ops/scripts/rollback.sh")],
        env=os.environ | {"SATCO_COMPATIBLE_ROLLBACK": "false"},
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "recovery-set" in result.stderr


def test_preflight_maps_governed_runtime_role_to_alembic_contract():
    script = (ROOT / "ops/scripts/preflight.sh").read_text(encoding="utf-8")
    assert ': "${SATCO_RUNTIME_DATABASE_ROLE:?required}"' in script
    assert ': "${MIGRATION_DATABASE_ROLE:?required}"' in script
    assert 'export RUNTIME_DATABASE_ROLE="$SATCO_RUNTIME_DATABASE_ROLE"' in script
    assert 'test "$SATCO_RUNTIME_DATABASE_ROLE" != "$MIGRATION_DATABASE_ROLE"' in script
    assert "CREATE ROLE {} LOGIN NOINHERIT NOSUPERUSER" in script
    assert 'SATCO_PREFLIGHT_PHASE" = "before' in script
    assert 'payload.get("verification_state") == "verified"' in script


def test_backup_and_restore_fail_closed_and_remove_plaintext():
    backup = (ROOT / "ops/scripts/backup.sh").read_text(encoding="utf-8")
    restore = (ROOT / "ops/scripts/restore-verify.sh").read_text(encoding="utf-8")
    for script in (backup, restore):
        assert "trap 'rm -f \"$plain\"' EXIT HUP INT TERM" in script
    for field in (
        "deployment_id", "release_id", "configuration_id", "alembic_head",
        "encryption_key_reference", "operational_actor_id", "database_sha256",
    ):
        assert field in backup
    assert "sha256sum" in restore
    assert "pg_restore --exit-on-error" in restore
    assert "SELECT version_num FROM alembic_version" in restore
    assert 'payload["verification_state"] = "verified"' in restore
    upgrade = (ROOT / "ops/scripts/upgrade.sh").read_text(encoding="utf-8")
    assert "restore-verify.sh" in upgrade
    assert "SATCO_PREFLIGHT_PHASE=before" in upgrade
    assert "SATCO_PREFLIGHT_PHASE=after" in upgrade
    assert "SATCO_PREUPGRADE_RECOVERY_SET_MANIFEST" in upgrade


def test_stale_verified_recovery_set_activates_both_write_gates(tmp_path):
    mode = tmp_path / "mode.json"
    key = tmp_path / "key"
    evidence = tmp_path / "evidence.log"
    recovery = tmp_path / "recovery.json"
    ca_file = tmp_path / "ca.pem"
    key.write_text("test-key", encoding="utf-8")
    ca_file.write_text("not-used-for-stale-path", encoding="utf-8")
    recovery.write_text(
        json.dumps(
            {
                "verification_state": "verified",
                "finished_at": (
                    datetime.now(timezone.utc) - timedelta(hours=5)
                ).isoformat(),
            }
        ),
        encoding="utf-8",
    )
    result = subprocess.run(
        ["sh", str(ROOT / "ops/scripts/ops-monitor.sh")],
        env=os.environ
        | {
            "SATCO_READY_URL": "https://not-used.invalid/health/ready",
            "SATCO_MONITOR_CA_FILE": str(ca_file),
            "SATCO_MONITOR_EVIDENCE_FILE": str(evidence),
            "SATCO_RECOVERY_SET_MANIFEST": str(recovery),
            "SATCO_OPS_MODE_FILE": str(mode),
            "SATCO_OPS_MODE_HMAC_KEY_FILE": str(key),
        },
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert json.loads(mode.read_text(encoding="utf-8"))["mode"] == "RECOVERY_PROTECTION_DEGRADED"
    assert (tmp_path / "write-blocked").read_text(encoding="utf-8") == "blocked\n"
    assert "recovery_protection_degraded" in evidence.read_text(encoding="utf-8")
