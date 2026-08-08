"""Inward-owned ports for Engineering Experience Capture."""

from typing import Mapping, Protocol
from uuid import UUID

from app.enums.engineering_experience_capture import (
    EngineeringExperienceCaptureLifecycle,
    EngineeringExperienceSourceKind,
)
from app.models.engineering_experience_capture import EngineeringExperienceCapture
from app.models.engineering_experience_capture_command import (
    EngineeringExperienceCaptureActor,
    EngineeringExperienceCaptureEvent,
    EngineeringExperienceCaptureOutcome,
    EngineeringExperienceCaptureResult,
)
from app.schemas.engineering_experience_capture import (
    EngineeringExperienceCaptureReadPage,
)


class EngineeringExperienceCaptureRepository(Protocol):
    def add(self, capture: EngineeringExperienceCapture) -> None: ...
    def get_scoped(self, capture_id: UUID, organization_id: UUID) -> EngineeringExperienceCapture | None: ...
    def list_project_scoped(self, **values) -> tuple[list[EngineeringExperienceCapture], int]: ...
    def list_workspace_scoped(self, **values) -> tuple[list[EngineeringExperienceCapture], int]: ...
    def persist_expected_version(self, capture: EngineeringExperienceCapture, expected_version: int) -> bool: ...
    def replacement_is_used(self, replacement_capture_id: UUID) -> bool: ...
    def predecessor_chain(self, capture_id: UUID, *, maximum_depth: int) -> tuple[EngineeringExperienceCapture, ...]: ...
    def read_authorized_page(
        self,
        *,
        organization_id: UUID,
        project_id: int,
        workspace_id: int | None,
        engineering_object_id: UUID | None,
        lifecycle: EngineeringExperienceCaptureLifecycle,
        source_kind: EngineeringExperienceSourceKind | None,
        discipline: str | None,
        page: int,
        size: int,
        authorized_workspace_ids: tuple[int, ...] | None,
    ) -> EngineeringExperienceCaptureReadPage: ...


class CaptureAuthorizationPolicy(Protocol):
    def authorize(self, **values) -> bool: ...


class CaptureContextValidator(Protocol):
    def validate(self, **values) -> Mapping[str, object]: ...


class CaptureSupersessionValidator(Protocol):
    def validate(self, **values) -> EngineeringExperienceCapture: ...


class CaptureAuditRecorder(Protocol):
    def record(self, **values) -> None: ...


class CaptureDomainEventRecorder(Protocol):
    def record(self, events: tuple[EngineeringExperienceCaptureEvent, ...]) -> None: ...


class CaptureIdempotencyStore(Protocol):
    def find(self, **values) -> EngineeringExperienceCaptureOutcome | None: ...
    def reserve(self, **values) -> None: ...
    def record_result(self, result: EngineeringExperienceCaptureResult, authorized_state: Mapping) -> None: ...


class EngineeringExperienceCaptureUnitOfWork(Protocol):
    captures: EngineeringExperienceCaptureRepository
    audit: CaptureAuditRecorder
    domain_events: CaptureDomainEventRecorder
    idempotency: CaptureIdempotencyStore

    def __enter__(self): ...
    def __exit__(self, exc_type, exc_value, traceback): ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


class CaptureClock(Protocol):
    def now(self): ...
