from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


def get_projects(
    db: Session,
    page: int = 1,
    size: int = 20,
):
    query = db.query(Project)

    total = query.count()

    items = (
        query
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return items, total


def get_project(db: Session, project_id: int):
    return (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )


def create_project(db: Session, project: ProjectCreate):
    db_project = Project(
        name=project.name,
        customer_id=project.customer_id
    )

    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return db_project


def update_project(
    db: Session,
    project_id: int,
    project_data: ProjectUpdate
):
    db_project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if not db_project:
        return None

    if project_data.name is not None:
        db_project.name = project_data.name

    if project_data.customer_id is not None:
        db_project.customer_id = project_data.customer_id

    if project_data.status is not None:
        db_project.status = project_data.status

    db.commit()
    db.refresh(db_project)

    return db_project


def delete_project(db: Session, project_id: int):
    db_project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if not db_project:
        return None

    db.delete(db_project)
    db.commit()

    return db_project