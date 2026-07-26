from .base import SatcoException


class ProjectNotFoundException(SatcoException):
    def __init__(self, project_id: int):
        super().__init__(
            status_code=404,
            code="PROJECT_NOT_FOUND",
            message=f"Project {project_id} not found",
        )


class ProjectRelatedEntityNotFoundException(SatcoException):
    def __init__(self, entity: str, entity_id: int):
        super().__init__(
            status_code=404,
            code=f"{entity.upper()}_NOT_FOUND",
            message=f"{entity.title()} {entity_id} not found",
        )


class ProjectForbiddenException(SatcoException):
    def __init__(self, message: str = "Project operation forbidden"):
        super().__init__(
            status_code=403,
            code="PROJECT_FORBIDDEN",
            message=message,
        )


class ProjectValidationException(SatcoException):
    def __init__(self, message: str):
        super().__init__(
            status_code=400,
            code="PROJECT_VALIDATION_ERROR",
            message=message,
        )
