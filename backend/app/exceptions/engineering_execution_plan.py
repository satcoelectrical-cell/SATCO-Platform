class EngineeringExecutionPlanError(ValueError):
    pass


class ExecutionPlanProtectedNotFound(EngineeringExecutionPlanError):
    pass


class ExecutionPlanInvalidRequest(EngineeringExecutionPlanError):
    pass


class ExecutionPlanVersionConflict(EngineeringExecutionPlanError):
    pass


class ExecutionPlanIdempotencyConflict(EngineeringExecutionPlanError):
    pass


class ExecutionPlanUnavailable(EngineeringExecutionPlanError):
    pass
