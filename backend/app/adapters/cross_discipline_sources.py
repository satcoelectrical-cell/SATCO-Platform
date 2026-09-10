"""Authorization-first source projection foundation for PATCH-053 Batch 1."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.discipline_packages.cross_discipline.canonical import digest
from app.models.engineering_workspace import EngineeringWorkspace, EngineeringWorkspaceMember
from app.models.project import Project
from app.ports.cross_discipline_intelligence import ProtectedResourceError


@dataclass(frozen=True, slots=True)
class AuthorizedScope:
    actor_id: int
    organization_id: UUID
    project_id: int
    workspace_ids: tuple[int, ...]
    mutate: bool
    authorization_scope_digest: str


class SqlAlchemyCrossDisciplineAuthorizer:
    """Resolve scoped authority before any canonical source query."""

    def __init__(self, session: Session):
        self.session = session
        self.authorized_calls = 0
        self.source_lookup_calls = 0

    def authorize_scope(
        self, *, actor_id: int, role: str, organization_id: UUID,
        project_id: int, workspace_ids: tuple[int, ...], mutate: bool,
    ) -> AuthorizedScope:
        self.authorized_calls += 1
        project = self.session.scalar(select(Project).where(
            Project.id == project_id, Project.organization_id == organization_id,
        ).with_for_update() if mutate else select(Project).where(
            Project.id == project_id, Project.organization_id == organization_id,
        ))
        if project is None:
            raise ProtectedResourceError()
        project_mutator = role == "admin" or actor_id in {
            project.owner_id, project.primary_assignee_id,
        }
        if mutate and not project_mutator:
            raise ProtectedResourceError()
        if not mutate and not project_mutator:
            # Existing Project visibility is deliberately conservative here.
            raise ProtectedResourceError()
        rows = tuple(self.session.scalars(select(EngineeringWorkspace).where(
            EngineeringWorkspace.project_id == project_id,
            EngineeringWorkspace.id.in_(workspace_ids),
        ).order_by(EngineeringWorkspace.id).with_for_update() if mutate else select(EngineeringWorkspace).where(
            EngineeringWorkspace.project_id == project_id,
            EngineeringWorkspace.id.in_(workspace_ids),
        ).order_by(EngineeringWorkspace.id)))
        if tuple(row.id for row in rows) != workspace_ids:
            raise ProtectedResourceError()
        memberships = set(self.session.execute(select(
            EngineeringWorkspaceMember.workspace_id,
        ).where(
            EngineeringWorkspaceMember.workspace_id.in_(workspace_ids),
            EngineeringWorkspaceMember.user_id == actor_id,
        )).scalars())
        for row in rows:
            is_mutator = role == "admin" or actor_id in {row.owner_id, row.primary_assignee_id}
            if mutate and not is_mutator:
                raise ProtectedResourceError()
            if not mutate and not (is_mutator or row.id in memberships):
                raise ProtectedResourceError()
        return AuthorizedScope(
            actor_id, organization_id, project_id, workspace_ids, mutate,
            digest({
                "actor_id": actor_id, "organization_id": organization_id,
                "project_id": project_id, "workspace_ids": workspace_ids,
                "mutate": mutate,
            }, "satco:xdi-authorized-scope:v1"),
        )

    def project_and_workspaces(self, scope: AuthorizedScope):
        if self.authorized_calls < 1:
            raise RuntimeError("authorization must precede source lookup")
        self.source_lookup_calls += 1
        project = self.session.get(Project, scope.project_id)
        workspaces = tuple(self.session.scalars(select(EngineeringWorkspace).where(
            EngineeringWorkspace.id.in_(scope.workspace_ids),
        ).order_by(EngineeringWorkspace.id)))
        if project is None or project.organization_id != scope.organization_id:
            raise ProtectedResourceError()
        return project, workspaces


def validate_scope_shape(workspace_ids: tuple[int, ...]) -> None:
    if (
        not workspace_ids
        or len(workspace_ids) > 12
        or tuple(sorted(set(workspace_ids))) != workspace_ids
        or any(value < 1 for value in workspace_ids)
    ):
        raise ValueError("invalid_scope")
