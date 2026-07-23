from sqlalchemy.orm import Session

from app.repositories import project_repository
from app.schemas.project import ProjectCreate


def get_projects(db: Session):
    return project_repository.get_projects(db)


def get_project(db: Session, project_id: int):
    return project_repository.get_project(db, project_id)


def create_project(db: Session, project: ProjectCreate):
    return project_repository.create_project(db, project)