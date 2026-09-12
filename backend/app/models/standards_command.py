"""Small immutable command records used by the standards service."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RightsCapabilityDecision:
    permitted: bool
    failure_code: str | None
    binding_id: UUID | None = None
    binding_version: int | None = None


@dataclass(frozen=True, slots=True)
class StandardsCommandResult:
    status_code: int
    body: dict
    resource_id: UUID | None
    completed_at: datetime
