"""Authorization-first source projection foundation for PATCH-053 Batch 1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.discipline_packages.cross_discipline.canonical import digest
from app.discipline_packages.cross_discipline.contracts import (
    BATCH_TWO_PROJECTION_IDS, parse_batch_two_selector,
)
from app.discipline_packages.cross_discipline.definitions.eic_v1 import BATCH_THREE_PROJECTION_IDS
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


@dataclass(frozen=True, slots=True)
class BatchTwoProjection:
    """Minimal immutable E↔I projection envelope; never a source-of-truth copy."""
    projection_id: str
    owner_kind: str
    owner_id: str
    owner_revision: str
    values: tuple[tuple[str, Any], ...]
    context_binding_ids: tuple[str, ...]
    evidence_binding_ids: tuple[str, ...]
    complete: bool
    authorization_scope_digest: str
    observed_at: datetime
    projection_digest: str


def build_batch_two_projection(*, authorized: AuthorizedScope, projection_id: str,
                               owner_kind: str, owner_id: str, owner_revision: str,
                               values: tuple[tuple[str, Any], ...],
                               context_binding_ids: tuple[str, ...] = (),
                               evidence_binding_ids: tuple[str, ...] = (),
                               complete: bool, observed_at: datetime) -> BatchTwoProjection:
    """Create a digestible minimal projection after authorization has completed."""
    if projection_id not in BATCH_TWO_PROJECTION_IDS or owner_kind not in {"engineering_object", "interface_commitment"}:
        raise ValueError("invalid_request")
    if not owner_id or not owner_revision or observed_at.tzinfo is None:
        raise ValueError("invalid_request")
    if tuple(sorted(values, key=lambda item: item[0])) != values or len({key for key, _ in values}) != len(values):
        raise ValueError("invalid_request")
    body = {
        "projection_id": projection_id, "owner_kind": owner_kind, "owner_id": owner_id,
        "owner_revision": owner_revision, "values": values,
        "context_binding_ids": tuple(sorted(context_binding_ids)),
        "evidence_binding_ids": tuple(sorted(evidence_binding_ids)), "complete": complete,
        "authorization_scope_digest": authorized.authorization_scope_digest,
        "observed_at": observed_at,
    }
    return BatchTwoProjection(**body, projection_digest=digest(body, "satco:xdi-projection:v1"))


def validate_batch_two_selectors(*, authorized: AuthorizedScope, selectors: tuple[str, ...]) -> tuple[tuple[str, str, str, str], ...]:
    """Closed parsing occurs only after scope authorization; no source resolution happens here."""
    if not authorized.workspace_ids:
        raise ValueError("invalid_request")
    parsed = tuple(parse_batch_two_selector(value) for value in selectors)
    if tuple(sorted(parsed, key=lambda item: (
        item[0], item[1], UUID(item[2]).bytes, item[3],
    ))) != parsed:
        raise ValueError("invalid_request")
    claims = {(source_kind, canonical_id, role) for _, source_kind, canonical_id, role in parsed}
    if len(claims) != len(parsed):
        raise ValueError("invalid_request")
    return parsed


@dataclass(frozen=True, slots=True)
class BatchThreeProjection:
    """Minimal immutable I↔C projection; authorization always precedes construction."""
    projection_id: str
    owner_kind: str
    owner_id: str
    owner_revision: str
    values: tuple[tuple[str, Any], ...]
    context_binding_ids: tuple[str, ...]
    evidence_binding_ids: tuple[str, ...]
    complete: bool
    authorization_scope_digest: str
    observed_at: datetime
    projection_digest: str


def build_batch_three_projection(*, authorized: AuthorizedScope, projection_id: str,
                                 owner_kind: str, owner_id: str, owner_revision: str,
                                 values: tuple[tuple[str, Any], ...],
                                 context_binding_ids: tuple[str, ...] = (),
                                 evidence_binding_ids: tuple[str, ...] = (),
                                 complete: bool, observed_at: datetime) -> BatchThreeProjection:
    if projection_id not in BATCH_THREE_PROJECTION_IDS or owner_kind not in {"engineering_object", "interface_commitment"}:
        raise ValueError("invalid_request")
    if not authorized.workspace_ids or not owner_id or not owner_revision or observed_at.tzinfo is None:
        raise ValueError("invalid_request")
    if tuple(sorted(values, key=lambda item: item[0])) != values or len({key for key, _ in values}) != len(values):
        raise ValueError("invalid_request")
    body = {
        "projection_id": projection_id, "owner_kind": owner_kind, "owner_id": owner_id,
        "owner_revision": owner_revision, "values": values,
        "context_binding_ids": tuple(sorted(context_binding_ids)),
        "evidence_binding_ids": tuple(sorted(evidence_binding_ids)), "complete": complete,
        "authorization_scope_digest": authorized.authorization_scope_digest,
        "observed_at": observed_at,
    }
    return BatchThreeProjection(**body, projection_digest=digest(body, "satco:xdi-projection:v1"))


def validate_batch_three_selectors(*, authorized: AuthorizedScope, selectors: tuple[str, ...]) -> tuple[tuple[str, str, str, str], ...]:
    """Parse I↔C selectors after full scope authorization, without source lookup."""
    if not authorized.workspace_ids:
        raise ValueError("invalid_request")
    parsed = []
    for value in selectors:
        if not isinstance(value, str) or any(character.isspace() for character in value):
            raise ValueError("invalid_request")
        parts = value.split("/")
        if len(parts) != 5 or parts[0] != "xdi.sel.v1":
            raise ValueError("invalid_request")
        _, discipline, source_kind, canonical_id, role = parts
        if discipline not in {"instrumentation", "control_automation"} or source_kind != "engineering_object":
            raise ValueError("invalid_request")
        if role not in {"signal_endpoint", "valve", "io_channel", "controller", "commitment"}:
            raise ValueError("invalid_request")
        try:
            if str(UUID(canonical_id)) != canonical_id:
                raise ValueError("invalid_request")
        except ValueError as error:
            raise ValueError("invalid_request") from error
        parsed.append((discipline, source_kind, canonical_id, role))
    ordered = tuple(sorted(parsed, key=lambda item: (item[0], item[1], UUID(item[2]).bytes, item[3])))
    if tuple(parsed) != ordered or len({(kind, identifier, role) for _, kind, identifier, role in parsed}) != len(parsed):
        raise ValueError("invalid_request")
    return ordered
