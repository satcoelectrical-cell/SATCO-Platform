"""Thin authenticated PATCH-049 Project Completeness transport."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
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


def _observation_request(project_id: str, workspace_id: str | None):
    try:
        return CompletenessAssessmentRequest(
            project_id=int(project_id),
            workspace_id=None if workspace_id is None else int(workspace_id),
        )
    except (TypeError, ValueError, ValidationError):
        raise HTTPException(422, "invalid_scope") from None


@router.post("/projects/{project_id}/completeness/observations")
def record_project_completeness_observation(
    project_id: str, workspace_id: str | None = None,
    application: ProjectCompletenessApplication = Depends(get_project_completeness_application),
):
    result = application.service.record_authorized_observation(
        actor=application.actor,
        request=_observation_request(project_id, workspace_id),
        current_user=application.current_user,
    )
    if result["outcome"] == "protected_not_found":
        raise HTTPException(404, "not_found")
    if result["outcome"] != "success":
        raise HTTPException(503, "observation_unavailable")
    return result


@router.get("/projects/{project_id}/completeness/observations")
def list_project_completeness_observations(
    project_id: str, workspace_id: str | None = None,
    window_days: int = Query(30),
    application: ProjectCompletenessApplication = Depends(get_project_completeness_application),
):
    result = application.service.list_authorized_observation_history(
        actor=application.actor,
        request=_observation_request(project_id, workspace_id),
        current_user=application.current_user,
        window_days=window_days,
    )
    if result["outcome"] == "protected_not_found":
        raise HTTPException(404, "not_found")
    if result["outcome"] == "invalid_request":
        raise HTTPException(422, "unsupported_window")
    if result["outcome"] != "success":
        raise HTTPException(503, "observation_unavailable")
    return result
