from pathlib import Path


def test_service_maps_all_approved_commands_and_atomic_effects():
    source = Path("app/services/engineering_relationship_service.py").read_text()
    for command in (
        "CreateEngineeringRelationship",
        "SubmitEngineeringRelationshipForReview",
        "ReviewEngineeringRelationship",
        "ApproveEngineeringRelationship",
        "DisputeEngineeringRelationship",
        "RejectEngineeringRelationship",
        "TransitionEngineeringRelationshipLifecycle",
        "TransferEngineeringRelationshipSteward",
    ):
        assert command in source
    for effect in (
        "uow.audit.record", "uow.domain_events.record",
        "uow.idempotency.record_result", "uow.commit()",
    ):
        assert effect in source


def test_service_has_no_transport_or_direct_session_dependency():
    source = Path("app/services/engineering_relationship_service.py").read_text()
    assert "fastapi" not in source.lower()
    assert "Session" not in source
