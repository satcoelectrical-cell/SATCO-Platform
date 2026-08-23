from enum import Enum


class ProjectFoundationAvailability(str, Enum):
    BASIS_NOT_ESTABLISHED = "basis_not_established"
    ESTABLISHED = "established"


class ProjectScopeKind(str, Enum):
    IN_SCOPE = "in_scope"
    OUT_OF_SCOPE = "out_of_scope"


class ProjectEngineeringStage(str, Enum):
    DEFINITION = "definition"
    PREPARATION = "preparation"
    EXECUTION = "execution"
    VERIFICATION = "verification"
    COMPLETION_READINESS = "completion_readiness"


PROJECT_STAGE_ORDER = tuple(ProjectEngineeringStage)
PROJECT_STAGE_RANK = {stage: index for index, stage in enumerate(PROJECT_STAGE_ORDER)}


class ProjectInputStanding(str, Enum):
    MISSING = "missing"
    RECEIVED = "received"
    CLARIFICATION_REQUIRED = "clarification_required"
    NOT_APPLICABLE = "not_applicable"


class ProjectInputSourceKind(str, Enum):
    SUPPORTING_FILE = "supporting_file"
    EVIDENCE = "evidence"


class ProjectReadinessState(str, Enum):
    READY = "ready"
    BLOCKED = "blocked"
    NOT_APPLICABLE = "not_applicable"


class ProjectReadinessBlockerCode(str, Enum):
    DEFINITION_INCOMPLETE = "definition_incomplete"
    SCOPE_INCOMPLETE = "scope_incomplete"
    COMPLETION_BASIS_INCOMPLETE = "completion_basis_incomplete"
    REQUIRED_INPUTS_NOT_DEFINED = "required_inputs_not_defined"
    INPUT_MISSING = "input_missing"
    INPUT_CLARIFICATION_REQUIRED = "input_clarification_required"
    INPUT_SOURCE_REAUTHORIZATION_REQUIRED = "input_source_reauthorization_required"


def stages_are_adjacent(current: ProjectEngineeringStage, target: ProjectEngineeringStage) -> bool:
    return abs(PROJECT_STAGE_RANK[current] - PROJECT_STAGE_RANK[target]) == 1


def is_forward_stage(current: ProjectEngineeringStage, target: ProjectEngineeringStage) -> bool:
    return PROJECT_STAGE_RANK[target] > PROJECT_STAGE_RANK[current]
