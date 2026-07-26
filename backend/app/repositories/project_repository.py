from datetime import date, datetime, timezone

from sqlalchemy import asc, desc
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, joinedload

from app.enums import ProjectPriority, ProjectStatus
from app.models.project import Project, ProjectCodeSequence
from app.models.user import User
from app.schemas.project import ProjectCreate


class ProjectRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(
        self,
        page: int = 1,
        size: int = 20,
        customer_id: int | None = None,
        status: ProjectStatus | None = None,
        priority: ProjectPriority | None = None,
        owner_id: int | None = None,
        primary_assignee_id: int | None = None,
        project_code: str | None = None,
        start_date_from: date | None = None,
        start_date_to: date | None = None,
        target_date_from: date | None = None,
        target_date_to: date | None = None,
        sort_by: str = "created_at",
        order: str = "desc",
    ):
        query = self._base_query()

        if customer_id is not None:
            query = query.filter(
                Project.customer_id == customer_id
            )
        if status is not None:
            query = query.filter(
                Project.status == status.value
            )
        if priority is not None:
            query = query.filter(
                Project.priority == priority.value
            )
        if owner_id is not None:
            query = query.filter(
                Project.owner_id == owner_id
            )
        if primary_assignee_id is not None:
            query = query.filter(
                Project.primary_assignee_id
                == primary_assignee_id
            )
        if project_code:
            query = query.filter(
                Project.project_code.ilike(
                    f"%{project_code.strip()}%"
                )
            )
        if start_date_from is not None:
            query = query.filter(
                Project.start_date >= start_date_from
            )
        if start_date_to is not None:
            query = query.filter(
                Project.start_date <= start_date_to
            )
        if target_date_from is not None:
            query = query.filter(
                Project.target_completion_date
                >= target_date_from
            )
        if target_date_to is not None:
            query = query.filter(
                Project.target_completion_date
                <= target_date_to
            )

        total = query.count()
        sort_column = {
            "name": Project.name,
            "project_code": Project.project_code,
            "created_at": Project.created_at,
            "updated_at": Project.updated_at,
            "status": Project.status,
            "priority": Project.priority,
            "progress": Project.progress,
            "start_date": Project.start_date,
            "target_completion_date": (
                Project.target_completion_date
            ),
        }[sort_by]
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
            self._base_query()
            .filter(Project.id == project_id)
            .first()
        )

    def get_by_code(self, project_code: str):
        return (
            self._base_query()
            .filter(Project.project_code == project_code)
            .first()
        )

    def get_user_by_id(self, user_id: int):
        return self.db.get(User, user_id)

    def create(
        self,
        project: ProjectCreate,
        *,
        owner_id: int,
        creation_time: datetime | None = None,
    ):
        creation_time = creation_time or datetime.now(timezone.utc)
        project_code = self.allocate_project_code(
            creation_time.year
        )
        data = project.model_dump(
            exclude={"owner_id"},
        )
        data["priority"] = project.priority.value

        db_project = Project(
            **data,
            project_code=project_code,
            owner_id=owner_id,
            status=ProjectStatus.NEW.value,
            progress=0,
            created_at=creation_time,
        )

        try:
            self.db.add(db_project)
            self.db.commit()
            self.db.refresh(db_project)
            return self.get_by_id(db_project.id)
        except Exception:
            self.db.rollback()
            raise

    def update(
        self,
        db_project: Project,
        update_data: dict,
    ):
        for key, value in update_data.items():
            if isinstance(value, (ProjectStatus, ProjectPriority)):
                value = value.value
            setattr(db_project, key, value)

        self.db.commit()
        self.db.refresh(db_project)

        return self.get_by_id(db_project.id)

    def delete(self, db_project: Project):
        self.db.delete(db_project)
        self.db.commit()

    def allocate_project_code(self, year: int) -> str:
        statement = (
            insert(ProjectCodeSequence)
            .values(
                year=year,
                last_value=1,
            )
            .on_conflict_do_update(
                index_elements=[
                    ProjectCodeSequence.year
                ],
                set_={
                    "last_value": (
                        ProjectCodeSequence.last_value + 1
                    )
                },
            )
            .returning(
                ProjectCodeSequence.last_value
            )
        )
        sequence_value = self.db.execute(
            statement
        ).scalar_one()
        return (
            f"SAT-PRJ-{year}-"
            f"{sequence_value:04d}"
        )

    def _base_query(self):
        return (
            self.db.query(Project)
            .options(
                joinedload(Project.customer),
                joinedload(Project.owner),
                joinedload(Project.primary_assignee),
            )
        )
