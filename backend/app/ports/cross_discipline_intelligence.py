"""Ports that keep owner authority and transaction control outside the kernel."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from app.discipline_packages.cross_discipline.contracts import (
    CompletenessAttestationV1, SourceProjectionV1,
)


class ProtectedResourceError(PermissionError):
    """Collapsed authorization/existence failure; carries no target detail."""


class AuthorizationChanged(ProtectedResourceError):
    pass


class CrossDisciplineAuthorizer(Protocol):
    def authorize_project(self, *, actor_id: int, organization_id: UUID, project_id: int, mutate: bool) -> None: ...
    def authorize_workspaces(self, *, actor_id: int, organization_id: UUID, project_id: int, workspace_ids: tuple[int, ...], mutate: bool) -> None: ...
    def authorize_recorded_sources(self, *, actor_id: int, organization_id: UUID, project_id: int, assessment_id: UUID) -> None: ...


class CrossDisciplineSourceReader(Protocol):
    def project_state(self, *, organization_id: UUID, project_id: int) -> str: ...
    def project_configuration(self, *, organization_id: UUID, project_id: int) -> dict[str, Any]: ...
    def projections(self, *, organization_id: UUID, project_id: int, workspace_ids: tuple[int, ...]) -> tuple[SourceProjectionV1, ...]: ...
    def attestations(self, *, organization_id: UUID, project_id: int, workspace_ids: tuple[int, ...]) -> tuple[CompletenessAttestationV1, ...]: ...
    def recheck(self, *, projections: tuple[SourceProjectionV1, ...], configuration: dict[str, Any]) -> bool: ...


class CrossDisciplineClock(Protocol):
    def now(self) -> datetime: ...


class ProjectControlImpactHandoff(Protocol):
    def create_potential(self, *, project_id: int, workspace_id: int | None, change_id: UUID,
                         change_version: int, target_kind: str, target_id: UUID,
                         rationale: str, idempotency_key: UUID): ...


class CrossDisciplineAIExplainer(Protocol):
    def explain(self, findings: tuple[dict, ...]): ...


class CrossDisciplineRepositoryPort(Protocol):
    def get_assessment(self, assessment_id: UUID, organization_id: UUID, project_id: int, *, lock: bool = False): ...
    def get_idempotency(self, *, organization_id: UUID, project_id: int, actor_id: int, operation: str, idempotency_key: UUID, lock: bool = False): ...
    def add(self, row: Any) -> None: ...


class CrossDisciplineUnitOfWorkPort(Protocol):
    repository: CrossDisciplineRepositoryPort
    def __enter__(self): ...
    def __exit__(self, exc_type, exc, traceback): ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
