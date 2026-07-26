from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.enums import ProjectStatus
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(
        self,
        page: int = 1,
        size: int = 20,
        customer_id: int | None = None,
        status: str | None = None,
        sort_by: str = "created_at",
        order: str = "desc",
    ):
        query = self.db.query(Project)

        if customer_id is not None:
            query = query.filter(
                Project.customer_id == customer_id
            )

        if status is not None:
            query = query.filter(
                Project.status == status
            )

        total = query.count()

        sort_columns = {
            "name": Project.name,
            "created_at": Project.created_at,
            "status": Project.status,
        }
        sort_column = sort_columns.get(
            sort_by,
            Project.created_at,
        )
        sort_direction = asc if order == "asc" else desc

        items = (
            query
            .order_by(
                sort_direction(sort_column),
                sort_direction(Project.id),
            )
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

        return items, total

    def get_by_id(self, project_id: int):
        return (
            self.db.query(Project)
            .filter(Project.id == project_id)
            .first()
        )

    def create(self, project: ProjectCreate):
        obj = Project(**project.model_dump())

        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)

        return obj

    def update(
        self,
        db_project: Project,
        project: ProjectUpdate,
    ):
        update_data = project.model_dump(
            exclude_unset=True
        )

        for key, value in update_data.items():
            if isinstance(value, ProjectStatus):
                value = value.value
            setattr(db_project, key, value)

        self.db.commit()
        self.db.refresh(db_project)

        return db_project

    def delete(self, db_project: Project):
        self.db.delete(db_project)
        self.db.commit()
