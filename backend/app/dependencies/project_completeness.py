"""Request-scoped PATCH-049 composition over public Project Context."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends

from app.dependencies.project_context import (
    ProjectContextApplication,
    get_project_context_application,
)
from app.ports.project_completeness import (
    CompletenessActor,
    ProjectContextObservationPort,
)
from app.schemas.project_context import ProjectContextRequest, ProjectContextResult
from app.services.project_completeness_service import ProjectCompletenessService


class ProjectContextCompletenessObserver(ProjectContextObservationPort):
    """Adapter deliberately calls only the public PATCH-048 application service."""

    def __init__(self, application: ProjectContextApplication) -> None:
        self._application = application

    def observe(
        self,
        *,
        actor: CompletenessActor,
        request: ProjectContextRequest,
        current_user: object,
    ) -> ProjectContextResult:
        if (
            actor.actor_id != self._application.actor.actor_id
            or actor.organization_id != self._application.actor.organization_id
            or current_user is not self._application.current_user
        ):
            from app.schemas.project_context import ProjectContextProtectedNotFound
            return ProjectContextProtectedNotFound()
        return self._application.service.assemble_project_context(
            actor=self._application.actor,
            request=request,
            current_user=self._application.current_user,
        )


@dataclass(frozen=True, slots=True)
class ProjectCompletenessApplication:
    service: ProjectCompletenessService
    actor: CompletenessActor
    current_user: object


def get_project_completeness_application(
    context: ProjectContextApplication = Depends(get_project_context_application),
) -> ProjectCompletenessApplication:
    actor = CompletenessActor(
        actor_id=context.actor.actor_id,
        organization_id=context.actor.organization_id,
    )
    return ProjectCompletenessApplication(
        service=ProjectCompletenessService(ProjectContextCompletenessObserver(context)),
        actor=actor,
        current_user=context.current_user,
    )
