from .base import SatcoException


class ProjectNotFoundException(SatcoException):
    def __init__(self, project_id: int):
        super().__init__(
            status_code=404,
            code="PROJECT_NOT_FOUND",
            message=f"Project {project_id} not found",
        )
