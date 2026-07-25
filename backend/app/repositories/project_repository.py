from sqlalchemy.orm import Session
from sqlalchemy import asc, desc

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


def get_projects(
    db: Session,
    page: int = 1,
    size: int = 20,
    customer_id: int | None = None,
    status: str | None = None,
    sort_by: str = "created_at",
    order: str = "desc",
):

    query = db.query(Project)


    if customer_id:
        query = query.filter(
            Project.customer_id == customer_id
        )


    if status:
        query = query.filter(
            Project.status == status
        )


    allowed_sort_fields = {
        "name": Project.name,
        "created_at": Project.created_at,
        "status": Project.status,
    }


    sort_column = allowed_sort_fields.get(
        sort_by,
        Project.created_at
    )


    if order == "asc":
        query = query.order_by(
            asc(sort_column)
        )
    else:
        query = query.order_by(
            desc(sort_column)
        )


    total = query.count()


    items = (
        query
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )


    return items, total



def get_project(
    db: Session,
    project_id: int
):
    return (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )



def create_project(
    db: Session,
    project: ProjectCreate
):

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



def delete_project(
    db: Session,
    project_id: int
):

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