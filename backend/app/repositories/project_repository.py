from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import and_, asc, desc, exists, or_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, joinedload

from app.enums import ProjectPriority, ProjectStatus
from app.models.project import Project, ProjectCodeSequence
from app.models.engineering_workspace import (
    EngineeringWorkspace,
    EngineeringWorkspaceMember,
)
from app.models.organization import Organization, UserOrganizationMembership
from app.models.user import User
from app.schemas.project import (
    ProjectAuthorizedSelectionItem,
    ProjectAuthorizedSelectionPage,
    ProjectCreate,
)


class ProjectRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(
        self,
        *,
        organization_id: UUID,
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
        query = self._base_query(organization_id)

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

    def get_by_id(self, project_id: int, *, organization_id: UUID):
        return (
            self._base_query(organization_id)
            .filter(Project.id == project_id)
            .first()
        )

    def get_by_code(self, project_code: str, *, organization_id: UUID):
        return (
            self._base_query(organization_id)
            .filter(Project.project_code == project_code)
            .first()
        )

    def selection_actor_is_active(
        self, *, actor_id: int, organization_id: UUID
    ) -> bool:
        """Check trusted actor prerequisites for protected Project selection."""

        return (
            self.db.query(User.id)
            .join(
                UserOrganizationMembership,
                and_(
                    UserOrganizationMembership.user_id == User.id,
                    UserOrganizationMembership.organization_id == organization_id,
                ),
            )
            .join(Organization, Organization.id == organization_id)
            .filter(
                User.id == actor_id,
                User.is_active.is_(True),
                User.role.in_(("admin", "engineer")),
                UserOrganizationMembership.is_enabled.is_(True),
                Organization.is_active.is_(True),
            )
            .first()
            is not None
        )

    def list_authorized_selection(
        self,
        *,
        actor_id: int,
        organization_id: UUID,
        page: int,
        size: int,
    ) -> ProjectAuthorizedSelectionPage:
        """Return a bounded deterministic page using existing access predicates."""

        user = self.db.get(User, actor_id)
        query = self.db.query(Project.id, Project.name).filter(
            Project.organization_id == organization_id
        )
        if user is None or user.role != "admin":
            workspace_access = exists().where(
                and_(
                    EngineeringWorkspace.project_id == Project.id,
                    or_(
                        EngineeringWorkspace.owner_id == actor_id,
                        EngineeringWorkspace.primary_assignee_id == actor_id,
                        exists().where(
                            and_(
                                EngineeringWorkspaceMember.workspace_id
                                == EngineeringWorkspace.id,
                                EngineeringWorkspaceMember.user_id == actor_id,
                            )
                        ),
                    ),
                )
            )
            query = query.filter(
                or_(
                    Project.owner_id == actor_id,
                    Project.primary_assignee_id == actor_id,
                    workspace_access,
                )
            )
        rows = (
            query.order_by(Project.name.asc(), Project.id.asc())
            .offset((page - 1) * size)
            .limit(size + 1)
            .all()
        )
        has_more = len(rows) > size
        items = tuple(
            ProjectAuthorizedSelectionItem(
                project_id=row.id, display_name=row.name
            )
            for row in rows[:size]
        )
        return ProjectAuthorizedSelectionPage(
            items=items,
            page=page,
            size=size,
            returned_count=len(items),
            has_more=has_more,
        )

    def get_user_by_id(self, user_id: int):
        return self.db.get(User, user_id)

    def create(
        self,
        project: ProjectCreate,
        *,
        organization_id: UUID,
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
            organization_id=organization_id,
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
            return self.get_by_id(
                db_project.id,
                organization_id=organization_id,
            )
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

        return self.get_by_id(
            db_project.id,
            organization_id=db_project.organization_id,
        )

    def delete(self, db_project: Project):
        self.db.delete(db_project)
        self.db.commit()

    def has_workspace_history(
        self,
        project_id: int,
        *,
        organization_id: UUID,
    ) -> bool:
        return (
            self.db.query(EngineeringWorkspace.id)
            .join(Project, Project.id == EngineeringWorkspace.project_id)
            .filter(
                EngineeringWorkspace.project_id == project_id,
                Project.organization_id == organization_id,
            )
            .first()
            is not None
        )

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

    def _base_query(self, organization_id: UUID):
        return (
            self.db.query(Project)
            .options(
                joinedload(Project.customer),
                joinedload(Project.owner),
                joinedload(Project.primary_assignee),
            )
            .filter(Project.organization_id == organization_id)
        )
