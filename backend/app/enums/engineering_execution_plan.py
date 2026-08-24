from enum import Enum


class ExecutionActivityStanding(str, Enum):
    PLANNED = "planned"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ExecutionMilestoneStanding(str, Enum):
    NOT_READY = "not_ready"
    BLOCKED = "blocked"
    ACHIEVED = "achieved"


class ExecutionOperation(str, Enum):
    ESTABLISH_PLAN = "establish_plan"
    CREATE_ACTIVITY = "create_activity"
    UPDATE_ACTIVITY = "update_activity"
    TRANSITION_ACTIVITY = "transition_activity"
    REPLACE_DEPENDENCIES = "replace_dependencies"
    CREATE_MILESTONE = "create_milestone"
    UPDATE_MILESTONE = "update_milestone"


EXECUTION_ACTIVITY_TERMINAL = frozenset({
    ExecutionActivityStanding.COMPLETED,
    ExecutionActivityStanding.CANCELLED,
})
EXECUTION_ACTIVITY_EXECUTABLE = frozenset({
    ExecutionActivityStanding.PLANNED,
    ExecutionActivityStanding.READY,
    ExecutionActivityStanding.IN_PROGRESS,
})


def valid_activity_transition(current: ExecutionActivityStanding, target: ExecutionActivityStanding) -> bool:
    allowed = {
        ExecutionActivityStanding.PLANNED: {
            ExecutionActivityStanding.READY, ExecutionActivityStanding.BLOCKED,
            ExecutionActivityStanding.CANCELLED,
        },
        ExecutionActivityStanding.READY: {
            ExecutionActivityStanding.IN_PROGRESS, ExecutionActivityStanding.BLOCKED,
            ExecutionActivityStanding.CANCELLED,
        },
        ExecutionActivityStanding.IN_PROGRESS: {
            ExecutionActivityStanding.COMPLETED, ExecutionActivityStanding.BLOCKED,
            ExecutionActivityStanding.CANCELLED,
        },
        ExecutionActivityStanding.BLOCKED: set(EXECUTION_ACTIVITY_EXECUTABLE) | {
            ExecutionActivityStanding.CANCELLED,
        },
        ExecutionActivityStanding.COMPLETED: set(),
        ExecutionActivityStanding.CANCELLED: set(),
    }
    return target in allowed[current]
