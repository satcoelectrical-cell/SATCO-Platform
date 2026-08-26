from pathlib import Path
def test_service_coordinates_required_atomic_records():
    source=Path("app/services/evidence_service.py").read_text()
    for text in ("uow.audit.record","uow.domain_events.record","uow.idempotency.record_result","uow.commit"):
        assert text in source

def test_graph_link_owner_read_is_bounded_authorized_and_read_only():
    source=Path("app/services/evidence_service.py").read_text()
    assert "def get_supporting_file_graph_links" in source
    assert "def get_evidence_graph_links_for_file" in source
    block=source[source.index("def get_supporting_file_graph_links"):source.index("def list(self")]
    assert "limit=91" in block and "ReadEvidence" in block
    assert ".commit(" not in block and ".add(" not in block
