from sqlalchemy.orm import Session

from app.repositories import project_repository
from app.schemas.project import ProjectCreate, ProjectUpdate


def get_projects(
    db: Session,
    page: int = 1,
    size: int = 20,
):
    return project_repository.get_projects(
        db,
        page,
        size,
    )


def get_project(
    db: Session,
    project_id: int,
):
    return project_repository.get_project(
        db,
        project_id,
    )


def create_project(
    db: Session,
    project: ProjectCreate,
):
    return project_repository.create_project(
        db,
        project,
    )


def update_project(
    db: Session,
    project_id: int,
    project_data: ProjectUpdate,
):
    return project_repository.update_project(
        db,
        project_id,
        project_data,
    )


def delete_project(
    db: Session,
    project_id: int,
):
    return project_repository.delete_project(
        db,
        project_id,
    )