from .base import SatcoException


class WorkspaceNotFound(SatcoException):
    def __init__(self, workspace_id: int):
        super().__init__(
            status_code=404,
            code="WORKSPACE_NOT_FOUND",
            message=f"Engineering Workspace {workspace_id} not found",
        )


class WorkspaceAlreadyExists(SatcoException):
    def __init__(self):
        super().__init__(
            status_code=409,
            code="WORKSPACE_ALREADY_EXISTS",
            message=(
                "An Engineering Workspace already exists for this "
                "Project and Discipline"
            ),
        )


class InvalidWorkspaceStatusTransition(SatcoException):
    def __init__(self, current: str, target: str):
        super().__init__(
            status_code=409,
            code="INVALID_WORKSPACE_STATUS_TRANSITION",
            message=(
                "Invalid Engineering Workspace status transition: "
                f"{current} -> {target}"
            ),
        )


class WorkspaceArchived(SatcoException):
    def __init__(self):
        super().__init__(
            status_code=409,
            code="WORKSPACE_ARCHIVED",
            message="Engineering Workspace is archived",
        )


class InvalidWorkspaceOwner(SatcoException):
    def __init__(self):
        super().__init__(
            status_code=422,
            code="INVALID_WORKSPACE_OWNER",
            message="Workspace owner must be an active internal User",
        )


class InvalidWorkspaceAssignee(SatcoException):
    def __init__(self):
        super().__init__(
            status_code=422,
            code="INVALID_WORKSPACE_ASSIGNEE",
            message=(
                "Workspace primary assignee must be an active internal User"
            ),
        )


class InvalidWorkspaceCollaborator(SatcoException):
    def __init__(self, message: str = "Invalid Workspace collaborator"):
        super().__init__(
            status_code=422,
            code="INVALID_WORKSPACE_COLLABORATOR",
            message=message,
        )


class WorkspaceMemberAlreadyExists(SatcoException):
    def __init__(self):
        super().__init__(
            status_code=409,
            code="WORKSPACE_MEMBER_ALREADY_EXISTS",
            message="User is already a Workspace collaborator",
        )


class WorkspaceMemberNotFound(SatcoException):
    def __init__(self):
        super().__init__(
            status_code=404,
            code="WORKSPACE_MEMBER_NOT_FOUND",
            message="Workspace collaborator not found",
        )


class WorkspaceVersionConflict(SatcoException):
    def __init__(self):
        super().__init__(
            status_code=409,
            code="WORKSPACE_VERSION_CONFLICT",
            message="Engineering Workspace was modified by another request",
        )


class WorkspaceForbidden(SatcoException):
    def __init__(self):
        super().__init__(
            status_code=403,
            code="WORKSPACE_FORBIDDEN",
            message="Engineering Workspace operation forbidden",
        )


class WorkspaceProjectStateConflict(SatcoException):
    def __init__(self, message: str):
        super().__init__(
            status_code=409,
            code="WORKSPACE_PROJECT_STATE_CONFLICT",
            message=message,
        )


class DisciplineNotSupported(SatcoException):
    def __init__(self):
        super().__init__(
            status_code=422,
            code="DISCIPLINE_NOT_SUPPORTED",
            message="Engineering Discipline is not supported",
        )


class ProjectHasWorkspaceHistory(SatcoException):
    def __init__(self):
        super().__init__(
            status_code=409,
            code="PROJECT_HAS_WORKSPACE_HISTORY",
            message=(
                "Project cannot be deleted after Engineering Workspace "
                "history exists"
            ),
        )
