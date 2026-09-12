"""Narrow ports for the Batch-1 standards aggregate."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID


class StandardsRepositoryPort(Protocol):
    def get_identity(self, identity_id: UUID, organization_id: UUID | None = None): ...
    def get_edition(self, edition_id: UUID): ...
    def get_current_rights(self, organization_id: UUID, edition_id: UUID, provider_id: str, *, lock: bool = False): ...


class StandardsUnitOfWorkPort(Protocol):
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
