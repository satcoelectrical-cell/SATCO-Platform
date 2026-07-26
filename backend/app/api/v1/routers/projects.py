from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import schemas

from app.core.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User
from app.permissions.roles import Role
from app.services.project_service import ProjectService


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
    service = ProjectService(db)

    try:
        return service.create(
            project,
            current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc



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

    service = ProjectService(db)

    items, total = service.get_all(
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

    service = ProjectService(db)

    try:
        result = service.update(
            project_id,
            project,
            current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return result



@router.delete(
    "/{project_id}",
)
def delete_project_api(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(Role.ADMIN)
    ),
):
    service = ProjectService(db)

    deleted = service.delete(
        project_id,
        current_user.id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return {
        "message": "Project deleted successfully",
        "project_id": project_id,
    }
