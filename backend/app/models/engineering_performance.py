"""PATCH-056 derived Engineering Performance persistence models."""

from uuid import uuid4
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.sql import func
from app.core.database import Base


class EngineeringPerformanceSnapshot(Base):
    __tablename__ = "engineering_performance_snapshots"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"), nullable=True)
    actor_id = Column(Integer, nullable=False, server_default="0")  # Zero marks unreadable legacy rows.
    indicator_id = Column(String(64), nullable=False)
    indicator_version = Column(String(32), nullable=False)
    window_start = Column(DateTime(timezone=True), nullable=False)
    window_end = Column(DateTime(timezone=True), nullable=False)
    observed_at = Column(DateTime(timezone=True), nullable=False)
    source_cutoff = Column(DateTime(timezone=True), nullable=False)
    source_digest = Column(String(64), nullable=False)
    source_handles_json = Column(JSONB, nullable=True)
    recomputation_reason = Column(String(32), nullable=False, server_default="legacy_unclassified")
    calculation_version = Column(String(32), nullable=False)
    observation_state = Column(String(24), nullable=False)
    value_json = Column(JSONB, nullable=False)
    limitation_codes_json = Column(JSONB, nullable=False, default=list)
    eligible_count = Column(Integer, nullable=True)
    numerator = Column(Integer, nullable=True)
    denominator = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (
        UniqueConstraint("organization_id","project_id","workspace_id","actor_id","indicator_id","indicator_version","window_start","window_end","source_digest","calculation_version",name="uq_eng_perf_snapshot_repro"),
        Index("uq_eng_perf_snapshot_project_repro", "organization_id", "project_id", "actor_id", "indicator_id", "indicator_version", "window_start", "window_end", "source_digest", "calculation_version", unique=True, postgresql_where=text("workspace_id IS NULL")),
        CheckConstraint("observation_state IN ('complete','partial','indeterminate','not_applicable')", name="ck_eng_perf_snapshot_state"),
        CheckConstraint("window_end >= window_start", name="ck_eng_perf_snapshot_window"),
        CheckConstraint("eligible_count IS NULL OR eligible_count >= 0", name="ck_eng_perf_snapshot_eligible"),
        CheckConstraint("actor_id >= 0", name="ck_eng_perf_snapshot_actor"),
        CheckConstraint("recomputation_reason IN ('legacy_unclassified','request_calculation')", name="ck_eng_perf_snapshot_reason"),
    )


class EngineeringNextActionProjection(Base):
    __tablename__ = "engineering_next_action_projections"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"), nullable=True)
    actor_id = Column(Integer, nullable=False, server_default="0")
    action_key = Column(String(64), nullable=False)
    rule_id = Column(String(64), nullable=False)
    rule_version = Column(String(32), nullable=False)
    title_code = Column(String(128), nullable=False)
    rationale_codes_json = Column(JSONB, nullable=False, default=list)
    supporting_handle_json = Column(JSONB, nullable=False, default=list)
    limitation_codes_json = Column(JSONB, nullable=False, default=list)
    first_seen_at = Column(DateTime(timezone=True), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=False)
    absent_recalculation_count = Column(Integer, nullable=False, default=0)
    status = Column(String(32), nullable=False)
    superseded_by_action_key = Column(String(64), nullable=True)
    source_digest = Column(String(64), nullable=False)
    calculation_version = Column(String(32), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    __table_args__ = (
        UniqueConstraint("organization_id","project_id","workspace_id","actor_id","action_key",name="uq_eng_next_action_scope_key"),
        Index("uq_eng_next_action_project_key", "organization_id", "project_id", "actor_id", "action_key", unique=True, postgresql_where=text("workspace_id IS NULL")),
        CheckConstraint("status IN ('active','stale','superseded','resolved_by_source_state')", name="ck_eng_next_action_status"),
        CheckConstraint("absent_recalculation_count >= 0", name="ck_eng_next_action_absent_count"),
        CheckConstraint("last_seen_at >= first_seen_at", name="ck_eng_next_action_seen_order"),
        CheckConstraint("actor_id >= 0", name="ck_eng_next_action_actor"),
    )
