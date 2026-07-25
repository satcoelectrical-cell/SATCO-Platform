from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import schemas

from app.core.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User

from app.services.project_service import (
    create_project,
    get_projects,
    update_project,
    delete_project,
)


router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)



@router.post(
    "/",
    response_model=schemas.ProjectResponse,
)
def create_project_api(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_project(
        db,
        project,
    )



@router.get(
    "/",
    response_model=schemas.PaginatedResponse[
        schemas.ProjectResponse
    ],
)
def get_projects_api(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    customer_id: int | None = Query(None),
    status: str | None = Query(None),
    sort_by: str = Query("created_at"),
    order: str = Query("desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    items, total = get_projects(
    db,
    page,
    size,
    customer_id,
    status,
    sort_by,
    order,
)


    return schemas.PaginatedResponse[
        schemas.ProjectResponse
    ](
        items=items,
        total=total,
        page=page,
        size=size,
    )



@router.put(
    "/{project_id}",
    response_model=schemas.ProjectResponse,
)
def update_project_api(
    project_id: int,
    project: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return update_project(
        db,
        project_id,
        project,
    )



@router.delete(
    "/{project_id}",
)
def delete_project_api(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):

    delete_project(
        db,
        project_id,
        current_user.id,
    )

    return {
        "message": "Project deleted successfully",
        "project_id": project_id,
    }