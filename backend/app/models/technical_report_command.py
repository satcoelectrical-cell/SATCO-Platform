"""Persistence-independent Technical Report commands and value contracts."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import hmac
import json
import unicodedata
from typing import TypeAlias
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, JSON, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func

from app.core.database import Base

from app.enums.engineering_experience_capture import (
    EngineeringExperienceCaptureLifecycle,
    EngineeringExperienceSourceKind,
)
from app.enums.engineering_knowledge import (
    EngineeringAuthorityStanding,
    EngineeringDiscipline,
    EngineeringLifecycle,
    EngineeringObjectFamily,
    EngineeringObjectType,
)
from app.enums.engineering_relationship import (
    RelationshipFamily,
    RelationshipLifecycle,
    RelationshipType,
)
from app.enums.evidence import EvidenceLifecycle, EvidenceSourceKind, EvidenceSourceStanding
from app.enums.technical_report import (
    TechnicalReportAvailabilityStatus,
    TechnicalReportIntegrityAlgorithm,
    TechnicalReportLifecycle,
    TechnicalReportOwningCapability,
    TechnicalReportPurpose,
    TechnicalReportSourceClass,
    TechnicalReportSourceType,
    TechnicalReportVerificationStatus,
)
from app.exceptions.technical_report import (
    TechnicalReportHistoricalBasisIncomplete,
    TechnicalReportIntegrityMismatch,
    TechnicalReportValidationError,
)


def _nonempty(value: str, field_name: str, maximum: int | None = None) -> str:
    if not isinstance(value, str):
        raise TechnicalReportValidationError(f"{field_name} is invalid")
    normalized = unicodedata.normalize("NFC", value.strip())
    if not normalized or (maximum is not None and len(normalized) > maximum):
        raise TechnicalReportValidationError(f"{field_name} is invalid")
    if any(ord(character) < 32 and character not in "\n\t" for character in normalized):
        raise TechnicalReportValidationError(f"{field_name} contains invalid characters")
    return normalized


def _capture_content(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n")).strip()
    if not normalized or len(normalized) > 10000:
        raise TechnicalReportValidationError("original_content is invalid")
    if any(ord(character) < 32 and character not in "\n\t" for character in normalized):
        raise TechnicalReportValidationError("original_content contains invalid characters")
    return normalized


def _single_line(value: str, field_name: str, maximum: int) -> str:
    normalized = _nonempty(value, field_name, maximum)
    if "\n" in normalized or "\r" in normalized:
        raise TechnicalReportValidationError(f"{field_name} must be single-line")
    return normalized


def _positive(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise TechnicalReportValidationError(f"{field_name} must be positive")


def _aware(value: datetime, field_name: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
        raise TechnicalReportValidationError(f"{field_name} must be timezone-aware UTC")


def _uuid(value: object, field_name: str) -> None:
    if not isinstance(value, UUID):
        raise TechnicalReportValidationError(f"{field_name} must be a UUID")


def _optional_uuid(value: object, field_name: str) -> None:
    if value is not None:
        _uuid(value, field_name)


def _sha256(value: object, field_name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower() or any(character not in "0123456789abcdef" for character in value):
        raise TechnicalReportValidationError(f"{field_name} must be lowercase SHA-256")
    return value


def _instance(value: object, expected: type, field_name: str) -> None:
    if not isinstance(value, expected):
        raise TechnicalReportValidationError(f"{field_name} has an invalid contract type")


@dataclass(frozen=True, slots=True)
class TechnicalReportActor:
    actor_id: int
    organization_id: UUID
    def __post_init__(self) -> None: _positive(self.actor_id, "actor_id"); _uuid(self.organization_id, "organization_id")


@dataclass(frozen=True, slots=True)
class TechnicalReportCommandMetadata:
    actor: TechnicalReportActor
    rationale: str
    correlation_id: UUID
    idempotency_id: UUID
    command_id: UUID
    def __post_init__(self) -> None:
        _instance(self.actor, TechnicalReportActor, "actor")
        object.__setattr__(self, "rationale", _nonempty(self.rationale, "rationale", 2000))
        for name in ("correlation_id", "idempotency_id", "command_id"): _uuid(getattr(self, name), name)


@dataclass(frozen=True, slots=True)
class TechnicalReportContent:
    engineering_scope: str
    technical_content: str
    assumptions: tuple[str, ...]
    uncertainty: str
    limitations: tuple[str, ...]
    conclusions: str
    recommendations: tuple[str, ...]
    def __post_init__(self) -> None:
        for name in ("engineering_scope", "technical_content", "uncertainty", "conclusions"):
            object.__setattr__(self, name, _nonempty(getattr(self, name), name, 10000))
        for name in ("assumptions", "limitations", "recommendations"):
            object.__setattr__(self, name, tuple(_nonempty(item, name, 10000) for item in getattr(self, name)))


@dataclass(frozen=True, slots=True)
class PreliminaryQualification:
    is_preliminary: bool
    evidence_deficiencies: tuple[str, ...] = ()
    unresolved_issues: tuple[str, ...] = ()
    follow_up_requirements: tuple[str, ...] = ()
    def __post_init__(self) -> None:
        if type(self.is_preliminary) is not bool:
            raise TechnicalReportValidationError("is_preliminary must be boolean")
        for name in ("evidence_deficiencies", "unresolved_issues", "follow_up_requirements"):
            object.__setattr__(self, name, tuple(_nonempty(item, name) for item in getattr(self, name)))
        basis = (self.evidence_deficiencies, self.unresolved_issues, self.follow_up_requirements)
        if self.is_preliminary != any(basis):
            raise TechnicalReportValidationError("preliminary qualification is incoherent")


@dataclass(frozen=True, slots=True)
class TechnicalReportDraftRevision:
    revision_id: UUID
    revision_number: int
    def __post_init__(self) -> None: _uuid(self.revision_id, "revision_id"); _positive(self.revision_number, "revision_number")


@dataclass(frozen=True, slots=True)
class CaptureHistoricalBasisV1:
    basis_schema_version: int; source_category: str; capture_id: UUID; source_version: int
    organization_id: UUID; project_id: int; workspace_id: int | None
    discipline: EngineeringDiscipline | None; engineering_object_id: UUID | None
    source_kind: EngineeringExperienceSourceKind; original_content: str
    source_reference: str | None; creator_id: int
    lifecycle: EngineeringExperienceCaptureLifecycle; created_at: datetime
    def __post_init__(self) -> None:
        if self.basis_schema_version != 1 or self.source_category != "universal_capture": raise TechnicalReportValidationError("invalid Capture discriminator")
        for name in ("capture_id", "organization_id"): _uuid(getattr(self, name), name)
        _optional_uuid(self.engineering_object_id, "engineering_object_id")
        for name in ("source_version", "project_id", "creator_id"): _positive(getattr(self, name), name)
        if self.workspace_id is not None: _positive(self.workspace_id, "workspace_id")
        object.__setattr__(self, "discipline", None if self.discipline is None else EngineeringDiscipline(self.discipline))
        object.__setattr__(self, "source_kind", EngineeringExperienceSourceKind(self.source_kind))
        object.__setattr__(self, "lifecycle", EngineeringExperienceCaptureLifecycle(self.lifecycle))
        object.__setattr__(self, "original_content", _capture_content(self.original_content))
        if self.source_reference is not None: object.__setattr__(self, "source_reference", _single_line(self.source_reference, "source_reference", 512))
        _aware(self.created_at, "created_at")


@dataclass(frozen=True, slots=True)
class EvidenceHistoricalBasisV1:
    basis_schema_version: int; source_category: str; evidence_id: UUID; source_version: int
    organization_id: UUID; project_id: int | None; workspace_id: int | None
    lifecycle: EvidenceLifecycle; source_kind: EvidenceSourceKind; source_reference: str
    source_revision: str; source_standing: EvidenceSourceStanding; effective_at: datetime | None
    supported_fact: str; creator_id: int
    def __post_init__(self) -> None:
        if self.basis_schema_version != 1 or self.source_category != "evidence": raise TechnicalReportValidationError("invalid Evidence discriminator")
        for name in ("evidence_id", "organization_id"): _uuid(getattr(self, name), name)
        for name in ("source_version", "creator_id"): _positive(getattr(self, name), name)
        for name in ("project_id", "workspace_id"):
            if getattr(self, name) is not None: _positive(getattr(self, name), name)
        object.__setattr__(self, "lifecycle", EvidenceLifecycle(self.lifecycle)); object.__setattr__(self, "source_kind", EvidenceSourceKind(self.source_kind)); object.__setattr__(self, "source_standing", EvidenceSourceStanding(self.source_standing))
        object.__setattr__(self, "source_reference", _single_line(self.source_reference, "source_reference", 512)); object.__setattr__(self, "source_revision", _single_line(self.source_revision, "source_revision", 128)); object.__setattr__(self, "supported_fact", _nonempty(self.supported_fact, "supported_fact", 2000))
        if self.effective_at is not None: _aware(self.effective_at, "effective_at")


@dataclass(frozen=True, slots=True)
class EngineeringObjectHistoricalBasisV1:
    basis_schema_version: int; source_category: str; engineering_object_id: UUID; source_version: int
    organization_id: UUID; customer_id: int | None; project_id: int; workspace_id: int
    family: EngineeringObjectFamily; discipline: EngineeringDiscipline; object_type: EngineeringObjectType
    subtype: None; lifecycle: EngineeringLifecycle; authority_standing: EngineeringAuthorityStanding
    creator_id: int; steward_id: int
    def __post_init__(self) -> None:
        if self.basis_schema_version != 1 or self.source_category != "engineering_object" or self.subtype is not None: raise TechnicalReportValidationError("invalid EngineeringObject discriminator")
        for name in ("engineering_object_id", "organization_id"): _uuid(getattr(self, name), name)
        for name in ("source_version", "project_id", "workspace_id", "creator_id", "steward_id"): _positive(getattr(self, name), name)
        if self.customer_id is not None: _positive(self.customer_id, "customer_id")
        for name, enum_type in (("family", EngineeringObjectFamily), ("discipline", EngineeringDiscipline), ("object_type", EngineeringObjectType), ("lifecycle", EngineeringLifecycle), ("authority_standing", EngineeringAuthorityStanding)): object.__setattr__(self, name, enum_type(getattr(self, name)))


@dataclass(frozen=True, slots=True)
class EngineeringRelationshipHistoricalBasisV1:
    basis_schema_version: int; source_category: str; engineering_relationship_id: UUID; source_version: int
    organization_id: UUID; project_id: int; workspace_id: int; source_object_id: UUID; target_object_id: UUID
    relationship_family: RelationshipFamily; relationship_type: RelationshipType
    lifecycle: RelationshipLifecycle; authority_standing: EngineeringAuthorityStanding
    evidence_references: tuple[UUID, ...]; creator_id: int; steward_id: int; reviewer_id: int | None; approver_id: int | None
    def __post_init__(self) -> None:
        if self.basis_schema_version != 1 or self.source_category != "engineering_relationship": raise TechnicalReportValidationError("invalid Relationship discriminator")
        for name in ("engineering_relationship_id", "organization_id", "source_object_id", "target_object_id"): _uuid(getattr(self, name), name)
        for reference in self.evidence_references: _uuid(reference, "evidence_reference")
        if self.source_object_id == self.target_object_id: raise TechnicalReportValidationError("relationship endpoints must be distinct")
        for name in ("source_version", "project_id", "workspace_id", "creator_id", "steward_id"): _positive(getattr(self, name), name)
        for name in ("reviewer_id", "approver_id"):
            if getattr(self, name) is not None: _positive(getattr(self, name), name)
        for name, enum_type in (("relationship_family", RelationshipFamily), ("relationship_type", RelationshipType), ("lifecycle", RelationshipLifecycle), ("authority_standing", EngineeringAuthorityStanding)): object.__setattr__(self, name, enum_type(getattr(self, name)))
        if len(self.evidence_references) != len(set(self.evidence_references)): raise TechnicalReportValidationError("evidence_references must be unique")
        object.__setattr__(self, "evidence_references", tuple(sorted(self.evidence_references, key=str)))


HistoricalBasis: TypeAlias = CaptureHistoricalBasisV1 | EvidenceHistoricalBasisV1 | EngineeringObjectHistoricalBasisV1 | EngineeringRelationshipHistoricalBasisV1
_HISTORICAL_TYPES = (CaptureHistoricalBasisV1, EvidenceHistoricalBasisV1, EngineeringObjectHistoricalBasisV1, EngineeringRelationshipHistoricalBasisV1)


@dataclass(frozen=True, slots=True)
class ExternalHumanLocator:
    report_local_source_id: UUID; external_reference: str; submitted_by_id: int | None
    observed_at: datetime | None; retrieved_at: datetime | None; submitted_at: datetime | None
    minimal_representation: str
    def __post_init__(self) -> None:
        _uuid(self.report_local_source_id, "report_local_source_id")
        object.__setattr__(self, "external_reference", _single_line(self.external_reference, "external_reference", 512)); object.__setattr__(self, "minimal_representation", _nonempty(self.minimal_representation, "minimal_representation", 10000))
        if self.submitted_by_id is not None: _positive(self.submitted_by_id, "submitted_by_id")
        for name in ("observed_at", "retrieved_at", "submitted_at"):
            if getattr(self, name) is not None: _aware(getattr(self, name), name)
        if not any((self.observed_at, self.retrieved_at, self.submitted_at)):
            raise TechnicalReportValidationError("external/Human source requires an applicable source time")


@dataclass(frozen=True, slots=True)
class StandardLocator:
    standard_identity: str; issuing_authority: str; edition: str; clause_or_location: str
    minimal_representation: str; retrieved_at: datetime | None = None
    def __post_init__(self) -> None:
        for name in ("standard_identity", "issuing_authority", "edition", "clause_or_location"): object.__setattr__(self, name, _single_line(getattr(self, name), name, 512))
        object.__setattr__(self, "minimal_representation", _nonempty(self.minimal_representation, "minimal_representation", 10000))
        if self.retrieved_at is not None: _aware(self.retrieved_at, "retrieved_at")


@dataclass(frozen=True, slots=True)
class ContextualLocator:
    context_id: UUID; owning_context: str
    def __post_init__(self) -> None: _uuid(self.context_id, "context_id"); object.__setattr__(self, "owning_context", _single_line(self.owning_context, "owning_context", 128))


ProvenanceLocator: TypeAlias = HistoricalBasis | ExternalHumanLocator | StandardLocator | ContextualLocator


def _canonical(value: object, *, field_name: str | None = None) -> object:
    if is_dataclass(value) and not isinstance(value, type): return {field.name: _canonical(getattr(value, field.name), field_name=field.name) for field in fields(value)}
    if isinstance(value, UUID): return str(value).lower()
    if isinstance(value, datetime): _aware(value, field_name or "timestamp"); return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if isinstance(value, Enum): return value.value
    if isinstance(value, str): return unicodedata.normalize("NFC", value)
    if value is None or type(value) in (bool, int): return value
    if isinstance(value, float): raise TechnicalReportValidationError("floating-point values are prohibited")
    if isinstance(value, dict): return {str(key): _canonical(item, field_name=str(key)) for key, item in value.items()}
    if isinstance(value, (tuple, list)): return [_canonical(item) for item in value]
    raise TechnicalReportValidationError(f"unsupported canonical value: {type(value).__name__}")


def canonical_json(value: object) -> bytes:
    return json.dumps(_canonical(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def canonical_historical_json(value: HistoricalBasis) -> bytes:
    if not isinstance(value, _HISTORICAL_TYPES): raise TechnicalReportHistoricalBasisIncomplete("one closed historical basis is required")
    return canonical_json(value)


def historical_basis_digest(value: HistoricalBasis) -> str: return hashlib.sha256(canonical_historical_json(value)).hexdigest()


def verify_historical_basis_digest(value: HistoricalBasis, expected_digest: str) -> None:
    try:
        normalized = _sha256(expected_digest, "expected_digest")
    except TechnicalReportValidationError as exc:
        raise TechnicalReportIntegrityMismatch() from exc
    if not hmac.compare_digest(historical_basis_digest(value), normalized): raise TechnicalReportIntegrityMismatch()


@dataclass(frozen=True, slots=True)
class TechnicalReportProvenanceEntry:
    entry_id: UUID; ordinal: int; source_class: TechnicalReportSourceClass; source_type: TechnicalReportSourceType
    is_material: bool; owning_capability: TechnicalReportOwningCapability | None; reliance_role: str
    verification_status: TechnicalReportVerificationStatus; availability_status: TechnicalReportAvailabilityStatus
    origin_attribution: str; limitations: tuple[str, ...]; locator: ProvenanceLocator
    integrity_algorithm: TechnicalReportIntegrityAlgorithm | None; integrity_digest: str | None
    def __post_init__(self) -> None:
        _uuid(self.entry_id, "entry_id")
        object.__setattr__(self, "source_class", TechnicalReportSourceClass(self.source_class)); object.__setattr__(self, "source_type", TechnicalReportSourceType(self.source_type)); object.__setattr__(self, "verification_status", TechnicalReportVerificationStatus(self.verification_status)); object.__setattr__(self, "availability_status", TechnicalReportAvailabilityStatus(self.availability_status))
        if isinstance(self.ordinal, bool) or self.ordinal < 0: raise TechnicalReportValidationError("ordinal must not be negative")
        if type(self.is_material) is not bool: raise TechnicalReportValidationError("is_material must be boolean")
        if self.owning_capability is not None:
            object.__setattr__(self, "owning_capability", TechnicalReportOwningCapability(self.owning_capability))
        object.__setattr__(self, "reliance_role", _nonempty(self.reliance_role, "reliance_role")); object.__setattr__(self, "origin_attribution", _nonempty(self.origin_attribution, "origin_attribution")); object.__setattr__(self, "limitations", tuple(_nonempty(item, "limitations") for item in self.limitations))
        expected = {TechnicalReportSourceType.UNIVERSAL_CAPTURE: (TechnicalReportOwningCapability.UNIVERSAL_CAPTURE, CaptureHistoricalBasisV1), TechnicalReportSourceType.EVIDENCE: (TechnicalReportOwningCapability.EVIDENCE, EvidenceHistoricalBasisV1), TechnicalReportSourceType.ENGINEERING_OBJECT: (TechnicalReportOwningCapability.ENGINEERING_OBJECT, EngineeringObjectHistoricalBasisV1), TechnicalReportSourceType.ENGINEERING_RELATIONSHIP: (TechnicalReportOwningCapability.ENGINEERING_RELATIONSHIP, EngineeringRelationshipHistoricalBasisV1)}
        if self.source_class is TechnicalReportSourceClass.CANONICAL_MATERIAL:
            if self.source_type not in expected: raise TechnicalReportHistoricalBasisIncomplete("canonical source type is invalid")
            owner, locator_type = expected[self.source_type]
            if not self.is_material or self.owning_capability is not owner or not isinstance(self.locator, locator_type): raise TechnicalReportHistoricalBasisIncomplete("canonical source owner, type, and basis are incoherent")
        elif self.source_class is TechnicalReportSourceClass.EXTERNAL_OR_HUMAN_MATERIAL:
            if self.owning_capability is not None or not self.is_material or self.source_type is not TechnicalReportSourceType.EXTERNAL_OR_HUMAN or not isinstance(self.locator, ExternalHumanLocator): raise TechnicalReportHistoricalBasisIncomplete("external/Human locator is incoherent")
        elif self.source_class is TechnicalReportSourceClass.STANDARDS_MATERIAL:
            if self.owning_capability is not None or not self.is_material or self.source_type is not TechnicalReportSourceType.STANDARD or not isinstance(self.locator, StandardLocator): raise TechnicalReportHistoricalBasisIncomplete("standards locator is incoherent")
        elif self.source_class is TechnicalReportSourceClass.CONTEXTUAL_NON_MATERIAL:
            if self.owning_capability is not None or self.is_material or self.source_type is not TechnicalReportSourceType.CONTEXTUAL or not isinstance(self.locator, ContextualLocator): raise TechnicalReportHistoricalBasisIncomplete("contextual locator is incoherent")
        else: raise TechnicalReportHistoricalBasisIncomplete("unknown source class")
        if self.is_material:
            if self.integrity_algorithm is not TechnicalReportIntegrityAlgorithm.SHA256 or self.integrity_digest is None: raise TechnicalReportHistoricalBasisIncomplete("material source requires SHA-256 integrity")
            digest = _sha256(self.integrity_digest, "integrity_digest")
            if not hmac.compare_digest(hashlib.sha256(canonical_json(self.locator)).hexdigest(), digest): raise TechnicalReportIntegrityMismatch()
        elif self.integrity_algorithm is not None or self.integrity_digest is not None: raise TechnicalReportValidationError("contextual source cannot carry material integrity")


@dataclass(frozen=True, slots=True)
class TechnicalReportAcceptedSnapshot:
    report_id: UUID; purpose: TechnicalReportPurpose; organization_id: UUID; workspace_id: int; project_id: int | None
    content: TechnicalReportContent; qualification: PreliminaryQualification; provenance: tuple[TechnicalReportProvenanceEntry, ...]
    accepted_draft_revision: TechnicalReportDraftRevision; accepted_aggregate_version: int
    accepted_by_id: int; accepted_at: datetime; predecessor_report_id: UUID | None
    def __post_init__(self) -> None:
        for name in ("report_id", "organization_id"): _uuid(getattr(self, name), name)
        object.__setattr__(self, "purpose", TechnicalReportPurpose(self.purpose)); _instance(self.content, TechnicalReportContent, "content"); _instance(self.qualification, PreliminaryQualification, "qualification"); _instance(self.accepted_draft_revision, TechnicalReportDraftRevision, "accepted_draft_revision")
        if any(not isinstance(entry, TechnicalReportProvenanceEntry) for entry in self.provenance): raise TechnicalReportValidationError("provenance contains an invalid contract")
        _optional_uuid(self.predecessor_report_id, "predecessor_report_id")
        _positive(self.workspace_id, "workspace_id"); _positive(self.accepted_aggregate_version, "accepted_aggregate_version"); _positive(self.accepted_by_id, "accepted_by_id")
        if self.project_id is not None: _positive(self.project_id, "project_id")
        _aware(self.accepted_at, "accepted_at")
    @property
    def canonical_bytes(self) -> bytes: return canonical_json(self)
    @property
    def integrity_digest(self) -> str: return hashlib.sha256(self.canonical_bytes).hexdigest()


_ACCEPTED_SNAPSHOT_KEYS = {
    "report_id", "purpose", "organization_id", "workspace_id", "project_id",
    "content", "qualification", "provenance", "accepted_draft_revision",
    "accepted_aggregate_version", "accepted_by_id", "accepted_at",
    "predecessor_report_id",
}
_ACCEPTED_CONTENT_KEYS = {
    "engineering_scope", "technical_content", "assumptions", "uncertainty",
    "limitations", "conclusions", "recommendations",
}
_ACCEPTED_QUALIFICATION_KEYS = {
    "is_preliminary", "evidence_deficiencies", "unresolved_issues",
    "follow_up_requirements",
}


def _closed_payload(value: object, keys: set[str], field_name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise TechnicalReportValidationError(f"{field_name} has an invalid closed shape")
    return value


def _payload_uuid(value: object, field_name: str) -> UUID:
    if not isinstance(value, str) or value != value.lower():
        raise TechnicalReportValidationError(f"{field_name} must be a canonical UUID")
    try:
        parsed = UUID(value)
    except (ValueError, AttributeError) as exc:
        raise TechnicalReportValidationError(f"{field_name} must be a canonical UUID") from exc
    if str(parsed) != value:
        raise TechnicalReportValidationError(f"{field_name} must be a canonical UUID")
    return parsed


def _payload_optional_uuid(value: object, field_name: str) -> UUID | None:
    return None if value is None else _payload_uuid(value, field_name)


def _payload_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise TechnicalReportValidationError(f"{field_name} must be canonical UTC")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise TechnicalReportValidationError(f"{field_name} must be canonical UTC") from exc
    _aware(parsed, field_name)
    if parsed.strftime("%Y-%m-%dT%H:%M:%S.%fZ") != value:
        raise TechnicalReportValidationError(f"{field_name} must be canonical UTC")
    return parsed


def _payload_optional_datetime(value: object, field_name: str) -> datetime | None:
    return None if value is None else _payload_datetime(value, field_name)


def _payload_string_array(value: object, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise TechnicalReportValidationError(f"{field_name} must be a string array")
    return tuple(value)


_HISTORICAL_KEYS: dict[str, set[str]] = {
    "universal_capture": {field.name for field in fields(CaptureHistoricalBasisV1)},
    "evidence": {field.name for field in fields(EvidenceHistoricalBasisV1)},
    "engineering_object": {field.name for field in fields(EngineeringObjectHistoricalBasisV1)},
    "engineering_relationship": {field.name for field in fields(EngineeringRelationshipHistoricalBasisV1)},
}


def historical_basis_from_payload(payload: object, source_type: str) -> HistoricalBasis:
    """Reconstruct one exact closed canonical historical-basis contract."""

    if source_type not in _HISTORICAL_KEYS:
        raise TechnicalReportHistoricalBasisIncomplete("canonical source type is invalid")
    value = _closed_payload(payload, _HISTORICAL_KEYS[source_type], "historical basis")
    data = dict(value)
    try:
        if source_type == "universal_capture":
            data.update(
                capture_id=_payload_uuid(data["capture_id"], "capture_id"),
                organization_id=_payload_uuid(data["organization_id"], "organization_id"),
                engineering_object_id=_payload_optional_uuid(data["engineering_object_id"], "engineering_object_id"),
                created_at=_payload_datetime(data["created_at"], "created_at"),
            )
            return CaptureHistoricalBasisV1(**data)
        if source_type == "evidence":
            data.update(
                evidence_id=_payload_uuid(data["evidence_id"], "evidence_id"),
                organization_id=_payload_uuid(data["organization_id"], "organization_id"),
                effective_at=_payload_optional_datetime(data["effective_at"], "effective_at"),
            )
            return EvidenceHistoricalBasisV1(**data)
        if source_type == "engineering_object":
            data.update(
                engineering_object_id=_payload_uuid(data["engineering_object_id"], "engineering_object_id"),
                organization_id=_payload_uuid(data["organization_id"], "organization_id"),
            )
            return EngineeringObjectHistoricalBasisV1(**data)
        data.update(
            engineering_relationship_id=_payload_uuid(data["engineering_relationship_id"], "engineering_relationship_id"),
            organization_id=_payload_uuid(data["organization_id"], "organization_id"),
            source_object_id=_payload_uuid(data["source_object_id"], "source_object_id"),
            target_object_id=_payload_uuid(data["target_object_id"], "target_object_id"),
            evidence_references=tuple(_payload_uuid(item, "evidence_reference") for item in data["evidence_references"]),
        )
        return EngineeringRelationshipHistoricalBasisV1(**data)
    except (KeyError, TypeError, ValueError) as exc:
        raise TechnicalReportHistoricalBasisIncomplete("historical basis is invalid") from exc


def _locator_from_payload(payload: object, source_type: str) -> ProvenanceLocator:
    if source_type in _HISTORICAL_KEYS:
        return historical_basis_from_payload(payload, source_type)
    if source_type == "external_or_human":
        value = _closed_payload(payload, {field.name for field in fields(ExternalHumanLocator)}, "external/Human locator")
        return ExternalHumanLocator(
            report_local_source_id=_payload_uuid(value["report_local_source_id"], "report_local_source_id"),
            external_reference=value["external_reference"], submitted_by_id=value["submitted_by_id"],
            observed_at=_payload_optional_datetime(value["observed_at"], "observed_at"),
            retrieved_at=_payload_optional_datetime(value["retrieved_at"], "retrieved_at"),
            submitted_at=_payload_optional_datetime(value["submitted_at"], "submitted_at"),
            minimal_representation=value["minimal_representation"],
        )
    if source_type == "standard":
        value = _closed_payload(payload, {field.name for field in fields(StandardLocator)}, "standard locator")
        return StandardLocator(
            standard_identity=value["standard_identity"], issuing_authority=value["issuing_authority"],
            edition=value["edition"], clause_or_location=value["clause_or_location"],
            minimal_representation=value["minimal_representation"],
            retrieved_at=_payload_optional_datetime(value["retrieved_at"], "retrieved_at"),
        )
    if source_type == "contextual":
        value = _closed_payload(payload, {field.name for field in fields(ContextualLocator)}, "contextual locator")
        return ContextualLocator(_payload_uuid(value["context_id"], "context_id"), value["owning_context"])
    raise TechnicalReportHistoricalBasisIncomplete("provenance source type is invalid")


def _provenance_from_payload(payload: object) -> TechnicalReportProvenanceEntry:
    keys = {
        "entry_id", "ordinal", "source_class", "source_type", "is_material",
        "owning_capability", "reliance_role", "verification_status",
        "availability_status", "origin_attribution", "limitations", "locator",
        "integrity_algorithm", "integrity_digest",
    }
    value = _closed_payload(payload, keys, "accepted snapshot provenance")
    limitations = _payload_string_array(value["limitations"], "provenance limitations")
    return TechnicalReportProvenanceEntry(
        entry_id=_payload_uuid(value["entry_id"], "entry_id"), ordinal=value["ordinal"],
        source_class=value["source_class"], source_type=value["source_type"],
        is_material=value["is_material"], owning_capability=value["owning_capability"],
        reliance_role=value["reliance_role"], verification_status=value["verification_status"],
        availability_status=value["availability_status"], origin_attribution=value["origin_attribution"],
        limitations=limitations, locator=_locator_from_payload(value["locator"], value["source_type"]),
        integrity_algorithm=(None if value["integrity_algorithm"] is None
                             else TechnicalReportIntegrityAlgorithm(value["integrity_algorithm"])),
        integrity_digest=value["integrity_digest"],
    )


def accepted_snapshot_payload(snapshot: TechnicalReportAcceptedSnapshot) -> dict[str, object]:
    """Return the one canonical JSON-compatible accepted representation."""

    _instance(snapshot, TechnicalReportAcceptedSnapshot, "accepted_snapshot")
    payload = json.loads(snapshot.canonical_bytes)
    validate_accepted_snapshot_payload(payload, snapshot.integrity_digest)
    return payload


def validate_accepted_snapshot_payload(
    payload: object,
    expected_digest: str,
) -> dict[str, object]:
    """Validate closed persisted snapshot shape and canonical integrity."""

    digest = _sha256(expected_digest, "accepted_snapshot_digest")
    if not isinstance(payload, dict) or set(payload) != _ACCEPTED_SNAPSHOT_KEYS:
        raise TechnicalReportValidationError("accepted snapshot has an invalid closed shape")
    content = payload.get("content")
    qualification = payload.get("qualification")
    revision = payload.get("accepted_draft_revision")
    provenance = payload.get("provenance")
    if not isinstance(content, dict) or set(content) != _ACCEPTED_CONTENT_KEYS:
        raise TechnicalReportValidationError("accepted snapshot content is incomplete")
    if not isinstance(qualification, dict) or set(qualification) != _ACCEPTED_QUALIFICATION_KEYS:
        raise TechnicalReportValidationError("accepted snapshot qualification is incomplete")
    if not isinstance(revision, dict) or set(revision) != {"revision_id", "revision_number"}:
        raise TechnicalReportValidationError("accepted snapshot revision is incomplete")
    if not isinstance(provenance, list) or not provenance:
        raise TechnicalReportValidationError("accepted snapshot provenance is incomplete")
    if not all(isinstance(entry, dict) and set(entry) == {
        "entry_id", "ordinal", "source_class", "source_type", "is_material",
        "owning_capability", "reliance_role", "verification_status",
        "availability_status", "origin_attribution", "limitations", "locator",
        "integrity_algorithm", "integrity_digest",
    } for entry in provenance):
        raise TechnicalReportValidationError("accepted snapshot provenance shape is invalid")
    try:
        snapshot = TechnicalReportAcceptedSnapshot(
            report_id=_payload_uuid(payload["report_id"], "report_id"),
            purpose=payload["purpose"],
            organization_id=_payload_uuid(payload["organization_id"], "organization_id"),
            workspace_id=payload["workspace_id"], project_id=payload["project_id"],
            content=TechnicalReportContent(
                engineering_scope=content["engineering_scope"], technical_content=content["technical_content"],
                assumptions=_payload_string_array(content["assumptions"], "assumptions"), uncertainty=content["uncertainty"],
                limitations=_payload_string_array(content["limitations"], "limitations"), conclusions=content["conclusions"],
                recommendations=_payload_string_array(content["recommendations"], "recommendations"),
            ),
            qualification=PreliminaryQualification(
                is_preliminary=qualification["is_preliminary"],
                evidence_deficiencies=_payload_string_array(qualification["evidence_deficiencies"], "evidence_deficiencies"),
                unresolved_issues=_payload_string_array(qualification["unresolved_issues"], "unresolved_issues"),
                follow_up_requirements=_payload_string_array(qualification["follow_up_requirements"], "follow_up_requirements"),
            ),
            provenance=tuple(_provenance_from_payload(entry) for entry in provenance),
            accepted_draft_revision=TechnicalReportDraftRevision(
                _payload_uuid(revision["revision_id"], "revision_id"), revision["revision_number"]
            ),
            accepted_aggregate_version=payload["accepted_aggregate_version"],
            accepted_by_id=payload["accepted_by_id"],
            accepted_at=_payload_datetime(payload["accepted_at"], "accepted_at"),
            predecessor_report_id=_payload_optional_uuid(payload["predecessor_report_id"], "predecessor_report_id"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise TechnicalReportValidationError("accepted snapshot has invalid typed content") from exc
    actual = hashlib.sha256(snapshot.canonical_bytes).hexdigest()
    if not hmac.compare_digest(actual, digest):
        raise TechnicalReportIntegrityMismatch()
    return payload


@dataclass(frozen=True, slots=True)
class TechnicalReportAcceptanceRecord:
    accepted_by_id: int; accepted_at: datetime; accepted_draft_revision: TechnicalReportDraftRevision; accepted_aggregate_version: int; snapshot_digest: str
    def __post_init__(self) -> None:
        _instance(self.accepted_draft_revision, TechnicalReportDraftRevision, "accepted_draft_revision")
        _positive(self.accepted_by_id, "accepted_by_id"); _positive(self.accepted_aggregate_version, "accepted_aggregate_version"); _aware(self.accepted_at, "accepted_at")
        _sha256(self.snapshot_digest, "snapshot_digest")


@dataclass(frozen=True, slots=True)
class TechnicalReportDomainEvent:
    event_id: UUID; report_id: UUID; aggregate_version: int; event_type: str; command_id: UUID; correlation_id: UUID; occurred_at: datetime
    organization_id: UUID; workspace_id: int; project_id: int | None
    purpose: TechnicalReportPurpose; lifecycle: str; draft_revision_id: UUID
    actor_id: int; causation_id: UUID; predecessor_report_id: UUID | None
    source_entry_count: int
    def __post_init__(self) -> None:
        for name in ("event_id", "report_id", "command_id", "correlation_id", "organization_id", "draft_revision_id", "causation_id"): _uuid(getattr(self, name), name)
        _optional_uuid(self.predecessor_report_id, "predecessor_report_id")
        for name in ("aggregate_version", "workspace_id", "actor_id"): _positive(getattr(self, name), name)
        if self.project_id is not None: _positive(self.project_id, "project_id")
        if isinstance(self.source_entry_count, bool) or not isinstance(self.source_entry_count, int) or self.source_entry_count < 0: raise TechnicalReportValidationError("source_entry_count is invalid")
        object.__setattr__(self, "purpose", TechnicalReportPurpose(self.purpose))
        if self.lifecycle not in {"draft", "accepted"}: raise TechnicalReportValidationError("event lifecycle is invalid")
        event_type = _single_line(self.event_type, "event_type", 128)
        if event_type not in {
            "TechnicalReportDraftCreated",
            "TechnicalReportDraftRevised",
            "TechnicalReportAccepted",
            "TechnicalReportSuccessorCreated",
        }:
            raise TechnicalReportValidationError("event_type is invalid")
        object.__setattr__(self, "event_type", event_type); _aware(self.occurred_at, "occurred_at")


@dataclass(frozen=True, slots=True)
class TechnicalReportCommandResult:
    report_id: UUID; previous_version: int | None; version: int; draft_revision: TechnicalReportDraftRevision
    command_type: str; correlation_id: UUID; events: tuple[TechnicalReportDomainEvent, ...]
    def __post_init__(self) -> None:
        _uuid(self.report_id, "report_id"); _uuid(self.correlation_id, "correlation_id")
        _instance(self.draft_revision, TechnicalReportDraftRevision, "draft_revision")
        if not self.events or any(not isinstance(event, TechnicalReportDomainEvent) for event in self.events): raise TechnicalReportValidationError("events must contain typed Domain Events")
        _positive(self.version, "version"); object.__setattr__(self, "command_type", _single_line(self.command_type, "command_type", 128))
        if self.previous_version is not None: _positive(self.previous_version, "previous_version")
        if any(event.report_id != self.report_id or event.aggregate_version != self.version for event in self.events): raise TechnicalReportValidationError("command events are incoherent")
    @property
    def safe_lifecycle(self) -> TechnicalReportLifecycle:
        return TechnicalReportLifecycle(self.events[0].lifecycle)
    @property
    def occurred_at(self) -> datetime:
        return self.events[0].occurred_at


def _validate_scope(workspace_id: int, project_id: int | None) -> None:
    _positive(workspace_id, "workspace_id")
    if project_id is not None: _positive(project_id, "project_id")


@dataclass(frozen=True, slots=True)
class CreateTechnicalReportDraft:
    metadata: TechnicalReportCommandMetadata; organization_id: UUID; workspace_id: int; project_id: int | None; owner_id: int
    purpose: TechnicalReportPurpose; content: TechnicalReportContent; qualification: PreliminaryQualification; provenance: tuple[TechnicalReportProvenanceEntry, ...]
    def __post_init__(self) -> None:
        _instance(self.metadata, TechnicalReportCommandMetadata, "metadata"); _instance(self.content, TechnicalReportContent, "content"); _instance(self.qualification, PreliminaryQualification, "qualification")
        if any(not isinstance(entry, TechnicalReportProvenanceEntry) for entry in self.provenance): raise TechnicalReportValidationError("provenance contains an invalid contract")
        _uuid(self.organization_id, "organization_id"); _positive(self.owner_id, "owner_id"); _validate_scope(self.workspace_id, self.project_id); object.__setattr__(self, "purpose", TechnicalReportPurpose(self.purpose))


@dataclass(frozen=True, slots=True)
class ReviseTechnicalReportDraft:
    metadata: TechnicalReportCommandMetadata; report_id: UUID; expected_version: int; expected_draft_revision_id: UUID
    content: TechnicalReportContent; qualification: PreliminaryQualification; provenance: tuple[TechnicalReportProvenanceEntry, ...]
    def __post_init__(self) -> None:
        _instance(self.metadata, TechnicalReportCommandMetadata, "metadata"); _instance(self.content, TechnicalReportContent, "content"); _instance(self.qualification, PreliminaryQualification, "qualification")
        if any(not isinstance(entry, TechnicalReportProvenanceEntry) for entry in self.provenance): raise TechnicalReportValidationError("provenance contains an invalid contract")
        _uuid(self.report_id, "report_id"); _uuid(self.expected_draft_revision_id, "expected_draft_revision_id"); _positive(self.expected_version, "expected_version")


@dataclass(frozen=True, slots=True)
class AcceptanceConfirmation:
    expected_version: int; exact_draft_revision_id: UUID; confirmed: bool
    def __post_init__(self) -> None:
        _uuid(self.exact_draft_revision_id, "exact_draft_revision_id")
        _positive(self.expected_version, "expected_version")
        if type(self.confirmed) is not bool or not self.confirmed: raise TechnicalReportValidationError("explicit Human acceptance confirmation is required")


@dataclass(frozen=True, slots=True)
class AcceptExactTechnicalReportDraft:
    metadata: TechnicalReportCommandMetadata; report_id: UUID; confirmation: AcceptanceConfirmation
    def __post_init__(self) -> None: _instance(self.metadata, TechnicalReportCommandMetadata, "metadata"); _instance(self.confirmation, AcceptanceConfirmation, "confirmation"); _uuid(self.report_id, "report_id")


@dataclass(frozen=True, slots=True)
class CreateTechnicalReportSuccessor:
    metadata: TechnicalReportCommandMetadata; predecessor_report_id: UUID; expected_predecessor_version: int
    workspace_id: int; project_id: int | None; purpose: TechnicalReportPurpose; content: TechnicalReportContent
    qualification: PreliminaryQualification; provenance: tuple[TechnicalReportProvenanceEntry, ...]
    selected_copy_references: tuple[UUID, ...] = ()
    def __post_init__(self) -> None:
        _instance(self.metadata, TechnicalReportCommandMetadata, "metadata"); _instance(self.content, TechnicalReportContent, "content"); _instance(self.qualification, PreliminaryQualification, "qualification")
        if any(not isinstance(entry, TechnicalReportProvenanceEntry) for entry in self.provenance): raise TechnicalReportValidationError("provenance contains an invalid contract")
        _uuid(self.predecessor_report_id, "predecessor_report_id"); _positive(self.expected_predecessor_version, "expected_predecessor_version"); _validate_scope(self.workspace_id, self.project_id); object.__setattr__(self, "purpose", TechnicalReportPurpose(self.purpose))
        if any(not isinstance(value, UUID) for value in self.selected_copy_references): raise TechnicalReportValidationError("selected copy reference is invalid")
        if len(self.selected_copy_references) != len(set(self.selected_copy_references)): raise TechnicalReportValidationError("selected copy references must be unique")
        object.__setattr__(self, "selected_copy_references", tuple(self.selected_copy_references))


class TechnicalReportOutboxRecord(Base):
    """Persistence-only outbox row; Batch 2 defines no emission behavior."""

    __tablename__ = "technical_report_outbox"
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_technical_report_outbox_event"),
        UniqueConstraint("aggregate_id", "aggregate_version", "event_type", name="uq_technical_report_outbox_aggregate_event"),
        CheckConstraint("aggregate_version >= 1", name="ck_technical_report_outbox_version"),
        CheckConstraint("schema_version = 1", name="ck_technical_report_outbox_schema_version"),
        Index("ix_technical_report_outbox_unpublished", "published_at", "occurred_at"),
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_id = Column(PGUUID(as_uuid=True), nullable=False)
    aggregate_id = Column(PGUUID(as_uuid=True), ForeignKey("technical_reports.id", ondelete="RESTRICT"), nullable=False)
    aggregate_version = Column(Integer, nullable=False)
    event_type = Column(String(128), nullable=False)
    schema_version = Column(Integer, nullable=False, default=1, server_default="1")
    payload = Column(JSON, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class TechnicalReportIdempotencyRecord(Base):
    """Persistence-only idempotency row; Batch 2 defines no orchestration."""

    __tablename__ = "technical_report_idempotency"
    __table_args__ = (
        UniqueConstraint("organization_id", "actor_id", "command_type", "idempotency_id", name="uq_technical_report_idempotency_scope"),
        CheckConstraint("status IN ('pending','completed')", name="ck_technical_report_idempotency_status"),
        Index("ix_technical_report_idempotency_lookup", "organization_id", "actor_id", "command_type", "idempotency_id"),
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    command_type = Column(String(128), nullable=False)
    idempotency_id = Column(PGUUID(as_uuid=True), nullable=False)
    request_fingerprint = Column(String(64), nullable=False)
    status = Column(String(16), nullable=False, default="pending", server_default="pending")
    aggregate_id = Column(PGUUID(as_uuid=True), ForeignKey("technical_reports.id", ondelete="RESTRICT"))
    result = Column(JSON)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
