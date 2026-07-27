from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app import schemas
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.enums import Discipline, WorkspaceStatus
from app.models.user import User
from app.schemas.engineering_workspace import (
    WorkspaceSortField,
    WorkspaceSortOrder,
)
from app.services.engineering_workspace_service import (
    EngineeringWorkspaceService,
)


router = APIRouter(tags=["Engineering Workspaces"])

WORKSPACE_EXAMPLE = {
    "id": 17,
    "project_id": 42,
    "project_code": "SAT-PRJ-2026-0001",
    "project_name": "PLC Modernization",
    "discipline": "electrical",
    "display_name": "Electrical Engineering Workspace",
    "description": "Electrical discipline workspace.",
    "status": "active",
    "owner": {
        "id": 3,
        "username": "owner",
        "full_name": "Project Owner",
    },
    "primary_assignee": {
        "id": 8,
        "username": "engineer",
        "full_name": "Primary Engineer",
    },
    "collaborators": [
        {
            "id": 11,
            "username": "reviewer",
            "full_name": "Discipline Reviewer",
        }
    ],
    "collaborator_count": 1,
    "version": 3,
    "archived_at": None,
    "created_at": "2026-07-26T10:00:00Z",
    "updated_at": "2026-07-26T11:30:00Z",
    "allowed_actions": [
        "view",
        "update_description",
        "assign_primary_assignee",
        "manage_collaborators",
        "change_status",
        "archive",
    ],
}
DRAFT_WORKSPACE_EXAMPLE = {
    **WORKSPACE_EXAMPLE,
    "status": "draft",
    "version": 1,
}
UNAUTHENTICATED = {
    "description": "Authentication required",
    "content": {
        "application/json": {
            "example": {"detail": "Not authenticated"}
        }
    },
}
FORBIDDEN = {
    "description": "Workspace capability denied",
    "content": {
        "application/json": {
            "example": {
                "success": False,
                "error": {
                    "code": "WORKSPACE_FORBIDDEN",
                    "message": (
                        "Engineering Workspace operation forbidden"
                    ),
                },
            }
        }
    },
}
NOT_FOUND = {
    "description": "Workspace or Project not found or not visible",
    "content": {
        "application/json": {
            "example": {
                "success": False,
                "error": {
                    "code": "WORKSPACE_NOT_FOUND",
                    "message": (
                        "Engineering Workspace 17 not found"
                    ),
                },
            }
        }
    },
}
CONFLICT = {
    "description": "Uniqueness, lifecycle, or version conflict",
    "content": {
        "application/json": {
            "example": {
                "success": False,
                "error": {
                    "code": "WORKSPACE_VERSION_CONFLICT",
                    "message": (
                        "Engineering Workspace was modified by "
                        "another request"
                    ),
                },
            }
        }
    },
}
VALIDATION = {
    "description": "Request validation failed",
    "content": {
        "application/json": {
            "example": {
                "detail": [
                    {
                        "loc": ["body", "expected_version"],
                        "msg": "Input should be greater than 0",
                        "type": "greater_than",
                    }
                ]
            }
        }
    },
}
STANDARD_RESPONSES = {
    401: UNAUTHENTICATED,
    403: FORBIDDEN,
    404: NOT_FOUND,
    409: CONFLICT,
    422: VALIDATION,
}


@router.post(
    "/projects/{project_id}/workspaces",
    response_model=schemas.EngineeringWorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Draft Engineering Workspace created",
            "content": {
                "application/json": {
                    "example": DRAFT_WORKSPACE_EXAMPLE
                }
            },
        },
        **STANDARD_RESPONSES,
    },
)
def create_workspace(
    project_id: int,
    data: schemas.EngineeringWorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return EngineeringWorkspaceService(db).create(
        project_id,
        data,
        current_user,
    )


@router.get(
    "/projects/{project_id}/workspaces",
    response_model=schemas.EngineeringWorkspaceListResponse,
    responses={
        200: {
            "description": "Visible Project Workspaces",
            "content": {
                "application/json": {
                    "example": {
                        "items": [WORKSPACE_EXAMPLE],
                        "total": 1,
                        "page": 1,
                        "size": 20,
                    }
                }
            },
        },
        **STANDARD_RESPONSES,
    },
)
def list_project_workspaces(
    project_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    discipline: Discipline | None = Query(None),
    workspace_status: WorkspaceStatus | None = Query(
        None,
        alias="status",
    ),
    owner_id: int | None = Query(None, gt=0),
    primary_assignee_id: int | None = Query(None, gt=0),
    include_archived: bool = Query(False),
    sort_by: WorkspaceSortField = Query("created_at"),
    order: WorkspaceSortOrder = Query("desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return EngineeringWorkspaceService(db).list_for_project(
        project_id=project_id,
        current_user=current_user,
        page=page,
        size=size,
        discipline=discipline,
        status=workspace_status,
        owner_id=owner_id,
        primary_assignee_id=primary_assignee_id,
        include_archived=include_archived,
        sort_by=sort_by,
        order=order,
    )


@router.get(
    "/workspaces/{workspace_id}",
    response_model=schemas.EngineeringWorkspaceResponse,
    responses={
        200: {
            "description": "Visible Engineering Workspace",
            "content": {
                "application/json": {"example": WORKSPACE_EXAMPLE}
            },
        },
        **STANDARD_RESPONSES,
    },
)
def get_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return EngineeringWorkspaceService(db).get(
        workspace_id,
        current_user,
    )


@router.patch(
    "/workspaces/{workspace_id}",
    response_model=schemas.EngineeringWorkspaceResponse,
    responses={
        200: {
            "description": "Workspace metadata updated",
            "content": {
                "application/json": {"example": WORKSPACE_EXAMPLE}
            },
        },
        **STANDARD_RESPONSES,
    },
)
def update_workspace(
    workspace_id: int,
    data: schemas.EngineeringWorkspaceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return EngineeringWorkspaceService(db).update(
        workspace_id,
        data,
        current_user,
    )


@router.post(
    "/workspaces/{workspace_id}/transitions",
    response_model=schemas.EngineeringWorkspaceResponse,
    responses={
        200: {
            "description": "Workspace lifecycle transitioned",
            "content": {
                "application/json": {"example": WORKSPACE_EXAMPLE}
            },
        },
        **STANDARD_RESPONSES,
    },
)
def transition_workspace(
    workspace_id: int,
    data: schemas.WorkspaceStatusTransitionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return EngineeringWorkspaceService(db).transition(
        workspace_id,
        data,
        current_user,
    )


@router.post(
    "/workspaces/{workspace_id}/archive",
    response_model=schemas.EngineeringWorkspaceResponse,
    responses={
        200: {
            "description": "Workspace archived with history retained",
            "content": {
                "application/json": {
                    "example": {
                        **WORKSPACE_EXAMPLE,
                        "status": "archived",
                        "version": 4,
                        "archived_at": "2026-07-26T12:00:00Z",
                        "allowed_actions": ["view", "restore"],
                    }
                }
            },
        },
        **STANDARD_RESPONSES,
    },
)
def archive_workspace(
    workspace_id: int,
    data: schemas.WorkspaceArchiveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return EngineeringWorkspaceService(db).archive(
        workspace_id,
        data,
        current_user,
    )


@router.post(
    "/workspaces/{workspace_id}/restore",
    response_model=schemas.EngineeringWorkspaceResponse,
    responses={
        200: {
            "description": "Archived Workspace identity restored",
            "content": {
                "application/json": {"example": WORKSPACE_EXAMPLE}
            },
        },
        **STANDARD_RESPONSES,
    },
)
def restore_workspace(
    workspace_id: int,
    data: schemas.WorkspaceRestoreRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return EngineeringWorkspaceService(db).restore(
        workspace_id,
        data,
        current_user,
    )


@router.post(
    "/workspaces/{workspace_id}/collaborators",
    response_model=schemas.EngineeringWorkspaceResponse,
    responses={
        200: {
            "description": "Workspace collaborator added",
            "content": {
                "application/json": {"example": WORKSPACE_EXAMPLE}
            },
        },
        **STANDARD_RESPONSES,
    },
)
def add_workspace_collaborator(
    workspace_id: int,
    data: schemas.EngineeringWorkspaceCollaboratorAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return EngineeringWorkspaceService(db).add_collaborator(
        workspace_id,
        data,
        current_user,
    )


@router.delete(
    "/workspaces/{workspace_id}/collaborators/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Workspace collaborator removed"},
        **STANDARD_RESPONSES,
    },
)
def remove_workspace_collaborator(
    workspace_id: int,
    user_id: int,
    expected_version: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    EngineeringWorkspaceService(db).remove_collaborator(
        workspace_id,
        user_id,
        expected_version,
        current_user,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
