#!/usr/bin/env sh
set -eu
: "${SATCO_HIGH_EXCEPTION_FILE:?required}"
: "${SATCO_ARTIFACT_DIGEST:?required}"
python3 - "$SATCO_HIGH_EXCEPTION_FILE" "$SATCO_ARTIFACT_DIGEST" <<'PY'
import datetime as d, json, re, sys
records=json.load(open(sys.argv[1], encoding='utf-8'))
assert isinstance(records, list)
now=d.datetime.now(d.timezone.utc)
seen=set()
for r in records:
    required={'finding_id','severity','source','artifact_digest','rationale','compensating_controls','scope','approver_id','approved_at','expires_at','retest_condition','retest_reference','retest_result','status'}
    assert set(r) == required
    assert all(isinstance(r[k], str) and r[k] for k in required)
    assert r['finding_id'] not in seen
    seen.add(r['finding_id'])
    assert r['severity']=='HIGH' and r['artifact_digest']==sys.argv[2]
    assert re.fullmatch(r'sha256:[0-9a-f]{64}', r['artifact_digest'])
    limits={'finding_id':128,'source':64,'rationale':2048,'compensating_controls':2048,'scope':512,'approver_id':128,'retest_condition':512,'retest_reference':512}
    assert all(len(r[key]) <= limit for key, limit in limits.items())
    approved=d.datetime.fromisoformat(r['approved_at'].replace('Z','+00:00'))
    expires=d.datetime.fromisoformat(r['expires_at'].replace('Z','+00:00'))
    assert approved <= now < expires
    assert r['status']=='active' and r['retest_result']=='pass'
PY
printf '%s\n' 'high-exception-pass'
