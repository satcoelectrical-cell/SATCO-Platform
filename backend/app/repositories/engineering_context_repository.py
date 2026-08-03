from __future__ import annotations

from sqlalchemy import and_
from sqlalchemy import asc
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.enums import ContextConfidentiality
from app.enums import ContextLifecycle
from app.models.engineering_context import EngineeringContext
from app.models.engineering_context import EngineeringContextAssumption
from app.models.engineering_context import EngineeringContextFact
from app.models.engineering_context import EngineeringContextSourceReference
from app.models.engineering_context import EngineeringContextSubjectReference
from app.models.engineering_context import EngineeringContextValue
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.engineering_workspace import EngineeringWorkspaceMember
from app.models.project import Project
from app.models.user import User
from app.models.organization import UserOrganizationMembership


class EngineeringContextRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_project(self, project_id: int, current_user: User) -> Project | None:
        return self.db.query(Project).filter(
            Project.id == project_id,
            Project.organization_id.in_(
                select(UserOrganizationMembership.organization_id).where(
                    UserOrganizationMembership.user_id == current_user.id,
                    UserOrganizationMembership.is_enabled.is_(True),
                    UserOrganizationMembership.is_selected.is_(True),
                )
            ),
        ).first()

    def get_workspace(
        self,
        workspace_id: int,
    ) -> EngineeringWorkspace | None:
        return self.db.get(EngineeringWorkspace, workspace_id)

    def get_user(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_id(
        self,
        context_id: int,
    ) -> EngineeringContext | None:
        return (
            self._base_query()
            .filter(EngineeringContext.id == context_id)
            .first()
        )

    def get_visible_by_id(
        self,
        context_id: int,
        current_user: User,
    ) -> EngineeringContext | None:
        return (
            self._apply_visibility(self._base_query(), current_user)
            .filter(EngineeringContext.id == context_id)
            .first()
        )

    def list_for_scope(
        self,
        *,
        project_id: int,
        workspace_id: int | None,
        current_user: User,
        page: int,
        size: int,
        include_withdrawn: bool,
    ) -> tuple[list[EngineeringContext], int]:
        scope_participation = self._has_scope_participation(
            project_id=project_id,
            workspace_id=workspace_id,
            current_user=current_user,
        )
        query = self._apply_visibility(
            self._base_query().filter(
                EngineeringContext.project_id == project_id,
                EngineeringContext.workspace_id == workspace_id,
            ),
            current_user,
            participation_override=(
                True if scope_participation else None
            ),
        )
        if not include_withdrawn:
            query = query.filter(
                EngineeringContext.lifecycle
                == ContextLifecycle.CURRENT.value
            )
        total = query.count()
        items = (
            query.order_by(
                asc(EngineeringContext.created_at),
                asc(EngineeringContext.id),
            )
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        return items, total

    def create(
        self,
        *,
        context_values: dict,
        payload_values: dict | None,
        subject_values: list[dict],
        source_values: list[dict],
    ) -> EngineeringContext:
        context = EngineeringContext(**context_values)
        self.db.add(context)
        self.db.flush()

        if context.kind == "qualified_fact":
            self.db.add(
                EngineeringContextFact(
                    context_id=context.id,
                    **(payload_values or {}),
                )
            )
        elif context.kind == "qualified_engineering_value":
            self.db.add(
                EngineeringContextValue(
                    context_id=context.id,
                    **(payload_values or {}),
                )
            )
        elif context.kind == "assumption":
            self.db.add(
                EngineeringContextAssumption(
                    context_id=context.id,
                    **(payload_values or {}),
                )
            )

        for values in subject_values:
            self.db.add(
                EngineeringContextSubjectReference(
                    context_id=context.id,
                    **values,
                )
            )
        for values in source_values:
            self.db.add(
                EngineeringContextSourceReference(
                    context_id=context.id,
                    **values,
                )
            )
        self.db.flush()
        return context

    def update_versioned(
        self,
        *,
        context_id: int,
        expected_version: int,
        values: dict,
    ) -> bool:
        updated = (
            self.db.query(EngineeringContext)
            .filter(
                EngineeringContext.id == context_id,
                EngineeringContext.version == expected_version,
            )
            .update(
                {
                    **values,
                    EngineeringContext.version: expected_version + 1,
                },
                synchronize_session=False,
            )
        )
        self.db.flush()
        return updated == 1

    def update_payload(
        self,
        context: EngineeringContext,
        values: dict,
    ) -> None:
        payload = (
            context.facts
            or context.engineering_value
            or context.assumption
        )
        if payload is None:
            return
        for field, value in values.items():
            setattr(payload, field, value)
        self.db.flush()

    def add_source_reference(
        self,
        *,
        context_id: int,
        values: dict,
    ) -> None:
        self.db.add(
            EngineeringContextSourceReference(
                context_id=context_id,
                **values,
            )
        )
        self.db.flush()

    def remove_source_reference(
        self,
        source: EngineeringContextSourceReference,
    ) -> None:
        self.db.delete(source)
        self.db.flush()

    def get_source_reference(
        self,
        *,
        context_id: int,
        source_id: int,
    ) -> EngineeringContextSourceReference | None:
        return (
            self.db.query(EngineeringContextSourceReference)
            .filter(
                EngineeringContextSourceReference.id == source_id,
                EngineeringContextSourceReference.context_id == context_id,
            )
            .first()
        )

    def _has_scope_participation(
        self,
        *,
        project_id: int,
        workspace_id: int | None,
        current_user: User,
    ) -> bool:
        if current_user.role == "admin":
            return True

        project = self.get_project(project_id, current_user)
        if project is not None and current_user.id in {
            project.owner_id,
            project.primary_assignee_id,
        }:
            return True

        if workspace_id is None:
            return False
        workspace = self.get_workspace(workspace_id)
        if workspace is None:
            return False
        if current_user.id in {
            workspace.owner_id,
            workspace.primary_assignee_id,
        }:
            return True
        return (
            self.db.query(EngineeringWorkspaceMember.workspace_id)
            .filter(
                EngineeringWorkspaceMember.workspace_id == workspace_id,
                EngineeringWorkspaceMember.user_id == current_user.id,
            )
            .first()
            is not None
        )

    @staticmethod
    def _apply_visibility(
        query,
        current_user: User,
        *,
        participation_override: bool | None = None,
    ):
        workspace_membership = EngineeringContext.workspace.has(
            EngineeringWorkspace.memberships.any(
                EngineeringWorkspaceMember.user_id == current_user.id
            )
        )
        participation = or_(
            EngineeringContext.owner_id == current_user.id,
            EngineeringContext.steward_id == current_user.id,
            EngineeringContext.project.has(
                or_(
                    Project.owner_id == current_user.id,
                    Project.primary_assignee_id == current_user.id,
                )
            ),
            EngineeringContext.workspace.has(
                or_(
                    EngineeringWorkspace.owner_id == current_user.id,
                    EngineeringWorkspace.primary_assignee_id
                    == current_user.id,
                )
            ),
            workspace_membership,
        )
        if participation_override is not None:
            participation = participation_override
        elif current_user.role == "admin":
            participation = True

        restricted_to_another_user = (
            EngineeringContext.source_references.any(
                and_(
                    EngineeringContextSourceReference.confidentiality
                    == ContextConfidentiality.RESTRICTED.value,
                    EngineeringContextSourceReference.source_owner_id
                    != current_user.id,
                )
            )
        )
        return query.filter(
            EngineeringContext.project.has(
                Project.organization_id.in_(
                    select(UserOrganizationMembership.organization_id).where(
                        UserOrganizationMembership.user_id == current_user.id,
                        UserOrganizationMembership.is_enabled.is_(True),
                        UserOrganizationMembership.is_selected.is_(True),
                    )
                )
            ),
            participation,
            ~restricted_to_another_user,
        )

    def _base_query(self):
        return self.db.query(EngineeringContext).options(
            joinedload(EngineeringContext.project),
            joinedload(EngineeringContext.workspace),
            joinedload(EngineeringContext.owner),
            joinedload(EngineeringContext.steward),
            joinedload(EngineeringContext.created_by),
            joinedload(EngineeringContext.facts),
            joinedload(EngineeringContext.engineering_value),
            joinedload(EngineeringContext.assumption),
            selectinload(EngineeringContext.subject_references),
            selectinload(
                EngineeringContext.source_references
            ).joinedload(
                EngineeringContextSourceReference.source_owner
            ),
        )
