from pathlib import Path
def test_repository_has_no_transaction_or_policy_ownership():
    source=Path("app/repositories/evidence_repository.py").read_text()
    assert ".commit(" not in source and "authorize(" not in source and "delete(" not in source
