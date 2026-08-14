"""Pure PATCH-034 Organizational Memory Aggregate Root."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID, uuid4

from app.enums.organizational_memory import MemoryEventType, MemoryStanding
from app.exceptions.organizational_memory import (
    OrganizationalMemoryInvalidLineage,
    OrganizationalMemoryInvalidStanding,
    OrganizationalMemoryValidationError,
    OrganizationalMemoryVersionConflict,
)
from app.models.organizational_memory_command import (
    AcceptedReportSource,
    AdmittedReportProjectionV1,
    MemoryDomainEvent,
    MemorySourceManifestV1,
    MemoryStandingHistoryRecord,
    _audience,
    _aware,
    _nonnegative,
    _positive,
    _restrictions,
    _text,
    _uuid,
    verify_projection_manifest,
)


@dataclass(frozen=True, slots=True)
class OrganizationalMemory:
    id: UUID
    organization_id: UUID
    workspace_id: int
    project_id: int | None
    version: int
    standing: MemoryStanding
    source: AcceptedReportSource
    projection: AdmittedReportProjectionV1
    manifest: MemorySourceManifestV1
    admitted_by_id: int
    admitted_at: datetime
    admission_rationale: str
    audience_actor_ids: tuple[int, ...]
    reuse_restrictions: tuple[str, ...]
    predecessor_memory_id: UUID | None
    withdrawn_by_id: int | None
    withdrawn_at: datetime | None
    withdrawal_reason: str | None
    superseded_by_id: int | None
    superseded_at: datetime | None
    supersession_reason: str | None
    replacement_memory_id: UUID | None
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        _uuid(self.id, "id"); _uuid(self.organization_id, "organization_id")
        _positive(self.workspace_id, "workspace_id"); _positive(self.version, "version")
        if self.project_id is not None: _positive(self.project_id, "project_id")
        object.__setattr__(self, "standing", MemoryStanding(self.standing))
        if not isinstance(self.source, AcceptedReportSource) or not isinstance(self.projection, AdmittedReportProjectionV1) or not isinstance(self.manifest, MemorySourceManifestV1):
            raise OrganizationalMemoryValidationError("memory source/projection/manifest contract is invalid")
        verify_projection_manifest(self.projection, self.manifest)
        if self.organization_id != self.projection.organization_id or self.workspace_id != self.projection.workspace_id or self.project_id != self.projection.project_id:
            raise OrganizationalMemoryValidationError("memory scope must equal the accepted projection scope")
        if self.source != self.manifest.source:
            raise OrganizationalMemoryValidationError("memory source must equal manifest source")
        _positive(self.admitted_by_id, "admitted_by_id"); _aware(self.admitted_at, "admitted_at")
        object.__setattr__(self, "admission_rationale", _text(self.admission_rationale, "admission_rationale", 2000))
        object.__setattr__(self, "audience_actor_ids", _audience(self.audience_actor_ids))
        object.__setattr__(self, "reuse_restrictions", _restrictions(self.reuse_restrictions))
        if self.predecessor_memory_id is not None:
            _uuid(self.predecessor_memory_id, "predecessor_memory_id")
            if self.predecessor_memory_id == self.id: raise OrganizationalMemoryInvalidLineage()
        _aware(self.created_at, "created_at"); _aware(self.updated_at, "updated_at")
        if self.updated_at < self.created_at or self.admitted_at != self.created_at:
            raise OrganizationalMemoryValidationError("memory timestamps are incoherent")
        self._validate_standing_shape()

    def _validate_standing_shape(self) -> None:
        withdrawn = (self.withdrawn_by_id, self.withdrawn_at, self.withdrawal_reason)
        superseded = (self.superseded_by_id, self.superseded_at, self.supersession_reason, self.replacement_memory_id)
        if self.standing is MemoryStanding.ACTIVE:
            if any(value is not None for value in withdrawn + superseded): raise OrganizationalMemoryValidationError("active memory has terminal fields")
        elif self.standing is MemoryStanding.WITHDRAWN:
            if any(value is None for value in withdrawn) or any(value is not None for value in superseded): raise OrganizationalMemoryValidationError("withdrawn memory shape is incoherent")
            _positive(self.withdrawn_by_id, "withdrawn_by_id"); _aware(self.withdrawn_at, "withdrawn_at"); _text(self.withdrawal_reason, "withdrawal_reason", 2000)
        else:
            if any(value is None for value in superseded) or any(value is not None for value in withdrawn): raise OrganizationalMemoryValidationError("superseded memory shape is incoherent")
            _positive(self.superseded_by_id, "superseded_by_id"); _aware(self.superseded_at, "superseded_at"); _text(self.supersession_reason, "supersession_reason", 2000); _uuid(self.replacement_memory_id, "replacement_memory_id")
            if self.replacement_memory_id == self.id: raise OrganizationalMemoryInvalidLineage()

    @classmethod
    def admit(
        cls, *, memory_id: UUID, projection: AdmittedReportProjectionV1,
        manifest: MemorySourceManifestV1, admitted_by_id: int, admitted_at: datetime,
        admission_rationale: str, audience_actor_ids: tuple[int, ...] = (),
        reuse_restrictions: tuple[str, ...] = (),
    ) -> "OrganizationalMemory":
        return cls._admit(
            memory_id=memory_id, projection=projection, manifest=manifest,
            admitted_by_id=admitted_by_id, admitted_at=admitted_at,
            admission_rationale=admission_rationale,
            audience_actor_ids=audience_actor_ids,
            reuse_restrictions=reuse_restrictions,
            predecessor_memory_id=None,
        )

    @classmethod
    def _admit(
        cls, *, memory_id: UUID, projection: AdmittedReportProjectionV1,
        manifest: MemorySourceManifestV1, admitted_by_id: int, admitted_at: datetime,
        admission_rationale: str, audience_actor_ids: tuple[int, ...],
        reuse_restrictions: tuple[str, ...], predecessor_memory_id: UUID | None,
    ) -> "OrganizationalMemory":
        return cls(
            id=memory_id, organization_id=projection.organization_id,
            workspace_id=projection.workspace_id, project_id=projection.project_id,
            version=1, standing=MemoryStanding.ACTIVE, source=manifest.source,
            projection=projection, manifest=manifest, admitted_by_id=admitted_by_id,
            admitted_at=admitted_at, admission_rationale=admission_rationale,
            audience_actor_ids=audience_actor_ids, reuse_restrictions=reuse_restrictions,
            predecessor_memory_id=predecessor_memory_id, withdrawn_by_id=None,
            withdrawn_at=None, withdrawal_reason=None, superseded_by_id=None,
            superseded_at=None, supersession_reason=None, replacement_memory_id=None,
            created_at=admitted_at, updated_at=admitted_at,
        )

    @classmethod
    def create_successor(
        cls, *, predecessor: "OrganizationalMemory", memory_id: UUID,
        projection: AdmittedReportProjectionV1, manifest: MemorySourceManifestV1,
        admitted_by_id: int, admitted_at: datetime, admission_rationale: str,
        audience_actor_ids: tuple[int, ...] = (), reuse_restrictions: tuple[str, ...] = (),
    ) -> "OrganizationalMemory":
        if manifest.source == predecessor.source:
            raise OrganizationalMemoryInvalidLineage("successor requires a different exact accepted source version")
        if (projection.organization_id, projection.workspace_id, projection.project_id) != (predecessor.organization_id, predecessor.workspace_id, predecessor.project_id):
            raise OrganizationalMemoryInvalidLineage("successor scope must match predecessor")
        normalized_audience = _audience(audience_actor_ids)
        if not cls._audience_not_broader(predecessor.audience_actor_ids, normalized_audience):
            raise OrganizationalMemoryInvalidLineage("successor audience cannot be broader than predecessor")
        return cls._admit(
            memory_id=memory_id, projection=projection, manifest=manifest,
            admitted_by_id=admitted_by_id, admitted_at=admitted_at,
            admission_rationale=admission_rationale,
            audience_actor_ids=normalized_audience, reuse_restrictions=reuse_restrictions,
            predecessor_memory_id=predecessor.id,
        )

    def withdraw(self, *, expected_version: int, actor_id: int, occurred_at: datetime, reason: str) -> tuple["OrganizationalMemory", MemoryStandingHistoryRecord]:
        self._require_active(expected_version); _positive(actor_id, "actor_id"); _aware(occurred_at, "occurred_at")
        if occurred_at < self.updated_at: raise OrganizationalMemoryValidationError("transition time precedes current state")
        normalized_reason = _text(reason, "reason", 2000)
        updated = replace(self, version=self.version + 1, standing=MemoryStanding.WITHDRAWN, withdrawn_by_id=actor_id, withdrawn_at=occurred_at, withdrawal_reason=normalized_reason, updated_at=occurred_at)
        return updated, self._history(updated, actor_id, occurred_at, normalized_reason, None)

    def supersede_with(self, replacement_memory: "OrganizationalMemory", *, expected_version: int, expected_replacement_version: int, actor_id: int, occurred_at: datetime, reason: str) -> tuple["OrganizationalMemory", MemoryStandingHistoryRecord]:
        self._require_active(expected_version); replacement_memory._require_active(expected_replacement_version)
        _positive(actor_id, "actor_id"); _aware(occurred_at, "occurred_at")
        if replacement_memory.id == self.id or replacement_memory.predecessor_memory_id != self.id: raise OrganizationalMemoryInvalidLineage("replacement must be the exact linked successor")
        if (replacement_memory.organization_id, replacement_memory.workspace_id, replacement_memory.project_id) != (self.organization_id, self.workspace_id, self.project_id): raise OrganizationalMemoryInvalidLineage("replacement scope must be coherent")
        if not self._audience_not_broader(self.audience_actor_ids, replacement_memory.audience_actor_ids): raise OrganizationalMemoryInvalidLineage("replacement audience cannot be broader than predecessor")
        if occurred_at < max(self.updated_at, replacement_memory.updated_at): raise OrganizationalMemoryValidationError("transition time precedes current state")
        normalized_reason = _text(reason, "reason", 2000)
        updated = replace(self, version=self.version + 1, standing=MemoryStanding.SUPERSEDED, superseded_by_id=actor_id, superseded_at=occurred_at, supersession_reason=normalized_reason, replacement_memory_id=replacement_memory.id, updated_at=occurred_at)
        return updated, self._history(updated, actor_id, occurred_at, normalized_reason, replacement_memory.id)

    def event(self, *, event_id: UUID, event_type: MemoryEventType, actor_id: int, occurred_at: datetime, command_id: UUID, correlation_id: UUID, causation_id: UUID) -> MemoryDomainEvent:
        return MemoryDomainEvent(event_id, event_type, 1, self.id, self.version, self.organization_id, self.workspace_id, self.project_id, self.standing, actor_id, occurred_at, command_id, correlation_id, causation_id, self.source.report_id, self.source.accepted_aggregate_version, self.predecessor_memory_id, self.replacement_memory_id, len(self.manifest.provenance_entries))

    def initial_history(self, *, event_id: UUID) -> MemoryStandingHistoryRecord:
        if self.version != 1 or self.standing is not MemoryStanding.ACTIVE:
            raise OrganizationalMemoryValidationError("initial history requires newly admitted active memory")
        return MemoryStandingHistoryRecord(event_id, self.id, self.organization_id, 1, None, MemoryStanding.ACTIVE, self.admitted_by_id, self.admitted_at, self.admission_rationale, None)

    def _require_active(self, expected_version: int) -> None:
        _positive(expected_version, "expected_version")
        if expected_version != self.version: raise OrganizationalMemoryVersionConflict()
        if self.standing is not MemoryStanding.ACTIVE: raise OrganizationalMemoryInvalidStanding()

    def _history(self, updated: "OrganizationalMemory", actor_id: int, occurred_at: datetime, reason: str, replacement_memory_id: UUID | None) -> MemoryStandingHistoryRecord:
        return MemoryStandingHistoryRecord(uuid4(), self.id, self.organization_id, updated.version, self.standing, updated.standing, actor_id, occurred_at, reason, replacement_memory_id)

    @staticmethod
    def _audience_not_broader(predecessor: tuple[int, ...], successor: tuple[int, ...]) -> bool:
        return not predecessor or (bool(successor) and set(successor).issubset(predecessor))
