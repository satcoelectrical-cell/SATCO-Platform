class ProjectFoundationError(ValueError):
    pass


class ProjectFoundationProtectedNotFound(ProjectFoundationError):
    pass


class ProjectFoundationInvalidRequest(ProjectFoundationError):
    pass


class ProjectFoundationVersionConflict(ProjectFoundationError):
    pass


class ProjectFoundationUnavailable(ProjectFoundationError):
    pass
