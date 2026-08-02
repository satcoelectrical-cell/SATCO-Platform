import importlib.util
from pathlib import Path
def test_migration_is_bounded_and_reversible():
    path=Path("migrations/versions/e02700000001_evidence_foundation.py")
    source=path.read_text()
    assert 'down_revision="e02500000001"' in source
    for table in ("evidence","evidence_outbox","evidence_idempotency"): assert f'op.create_table("{table}"' in source and f'op.drop_table("{table}")' in source
