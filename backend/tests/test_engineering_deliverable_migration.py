from pathlib import Path
from alembic.config import Config
from alembic.script import ScriptDirectory


def test_deliverable_migration_is_the_sole_successor_head():
    script=ScriptDirectory.from_config(Config("alembic.ini"))
    assert script.get_heads()==["e04600000001"]
    assert script.get_revision("e04600000001").down_revision=="e04500000001"
    source=Path("migrations/versions/e04600000001_engineering_deliverable.py").read_text()
    for table in ("engineering_deliverables","engineering_deliverable_revisions","engineering_deliverable_history","engineering_deliverable_idempotency","engineering_deliverable_outbox"):
        assert table in source
    assert "satco_deliverable_guard" in source and "satco_deliverable_revision_guard" in source
