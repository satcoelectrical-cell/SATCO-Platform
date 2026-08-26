from pathlib import Path
def test_repository_has_no_transaction_or_policy_ownership():
    source=Path("app/repositories/evidence_repository.py").read_text()
    assert ".commit(" not in source and "authorize(" not in source and "delete(" not in source

def test_graph_link_selectors_are_exact_bounded_and_deterministic():
    source=Path("app/repositories/evidence_repository.py").read_text()
    assert "def list_graph_links_for_evidence" in source
    assert "def list_graph_links_for_asset" in source
    assert source.count(".limit(limit).all()") >= 2
    assert "EvidenceSupportingFileLink.ordinal" in source
