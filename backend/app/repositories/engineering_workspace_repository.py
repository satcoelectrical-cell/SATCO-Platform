from sqlalchemy import asc
from sqlalchemy import desc
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload
from uuid import UUID

from app.enums import Discipline, WorkspaceStatus
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.engineering_workspace import EngineeringWorkspaceMember
from app.models.project import Project
from app.models.user import User
from app.models.organization import Organization, UserOrganizationMembership


class EngineeringWorkspaceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_project(
        self, project_id: int, organization_id: UUID
    ) -> Project | None:
        return self.db.query(Project).filter(
            Project.id == project_id,
            Project.organization_id == organization_id,
        ).first()

    def get_selected_organization_id(self, user_id: int) -> UUID | None:
        rows = self.db.query(UserOrganizationMembership.organization_id).join(
            Organization,
            Organization.id == UserOrganizationMembership.organization_id,
        ).filter(
            UserOrganizationMembership.user_id == user_id,
            UserOrganizationMembership.is_enabled.is_(True),
            UserOrganizationMembership.is_selected.is_(True),
            Organization.is_active.is_(True),
        ).limit(2).all()
        return rows[0][0] if len(rows) == 1 else None

    def get_user(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_id(
        self,
        workspace_id: int,
        organization_id: UUID,
    ) -> EngineeringWorkspace | None:
        return (
            self._base_query(organization_id)
            .filter(EngineeringWorkspace.id == workspace_id)
            .first()
        )

    def get_visible_by_id(
        self,
        workspace_id: int,
        current_user: User,
        organization_id: UUID,
    ) -> EngineeringWorkspace | None:
        query = self._base_query(organization_id).filter(
            EngineeringWorkspace.id == workspace_id
        )
        if current_user.role != "admin":
            query = self._apply_visibility(query, current_user.id)
        return query.first()

    def get_by_project_discipline(
        self,
        project_id: int,
        discipline: Discipline,
        organization_id: UUID,
    ) -> EngineeringWorkspace | None:
        return (
            self._base_query(organization_id)
            .filter(
                EngineeringWorkspace.project_id == project_id,
                EngineeringWorkspace.discipline == discipline.value,
            )
            .first()
        )

    def list_for_project(
        self,
        *,
        project_id: int,
        current_user: User,
        organization_id: UUID,
        page: int,
        size: int,
        discipline: Discipline | None,
        status: WorkspaceStatus | None,
        owner_id: int | None,
        primary_assignee_id: int | None,
        include_archived: bool,
        sort_by: str,
        order: str,
    ) -> tuple[list[EngineeringWorkspace], int]:
        query = self._base_query(organization_id).filter(
            EngineeringWorkspace.project_id == project_id
        )
        if current_user.role != "admin":
            query = self._apply_visibility(query, current_user.id)
        if discipline is not None:
            query = query.filter(
                EngineeringWorkspace.discipline == discipline.value
            )
        if status is not None:
            query = query.filter(
                EngineeringWorkspace.status == status.value
            )
        if owner_id is not None:
            query = query.filter(
                EngineeringWorkspace.owner_id == owner_id
            )
        if primary_assignee_id is not None:
            query = query.filter(
                EngineeringWorkspace.primary_assignee_id
                == primary_assignee_id
            )
        if not include_archived:
            query = query.filter(
                EngineeringWorkspace.status
                != WorkspaceStatus.ARCHIVED.value
            )

        total = query.count()
        sort_column = {
            "discipline": EngineeringWorkspace.discipline,
            "status": EngineeringWorkspace.status,
            "created_at": EngineeringWorkspace.created_at,
            "updated_at": EngineeringWorkspace.updated_at,
        }[sort_by]
        direction = asc if order == "asc" else desc
        items = (
            query.order_by(
                direction(sort_column),
                direction(EngineeringWorkspace.id),
            )
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        return items, total

    def create(
        self,
        *,
        project_id: int,
        discipline: Discipline,
        description: str | None,
        owner_id: int,
        primary_assignee_id: int | None,
        created_by_id: int,
    ) -> EngineeringWorkspace:
        workspace = EngineeringWorkspace(
            project_id=project_id,
            discipline=discipline.value,
            description=description,
            status=WorkspaceStatus.DRAFT.value,
            owner_id=owner_id,
            primary_assignee_id=primary_assignee_id,
            created_by_id=created_by_id,
            version=1,
        )
        self.db.add(workspace)
        self.db.flush()
        return workspace

    def update_versioned(
        self,
        workspace_id: int,
        expected_version: int,
        values: dict,
        organization_id: UUID,
    ) -> bool:
        updated = (
            self.db.query(EngineeringWorkspace)
            .filter(
                EngineeringWorkspace.id == workspace_id,
                EngineeringWorkspace.version == expected_version,
                EngineeringWorkspace.project_id.in_(
                    select(Project.id).where(
                        Project.organization_id == organization_id
                    )
                ),
            )
            .update(
                {
                    **values,
                    EngineeringWorkspace.version: expected_version + 1,
                },
                synchronize_session=False,
            )
        )
        self.db.flush()
        return updated == 1

    def add_member(
        self,
        *,
        workspace_id: int,
        user_id: int,
        added_by_id: int,
    ) -> None:
        self.db.add(
            EngineeringWorkspaceMember(
                workspace_id=workspace_id,
                user_id=user_id,
                added_by_id=added_by_id,
            )
        )
        self.db.flush()

    def get_member(
        self,
        workspace_id: int,
        user_id: int,
    ) -> EngineeringWorkspaceMember | None:
        return self.db.get(
            EngineeringWorkspaceMember,
            (workspace_id, user_id),
        )

    def remove_member(
        self,
        member: EngineeringWorkspaceMember,
    ) -> None:
        self.db.delete(member)
        self.db.flush()

    def project_has_workspace_history(self, project_id: int) -> bool:
        return (
            self.db.query(EngineeringWorkspace.id)
            .filter(EngineeringWorkspace.project_id == project_id)
            .first()
            is not None
        )

    def user_has_project_workspace_access(
        self,
        project_id: int,
        user_id: int,
        organization_id: UUID,
    ) -> bool:
        query = self.db.query(EngineeringWorkspace.id).filter(
            EngineeringWorkspace.project_id == project_id
        ).join(Project, Project.id == EngineeringWorkspace.project_id).filter(
            Project.organization_id == organization_id
        )
        return self._apply_visibility(query, user_id).first() is not None

    @staticmethod
    def _apply_visibility(query, user_id: int):
        membership_exists = (
            EngineeringWorkspace.memberships.any(
                EngineeringWorkspaceMember.user_id == user_id
            )
        )
        return query.filter(
            or_(
                Project.owner_id == user_id,
                Project.primary_assignee_id == user_id,
                EngineeringWorkspace.owner_id == user_id,
                EngineeringWorkspace.primary_assignee_id == user_id,
                membership_exists,
            )
        )

    def _base_query(self, organization_id: UUID):
        return (
            self.db.query(EngineeringWorkspace)
            .join(Project, Project.id == EngineeringWorkspace.project_id)
            .options(
                joinedload(EngineeringWorkspace.project),
                joinedload(EngineeringWorkspace.owner),
                joinedload(EngineeringWorkspace.primary_assignee),
                selectinload(EngineeringWorkspace.memberships).joinedload(
                    EngineeringWorkspaceMember.user
                ),
            )
            .filter(Project.organization_id == organization_id)
        )
