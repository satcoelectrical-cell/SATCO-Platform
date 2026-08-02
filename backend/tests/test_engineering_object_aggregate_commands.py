"""Sprint-1 unit tests for EngineeringObject aggregate commands."""

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from uuid import uuid4

import pytest

from app.enums import EngineeringAuthorityStanding
from app.enums import EngineeringDiscipline
from app.enums import EngineeringLifecycle
from app.enums import EngineeringObjectFamily
from app.enums import EngineeringObjectType
from app.models.engineering_object import EngineeringObject
from app.models.engineering_object_command import AuthenticatedActor
from app.models.engineering_object_command import AuthorizationContext
from app.models.engineering_object_command import CommandMetadata
from app.models.engineering_object_command import CreateEngineeringObject
from app.models.engineering_object_command import EngineeringObjectNoOp
from app.models.engineering_object_command import EngineeringObjectTransitionRejected
from app.models.engineering_object_command import EngineeringObjectVersionMismatch
from app.models.engineering_object_command import ReclassifyEngineeringObject
from app.models.engineering_object_command import TransferEngineeringObjectSteward
from app.models.engineering_object_command import TransitionEngineeringObjectAuthority
from app.models.engineering_object_command import TransitionEngineeringObjectLifecycle


NOW = datetime(2026, 8, 1, 8, 0, tzinfo=timezone.utc)


def metadata(operation: str) -> CommandMetadata:
    organization_id = uuid4()
    return CommandMetadata(
        actor=AuthenticatedActor(7, organization_id),
        authorization=AuthorizationContext(operation, {}),
        rationale="Approved engineering rationale",
        correlation_id=uuid4(),
        idempotency_id=uuid4(),
        command_id=uuid4(),
    )


def create_object() -> EngineeringObject:
    command_metadata = metadata("engineering_object.create")
    aggregate, result = EngineeringObject.create(
        CreateEngineeringObject(
            metadata=command_metadata,
            organization_id=command_metadata.actor.organization_id,
            customer_id=None,
            project_id=3,
            workspace_id=4,
            family=EngineeringObjectFamily.ELECTRICAL,
            discipline=EngineeringDiscipline.ELECTRICAL,
            object_type=EngineeringObjectType.MOTOR,
            creator_id=7,
            steward_id=7,
        ),
        NOW,
    )
    assert result.previous_version is None
    assert result.version == 1
    assert result.events[0].event_type == "EngineeringObjectCreated"
    return aggregate


def test_create_applies_blueprint_defaults() -> None:
    aggregate = create_object()

    assert aggregate.lifecycle == EngineeringLifecycle.PROPOSED.value
    assert aggregate.authority_standing == (
        EngineeringAuthorityStanding.DRAFT.value
    )
    assert aggregate.version == 1
    assert aggregate.created_at == aggregate.updated_at == NOW


def test_reclassify_changes_complete_classification_once() -> None:
    aggregate = create_object()
    command_metadata = metadata("engineering_object.reclassify")

    result = aggregate.reclassify(
        ReclassifyEngineeringObject(
            metadata=command_metadata,
            object_id=aggregate.id,
            expected_version=1,
            family=EngineeringObjectFamily.AUTOMATION,
            discipline=EngineeringDiscipline.INDUSTRIAL_AUTOMATION,
            object_type=EngineeringObjectType.PLC,
        ),
        NOW + timedelta(minutes=1),
    )

    assert aggregate.family == EngineeringObjectFamily.AUTOMATION.value
    assert aggregate.discipline == (
        EngineeringDiscipline.INDUSTRIAL_AUTOMATION.value
    )
    assert aggregate.object_type == EngineeringObjectType.PLC.value
    assert result.previous_version == 1
    assert result.version == 2
    assert result.events[0].event_type == "EngineeringObjectReclassified"


def test_material_reclassification_reassesses_authority() -> None:
    aggregate = create_object()
    aggregate.authority_standing = EngineeringAuthorityStanding.APPROVED
    command_metadata = metadata("engineering_object.reclassify")

    result = aggregate.reclassify(
        ReclassifyEngineeringObject(
            metadata=command_metadata,
            object_id=aggregate.id,
            expected_version=1,
            family=EngineeringObjectFamily.AUTOMATION,
            discipline=EngineeringDiscipline.INDUSTRIAL_AUTOMATION,
            object_type=EngineeringObjectType.PLC,
        ),
        NOW + timedelta(minutes=1),
    )

    assert aggregate.authority_standing == (
        EngineeringAuthorityStanding.PROPOSED.value
    )
    assert [event.event_type for event in result.events] == [
        "EngineeringObjectReclassified",
        "EngineeringObjectAuthorityTransitioned",
    ]


def test_lifecycle_transition_requires_approved_path() -> None:
    aggregate = create_object()
    command_metadata = metadata("engineering_object.transition_lifecycle")

    with pytest.raises(EngineeringObjectTransitionRejected):
        aggregate.transition_lifecycle(
            TransitionEngineeringObjectLifecycle(
                metadata=command_metadata,
                object_id=aggregate.id,
                expected_version=1,
                lifecycle=EngineeringLifecycle.RETIRED,
            ),
            NOW + timedelta(minutes=1),
        )

    assert aggregate.lifecycle == EngineeringLifecycle.PROPOSED.value
    assert aggregate.version == 1


def test_supersession_requires_distinct_replacement() -> None:
    aggregate = create_object()
    aggregate.lifecycle = EngineeringLifecycle.ACTIVE
    command_metadata = metadata("engineering_object.transition_lifecycle")

    with pytest.raises(EngineeringObjectTransitionRejected):
        aggregate.transition_lifecycle(
            TransitionEngineeringObjectLifecycle(
                metadata=command_metadata,
                object_id=aggregate.id,
                expected_version=1,
                lifecycle=EngineeringLifecycle.SUPERSEDED,
            ),
            NOW + timedelta(minutes=1),
        )

    result = aggregate.transition_lifecycle(
        TransitionEngineeringObjectLifecycle(
            metadata=command_metadata,
            object_id=aggregate.id,
            expected_version=1,
            lifecycle=EngineeringLifecycle.SUPERSEDED,
            replacement_object_id=uuid4(),
        ),
        NOW + timedelta(minutes=1),
    )
    assert result.version == 2


def test_authority_transition_uses_approved_matrix() -> None:
    aggregate = create_object()
    command_metadata = metadata("engineering_object.transition_authority")

    result = aggregate.transition_authority(
        TransitionEngineeringObjectAuthority(
            metadata=command_metadata,
            object_id=aggregate.id,
            expected_version=1,
            authority_standing=EngineeringAuthorityStanding.PROPOSED,
        ),
        NOW + timedelta(minutes=1),
    )

    assert aggregate.authority_standing == (
        EngineeringAuthorityStanding.PROPOSED.value
    )
    assert result.version == 2


def test_transfer_steward_preserves_unrelated_state() -> None:
    aggregate = create_object()
    command_metadata = metadata("engineering_object.transfer_steward")
    original = (
        aggregate.id,
        aggregate.creator_id,
        aggregate.family,
        aggregate.lifecycle,
        aggregate.authority_standing,
    )

    result = aggregate.transfer_steward(
        TransferEngineeringObjectSteward(
            metadata=command_metadata,
            object_id=aggregate.id,
            expected_version=1,
            steward_id=9,
        ),
        NOW + timedelta(minutes=1),
    )

    assert aggregate.steward_id == 9
    assert result.version == 2
    assert original == (
        aggregate.id,
        aggregate.creator_id,
        aggregate.family,
        aggregate.lifecycle,
        aggregate.authority_standing,
    )


def test_stale_and_no_op_commands_leave_state_unchanged() -> None:
    aggregate = create_object()
    command_metadata = metadata("engineering_object.transfer_steward")

    with pytest.raises(EngineeringObjectVersionMismatch):
        aggregate.transfer_steward(
            TransferEngineeringObjectSteward(
                metadata=command_metadata,
                object_id=aggregate.id,
                expected_version=2,
                steward_id=9,
            ),
            NOW + timedelta(minutes=1),
        )
    with pytest.raises(EngineeringObjectNoOp):
        aggregate.transfer_steward(
            TransferEngineeringObjectSteward(
                metadata=command_metadata,
                object_id=aggregate.id,
                expected_version=1,
                steward_id=7,
            ),
            NOW + timedelta(minutes=1),
        )

    assert aggregate.steward_id == 7
    assert aggregate.version == 1

