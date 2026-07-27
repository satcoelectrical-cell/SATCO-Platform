from enum import Enum


class Discipline(str, Enum):
    ELECTRICAL = "electrical"
    INSTRUMENTATION = "instrumentation"
    CONTROL = "control"
    MECHANICAL = "mechanical"
    CIVIL = "civil"
    PROCESS = "process"

    @property
    def display_name(self) -> str:
        return f"{self.value.title()} Engineering Workspace"
