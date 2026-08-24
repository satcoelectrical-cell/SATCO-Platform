from datetime import datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from app.core.database import Base


DELIVERABLE_STANDINGS = "'planned','in_preparation','ready_for_review','reviewed','issued','withdrawn','cancelled'"
REVISION_STANDINGS = "'draft','ready_for_review','reviewed','issued','superseded','withdrawn'"
EXTERNAL_AUTHORITIES = "'cad','eplan','etap','spreadsheet','document','vendor_tool','other'"


class EngineeringDeliverable(Base):
    __tablename__ = "engineering_deliverables"
    __table_args__ = (
        CheckConstraint("length(btrim(code)) BETWEEN 1 AND 64", name="ck_deliverable_code"),
        CheckConstraint("length(btrim(title)) BETWEEN 1 AND 200", name="ck_deliverable_title"),
        CheckConstraint("length(btrim(discipline)) BETWEEN 1 AND 80", name="ck_deliverable_discipline"),
        CheckConstraint("length(btrim(deliverable_type)) BETWEEN 1 AND 80", name="ck_deliverable_type"),
        CheckConstraint("purpose IS NULL OR length(btrim(purpose)) BETWEEN 1 AND 2000", name="ck_deliverable_purpose"),
        CheckConstraint(f"standing IN ({DELIVERABLE_STANDINGS})", name="ck_deliverable_standing"),
        CheckConstraint(f"external_authority IN ({EXTERNAL_AUTHORITIES})", name="ck_deliverable_external_authority"),
        CheckConstraint("version >= 1 AND current_revision_sequence >= 1", name="ck_deliverable_versions"),
        UniqueConstraint("project_id", "code", name="uq_deliverable_project_code"),
        Index("ix_deliverable_project_order", "organization_id", "project_id", "target_date", "code", "id"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"))
    activity_id = Column(PGUUID(as_uuid=True), ForeignKey("engineering_execution_activities.id", ondelete="RESTRICT"))
    milestone_id = Column(PGUUID(as_uuid=True), ForeignKey("engineering_execution_milestones.id", ondelete="RESTRICT"))
    code = Column(String(64), nullable=False)
    title = Column(String(200), nullable=False)
    discipline = Column(String(80), nullable=False)
    deliverable_type = Column(String(80), nullable=False)
    purpose = Column(String(2000))
    external_authority = Column(String(32), nullable=False)
    responsible_user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"))
    target_date = Column(Date)
    standing = Column(String(32), nullable=False, default="planned", server_default="planned")
    current_revision_sequence = Column(Integer, nullable=False, default=1, server_default="1")
    version = Column(Integer, nullable=False, default=1, server_default="1")
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class EngineeringDeliverableRevision(Base):
    __tablename__ = "engineering_deliverable_revisions"
    __table_args__ = (
        CheckConstraint("sequence >= 1 AND version >= 1", name="ck_deliverable_revision_versions"),
        CheckConstraint("length(btrim(external_label)) BETWEEN 1 AND 80", name="ck_deliverable_revision_label"),
        CheckConstraint("source_reference IS NULL OR length(btrim(source_reference)) BETWEEN 1 AND 512", name="ck_deliverable_revision_source_reference"),
        CheckConstraint(f"standing IN ({REVISION_STANDINGS})", name="ck_deliverable_revision_standing"),
        UniqueConstraint("deliverable_id", "sequence", name="uq_deliverable_revision_sequence"),
        Index("ix_deliverable_revision_history", "organization_id", "deliverable_id", "sequence"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    deliverable_id = Column(PGUUID(as_uuid=True), ForeignKey("engineering_deliverables.id", ondelete="RESTRICT"), nullable=False)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    sequence = Column(Integer, nullable=False)
    external_label = Column(String(80), nullable=False)
    source_reference = Column(String(512))
    supporting_file_id = Column(PGUUID(as_uuid=True), ForeignKey("supporting_file_assets.id", ondelete="RESTRICT"))
    standing = Column(String(32), nullable=False, default="draft", server_default="draft")
    version = Column(Integer, nullable=False, default=1, server_default="1")
    rationale = Column(String(2000), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    transitioned_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    transitioned_at = Column(DateTime(timezone=True), nullable=False)


class EngineeringDeliverableHistory(Base):
    __tablename__ = "engineering_deliverable_history"
    __table_args__ = (
        CheckConstraint("aggregate_version >= 1", name="ck_deliverable_history_version"),
        CheckConstraint("length(btrim(event_type)) BETWEEN 1 AND 80", name="ck_deliverable_history_type"),
        UniqueConstraint("deliverable_id", "aggregate_version", name="uq_deliverable_history_version"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    deliverable_id = Column(PGUUID(as_uuid=True), ForeignKey("engineering_deliverables.id", ondelete="RESTRICT"), nullable=False)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    aggregate_version = Column(Integer, nullable=False)
    event_type = Column(String(80), nullable=False)
    revision_id = Column(PGUUID(as_uuid=True), ForeignKey("engineering_deliverable_revisions.id", ondelete="RESTRICT"))
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)


class EngineeringDeliverableIdempotency(Base):
    __tablename__ = "engineering_deliverable_idempotency"
    __table_args__ = (
        CheckConstraint("length(fingerprint)=64", name="ck_deliverable_idempotency_fingerprint"),
        CheckConstraint("length(replay_json::text)<=1024", name="ck_deliverable_idempotency_size"),
        UniqueConstraint("organization_id", "actor_id", "operation", "idempotency_key", name="uq_deliverable_idempotency_key"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    operation = Column(String(32), nullable=False)
    idempotency_key = Column(PGUUID(as_uuid=True), nullable=False)
    fingerprint = Column(String(64), nullable=False)
    replay_json = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)


class EngineeringDeliverableOutbox(Base):
    __tablename__ = "engineering_deliverable_outbox"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_id = Column(PGUUID(as_uuid=True), nullable=False, unique=True)
    deliverable_id = Column(PGUUID(as_uuid=True), ForeignKey("engineering_deliverables.id", ondelete="RESTRICT"), nullable=False)
    aggregate_version = Column(Integer, nullable=False)
    event_type = Column(String(96), nullable=False)
    payload = Column(JSONB, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
