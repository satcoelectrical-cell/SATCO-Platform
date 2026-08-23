#!/usr/bin/env sh
set -eu

: "${SATCO_DIAGNOSTICS_FILE:?required}"
: "${SATCO_OPERATIONS_LOG_FILE:?required}"
: "${SATCO_RELEASE_MANIFEST_PATH:?required}"
: "${SATCO_SUPPORT_INCIDENT_REFERENCE:?required}"
: "${SATCO_SUPPORT_RECIPIENT:?required}"
: "${SATCO_SUPPORT_BUNDLE_OUTPUT:?required}"
command -v age >/dev/null
command -v tar >/dev/null

umask 077
bundle_dir="$(mktemp -d)"
plain="$(mktemp)"
trap 'rm -rf "$bundle_dir"; rm -f "$plain"' EXIT HUP INT TERM

python3 - "$SATCO_DIAGNOSTICS_FILE" "$SATCO_OPERATIONS_LOG_FILE" "$SATCO_RELEASE_MANIFEST_PATH" "$SATCO_SUPPORT_INCIDENT_REFERENCE" "$bundle_dir" <<'PY'
import datetime as dt, json, pathlib, sys

diagnostics_path, log_path, release_path, incident, output_dir = sys.argv[1:]
assert 1 <= len(incident) <= 128
output = pathlib.Path(output_dir)

diagnostics = json.load(open(diagnostics_path, encoding="utf-8"))
diagnostic_keys = {"environment", "readiness", "operational_mode", "expected_alembic_head", "observed_at"}
assert isinstance(diagnostics, dict) and set(diagnostics) <= diagnostic_keys
assert all(isinstance(value, str) and len(value) <= 128 for value in diagnostics.values())
(output / "diagnostics.json").write_text(json.dumps(diagnostics, sort_keys=True, separators=(",", ":")), encoding="utf-8")

allowed_log_keys = {"timestamp", "event_code", "correlation_id", "component", "release_id", "outcome", "duration_ms", "actor_id"}
safe_events = []
for raw in pathlib.Path(log_path).read_text(encoding="utf-8").splitlines()[-1000:]:
    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        continue
    if not isinstance(event, dict) or not set(event) <= allowed_log_keys:
        continue
    if any(isinstance(value, str) and len(value) > 128 for value in event.values()):
        continue
    safe_events.append(event)
(output / "operations.json").write_text(json.dumps(safe_events, sort_keys=True, separators=(",", ":")), encoding="utf-8")

release = json.load(open(release_path, encoding="utf-8"))
release_reference = {key: release[key] for key in ("release_id", "git_commit", "expected_alembic_head")}
(output / "release.json").write_text(json.dumps(release_reference, sort_keys=True, separators=(",", ":")), encoding="utf-8")
(output / "bundle.json").write_text(json.dumps({
    "incident_reference": incident,
    "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    "event_count": len(safe_events),
}, sort_keys=True, separators=(",", ":")), encoding="utf-8")
PY

tar -C "$bundle_dir" -cf "$plain" bundle.json diagnostics.json operations.json release.json
age -r "$SATCO_SUPPORT_RECIPIENT" -o "$SATCO_SUPPORT_BUNDLE_OUTPUT" "$plain"
printf '%s\n' 'support-bundle-created'
