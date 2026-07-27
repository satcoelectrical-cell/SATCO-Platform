from .base import SatcoException


class RelationshipNotFound(SatcoException):
    def __init__(self):
        super().__init__(
            status_code=404,
            code="CONTEXT_RELATIONSHIP_NOT_FOUND",
            message="Context Relationship not found",
        )


class CommitmentNotFound(SatcoException):
    def __init__(self):
        super().__init__(
            status_code=404,
            code="INTERFACE_COMMITMENT_NOT_FOUND",
            message="Interface Commitment not found",
        )


class RelationshipForbidden(SatcoException):
    def __init__(self):
        super().__init__(
            status_code=403,
            code="CONTEXT_RELATIONSHIP_FORBIDDEN",
            message="Context Relationship operation forbidden",
        )


class InvalidRelationship(SatcoException):
    def __init__(self, message: str):
        super().__init__(
            status_code=422,
            code="INVALID_CONTEXT_RELATIONSHIP",
            message=message,
        )


class InvalidCommitment(SatcoException):
    def __init__(self, message: str):
        super().__init__(
            status_code=422,
            code="INVALID_INTERFACE_COMMITMENT",
            message=message,
        )


class DuplicateRelationship(SatcoException):
    def __init__(self):
        super().__init__(
            status_code=409,
            code="DUPLICATE_CONTEXT_RELATIONSHIP",
            message="An equivalent current Context Relationship exists",
        )


class RelationshipVersionConflict(SatcoException):
    def __init__(self):
        super().__init__(
            status_code=409,
            code="CONTEXT_RELATIONSHIP_VERSION_CONFLICT",
            message="Context Relationship was modified by another request",
        )


class CommitmentVersionConflict(SatcoException):
    def __init__(self):
        super().__init__(
            status_code=409,
            code="INTERFACE_COMMITMENT_VERSION_CONFLICT",
            message="Interface Commitment was modified by another request",
        )


class RelationshipLifecycleConflict(SatcoException):
    def __init__(self, current: str, target: str):
        super().__init__(
            status_code=409,
            code="CONTEXT_RELATIONSHIP_LIFECYCLE_CONFLICT",
            message=f"Invalid relationship transition: {current} -> {target}",
        )


class CommitmentLifecycleConflict(SatcoException):
    def __init__(self, current: str, target: str):
        super().__init__(
            status_code=409,
            code="INTERFACE_COMMITMENT_LIFECYCLE_CONFLICT",
            message=f"Invalid commitment transition: {current} -> {target}",
        )
