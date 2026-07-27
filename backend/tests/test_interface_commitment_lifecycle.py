import pytest

from app.enums import InterfaceCommitmentState
from app.exceptions.engineering_context_relationship import InvalidCommitment
from app.models.audit_log import AuditLog
from app.models.engineering_context_relationship import InterfaceCommitment
from app.services.engineering_context_relationship_service import (
    COMMITMENT_TRANSITIONS,
)


def test_commitment_has_exactly_eight_states():
    assert {state.value for state in InterfaceCommitmentState} == {
        "identified",
        "acknowledged_by_provider",
        "information_provided",
        "consumer_review_required",
        "fulfilled_for_stated_use",
        "rejected",
        "disputed",
        "superseded",
    }


def test_delivery_review_and_fulfilment_are_distinct():
    assert (
        InterfaceCommitmentState.CONSUMER_REVIEW_REQUIRED
        in COMMITMENT_TRANSITIONS[
            InterfaceCommitmentState.INFORMATION_PROVIDED
        ]
    )
    assert (
        InterfaceCommitmentState.FULFILLED_FOR_STATED_USE
        not in COMMITMENT_TRANSITIONS[
            InterfaceCommitmentState.ACKNOWLEDGED_BY_PROVIDER
        ]
    )


def test_superseded_is_terminal_and_withdrawal_is_not_a_state():
    assert not COMMITMENT_TRANSITIONS[
        InterfaceCommitmentState.SUPERSEDED
    ]
    with pytest.raises(ValueError):
        InterfaceCommitmentState("withdrawn")
    assert "current_use" in InterfaceCommitment.__table__.columns


def test_commitment_retains_source_revision_and_reassessment():
    columns = InterfaceCommitment.__table__.columns
    assert columns.supplied_source_key is not None
    assert columns.supplied_revision is not None
    assert columns.reassessment_needed.nullable is False


def test_required_external_review_blocks_fulfilment_atomically(
    relationship_domain,
):
    domain = relationship_domain
    service = domain["service"]
    owner = domain["actors"]["project_owner"]
    provider = domain["actors"]["provider"]
    consumer = domain["actors"]["consumer"]
    relationship_record = service.create_relationship(
        data={
            "project_id": domain["project"].id,
            "meaning": "requires",
            "purpose": "Reviewed information dependency",
            "source_role": "provider",
            "target_role": "consumer",
            "source": {
                "kind": "workspace",
                "workspace_id": domain["provider_workspace"].id,
            },
            "target": {
                "kind": "workspace",
                "workspace_id": domain["consumer_workspace"].id,
            },
            "steward_id": owner.id,
        },
        current_user=owner,
    )
    commitment = service.create_commitment(
        data={
            "relationship_id": relationship_record["id"],
            "provider_kind": "workspace",
            "provider_workspace_id": domain["provider_workspace"].id,
            "consumer_workspace_id": domain["consumer_workspace"].id,
            "required_information": "Reviewed load schedule",
            "intended_use": "Consumer detailed design",
            "completeness_expectation": "Complete and revision identified",
            "expected_source_basis": "Approved calculation",
            "stage_or_due_condition": "Before detailed design",
            "criticality": "critical",
            "confidentiality": "project",
            "steward_id": owner.id,
            "consumer_reviewer_id": consumer.id,
            "external_review_required": True,
        },
        current_user=owner,
    )
    service.transition_commitment(
        commitment_id=commitment["id"],
        target="acknowledged_by_provider",
        expected_version=1,
        reason="Provider accepts responsibility",
        current_user=provider,
    )
    provided = service.transition_commitment(
        commitment_id=commitment["id"],
        target="information_provided",
        expected_version=2,
        reason="Information supplied",
        supplied_source_key="CALC-001",
        supplied_revision="A",
        current_user=provider,
    )
    audit_count = service.db.query(AuditLog).count()
    with pytest.raises(InvalidCommitment):
        service.transition_commitment(
            commitment_id=commitment["id"],
            target="fulfilled_for_stated_use",
            expected_version=provided["version"],
            reason="Attempt without review evidence",
            fulfilment_use="Consumer detailed design",
            current_user=consumer,
        )
    unchanged = service.get_commitment(
        commitment_id=commitment["id"],
        current_user=consumer,
    )
    assert unchanged["state"] == "information_provided"
    assert unchanged["version"] == provided["version"]
    assert service.db.query(AuditLog).count() == audit_count

    fulfilled = service.transition_commitment(
        commitment_id=commitment["id"],
        target="fulfilled_for_stated_use",
        expected_version=provided["version"],
        reason="Reviewed for stated use",
        fulfilment_use="Consumer detailed design",
        external_review_evidence="EXT-REVIEW-202022",
        current_user=consumer,
    )
    assert fulfilled["external_review_evidence"] == "EXT-REVIEW-202022"
