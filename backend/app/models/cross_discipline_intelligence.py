"""Relational mapping for PATCH-053-owned immutable assessment history."""

from uuid import uuid4

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, Column, DateTime, ForeignKey,
    ForeignKeyConstraint, Index, Integer, String, Text, UniqueConstraint, text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.sql import func

from app.core.database import Base


class CrossDisciplineAssessment(Base):
    __tablename__ = "cross_discipline_assessments"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "organization_id"],
            ["projects.id", "projects.organization_id"],
            name="fk_xdi_root_project_scope", ondelete="RESTRICT",
        ),
        UniqueConstraint("organization_id", "project_id", "id", name="uq_xdi_root_scope"),
        UniqueConstraint("organization_id", "project_id", "actor_id", "idempotency_key", name="uq_xdi_assessment_idempotency"),
        CheckConstraint("aggregate_version >= 1", name="ck_xdi_assessment_version"),
        CheckConstraint("purpose IN ('interface_assessment','current_handoff_gate','explicit_change_impact')", name="ck_xdi_assessment_purpose"),
        CheckConstraint("status IN ('completed_no_findings','completed_with_findings','indeterminate','unavailable')", name="ck_xdi_assessment_status"),
        CheckConstraint(
            "(status IN ('indeterminate','unavailable') AND reason_code IS NOT NULL) OR "
            "(status IN ('completed_no_findings','completed_with_findings') AND reason_code IS NULL)",
            name="ck_xdi_assessment_status_reason",
        ),
        Index("ix_xdi_assessment_project_time", "organization_id", "project_id", "completed_at", "id"),
        Index("ix_xdi_assessment_status_combination", "organization_id", "project_id", "status", "combination_id"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    project_id = Column(Integer, nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    request_id = Column(PGUUID(as_uuid=True), nullable=False, unique=True, default=uuid4)
    purpose = Column(String(48), nullable=False)
    rationale = Column(Text, nullable=False)
    correlation_id = Column(PGUUID(as_uuid=True), nullable=False)
    causation_id = Column(PGUUID(as_uuid=True))
    idempotency_key = Column(PGUUID(as_uuid=True), nullable=False)
    combination_id = Column(String(128), nullable=False)
    request_digest = Column(String(64), nullable=False)
    scope_digest = Column(String(64), nullable=False)
    status = Column(String(48), nullable=False)
    reason_code = Column(String(64))
    aggregate_version = Column(Integer, nullable=False, default=1, server_default="1")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=False)


class ScopedChild:
    organization_id = Column(PGUUID(as_uuid=True), nullable=False)
    project_id = Column(Integer, nullable=False)
    assessment_id = Column(PGUUID(as_uuid=True), nullable=False)

    @classmethod
    def scope_fk(cls, name):
        return ForeignKeyConstraint(
            ["organization_id", "project_id", "assessment_id"],
            ["cross_discipline_assessments.organization_id", "cross_discipline_assessments.project_id", "cross_discipline_assessments.id"],
            name=name, ondelete="RESTRICT",
        )


class CrossDisciplineSnapshot(ScopedChild, Base):
    __tablename__ = "cross_discipline_assessment_snapshots"
    __table_args__ = (
        ScopedChild.scope_fk("fk_xdi_snapshot_root_scope"),
        CheckConstraint("octet_length(payload::text) <= 2097152", name="ck_xdi_snapshot_size"),
    )
    assessment_id = Column(PGUUID(as_uuid=True), primary_key=True)
    execution_id = Column(PGUUID(as_uuid=True), nullable=False, unique=True)
    snapshot_id = Column(PGUUID(as_uuid=True), nullable=False, unique=True)
    registry_digest = Column(String(64), nullable=False)
    definition_digest = Column(String(64), nullable=False)
    source_manifest_digest = Column(String(64), nullable=False)
    finding_set_digest = Column(String(64), nullable=False)
    snapshot_digest = Column(String(64), nullable=False)
    result_digest = Column(String(64), nullable=False)
    observed_through = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=False)
    payload = Column(JSONB, nullable=False)


class CrossDisciplineAssessmentWorkspace(ScopedChild, Base):
    __tablename__ = "cross_discipline_assessment_workspaces"
    __table_args__ = (
        ScopedChild.scope_fk("fk_xdi_workspace_root_scope"),
        ForeignKeyConstraint(
            ["workspace_id", "project_id"],
            ["engineering_workspaces.id", "engineering_workspaces.project_id"],
            name="fk_xdi_workspace_project_scope", ondelete="RESTRICT",
        ),
        UniqueConstraint("assessment_id", "workspace_id", name="uq_xdi_workspace_participant"),
        UniqueConstraint("assessment_id", "role", name="uq_xdi_workspace_role"),
    )
    assessment_id = Column(PGUUID(as_uuid=True), primary_key=True)
    workspace_id = Column(Integer, primary_key=True)
    package_key = Column(String(64), primary_key=True)
    discipline_id = Column(String(64), nullable=False)
    role = Column(String(64), nullable=False)
    binding_revision = Column(BigInteger, nullable=False)
    binding_digest = Column(String(64), nullable=False)


class CrossDisciplineSourceProjection(ScopedChild, Base):
    __tablename__ = "cross_discipline_source_projections"
    __table_args__ = (
        ScopedChild.scope_fk("fk_xdi_projection_root_scope"),
        UniqueConstraint("assessment_id", "id", name="uq_xdi_projection_root"),
        UniqueConstraint("assessment_id", "projection_id", name="uq_xdi_projection_id"),
        UniqueConstraint("assessment_id", "owner_kind", "owner_id", "revision_kind", "revision", "projection_id", name="uq_xdi_projection_owner"),
        CheckConstraint("revision_kind IN ('aggregate_version','snapshot_digest')", name="ck_xdi_projection_revision_kind"),
        Index("ix_xdi_projection_owner", "assessment_id", "owner_kind", "owner_id", "revision"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    projection_id = Column(String(128), nullable=False)
    owner_kind = Column(String(64), nullable=False)
    owner_id = Column(String(128), nullable=False)
    revision_kind = Column(String(32), nullable=False)
    revision = Column(String(128), nullable=False)
    schema_id = Column(String(128), nullable=False)
    adapter_capability_id = Column(String(128), nullable=False)
    sensitivity = Column(String(32), nullable=False)
    payload = Column(JSONB, nullable=False)
    projection_digest = Column(String(64), nullable=False)


class CrossDisciplineCompletenessAttestation(ScopedChild, Base):
    __tablename__ = "cross_discipline_completeness_attestations"
    __table_args__ = (
        ScopedChild.scope_fk("fk_xdi_attestation_root_scope"),
        UniqueConstraint("assessment_id", "id", name="uq_xdi_attestation_root"),
        UniqueConstraint("assessment_id", "attestation_digest", name="uq_xdi_attestation_digest"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    owner_kind = Column(String(64), nullable=False)
    owner_id = Column(String(128), nullable=False)
    selector_digest = Column(String(64), nullable=False)
    observed_cardinality = Column(Integer, nullable=False)
    page_count = Column(Integer, nullable=False)
    non_truncated = Column(Boolean, nullable=False)
    negative_result = Column(Boolean, nullable=False)
    payload = Column(JSONB, nullable=False)
    attestation_digest = Column(String(64), nullable=False)


class CrossDisciplineOccurrence(ScopedChild, Base):
    __tablename__ = "cross_discipline_interface_occurrences"
    __table_args__ = (
        ScopedChild.scope_fk("fk_xdi_occurrence_root_scope"),
        ForeignKeyConstraint(
            ["assessment_id", "provider_workspace_id"],
            ["cross_discipline_assessment_workspaces.assessment_id", "cross_discipline_assessment_workspaces.workspace_id"],
            name="fk_xdi_occurrence_provider_workspace", ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["assessment_id", "consumer_workspace_id"],
            ["cross_discipline_assessment_workspaces.assessment_id", "cross_discipline_assessment_workspaces.workspace_id"],
            name="fk_xdi_occurrence_consumer_workspace", ondelete="RESTRICT",
        ),
        UniqueConstraint("assessment_id", "occurrence_key", name="uq_xdi_occurrence_key"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    occurrence_key = Column(String(64), nullable=False)
    interface_definition_id = Column(String(128), nullable=False)
    provider_workspace_id = Column(Integer, nullable=False)
    consumer_workspace_id = Column(Integer, nullable=False)
    commitment_id = Column(Integer)
    commitment_version = Column(Integer)
    applicability = Column(String(32), nullable=False)
    payload = Column(JSONB, nullable=False)
    occurrence_digest = Column(String(64), nullable=False)


class CrossDisciplineFinding(ScopedChild, Base):
    __tablename__ = "cross_discipline_findings"
    __table_args__ = (
        ScopedChild.scope_fk("fk_xdi_finding_root_scope"),
        UniqueConstraint("assessment_id", "id", name="uq_xdi_finding_root"),
        UniqueConstraint("assessment_id", "fingerprint", name="uq_xdi_finding_fingerprint"),
        UniqueConstraint("assessment_id", "ordinal", name="uq_xdi_finding_ordinal"),
        Index("ix_xdi_finding_order", "assessment_id", "ordinal"),
        Index("ix_xdi_finding_recurrence", "recurrence_key"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    occurrence_id = Column(PGUUID(as_uuid=True), ForeignKey("cross_discipline_interface_occurrences.id", ondelete="RESTRICT"))
    ordinal = Column(Integer, nullable=False)
    rule_id = Column(String(128), nullable=False)
    rule_version = Column(String(16), nullable=False)
    rule_digest = Column(String(64), nullable=False)
    category = Column(String(64), nullable=False)
    subcode = Column(String(128), nullable=False)
    severity = Column(String(16), nullable=False)
    fingerprint = Column(String(64), nullable=False)
    recurrence_key = Column(String(64), nullable=False)
    affected_selector = Column(String(256), nullable=False)
    payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class CrossDisciplineDisposition(ScopedChild, Base):
    __tablename__ = "cross_discipline_finding_dispositions"
    __table_args__ = (
        ScopedChild.scope_fk("fk_xdi_disposition_root_scope"),
        ForeignKeyConstraint(
            ["assessment_id", "finding_id"],
            ["cross_discipline_findings.assessment_id", "cross_discipline_findings.id"],
            name="fk_xdi_disposition_finding_scope", ondelete="RESTRICT",
        ),
        UniqueConstraint("assessment_id", "id", name="uq_xdi_disposition_root"),
        UniqueConstraint("assessment_id", "sequence", name="uq_xdi_disposition_sequence"),
        UniqueConstraint("organization_id", "project_id", "actor_id", "idempotency_key", name="uq_xdi_disposition_idempotency"),
        Index("ix_xdi_disposition_order", "assessment_id", "finding_id", "sequence"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    finding_id = Column(PGUUID(as_uuid=True), nullable=False)
    sequence = Column(Integer, nullable=False)
    action = Column(String(64), nullable=False)
    resulting_view_state = Column(String(64), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    actor_role = Column(String(32), nullable=False)
    rationale = Column(Text, nullable=False)
    expected_assessment_version = Column(Integer, nullable=False)
    expected_view_version = Column(Integer, nullable=False)
    resulting_view_version = Column(Integer, nullable=False)
    correlation_id = Column(PGUUID(as_uuid=True), nullable=False)
    causation_id = Column(PGUUID(as_uuid=True))
    idempotency_key = Column(PGUUID(as_uuid=True), nullable=False)
    payload = Column(JSONB, nullable=False)
    disposition_digest = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class CrossDisciplineFindingCurrent(ScopedChild, Base):
    __tablename__ = "cross_discipline_finding_current"
    __table_args__ = (
        ScopedChild.scope_fk("fk_xdi_current_root_scope"),
        ForeignKeyConstraint(
            ["assessment_id", "finding_id"],
            ["cross_discipline_findings.assessment_id", "cross_discipline_findings.id"],
            name="fk_xdi_current_finding_scope", ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["assessment_id", "latest_disposition_id"],
            ["cross_discipline_finding_dispositions.assessment_id", "cross_discipline_finding_dispositions.id"],
            name="fk_xdi_current_disposition_scope", ondelete="RESTRICT",
        ),
        Index("ix_xdi_current_category_state", "organization_id", "project_id", "current_state"),
    )
    finding_id = Column(PGUUID(as_uuid=True), primary_key=True)
    projection_version = Column(Integer, nullable=False, server_default="0")
    latest_disposition_id = Column(PGUUID(as_uuid=True))
    latest_action = Column(String(64))
    current_state = Column(String(64), nullable=False, server_default="open")
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class CrossDisciplineLineage(Base):
    __tablename__ = "cross_discipline_assessment_lineage"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "project_id", "predecessor_id"],
            ["cross_discipline_assessments.organization_id", "cross_discipline_assessments.project_id", "cross_discipline_assessments.id"],
            name="fk_xdi_lineage_predecessor_scope", ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["organization_id", "project_id", "successor_id"],
            ["cross_discipline_assessments.organization_id", "cross_discipline_assessments.project_id", "cross_discipline_assessments.id"],
            name="fk_xdi_lineage_successor_scope", ondelete="RESTRICT",
        ),
        CheckConstraint("predecessor_id <> successor_id", name="ck_xdi_lineage_not_self"),
        UniqueConstraint("kind", "predecessor_id", "replacement_operation_id", name="uq_xdi_lineage_operation"),
        Index(
            "uq_xdi_lineage_supersedes", "predecessor_id", unique=True,
            postgresql_where=text("kind='supersedes'"),
        ),
        Index("ix_xdi_lineage_predecessor", "organization_id", "project_id", "predecessor_id"),
        Index("ix_xdi_lineage_successor", "organization_id", "project_id", "successor_id"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), nullable=False)
    project_id = Column(Integer, nullable=False)
    predecessor_id = Column(PGUUID(as_uuid=True), nullable=False)
    successor_id = Column(PGUUID(as_uuid=True), nullable=False)
    kind = Column(String(32), nullable=False)
    scope_family_digest = Column(String(64), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    rationale = Column(Text, nullable=False)
    correlation_id = Column(PGUUID(as_uuid=True), nullable=False)
    idempotency_key = Column(PGUUID(as_uuid=True), nullable=False)
    replacement_operation_id = Column(PGUUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class CrossDisciplineIdempotency(Base):
    __tablename__ = "cross_discipline_idempotency"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "organization_id"],
            ["projects.id", "projects.organization_id"],
            name="fk_xdi_idempotency_project_scope", ondelete="RESTRICT",
        ),
        UniqueConstraint("organization_id", "project_id", "actor_id", "operation", "idempotency_key", name="uq_xdi_idempotency_scope"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    project_id = Column(Integer, nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    operation = Column(String(64), nullable=False)
    idempotency_key = Column(PGUUID(as_uuid=True), nullable=False)
    request_digest = Column(String(64), nullable=False)
    response_json = Column(JSONB)
    response_digest = Column(String(64))
    assessment_id = Column(PGUUID(as_uuid=True), ForeignKey("cross_discipline_assessments.id", ondelete="RESTRICT"))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class CrossDisciplineOutbox(Base):
    """Transactional delivery record; payload is metadata-only."""

    __tablename__ = "cross_discipline_outbox"
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_xdi_outbox_event"),
        Index("ix_xdi_outbox_unpublished", "published_at", "created_at"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_id = Column(PGUUID(as_uuid=True), nullable=False)
    assessment_id = Column(PGUUID(as_uuid=True), ForeignKey("cross_discipline_assessments.id", ondelete="RESTRICT"), nullable=False)
    event_type = Column(String(96), nullable=False)
    schema_version = Column(Integer, nullable=False, server_default="1")
    payload = Column(JSONB, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
