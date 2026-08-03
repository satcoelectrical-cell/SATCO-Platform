from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import schemas
from app.core.database import get_db
from app.dependencies.auth import (
    AuthenticatedOrganizationContext,
    get_current_user_organization_context,
)
from app.enums import ProjectPriority, ProjectStatus
from app.models.user import User
from app.schemas.project import ProjectSortField, SortOrder
from app.services.project_service import ProjectService


router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)

PROJECT_EXAMPLE = {
    "id": 42,
    "project_code": "SAT-PRJ-2026-0001",
    "name": "PLC Modernization",
    "description": "Replace the legacy control system.",
    "customer": {
        "id": 12,
        "name": "Example Customer",
    },
    "status": "in_progress",
    "priority": "high",
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
    "start_date": "2026-08-01",
    "target_completion_date": "2026-11-30",
    "completed_at": None,
    "progress": 35,
    "created_at": "2026-07-26T06:00:00Z",
    "updated_at": "2026-08-15T10:30:00Z",
}

UNAUTHORIZED_RESPONSE = {
    "description": "Authentication required",
    "content": {
        "application/json": {
            "example": {"detail": "Not authenticated"}
        }
    },
}
FORBIDDEN_RESPONSE = {
    "description": "Permission denied",
    "content": {
        "application/json": {
            "example": {
                "success": False,
                "error": {
                    "code": "PROJECT_FORBIDDEN",
                    "message": "Project operation forbidden",
                },
            }
        }
    },
}
NOT_FOUND_RESPONSE = {
    "description": "Project or relationship not found",
    "content": {
        "application/json": {
            "example": {
                "success": False,
                "error": {
                    "code": "PROJECT_NOT_FOUND",
                    "message": "Project 42 not found",
                },
            }
        }
    },
}
VALIDATION_RESPONSE = {
    "description": "Request or business-rule validation failed",
    "content": {
        "application/json": {
            "example": {
                "detail": [
                    {
                        "loc": ["body", "progress"],
                        "msg": "Input should be less than or equal to 100",
                        "type": "less_than_equal",
                    }
                ]
            }
        }
    },
}


@router.post(
    "/",
    response_model=schemas.ProjectResponse,
    responses={
        200: {
            "description": "Project created",
            "content": {
                "application/json": {
                    "example": PROJECT_EXAMPLE
                }
            },
        },
        401: UNAUTHORIZED_RESPONSE,
        403: FORBIDDEN_RESPONSE,
        404: NOT_FOUND_RESPONSE,
        422: VALIDATION_RESPONSE,
    },
)
def create_project_api(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    context: AuthenticatedOrganizationContext = Depends(
        get_current_user_organization_context
    ),
):
    return ProjectService(db).create(
        project,
        context.user,
        context.organization_id,
    )


@router.get(
    "/",
    response_model=schemas.PaginatedResponse[
        schemas.ProjectResponse
    ],
    responses={
        200: {
            "description": "Paginated Project list",
            "content": {
                "application/json": {
                    "example": {
                        "items": [PROJECT_EXAMPLE],
                        "total": 1,
                        "page": 1,
                        "size": 20,
                    }
                }
            },
        },
        401: UNAUTHORIZED_RESPONSE,
        422: VALIDATION_RESPONSE,
    },
)
def get_projects_api(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    customer_id: int | None = Query(None),
    status: ProjectStatus | None = Query(None),
    priority: ProjectPriority | None = Query(None),
    owner_id: int | None = Query(None),
    primary_assignee_id: int | None = Query(None),
    project_code: str | None = Query(None, min_length=1),
    start_date_from: date | None = Query(None),
    start_date_to: date | None = Query(None),
    target_date_from: date | None = Query(None),
    target_date_to: date | None = Query(None),
    sort_by: ProjectSortField = Query("created_at"),
    order: SortOrder = Query("desc"),
    db: Session = Depends(get_db),
    context: AuthenticatedOrganizationContext = Depends(
        get_current_user_organization_context
    ),
):
    items, total = ProjectService(db).get_all(
        organization_id=context.organization_id,
        page=page,
        size=size,
        customer_id=customer_id,
        status=status,
        priority=priority,
        owner_id=owner_id,
        primary_assignee_id=primary_assignee_id,
        project_code=project_code,
        start_date_from=start_date_from,
        start_date_to=start_date_to,
        target_date_from=target_date_from,
        target_date_to=target_date_to,
        sort_by=sort_by,
        order=order,
    )
    return schemas.PaginatedResponse[
        schemas.ProjectResponse
    ](
        items=items,
        total=total,
        page=page,
        size=size,
    )


@router.get(
    "/{project_id}",
    response_model=schemas.ProjectResponse,
    responses={
        200: {
            "description": "Project detail",
            "content": {
                "application/json": {
                    "example": PROJECT_EXAMPLE
                }
            },
        },
        401: UNAUTHORIZED_RESPONSE,
        404: NOT_FOUND_RESPONSE,
        422: VALIDATION_RESPONSE,
    },
)
def get_project_api(
    project_id: int,
    db: Session = Depends(get_db),
    context: AuthenticatedOrganizationContext = Depends(
        get_current_user_organization_context
    ),
):
    return ProjectService(db).get_by_id(
        project_id,
        organization_id=context.organization_id,
    )


@router.put(
    "/{project_id}",
    response_model=schemas.ProjectResponse,
    responses={
        200: {
            "description": "Project updated",
            "content": {
                "application/json": {
                    "example": PROJECT_EXAMPLE
                }
            },
        },
        400: VALIDATION_RESPONSE,
        401: UNAUTHORIZED_RESPONSE,
        403: FORBIDDEN_RESPONSE,
        404: NOT_FOUND_RESPONSE,
        422: VALIDATION_RESPONSE,
    },
)
def update_project_api(
    project_id: int,
    project: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
    context: AuthenticatedOrganizationContext = Depends(
        get_current_user_organization_context
    ),
):
    return ProjectService(db).update(
        project_id,
        project,
        context.user,
        context.organization_id,
    )


@router.delete(
    "/{project_id}",
    responses={
        200: {
            "description": "Project deleted",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Project deleted successfully",
                        "project_id": 42,
                        "project_code": "SAT-PRJ-2026-0001",
                    }
                }
            },
        },
        401: UNAUTHORIZED_RESPONSE,
        403: FORBIDDEN_RESPONSE,
        404: NOT_FOUND_RESPONSE,
    },
)
def delete_project_api(
    project_id: int,
    db: Session = Depends(get_db),
    context: AuthenticatedOrganizationContext = Depends(
        get_current_user_organization_context
    ),
):
    deleted = ProjectService(db).delete(
        project_id,
        context.user,
        context.organization_id,
    )
    return {
        "message": "Project deleted successfully",
        **deleted,
    }
