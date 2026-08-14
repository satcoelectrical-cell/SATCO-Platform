"""Transport-neutral Organizational Memory domain failures."""


class OrganizationalMemoryError(ValueError):
    code = "ORGANIZATIONAL_MEMORY_ERROR"

    def __init__(self, message: str = "Organizational Memory operation failed") -> None:
        super().__init__(message)


class OrganizationalMemoryValidationError(OrganizationalMemoryError):
    code = "ORGANIZATIONAL_MEMORY_VALIDATION_ERROR"


class OrganizationalMemoryIntegrityError(OrganizationalMemoryError):
    code = "ORGANIZATIONAL_MEMORY_INTEGRITY_ERROR"

    def __init__(self, message: str = "Organizational Memory integrity validation failed") -> None:
        super().__init__(message)


class OrganizationalMemoryInvalidStanding(OrganizationalMemoryError):
    code = "ORGANIZATIONAL_MEMORY_INVALID_STANDING"

    def __init__(self) -> None:
        super().__init__("Organizational Memory standing does not permit this operation")


class OrganizationalMemoryVersionConflict(OrganizationalMemoryError):
    code = "ORGANIZATIONAL_MEMORY_VERSION_CONFLICT"

    def __init__(self) -> None:
        super().__init__("Organizational Memory version conflict")


class OrganizationalMemoryInvalidLineage(OrganizationalMemoryError):
    code = "ORGANIZATIONAL_MEMORY_INVALID_LINEAGE"

    def __init__(self, message: str = "Organizational Memory lineage is invalid") -> None:
        super().__init__(message)


class OrganizationalMemoryImmutable(OrganizationalMemoryError):
    code = "ORGANIZATIONAL_MEMORY_IMMUTABLE"

    def __init__(self) -> None:
        super().__init__("Admitted Organizational Memory state is immutable")
