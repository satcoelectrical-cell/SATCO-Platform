from datetime import datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, SmallInteger, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.core.database import Base
from app.enums.project_foundation import ProjectEngineeringStage, ProjectInputSourceKind, ProjectInputStanding, ProjectScopeKind


class ProjectFoundation(Base):
    __tablename__ = "project_foundations"
    __table_args__ = (
        CheckConstraint("length(btrim(purpose)) BETWEEN 1 AND 2000", name="ck_project_foundation_purpose"),
        CheckConstraint("length(btrim(engineering_basis)) BETWEEN 1 AND 5000", name="ck_project_foundation_basis"),
        CheckConstraint("stage IN ('definition','preparation','execution','verification','completion_readiness')", name="ck_project_foundation_stage"),
        CheckConstraint("version >= 1", name="ck_project_foundation_version"),
        Index("ix_project_foundation_scope", "organization_id", "project_id"),
    )
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="RESTRICT"), primary_key=True)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    purpose = Column(String(2000), nullable=False)
    engineering_basis = Column(String(5000), nullable=False)
    stage = Column(String(32), nullable=False, default=ProjectEngineeringStage.DEFINITION.value, server_default="definition")
    version = Column(Integer, nullable=False, default=1, server_default="1")
    established_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    established_at = Column(DateTime(timezone=True), nullable=False)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class ProjectScopeItem(Base):
    __tablename__ = "project_scope_items"
    __table_args__ = (
        CheckConstraint("kind IN ('in_scope','out_of_scope')", name="ck_project_scope_kind"),
        CheckConstraint("ordinal BETWEEN 0 AND 49", name="ck_project_scope_ordinal"),
        CheckConstraint("length(btrim(statement)) BETWEEN 1 AND 1000", name="ck_project_scope_statement"),
        UniqueConstraint("project_id", "kind", "ordinal", name="uq_project_scope_ordinal"),
        Index("ix_project_scope_order", "organization_id", "project_id", "kind", "ordinal"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    kind = Column(String(16), nullable=False)
    statement = Column(String(1000), nullable=False)
    ordinal = Column(SmallInteger, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class ProjectCompletionCriterion(Base):
    __tablename__ = "project_completion_criteria"
    __table_args__ = (
        CheckConstraint("ordinal BETWEEN 0 AND 49", name="ck_project_completion_ordinal"),
        CheckConstraint("length(btrim(statement)) BETWEEN 1 AND 1000", name="ck_project_completion_statement"),
        UniqueConstraint("project_id", "ordinal", name="uq_project_completion_ordinal"),
        Index("ix_project_completion_order", "organization_id", "project_id", "ordinal"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    statement = Column(String(1000), nullable=False)
    ordinal = Column(SmallInteger, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class ProjectRequiredInput(Base):
    __tablename__ = "project_required_inputs"
    __table_args__ = (
        CheckConstraint("length(btrim(title)) BETWEEN 1 AND 200", name="ck_project_input_title"),
        CheckConstraint("description IS NULL OR length(btrim(description)) BETWEEN 1 AND 2000", name="ck_project_input_description"),
        CheckConstraint("ordinal BETWEEN 0 AND 99", name="ck_project_input_ordinal"),
        CheckConstraint("required_by_stage IN ('definition','preparation','execution','verification','completion_readiness')", name="ck_project_input_required_stage"),
        CheckConstraint("standing IN ('missing','received','clarification_required','not_applicable')", name="ck_project_input_standing"),
        CheckConstraint("version >= 1", name="ck_project_input_version"),
        CheckConstraint("length(btrim(standing_rationale)) BETWEEN 1 AND 2000", name="ck_project_input_rationale"),
        CheckConstraint("(standing='received' AND source_kind IN ('supporting_file','evidence') AND source_id IS NOT NULL AND source_version >= 1) OR (standing<>'received' AND source_kind IS NULL AND source_id IS NULL AND source_version IS NULL AND source_workspace_id IS NULL)", name="ck_project_input_source_pair"),
        UniqueConstraint("project_id", "ordinal", name="uq_project_input_ordinal", deferrable=True, initially="DEFERRED"),
        Index("ix_project_input_order", "organization_id", "project_id", "ordinal", "id"),
        Index("ix_project_input_source", "source_kind", "source_id"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(String(2000))
    ordinal = Column(SmallInteger, nullable=False)
    required_by_stage = Column(String(32), nullable=False)
    standing = Column(String(32), nullable=False, default=ProjectInputStanding.MISSING.value, server_default="missing")
    source_kind = Column(String(32))
    source_id = Column(PGUUID(as_uuid=True))
    source_version = Column(Integer)
    source_workspace_id = Column(Integer, ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"))
    standing_rationale = Column(String(2000), nullable=False)
    standing_changed_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    standing_changed_at = Column(DateTime(timezone=True), nullable=False)
    version = Column(Integer, nullable=False, default=1, server_default="1")
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class ProjectStageHistory(Base):
    __tablename__ = "project_stage_history"
    __table_args__ = (
        CheckConstraint("from_stage IS NULL OR from_stage IN ('definition','preparation','execution','verification','completion_readiness')", name="ck_project_stage_history_from"),
        CheckConstraint("to_stage IN ('definition','preparation','execution','verification','completion_readiness')", name="ck_project_stage_history_to"),
        CheckConstraint("foundation_version >= 1", name="ck_project_stage_history_version"),
        CheckConstraint("length(btrim(rationale)) BETWEEN 1 AND 2000", name="ck_project_stage_history_rationale"),
        UniqueConstraint("project_id", "foundation_version", name="uq_project_stage_history_version"),
        Index("ix_project_stage_history_order", "organization_id", "project_id", "transitioned_at", "id"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    from_stage = Column(String(32))
    to_stage = Column(String(32), nullable=False)
    foundation_version = Column(Integer, nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    rationale = Column(String(2000), nullable=False)
    transitioned_at = Column(DateTime(timezone=True), nullable=False)


def valid_input_transition(current: ProjectInputStanding, target: ProjectInputStanding) -> bool:
    allowed = {
        ProjectInputStanding.MISSING: {ProjectInputStanding.RECEIVED, ProjectInputStanding.CLARIFICATION_REQUIRED, ProjectInputStanding.NOT_APPLICABLE},
        ProjectInputStanding.CLARIFICATION_REQUIRED: {ProjectInputStanding.MISSING, ProjectInputStanding.RECEIVED, ProjectInputStanding.NOT_APPLICABLE},
        ProjectInputStanding.RECEIVED: {ProjectInputStanding.MISSING, ProjectInputStanding.CLARIFICATION_REQUIRED},
        ProjectInputStanding.NOT_APPLICABLE: {ProjectInputStanding.MISSING, ProjectInputStanding.CLARIFICATION_REQUIRED},
    }
    return target in allowed[current]
