"""Narrow PATCH-049 public Project Context observation boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.schemas.project_context import ProjectContextRequest, ProjectContextResult


@dataclass(frozen=True, slots=True)
class CompletenessActor:
    """Trusted server-bound actor; Organization is never transport input."""

    actor_id: int
    organization_id: UUID


@dataclass(frozen=True, slots=True)
class CompletenessAssessmentRequest:
    project_id: int
    workspace_id: int | None = None

    def __post_init__(self) -> None:
        if type(self.project_id) is not int or self.project_id <= 0:
            raise ValueError("project_id must be positive")
        if self.workspace_id is not None and (
            type(self.workspace_id) is not int or self.workspace_id <= 0
        ):
            raise ValueError("workspace_id must be positive when supplied")


class ProjectContextObservationPort(Protocol):
    """One fresh, typed public Project Context call; no owner persistence seam."""

    def observe(
        self,
        *,
        actor: CompletenessActor,
        request: ProjectContextRequest,
        current_user: object,
    ) -> ProjectContextResult: ...
