import json
import os
import subprocess
import tarfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.core.operational_logging import safe_operational_event
from app.api.v1.routers.operations import require_monitoring_principal
from app.core.config import settings
from fastapi import HTTPException
import pytest


ROOT = Path(__file__).resolve().parents[2]


def test_operational_logging_drops_secret_and_customer_content():
    payload = json.loads(safe_operational_event(
        "ops.test", component="backend", secret="never", customer_content="never"
    ))
    assert payload["component"] == "backend"
    assert "secret" not in payload
    assert "customer_content" not in payload


def _high_exception(now):
    return {
        "finding_id": "CVE-TEST", "severity": "HIGH", "source": "scanner",
        "artifact_digest": "sha256:" + "a" * 64, "rationale": "bounded",
        "compensating_controls": "isolated", "scope": "one artifact",
        "approver_id": "security-human", "approved_at": now.isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "retest_condition": "scanner rerun", "retest_reference": "scan-1",
        "retest_result": "pass", "status": "active",
    }


def test_high_exception_validator_accepts_one_active_record_and_rejects_duplicates(tmp_path):
    now = datetime.now(timezone.utc)
    record = _high_exception(now)
    evidence = tmp_path / "exceptions.json"
    environment = os.environ | {
        "SATCO_HIGH_EXCEPTION_FILE": str(evidence),
        "SATCO_ARTIFACT_DIGEST": record["artifact_digest"],
    }
    script = str(ROOT / "ops/scripts/validate-high-exceptions.sh")
    evidence.write_text(json.dumps([record]), encoding="utf-8")
    assert subprocess.run(["sh", script], env=environment).returncode == 0
    evidence.write_text(json.dumps([record, record]), encoding="utf-8")
    assert subprocess.run(["sh", script], env=environment).returncode != 0


def test_monitoring_principal_is_dedicated_and_fail_closed(tmp_path, monkeypatch):
    token = tmp_path / "monitoring-token"
    token.write_text("m" * 40, encoding="utf-8")
    monkeypatch.setattr(settings, "SATCO_MONITORING_TOKEN_FILE", str(token))
    monkeypatch.setattr(settings, "SATCO_MONITORING_TOKEN", "")
    require_monitoring_principal("m" * 40)
    with pytest.raises(HTTPException) as denied:
        require_monitoring_principal("wrong")
    assert denied.value.status_code == 403
    assert denied.value.detail == "forbidden"


def test_break_glass_rejects_expired_human_authorization_before_recording(tmp_path):
    now = datetime.now(timezone.utc)
    environment = os.environ | {
        "SATCO_ACTIVE_INCIDENT_ID": "incident-1",
        "SATCO_HUMAN_AUTHORIZATION_ID": "human-approval-1",
        "SATCO_BREAK_GLASS_SCOPE": "diagnostics-only",
        "SATCO_BREAK_GLASS_TARGET": "deployment-1",
        "SATCO_BREAK_GLASS_ACTION": "read-safe-diagnostics",
        "SATCO_BREAK_GLASS_SAFE_OUTCOME": "denied",
        "SATCO_AUTHORIZATION_START": (now - timedelta(hours=2)).isoformat(),
        "SATCO_AUTHORIZATION_END": (now - timedelta(hours=1)).isoformat(),
        "SATCO_PRIMARY_RECORDER_AVAILABLE": "false",
        "SATCO_ALTERNATE_RECORDER_URL": "https://recorder.invalid/events",
        "SATCO_ALTERNATE_RECORDER_CLIENT_CERT": str(tmp_path / "cert"),
        "SATCO_ALTERNATE_RECORDER_CLIENT_KEY": str(tmp_path / "key"),
    }
    result = subprocess.run(
        ["sh", str(ROOT / "ops/scripts/record-break-glass.sh")],
        env=environment,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "incident-1" not in result.stdout + result.stderr


def test_support_bundle_is_bounded_allow_listed_and_excludes_unknown_content(tmp_path):
    diagnostics = tmp_path / "diagnostics.json"
    operations = tmp_path / "operations.log"
    release = tmp_path / "release.json"
    output = tmp_path / "bundle.age"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_age = fake_bin / "age"
    fake_age.write_text("#!/bin/sh\ncp \"$5\" \"$4\"\n", encoding="utf-8")
    fake_age.chmod(0o700)
    diagnostics.write_text(
        json.dumps({"readiness": "ready", "operational_mode": "normal"}),
        encoding="utf-8",
    )
    operations.write_text(
        json.dumps({"event_code": "safe", "outcome": "pass"})
        + "\n"
        + json.dumps({"event_code": "unsafe", "customer_content": "never"})
        + "\n",
        encoding="utf-8",
    )
    release.write_text(
        json.dumps(
            {
                "release_id": "r1",
                "git_commit": "abcdef0",
                "expected_alembic_head": "e04100000001",
                "secret": "never",
            }
        ),
        encoding="utf-8",
    )
    environment = os.environ | {
        "PATH": str(fake_bin) + os.pathsep + os.environ["PATH"],
        "SATCO_DIAGNOSTICS_FILE": str(diagnostics),
        "SATCO_OPERATIONS_LOG_FILE": str(operations),
        "SATCO_RELEASE_MANIFEST_PATH": str(release),
        "SATCO_SUPPORT_INCIDENT_REFERENCE": "incident-1",
        "SATCO_SUPPORT_RECIPIENT": "age-test-recipient",
        "SATCO_SUPPORT_BUNDLE_OUTPUT": str(output),
    }
    result = subprocess.run(
        ["sh", str(ROOT / "ops/scripts/support-bundle.sh")],
        env=environment,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    with tarfile.open(output) as archive:
        operations_payload = archive.extractfile("operations.json").read()
        release_payload = archive.extractfile("release.json").read()
    assert b"safe" in operations_payload
    assert b"customer_content" not in operations_payload
    assert b"never" not in operations_payload + release_payload
