import pytest

from app.enums.project_foundation import ProjectEngineeringStage, is_forward_stage, stages_are_adjacent
from app.models.project_foundation import valid_input_transition
from app.enums.project_foundation import ProjectInputStanding


def test_project_stage_machine_is_linear_and_distinct_from_project_status():
    stages = list(ProjectEngineeringStage)
    assert [stage.value for stage in stages] == [
        "definition", "preparation", "execution", "verification", "completion_readiness",
    ]
    for index, current in enumerate(stages):
        for other_index, target in enumerate(stages):
            assert stages_are_adjacent(current, target) is (abs(index - other_index) == 1)
    assert is_forward_stage(ProjectEngineeringStage.DEFINITION, ProjectEngineeringStage.PREPARATION)
    assert not is_forward_stage(ProjectEngineeringStage.EXECUTION, ProjectEngineeringStage.PREPARATION)


def test_required_input_state_machine_is_closed():
    valid = {
        ("missing", "received"), ("missing", "clarification_required"), ("missing", "not_applicable"),
        ("clarification_required", "missing"), ("clarification_required", "received"),
        ("clarification_required", "not_applicable"), ("received", "missing"),
        ("received", "clarification_required"), ("not_applicable", "missing"),
        ("not_applicable", "clarification_required"),
    }
    for current in ProjectInputStanding:
        for target in ProjectInputStanding:
            assert valid_input_transition(current, target) is ((current.value, target.value) in valid)


def test_no_project_foundation_enum_invents_tasks_deliverables_or_approval():
    vocabulary = " ".join(item.value for enum in (ProjectEngineeringStage, ProjectInputStanding) for item in enum)
    for prohibited in ("task", "milestone", "deliverable", "approved", "procurement", "closeout"):
        assert prohibited not in vocabulary
