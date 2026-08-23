from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.enums.project_foundation import ProjectEngineeringStage, ProjectInputStanding
from app.schemas.project_foundation import (
    ProjectFoundationInvalidResult,
    ProjectFoundationNotEstablished,
    ProjectFoundationProtectedResult,
    ProjectInputSafeSource,
    ProjectRequiredInputDTO,
    PutProjectFoundationRequest,
    ReorderProjectInputsRequest,
    TransitionProjectInputRequest,
)


def test_basis_contract_is_closed_normalized_and_requires_real_collections():
    value = PutProjectFoundationRequest(
        expected_version=0, purpose="  Conveyor control  ", engineering_basis=" PLC and panel engineering ",
        in_scope=("Control-system engineering",), out_of_scope=(),
        completion_criteria=("Recorded engineering basis reviewed",), rationale="Human establishment",
    )
    assert value.purpose == "Conveyor control"
    with pytest.raises(ValidationError):
        PutProjectFoundationRequest(**{**value.model_dump(), "unexpected": True})
    with pytest.raises(ValidationError):
        PutProjectFoundationRequest(**{**value.model_dump(), "in_scope": ("Panel", " panel ")})
    with pytest.raises(ValidationError):
        PutProjectFoundationRequest(**{**value.model_dump(), "completion_criteria": ()})


def test_input_transition_source_pair_is_exact_and_unsupported_values_fail():
    source_id = uuid4()
    received = TransitionProjectInputRequest(
        expected_foundation_version=1, expected_input_version=1,
        target_standing="received", source_kind="evidence", source_id=source_id,
        rationale="Authorized current Evidence received",
    )
    assert received.target_standing is ProjectInputStanding.RECEIVED
    for bad in (
        {"target_standing": "received", "source_kind": None, "source_id": None},
        {"target_standing": "missing", "source_kind": "evidence", "source_id": source_id},
        {"target_standing": "expected", "source_kind": None, "source_id": None},
        {"target_standing": "received", "source_kind": "capture", "source_id": source_id},
    ):
        with pytest.raises(ValidationError):
            TransitionProjectInputRequest(
                expected_foundation_version=1, expected_input_version=1,
                rationale="Human rationale", **bad,
            )


def test_reorder_requires_every_identity_once_and_protected_results_are_payload_free():
    identity = uuid4()
    with pytest.raises(ValidationError):
        ReorderProjectInputsRequest(expected_foundation_version=1, ordered_input_ids=(identity, identity), rationale="Order")
    assert ProjectFoundationProtectedResult().model_dump() == {"outcome": "protected_not_found"}
    assert ProjectFoundationInvalidResult().model_dump() == {"outcome": "invalid_request"}
    assert ProjectFoundationNotEstablished(project_id=7).model_dump(exclude_defaults=False)["availability"] == "basis_not_established"


def test_safe_source_is_present_only_when_independently_authorized():
    now = datetime.now(timezone.utc)
    source = ProjectInputSafeSource(kind="supporting_file", source_id=uuid4(), version=2, workspace_id=9)
    item = ProjectRequiredInputDTO(
        id=uuid4(), title="Motor datasheet", description=None, ordinal=0,
        required_by_stage=ProjectEngineeringStage.PREPARATION, standing="received",
        source_condition="authorized_current", source=source, version=2,
        standing_changed_at=now, updated_at=now,
    )
    assert item.source == source
    with pytest.raises(ValidationError):
        ProjectRequiredInputDTO(**{**item.model_dump(), "source_condition": "source_reauthorization_required"})
