from sqlalchemy.orm import Session

from app.repositories import project_repository
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.audit_service import create_audit_log


def get_projects(
    db: Session,
    page: int = 1,
    size: int = 20,
    customer_id: int | None = None,
    status: str | None = None,
    sort_by: str = "created_at",
    order: str = "desc",
):

    return project_repository.get_projects(
        db,
        page,
        size,
        customer_id,
        status,
        sort_by,
        order,
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
    user_id: int,
):

    project = project_repository.get_project(
        db,
        project_id,
    )

    result = project_repository.delete_project(
        db,
        project_id,
    )

    create_audit_log(
        db=db,
        user_id=user_id,
        action="DELETE",
        entity="PROJECT",
        entity_id=project_id,
        details={
            "project_name": project.name
        },
    )

    return result
