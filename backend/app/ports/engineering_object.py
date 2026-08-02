"""Inward-owned application ports for EngineeringObject use cases.

Only contracts live in this module. Infrastructure implementations belong to
later PATCH-023 sprints.
"""

from datetime import datetime
from typing import Mapping
from typing import Protocol
from typing import Self
from uuid import UUID

from app.models.engineering_object import EngineeringObject
from app.models.engineering_object_command import AuthenticatedActor
from app.models.engineering_object_command import AuthorizationContext
from app.models.engineering_object_command import EngineeringObjectCommandResult
from app.models.engineering_object_command import EngineeringObjectDomainEvent
from app.models.engineering_object_command import EngineeringObjectIdempotencyOutcome
from app.models.engineering_object_command import Scalar
from app.enums import EngineeringDiscipline


class EngineeringObjectRepository(Protocol):
    """Persistence-only contract for authorized aggregate scope."""

    def get_authorized(
        self,
        object_id: UUID,
        organization_id: UUID,
    ) -> EngineeringObject | None:
        """Load and fully rehydrate one object inside authorized scope."""
        ...

    def list_authorized(
        self,
        *,
        organization_id: UUID,
        project_id: int,
        filters: Mapping[str, Scalar],
        page: int,
        size: int,
    ) -> tuple[list[EngineeringObject], int]:
        """Return a bounded authorized project-scoped page and total."""
        ...

    def add(self, engineering_object: EngineeringObject) -> None:
        """Stage a newly created aggregate without committing."""
        ...

    def persist_expected_version(
        self,
        engineering_object: EngineeringObject,
        expected_version: int,
    ) -> bool:
        """Stage compare-and-change persistence without committing."""
        ...


class AuditRecorder(Protocol):
    """Stage accountable Audit evidence in the active Unit of Work."""

    def record(
        self,
        *,
        command_type: str,
        actor: AuthenticatedActor,
        object_id: UUID,
        correlation_id: UUID,
        idempotency_id: UUID,
        rationale: str,
        previous_version: int | None,
        version: int,
        details: Mapping[str, Scalar],
    ) -> None:
        """Stage one bounded EngineeringObject Audit record."""
        ...


class DomainEventRecorder(Protocol):
    """Stage immutable Domain Events for durable outbox publication."""

    def record(self, events: tuple[EngineeringObjectDomainEvent, ...]) -> None:
        """Stage events without publishing or committing them."""
        ...


class IdempotencyStore(Protocol):
    """Reserve command identity and stage its authorized outcome."""

    def find(
        self,
        *,
        actor_id: int,
        command_type: str,
        idempotency_id: UUID,
        request_fingerprint: str,
    ) -> EngineeringObjectIdempotencyOutcome | None:
        """Return a matching result or reject conflicting key reuse."""
        ...

    def reserve(
        self,
        *,
        actor_id: int,
        command_type: str,
        idempotency_id: UUID,
        request_fingerprint: str,
    ) -> None:
        """Stage a unique idempotency reservation."""
        ...

    def record_result(
        self,
        result: EngineeringObjectCommandResult,
        authorized_state: Mapping[str, Scalar],
    ) -> None:
        """Stage the authorized command outcome."""
        ...


class AuthorizationPolicy(Protocol):
    """Deny-by-default, operation-specific authorization contract."""

    def authorize(
        self,
        *,
        actor: AuthenticatedActor,
        context: AuthorizationContext,
        current_state: EngineeringObject | None,
        target_state: Mapping[str, Scalar],
    ) -> bool:
        """Return an explicit decision before disclosure or mutation."""
        ...


class ReferenceValidator(Protocol):
    """Validate application-owned references without mutating aggregates."""

    def validate_creation_references(
        self,
        *,
        actor: AuthenticatedActor,
        project_id: int,
        steward_id: int | None,
        evidence_references: tuple[UUID, ...],
        discipline: EngineeringDiscipline,
    ) -> Mapping[str, Scalar]:
        """Return trusted derived creation scope and responsibility values."""
        ...

    def validate_mutation_references(
        self,
        *,
        actor: AuthenticatedActor,
        object_id: UUID,
        references: Mapping[str, Scalar],
    ) -> None:
        """Validate command-specific target and Evidence references."""
        ...


class Clock(Protocol):
    """Controlled source of timezone-aware application time."""

    def now(self) -> datetime:
        """Return the current timezone-aware instant."""
        ...


class UnitOfWork(Protocol):
    """Single transaction boundary for all successful mutation outcomes."""

    engineering_objects: EngineeringObjectRepository
    audit: AuditRecorder
    domain_events: DomainEventRecorder
    idempotency: IdempotencyStore

    def __enter__(self) -> Self:
        """Begin one transaction and return this Unit of Work."""
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> bool | None:
        """Roll back an uncommitted transaction on scope exit."""
        ...

    def commit(self) -> None:
        """Commit all staged aggregate, Audit, event, and idempotency writes."""
        ...

    def rollback(self) -> None:
        """Roll back every staged write in the transaction."""
        ...
