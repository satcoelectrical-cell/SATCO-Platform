from .base import SatcoException


class ContextNotFound(SatcoException):
    def __init__(self, context_id: int):
        super().__init__(
            status_code=404,
            code="ENGINEERING_CONTEXT_NOT_FOUND",
            message=f"Engineering Context {context_id} not found",
        )


class ContextForbidden(SatcoException):
    def __init__(self):
        super().__init__(
            status_code=403,
            code="ENGINEERING_CONTEXT_FORBIDDEN",
            message="Engineering Context operation forbidden",
        )


class InvalidContext(SatcoException):
    def __init__(self, message: str):
        super().__init__(
            status_code=422,
            code="INVALID_ENGINEERING_CONTEXT",
            message=message,
        )


class InvalidContextResponsibility(SatcoException):
    def __init__(self):
        super().__init__(
            status_code=422,
            code="INVALID_CONTEXT_RESPONSIBILITY",
            message=(
                "Context owner and steward must be active internal Users"
            ),
        )


class ContextVersionConflict(SatcoException):
    def __init__(self):
        super().__init__(
            status_code=409,
            code="ENGINEERING_CONTEXT_VERSION_CONFLICT",
            message="Engineering Context was modified by another request",
        )


class ContextLifecycleConflict(SatcoException):
    def __init__(self, current: str, target: str):
        super().__init__(
            status_code=409,
            code="ENGINEERING_CONTEXT_LIFECYCLE_CONFLICT",
            message=(
                "Invalid Engineering Context lifecycle transition: "
                f"{current} -> {target}"
            ),
        )
