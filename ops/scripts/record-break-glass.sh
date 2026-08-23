#!/usr/bin/env sh
set -eu
: "${SATCO_ACTIVE_INCIDENT_ID:?required}"
: "${SATCO_HUMAN_AUTHORIZATION_ID:?required}"
: "${SATCO_BREAK_GLASS_SCOPE:?required}"
: "${SATCO_BREAK_GLASS_TARGET:?required}"
: "${SATCO_BREAK_GLASS_ACTION:?required}"
: "${SATCO_BREAK_GLASS_SAFE_OUTCOME:?required}"
: "${SATCO_AUTHORIZATION_START:?required}"
: "${SATCO_AUTHORIZATION_END:?required}"
: "${SATCO_PRIMARY_RECORDER_AVAILABLE:?required}"
if [ "$SATCO_PRIMARY_RECORDER_AVAILABLE" = "true" ]; then exit 0; fi
: "${SATCO_ALTERNATE_RECORDER_URL:?pre-established alternate endpoint required}"
: "${SATCO_ALTERNATE_RECORDER_CLIENT_CERT:?required}"
: "${SATCO_ALTERNATE_RECORDER_CLIENT_KEY:?required}"
case "$SATCO_ALTERNATE_RECORDER_URL" in https://*) ;; *) exit 77 ;; esac
payload="$(python3 - "$SATCO_ACTIVE_INCIDENT_ID" "$SATCO_HUMAN_AUTHORIZATION_ID" "$SATCO_BREAK_GLASS_SCOPE" "$SATCO_BREAK_GLASS_TARGET" "$SATCO_BREAK_GLASS_ACTION" "$SATCO_BREAK_GLASS_SAFE_OUTCOME" "$SATCO_AUTHORIZATION_START" "$SATCO_AUTHORIZATION_END" <<'PY'
import datetime as dt, json, sys
incident, authorization, scope, target, action, outcome, start_text, end_text = sys.argv[1:]
assert all(value and len(value) <= 128 for value in (incident, authorization, scope, target, action, outcome))
start = dt.datetime.fromisoformat(start_text.replace("Z", "+00:00"))
end = dt.datetime.fromisoformat(end_text.replace("Z", "+00:00"))
now = dt.datetime.now(dt.timezone.utc)
assert start.tzinfo is not None and end.tzinfo is not None
assert start <= now < end <= start + dt.timedelta(hours=4)
print(json.dumps({
    "incident_id": incident,
    "authorization_id": authorization,
    "scope": scope, "target": target, "action": action,
    "safe_outcome": outcome, "observed_at": now.isoformat(),
}, sort_keys=True, separators=(",", ":")))
PY
)"
curl --fail --silent --show-error --cert "$SATCO_ALTERNATE_RECORDER_CLIENT_CERT" --key "$SATCO_ALTERNATE_RECORDER_CLIENT_KEY" --header 'Content-Type: application/json' --data "$payload" "$SATCO_ALTERNATE_RECORDER_URL" >/dev/null
