#!/usr/bin/env sh
set -eu
: "${SATCO_READY_URL:?required}"
: "${SATCO_MONITOR_EVIDENCE_FILE:?required}"
: "${SATCO_MONITOR_CA_FILE:?required}"
: "${SATCO_RECOVERY_SET_MANIFEST:?required}"
: "${SATCO_OPS_MODE_FILE:?required}"
: "${SATCO_OPS_MODE_HMAC_KEY_FILE:?required}"
case "$SATCO_READY_URL" in https://*) ;; *) exit 64 ;; esac
umask 077

record() {
  printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" >> "$SATCO_MONITOR_EVIDENCE_FILE"
}

degrade() {
  sh "$(dirname "$0")/set-ops-mode.sh" RECOVERY_PROTECTION_DEGRADED
  record "$1"
  exit 1
}

if ! python3 - "$SATCO_RECOVERY_SET_MANIFEST" <<'PY'
import datetime as dt, json, sys
payload = json.load(open(sys.argv[1], encoding="utf-8"))
assert payload.get("verification_state") == "verified"
finished = dt.datetime.fromisoformat(payload["finished_at"].replace("Z", "+00:00"))
assert finished.tzinfo is not None
age = dt.datetime.now(dt.timezone.utc) - finished.astimezone(dt.timezone.utc)
assert dt.timedelta(0) <= age <= dt.timedelta(hours=4)
PY
then
  degrade recovery_protection_degraded
fi

if python3 - "$SATCO_READY_URL" "$SATCO_MONITOR_CA_FILE" <<'PY'
import ssl, sys, urllib.request
context = ssl.create_default_context(cafile=sys.argv[2])
request = urllib.request.Request(sys.argv[1], method="GET")
with urllib.request.urlopen(request, timeout=5, context=context) as response:
    assert 200 <= response.status < 300
PY
then
  record ready
  exit 0
fi

if [ -n "${SATCO_MANUAL_FALLBACK_FILE:-}" ] && python3 - "$SATCO_MANUAL_FALLBACK_FILE" <<'PY'
import datetime as dt, json, sys
payload = json.load(open(sys.argv[1], encoding="utf-8"))
assert set(payload) == {"incident_id", "human_approver_id", "approved_at", "expires_at"}
assert all(isinstance(payload[key], str) and 1 <= len(payload[key]) <= 128 for key in ("incident_id", "human_approver_id"))
approved = dt.datetime.fromisoformat(payload["approved_at"].replace("Z", "+00:00"))
expires = dt.datetime.fromisoformat(payload["expires_at"].replace("Z", "+00:00"))
now = dt.datetime.now(dt.timezone.utc)
assert approved.tzinfo is not None and expires.tzinfo is not None
assert approved <= now < expires <= approved + dt.timedelta(hours=4)
PY
then
  record monitoring_manual_fallback
  exit 0
fi

degrade monitoring_unavailable
