from sqlalchemy import asc
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Session

from app.enums import ContextConfidentiality
from app.enums import RelationshipLifecycle
from app.models.engineering_context import EngineeringContext
from app.models.engineering_context_relationship import (
    EngineeringContextRelationship,
)
from app.models.engineering_context_relationship import InterfaceCommitment
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.engineering_workspace import EngineeringWorkspaceMember
from app.models.project import Project
from app.models.user import User


class EngineeringContextRelationshipRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_project(self, project_id: int) -> Project | None:
        return self.db.get(Project, project_id)

    def get_workspace(
        self,
        workspace_id: int,
    ) -> EngineeringWorkspace | None:
        return self.db.get(EngineeringWorkspace, workspace_id)

    def get_context(self, context_id: int) -> EngineeringContext | None:
        return self.db.get(EngineeringContext, context_id)

    def get_user(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_relationship(
        self,
        relationship_id: int,
    ) -> EngineeringContextRelationship | None:
        return (
            self._relationship_query()
            .filter(EngineeringContextRelationship.id == relationship_id)
            .first()
        )

    def get_visible_relationship(
        self,
        relationship_id: int,
        current_user: User,
    ) -> EngineeringContextRelationship | None:
        return (
            self._visible_relationships(current_user)
            .filter(EngineeringContextRelationship.id == relationship_id)
            .first()
        )

    def list_relationships(
        self,
        *,
        project_id: int,
        workspace_id: int | None,
        current_user: User,
        page: int,
        size: int,
        include_withdrawn: bool = False,
    ) -> tuple[list[EngineeringContextRelationship], int]:
        query = self._visible_relationships(current_user).filter(
            EngineeringContextRelationship.project_id == project_id
        )
        if workspace_id is not None:
            query = query.filter(
                or_(
                    EngineeringContextRelationship.source_workspace_id
                    == workspace_id,
                    EngineeringContextRelationship.target_workspace_id
                    == workspace_id,
                )
            )
        if not include_withdrawn:
            query = query.filter(
                EngineeringContextRelationship.lifecycle
                == RelationshipLifecycle.CURRENT.value
            )
        total = query.count()
        return (
            query.order_by(
                asc(EngineeringContextRelationship.created_at),
                asc(EngineeringContextRelationship.id),
            )
            .offset((page - 1) * size)
            .limit(size)
            .all(),
            total,
        )

    def equivalent_current_exists(self, values: dict) -> bool:
        fields = (
            "project_id",
            "meaning",
            "purpose",
            "source_kind",
            "source_context_id",
            "source_project_id",
            "source_workspace_id",
            "source_discipline",
            "source_external_key",
            "target_kind",
            "target_context_id",
            "target_project_id",
            "target_workspace_id",
            "target_discipline",
            "target_external_key",
        )
        query = self.db.query(EngineeringContextRelationship.id).filter(
            EngineeringContextRelationship.lifecycle
            == RelationshipLifecycle.CURRENT.value
        )
        for field in fields:
            query = query.filter(
                getattr(EngineeringContextRelationship, field)
                == values.get(field)
            )
        return query.first() is not None

    def create_relationship(
        self,
        values: dict,
    ) -> EngineeringContextRelationship:
        relationship_record = EngineeringContextRelationship(**values)
        self.db.add(relationship_record)
        self.db.flush()
        return relationship_record

    def update_relationship_versioned(
        self,
        *,
        relationship_id: int,
        expected_version: int,
        values: dict,
    ) -> bool:
        count = (
            self.db.query(EngineeringContextRelationship)
            .filter(
                EngineeringContextRelationship.id == relationship_id,
                EngineeringContextRelationship.version == expected_version,
            )
            .update(
                {
                    **values,
                    EngineeringContextRelationship.version:
                        expected_version + 1,
                },
                synchronize_session=False,
            )
        )
        self.db.flush()
        return count == 1

    def get_commitment(
        self,
        commitment_id: int,
    ) -> InterfaceCommitment | None:
        return (
            self._commitment_query()
            .filter(InterfaceCommitment.id == commitment_id)
            .first()
        )

    def get_visible_commitment(
        self,
        commitment_id: int,
        current_user: User,
    ) -> InterfaceCommitment | None:
        return (
            self._visible_commitments(current_user)
            .filter(InterfaceCommitment.id == commitment_id)
            .first()
        )

    def list_commitments(
        self,
        *,
        project_id: int,
        workspace_id: int | None,
        current_user: User,
        page: int,
        size: int,
        include_withdrawn: bool = False,
    ) -> tuple[list[InterfaceCommitment], int]:
        query = self._visible_commitments(current_user).filter(
            InterfaceCommitment.project_id == project_id
        )
        if workspace_id is not None:
            query = query.filter(
                or_(
                    InterfaceCommitment.provider_workspace_id == workspace_id,
                    InterfaceCommitment.consumer_workspace_id == workspace_id,
                )
            )
        if not include_withdrawn:
            query = query.filter(InterfaceCommitment.current_use.is_(True))
        total = query.count()
        return (
            query.order_by(
                asc(InterfaceCommitment.created_at),
                asc(InterfaceCommitment.id),
            )
            .offset((page - 1) * size)
            .limit(size)
            .all(),
            total,
        )

    def create_commitment(
        self,
        values: dict,
    ) -> InterfaceCommitment:
        commitment = InterfaceCommitment(**values)
        self.db.add(commitment)
        self.db.flush()
        return commitment

    def update_commitment_versioned(
        self,
        *,
        commitment_id: int,
        expected_version: int,
        values: dict,
    ) -> bool:
        count = (
            self.db.query(InterfaceCommitment)
            .filter(
                InterfaceCommitment.id == commitment_id,
                InterfaceCommitment.version == expected_version,
            )
            .update(
                {
                    **values,
                    InterfaceCommitment.version: expected_version + 1,
                },
                synchronize_session=False,
            )
        )
        self.db.flush()
        return count == 1

    def is_workspace_participant(
        self,
        workspace: EngineeringWorkspace,
        user_id: int,
    ) -> bool:
        if user_id in {workspace.owner_id, workspace.primary_assignee_id}:
            return True
        return (
            self.db.query(EngineeringWorkspaceMember.workspace_id)
            .filter(
                EngineeringWorkspaceMember.workspace_id == workspace.id,
                EngineeringWorkspaceMember.user_id == user_id,
            )
            .first()
            is not None
        )

    def _visible_relationships(self, current_user: User):
        participation = self._relationship_participation(current_user)
        if current_user.role == "admin":
            participation = True
        return self._relationship_query().filter(participation)

    def _relationship_participation(self, current_user: User):
        return or_(
            EngineeringContextRelationship.steward_id == current_user.id,
            EngineeringContextRelationship.created_by_id == current_user.id,
            EngineeringContextRelationship.project.has(
                or_(
                    Project.owner_id == current_user.id,
                    Project.primary_assignee_id == current_user.id,
                )
            ),
            EngineeringContextRelationship.source_workspace.has(
                or_(
                    EngineeringWorkspace.owner_id == current_user.id,
                    EngineeringWorkspace.primary_assignee_id
                    == current_user.id,
                    EngineeringWorkspace.memberships.any(
                        EngineeringWorkspaceMember.user_id == current_user.id
                    ),
                )
            ),
            EngineeringContextRelationship.target_workspace.has(
                or_(
                    EngineeringWorkspace.owner_id == current_user.id,
                    EngineeringWorkspace.primary_assignee_id
                    == current_user.id,
                    EngineeringWorkspace.memberships.any(
                        EngineeringWorkspaceMember.user_id == current_user.id
                    ),
                )
            ),
        )

    def _visible_commitments(self, current_user: User):
        participation = or_(
            InterfaceCommitment.steward_id == current_user.id,
            InterfaceCommitment.consumer_reviewer_id == current_user.id,
            InterfaceCommitment.provider_user_id == current_user.id,
            InterfaceCommitment.created_by_id == current_user.id,
            InterfaceCommitment.project.has(
                or_(
                    Project.owner_id == current_user.id,
                    Project.primary_assignee_id == current_user.id,
                )
            ),
            InterfaceCommitment.provider_workspace.has(
                or_(
                    EngineeringWorkspace.owner_id == current_user.id,
                    EngineeringWorkspace.primary_assignee_id
                    == current_user.id,
                    EngineeringWorkspace.memberships.any(
                        EngineeringWorkspaceMember.user_id == current_user.id
                    ),
                )
            ),
            InterfaceCommitment.consumer_workspace.has(
                or_(
                    EngineeringWorkspace.owner_id == current_user.id,
                    EngineeringWorkspace.primary_assignee_id
                    == current_user.id,
                    EngineeringWorkspace.memberships.any(
                        EngineeringWorkspaceMember.user_id == current_user.id
                    ),
                )
            ),
        )
        if current_user.role == "admin":
            participation = True
        return self._commitment_query().filter(
            participation,
            or_(
                InterfaceCommitment.confidentiality
                != ContextConfidentiality.RESTRICTED.value,
                InterfaceCommitment.provider_user_id == current_user.id,
                InterfaceCommitment.steward_id == current_user.id,
            ),
        )

    def _relationship_query(self):
        return self.db.query(EngineeringContextRelationship).options(
            joinedload(EngineeringContextRelationship.project),
            joinedload(EngineeringContextRelationship.source_context),
            joinedload(EngineeringContextRelationship.target_context),
            joinedload(EngineeringContextRelationship.source_workspace),
            joinedload(EngineeringContextRelationship.target_workspace),
            joinedload(EngineeringContextRelationship.steward),
        )

    def _commitment_query(self):
        return self.db.query(InterfaceCommitment).options(
            joinedload(InterfaceCommitment.relationship_record),
            joinedload(InterfaceCommitment.project),
            joinedload(InterfaceCommitment.provider_user),
            joinedload(InterfaceCommitment.provider_workspace),
            joinedload(InterfaceCommitment.consumer_workspace),
            joinedload(InterfaceCommitment.steward),
            joinedload(InterfaceCommitment.consumer_reviewer),
            joinedload(InterfaceCommitment.successor),
        )
