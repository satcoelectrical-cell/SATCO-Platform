from pathlib import Path


def test_required_operational_runbooks_are_governed_and_complete():
    text = (Path(__file__).resolve().parents[2] / "ops/runbooks/PATCH-042-Operational-Runbooks.md").read_text(encoding="utf-8")
    for title in ("Deployment", "Bootstrap", "Migration", "Backup", "Restore", "Recovery", "Rollback", "Break glass", "TLS lifecycle", "Monitoring fallback", "Vulnerability disposition"):
        assert title in text
    for required in ("Trigger and authority", "Steps/evidence", "Failure route", "No procedure grants"):
        assert required in text
