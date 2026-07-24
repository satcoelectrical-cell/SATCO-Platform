from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import schemas
from app.core.database import SessionLocal
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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/",
    response_model=schemas.ProjectResponse,
)
def create_project_api(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db),
):
    return create_project(db, project)


@router.get(
    "/",
    response_model=schemas.PaginatedResponse[
        schemas.ProjectResponse
    ],
)
def get_projects_api(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = get_projects(
        db,
        page,
        size,
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
):
    return update_project(
        db,
        project_id,
        project,
    )


@router.delete(
    "/{project_id}",
    response_model=schemas.ProjectResponse,
)
def delete_project_api(
    project_id: int,
    db: Session = Depends(get_db),
):
    return delete_project(
        db,
        project_id,
    )