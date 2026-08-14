"""No-commit SQLAlchemy persistence for PATCH-034 Organizational Memory."""

from __future__ import annotations

from datetime import datetime
import json
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CHAR,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
    text,
    update,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.database import Base
from app.enums.organizational_memory import MemoryStanding
from app.models.organizational_memory import OrganizationalMemory
from app.models.organizational_memory_command import (
    AcceptedReportSource,
    ActiveMemoryCriteria,
    AdmittedQualificationV1,
    AdmittedReportProjectionV1,
    AdmittedTechnicalContentV1,
    MemoryProvenanceDigestEntry,
    MemorySourceManifestV1,
    MemoryStandingHistoryRecord,
    canonical_json,
)
from app.ports.organizational_memory import MemoryCandidatePage


class OrganizationalMemoryRecord(Base):
    __tablename__ = "organizational_memories"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "source_report_id", "source_accepted_version",
            name="uq_organizational_memory_source",
        ),
        CheckConstraint("workspace_id > 0", name="ck_organizational_memories_workspace_positive"),
        CheckConstraint("project_id IS NULL OR project_id > 0", name="ck_organizational_memories_project_positive"),
        CheckConstraint("version > 0", name="ck_organizational_memories_version_positive"),
        CheckConstraint("standing IN ('active','withdrawn','superseded')", name="ck_organizational_memories_standing"),
        CheckConstraint("source_accepted_version > 0", name="ck_organizational_memories_source_version"),
        CheckConstraint("source_snapshot_digest ~ '^[0-9a-f]{64}$'", name="ck_organizational_memories_source_digest"),
        CheckConstraint("projection_contract = 'organizational_memory.accepted_report.v1'", name="ck_organizational_memories_projection_contract"),
        CheckConstraint("projection_digest ~ '^[0-9a-f]{64}$'", name="ck_organizational_memories_projection_digest"),
        CheckConstraint("provenance_digest ~ '^[0-9a-f]{64}$'", name="ck_organizational_memories_provenance_digest"),
        CheckConstraint("admitted_by_id > 0", name="ck_organizational_memories_admitted_by"),
        CheckConstraint("predecessor_memory_id IS NULL OR predecessor_memory_id <> id", name="ck_organizational_memories_distinct_predecessor"),
        CheckConstraint("replacement_memory_id IS NULL OR replacement_memory_id <> id", name="ck_organizational_memories_distinct_replacement"),
        CheckConstraint("cardinality(audience_actor_ids) <= 100 AND NOT (0 = ANY(audience_actor_ids))", name="ck_organizational_memories_audience_bound"),
        CheckConstraint("jsonb_typeof(reuse_restrictions) = 'array' AND jsonb_array_length(reuse_restrictions) <= 32", name="ck_organizational_memories_restrictions_bound"),
        CheckConstraint("updated_at >= created_at", name="ck_organizational_memories_timestamp_order"),
        CheckConstraint("organizational_memory_projection_v1_valid(projection)", name="ck_organizational_memories_projection_valid"),
        CheckConstraint("organizational_memory_manifest_v1_valid(manifest)", name="ck_organizational_memories_manifest_valid"),
        CheckConstraint("projection_digest=encode(sha256(convert_to(organizational_memory_canonical_json(projection),'UTF8')),'hex')", name="ck_organizational_memories_projection_digest_coherent"),
        CheckConstraint("projection_contract=manifest->>'projection_contract' AND source_report_id::text=manifest->'source'->>'report_id' AND source_accepted_version=(manifest->'source'->>'accepted_aggregate_version')::bigint AND source_snapshot_digest=manifest->>'source_snapshot_digest' AND projection_digest=manifest->>'admitted_projection_digest' AND provenance_digest=manifest->>'provenance_digest'", name="ck_organizational_memories_manifest_root_coherent"),
        Index(
            "ix_organizational_memories_active_order", "organization_id",
            "workspace_id", "project_id", "standing", text("admitted_at DESC"),
            text("id ASC"),
        ),
        Index("ix_organizational_memories_predecessor", "predecessor_memory_id"),
        Index("ix_organizational_memories_replacement", "replacement_memory_id"),
        Index(
            "uq_organizational_memories_replacement_once",
            "replacement_memory_id", unique=True,
            postgresql_where=text("replacement_memory_id IS NOT NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    workspace_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"), nullable=False)
    project_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=True)
    version: Mapped[int] = mapped_column(BigInteger, server_default="1", nullable=False)
    standing: Mapped[str] = mapped_column(String(16), server_default="active", nullable=False)
    source_report_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("technical_reports.id", ondelete="RESTRICT"), nullable=False)
    source_accepted_version: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source_snapshot_digest: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    projection_contract: Mapped[str] = mapped_column(String(64), nullable=False)
    projection: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    projection_digest: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    manifest: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    provenance_digest: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    admitted_by_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    admitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    admission_rationale: Mapped[str] = mapped_column(String(2000), nullable=False)
    audience_actor_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), server_default="{}", nullable=False)
    reuse_restrictions: Mapped[list[str]] = mapped_column(JSONB, server_default="[]", nullable=False)
    predecessor_memory_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("organizational_memories.id", ondelete="RESTRICT"), nullable=True)
    withdrawn_by_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    withdrawal_reason: Mapped[str | None] = mapped_column(String(2000))
    superseded_by_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    supersession_reason: Mapped[str | None] = mapped_column(String(2000))
    replacement_memory_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("organizational_memories.id", ondelete="RESTRICT"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class OrganizationalMemoryStandingHistoryRecord(Base):
    __tablename__ = "organizational_memory_standing_history"
    __table_args__ = (
        UniqueConstraint("memory_id", "aggregate_version", name="uq_organizational_memory_history_version"),
        CheckConstraint("aggregate_version > 0", name="ck_organizational_memory_history_version"),
        CheckConstraint("actor_id > 0", name="ck_organizational_memory_history_actor"),
        CheckConstraint("from_standing IS NULL OR from_standing = 'active'", name="ck_organizational_memory_history_from"),
        CheckConstraint("to_standing IN ('active','withdrawn','superseded')", name="ck_organizational_memory_history_to"),
        Index("ix_organizational_memory_history_memory_version", "memory_id", "aggregate_version"),
    )

    event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    memory_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("organizational_memories.id", ondelete="RESTRICT"), nullable=False)
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    aggregate_version: Mapped[int] = mapped_column(BigInteger, nullable=False)
    from_standing: Mapped[str | None] = mapped_column(String(16))
    to_standing: Mapped[str] = mapped_column(String(16), nullable=False)
    actor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str] = mapped_column(String(2000), nullable=False)
    replacement_memory_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("organizational_memories.id", ondelete="RESTRICT"), nullable=True)


class OrganizationalMemoryOutboxRecord(Base):
    __tablename__ = "organizational_memory_events_outbox"
    __table_args__ = (
        UniqueConstraint("memory_id", "aggregate_version", "event_type", name="uq_organizational_memory_outbox_aggregate_event"),
        CheckConstraint("aggregate_version > 0", name="ck_organizational_memory_outbox_version"),
        CheckConstraint("event_type IN ('ORGANIZATIONAL_MEMORY_ADMITTED','ORGANIZATIONAL_MEMORY_WITHDRAWN','ORGANIZATIONAL_MEMORY_SUPERSEDED')", name="ck_organizational_memory_outbox_event_type"),
        CheckConstraint("payload_schema_version = 1", name="ck_organizational_memory_outbox_schema_version"),
        CheckConstraint("attempt_count >= 0", name="ck_organizational_memory_outbox_attempt_count"),
        CheckConstraint("last_error_category IS NULL OR (length(last_error_category) BETWEEN 1 AND 64 AND last_error_category ~ '^[a-z0-9_]+$')", name="ck_organizational_memory_outbox_error_category"),
        CheckConstraint("organizational_memory_event_payload_v1_valid(event_type,payload)", name="ck_organizational_memory_outbox_payload"),
        CheckConstraint("memory_id::text=payload->>'memory_id' AND aggregate_version=(payload->>'aggregate_version')::bigint AND occurred_at=(payload->>'occurred_at')::timestamptz", name="ck_organizational_memory_outbox_root_coherent"),
        Index(
            "ix_organizational_memory_outbox_pending", "published_at", "created_at",
            "event_id", postgresql_where=text("published_at IS NULL"),
        ),
    )

    event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    memory_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("organizational_memories.id", ondelete="RESTRICT"), nullable=False)
    aggregate_version: Mapped[int] = mapped_column(BigInteger, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_schema_version: Mapped[int] = mapped_column(SmallInteger, server_default="1", nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempt_count: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    last_error_category: Mapped[str | None] = mapped_column(String(64))


class OrganizationalMemoryIdempotencyRecord(Base):
    __tablename__ = "organizational_memory_idempotency"
    __table_args__ = (
        CheckConstraint("actor_id > 0", name="ck_organizational_memory_idempotency_actor"),
        CheckConstraint("operation IN ('admit','withdraw','create_successor','supersede')", name="ck_organizational_memory_idempotency_operation"),
        CheckConstraint("request_fingerprint ~ '^[0-9a-f]{64}$'", name="ck_organizational_memory_idempotency_fingerprint"),
        CheckConstraint("status IN ('pending','completed')", name="ck_organizational_memory_idempotency_status"),
        CheckConstraint("result_schema_version = 1", name="ck_organizational_memory_idempotency_schema_version"),
        CheckConstraint("updated_at >= created_at", name="ck_organizational_memory_idempotency_timestamp_order"),
        CheckConstraint("(status='pending' AND safe_result IS NULL AND completed_at IS NULL) OR (status='completed' AND safe_result IS NOT NULL AND completed_at IS NOT NULL AND organizational_memory_idempotency_result_v1_valid(operation,safe_result))", name="ck_organizational_memory_idempotency_result"),
    )

    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), primary_key=True)
    actor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), primary_key=True)
    operation: Mapped[str] = mapped_column(String(32), primary_key=True)
    idempotency_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    request_fingerprint: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), server_default="pending", nullable=False)
    result_schema_version: Mapped[int] = mapped_column(SmallInteger, server_default="1", nullable=False)
    safe_result: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


def _projection(payload: dict[str, object]) -> AdmittedReportProjectionV1:
    content = payload["content"]
    qualification = payload["qualification"]
    assert isinstance(content, dict) and isinstance(qualification, dict)
    return AdmittedReportProjectionV1(
        projection_contract=payload["projection_contract"],
        report_id=UUID(str(payload["report_id"])),
        purpose=payload["purpose"],
        organization_id=UUID(str(payload["organization_id"])),
        workspace_id=payload["workspace_id"],
        project_id=payload["project_id"],
        content=AdmittedTechnicalContentV1(
            engineering_scope=content["engineering_scope"],
            technical_content=content["technical_content"],
            assumptions=tuple(content["assumptions"]),
            uncertainty=content["uncertainty"],
            limitations=tuple(content["limitations"]),
            conclusions=content["conclusions"],
            recommendations=tuple(content["recommendations"]),
        ),
        qualification=AdmittedQualificationV1(
            is_preliminary=qualification["is_preliminary"],
            evidence_deficiencies=tuple(qualification["evidence_deficiencies"]),
            unresolved_issues=tuple(qualification["unresolved_issues"]),
            follow_up_requirements=tuple(qualification["follow_up_requirements"]),
        ),
        accepted_draft_revision_id=UUID(str(payload["accepted_draft_revision_id"])),
        accepted_draft_revision_number=payload["accepted_draft_revision_number"],
        accepted_aggregate_version=payload["accepted_aggregate_version"],
        accepted_by_id=payload["accepted_by_id"],
        accepted_at=datetime.fromisoformat(str(payload["accepted_at"]).replace("Z", "+00:00")),
        predecessor_report_id=(None if payload["predecessor_report_id"] is None else UUID(str(payload["predecessor_report_id"]))),
    )


def _manifest(payload: dict[str, object]) -> MemorySourceManifestV1:
    source = payload["source"]
    assert isinstance(source, dict)
    entries = tuple(MemoryProvenanceDigestEntry(
        entry_id=UUID(str(item["entry_id"])),
        ordinal=item["ordinal"],
        source_class=item["source_class"],
        source_type=item["source_type"],
        owning_capability=item["owning_capability"],
        is_material=item["is_material"],
        reliance_role=item["reliance_role"],
        locator_digest=item["locator_digest"],
        source_integrity_algorithm=item["source_integrity_algorithm"],
        source_integrity_digest=item["source_integrity_digest"],
    ) for item in payload["provenance_entries"])
    return MemorySourceManifestV1(
        source=AcceptedReportSource(
            UUID(str(source["report_id"])),
            source["accepted_aggregate_version"],
            source["accepted_snapshot_digest"],
        ),
        source_snapshot_digest=payload["source_snapshot_digest"],
        projection_contract=payload["projection_contract"],
        admitted_projection_digest=payload["admitted_projection_digest"],
        provenance_digest=payload["provenance_digest"],
        provenance_entries=entries,
    )


class SqlAlchemyOrganizationalMemoryRepository:
    """Persist memory aggregates while leaving transaction ownership to a UoW."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, memory: OrganizationalMemory) -> None:
        self.session.add(OrganizationalMemoryRecord(
            id=memory.id,
            organization_id=memory.organization_id,
            workspace_id=memory.workspace_id,
            project_id=memory.project_id,
            version=memory.version,
            standing=memory.standing.value,
            source_report_id=memory.source.report_id,
            source_accepted_version=memory.source.accepted_aggregate_version,
            source_snapshot_digest=memory.source.accepted_snapshot_digest,
            projection_contract=memory.projection.projection_contract,
            projection=json.loads(canonical_json(memory.projection)),
            projection_digest=memory.manifest.admitted_projection_digest,
            manifest=json.loads(canonical_json(memory.manifest)),
            provenance_digest=memory.manifest.provenance_digest,
            admitted_by_id=memory.admitted_by_id,
            admitted_at=memory.admitted_at,
            admission_rationale=memory.admission_rationale,
            audience_actor_ids=list(memory.audience_actor_ids),
            reuse_restrictions=list(memory.reuse_restrictions),
            predecessor_memory_id=memory.predecessor_memory_id,
            withdrawn_by_id=memory.withdrawn_by_id,
            withdrawn_at=memory.withdrawn_at,
            withdrawal_reason=memory.withdrawal_reason,
            superseded_by_id=memory.superseded_by_id,
            superseded_at=memory.superseded_at,
            supersession_reason=memory.supersession_reason,
            replacement_memory_id=memory.replacement_memory_id,
            created_at=memory.created_at,
            updated_at=memory.updated_at,
        ))
        self.session.flush()

    def get_scoped(self, memory_id: UUID, organization_id: UUID) -> OrganizationalMemory | None:
        record = self.session.query(OrganizationalMemoryRecord).filter_by(
            id=memory_id, organization_id=organization_id,
        ).one_or_none()
        return None if record is None else self._aggregate(record)

    def lock_scoped(self, memory_id: UUID, organization_id: UUID) -> OrganizationalMemory | None:
        record = self.session.query(OrganizationalMemoryRecord).filter_by(
            id=memory_id, organization_id=organization_id,
        ).with_for_update().one_or_none()
        return None if record is None else self._aggregate(record)

    def lock_pair_scoped(
        self, first_id: UUID, second_id: UUID, organization_id: UUID,
    ) -> tuple[OrganizationalMemory, OrganizationalMemory] | None:
        ordered = tuple(sorted((first_id, second_id), key=str))
        records = self.session.query(OrganizationalMemoryRecord).filter(
            OrganizationalMemoryRecord.organization_id == organization_id,
            OrganizationalMemoryRecord.id.in_(ordered),
        ).order_by(OrganizationalMemoryRecord.id).with_for_update().all()
        if len(records) != 2:
            return None
        by_id = {record.id: self._aggregate(record) for record in records}
        return by_id[first_id], by_id[second_id]

    def get_by_source(self, source: AcceptedReportSource, organization_id: UUID) -> OrganizationalMemory | None:
        record = self.session.query(OrganizationalMemoryRecord).filter_by(
            organization_id=organization_id,
            source_report_id=source.report_id,
            source_accepted_version=source.accepted_aggregate_version,
        ).one_or_none()
        return None if record is None else self._aggregate(record)

    def persist_standing_expected_version(self, memory: OrganizationalMemory, expected_version: int) -> bool:
        result = self.session.execute(
            update(OrganizationalMemoryRecord)
            .where(
                OrganizationalMemoryRecord.id == memory.id,
                OrganizationalMemoryRecord.organization_id == memory.organization_id,
                OrganizationalMemoryRecord.version == expected_version,
                OrganizationalMemoryRecord.standing == MemoryStanding.ACTIVE.value,
            )
            .values(
                version=memory.version,
                standing=memory.standing.value,
                withdrawn_by_id=memory.withdrawn_by_id,
                withdrawn_at=memory.withdrawn_at,
                withdrawal_reason=memory.withdrawal_reason,
                superseded_by_id=memory.superseded_by_id,
                superseded_at=memory.superseded_at,
                supersession_reason=memory.supersession_reason,
                replacement_memory_id=memory.replacement_memory_id,
                updated_at=memory.updated_at,
            )
        )
        return result.rowcount == 1

    def list_active(self, criteria: ActiveMemoryCriteria) -> MemoryCandidatePage:
        query = self.session.query(OrganizationalMemoryRecord).filter_by(
            organization_id=criteria.organization_id,
            workspace_id=criteria.workspace_id,
            standing=MemoryStanding.ACTIVE.value,
        )
        if criteria.project_id is not None:
            query = query.filter(OrganizationalMemoryRecord.project_id == criteria.project_id)
        if criteria.purpose is not None:
            query = query.filter(OrganizationalMemoryRecord.projection["purpose"].astext == criteria.purpose.value)
        if criteria.anchor is not None:
            query = query.filter(
                (OrganizationalMemoryRecord.admitted_at < criteria.anchor.admitted_at)
                | ((OrganizationalMemoryRecord.admitted_at == criteria.anchor.admitted_at) & (OrganizationalMemoryRecord.id > criteria.anchor.memory_id))
            )
        rows = query.order_by(
            OrganizationalMemoryRecord.admitted_at.desc(),
            OrganizationalMemoryRecord.id.asc(),
        ).limit(min(criteria.candidate_limit + 1, 101)).all()
        return MemoryCandidatePage(
            tuple(self._aggregate(item) for item in rows[:criteria.candidate_limit]),
            len(rows) > criteria.candidate_limit,
        )

    def append_history(self, record: MemoryStandingHistoryRecord) -> None:
        self.session.add(OrganizationalMemoryStandingHistoryRecord(
            event_id=record.event_id,
            memory_id=record.memory_id,
            organization_id=record.organization_id,
            aggregate_version=record.aggregate_version,
            from_standing=None if record.from_standing is None else record.from_standing.value,
            to_standing=record.to_standing.value,
            actor_id=record.actor_id,
            occurred_at=record.occurred_at,
            reason=record.reason,
            replacement_memory_id=record.replacement_memory_id,
        ))
        self.session.flush()

    @staticmethod
    def _aggregate(record: OrganizationalMemoryRecord) -> OrganizationalMemory:
        projection = _projection(record.projection)
        manifest = _manifest(record.manifest)
        return OrganizationalMemory(
            id=record.id,
            organization_id=record.organization_id,
            workspace_id=record.workspace_id,
            project_id=record.project_id,
            version=record.version,
            standing=MemoryStanding(record.standing),
            source=manifest.source,
            projection=projection,
            manifest=manifest,
            admitted_by_id=record.admitted_by_id,
            admitted_at=record.admitted_at,
            admission_rationale=record.admission_rationale,
            audience_actor_ids=tuple(record.audience_actor_ids),
            reuse_restrictions=tuple(record.reuse_restrictions),
            predecessor_memory_id=record.predecessor_memory_id,
            withdrawn_by_id=record.withdrawn_by_id,
            withdrawn_at=record.withdrawn_at,
            withdrawal_reason=record.withdrawal_reason,
            superseded_by_id=record.superseded_by_id,
            superseded_at=record.superseded_at,
            supersession_reason=record.supersession_reason,
            replacement_memory_id=record.replacement_memory_id,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
