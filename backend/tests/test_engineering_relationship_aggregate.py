"""PATCH-026 Sprint-1 aggregate and vocabulary tests."""

from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.enums import EngineeringAuthorityStanding
from app.enums import EngineeringRelationshipLifecycle as RelationshipLifecycle
from app.enums import RelationshipFamily, RelationshipType
from app.enums import validate_relationship_pair
from app.models.engineering_relationship import EngineeringRelationship
from app.models.engineering_relationship_command import (
    ApproveEngineeringRelationship,
    AuthenticatedRelationshipActor,
    CreateEngineeringRelationship,
    EngineeringRelationshipInvariantViolation,
    EngineeringRelationshipMutation,
    EngineeringRelationshipTransitionRejected,
    EngineeringRelationshipVersionMismatch,
    RelationshipAuthorizationContext,
    RelationshipCommandMetadata,
    RelationshipValidationResult,
    ReviewEngineeringRelationship,
    SubmitEngineeringRelationshipForReview,
    TransferEngineeringRelationshipSteward,
    TransitionEngineeringRelationshipLifecycle,
)


NOW = datetime(2026, 8, 1, 8, 0, tzinfo=timezone.utc)
ORGANIZATION_ID = uuid4()


def metadata(actor_id: int = 7, evidence=()) -> RelationshipCommandMetadata:
    return RelationshipCommandMetadata(
        actor=AuthenticatedRelationshipActor(actor_id, ORGANIZATION_ID),
        authorization=RelationshipAuthorizationContext("relationship.command", {}),
        rationale="Approved engineering rationale",
        correlation_id=uuid4(), idempotency_id=uuid4(), command_id=uuid4(),
        evidence_references=tuple(evidence),
    )


def validation(**overrides) -> RelationshipValidationResult:
    values = {
        "source_organization_id": ORGANIZATION_ID,
        "target_organization_id": ORGANIZATION_ID,
        "source_project_id": 3, "target_project_id": 3,
        "source_workspace_id": 4, "target_workspace_id": 4,
    }
    values.update(overrides)
    return RelationshipValidationResult(**values)


def create_command(**overrides) -> CreateEngineeringRelationship:
    values = {
        "metadata": metadata(evidence=(uuid4(),)),
        "relationship_family": RelationshipFamily.ELECTRICAL,
        "relationship_type": RelationshipType.POWERED_BY,
        "source_object_id": uuid4(), "target_object_id": uuid4(),
        "organization_id": ORGANIZATION_ID, "project_id": 3,
        "workspace_id": 4,
        "creator_id": 7, "steward_id": 7, "validation": validation(),
    }
    values.update(overrides)
    return CreateEngineeringRelationship(**values)


def create_relationship(**overrides) -> EngineeringRelationship:
    aggregate, result = EngineeringRelationship.create(
        create_command(**overrides), NOW
    )
    assert result.previous_version is None
    assert result.events[0].event_type == "EngineeringRelationshipCreated"
    return aggregate


def mutation(command_type, aggregate, *, actor_id=7, evidence=(), **values):
    return command_type(
        metadata=metadata(actor_id, evidence), relationship_id=aggregate.id,
        relationship_family=RelationshipFamily(aggregate.relationship_family),
        relationship_type=RelationshipType(aggregate.relationship_type),
        expected_version=aggregate.version, **values,
    )


def test_family_and_type_are_a_required_canonical_pair() -> None:
    mutation_fields = {field.name for field in fields(EngineeringRelationshipMutation)}
    assert {"relationship_family", "relationship_type"} <= mutation_fields

    validate_relationship_pair(
        RelationshipFamily.INSTRUMENTATION,
        RelationshipType.MONITORED_BY,
    )
    validate_relationship_pair(
        RelationshipFamily.AUTOMATION,
        RelationshipType.MONITORED_BY,
    )
    with pytest.raises(ValueError):
        validate_relationship_pair(
            RelationshipFamily.ELECTRICAL,
            RelationshipType.MONITORED_BY,
        )


def test_create_preserves_direction_and_approved_defaults() -> None:
    command = create_command()
    aggregate, _ = EngineeringRelationship.create(command, NOW)

    assert aggregate.source_object_id == command.source_object_id
    assert aggregate.target_object_id == command.target_object_id
    assert aggregate.relationship_family == "electrical"
    assert aggregate.relationship_type == "powered_by"
    assert aggregate.lifecycle == RelationshipLifecycle.PROPOSED.value
    assert aggregate.authority_standing == EngineeringAuthorityStanding.DRAFT.value
    assert aggregate.version == 1


@pytest.mark.parametrize(
    "override",
    [
        {"active_duplicate_exists": True},
        {"target_organization_id": uuid4()},
        {"target_project_id": 99},
    ],
)
def test_create_rejects_duplicate_and_scope_violations(override) -> None:
    with pytest.raises(EngineeringRelationshipInvariantViolation):
        create_relationship(validation=validation(**override))


def test_self_reference_is_prohibited() -> None:
    object_id = uuid4()
    with pytest.raises(EngineeringRelationshipInvariantViolation):
        create_relationship(
            source_object_id=object_id,
            target_object_id=object_id,
        )


def test_cross_workspace_policy_is_family_scoped() -> None:
    cross_workspace = validation(target_workspace_id=8)
    create_relationship(validation=cross_workspace)

    with pytest.raises(EngineeringRelationshipInvariantViolation):
        create_relationship(
            relationship_family=RelationshipFamily.STRUCTURAL,
            relationship_type=RelationshipType.PART_OF,
            validation=cross_workspace,
        )


def test_cycles_are_rejected_only_for_approved_acyclic_pairs() -> None:
    cycle = validation(prohibited_cycle_exists=True)
    with pytest.raises(EngineeringRelationshipInvariantViolation):
        create_relationship(validation=cycle)

    create_relationship(
        relationship_family=RelationshipFamily.PHYSICAL,
        relationship_type=RelationshipType.CONNECTED_TO,
        validation=cycle,
    )


def test_review_approval_and_current_lifecycle_are_human_governed() -> None:
    aggregate = create_relationship()
    submitted = aggregate.submit_for_review(
        mutation(SubmitEngineeringRelationshipForReview, aggregate),
        NOW + timedelta(minutes=1),
    )
    assert submitted.version == 2

    aggregate.review(
        mutation(ReviewEngineeringRelationship, aggregate, actor_id=8),
        NOW + timedelta(minutes=2),
    )
    aggregate.approve(
        mutation(ApproveEngineeringRelationship, aggregate, actor_id=9),
        NOW + timedelta(minutes=3),
    )
    result = aggregate.transition_lifecycle(
        mutation(
            TransitionEngineeringRelationshipLifecycle,
            aggregate,
            lifecycle=RelationshipLifecycle.CURRENT,
        ),
        NOW + timedelta(minutes=4),
    )

    assert aggregate.reviewer_id == 8
    assert aggregate.approver_id == 9
    assert aggregate.lifecycle == RelationshipLifecycle.CURRENT.value
    assert result.version == 5


def test_approver_must_differ_from_creator_and_reviewer() -> None:
    aggregate = create_relationship()
    aggregate.submit_for_review(
        mutation(SubmitEngineeringRelationshipForReview, aggregate), NOW
    )
    aggregate.review(
        mutation(ReviewEngineeringRelationship, aggregate, actor_id=8), NOW
    )
    with pytest.raises(EngineeringRelationshipTransitionRejected):
        aggregate.approve(
            mutation(ApproveEngineeringRelationship, aggregate, actor_id=8), NOW
        )


def test_withdrawal_is_logical_and_restorable() -> None:
    aggregate = create_relationship()
    aggregate.transition_lifecycle(
        mutation(
            TransitionEngineeringRelationshipLifecycle, aggregate,
            lifecycle=RelationshipLifecycle.WITHDRAWN,
        ), NOW,
    )
    assert aggregate.lifecycle == RelationshipLifecycle.WITHDRAWN.value

    aggregate.transition_lifecycle(
        mutation(
            TransitionEngineeringRelationshipLifecycle, aggregate,
            lifecycle=RelationshipLifecycle.PROPOSED,
        ), NOW + timedelta(minutes=1),
    )
    assert aggregate.lifecycle == RelationshipLifecycle.PROPOSED.value


def test_stale_version_and_unchanged_steward_preserve_state() -> None:
    aggregate = create_relationship()
    stale = mutation(
        TransferEngineeringRelationshipSteward, aggregate,
        steward_id=9,
    )
    stale = replace(stale, expected_version=2)
    with pytest.raises(EngineeringRelationshipVersionMismatch):
        aggregate.transfer_steward(stale, NOW)
    assert aggregate.version == 1
    assert aggregate.steward_id == 7
