from datetime import datetime, timezone
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from uuid import UUID, uuid4

from app.core.database import SessionLocal
from app.enums import Discipline, ProjectStatus, WorkspaceStatus
from app.exceptions.engineering_workspace import (
    InvalidWorkspaceAssignee,
    InvalidWorkspaceCollaborator,
    InvalidWorkspaceOwner,
    InvalidWorkspaceStatusTransition,
    WorkspaceAlreadyExists,
    WorkspaceArchived,
    WorkspaceForbidden,
    WorkspaceMemberAlreadyExists,
    WorkspaceMemberNotFound,
    WorkspaceNotFound,
    WorkspaceProjectStateConflict,
    WorkspaceVersionConflict,
)
from app.exceptions.project import ProjectNotFoundException
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.user import User
from app.permissions.roles import Role
from app.repositories.engineering_workspace_repository import (
    EngineeringWorkspaceRepository,
)
from app.schemas.engineering_workspace import (
    EngineeringWorkspaceCollaboratorAdd,
    EngineeringWorkspaceCreate,
    EngineeringWorkspaceGraphSummary,
    EngineeringWorkspaceUpdate,
    WorkspaceArchiveRequest,
    WorkspaceRestoreRequest,
    WorkspaceStatusTransitionRequest,
)
from app.services.audit_service import create_audit_log
from app.services.discipline_package_service import (
    DisciplinePackageWorkspaceService,
    FrozenGuardedIdentity,
    PackageWorkspaceAlreadyExists,
    PackageWorkspaceConflict,
    PackageWorkspaceForbidden,
    PackageWorkspaceInvalidPerson,
    WorkspaceCreateCommand,
)


ALLOWED_TRANSITIONS = {
    WorkspaceStatus.DRAFT: {
        WorkspaceStatus.ACTIVE,
    },
    WorkspaceStatus.ACTIVE: {
        WorkspaceStatus.ON_HOLD,
        WorkspaceStatus.UNDER_REVIEW,
    },
    WorkspaceStatus.ON_HOLD: {
        WorkspaceStatus.ACTIVE,
    },
    WorkspaceStatus.UNDER_REVIEW: {
        WorkspaceStatus.ACTIVE,
        WorkspaceStatus.COMPLETED,
    },
    WorkspaceStatus.COMPLETED: {
        WorkspaceStatus.ACTIVE,
    },
    WorkspaceStatus.ARCHIVED: set(),
}
PROJECT_BLOCKED_STATUSES = {
    ProjectStatus.COMPLETED.value,
    ProjectStatus.CANCELLED.value,
}


class EngineeringWorkspaceService:
    def __init__(self, db: Session, organization_id=None, *, package_uow_factory=None):
        self.db = db
        self.repository = EngineeringWorkspaceRepository(db)
        self.organization_id = organization_id
        self._package_uow_factory = package_uow_factory or SessionLocal

    def create(
        self,
        project_id: int,
        data: EngineeringWorkspaceCreate,
        current_user: User,
        correlation_id: UUID | None = None,
    ) -> dict:
        """Create package-derived state in a fresh guarded UoW."""
        organization_id = self._organization_id(current_user)
        owner_id = data.owner_id or current_user.id
        try:
            workspace_id = DisciplinePackageWorkspaceService(
                self._package_uow_factory
            ).create(
                FrozenGuardedIdentity(
                    actor_id=current_user.id,
                    organization_id=organization_id,
                    auth_version=current_user.auth_version,
                    correlation_id=correlation_id or uuid4(),
                ),
                WorkspaceCreateCommand(
                    project_id=project_id,
                    discipline=data.discipline.value,
                    description=data.description,
                    owner_id=owner_id,
                    primary_assignee_id=data.primary_assignee_id,
                    collaborator_ids=tuple(data.collaborator_ids),
                ),
            )
        except PackageWorkspaceAlreadyExists as exc:
            raise WorkspaceAlreadyExists() from exc
        except PackageWorkspaceForbidden as exc:
            raise WorkspaceForbidden() from exc
        except PackageWorkspaceInvalidPerson as exc:
            if exc.kind == "owner":
                raise InvalidWorkspaceOwner() from exc
            if exc.kind == "assignee":
                raise InvalidWorkspaceAssignee() from exc
            raise InvalidWorkspaceCollaborator() from exc
        except PackageWorkspaceConflict as exc:
            raise WorkspaceProjectStateConflict(str(exc)) from exc
        self.db.expire_all()
        return self._response(
            self._get_visible(workspace_id, current_user), current_user
        )

    def _legacy_create_for_reference(
        self,
        project_id: int,
        data: EngineeringWorkspaceCreate,
        current_user: User,
    ) -> dict:
        organization_id = self._organization_id(current_user)
        project = self._get_project(project_id, organization_id)
        is_admin = self._is_admin(current_user)
        if not is_admin and project.owner_id != current_user.id:
            raise WorkspaceForbidden()
        if project.status in PROJECT_BLOCKED_STATUSES:
            raise WorkspaceProjectStateConflict(
                "Workspaces cannot be created for completed or "
                "cancelled Projects"
            )
        if self.repository.get_by_project_discipline(
            project_id,
            data.discipline,
            organization_id,
        ):
            raise WorkspaceAlreadyExists()

        owner_id = data.owner_id or current_user.id
        self._validate_user(owner_id, "owner")
        if data.primary_assignee_id is not None:
            self._validate_user(
                data.primary_assignee_id,
                "assignee",
            )
        collaborators = self._validate_collaborators(
            data.collaborator_ids,
            owner_id,
            data.primary_assignee_id,
        )

        try:
            workspace = self.repository.create(
                project_id=project_id,
                discipline=data.discipline,
                description=data.description,
                owner_id=owner_id,
                primary_assignee_id=data.primary_assignee_id,
                created_by_id=current_user.id,
            )
            for collaborator in collaborators:
                self.repository.add_member(
                    workspace_id=workspace.id,
                    user_id=collaborator.id,
                    added_by_id=current_user.id,
                )
            self._audit_and_commit(
                current_user=current_user,
                action="workspace_created",
                workspace_id=workspace.id,
                details={
                    "project_id": project_id,
                    "discipline": data.discipline.value,
                    "owner_id": owner_id,
                    "primary_assignee_id": data.primary_assignee_id,
                    "collaborator_ids": [
                        collaborator.id
                        for collaborator in collaborators
                    ],
                    "status": WorkspaceStatus.DRAFT.value,
                    "version": 1,
                },
            )
        except IntegrityError as exc:
            self.db.rollback()
            raise WorkspaceAlreadyExists() from exc

        return self._response(
            self._get_visible(workspace.id, current_user),
            current_user,
        )

    def list_for_project(
        self,
        *,
        project_id: int,
        current_user: User,
        **filters,
    ) -> dict:
        organization_id = self._organization_id(current_user)
        project = self._get_project(project_id, organization_id)
        items, total = self.repository.list_for_project(
            project_id=project_id,
            current_user=current_user,
            organization_id=organization_id,
            **filters,
        )
        if (
            not self._is_admin(current_user)
            and project.owner_id != current_user.id
            and project.primary_assignee_id != current_user.id
            and not self.repository.user_has_project_workspace_access(
                project_id,
                current_user.id,
                organization_id,
            )
        ):
            raise ProjectNotFoundException(project_id)
        return {
            "items": [
                self._response(item, current_user)
                for item in items
            ],
            "total": total,
            "page": filters["page"],
            "size": filters["size"],
        }

    def get(self, workspace_id: int, current_user: User) -> dict:
        return self._response(
            self._get_visible(workspace_id, current_user),
            current_user,
        )

    def get_authorized_graph_summary(self, *, workspace_id: int, current_user: User) -> EngineeringWorkspaceGraphSummary:
        """Exact visibility-authorized Workspace read without broad response fields."""
        workspace = self._get_visible(workspace_id, current_user)
        return EngineeringWorkspaceGraphSummary(workspace_id=workspace.id, project_id=workspace.project_id, discipline=workspace.discipline, workspace_status=workspace.status)

    def update(
        self,
        workspace_id: int,
        data: EngineeringWorkspaceUpdate,
        current_user: User,
    ) -> dict:
        workspace = self._get_visible(workspace_id, current_user)
        self._require_operational(workspace)
        values = data.model_dump(
            exclude={"expected_version"},
            exclude_unset=True,
        )
        self._authorize_metadata_update(
            workspace,
            values,
            current_user,
        )
        if "owner_id" in values:
            self._validate_user(values["owner_id"], "owner")
        if (
            "primary_assignee_id" in values
            and values["primary_assignee_id"] is not None
        ):
            self._validate_user(
                values["primary_assignee_id"],
                "assignee",
            )
        self._reject_assignment_membership_overlap(
            workspace,
            values,
        )

        before = self._snapshot(workspace)
        self._versioned_update(
            workspace.id,
            data.expected_version,
            values,
        )
        updated = self.repository.get_by_id(
            workspace.id,
            self._organization_id(current_user),
        )
        after = self._snapshot(updated)
        changed = [
            key for key in values
            if before.get(key) != after.get(key)
        ]
        if "owner_id" in changed:
            action = "workspace_owner_changed"
        elif "primary_assignee_id" in changed:
            action = "workspace_primary_assignee_changed"
        else:
            action = "workspace_updated"
        self._audit_and_commit(
            current_user=current_user,
            action=action,
            workspace_id=workspace.id,
            details={
                "project_id": workspace.project_id,
                "changed_fields": changed,
                "before": {
                    field: before.get(field)
                    for field in changed
                },
                "after": {
                    field: after.get(field)
                    for field in changed
                },
                "version": data.expected_version + 1,
            },
        )
        return self.get(workspace.id, current_user)

    def transition(
        self,
        workspace_id: int,
        data: WorkspaceStatusTransitionRequest,
        current_user: User,
    ) -> dict:
        workspace = self._get_visible(workspace_id, current_user)
        self._authorize_governance(workspace, current_user)
        self._require_operational(workspace)
        if data.status == WorkspaceStatus.ARCHIVED:
            raise InvalidWorkspaceStatusTransition(
                workspace.status,
                data.status.value,
            )
        current = WorkspaceStatus(workspace.status)
        if current == data.status:
            if workspace.version != data.expected_version:
                raise WorkspaceVersionConflict()
            return self._response(workspace, current_user)
        if data.status not in ALLOWED_TRANSITIONS[current]:
            raise InvalidWorkspaceStatusTransition(
                current.value,
                data.status.value,
            )
        if (
            current == WorkspaceStatus.COMPLETED
            and data.status == WorkspaceStatus.ACTIVE
            and not data.reason
        ):
            raise WorkspaceProjectStateConflict(
                "Reopening a completed Workspace requires a reason"
            )
        if data.status == WorkspaceStatus.ACTIVE:
            self._require_active_project(workspace.project.status)

        self._versioned_update(
            workspace.id,
            data.expected_version,
            {"status": data.status.value},
        )
        self._audit_and_commit(
            current_user=current_user,
            action="workspace_status_changed",
            workspace_id=workspace.id,
            details={
                "project_id": workspace.project_id,
                "before": {"status": current.value},
                "after": {"status": data.status.value},
                "reason": data.reason,
                "version": data.expected_version + 1,
            },
        )
        return self.get(workspace.id, current_user)

    def archive(
        self,
        workspace_id: int,
        data: WorkspaceArchiveRequest,
        current_user: User,
    ) -> dict:
        workspace = self._get_visible(workspace_id, current_user)
        self._authorize_governance(workspace, current_user)
        self._require_operational(workspace)
        previous_status = workspace.status
        archived_at = datetime.now(timezone.utc)
        self._versioned_update(
            workspace.id,
            data.expected_version,
            {
                "status": WorkspaceStatus.ARCHIVED.value,
                "archived_at": archived_at,
            },
        )
        self._audit_and_commit(
            current_user=current_user,
            action="workspace_archived",
            workspace_id=workspace.id,
            details={
                "project_id": workspace.project_id,
                "before": {"status": previous_status},
                "after": {
                    "status": WorkspaceStatus.ARCHIVED.value,
                    "archived_at": archived_at.isoformat(),
                },
                "reason": data.reason,
                "version": data.expected_version + 1,
            },
        )
        return self.get(workspace.id, current_user)

    def restore(
        self,
        workspace_id: int,
        data: WorkspaceRestoreRequest,
        current_user: User,
    ) -> dict:
        workspace = self._get_visible(workspace_id, current_user)
        self._authorize_governance(workspace, current_user)
        if workspace.status != WorkspaceStatus.ARCHIVED.value:
            raise InvalidWorkspaceStatusTransition(
                workspace.status,
                WorkspaceStatus.ACTIVE.value,
            )
        self._require_active_project(workspace.project.status)
        self._versioned_update(
            workspace.id,
            data.expected_version,
            {
                "status": WorkspaceStatus.ACTIVE.value,
                "archived_at": None,
            },
        )
        self._audit_and_commit(
            current_user=current_user,
            action="workspace_restored",
            workspace_id=workspace.id,
            details={
                "project_id": workspace.project_id,
                "before": {
                    "status": WorkspaceStatus.ARCHIVED.value,
                },
                "after": {
                    "status": WorkspaceStatus.ACTIVE.value,
                    "archived_at": None,
                },
                "reason": data.reason,
                "version": data.expected_version + 1,
            },
        )
        return self.get(workspace.id, current_user)

    def add_collaborator(
        self,
        workspace_id: int,
        data: EngineeringWorkspaceCollaboratorAdd,
        current_user: User,
    ) -> dict:
        workspace = self._get_visible(workspace_id, current_user)
        self._authorize_governance(workspace, current_user)
        self._require_operational(workspace)
        collaborator = self._validate_user(data.user_id, "collaborator")
        if data.user_id in {
            workspace.owner_id,
            workspace.primary_assignee_id,
        }:
            raise InvalidWorkspaceCollaborator(
                "Owner and primary assignee are already Workspace participants"
            )
        if self.repository.get_member(workspace.id, data.user_id):
            raise WorkspaceMemberAlreadyExists()
        self._versioned_update(
            workspace.id,
            data.expected_version,
            {},
        )
        try:
            self.repository.add_member(
                workspace_id=workspace.id,
                user_id=collaborator.id,
                added_by_id=current_user.id,
            )
            self._audit_and_commit(
                current_user=current_user,
                action="workspace_collaborator_added",
                workspace_id=workspace.id,
                details={
                    "project_id": workspace.project_id,
                    "user_id": collaborator.id,
                    "version": data.expected_version + 1,
                },
            )
        except IntegrityError as exc:
            self.db.rollback()
            raise WorkspaceMemberAlreadyExists() from exc
        return self.get(workspace.id, current_user)

    def remove_collaborator(
        self,
        workspace_id: int,
        user_id: int,
        expected_version: int,
        current_user: User,
    ) -> None:
        workspace = self._get_visible(workspace_id, current_user)
        self._authorize_governance(workspace, current_user)
        self._require_operational(workspace)
        member = self.repository.get_member(workspace.id, user_id)
        if member is None:
            raise WorkspaceMemberNotFound()
        self._versioned_update(
            workspace.id,
            expected_version,
            {},
        )
        self.repository.remove_member(member)
        self._audit_and_commit(
            current_user=current_user,
            action="workspace_collaborator_removed",
            workspace_id=workspace.id,
            details={
                "project_id": workspace.project_id,
                "user_id": user_id,
                "version": expected_version + 1,
            },
        )

    def _get_project(self, project_id: int, organization_id):
        project = self.repository.get_project(project_id, organization_id)
        if project is None:
            raise ProjectNotFoundException(project_id)
        return project

    def _get_visible(
        self,
        workspace_id: int,
        current_user: User,
    ) -> EngineeringWorkspace:
        organization_id = self._organization_id(current_user)
        workspace = self.repository.get_visible_by_id(
            workspace_id,
            current_user,
            organization_id,
        )
        if workspace is None:
            raise WorkspaceNotFound(workspace_id)
        return workspace

    def _organization_id(self, current_user: User):
        if self.organization_id is not None:
            self._active_organization_id = self.organization_id
            return self.organization_id
        organization_id = self.repository.get_selected_organization_id(
            current_user.id
        )
        if organization_id is None:
            raise WorkspaceNotFound(0)
        self._active_organization_id = organization_id
        return organization_id

    def _validate_user(self, user_id: int, kind: str) -> User:
        user = self.repository.get_user(user_id)
        valid = (
            user is not None
            and user.is_active
            and user.role in {Role.ADMIN.value, Role.ENGINEER.value}
        )
        if not valid:
            if kind == "owner":
                raise InvalidWorkspaceOwner()
            if kind == "assignee":
                raise InvalidWorkspaceAssignee()
            raise InvalidWorkspaceCollaborator()
        return user

    def _validate_collaborators(
        self,
        collaborator_ids: list[int],
        owner_id: int,
        assignee_id: int | None,
    ) -> list[User]:
        if owner_id in collaborator_ids or (
            assignee_id is not None
            and assignee_id in collaborator_ids
        ):
            raise InvalidWorkspaceCollaborator(
                "Owner and primary assignee must not be duplicated as "
                "collaborators"
            )
        return [
            self._validate_user(user_id, "collaborator")
            for user_id in collaborator_ids
        ]

    def _authorize_metadata_update(
        self,
        workspace: EngineeringWorkspace,
        values: dict,
        current_user: User,
    ) -> None:
        is_admin = self._is_admin(current_user)
        is_project_owner = workspace.project.owner_id == current_user.id
        is_workspace_owner = workspace.owner_id == current_user.id
        is_assignee = (
            workspace.primary_assignee_id == current_user.id
        )
        if not (
            is_admin
            or is_project_owner
            or is_workspace_owner
            or is_assignee
        ):
            raise WorkspaceForbidden()
        if "owner_id" in values and not (
            is_admin or is_project_owner
        ):
            raise WorkspaceForbidden()
        if "primary_assignee_id" in values and not (
            is_admin or is_project_owner or is_workspace_owner
        ):
            raise WorkspaceForbidden()
        if is_assignee and not (
            is_admin or is_project_owner or is_workspace_owner
        ) and set(values) != {"description"}:
            raise WorkspaceForbidden()

    def _authorize_governance(
        self,
        workspace: EngineeringWorkspace,
        current_user: User,
    ) -> None:
        if not (
            self._is_admin(current_user)
            or workspace.project.owner_id == current_user.id
            or workspace.owner_id == current_user.id
        ):
            raise WorkspaceForbidden()

    def _reject_assignment_membership_overlap(
        self,
        workspace: EngineeringWorkspace,
        values: dict,
    ) -> None:
        member_ids = {
            membership.user_id
            for membership in workspace.memberships
        }
        next_owner = values.get("owner_id", workspace.owner_id)
        next_assignee = values.get(
            "primary_assignee_id",
            workspace.primary_assignee_id,
        )
        if next_owner in member_ids or (
            next_assignee is not None
            and next_assignee in member_ids
        ):
            raise InvalidWorkspaceCollaborator(
                "A collaborator must be removed before assignment as "
                "owner or primary assignee"
            )

    def _versioned_update(
        self,
        workspace_id: int,
        expected_version: int,
        values: dict,
    ) -> None:
        if not self.repository.update_versioned(
            workspace_id,
            expected_version,
            values,
            organization_id=self._active_organization_id,
        ):
            self.db.rollback()
            raise WorkspaceVersionConflict()
        self.db.expire_all()

    def _audit_and_commit(
        self,
        *,
        current_user: User,
        action: str,
        workspace_id: int,
        details: dict,
    ) -> None:
        try:
            create_audit_log(
                db=self.db,
                user_id=current_user.id,
                action=action,
                entity="ENGINEERING_WORKSPACE",
                entity_id=workspace_id,
                details=details,
            )
        except Exception:
            self.db.rollback()
            raise
        self.db.expire_all()

    @staticmethod
    def _require_operational(workspace: EngineeringWorkspace) -> None:
        if workspace.status == WorkspaceStatus.ARCHIVED.value:
            raise WorkspaceArchived()

    @staticmethod
    def _require_active_project(project_status: str) -> None:
        if project_status in PROJECT_BLOCKED_STATUSES:
            raise WorkspaceProjectStateConflict(
                "Workspace cannot become active while its Project is "
                "completed or cancelled"
            )

    @staticmethod
    def _is_admin(user: User) -> bool:
        return user.role == Role.ADMIN.value

    @classmethod
    def _snapshot(cls, workspace: EngineeringWorkspace) -> dict:
        return {
            "description": workspace.description,
            "owner_id": workspace.owner_id,
            "primary_assignee_id": workspace.primary_assignee_id,
            "status": workspace.status,
            "archived_at": cls._serialize(workspace.archived_at),
            "version": workspace.version,
        }

    @staticmethod
    def _serialize(value: Any):
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    def _response(
        self,
        workspace: EngineeringWorkspace,
        current_user: User,
    ) -> dict:
        collaborators = sorted(
            (
                membership.user
                for membership in workspace.memberships
            ),
            key=lambda user: user.id,
        )
        return {
            "id": workspace.id,
            "project_id": workspace.project_id,
            "project_code": workspace.project.project_code,
            "project_name": workspace.project.name,
            "discipline": workspace.discipline,
            "display_name": Discipline(
                workspace.discipline
            ).display_name,
            "description": workspace.description,
            "status": workspace.status,
            "owner": self._user_summary(workspace.owner),
            "primary_assignee": self._user_summary(
                workspace.primary_assignee
            ),
            "collaborators": [
                self._user_summary(user)
                for user in collaborators
            ],
            "collaborator_count": len(collaborators),
            "version": workspace.version,
            "archived_at": workspace.archived_at,
            "created_at": workspace.created_at,
            "updated_at": workspace.updated_at,
            "allowed_actions": self._allowed_actions(
                workspace,
                current_user,
            ),
        }

    @staticmethod
    def _user_summary(user: User | None) -> dict | None:
        if user is None:
            return None
        return {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
        }

    def _allowed_actions(
        self,
        workspace: EngineeringWorkspace,
        current_user: User,
    ) -> list[str]:
        actions = ["view"]
        if workspace.status == WorkspaceStatus.ARCHIVED.value:
            if (
                self._is_admin(current_user)
                or workspace.project.owner_id == current_user.id
                or workspace.owner_id == current_user.id
            ) and workspace.project.status not in PROJECT_BLOCKED_STATUSES:
                actions.append("restore")
            return actions

        is_admin = self._is_admin(current_user)
        is_project_owner = workspace.project.owner_id == current_user.id
        is_workspace_owner = workspace.owner_id == current_user.id
        is_assignee = (
            workspace.primary_assignee_id == current_user.id
        )
        if is_admin or is_project_owner or is_workspace_owner or is_assignee:
            actions.append("update_description")
        if is_admin or is_project_owner:
            actions.append("assign_owner")
        if is_admin or is_project_owner or is_workspace_owner:
            actions.extend(
                [
                    "assign_primary_assignee",
                    "manage_collaborators",
                    "change_status",
                    "archive",
                ]
            )
        return actions
