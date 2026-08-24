from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.enums.engineering_execution_plan import ExecutionActivityStanding, valid_activity_transition
from app.schemas.engineering_execution_plan import (
    CreateExecutionActivityRequest, ExecutionDependencyDTO, ExecutionPlanInvalidResult,
    ExecutionPlanProtectedResult, ExecutionProgressDTO, ReplaceExecutionDependenciesRequest,
    TransitionExecutionActivityRequest,
)


def test_activity_contract_is_closed_normalized_and_no_generic_progress_exists():
    value = CreateExecutionActivityRequest(
        expected_plan_version=1, title="  Prepare motor schedule ", description="  Human engineering activity ",
        ordinal=0, workspace_id=None, responsible_user_id=None, target_date=None,
        completion_basis="  Record the reviewed engineering result ", rationale="Human plan change",
    )
    assert value.title == "Prepare motor schedule"
    with pytest.raises(ValidationError):
        CreateExecutionActivityRequest(**{**value.model_dump(), "progress": 55})
    with pytest.raises(ValidationError):
        CreateExecutionActivityRequest(**{**value.model_dump(), "title": " "})


def test_standing_machine_is_closed_and_terminal_states_do_not_reopen():
    assert valid_activity_transition(ExecutionActivityStanding.PLANNED, ExecutionActivityStanding.READY)
    assert valid_activity_transition(ExecutionActivityStanding.IN_PROGRESS, ExecutionActivityStanding.COMPLETED)
    assert not valid_activity_transition(ExecutionActivityStanding.COMPLETED, ExecutionActivityStanding.IN_PROGRESS)
    with pytest.raises(ValidationError):
        TransitionExecutionActivityRequest(expected_activity_version=1, target_standing="done", rationale="Human completion")


def test_dependencies_are_unique_ordered_and_self_edges_are_rejected():
    first, second = uuid4(), uuid4()
    with pytest.raises(ValidationError):
        ExecutionDependencyDTO(predecessor_activity_id=first, dependent_activity_id=first)
    edge = ExecutionDependencyDTO(predecessor_activity_id=first, dependent_activity_id=second)
    with pytest.raises(ValidationError):
        ReplaceExecutionDependenciesRequest(expected_plan_version=1, dependencies=(edge, edge), rationale="Human sequencing")


def test_progress_is_derived_and_protected_results_are_payload_free():
    assert ExecutionProgressDTO(completed_count=2, eligible_count=3, percent=66).percent == 66
    with pytest.raises(ValidationError):
        ExecutionProgressDTO(completed_count=2, eligible_count=3, percent=67)
    assert ExecutionPlanProtectedResult().model_dump() == {"outcome": "protected_not_found"}
    assert ExecutionPlanInvalidResult().model_dump() == {"outcome": "invalid_request"}
