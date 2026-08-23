from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.enums.project_foundation import ProjectScopeKind
from app.models.project import Project
from app.models.project_foundation import (
    ProjectCompletionCriterion,
    ProjectFoundation,
    ProjectRequiredInput,
    ProjectScopeItem,
)


class ProjectFoundationRepository:
    """No-commit persistence for the Project-owned foundation."""

    def __init__(self, session: Session):
        self.session = session

    def get_project(self, project_id: int, organization_id: UUID, *, lock: bool = False):
        query = self.session.query(Project).filter(
            Project.id == project_id,
            Project.organization_id == organization_id,
        )
        if lock:
            query = query.with_for_update()
        return query.first()

    def get_foundation(self, project_id: int, organization_id: UUID, *, lock: bool = False):
        query = self.session.query(ProjectFoundation).filter(
            ProjectFoundation.project_id == project_id,
            ProjectFoundation.organization_id == organization_id,
        )
        if lock:
            query = query.with_for_update()
        return query.first()

    def get_input(self, input_id: UUID, project_id: int, organization_id: UUID, *, lock: bool = False):
        query = self.session.query(ProjectRequiredInput).filter(
            ProjectRequiredInput.id == input_id,
            ProjectRequiredInput.project_id == project_id,
            ProjectRequiredInput.organization_id == organization_id,
        )
        if lock:
            query = query.with_for_update()
        return query.first()

    def add(self, item: object) -> None:
        self.session.add(item)

    def load_children(self, project_id: int, organization_id: UUID):
        scope = self.session.query(ProjectScopeItem).filter_by(
            project_id=project_id, organization_id=organization_id,
        ).order_by(ProjectScopeItem.kind, ProjectScopeItem.ordinal, ProjectScopeItem.id).all()
        criteria = self.session.query(ProjectCompletionCriterion).filter_by(
            project_id=project_id, organization_id=organization_id,
        ).order_by(ProjectCompletionCriterion.ordinal, ProjectCompletionCriterion.id).all()
        inputs = self.session.query(ProjectRequiredInput).filter_by(
            project_id=project_id, organization_id=organization_id,
        ).order_by(ProjectRequiredInput.ordinal, ProjectRequiredInput.id).all()
        return scope, criteria, inputs

    def replace_basis_children(
        self,
        foundation: ProjectFoundation,
        *,
        in_scope: tuple[str, ...],
        out_of_scope: tuple[str, ...],
        completion_criteria: tuple[str, ...],
        actor_id: int,
        now: datetime,
    ) -> None:
        self.session.query(ProjectScopeItem).filter_by(project_id=foundation.project_id).delete(synchronize_session=False)
        self.session.query(ProjectCompletionCriterion).filter_by(project_id=foundation.project_id).delete(synchronize_session=False)
        for kind, statements in (
            (ProjectScopeKind.IN_SCOPE.value, in_scope),
            (ProjectScopeKind.OUT_OF_SCOPE.value, out_of_scope),
        ):
            for ordinal, statement in enumerate(statements):
                self.session.add(ProjectScopeItem(
                    id=uuid4(), project_id=foundation.project_id,
                    organization_id=foundation.organization_id, kind=kind,
                    statement=statement, ordinal=ordinal,
                    created_by_id=actor_id, created_at=now,
                    updated_by_id=actor_id, updated_at=now,
                ))
        for ordinal, statement in enumerate(completion_criteria):
            self.session.add(ProjectCompletionCriterion(
                id=uuid4(), project_id=foundation.project_id,
                organization_id=foundation.organization_id,
                statement=statement, ordinal=ordinal,
                created_by_id=actor_id, created_at=now,
                updated_by_id=actor_id, updated_at=now,
            ))

    def reorder_inputs(
        self,
        project_id: int,
        organization_id: UUID,
        ordered_ids: tuple[UUID, ...],
        actor_id: int,
        now: datetime,
    ) -> bool:
        rows = self.session.query(ProjectRequiredInput).filter_by(
            project_id=project_id, organization_id=organization_id,
        ).with_for_update().all()
        by_id = {row.id: row for row in rows}
        if set(by_id) != set(ordered_ids) or len(rows) != len(ordered_ids):
            return False
        for ordinal, identity in enumerate(ordered_ids):
            row = by_id[identity]
            row.ordinal = ordinal
            row.updated_by_id = actor_id
            row.updated_at = now
            row.version += 1
        return True

    def flush(self) -> None:
        self.session.flush()
