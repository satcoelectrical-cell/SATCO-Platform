import hashlib
import json

from scripts.discipline_package_preflight import _canonical


def test_preflight_digest_is_canonical_and_stable():
    payload = {"overall": "PASS", "schema_version": 1}
    assert hashlib.sha256(_canonical(payload)).hexdigest() == hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
