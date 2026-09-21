"""Prospective, actor-scoped Project Completeness observation history."""

from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from app.core.database import Base


class ProjectCompletenessObservation(Base):
    __tablename__ = "project_completeness_observations"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"), nullable=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    observation_version = Column(Integer, nullable=False, default=1)
    method_version = Column(String(64), nullable=False)
    catalog_digest = Column(String(64), nullable=False)
    source_digest = Column(String(64), nullable=False)
    source_cutoff = Column(DateTime(timezone=True), nullable=False)
    observed_at = Column(DateTime(timezone=True), nullable=False)
    assessment_status = Column(String(32), nullable=False)
    classifications_json = Column(JSONB, nullable=False)
    limitations_json = Column(JSONB, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "project_id", "workspace_id", "actor_id",
            "method_version", "catalog_digest", "source_digest",
            name="uq_project_completeness_observation_source",
        ),
        Index(
            "uq_project_completeness_project_source",
            "organization_id", "project_id", "actor_id", "method_version",
            "catalog_digest", "source_digest", unique=True,
            postgresql_where=text("workspace_id IS NULL"),
        ),
        Index(
            "ix_project_completeness_observation_history",
            "organization_id", "project_id", "workspace_id", "actor_id",
            "source_cutoff", "id",
        ),
    )
