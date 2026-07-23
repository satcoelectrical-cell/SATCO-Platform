from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ....core.database import SessionLocal
from .... import schemas
from ....services.project_service import create_project, get_projects


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