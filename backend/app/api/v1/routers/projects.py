from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ....core.database import SessionLocal
from .... import schemas
from ....services.project_service import (
    create_project,
    get_projects,
    update_project,
    delete_project
)


router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=schemas.ProjectResponse)
def create_project_api(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db)
):
    return create_project(db, project)


@router.get("/", response_model=list[schemas.ProjectResponse])
def get_projects_api(
    db: Session = Depends(get_db)
):
    return get_projects(db)


@router.put("/{project_id}", response_model=schemas.ProjectResponse)
def update_project_api(
    project_id: int,
    project: schemas.ProjectUpdate,
    db: Session = Depends(get_db)
):
    result = update_project(db, project_id, project)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    return result


@router.delete("/{project_id}", response_model=schemas.ProjectResponse)
def delete_project_api(
    project_id: int,
    db: Session = Depends(get_db)
):
    result = delete_project(db, project_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    return result