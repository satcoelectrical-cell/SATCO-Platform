from pathlib import Path
def test_single_uow_owns_commit_and_rollback():
    source=Path("app/repositories/evidence_unit_of_work.py").read_text()
    assert "self.session.commit()" in source and "self.session.rollback()" in source
