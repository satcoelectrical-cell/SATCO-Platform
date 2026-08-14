"""Persistence-independent PATCH-034 Organizational Memory contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import unicodedata
from typing import Literal, TypeAlias
from uuid import UUID

from app.enums.organizational_memory import (
    IDEMPOTENCY_RESULT_TYPES,
    MemoryEventType,
    MemoryOperation,
    MemoryProvenanceOperation,
    MemoryRejectionReason,
    MemoryStanding,
)
from app.enums.technical_report import (
    TechnicalReportOwningCapability,
    TechnicalReportPurpose,
    TechnicalReportSourceClass,
    TechnicalReportSourceType,
)
from app.exceptions.organizational_memory import (
    OrganizationalMemoryIntegrityError,
    OrganizationalMemoryValidationError,
)
from app.models.technical_report_command import TechnicalReportAcceptedSnapshot


PROJECTION_CONTRACT = "organizational_memory.accepted_report.v1"
SHA256 = "sha256"
MAX_PROJECTION_BYTES = 256 * 1024
MAX_MANIFEST_BYTES = 128 * 1024
MAX_STORED_RESULT_BYTES = 1024


def _positive(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise OrganizationalMemoryValidationError(f"{name} must be a positive integer")
    return value


def _nonnegative(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise OrganizationalMemoryValidationError(f"{name} must be a non-negative integer")
    return value


def _uuid(value: object, name: str) -> UUID:
    if not isinstance(value, UUID):
        raise OrganizationalMemoryValidationError(f"{name} must be a UUID")
    return value


def _aware(value: object, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
        raise OrganizationalMemoryValidationError(f"{name} must be timezone-aware UTC")
    return value


def _sha256(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower() or any(c not in "0123456789abcdef" for c in value):
        raise OrganizationalMemoryValidationError(f"{name} must be lowercase SHA-256")
    return value


def _text(value: object, name: str, maximum: int, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise OrganizationalMemoryValidationError(f"{name} must be text")
    normalized = unicodedata.normalize("NFC", value.strip())
    if (not normalized and not allow_empty) or len(normalized) > maximum:
        raise OrganizationalMemoryValidationError(f"{name} is outside its accepted bounds")
    if any(ord(c) < 32 and c not in "\n\t" for c in normalized):
        raise OrganizationalMemoryValidationError(f"{name} contains a prohibited control character")
    return normalized


def _exact_text(value: object, name: str) -> str:
    if (
        not isinstance(value, str) or not value or len(value) > 10000
        or unicodedata.normalize("NFC", value) != value or value.strip() != value
        or any(ord(c) < 32 and c not in "\n\t" for c in value)
    ):
        raise OrganizationalMemoryValidationError(f"{name} must be canonical source text")
    return value


def _canonical_value(value: object) -> object:
    if is_dataclass(value):
        return {field.name: _canonical_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        _aware(value, "datetime")
        return value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if isinstance(value, tuple):
        return [_canonical_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _canonical_value(item) for key, item in value.items()}
    if isinstance(value, float):
        raise OrganizationalMemoryValidationError("floats are prohibited in canonical JSON")
    return value


def canonical_json(value: object) -> bytes:
    try:
        return json.dumps(
            _canonical_value(value), ensure_ascii=False, allow_nan=False,
            sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise OrganizationalMemoryValidationError("value is not canonically serializable") from exc


def canonical_digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


@dataclass(frozen=True, slots=True)
class MemoryActor:
    actor_id: int
    organization_id: UUID

    def __post_init__(self) -> None:
        _positive(self.actor_id, "actor_id")
        _uuid(self.organization_id, "organization_id")


@dataclass(frozen=True, slots=True)
class MemoryScope:
    organization_id: UUID
    workspace_id: int
    project_id: int | None

    def __post_init__(self) -> None:
        _uuid(self.organization_id, "organization_id")
        _positive(self.workspace_id, "workspace_id")
        if self.project_id is not None:
            _positive(self.project_id, "project_id")


@dataclass(frozen=True, slots=True)
class MemoryId:
    value: UUID

    def __post_init__(self) -> None:
        _uuid(self.value, "value")


@dataclass(frozen=True, slots=True)
class MemoryVersion:
    value: int

    def __post_init__(self) -> None:
        _positive(self.value, "value")


@dataclass(frozen=True, slots=True)
class AcceptedReportSource:
    report_id: UUID
    accepted_aggregate_version: int
    accepted_snapshot_digest: str

    def __post_init__(self) -> None:
        _uuid(self.report_id, "report_id")
        _positive(self.accepted_aggregate_version, "accepted_aggregate_version")
        _sha256(self.accepted_snapshot_digest, "accepted_snapshot_digest")


@dataclass(frozen=True, slots=True)
class AdmittedTechnicalContentV1:
    engineering_scope: str
    technical_content: str
    assumptions: tuple[str, ...]
    uncertainty: str
    limitations: tuple[str, ...]
    conclusions: str
    recommendations: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("engineering_scope", "technical_content", "uncertainty", "conclusions"):
            _exact_text(getattr(self, name), name)
        for name in ("assumptions", "limitations", "recommendations"):
            value = getattr(self, name)
            if not isinstance(value, tuple):
                raise OrganizationalMemoryValidationError(f"{name} must be a tuple")
            for item in value:
                _exact_text(item, name)


@dataclass(frozen=True, slots=True)
class AdmittedQualificationV1:
    is_preliminary: bool
    evidence_deficiencies: tuple[str, ...]
    unresolved_issues: tuple[str, ...]
    follow_up_requirements: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.is_preliminary) is not bool:
            raise OrganizationalMemoryValidationError("is_preliminary must be boolean")
        for name in ("evidence_deficiencies", "unresolved_issues", "follow_up_requirements"):
            value = getattr(self, name)
            if not isinstance(value, tuple):
                raise OrganizationalMemoryValidationError(f"{name} must be a tuple")
            for item in value:
                _exact_text(item, name)
        if self.is_preliminary != any((self.evidence_deficiencies, self.unresolved_issues, self.follow_up_requirements)):
            raise OrganizationalMemoryValidationError("admitted qualification is incoherent")


@dataclass(frozen=True, slots=True)
class AdmittedReportProjectionV1:
    projection_contract: Literal["organizational_memory.accepted_report.v1"]
    report_id: UUID
    purpose: TechnicalReportPurpose
    organization_id: UUID
    workspace_id: int
    project_id: int | None
    content: AdmittedTechnicalContentV1
    qualification: AdmittedQualificationV1
    accepted_draft_revision_id: UUID
    accepted_draft_revision_number: int
    accepted_aggregate_version: int
    accepted_by_id: int
    accepted_at: datetime
    predecessor_report_id: UUID | None

    def __post_init__(self) -> None:
        if self.projection_contract != PROJECTION_CONTRACT:
            raise OrganizationalMemoryValidationError("invalid projection contract")
        for name in ("report_id", "organization_id", "accepted_draft_revision_id"):
            _uuid(getattr(self, name), name)
        if self.predecessor_report_id is not None:
            _uuid(self.predecessor_report_id, "predecessor_report_id")
        object.__setattr__(self, "purpose", TechnicalReportPurpose(self.purpose))
        for name in ("workspace_id", "accepted_draft_revision_number", "accepted_aggregate_version", "accepted_by_id"):
            _positive(getattr(self, name), name)
        if self.project_id is not None:
            _positive(self.project_id, "project_id")
        if not isinstance(self.content, AdmittedTechnicalContentV1) or not isinstance(self.qualification, AdmittedQualificationV1):
            raise OrganizationalMemoryValidationError("projection content contract is invalid")
        _aware(self.accepted_at, "accepted_at")
        if len(canonical_json(self)) > MAX_PROJECTION_BYTES:
            raise OrganizationalMemoryValidationError("admitted projection exceeds 256 KiB")

    @classmethod
    def from_accepted_snapshot(cls, snapshot: TechnicalReportAcceptedSnapshot) -> "AdmittedReportProjectionV1":
        if not isinstance(snapshot, TechnicalReportAcceptedSnapshot):
            raise OrganizationalMemoryValidationError("accepted snapshot contract is required")
        projection = cls(
            projection_contract=PROJECTION_CONTRACT,
            report_id=snapshot.report_id,
            purpose=snapshot.purpose,
            organization_id=snapshot.organization_id,
            workspace_id=snapshot.workspace_id,
            project_id=snapshot.project_id,
            content=AdmittedTechnicalContentV1(**asdict(snapshot.content)),
            qualification=AdmittedQualificationV1(**asdict(snapshot.qualification)),
            accepted_draft_revision_id=snapshot.accepted_draft_revision.revision_id,
            accepted_draft_revision_number=snapshot.accepted_draft_revision.revision_number,
            accepted_aggregate_version=snapshot.accepted_aggregate_version,
            accepted_by_id=snapshot.accepted_by_id,
            accepted_at=snapshot.accepted_at,
            predecessor_report_id=snapshot.predecessor_report_id,
        )
        if canonical_digest(snapshot) != snapshot.integrity_digest:
            raise OrganizationalMemoryIntegrityError()
        return projection


@dataclass(frozen=True, slots=True)
class MemoryProvenanceDigestEntry:
    entry_id: UUID
    ordinal: int
    source_class: TechnicalReportSourceClass
    source_type: str
    owning_capability: str
    is_material: bool
    reliance_role: str
    locator_digest: str
    source_integrity_algorithm: Literal["sha256"]
    source_integrity_digest: str

    def __post_init__(self) -> None:
        _uuid(self.entry_id, "entry_id")
        _nonnegative(self.ordinal, "ordinal")
        object.__setattr__(self, "source_class", TechnicalReportSourceClass(self.source_class))
        if self.source_class is not TechnicalReportSourceClass.CANONICAL_MATERIAL:
            raise OrganizationalMemoryValidationError("V1 provenance source class must be canonical material")
        source_type = TechnicalReportSourceType(self.source_type)
        owner = TechnicalReportOwningCapability(self.owning_capability)
        expected = {
            TechnicalReportSourceType.UNIVERSAL_CAPTURE: TechnicalReportOwningCapability.UNIVERSAL_CAPTURE,
            TechnicalReportSourceType.EVIDENCE: TechnicalReportOwningCapability.EVIDENCE,
            TechnicalReportSourceType.ENGINEERING_OBJECT: TechnicalReportOwningCapability.ENGINEERING_OBJECT,
            TechnicalReportSourceType.ENGINEERING_RELATIONSHIP: TechnicalReportOwningCapability.ENGINEERING_RELATIONSHIP,
        }
        if expected.get(source_type) is not owner:
            raise OrganizationalMemoryValidationError("V1 provenance source/owner is incoherent")
        object.__setattr__(self, "source_type", source_type.value); object.__setattr__(self, "owning_capability", owner.value)
        normalized_role = _text(self.reliance_role, "reliance_role", 2000)
        if normalized_role != self.reliance_role: raise OrganizationalMemoryValidationError("reliance_role must already be normalized")
        if type(self.is_material) is not bool or not self.is_material:
            raise OrganizationalMemoryValidationError("V1 provenance must be material")
        if self.source_integrity_algorithm != SHA256:
            raise OrganizationalMemoryValidationError("source integrity algorithm must be sha256")
        _sha256(self.locator_digest, "locator_digest")
        _sha256(self.source_integrity_digest, "source_integrity_digest")


@dataclass(frozen=True, slots=True)
class MemorySourceManifestV1:
    source: AcceptedReportSource
    source_snapshot_digest: str
    projection_contract: Literal["organizational_memory.accepted_report.v1"]
    admitted_projection_digest: str
    provenance_digest: str
    provenance_entries: tuple[MemoryProvenanceDigestEntry, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.source, AcceptedReportSource) or self.projection_contract != PROJECTION_CONTRACT:
            raise OrganizationalMemoryValidationError("manifest source/projection contract is invalid")
        for name in ("source_snapshot_digest", "admitted_projection_digest", "provenance_digest"):
            _sha256(getattr(self, name), name)
        if self.source_snapshot_digest != self.source.accepted_snapshot_digest:
            raise OrganizationalMemoryIntegrityError("source snapshot digest mismatch")
        if not 1 <= len(self.provenance_entries) <= 256:
            raise OrganizationalMemoryValidationError("provenance entry count must be 1..256")
        if [entry.ordinal for entry in self.provenance_entries] != list(range(len(self.provenance_entries))):
            raise OrganizationalMemoryValidationError("provenance ordinals must be contiguous")
        if self.provenance_digest != canonical_digest(self.provenance_entries):
            raise OrganizationalMemoryIntegrityError("provenance digest mismatch")
        if len(canonical_json(self)) > MAX_MANIFEST_BYTES:
            raise OrganizationalMemoryValidationError("source manifest exceeds 128 KiB")


def verify_projection_manifest(projection: AdmittedReportProjectionV1, manifest: MemorySourceManifestV1) -> None:
    if projection.report_id != manifest.source.report_id or projection.accepted_aggregate_version != manifest.source.accepted_aggregate_version:
        raise OrganizationalMemoryIntegrityError("source identity/version mismatch")
    if canonical_digest(projection) != manifest.admitted_projection_digest:
        raise OrganizationalMemoryIntegrityError("admitted projection digest mismatch")


def admission_material_from_snapshot(
    snapshot: TechnicalReportAcceptedSnapshot,
) -> tuple[AdmittedReportProjectionV1, MemorySourceManifestV1]:
    """Copy one exact accepted snapshot into the closed, non-transformative V1 projection."""

    projection = AdmittedReportProjectionV1.from_accepted_snapshot(snapshot)
    entries: list[MemoryProvenanceDigestEntry] = []
    for entry in snapshot.provenance:
        if entry.source_class is not TechnicalReportSourceClass.CANONICAL_MATERIAL or entry.owning_capability is None:
            raise OrganizationalMemoryValidationError("unsupported provenance makes the report ineligible for V1 admission")
        entries.append(MemoryProvenanceDigestEntry(
            entry_id=entry.entry_id,
            ordinal=entry.ordinal,
            source_class=entry.source_class,
            source_type=entry.source_type.value,
            owning_capability=entry.owning_capability.value,
            is_material=entry.is_material,
            reliance_role=entry.reliance_role,
            locator_digest=canonical_digest(entry.locator),
            source_integrity_algorithm="sha256",
            source_integrity_digest=entry.integrity_digest or "",
        ))
    provenance_entries = tuple(entries)
    source = AcceptedReportSource(snapshot.report_id, snapshot.accepted_aggregate_version, snapshot.integrity_digest)
    manifest = MemorySourceManifestV1(
        source=source,
        source_snapshot_digest=snapshot.integrity_digest,
        projection_contract=PROJECTION_CONTRACT,
        admitted_projection_digest=canonical_digest(projection),
        provenance_digest=canonical_digest(provenance_entries),
        provenance_entries=provenance_entries,
    )
    verify_projection_manifest(projection, manifest)
    return projection, manifest


@dataclass(frozen=True, slots=True)
class MemoryCommandMetadata:
    actor: MemoryActor
    correlation_id: UUID
    command_id: UUID
    idempotency_id: UUID
    rationale: str

    def __post_init__(self) -> None:
        if not isinstance(self.actor, MemoryActor):
            raise OrganizationalMemoryValidationError("actor contract is invalid")
        for name in ("correlation_id", "command_id", "idempotency_id"):
            _uuid(getattr(self, name), name)
        object.__setattr__(self, "rationale", _text(self.rationale, "rationale", 2000))


def _audience(values: tuple[int, ...]) -> tuple[int, ...]:
    if not isinstance(values, tuple) or len(values) > 100:
        raise OrganizationalMemoryValidationError("audience must be a tuple of at most 100 actors")
    if any(_positive(item, "audience_actor_id") != item for item in values) or tuple(sorted(set(values))) != values:
        raise OrganizationalMemoryValidationError("audience actor IDs must be unique and sorted")
    return values


def _restrictions(values: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(values, tuple) or len(values) > 32:
        raise OrganizationalMemoryValidationError("reuse restrictions exceed the accepted bound")
    return tuple(_text(item, "reuse_restriction", 2000) for item in values)


@dataclass(frozen=True, slots=True)
class AdmitAcceptedReport:
    metadata: MemoryCommandMetadata
    source: AcceptedReportSource
    scope: MemoryScope
    audience_actor_ids: tuple[int, ...]
    reuse_restrictions: tuple[str, ...]
    admission_rationale: str

    def __post_init__(self) -> None:
        _validate_admission_command(self)


@dataclass(frozen=True, slots=True)
class CreateMemorySuccessor:
    metadata: MemoryCommandMetadata
    source: AcceptedReportSource
    scope: MemoryScope
    audience_actor_ids: tuple[int, ...]
    reuse_restrictions: tuple[str, ...]
    admission_rationale: str
    predecessor_memory_id: UUID

    def __post_init__(self) -> None:
        _validate_admission_command(self)
        _uuid(self.predecessor_memory_id, "predecessor_memory_id")


def _validate_admission_command(command: AdmitAcceptedReport | CreateMemorySuccessor) -> None:
    if not isinstance(command.metadata, MemoryCommandMetadata) or not isinstance(command.source, AcceptedReportSource) or not isinstance(command.scope, MemoryScope):
        raise OrganizationalMemoryValidationError("admission command contract is invalid")
    if command.metadata.actor.organization_id != command.scope.organization_id:
        raise OrganizationalMemoryValidationError("trusted Organization scope mismatch")
    object.__setattr__(command, "audience_actor_ids", _audience(command.audience_actor_ids))
    object.__setattr__(command, "reuse_restrictions", _restrictions(command.reuse_restrictions))
    object.__setattr__(command, "admission_rationale", _text(command.admission_rationale, "admission_rationale", 2000))


@dataclass(frozen=True, slots=True)
class WithdrawMemory:
    metadata: MemoryCommandMetadata
    memory_id: UUID
    expected_version: int
    reason: str

    def __post_init__(self) -> None:
        _uuid(self.memory_id, "memory_id"); _positive(self.expected_version, "expected_version")
        object.__setattr__(self, "reason", _text(self.reason, "reason", 2000))


@dataclass(frozen=True, slots=True)
class SupersedeMemory:
    metadata: MemoryCommandMetadata
    predecessor_memory_id: UUID
    replacement_memory_id: UUID
    expected_predecessor_version: int
    expected_replacement_version: int
    reason: str

    def __post_init__(self) -> None:
        _uuid(self.predecessor_memory_id, "predecessor_memory_id"); _uuid(self.replacement_memory_id, "replacement_memory_id")
        if self.predecessor_memory_id == self.replacement_memory_id:
            raise OrganizationalMemoryValidationError("supersession identities must differ")
        _positive(self.expected_predecessor_version, "expected_predecessor_version"); _positive(self.expected_replacement_version, "expected_replacement_version")
        object.__setattr__(self, "reason", _text(self.reason, "reason", 2000))


@dataclass(frozen=True, slots=True)
class GetActiveMemory:
    memory_id: UUID
    include_provenance: bool = False
    reuse_intent: bool = False
    def __post_init__(self) -> None:
        _uuid(self.memory_id, "memory_id")
        if type(self.include_provenance) is not bool or type(self.reuse_intent) is not bool: raise OrganizationalMemoryValidationError("read flags must be boolean")


@dataclass(frozen=True, slots=True)
class InspectMemoryHistory:
    memory_id: UUID
    include_predecessor: bool = False
    include_replacement: bool = False
    include_provenance: bool = False
    def __post_init__(self) -> None:
        _uuid(self.memory_id, "memory_id")
        if any(type(value) is not bool for value in (self.include_predecessor, self.include_replacement, self.include_provenance)): raise OrganizationalMemoryValidationError("history flags must be boolean")


@dataclass(frozen=True, slots=True)
class ListActiveMemory:
    scope: MemoryScope
    page_size: int = 50
    continuation: str | None = None
    def __post_init__(self) -> None:
        if not isinstance(self.scope, MemoryScope) or not 1 <= _positive(self.page_size, "page_size") <= 100: raise OrganizationalMemoryValidationError("page size must be 1..100")
        if self.continuation is not None: object.__setattr__(self, "continuation", _text(self.continuation, "continuation", 4096))


# Context-specific provenance authorization request variants.
@dataclass(frozen=True, slots=True)
class CaptureProvenanceAuthorization:
    entry_id: UUID; ordinal: int; capture_id: UUID; source_version: int; organization_id: UUID; project_id: int; workspace_id: int | None; engineering_object_id: UUID | None
    def __post_init__(self) -> None: _validate_provenance_identity(self, ("capture_id",), ("source_version", "project_id"))

@dataclass(frozen=True, slots=True)
class EvidenceProvenanceAuthorization:
    entry_id: UUID; ordinal: int; evidence_id: UUID; source_version: int; organization_id: UUID; project_id: int | None; workspace_id: int | None
    def __post_init__(self) -> None: _validate_provenance_identity(self, ("evidence_id",), ("source_version",))

@dataclass(frozen=True, slots=True)
class EngineeringObjectProvenanceAuthorization:
    entry_id: UUID; ordinal: int; engineering_object_id: UUID; source_version: int; organization_id: UUID; project_id: int; workspace_id: int
    def __post_init__(self) -> None: _validate_provenance_identity(self, ("engineering_object_id",), ("source_version", "project_id", "workspace_id"))

@dataclass(frozen=True, slots=True)
class EngineeringRelationshipProvenanceAuthorization:
    entry_id: UUID; ordinal: int; engineering_relationship_id: UUID; source_version: int; organization_id: UUID; project_id: int; workspace_id: int; source_object_id: UUID; target_object_id: UUID
    def __post_init__(self) -> None:
        _validate_provenance_identity(self, ("engineering_relationship_id", "source_object_id", "target_object_id"), ("source_version", "project_id", "workspace_id"))
        if self.source_object_id == self.target_object_id: raise OrganizationalMemoryValidationError("relationship endpoints must differ")


def _validate_provenance_identity(value: object, uuid_fields: tuple[str, ...], positive_fields: tuple[str, ...]) -> None:
    _uuid(getattr(value, "entry_id"), "entry_id"); _nonnegative(getattr(value, "ordinal"), "ordinal"); _uuid(getattr(value, "organization_id"), "organization_id")
    for name in uuid_fields: _uuid(getattr(value, name), name)
    for name in positive_fields: _positive(getattr(value, name), name)
    for name in ("project_id", "workspace_id"):
        if hasattr(value, name) and getattr(value, name) is not None: _positive(getattr(value, name), name)
    if hasattr(value, "engineering_object_id") and getattr(value, "engineering_object_id") is not None: _uuid(getattr(value, "engineering_object_id"), "engineering_object_id")


CanonicalProvenanceAuthorization: TypeAlias = CaptureProvenanceAuthorization | EvidenceProvenanceAuthorization | EngineeringObjectProvenanceAuthorization | EngineeringRelationshipProvenanceAuthorization


@dataclass(frozen=True, slots=True)
class MemoryProvenanceAuthorizationRequest:
    actor: MemoryActor; operation: MemoryProvenanceOperation; memory_scope: MemoryScope; source: AcceptedReportSource; items: tuple[CanonicalProvenanceAuthorization, ...]
    def __post_init__(self) -> None:
        if not isinstance(self.actor, MemoryActor) or not isinstance(self.memory_scope, MemoryScope) or not isinstance(self.source, AcceptedReportSource): raise OrganizationalMemoryValidationError("provenance request contract is invalid")
        object.__setattr__(self, "operation", MemoryProvenanceOperation(self.operation))
        allowed_types = (CaptureProvenanceAuthorization, EvidenceProvenanceAuthorization, EngineeringObjectProvenanceAuthorization, EngineeringRelationshipProvenanceAuthorization)
        if not isinstance(self.items, tuple) or not 1 <= len(self.items) <= 100 or any(type(item) not in allowed_types for item in self.items):
            raise OrganizationalMemoryValidationError("provenance request contains an unsupported identity contract")
        if self.actor.organization_id != self.memory_scope.organization_id: raise OrganizationalMemoryValidationError("provenance request Organization is invalid")
        if [item.ordinal for item in self.items] != sorted(item.ordinal for item in self.items): raise OrganizationalMemoryValidationError("provenance request ordering is invalid")
        for item in self.items:
            if item.organization_id != self.actor.organization_id:
                raise OrganizationalMemoryValidationError("provenance item Organization is invalid")
            if item.project_id is not None and item.project_id != self.memory_scope.project_id:
                raise OrganizationalMemoryValidationError("provenance item Project is incompatible with memory scope")
            if item.workspace_id is not None and item.workspace_id != self.memory_scope.workspace_id:
                raise OrganizationalMemoryValidationError("provenance item Workspace is incompatible with memory scope")
        identities = [(type(item), getattr(item, next(name for name in ("capture_id", "evidence_id", "engineering_object_id", "engineering_relationship_id") if hasattr(item, name))), item.source_version) for item in self.items]
        if len(identities) != len(set(identities)): raise OrganizationalMemoryValidationError("provenance identities must be unique")


@dataclass(frozen=True, slots=True)
class SafeAuthorizedProvenance(MemoryProvenanceDigestEntry):
    pass


@dataclass(frozen=True, slots=True)
class ProvenanceAuthorized:
    outcome: Literal["success"]
    items: tuple[SafeAuthorizedProvenance, ...]
    def __post_init__(self) -> None:
        if self.outcome != "success" or not isinstance(self.items, tuple) or any(type(item) is not SafeAuthorizedProvenance for item in self.items):
            raise OrganizationalMemoryValidationError("authorized provenance result is invalid")
        if [item.ordinal for item in self.items] != sorted(item.ordinal for item in self.items):
            raise OrganizationalMemoryValidationError("authorized provenance ordering is invalid")


@dataclass(frozen=True, slots=True)
class ProvenanceProtectedNotFound:
    outcome: Literal["protected_not_found"] = "protected_not_found"
    def __post_init__(self) -> None: _literal(self.outcome, "protected_not_found", "outcome")


@dataclass(frozen=True, slots=True)
class ProvenanceUnavailable:
    outcome: Literal["unavailable"] = "unavailable"
    def __post_init__(self) -> None: _literal(self.outcome, "unavailable", "outcome")


MemoryProvenanceAuthorizationResult: TypeAlias = ProvenanceAuthorized | ProvenanceProtectedNotFound | ProvenanceUnavailable


def validate_provenance_success(request: MemoryProvenanceAuthorizationRequest, result: ProvenanceAuthorized) -> None:
    if len(result.items) != len(request.items):
        raise OrganizationalMemoryValidationError("authorized provenance cardinality mismatch")
    for requested, returned in zip(request.items, result.items, strict=True):
        if (returned.entry_id, returned.ordinal) != (requested.entry_id, requested.ordinal):
            raise OrganizationalMemoryValidationError("authorized provenance identity/order mismatch")


def _literal(value: object, expected: object, name: str) -> None:
    if value != expected or type(value) is not type(expected):
        raise OrganizationalMemoryValidationError(f"{name} must equal {expected!r}")


def _optional_positive(value: object, name: str) -> None:
    if value is not None: _positive(value, name)


def _optional_uuid(value: object, name: str) -> None:
    if value is not None: _uuid(value, name)


def _validate_success(outcome: object, memory_id: object, version: object, standing: object, expected_standing: MemoryStanding) -> None:
    _literal(outcome, "success", "outcome"); _uuid(memory_id, "memory_id"); _positive(version, "version")
    if standing is not expected_standing: raise OrganizationalMemoryValidationError("success standing is invalid")


@dataclass(frozen=True, slots=True)
class AdmissionSuccess:
    outcome: Literal["success"]; memory_id: UUID; version: Literal[1]; standing: Literal[MemoryStanding.ACTIVE]; source: AcceptedReportSource
    def __post_init__(self) -> None:
        _validate_success(self.outcome, self.memory_id, self.version, self.standing, MemoryStanding.ACTIVE); _literal(self.version, 1, "version")
        if not isinstance(self.source, AcceptedReportSource): raise OrganizationalMemoryValidationError("source contract is invalid")


@dataclass(frozen=True, slots=True)
class WithdrawalSuccess:
    outcome: Literal["success"]; memory_id: UUID; version: int; standing: Literal[MemoryStanding.WITHDRAWN]; withdrawn_at: datetime
    def __post_init__(self) -> None: _validate_success(self.outcome, self.memory_id, self.version, self.standing, MemoryStanding.WITHDRAWN); _aware(self.withdrawn_at, "withdrawn_at")


@dataclass(frozen=True, slots=True)
class CreateSuccessorSuccess:
    outcome: Literal["success"]; memory_id: UUID; version: Literal[1]; standing: Literal[MemoryStanding.ACTIVE]; source: AcceptedReportSource; predecessor_memory_id: UUID
    def __post_init__(self) -> None:
        _validate_success(self.outcome, self.memory_id, self.version, self.standing, MemoryStanding.ACTIVE); _literal(self.version, 1, "version"); _uuid(self.predecessor_memory_id, "predecessor_memory_id")
        if not isinstance(self.source, AcceptedReportSource): raise OrganizationalMemoryValidationError("source contract is invalid")


@dataclass(frozen=True, slots=True)
class SupersessionSuccess:
    outcome: Literal["success"]; predecessor_memory_id: UUID; predecessor_version: int; predecessor_standing: Literal[MemoryStanding.SUPERSEDED]; replacement_memory_id: UUID; replacement_version: int; replacement_standing: Literal[MemoryStanding.ACTIVE]; superseded_at: datetime
    def __post_init__(self) -> None:
        _literal(self.outcome, "success", "outcome"); _uuid(self.predecessor_memory_id, "predecessor_memory_id"); _uuid(self.replacement_memory_id, "replacement_memory_id")
        if self.predecessor_memory_id == self.replacement_memory_id: raise OrganizationalMemoryValidationError("supersession identities must differ")
        _positive(self.predecessor_version, "predecessor_version"); _positive(self.replacement_version, "replacement_version")
        if self.predecessor_standing is not MemoryStanding.SUPERSEDED or self.replacement_standing is not MemoryStanding.ACTIVE: raise OrganizationalMemoryValidationError("supersession success standing is invalid")
        _aware(self.superseded_at, "superseded_at")


@dataclass(frozen=True, slots=True)
class MemoryProtectedNotFound:
    outcome: Literal["protected_not_found"] = "protected_not_found"
    def __post_init__(self) -> None: _literal(self.outcome, "protected_not_found", "outcome")
@dataclass(frozen=True, slots=True)
class MemoryInvalidRequest:
    outcome: Literal["invalid_request"] = "invalid_request"
    def __post_init__(self) -> None: _literal(self.outcome, "invalid_request", "outcome")
@dataclass(frozen=True, slots=True)
class MemoryVersionConflict:
    outcome: Literal["version_conflict"] = "version_conflict"
    def __post_init__(self) -> None: _literal(self.outcome, "version_conflict", "outcome")
@dataclass(frozen=True, slots=True)
class MemoryIdempotencyConflict:
    outcome: Literal["idempotency_conflict"] = "idempotency_conflict"
    def __post_init__(self) -> None: _literal(self.outcome, "idempotency_conflict", "outcome")
@dataclass(frozen=True, slots=True)
class MemoryInvalidStanding:
    outcome: Literal["invalid_standing"] = "invalid_standing"
    def __post_init__(self) -> None: _literal(self.outcome, "invalid_standing", "outcome")
@dataclass(frozen=True, slots=True)
class MemoryDuplicateSource:
    outcome: Literal["duplicate_source"] = "duplicate_source"
    def __post_init__(self) -> None: _literal(self.outcome, "duplicate_source", "outcome")
@dataclass(frozen=True, slots=True)
class MemoryUnavailable:
    outcome: Literal["unavailable"] = "unavailable"
    def __post_init__(self) -> None: _literal(self.outcome, "unavailable", "outcome")


@dataclass(frozen=True, slots=True)
class StoredAdmissionResultV1:
    result_type: Literal["admit.v1"]; memory_id: UUID; version: Literal[1]; standing: Literal["active"]; source_report_id: UUID; source_accepted_version: int
    def __post_init__(self) -> None: _literal(self.result_type, "admit.v1", "result_type"); _uuid(self.memory_id, "memory_id"); _literal(self.version, 1, "version"); _literal(self.standing, "active", "standing"); _uuid(self.source_report_id, "source_report_id"); _positive(self.source_accepted_version, "source_accepted_version")
@dataclass(frozen=True, slots=True)
class StoredWithdrawalResultV1:
    result_type: Literal["withdraw.v1"]; memory_id: UUID; result_version: int; standing: Literal["withdrawn"]; withdrawn_at: datetime
    def __post_init__(self) -> None: _literal(self.result_type, "withdraw.v1", "result_type"); _uuid(self.memory_id, "memory_id"); _positive(self.result_version, "result_version"); _literal(self.standing, "withdrawn", "standing"); _aware(self.withdrawn_at, "withdrawn_at")
@dataclass(frozen=True, slots=True)
class StoredSuccessorResultV1:
    result_type: Literal["create_successor.v1"]; memory_id: UUID; version: Literal[1]; standing: Literal["active"]; source_report_id: UUID; source_accepted_version: int; predecessor_memory_id: UUID
    def __post_init__(self) -> None: _literal(self.result_type, "create_successor.v1", "result_type"); _uuid(self.memory_id, "memory_id"); _literal(self.version, 1, "version"); _literal(self.standing, "active", "standing"); _uuid(self.source_report_id, "source_report_id"); _positive(self.source_accepted_version, "source_accepted_version"); _uuid(self.predecessor_memory_id, "predecessor_memory_id")
@dataclass(frozen=True, slots=True)
class StoredSupersessionResultV1:
    result_type: Literal["supersede.v1"]; predecessor_memory_id: UUID; predecessor_result_version: int; predecessor_standing: Literal["superseded"]; replacement_memory_id: UUID; replacement_version_at_command: int; replacement_standing: Literal["active"]; superseded_at: datetime
    def __post_init__(self) -> None: _literal(self.result_type, "supersede.v1", "result_type"); _uuid(self.predecessor_memory_id, "predecessor_memory_id"); _positive(self.predecessor_result_version, "predecessor_result_version"); _literal(self.predecessor_standing, "superseded", "predecessor_standing"); _uuid(self.replacement_memory_id, "replacement_memory_id"); _positive(self.replacement_version_at_command, "replacement_version_at_command"); _literal(self.replacement_standing, "active", "replacement_standing"); _aware(self.superseded_at, "superseded_at")
MemoryStoredResultV1: TypeAlias = StoredAdmissionResultV1 | StoredWithdrawalResultV1 | StoredSuccessorResultV1 | StoredSupersessionResultV1


def validate_stored_result(operation: str, result: MemoryStoredResultV1) -> None:
    allowed = (StoredAdmissionResultV1, StoredWithdrawalResultV1, StoredSuccessorResultV1, StoredSupersessionResultV1)
    if type(result) not in allowed or IDEMPOTENCY_RESULT_TYPES.get(operation) != result.result_type:
        raise OrganizationalMemoryValidationError("operation/result discriminator mismatch")
    payload = canonical_json(result)
    if len(payload) > MAX_STORED_RESULT_BYTES: raise OrganizationalMemoryValidationError("stored result exceeds 1 KiB")
    prohibited = ("projection", "content", "manifest", "provenance", "rationale", "reason", "audience", "restriction", "diagnostic", "exception", "credential")
    if any(term in payload.decode("utf-8").lower() for term in prohibited): raise OrganizationalMemoryValidationError("stored result contains prohibited plaintext fields")


@dataclass(frozen=True, slots=True)
class MemoryStandingHistoryRecord:
    event_id: UUID; memory_id: UUID; organization_id: UUID; aggregate_version: int; from_standing: MemoryStanding | None; to_standing: MemoryStanding; actor_id: int; occurred_at: datetime; reason: str; replacement_memory_id: UUID | None
    def __post_init__(self) -> None:
        for name in ("event_id", "memory_id", "organization_id"): _uuid(getattr(self, name), name)
        _positive(self.aggregate_version, "aggregate_version"); _positive(self.actor_id, "actor_id"); _aware(self.occurred_at, "occurred_at"); object.__setattr__(self, "reason", _text(self.reason, "reason", 2000)); _optional_uuid(self.replacement_memory_id, "replacement_memory_id")
        if self.from_standing is None:
            if self.aggregate_version != 1 or self.to_standing is not MemoryStanding.ACTIVE or self.replacement_memory_id is not None: raise OrganizationalMemoryValidationError("initial standing history is invalid")
        elif self.from_standing is not MemoryStanding.ACTIVE or self.to_standing not in (MemoryStanding.WITHDRAWN, MemoryStanding.SUPERSEDED): raise OrganizationalMemoryValidationError("standing history transition is invalid")
        elif (self.to_standing is MemoryStanding.SUPERSEDED) != (self.replacement_memory_id is not None): raise OrganizationalMemoryValidationError("standing history replacement is incoherent")


@dataclass(frozen=True, slots=True)
class MemoryEventPayloadV1:
    memory_id: UUID; aggregate_version: int; organization_id: UUID; workspace_id: int; project_id: int | None; standing: MemoryStanding; actor_id: int; occurred_at: datetime; command_id: UUID; correlation_id: UUID; causation_id: UUID; source_report_id: UUID; source_accepted_version: int; predecessor_memory_id: UUID | None; replacement_memory_id: UUID | None; provenance_entry_count: int
    def __post_init__(self) -> None:
        for name in ("memory_id", "organization_id", "command_id", "correlation_id", "causation_id", "source_report_id"): _uuid(getattr(self, name), name)
        for name in ("aggregate_version", "workspace_id", "actor_id", "source_accepted_version"): _positive(getattr(self, name), name)
        _optional_positive(self.project_id, "project_id"); object.__setattr__(self, "standing", MemoryStanding(self.standing)); _aware(self.occurred_at, "occurred_at"); _optional_uuid(self.predecessor_memory_id, "predecessor_memory_id"); _optional_uuid(self.replacement_memory_id, "replacement_memory_id"); _nonnegative(self.provenance_entry_count, "provenance_entry_count")
        if (self.standing is MemoryStanding.SUPERSEDED) != (self.replacement_memory_id is not None):
            raise OrganizationalMemoryValidationError("event replacement/standing is incoherent")


@dataclass(frozen=True, slots=True)
class MemoryDomainEvent:
    event_id: UUID; event_type: MemoryEventType; payload_schema_version: Literal[1]; memory_id: UUID; aggregate_version: int; organization_id: UUID; workspace_id: int; project_id: int | None; standing: MemoryStanding; actor_id: int; occurred_at: datetime; command_id: UUID; correlation_id: UUID; causation_id: UUID; source_report_id: UUID; source_accepted_version: int; predecessor_memory_id: UUID | None; replacement_memory_id: UUID | None; provenance_entry_count: int
    def __post_init__(self) -> None:
        _uuid(self.event_id, "event_id"); object.__setattr__(self, "event_type", MemoryEventType(self.event_type)); _literal(self.payload_schema_version, 1, "payload_schema_version")
        payload = self.payload
        expected = {MemoryEventType.ADMITTED: MemoryStanding.ACTIVE, MemoryEventType.WITHDRAWN: MemoryStanding.WITHDRAWN, MemoryEventType.SUPERSEDED: MemoryStanding.SUPERSEDED}[self.event_type]
        if payload.standing is not expected: raise OrganizationalMemoryValidationError("event type/standing is incoherent")
    @property
    def payload(self) -> MemoryEventPayloadV1:
        return MemoryEventPayloadV1(*(getattr(self, field.name) for field in fields(MemoryEventPayloadV1)))


@dataclass(frozen=True, slots=True)
class MemoryAuthorizationRequest:
    actor: MemoryActor; operation: MemoryOperation; scope: MemoryScope; memory_id: UUID | None; source: AcceptedReportSource | None; predecessor_memory_id: UUID | None; replacement_memory_id: UUID | None; audience_actor_ids: tuple[int, ...]
    def __post_init__(self) -> None:
        if not isinstance(self.actor, MemoryActor) or not isinstance(self.scope, MemoryScope) or self.actor.organization_id != self.scope.organization_id: raise OrganizationalMemoryValidationError("authorization actor/scope is invalid")
        object.__setattr__(self, "operation", MemoryOperation(self.operation)); _optional_uuid(self.memory_id, "memory_id"); _optional_uuid(self.predecessor_memory_id, "predecessor_memory_id"); _optional_uuid(self.replacement_memory_id, "replacement_memory_id"); object.__setattr__(self, "audience_actor_ids", _audience(self.audience_actor_ids))
        if self.source is not None and not isinstance(self.source, AcceptedReportSource): raise OrganizationalMemoryValidationError("authorization source is invalid")


@dataclass(frozen=True, slots=True)
class MemoryFinalRecheckRequest:
    authorization: MemoryAuthorizationRequest; expected_memory_version: int | None; expected_predecessor_version: int | None; expected_replacement_version: int | None; expected_source_snapshot_digest: str | None
    def __post_init__(self) -> None:
        if not isinstance(self.authorization, MemoryAuthorizationRequest): raise OrganizationalMemoryValidationError("authorization request is invalid")
        for name in ("expected_memory_version", "expected_predecessor_version", "expected_replacement_version"): _optional_positive(getattr(self, name), name)
        if self.expected_source_snapshot_digest is not None: _sha256(self.expected_source_snapshot_digest, "expected_source_snapshot_digest")


@dataclass(frozen=True, slots=True)
class MemoryAuditRecord:
    operation: MemoryOperation; actor_id: int; organization_id: UUID; memory_id: UUID; previous_version: int | None; result_version: int; standing: MemoryStanding; source_report_id: UUID; source_accepted_version: int; correlation_id: UUID; command_id: UUID; idempotency_id: UUID; occurred_at: datetime; predecessor_memory_id: UUID | None; replacement_memory_id: UUID | None; provenance_entry_count: int
    def __post_init__(self) -> None:
        object.__setattr__(self, "operation", MemoryOperation(self.operation)); _positive(self.actor_id, "actor_id"); _uuid(self.organization_id, "organization_id"); _uuid(self.memory_id, "memory_id"); _optional_positive(self.previous_version, "previous_version"); _positive(self.result_version, "result_version"); object.__setattr__(self, "standing", MemoryStanding(self.standing)); _uuid(self.source_report_id, "source_report_id"); _positive(self.source_accepted_version, "source_accepted_version")
        for name in ("correlation_id", "command_id", "idempotency_id"): _uuid(getattr(self, name), name)
        _aware(self.occurred_at, "occurred_at"); _optional_uuid(self.predecessor_memory_id, "predecessor_memory_id"); _optional_uuid(self.replacement_memory_id, "replacement_memory_id"); _nonnegative(self.provenance_entry_count, "provenance_entry_count")


@dataclass(frozen=True, slots=True)
class MemoryRejectionAuditRecord:
    operation: MemoryOperation; reason: MemoryRejectionReason; actor_id: int; organization_id: UUID; correlation_id: UUID; command_id: UUID; occurred_at: datetime; memory_id: UUID | None
    def __post_init__(self) -> None:
        object.__setattr__(self, "operation", MemoryOperation(self.operation)); object.__setattr__(self, "reason", MemoryRejectionReason(self.reason)); _positive(self.actor_id, "actor_id"); _uuid(self.organization_id, "organization_id"); _uuid(self.correlation_id, "correlation_id"); _uuid(self.command_id, "command_id"); _aware(self.occurred_at, "occurred_at"); _optional_uuid(self.memory_id, "memory_id")


@dataclass(frozen=True, slots=True)
class MemoryOrderingAnchor:
    admitted_at: datetime; memory_id: UUID
    def __post_init__(self) -> None: _aware(self.admitted_at, "admitted_at"); _uuid(self.memory_id, "memory_id")


@dataclass(frozen=True, slots=True)
class ActiveMemoryCriteria:
    organization_id: UUID; workspace_id: int; project_id: int | None; purpose: TechnicalReportPurpose | None; anchor: MemoryOrderingAnchor | None; candidate_limit: int
    def __post_init__(self) -> None:
        _uuid(self.organization_id, "organization_id"); _positive(self.workspace_id, "workspace_id"); _optional_positive(self.project_id, "project_id"); _positive(self.candidate_limit, "candidate_limit")
        if self.candidate_limit > 101: raise OrganizationalMemoryValidationError("candidate limit exceeds 101")
        if self.purpose is not None: object.__setattr__(self, "purpose", TechnicalReportPurpose(self.purpose))
        if self.anchor is not None and not isinstance(self.anchor, MemoryOrderingAnchor): raise OrganizationalMemoryValidationError("ordering anchor is invalid")


@dataclass(frozen=True, slots=True)
class MemoryIdempotencyKey:
    organization_id: UUID; actor_id: int; operation: Literal["admit", "withdraw", "create_successor", "supersede"]; idempotency_id: UUID
    def __post_init__(self) -> None:
        _uuid(self.organization_id, "organization_id"); _positive(self.actor_id, "actor_id"); _uuid(self.idempotency_id, "idempotency_id")
        if self.operation not in IDEMPOTENCY_RESULT_TYPES: raise OrganizationalMemoryValidationError("idempotency operation is invalid")


@dataclass(frozen=True, slots=True)
class MemoryIdempotencyMiss:
    state: Literal["missing"] = "missing"
    def __post_init__(self) -> None: _literal(self.state, "missing", "state")
@dataclass(frozen=True, slots=True)
class MemoryIdempotencyPending:
    state: Literal["pending"] = "pending"
    def __post_init__(self) -> None: _literal(self.state, "pending", "state")
@dataclass(frozen=True, slots=True)
class MemoryIdempotencyCompleted:
    state: Literal["completed"]; request_fingerprint: str; result_schema_version: Literal[1]; result: MemoryStoredResultV1
    def __post_init__(self) -> None:
        _literal(self.state, "completed", "state"); _sha256(self.request_fingerprint, "request_fingerprint"); _literal(self.result_schema_version, 1, "result_schema_version")
        if type(self.result) not in (StoredAdmissionResultV1, StoredWithdrawalResultV1, StoredSuccessorResultV1, StoredSupersessionResultV1): raise OrganizationalMemoryValidationError("stored idempotency result is invalid")
MemoryIdempotencyLookup: TypeAlias = MemoryIdempotencyMiss | MemoryIdempotencyPending | MemoryIdempotencyCompleted


@dataclass(frozen=True, slots=True)
class MemoryOutboxRecord:
    event_id: UUID; memory_id: UUID; aggregate_version: int; event_type: MemoryEventType; payload_schema_version: Literal[1]; payload: MemoryEventPayloadV1; occurred_at: datetime; created_at: datetime
    def __post_init__(self) -> None:
        _uuid(self.event_id, "event_id"); _uuid(self.memory_id, "memory_id"); _positive(self.aggregate_version, "aggregate_version"); object.__setattr__(self, "event_type", MemoryEventType(self.event_type)); _literal(self.payload_schema_version, 1, "payload_schema_version")
        if not isinstance(self.payload, MemoryEventPayloadV1) or (self.memory_id, self.aggregate_version, self.event_type, self.occurred_at) != (self.payload.memory_id, self.payload.aggregate_version, _event_type_for_standing(self.payload.standing), self.payload.occurred_at): raise OrganizationalMemoryValidationError("outbox payload is incoherent")
        _aware(self.created_at, "created_at")


def _event_type_for_standing(standing: MemoryStanding) -> MemoryEventType:
    return {MemoryStanding.ACTIVE: MemoryEventType.ADMITTED, MemoryStanding.WITHDRAWN: MemoryEventType.WITHDRAWN, MemoryStanding.SUPERSEDED: MemoryEventType.SUPERSEDED}[standing]


@dataclass(frozen=True, slots=True)
class AcceptedReportProjection:
    source: AcceptedReportSource; owner_id: int; scope: MemoryScope; snapshot: TechnicalReportAcceptedSnapshot
    def __post_init__(self) -> None:
        if not isinstance(self.source, AcceptedReportSource) or not isinstance(self.scope, MemoryScope) or not isinstance(self.snapshot, TechnicalReportAcceptedSnapshot): raise OrganizationalMemoryValidationError("accepted report projection is invalid")
        _positive(self.owner_id, "owner_id")
        if (self.source.report_id, self.source.accepted_aggregate_version, self.source.accepted_snapshot_digest) != (self.snapshot.report_id, self.snapshot.accepted_aggregate_version, self.snapshot.integrity_digest): raise OrganizationalMemoryIntegrityError("accepted report source binding is invalid")
        if (self.scope.organization_id, self.scope.workspace_id, self.scope.project_id) != (self.snapshot.organization_id, self.snapshot.workspace_id, self.snapshot.project_id): raise OrganizationalMemoryValidationError("accepted report scope binding is invalid")


@dataclass(frozen=True, slots=True)
class AcceptedReportProtectedNotFound:
    outcome: Literal["protected_not_found"] = "protected_not_found"
    def __post_init__(self) -> None: _literal(self.outcome, "protected_not_found", "outcome")
@dataclass(frozen=True, slots=True)
class AcceptedReportUnavailable:
    outcome: Literal["unavailable"] = "unavailable"
    def __post_init__(self) -> None: _literal(self.outcome, "unavailable", "outcome")
AcceptedReportReadResult: TypeAlias = AcceptedReportProjection | AcceptedReportProtectedNotFound | AcceptedReportUnavailable


@dataclass(frozen=True, slots=True)
class ActiveMemorySummary:
    memory_id: UUID; version: int; standing: Literal[MemoryStanding.ACTIVE]; source_report_id: UUID; source_accepted_version: int; purpose: TechnicalReportPurpose; organization_id: UUID; workspace_id: int; project_id: int | None; admitted_by_id: int; admitted_at: datetime; updated_at: datetime
    def __post_init__(self) -> None:
        _uuid(self.memory_id, "memory_id"); _positive(self.version, "version")
        if self.standing is not MemoryStanding.ACTIVE: raise OrganizationalMemoryValidationError("active summary standing is invalid")
        _uuid(self.source_report_id, "source_report_id"); _positive(self.source_accepted_version, "source_accepted_version"); object.__setattr__(self, "purpose", TechnicalReportPurpose(self.purpose)); _uuid(self.organization_id, "organization_id"); _positive(self.workspace_id, "workspace_id"); _optional_positive(self.project_id, "project_id"); _positive(self.admitted_by_id, "admitted_by_id"); _aware(self.admitted_at, "admitted_at"); _aware(self.updated_at, "updated_at")


@dataclass(frozen=True, slots=True)
class ActiveMemoryDetail:
    summary: ActiveMemorySummary; projection: AdmittedReportProjectionV1; admission_rationale: str; reuse_restrictions: tuple[str, ...]; safe_provenance: tuple[SafeAuthorizedProvenance, ...]
    def __post_init__(self) -> None:
        if not isinstance(self.summary, ActiveMemorySummary) or not isinstance(self.projection, AdmittedReportProjectionV1): raise OrganizationalMemoryValidationError("active detail contract is invalid")
        if (
            self.summary.source_report_id,
            self.summary.source_accepted_version,
            self.summary.purpose,
            self.summary.organization_id,
            self.summary.workspace_id,
            self.summary.project_id,
        ) != (
            self.projection.report_id,
            self.projection.accepted_aggregate_version,
            self.projection.purpose,
            self.projection.organization_id,
            self.projection.workspace_id,
            self.projection.project_id,
        ):
            raise OrganizationalMemoryValidationError("active detail projection is incoherent")
        object.__setattr__(self, "admission_rationale", _text(self.admission_rationale, "admission_rationale", 2000)); object.__setattr__(self, "reuse_restrictions", _restrictions(self.reuse_restrictions))
        if not isinstance(self.safe_provenance, tuple) or any(type(item) is not SafeAuthorizedProvenance for item in self.safe_provenance): raise OrganizationalMemoryValidationError("safe provenance contract is invalid")


@dataclass(frozen=True, slots=True)
class AuthorizedMemoryLink:
    memory_id: UUID
    def __post_init__(self) -> None: _uuid(self.memory_id, "memory_id")


def _validate_history_base(value: object, expected: MemoryStanding) -> None:
    _uuid(getattr(value, "memory_id"), "memory_id"); _positive(getattr(value, "version"), "version")
    if getattr(value, "standing") is not expected: raise OrganizationalMemoryValidationError("history standing is invalid")
    if not isinstance(getattr(value, "source"), AcceptedReportSource) or not isinstance(getattr(value, "projection"), AdmittedReportProjectionV1): raise OrganizationalMemoryValidationError("history source/projection is invalid")
    if (
        getattr(value, "source").report_id,
        getattr(value, "source").accepted_aggregate_version,
    ) != (
        getattr(value, "projection").report_id,
        getattr(value, "projection").accepted_aggregate_version,
    ):
        raise OrganizationalMemoryValidationError("history source/projection is incoherent")
    _positive(getattr(value, "admitted_by_id"), "admitted_by_id"); _aware(getattr(value, "admitted_at"), "admitted_at")
    predecessor = getattr(value, "predecessor")
    if predecessor is not None and not isinstance(predecessor, AuthorizedMemoryLink): raise OrganizationalMemoryValidationError("protected predecessor slot is invalid")
    provenance = getattr(value, "safe_provenance")
    if not isinstance(provenance, tuple) or any(type(item) is not SafeAuthorizedProvenance for item in provenance): raise OrganizationalMemoryValidationError("history provenance is invalid")


@dataclass(frozen=True, slots=True)
class ActiveMemoryHistory:
    memory_id: UUID; version: int; standing: Literal[MemoryStanding.ACTIVE]; source: AcceptedReportSource; projection: AdmittedReportProjectionV1; admitted_by_id: int; admitted_at: datetime; predecessor: AuthorizedMemoryLink | None; safe_provenance: tuple[SafeAuthorizedProvenance, ...]
    def __post_init__(self) -> None: _validate_history_base(self, MemoryStanding.ACTIVE)


@dataclass(frozen=True, slots=True)
class WithdrawnMemoryHistory:
    memory_id: UUID; version: int; standing: Literal[MemoryStanding.WITHDRAWN]; source: AcceptedReportSource; projection: AdmittedReportProjectionV1; admitted_by_id: int; admitted_at: datetime; withdrawn_by_id: int; withdrawn_at: datetime; withdrawal_reason: str; predecessor: AuthorizedMemoryLink | None; safe_provenance: tuple[SafeAuthorizedProvenance, ...]
    def __post_init__(self) -> None:
        _validate_history_base(self, MemoryStanding.WITHDRAWN); _positive(self.withdrawn_by_id, "withdrawn_by_id"); _aware(self.withdrawn_at, "withdrawn_at"); object.__setattr__(self, "withdrawal_reason", _text(self.withdrawal_reason, "withdrawal_reason", 2000))


@dataclass(frozen=True, slots=True)
class SupersededMemoryHistory:
    memory_id: UUID; version: int; standing: Literal[MemoryStanding.SUPERSEDED]; source: AcceptedReportSource; projection: AdmittedReportProjectionV1; admitted_by_id: int; admitted_at: datetime; superseded_by_id: int; superseded_at: datetime; supersession_reason: str; predecessor: AuthorizedMemoryLink | None; replacement: AuthorizedMemoryLink | None; safe_provenance: tuple[SafeAuthorizedProvenance, ...]
    def __post_init__(self) -> None:
        _validate_history_base(self, MemoryStanding.SUPERSEDED); _positive(self.superseded_by_id, "superseded_by_id"); _aware(self.superseded_at, "superseded_at"); object.__setattr__(self, "supersession_reason", _text(self.supersession_reason, "supersession_reason", 2000))
        if self.replacement is not None and not isinstance(self.replacement, AuthorizedMemoryLink): raise OrganizationalMemoryValidationError("protected replacement slot is invalid")


HistoricalMemoryDetail: TypeAlias = ActiveMemoryHistory | WithdrawnMemoryHistory | SupersededMemoryHistory


@dataclass(frozen=True, slots=True)
class ActiveMemoryPage:
    items: tuple[ActiveMemorySummary, ...]; visible_total: int; next_continuation: str | None
    def __post_init__(self) -> None:
        if not isinstance(self.items, tuple) or len(self.items) > 100 or any(type(item) is not ActiveMemorySummary for item in self.items): raise OrganizationalMemoryValidationError("active page items are invalid")
        _nonnegative(self.visible_total, "visible_total")
        if self.visible_total != len(self.items): raise OrganizationalMemoryValidationError("visible total must equal returned item count")
        if self.next_continuation is not None: object.__setattr__(self, "next_continuation", _text(self.next_continuation, "next_continuation", 4096))


@dataclass(frozen=True, slots=True)
class GetActiveSuccess:
    outcome: Literal["success"]; item: ActiveMemoryDetail
    def __post_init__(self) -> None:
        _literal(self.outcome, "success", "outcome")
        if not isinstance(self.item, ActiveMemoryDetail): raise OrganizationalMemoryValidationError("active result item is invalid")
@dataclass(frozen=True, slots=True)
class ListActiveSuccess:
    outcome: Literal["success"]; page: ActiveMemoryPage
    def __post_init__(self) -> None:
        _literal(self.outcome, "success", "outcome")
        if not isinstance(self.page, ActiveMemoryPage): raise OrganizationalMemoryValidationError("list result page is invalid")
@dataclass(frozen=True, slots=True)
class InspectHistorySuccess:
    outcome: Literal["success"]; item: HistoricalMemoryDetail
    def __post_init__(self) -> None:
        _literal(self.outcome, "success", "outcome")
        if type(self.item) not in (ActiveMemoryHistory, WithdrawnMemoryHistory, SupersededMemoryHistory): raise OrganizationalMemoryValidationError("history result item is invalid")


AdmitResult: TypeAlias = AdmissionSuccess | MemoryProtectedNotFound | MemoryInvalidRequest | MemoryIdempotencyConflict | MemoryDuplicateSource | MemoryUnavailable
WithdrawResult: TypeAlias = WithdrawalSuccess | MemoryProtectedNotFound | MemoryInvalidRequest | MemoryVersionConflict | MemoryIdempotencyConflict | MemoryInvalidStanding | MemoryUnavailable
CreateSuccessorResult: TypeAlias = CreateSuccessorSuccess | MemoryProtectedNotFound | MemoryInvalidRequest | MemoryIdempotencyConflict | MemoryDuplicateSource | MemoryUnavailable
SupersedeResult: TypeAlias = SupersessionSuccess | MemoryProtectedNotFound | MemoryInvalidRequest | MemoryVersionConflict | MemoryIdempotencyConflict | MemoryInvalidStanding | MemoryUnavailable
GetActiveResult: TypeAlias = GetActiveSuccess | MemoryProtectedNotFound | MemoryInvalidRequest | MemoryUnavailable
ListActiveResult: TypeAlias = ListActiveSuccess | MemoryProtectedNotFound | MemoryInvalidRequest | MemoryUnavailable
InspectHistoryResult: TypeAlias = InspectHistorySuccess | MemoryProtectedNotFound | MemoryInvalidRequest | MemoryUnavailable
