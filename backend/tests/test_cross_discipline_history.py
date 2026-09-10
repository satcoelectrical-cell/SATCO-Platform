from uuid import uuid4

from app.discipline_packages.cross_discipline.canonical import digest
from app.services.cross_discipline_service import (
    lineage_would_cycle, verify_retained_snapshot,
)


def test_historical_verification_uses_exact_retained_bytes():
    payload = {"configuration_revision": 1, "result_digest": "e" * 64}
    snapshot_digest = digest(payload, "satco:cross-discipline-snapshot:v1")
    assert verify_retained_snapshot(payload=payload, expected_snapshot_digest=snapshot_digest, expected_result_digest="e" * 64)["outcome"] == "verified"
    changed = {**payload, "configuration_revision": 2}
    assert verify_retained_snapshot(payload=changed, expected_snapshot_digest=snapshot_digest, expected_result_digest="e" * 64) == {
        "outcome": "mismatch", "reason_code": "snapshot_digest_mismatch",
    }


def test_lineage_rejects_self_links_and_cycles_but_allows_parallel_reassessment():
    first, second, third = uuid4(), uuid4(), uuid4()
    assert lineage_would_cycle((), first, first)
    assert not lineage_would_cycle(((first, second),), first, third)
    assert lineage_would_cycle(((first, second), (second, third)), third, first)
