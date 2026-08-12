"""PATCH-032 persistence-independent Technical Report Aggregate Root."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, event, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.sql import func

from app.core.database import Base

from app.enums.technical_report import (
    TechnicalReportLifecycle,
    TechnicalReportPurpose,
    TechnicalReportSourceClass,
    TechnicalReportSourceType,
)
from app.exceptions.technical_report import (
    TechnicalReportAcceptedImmutable,
    TechnicalReportAuthorizationDenied,
    TechnicalReportHistoricalBasisIncomplete,
    TechnicalReportInvalidLifecycle,
    TechnicalReportInvalidLineage,
    TechnicalReportValidationError,
    TechnicalReportVersionConflict,
)
from app.models.technical_report_command import (
    AcceptExactTechnicalReportDraft,
    CreateTechnicalReportDraft,
    CreateTechnicalReportSuccessor,
    PreliminaryQualification,
    ReviseTechnicalReportDraft,
    TechnicalReportAcceptedSnapshot,
    TechnicalReportAcceptanceRecord,
    TechnicalReportCommandResult,
    TechnicalReportContent,
    TechnicalReportDomainEvent,
    TechnicalReportDraftRevision,
    TechnicalReportProvenanceEntry,
    historical_basis_from_payload,
    validate_accepted_snapshot_payload,
    _aware,
)


class TechnicalReport:
    """Aggregate whose state changes only through explicit domain commands."""

    __slots__ = (
        "_id", "_organization_id", "_workspace_id", "_project_id", "_owner_id",
        "_purpose", "_content", "_qualification", "_provenance", "_draft_revision",
        "_lifecycle", "_predecessor_report_id", "_version", "_accepted_snapshot",
        "_acceptance_record", "_created_at", "_updated_at",
    )

    def __init__(self) -> None:
        raise TypeError("TechnicalReport must be created through an Aggregate factory")

    @property
    def id(self) -> UUID: return self._id
    @property
    def organization_id(self) -> UUID: return self._organization_id
    @property
    def workspace_id(self) -> int: return self._workspace_id
    @property
    def project_id(self) -> int | None: return self._project_id
    @property
    def owner_id(self) -> int: return self._owner_id
    @property
    def purpose(self) -> TechnicalReportPurpose: return self._purpose
    @property
    def content(self) -> TechnicalReportContent: return self._content
    @property
    def engineering_scope(self) -> str: return self._content.engineering_scope
    @property
    def draft_content(self) -> str: return self._content.technical_content
    @property
    def assumptions(self) -> tuple[str, ...]: return self._content.assumptions
    @property
    def uncertainty(self) -> str: return self._content.uncertainty
    @property
    def limitations(self) -> tuple[str, ...]: return self._content.limitations
    @property
    def conclusions(self) -> str: return self._content.conclusions
    @property
    def recommendations(self) -> tuple[str, ...]: return self._content.recommendations
    @property
    def qualification(self) -> PreliminaryQualification: return self._qualification
    @property
    def provenance(self) -> tuple[TechnicalReportProvenanceEntry, ...]: return self._provenance
    @property
    def draft_revision(self) -> TechnicalReportDraftRevision: return self._draft_revision
    @property
    def draft_revision_id(self) -> UUID: return self._draft_revision.revision_id
    @property
    def lifecycle(self) -> TechnicalReportLifecycle: return self._lifecycle
    @property
    def predecessor_report_id(self) -> UUID | None: return self._predecessor_report_id
    @property
    def version(self) -> int: return self._version
    @property
    def accepted_snapshot(self) -> TechnicalReportAcceptedSnapshot | None: return self._accepted_snapshot
    @property
    def acceptance_record(self) -> TechnicalReportAcceptanceRecord | None: return self._acceptance_record
    @property
    def accepted_by_id(self) -> int | None: return None if self._acceptance_record is None else self._acceptance_record.accepted_by_id
    @property
    def accepted_at(self) -> datetime | None: return None if self._acceptance_record is None else self._acceptance_record.accepted_at
    @property
    def accepted_draft_revision_id(self) -> UUID | None: return None if self._acceptance_record is None else self._acceptance_record.accepted_draft_revision.revision_id
    @property
    def accepted_aggregate_version(self) -> int | None: return None if self._acceptance_record is None else self._acceptance_record.accepted_aggregate_version
    @property
    def created_at(self) -> datetime: return self._created_at
    @property
    def updated_at(self) -> datetime: return self._updated_at

    @classmethod
    def _build(cls, **state: object) -> TechnicalReport:
        report = object.__new__(cls)
        for name, value in state.items(): object.__setattr__(report, f"_{name}", value)
        return report

    @classmethod
    def create(cls, command: CreateTechnicalReportDraft, now: datetime) -> tuple[TechnicalReport, TechnicalReportCommandResult]:
        _aware(now, "now")
        if command.organization_id != command.metadata.actor.organization_id or command.owner_id != command.metadata.actor.actor_id: raise TechnicalReportAuthorizationDenied()
        cls._validate_provenance(command.provenance)
        report = cls._build(id=uuid4(), organization_id=command.organization_id, workspace_id=command.workspace_id, project_id=command.project_id, owner_id=command.owner_id, purpose=command.purpose, content=command.content, qualification=command.qualification, provenance=tuple(command.provenance), draft_revision=TechnicalReportDraftRevision(uuid4(), 1), lifecycle=TechnicalReportLifecycle.DRAFT, predecessor_report_id=None, version=1, accepted_snapshot=None, acceptance_record=None, created_at=now, updated_at=now)
        return report, report._make_result(report.id, report.version, report.draft_revision, command, None, now, "TechnicalReportDraftCreated", TechnicalReportLifecycle.DRAFT, report.provenance)

    def revise(self, command: ReviseTechnicalReportDraft, now: datetime) -> TechnicalReportCommandResult:
        _aware(now, "now")
        self._require_owner(command.metadata.actor.actor_id, command.metadata.actor.organization_id); self._require_draft(); self._require_identity_version(command.report_id, command.expected_version, command.expected_draft_revision_id); self._validate_provenance(command.provenance)
        if command.content == self.content and command.qualification == self.qualification and command.provenance == self.provenance: raise TechnicalReportValidationError("draft revision must change semantic state")
        previous = self.version; next_version = previous + 1
        next_revision = TechnicalReportDraftRevision(uuid4(), self.draft_revision.revision_number + 1)
        result = self._make_result(self.id, next_version, next_revision, command, previous, now, "TechnicalReportDraftRevised", TechnicalReportLifecycle.DRAFT, command.provenance)
        object.__setattr__(self, "_content", command.content); object.__setattr__(self, "_qualification", command.qualification); object.__setattr__(self, "_provenance", tuple(command.provenance)); object.__setattr__(self, "_draft_revision", next_revision); object.__setattr__(self, "_version", next_version); object.__setattr__(self, "_updated_at", now)
        return result

    def accept_exact_draft(self, command: AcceptExactTechnicalReportDraft, now: datetime) -> TechnicalReportCommandResult:
        _aware(now, "now")
        self._require_owner(command.metadata.actor.actor_id, command.metadata.actor.organization_id); self._require_draft(); self._require_identity_version(command.report_id, command.confirmation.expected_version, command.confirmation.exact_draft_revision_id); self._validate_provenance(self.provenance, True)
        previous = self.version; resulting = previous + 1
        snapshot = TechnicalReportAcceptedSnapshot(self.id, self.purpose, self.organization_id, self.workspace_id, self.project_id, self.content, self.qualification, self.provenance, self.draft_revision, resulting, command.metadata.actor.actor_id, now, self.predecessor_report_id)
        record = TechnicalReportAcceptanceRecord(command.metadata.actor.actor_id, now, self.draft_revision, resulting, snapshot.integrity_digest)
        result = self._make_result(self.id, resulting, self.draft_revision, command, previous, now, "TechnicalReportAccepted", TechnicalReportLifecycle.ACCEPTED, self.provenance)
        object.__setattr__(self, "_lifecycle", TechnicalReportLifecycle.ACCEPTED); object.__setattr__(self, "_version", resulting); object.__setattr__(self, "_accepted_snapshot", snapshot); object.__setattr__(self, "_acceptance_record", record); object.__setattr__(self, "_updated_at", now)
        return result

    def create_successor(self, command: CreateTechnicalReportSuccessor, now: datetime) -> tuple[TechnicalReport, TechnicalReportCommandResult]:
        _aware(now, "now")
        self._require_owner(command.metadata.actor.actor_id, command.metadata.actor.organization_id)
        if self.lifecycle is not TechnicalReportLifecycle.ACCEPTED: raise TechnicalReportInvalidLineage("successor requires an accepted predecessor")
        if command.predecessor_report_id != self.id or command.expected_predecessor_version != self.version: raise TechnicalReportVersionConflict()
        if command.workspace_id != self.workspace_id or command.project_id != self.project_id: raise TechnicalReportInvalidLineage("successor scope must match predecessor")
        create = CreateTechnicalReportDraft(command.metadata, self.organization_id, command.workspace_id, command.project_id, command.metadata.actor.actor_id, command.purpose, command.content, command.qualification, command.provenance)
        successor, _ = self.create(create, now); object.__setattr__(successor, "_predecessor_report_id", self.id)
        return successor, successor._make_result(successor.id, successor.version, successor.draft_revision, command, None, now, "TechnicalReportSuccessorCreated", TechnicalReportLifecycle.DRAFT, successor.provenance)

    def _require_owner(self, actor_id: int, organization_id: UUID) -> None:
        if actor_id != self.owner_id or organization_id != self.organization_id: raise TechnicalReportAuthorizationDenied()
    def _require_draft(self) -> None:
        if self.lifecycle is TechnicalReportLifecycle.ACCEPTED: raise TechnicalReportAcceptedImmutable()
        if self.lifecycle is not TechnicalReportLifecycle.DRAFT: raise TechnicalReportInvalidLifecycle()
    def _require_identity_version(self, report_id: UUID, expected_version: int, revision_id: UUID) -> None:
        if report_id != self.id: raise TechnicalReportValidationError("Technical Report identity mismatch")
        if expected_version != self.version or revision_id != self.draft_revision_id: raise TechnicalReportVersionConflict()
    @staticmethod
    def _validate_provenance(entries: tuple[TechnicalReportProvenanceEntry, ...], require_material: bool = False) -> None:
        ordinals = [entry.ordinal for entry in entries]
        if ordinals != list(range(len(entries))): raise TechnicalReportValidationError("provenance ordinals must be unique and contiguous")
        if require_material and not any(entry.is_material for entry in entries): raise TechnicalReportHistoricalBasisIncomplete("acceptance requires at least one material source")
    def _make_result(self, report_id: UUID, version: int, revision: TechnicalReportDraftRevision, command: object, previous: int | None, now: datetime, event_type: str, lifecycle: TechnicalReportLifecycle, provenance: tuple[TechnicalReportProvenanceEntry, ...]) -> TechnicalReportCommandResult:
        metadata = command.metadata
        event = TechnicalReportDomainEvent(
            uuid4(), report_id, version, event_type, metadata.command_id,
            metadata.correlation_id, now, self.organization_id, self.workspace_id,
            self.project_id, self.purpose, lifecycle.value, revision.revision_id,
            metadata.actor.actor_id, metadata.command_id, self.predecessor_report_id,
            len(provenance),
        )
        return TechnicalReportCommandResult(report_id, previous, version, revision, type(command).__name__, metadata.correlation_id, (event,))


def _enum_values(enum_type: type) -> str:
    return ",".join(f"'{item.value}'" for item in enum_type)


class TechnicalReportRecord(Base):
    """Persistence record kept separate from the protected domain Aggregate."""

    __tablename__ = "technical_reports"
    __table_args__ = (
        CheckConstraint(f"purpose IN ({_enum_values(TechnicalReportPurpose)})", name="ck_technical_reports_purpose"),
        CheckConstraint(f"lifecycle IN ({_enum_values(TechnicalReportLifecycle)})", name="ck_technical_reports_lifecycle"),
        CheckConstraint("version >= 1", name="ck_technical_reports_version"),
        CheckConstraint("draft_revision_number >= 1", name="ck_technical_reports_draft_revision_number"),
        CheckConstraint("predecessor_report_id IS NULL OR predecessor_report_id <> id", name="ck_technical_reports_distinct_predecessor"),
        CheckConstraint(
            "(lifecycle = 'draft' AND accepted_snapshot IS NULL AND accepted_snapshot_digest IS NULL "
            "AND accepted_by_id IS NULL AND accepted_at IS NULL AND accepted_draft_revision_id IS NULL "
            "AND accepted_aggregate_version IS NULL) OR "
            "(lifecycle = 'accepted' AND accepted_snapshot IS NOT NULL AND accepted_snapshot_digest IS NOT NULL "
            "AND accepted_by_id IS NOT NULL AND accepted_at IS NOT NULL AND accepted_draft_revision_id IS NOT NULL "
            "AND accepted_aggregate_version IS NOT NULL AND accepted_aggregate_version = version)",
            name="ck_technical_reports_acceptance_coherence",
        ),
        CheckConstraint(
            "NOT is_preliminary OR json_array_length(evidence_deficiencies) + "
            "json_array_length(unresolved_issues) + json_array_length(follow_up_requirements) > 0",
            name="ck_technical_reports_preliminary_basis",
        ),
        CheckConstraint("updated_at >= created_at", name="ck_technical_reports_timestamp_order"),
        CheckConstraint("accepted_snapshot_digest IS NULL OR accepted_snapshot_digest ~ '^[0-9a-f]{64}$'", name="ck_technical_reports_snapshot_digest"),
        Index("ix_technical_reports_workspace_order", "organization_id", "workspace_id", "lifecycle", text("updated_at DESC"), text("id DESC")),
        Index("ix_technical_reports_project_order", "organization_id", "project_id", "lifecycle", text("updated_at DESC"), text("id DESC")),
        Index("ix_technical_reports_owner_lifecycle", "organization_id", "owner_id", "lifecycle"),
        Index("ix_technical_reports_predecessor", "predecessor_report_id"),
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="RESTRICT"))
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    purpose = Column(String(32), nullable=False)
    engineering_scope = Column(Text, nullable=False)
    draft_content = Column(Text, nullable=False)
    assumptions = Column(JSON, nullable=False, default=list)
    uncertainty = Column(Text, nullable=False)
    limitations = Column(JSON, nullable=False, default=list)
    conclusions = Column(Text, nullable=False)
    recommendations = Column(JSON, nullable=False, default=list)
    is_preliminary = Column(Boolean, nullable=False, default=False, server_default="false")
    evidence_deficiencies = Column(JSON, nullable=False, default=list)
    unresolved_issues = Column(JSON, nullable=False, default=list)
    follow_up_requirements = Column(JSON, nullable=False, default=list)
    draft_revision_id = Column(PGUUID(as_uuid=True), nullable=False)
    draft_revision_number = Column(Integer, nullable=False)
    lifecycle = Column(String(16), nullable=False, default="draft", server_default="draft")
    predecessor_report_id = Column(PGUUID(as_uuid=True), ForeignKey("technical_reports.id", ondelete="RESTRICT"))
    version = Column(Integer, nullable=False, default=1, server_default="1")
    accepted_snapshot = Column(JSONB)
    accepted_snapshot_digest = Column(String(64))
    accepted_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"))
    accepted_at = Column(DateTime(timezone=True))
    accepted_draft_revision_id = Column(PGUUID(as_uuid=True))
    accepted_aggregate_version = Column(Integer)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class TechnicalReportProvenanceRecord(Base):
    """Typed persistence representation of an Aggregate-owned source entry."""

    __tablename__ = "technical_report_provenance_entries"
    __table_args__ = (
        UniqueConstraint("technical_report_id", "ordinal", name="uq_technical_report_provenance_ordinal"),
        CheckConstraint(f"source_class IN ({_enum_values(TechnicalReportSourceClass)})", name="ck_technical_report_provenance_source_class"),
        CheckConstraint(f"source_type IN ({_enum_values(TechnicalReportSourceType)})", name="ck_technical_report_provenance_source_type"),
        CheckConstraint("verification_status IN ('verified','unverified')", name="ck_technical_report_provenance_verification"),
        CheckConstraint("availability_status IN ('available','unavailable')", name="ck_technical_report_provenance_availability"),
        CheckConstraint("ordinal >= 0", name="ck_technical_report_provenance_ordinal"),
        CheckConstraint("capture_version IS NULL OR capture_version >= 1", name="ck_technical_report_provenance_capture_version"),
        CheckConstraint("evidence_version IS NULL OR evidence_version >= 1", name="ck_technical_report_provenance_evidence_version"),
        CheckConstraint("engineering_object_version IS NULL OR engineering_object_version >= 1", name="ck_technical_report_provenance_object_version"),
        CheckConstraint("engineering_relationship_version IS NULL OR engineering_relationship_version >= 1", name="ck_technical_report_provenance_relationship_version"),
        CheckConstraint(
            "(source_type='universal_capture' AND capture_id IS NOT NULL AND capture_version IS NOT NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR "
            "(source_type='evidence' AND evidence_id IS NOT NULL AND evidence_version IS NOT NULL AND capture_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR "
            "(source_type='engineering_object' AND engineering_object_id IS NOT NULL AND engineering_object_version IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_relationship_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR "
            "(source_type='engineering_relationship' AND engineering_relationship_id IS NOT NULL AND engineering_relationship_version IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR "
            "(source_type='external_or_human' AND report_local_source_id IS NOT NULL AND external_reference IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR "
            "(source_type='standard' AND standard_identity IS NOT NULL AND issuing_authority IS NOT NULL AND edition IS NOT NULL AND clause_or_location IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND report_local_source_id IS NULL AND context_id IS NULL) OR "
            "(source_type='contextual' AND context_id IS NOT NULL AND owning_context IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL)",
            name="ck_technical_report_provenance_locator_shape",
        ),
        CheckConstraint(
            "(source_type='universal_capture' AND source_class='canonical_material' AND owning_capability='universal_capture' AND is_material) OR "
            "(source_type='evidence' AND source_class='canonical_material' AND owning_capability='evidence' AND is_material) OR "
            "(source_type='engineering_object' AND source_class='canonical_material' AND owning_capability='engineering_object' AND is_material) OR "
            "(source_type='engineering_relationship' AND source_class='canonical_material' AND owning_capability='engineering_relationship' AND is_material) OR "
            "(source_type='external_or_human' AND source_class='external_or_human_material' AND owning_capability IS NULL AND is_material) OR "
            "(source_type='standard' AND source_class='standards_material' AND owning_capability IS NULL AND is_material) OR "
            "(source_type='contextual' AND source_class='contextual_non_material' AND owning_capability IS NULL AND NOT is_material)",
            name="ck_technical_report_provenance_owner_coherence",
        ),
        CheckConstraint("NOT is_material OR (integrity_algorithm='sha256' AND integrity_digest IS NOT NULL)", name="ck_technical_report_provenance_material_integrity"),
        CheckConstraint("integrity_digest IS NULL OR integrity_digest ~ '^[0-9a-f]{64}$'", name="ck_technical_report_provenance_digest_format"),
        CheckConstraint(
            "(source_class='canonical_material' AND ((canonical_snapshot_id IS NOT NULL AND minimal_historical_representation IS NULL) OR (canonical_snapshot_id IS NULL AND minimal_historical_representation IS NOT NULL))) OR "
            "(source_class IN ('external_or_human_material','standards_material') AND canonical_snapshot_id IS NULL AND minimal_historical_representation IS NOT NULL) OR "
            "(source_class='contextual_non_material' AND canonical_snapshot_id IS NULL AND minimal_historical_representation IS NULL AND integrity_algorithm IS NULL AND integrity_digest IS NULL)",
            name="ck_technical_report_provenance_historical_basis",
        ),
        Index("ix_technical_report_provenance_report", "technical_report_id", "ordinal"),
        Index("ix_technical_report_provenance_capture", "capture_id", postgresql_where=text("capture_id IS NOT NULL")),
        Index("ix_technical_report_provenance_evidence", "evidence_id", postgresql_where=text("evidence_id IS NOT NULL")),
        Index("ix_technical_report_provenance_object", "engineering_object_id", postgresql_where=text("engineering_object_id IS NOT NULL")),
        Index("ix_technical_report_provenance_relationship", "engineering_relationship_id", postgresql_where=text("engineering_relationship_id IS NOT NULL")),
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    technical_report_id = Column(PGUUID(as_uuid=True), ForeignKey("technical_reports.id", ondelete="RESTRICT"), nullable=False)
    ordinal = Column(Integer, nullable=False)
    source_class = Column(String(40), nullable=False)
    source_type = Column(String(40), nullable=False)
    is_material = Column(Boolean, nullable=False)
    owning_capability = Column(String(40))
    reliance_role = Column(Text, nullable=False)
    verification_status = Column(String(16), nullable=False)
    availability_status = Column(String(16), nullable=False)
    origin_attribution = Column(Text, nullable=False)
    limitations = Column(JSON, nullable=False, default=list)
    observed_at = Column(DateTime(timezone=True))
    retrieved_at = Column(DateTime(timezone=True))
    submitted_at = Column(DateTime(timezone=True))
    integrity_algorithm = Column(String(16))
    integrity_digest = Column(String(64))
    minimal_historical_representation = Column(JSON)
    capture_id = Column(PGUUID(as_uuid=True))
    capture_version = Column(Integer)
    evidence_id = Column(PGUUID(as_uuid=True))
    evidence_version = Column(Integer)
    engineering_object_id = Column(PGUUID(as_uuid=True))
    engineering_object_version = Column(Integer)
    engineering_relationship_id = Column(PGUUID(as_uuid=True))
    engineering_relationship_version = Column(Integer)
    canonical_snapshot_id = Column(PGUUID(as_uuid=True))
    report_local_source_id = Column(PGUUID(as_uuid=True))
    external_reference = Column(Text)
    submitted_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"))
    standard_identity = Column(Text)
    issuing_authority = Column(Text)
    edition = Column(Text)
    clause_or_location = Column(Text)
    context_id = Column(PGUUID(as_uuid=True))
    owning_context = Column(String(128))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


@event.listens_for(TechnicalReportRecord, "before_insert")
@event.listens_for(TechnicalReportRecord, "before_update")
def _validate_persisted_accepted_snapshot(_mapper, _connection, target: TechnicalReportRecord) -> None:
    if target.lifecycle == TechnicalReportLifecycle.ACCEPTED.value:
        validate_accepted_snapshot_payload(target.accepted_snapshot, target.accepted_snapshot_digest)


@event.listens_for(TechnicalReportProvenanceRecord, "before_insert")
@event.listens_for(TechnicalReportProvenanceRecord, "before_update")
def _validate_persisted_historical_basis(_mapper, _connection, target: TechnicalReportProvenanceRecord) -> None:
    if target.source_class == TechnicalReportSourceClass.CANONICAL_MATERIAL.value:
        if target.canonical_snapshot_id is None:
            historical_basis_from_payload(target.minimal_historical_representation, target.source_type)
        elif target.minimal_historical_representation is not None:
            raise TechnicalReportValidationError("canonical provenance historical basis is ambiguous")
