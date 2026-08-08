import logging
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.enums import ProjectPriority, ProjectStatus
from app.exceptions.project import (
    ProjectForbiddenException,
    ProjectNotFoundException,
    ProjectRelatedEntityNotFoundException,
    ProjectValidationException,
)
from app.exceptions.engineering_workspace import (
    ProjectHasWorkspaceHistory,
)
from app.models.project import Project
from app.models.user import User
from app.permissions.roles import Role
from app.repositories.customer_repository import CustomerRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import (
    ProjectAuthorizedSelectionPage,
    ProjectCreate,
    ProjectSelectionActor,
    ProjectUpdate,
)
from app.services.audit_service import create_audit_log


logger = logging.getLogger(__name__)


ALLOWED_STATUS_TRANSITIONS = {
    ProjectStatus.NEW: {
        ProjectStatus.IN_PROGRESS,
        ProjectStatus.ON_HOLD,
        ProjectStatus.CANCELLED,
    },
    ProjectStatus.IN_PROGRESS: {
        ProjectStatus.ON_HOLD,
        ProjectStatus.COMPLETED,
        ProjectStatus.CANCELLED,
    },
    ProjectStatus.ON_HOLD: {
        ProjectStatus.IN_PROGRESS,
        ProjectStatus.CANCELLED,
    },
    ProjectStatus.COMPLETED: set(),
    ProjectStatus.CANCELLED: set(),
}


class ProjectService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = ProjectRepository(db)
        self.customer_repository = CustomerRepository(db)

    def get_all(self, *, organization_id: UUID, **filters):
        return self.repository.get_all(
            organization_id=organization_id,
            **filters,
        )

    def get_by_id(self, project_id: int, *, organization_id: UUID):
        project = self.repository.get_by_id(
            project_id,
            organization_id=organization_id,
        )
        if project is None:
            raise ProjectNotFoundException(project_id)
        return project

    def list_authorized_selection(
        self,
        *,
        actor: ProjectSelectionActor,
        page: int,
        size: int,
    ) -> ProjectAuthorizedSelectionPage:
        """Return only Projects visible to an active actor in trusted scope."""

        if not self.repository.selection_actor_is_active(
            actor_id=actor.actor_id,
            organization_id=actor.organization_id,
        ):
            raise ProjectForbiddenException()
        return self.repository.list_authorized_selection(
            actor_id=actor.actor_id,
            organization_id=actor.organization_id,
            page=page,
            size=size,
        )

    def authorize_selection_actor(self, *, actor: ProjectSelectionActor) -> None:
        """Establish active trusted scope before a Project-less shell exists."""

        if not self.repository.selection_actor_is_active(
            actor_id=actor.actor_id,
            organization_id=actor.organization_id,
        ):
            raise ProjectForbiddenException()

    def create(
        self,
        project: ProjectCreate,
        current_user: User,
        organization_id: UUID,
    ):
        self._validate_customer(project.customer_id)
        owner_id = self._resolve_owner_for_create(
            project.owner_id,
            current_user,
        )
        self._validate_internal_user(
            owner_id,
            "owner",
        )
        if project.primary_assignee_id is not None:
            self._validate_internal_user(
                project.primary_assignee_id,
                "primary assignee",
            )
        self._validate_dates(
            project.start_date,
            project.target_completion_date,
        )

        result = self.repository.create(
            project,
            organization_id=organization_id,
            owner_id=owner_id,
        )
        snapshot = self._snapshot(result)

        create_audit_log(
            db=self.db,
            user_id=current_user.id,
            action="CREATE",
            entity="PROJECT",
            entity_id=result.id,
            details=snapshot,
        )
        logger.info(
            "Project created: %s",
            result.project_code,
        )
        return result

    def update(
        self,
        project_id: int,
        project_data: ProjectUpdate,
        current_user: User,
        organization_id: UUID,
    ):
        project = self.get_by_id(
            project_id,
            organization_id=organization_id,
        )
        update_data = project_data.model_dump(
            exclude_unset=True
        )
        if not update_data:
            raise ProjectValidationException(
                "At least one Project field is required"
            )

        self._authorize_update(
            project,
            update_data,
            current_user,
        )
        self._validate_update_relationships(update_data)

        if "customer_id" in update_data:
            self._validate_customer(
                update_data["customer_id"]
            )

        next_status = ProjectStatus(
            update_data.get("status", project.status)
        )
        self._validate_transition(
            ProjectStatus(project.status),
            next_status,
        )

        start_date = update_data.get(
            "start_date",
            project.start_date,
        )
        target_date = update_data.get(
            "target_completion_date",
            project.target_completion_date,
        )
        self._validate_dates(start_date, target_date)

        progress = update_data.get(
            "progress",
            project.progress,
        )
        if next_status == ProjectStatus.COMPLETED:
            update_data["progress"] = 100
            update_data["completed_at"] = datetime.now(
                timezone.utc
            )
        else:
            if progress == 100:
                raise ProjectValidationException(
                    "Only completed Projects may have "
                    "progress 100"
                )
            update_data["completed_at"] = None

        before = self._snapshot(project)
        result = self.repository.update(
            project,
            update_data,
        )
        after = self._snapshot(result)
        changed_fields = [
            key for key in update_data
            if before.get(key) != after.get(key)
        ]

        create_audit_log(
            db=self.db,
            user_id=current_user.id,
            action="UPDATE",
            entity="PROJECT",
            entity_id=result.id,
            details={
                "project_code": result.project_code,
                "changed_fields": changed_fields,
                "before": {
                    key: before.get(key)
                    for key in changed_fields
                },
                "after": {
                    key: after.get(key)
                    for key in changed_fields
                },
            },
        )
        logger.info(
            "Project updated: %s",
            result.project_code,
        )
        return result

    def delete(
        self,
        project_id: int,
        current_user: User,
        organization_id: UUID,
    ) -> dict:
        project = self.get_by_id(
            project_id,
            organization_id=organization_id,
        )
        if current_user.role != Role.ADMIN.value:
            raise ProjectForbiddenException(
                "Only administrators may delete Projects"
            )
        if self.repository.has_workspace_history(
            project_id,
            organization_id=organization_id,
        ):
            raise ProjectHasWorkspaceHistory()
        snapshot = self._snapshot(project)
        project_code = project.project_code

        self.repository.delete(project)
        create_audit_log(
            db=self.db,
            user_id=current_user.id,
            action="DELETE",
            entity="PROJECT",
            entity_id=project_id,
            details=snapshot,
        )
        logger.info(
            "Project deleted: %s",
            project_code,
        )
        return {
            "project_id": project_id,
            "project_code": project_code,
        }

    def _resolve_owner_for_create(
        self,
        requested_owner_id: int | None,
        current_user: User,
    ) -> int:
        if requested_owner_id is None:
            return current_user.id
        if (
            requested_owner_id != current_user.id
            and current_user.role != Role.ADMIN.value
        ):
            raise ProjectForbiddenException(
                "Only administrators may create a "
                "Project for another owner"
            )
        return requested_owner_id

    def _authorize_update(
        self,
        project: Project,
        update_data: dict,
        current_user: User,
    ) -> None:
        is_admin = current_user.role == Role.ADMIN.value
        is_owner = project.owner_id == current_user.id
        is_primary_assignee = (
            project.primary_assignee_id == current_user.id
        )
        is_legacy_unowned = project.owner_id is None

        if not (
            is_admin
            or is_owner
            or is_primary_assignee
            or is_legacy_unowned
        ):
            raise ProjectForbiddenException()

        if "owner_id" in update_data and not is_admin:
            if update_data["owner_id"] != project.owner_id:
                raise ProjectForbiddenException(
                    "Only administrators may transfer "
                    "Project ownership"
                )

        if (
            "primary_assignee_id" in update_data
            and not (is_admin or is_owner)
        ):
            if (
                update_data["primary_assignee_id"]
                != project.primary_assignee_id
            ):
                raise ProjectForbiddenException(
                    "Only Project owners or administrators "
                    "may change the primary assignee"
                )

    def _validate_update_relationships(
        self,
        update_data: dict,
    ) -> None:
        if update_data.get("owner_id") is not None:
            self._validate_internal_user(
                update_data["owner_id"],
                "owner",
            )
        if (
            "primary_assignee_id" in update_data
            and update_data["primary_assignee_id"] is not None
        ):
            self._validate_internal_user(
                update_data["primary_assignee_id"],
                "primary assignee",
            )

    def _validate_customer(self, customer_id: int) -> None:
        customer = self.customer_repository.get_by_id(
            customer_id
        )
        if customer is None:
            raise ProjectRelatedEntityNotFoundException(
                "customer",
                customer_id,
            )

    def _validate_internal_user(
        self,
        user_id: int,
        relationship: str,
    ) -> User:
        user = self.repository.get_user_by_id(user_id)
        if user is None:
            raise ProjectRelatedEntityNotFoundException(
                relationship,
                user_id,
            )
        if (
            not user.is_active
            or user.role
            not in {
                Role.ADMIN.value,
                Role.ENGINEER.value,
            }
        ):
            raise ProjectValidationException(
                f"Project {relationship} must be an active "
                "internal user"
            )
        return user

    @staticmethod
    def _validate_dates(
        start_date: date | None,
        target_date: date | None,
    ) -> None:
        if (
            start_date is not None
            and target_date is not None
            and target_date < start_date
        ):
            raise ProjectValidationException(
                "Target completion date must be on or "
                "after start date"
            )

    @staticmethod
    def _validate_transition(
        current: ProjectStatus,
        next_status: ProjectStatus,
    ) -> None:
        if current == next_status:
            return
        if next_status not in ALLOWED_STATUS_TRANSITIONS[current]:
            raise ProjectValidationException(
                f"Invalid Project status transition: "
                f"{current.value} -> {next_status.value}"
            )

    @classmethod
    def _snapshot(cls, project: Project) -> dict:
        return {
            "project_code": project.project_code,
            "name": project.name,
            "description": project.description,
            "customer_id": project.customer_id,
            "status": project.status,
            "priority": project.priority,
            "owner_id": project.owner_id,
            "primary_assignee_id": (
                project.primary_assignee_id
            ),
            "start_date": cls._serialize(project.start_date),
            "target_completion_date": cls._serialize(
                project.target_completion_date
            ),
            "completed_at": cls._serialize(
                project.completed_at
            ),
            "progress": project.progress,
            "created_at": cls._serialize(project.created_at),
            "updated_at": cls._serialize(project.updated_at),
        }

    @staticmethod
    def _serialize(value: Any):
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        return value
