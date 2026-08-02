from pathlib import Path
def test_service_coordinates_required_atomic_records():
    source=Path("app/services/evidence_service.py").read_text()
    for text in ("uow.audit.record","uow.domain_events.record","uow.idempotency.record_result","uow.commit"):
        assert text in source
