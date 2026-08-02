"""Inward-owned interface-only ports for PATCH-026 Sprint-1."""

from typing import Mapping, Protocol
from uuid import UUID

from app.enums import RelationshipFamily, RelationshipType
from app.models.engineering_relationship import EngineeringRelationship
from app.models.engineering_relationship_command import (
    AuthenticatedRelationshipActor,
    RelationshipAuthorizationContext,
    RelationshipValidationResult,
    Scalar,
    EngineeringRelationshipCommandResult,
    EngineeringRelationshipDomainEvent,
    EngineeringRelationshipIdempotencyOutcome,
)


class EngineeringRelationshipRepository(Protocol):
    """Persistence contract; implementations must not authorize or commit."""

    def get_authorized(
        self, relationship_id: UUID, organization_id: UUID
    ) -> EngineeringRelationship | None: ...

    def add(self, relationship: EngineeringRelationship) -> None: ...

    def persist_expected_version(
        self, relationship: EngineeringRelationship, expected_version: int
    ) -> bool: ...

    def active_duplicate_exists(
        self, *, organization_id: UUID, project_id: int, workspace_id: int,
        source_object_id: UUID, target_object_id: UUID,
        relationship_family: RelationshipFamily,
        relationship_type: RelationshipType,
    ) -> bool: ...

    def creates_cycle(
        self, *, organization_id: UUID, project_id: int,
        source_object_id: UUID, target_object_id: UUID,
        relationship_family: RelationshipFamily,
        relationship_type: RelationshipType,
    ) -> bool: ...

    def list_for_endpoint(self, *, organization_id: UUID, object_id: UUID,
                          filters: Mapping, page: int, size: int): ...

    def bounded_neighborhood(self, *, organization_id: UUID, object_id: UUID,
                             filters: Mapping, max_depth: int,
                             max_results: int): ...

    def bounded_path(self, *, organization_id: UUID, source_object_id: UUID,
                     target_object_id: UUID, filters: Mapping, max_depth: int,
                     max_results: int): ...


class RelationshipPolicy(Protocol):
    """Deny-by-default operation and visibility policy."""

    def authorize(
        self, *, actor: AuthenticatedRelationshipActor,
        context: RelationshipAuthorizationContext,
        current_state: EngineeringRelationship | None,
        target_state: Mapping[str, Scalar],
    ) -> bool: ...


class RelationshipValidator(Protocol):
    """Validate endpoints, scope, Evidence, roles, duplicates, and cycles."""

    def validate_creation(
        self, *, actor: AuthenticatedRelationshipActor,
        source_object_id: UUID, target_object_id: UUID,
        relationship_family: RelationshipFamily,
        relationship_type: RelationshipType,
        steward_id: int | None, evidence_references: tuple[UUID, ...],
    ) -> RelationshipValidationResult: ...

    def validate_mutation(
        self, *, actor: AuthenticatedRelationshipActor,
        relationship_id: UUID, references: Mapping[str, Scalar],
    ) -> None: ...


class AuditRecorder(Protocol):
    def record(self, **values) -> None: ...


class DomainEventRecorder(Protocol):
    def record(
        self, events: tuple[EngineeringRelationshipDomainEvent, ...]
    ) -> None: ...


class IdempotencyStore(Protocol):
    def find(self, **values) -> EngineeringRelationshipIdempotencyOutcome | None: ...
    def reserve(self, **values) -> None: ...
    def record_result(
        self, result: EngineeringRelationshipCommandResult,
        authorized_state: Mapping[str, object],
    ) -> None: ...


class EngineeringRelationshipUnitOfWork(Protocol):
    engineering_relationships: EngineeringRelationshipRepository
    audit: AuditRecorder
    domain_events: DomainEventRecorder
    idempotency: IdempotencyStore
    def __enter__(self): ...
    def __exit__(self, exc_type, exc_value, traceback): ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


class Clock(Protocol):
    def now(self): ...
