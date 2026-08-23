#!/usr/bin/env sh
set -eu

: "${SATCO_OPS_MODE_FILE:?required}"
: "${SATCO_OPS_MODE_HMAC_KEY_FILE:?required}"
mode="${1:?normal|read_only|RECOVERY_PROTECTION_DEGRADED required}"
case "$mode" in normal|read_only|RECOVERY_PROTECTION_DEGRADED|reconcile) ;; *) exit 64 ;; esac
umask 077
python3 - "$SATCO_OPS_MODE_FILE" "$SATCO_OPS_MODE_HMAC_KEY_FILE" "$mode" <<'PY'
import hashlib, hmac, json, os, pathlib, sys, tempfile
target = pathlib.Path(sys.argv[1])
key_path = pathlib.Path(sys.argv[2])
mode = sys.argv[3]
target.parent.mkdir(parents=True, exist_ok=True)
key = key_path.read_bytes().strip()
if mode == "reconcile":
    existing = json.loads(target.read_text(encoding="utf-8"))
    signature = existing.pop("signature", None)
    encoded_existing = json.dumps(existing, sort_keys=True, separators=(",", ":")).encode()
    expected = hmac.new(key, encoded_existing, hashlib.sha256).hexdigest()
    if not isinstance(signature, str) or not hmac.compare_digest(signature, expected):
        raise SystemExit(65)
    mode = existing.get("mode")
    if mode not in {"normal", "read_only", "RECOVERY_PROTECTION_DEGRADED"}:
        raise SystemExit(65)
payload = {"mode": mode}
encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
payload["signature"] = hmac.new(key, encoded, hashlib.sha256).hexdigest()
with tempfile.NamedTemporaryFile("w", dir=target.parent, delete=False, encoding="utf-8") as stream:
    stream.write(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    temporary = pathlib.Path(stream.name)
os.chmod(temporary, 0o644)
os.replace(temporary, target)

edge_marker = target.parent / "write-blocked"
if mode == "normal":
    edge_marker.unlink(missing_ok=True)
else:
    with tempfile.NamedTemporaryFile("w", dir=target.parent, delete=False, encoding="utf-8") as stream:
        stream.write("blocked\n")
        temporary_marker = pathlib.Path(stream.name)
    os.chmod(temporary_marker, 0o644)
    os.replace(temporary_marker, edge_marker)
PY
