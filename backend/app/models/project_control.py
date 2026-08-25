from uuid import uuid4
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from app.core.database import Base


class ProjectControlRoot(Base):
    __abstract__=True
    id=Column(PGUUID(as_uuid=True),primary_key=True,default=uuid4); organization_id=Column(PGUUID(as_uuid=True),ForeignKey("organizations.id",ondelete="RESTRICT"),nullable=False); project_id=Column(Integer,ForeignKey("projects.id",ondelete="RESTRICT"),nullable=False); workspace_id=Column(Integer,ForeignKey("engineering_workspaces.id",ondelete="RESTRICT")); version=Column(Integer,nullable=False,default=1,server_default="1"); created_by_id=Column(Integer,ForeignKey("users.id",ondelete="RESTRICT"),nullable=False); created_at=Column(DateTime(timezone=True),nullable=False); updated_by_id=Column(Integer,ForeignKey("users.id",ondelete="RESTRICT"),nullable=False); updated_at=Column(DateTime(timezone=True),nullable=False)

class ProjectRisk(ProjectControlRoot):
    __tablename__="project_risks"; __table_args__=(CheckConstraint("standing IN ('open','treated','accepted','closed')",name="ck_risk_standing"),CheckConstraint("likelihood IN ('low','medium','high') AND impact IN ('low','medium','high')",name="ck_risk_qualitative"),Index("ix_risk_project", "organization_id","project_id","standing","id"))
    statement=Column(String(2000),nullable=False); category=Column(String(80),nullable=False); likelihood=Column(String(16),nullable=False); impact=Column(String(16),nullable=False); standing=Column(String(16),nullable=False,server_default="open"); owner_id=Column(Integer,ForeignKey("users.id",ondelete="RESTRICT")); disposition=Column(String(2000))
class ProjectIssue(ProjectControlRoot):
    __tablename__="project_issues"; __table_args__=(CheckConstraint("standing IN ('open','resolved','closed')",name="ck_issue_standing"),Index("ix_issue_project","organization_id","project_id","standing","id"))
    statement=Column(String(2000),nullable=False); observed_context=Column(String(4000),nullable=False); severity=Column(String(16),nullable=False); standing=Column(String(16),nullable=False,server_default="open"); owner_id=Column(Integer,ForeignKey("users.id",ondelete="RESTRICT")); disposition=Column(String(2000))
class ProjectDecision(ProjectControlRoot):
    __tablename__="project_decisions"; __table_args__=(CheckConstraint("standing IN ('draft','accepted','superseded')",name="ck_decision_standing"),UniqueConstraint("predecessor_id",name="uq_decision_predecessor"))
    statement=Column(String(4000),nullable=False); rationale=Column(String(4000),nullable=False); alternatives=Column(JSONB); standing=Column(String(16),nullable=False,server_default="draft"); predecessor_id=Column(PGUUID(as_uuid=True),ForeignKey("project_decisions.id",ondelete="RESTRICT")); accepted_by_id=Column(Integer,ForeignKey("users.id",ondelete="RESTRICT")); accepted_at=Column(DateTime(timezone=True))
class ProjectChange(ProjectControlRoot):
    __tablename__="project_changes"; __table_args__=(CheckConstraint("standing IN ('recorded','confirmed','withdrawn')",name="ck_change_standing"),UniqueConstraint("predecessor_id",name="uq_change_predecessor"))
    statement=Column(String(4000),nullable=False); rationale=Column(String(4000),nullable=False); standing=Column(String(16),nullable=False,server_default="recorded"); predecessor_id=Column(PGUUID(as_uuid=True),ForeignKey("project_changes.id",ondelete="RESTRICT")); confirmed_by_id=Column(Integer,ForeignKey("users.id",ondelete="RESTRICT")); confirmed_at=Column(DateTime(timezone=True))
class ProjectChangeImpact(Base):
    __tablename__="project_change_impacts"; __table_args__=(CheckConstraint("standing IN ('potential','confirmed')",name="ck_change_impact_standing"),UniqueConstraint("change_id","target_kind","target_id",name="uq_change_impact_target"))
    id=Column(PGUUID(as_uuid=True),primary_key=True,default=uuid4); change_id=Column(PGUUID(as_uuid=True),ForeignKey("project_changes.id",ondelete="RESTRICT"),nullable=False); organization_id=Column(PGUUID(as_uuid=True),ForeignKey("organizations.id",ondelete="RESTRICT"),nullable=False); project_id=Column(Integer,ForeignKey("projects.id",ondelete="RESTRICT"),nullable=False); target_kind=Column(String(32),nullable=False); target_id=Column(PGUUID(as_uuid=True),nullable=False); statement=Column(String(2000),nullable=False); standing=Column(String(16),nullable=False,server_default="potential"); confirmed_by_id=Column(Integer,ForeignKey("users.id",ondelete="RESTRICT")); confirmed_at=Column(DateTime(timezone=True),nullable=True)

class _ControlHistory(Base):
    __abstract__=True
    id=Column(PGUUID(as_uuid=True),primary_key=True,default=uuid4); organization_id=Column(PGUUID(as_uuid=True),ForeignKey("organizations.id",ondelete="RESTRICT"),nullable=False); project_id=Column(Integer,ForeignKey("projects.id",ondelete="RESTRICT"),nullable=False); aggregate_version=Column(Integer,nullable=False); event_type=Column(String(80),nullable=False); actor_id=Column(Integer,ForeignKey("users.id",ondelete="RESTRICT"),nullable=False); occurred_at=Column(DateTime(timezone=True),nullable=False)
class ProjectRiskHistory(_ControlHistory):
    __tablename__="project_risk_history"; __table_args__=(UniqueConstraint("risk_id","aggregate_version",name="uq_risk_history_version"),CheckConstraint("aggregate_version>=1",name="ck_risk_history_version")); risk_id=Column(PGUUID(as_uuid=True),ForeignKey("project_risks.id",ondelete="RESTRICT"),nullable=False)
class ProjectIssueHistory(_ControlHistory):
    __tablename__="project_issue_history"; __table_args__=(UniqueConstraint("issue_id","aggregate_version",name="uq_issue_history_version"),CheckConstraint("aggregate_version>=1",name="ck_issue_history_version")); issue_id=Column(PGUUID(as_uuid=True),ForeignKey("project_issues.id",ondelete="RESTRICT"),nullable=False)
class ProjectDecisionHistory(_ControlHistory):
    __tablename__="project_decision_history"; __table_args__=(UniqueConstraint("decision_id","aggregate_version",name="uq_decision_history_version"),CheckConstraint("aggregate_version>=1",name="ck_decision_history_version")); decision_id=Column(PGUUID(as_uuid=True),ForeignKey("project_decisions.id",ondelete="RESTRICT"),nullable=False)
class ProjectChangeHistory(_ControlHistory):
    __tablename__="project_change_history"; __table_args__=(UniqueConstraint("change_id","aggregate_version",name="uq_change_history_version"),CheckConstraint("aggregate_version>=1",name="ck_change_history_version")); change_id=Column(PGUUID(as_uuid=True),ForeignKey("project_changes.id",ondelete="RESTRICT"),nullable=False)
class ProjectControlIdempotency(Base):
    __tablename__="project_control_idempotency"; __table_args__=(UniqueConstraint("organization_id","project_id","actor_id","operation","idempotency_key",name="uq_project_control_idempotency"),CheckConstraint("length(fingerprint)=64",name="ck_project_control_idempotency_fingerprint"),CheckConstraint("length(replay_json::text)<=1024",name="ck_project_control_idempotency_size"))
    id=Column(PGUUID(as_uuid=True),primary_key=True,default=uuid4); organization_id=Column(PGUUID(as_uuid=True),ForeignKey("organizations.id",ondelete="RESTRICT"),nullable=False); project_id=Column(Integer,ForeignKey("projects.id",ondelete="RESTRICT"),nullable=False); actor_id=Column(Integer,ForeignKey("users.id",ondelete="RESTRICT"),nullable=False); operation=Column(String(48),nullable=False); idempotency_key=Column(PGUUID(as_uuid=True),nullable=False); fingerprint=Column(String(64),nullable=False); replay_json=Column(JSONB,nullable=False); created_at=Column(DateTime(timezone=True),nullable=False)
class ProjectControlOutbox(Base):
    __tablename__="project_control_outbox"; __table_args__=(UniqueConstraint("event_id",name="uq_project_control_outbox_event"),CheckConstraint("aggregate_kind IN ('risk','issue','decision','change')",name="ck_project_control_outbox_kind"))
    id=Column(PGUUID(as_uuid=True),primary_key=True,default=uuid4); event_id=Column(PGUUID(as_uuid=True),nullable=False); organization_id=Column(PGUUID(as_uuid=True),ForeignKey("organizations.id",ondelete="RESTRICT"),nullable=False); project_id=Column(Integer,ForeignKey("projects.id",ondelete="RESTRICT"),nullable=False); aggregate_kind=Column(String(16),nullable=False); aggregate_id=Column(PGUUID(as_uuid=True),nullable=False); aggregate_version=Column(Integer,nullable=False); event_type=Column(String(96),nullable=False); payload=Column(JSONB,nullable=False); occurred_at=Column(DateTime(timezone=True),nullable=False)
