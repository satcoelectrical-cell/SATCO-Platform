from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self, page: int = 1, size: int = 20):
        query = self.db.query(Project)

        total = query.count()

        items = (
            query
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
            setattr(db_project, key, value)

        self.db.commit()
        self.db.refresh(db_project)

        return db_project

    def delete(self, db_project: Project):
        self.db.delete(db_project)
        self.db.commit()
