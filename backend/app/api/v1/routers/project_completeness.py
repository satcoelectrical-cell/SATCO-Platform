"""Thin authenticated PATCH-049 Project Completeness transport."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import ValidationError

from app.dependencies.project_completeness import (
    ProjectCompletenessApplication,
    get_project_completeness_application,
)
from app.ports.project_completeness import CompletenessAssessmentRequest
from app.schemas.project_completeness import (
    CompletenessAssessmentResult,
    CompletenessInvalidRequest,
)

router = APIRouter(tags=["Project Completeness"])


@router.get(
    "/projects/{project_id}/completeness",
    response_model=CompletenessAssessmentResult,
)
def assess_project_completeness(
    project_id: str,
    workspace_id: str | None = None,
    application: ProjectCompletenessApplication = Depends(
        get_project_completeness_application
    ),
):
    try:
        request = CompletenessAssessmentRequest(
            project_id=int(project_id),
            workspace_id=None if workspace_id is None else int(workspace_id),
        )
    except (TypeError, ValueError, ValidationError):
        return CompletenessInvalidRequest()
    return application.service.assess(
        actor=application.actor,
        request=request,
        current_user=application.current_user,
    )
