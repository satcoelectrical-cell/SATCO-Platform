from datetime import datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKey, Index, Integer, SmallInteger, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from app.core.database import Base
from app.enums.engineering_execution_plan import ExecutionActivityStanding


ACTIVITY_STANDINGS = "'planned','ready','in_progress','blocked','completed','cancelled'"


class EngineeringExecutionPlan(Base):
    __tablename__ = "engineering_execution_plans"
    __table_args__ = (
        CheckConstraint("version >= 1", name="ck_execution_plan_version"),
        Index("ix_execution_plan_scope", "organization_id", "project_id"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, unique=True)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    version = Column(Integer, nullable=False, default=1, server_default="1")
    established_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    established_at = Column(DateTime(timezone=True), nullable=False)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class EngineeringExecutionPlanRevision(Base):
    __tablename__ = "engineering_execution_plan_revisions"
    __table_args__ = (
        CheckConstraint("revision_number >= 1", name="ck_execution_plan_revision_number"),
        CheckConstraint("length(config_digest) = 64", name="ck_execution_plan_revision_digest"),
        UniqueConstraint("plan_id", "revision_number", name="uq_execution_plan_revision_number"),
        Index("ix_execution_plan_revision_order", "organization_id", "plan_id", "revision_number"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    plan_id = Column(PGUUID(as_uuid=True), ForeignKey("engineering_execution_plans.id", ondelete="RESTRICT"), nullable=False)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    revision_number = Column(Integer, nullable=False)
    config_json = Column(JSONB, nullable=False)
    config_digest = Column(String(64), nullable=False)
    rationale = Column(String(2000), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)


class EngineeringExecutionActivity(Base):
    __tablename__ = "engineering_execution_activities"
    __table_args__ = (
        CheckConstraint("length(btrim(title)) BETWEEN 1 AND 200", name="ck_execution_activity_title"),
        CheckConstraint("description IS NULL OR length(btrim(description)) BETWEEN 1 AND 2000", name="ck_execution_activity_description"),
        CheckConstraint("length(btrim(completion_basis)) BETWEEN 1 AND 2000", name="ck_execution_activity_completion_basis"),
        CheckConstraint("ordinal BETWEEN 0 AND 199", name="ck_execution_activity_ordinal"),
        CheckConstraint(f"standing IN ({ACTIVITY_STANDINGS})", name="ck_execution_activity_standing"),
        CheckConstraint("version >= 1", name="ck_execution_activity_version"),
        CheckConstraint("blocker_rationale IS NULL OR length(btrim(blocker_rationale)) BETWEEN 1 AND 2000", name="ck_execution_activity_blocker"),
        CheckConstraint("completion_rationale IS NULL OR length(btrim(completion_rationale)) BETWEEN 1 AND 2000", name="ck_execution_activity_completion_rationale"),
        CheckConstraint("(standing = 'blocked') = (blocker_rationale IS NOT NULL)", name="ck_execution_activity_blocker_pair"),
        CheckConstraint("(standing = 'blocked' AND blocked_return_standing IN ('planned','ready','in_progress')) OR (standing <> 'blocked' AND blocked_return_standing IS NULL)", name="ck_execution_activity_blocked_return_pair"),
        CheckConstraint("standing <> 'completed' OR completion_rationale IS NOT NULL", name="ck_execution_activity_completion_pair"),
        UniqueConstraint("plan_id", "ordinal", name="uq_execution_activity_ordinal", deferrable=True, initially="DEFERRED"),
        Index("ix_execution_activity_order", "organization_id", "project_id", "plan_id", "ordinal", "id"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    plan_id = Column(PGUUID(as_uuid=True), ForeignKey("engineering_execution_plans.id", ondelete="RESTRICT"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(String(2000))
    ordinal = Column(SmallInteger, nullable=False)
    workspace_id = Column(Integer, ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"))
    responsible_user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"))
    target_date = Column(Date)
    completion_basis = Column(String(2000), nullable=False)
    standing = Column(String(32), nullable=False, default=ExecutionActivityStanding.PLANNED.value, server_default="planned")
    blocker_rationale = Column(String(2000))
    blocked_return_standing = Column(String(32))
    completion_rationale = Column(String(2000))
    version = Column(Integer, nullable=False, default=1, server_default="1")
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class EngineeringExecutionActivityHistory(Base):
    __tablename__ = "engineering_execution_activity_history"
    __table_args__ = (
        CheckConstraint("from_standing IS NULL OR from_standing IN (" + ACTIVITY_STANDINGS + ")", name="ck_execution_activity_history_from"),
        CheckConstraint("to_standing IN (" + ACTIVITY_STANDINGS + ")", name="ck_execution_activity_history_to"),
        CheckConstraint("activity_version >= 1", name="ck_execution_activity_history_version"),
        CheckConstraint("length(btrim(rationale)) BETWEEN 1 AND 2000", name="ck_execution_activity_history_rationale"),
        UniqueConstraint("activity_id", "activity_version", name="uq_execution_activity_history_version"),
        Index("ix_execution_activity_history_order", "organization_id", "activity_id", "transitioned_at", "id"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    activity_id = Column(PGUUID(as_uuid=True), ForeignKey("engineering_execution_activities.id", ondelete="RESTRICT"), nullable=False)
    plan_id = Column(PGUUID(as_uuid=True), ForeignKey("engineering_execution_plans.id", ondelete="RESTRICT"), nullable=False)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    from_standing = Column(String(32))
    to_standing = Column(String(32), nullable=False)
    activity_version = Column(Integer, nullable=False)
    rationale = Column(String(2000), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    transitioned_at = Column(DateTime(timezone=True), nullable=False)


class EngineeringExecutionMilestone(Base):
    __tablename__ = "engineering_execution_milestones"
    __table_args__ = (
        CheckConstraint("length(btrim(title)) BETWEEN 1 AND 200", name="ck_execution_milestone_title"),
        CheckConstraint("length(btrim(completion_basis)) BETWEEN 1 AND 2000", name="ck_execution_milestone_basis"),
        CheckConstraint("ordinal BETWEEN 0 AND 49", name="ck_execution_milestone_ordinal"),
        UniqueConstraint("plan_id", "ordinal", name="uq_execution_milestone_ordinal", deferrable=True, initially="DEFERRED"),
        Index("ix_execution_milestone_order", "organization_id", "project_id", "plan_id", "ordinal", "id"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    plan_id = Column(PGUUID(as_uuid=True), ForeignKey("engineering_execution_plans.id", ondelete="RESTRICT"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    title = Column(String(200), nullable=False)
    completion_basis = Column(String(2000), nullable=False)
    target_date = Column(Date)
    ordinal = Column(SmallInteger, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class EngineeringExecutionMilestoneActivity(Base):
    __tablename__ = "engineering_execution_milestone_activities"
    __table_args__ = (
        CheckConstraint("ordinal BETWEEN 0 AND 199", name="ck_execution_milestone_activity_ordinal"),
        UniqueConstraint("milestone_id", "ordinal", name="uq_execution_milestone_activity_ordinal"),
    )
    milestone_id = Column(PGUUID(as_uuid=True), ForeignKey("engineering_execution_milestones.id", ondelete="RESTRICT"), primary_key=True)
    activity_id = Column(PGUUID(as_uuid=True), ForeignKey("engineering_execution_activities.id", ondelete="RESTRICT"), primary_key=True)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    ordinal = Column(SmallInteger, nullable=False)


class EngineeringExecutionDependency(Base):
    __tablename__ = "engineering_execution_dependencies"
    __table_args__ = (
        CheckConstraint("predecessor_activity_id <> dependent_activity_id", name="ck_execution_dependency_not_self"),
        UniqueConstraint("plan_id", "predecessor_activity_id", "dependent_activity_id", name="uq_execution_dependency_edge"),
        Index("ix_execution_dependency_dependent", "organization_id", "plan_id", "dependent_activity_id"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    plan_id = Column(PGUUID(as_uuid=True), ForeignKey("engineering_execution_plans.id", ondelete="RESTRICT"), nullable=False)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    predecessor_activity_id = Column(PGUUID(as_uuid=True), ForeignKey("engineering_execution_activities.id", ondelete="RESTRICT"), nullable=False)
    dependent_activity_id = Column(PGUUID(as_uuid=True), ForeignKey("engineering_execution_activities.id", ondelete="RESTRICT"), nullable=False)


class EngineeringExecutionIdempotency(Base):
    __tablename__ = "engineering_execution_idempotency"
    __table_args__ = (
        CheckConstraint("length(fingerprint) = 64", name="ck_execution_idempotency_fingerprint"),
        CheckConstraint("length(replay_json::text) <= 1024", name="ck_execution_idempotency_replay_size"),
        CheckConstraint("jsonb_typeof(replay_json) = 'object' AND replay_json->>'schema' = 'execution.idempotency.v1' AND replay_json->>'operation' = operation AND jsonb_typeof(replay_json->'result') = 'object' AND replay_json->'result'->>'outcome' = 'success' AND NOT (replay_json ?| ARRAY['rationale','description','completion_basis','blocker_rationale']) AND NOT ((replay_json->'result') ?| ARRAY['rationale','description','completion_basis','blocker_rationale'])", name="ck_execution_idempotency_shape"),
        UniqueConstraint("organization_id", "actor_id", "operation", "idempotency_key", name="uq_execution_idempotency_key"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    operation = Column(String(32), nullable=False)
    idempotency_key = Column(PGUUID(as_uuid=True), nullable=False)
    fingerprint = Column(String(64), nullable=False)
    replay_json = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
