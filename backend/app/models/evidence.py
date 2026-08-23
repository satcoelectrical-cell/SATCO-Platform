"""Governed metadata-only Evidence Aggregate Root."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func
from app.core.database import Base
from app.enums import EvidenceLifecycle, EvidenceSourceKind, EvidenceSourceStanding
from app.models.evidence_command import CreateEvidence, EvidenceEvent, EvidenceResult, EvidenceTransitionRejected, EvidenceVersionMismatch, LinkEvidenceSupportingFiles, TransitionEvidenceLifecycle

TRANS={EvidenceLifecycle.PROPOSED:{EvidenceLifecycle.CURRENT,EvidenceLifecycle.WITHDRAWN,EvidenceLifecycle.REJECTED},EvidenceLifecycle.CURRENT:{EvidenceLifecycle.WITHDRAWN,EvidenceLifecycle.SUPERSEDED},EvidenceLifecycle.WITHDRAWN:{EvidenceLifecycle.PROPOSED},EvidenceLifecycle.SUPERSEDED:set(),EvidenceLifecycle.REJECTED:set()}
def vals(e): return ",".join(f"'{x.value}'" for x in e)
class Evidence(Base):
    __tablename__="evidence"; __table_args__=(CheckConstraint(f"lifecycle IN ({vals(EvidenceLifecycle)})",name="ck_evidence_lifecycle"),CheckConstraint(f"source_kind IN ({vals(EvidenceSourceKind)})",name="ck_evidence_source_kind"),CheckConstraint(f"source_standing IN ({vals(EvidenceSourceStanding)})",name="ck_evidence_source_standing"),CheckConstraint("workspace_id IS NULL OR project_id IS NOT NULL",name="ck_evidence_workspace_project"),CheckConstraint("version>=1",name="ck_evidence_version"),Index("ix_evidence_scope","organization_id","project_id","workspace_id","lifecycle"))
    id=Column(PGUUID(as_uuid=True),primary_key=True,default=uuid4); organization_id=Column(PGUUID(as_uuid=True),ForeignKey("organizations.id",ondelete="RESTRICT"),nullable=False); project_id=Column(Integer,ForeignKey("projects.id",ondelete="RESTRICT")); workspace_id=Column(Integer,ForeignKey("engineering_workspaces.id",ondelete="RESTRICT")); lifecycle=Column(String(16),default="proposed",server_default="proposed",nullable=False); source_kind=Column(String(32),nullable=False); source_reference=Column(String(512),nullable=False); source_revision=Column(String(128),nullable=False); source_standing=Column(String(16),nullable=False); effective_at=Column(DateTime(timezone=True)); supported_fact=Column(String(2000),nullable=False); creator_id=Column(Integer,ForeignKey("users.id",ondelete="RESTRICT"),nullable=False); version=Column(Integer,default=1,server_default="1",nullable=False); supporting_file_links_sealed_at=Column(DateTime(timezone=True)); created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False); updated_at=Column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now(),nullable=False)
    @classmethod
    def create(cls,c:CreateEvidence,now:datetime):
        if c.organization_id!=c.metadata.actor.organization_id or c.creator_id!=c.metadata.actor.actor_id: raise ValueError("trusted scope mismatch")
        if c.workspace_id is not None and c.project_id is None: raise ValueError("Workspace requires Project")
        for v in (c.source_reference,c.source_revision,c.supported_fact):
            if not v.strip(): raise ValueError("Evidence metadata must not be empty")
        a=cls(id=uuid4(),organization_id=c.organization_id,project_id=c.project_id,workspace_id=c.workspace_id,lifecycle="proposed",source_kind=c.source_kind.value,source_reference=c.source_reference.strip(),source_revision=c.source_revision.strip(),source_standing=c.source_standing.value,effective_at=c.effective_at,supported_fact=c.supported_fact.strip(),creator_id=c.creator_id,version=1,created_at=now,updated_at=now)
        e=a._event(c,"EvidenceCreated",now); return a,EvidenceResult(a.id,None,1,type(c).__name__,c.metadata.correlation_id,(e,))
    def transition_lifecycle(self,c:TransitionEvidenceLifecycle,now:datetime):
        if c.evidence_id!=self.id: raise ValueError("identity mismatch")
        if c.expected_version!=self.version: raise EvidenceVersionMismatch()
        target=EvidenceLifecycle(c.lifecycle); current=EvidenceLifecycle(self.lifecycle)
        if target not in TRANS[current]: raise EvidenceTransitionRejected()
        if target is EvidenceLifecycle.CURRENT and self.source_standing!="current": raise EvidenceTransitionRejected("current Evidence requires current source")
        if target is EvidenceLifecycle.SUPERSEDED and (c.replacement_evidence_id is None or c.replacement_evidence_id==self.id): raise EvidenceTransitionRejected("replacement required")
        prev=self.version; self.lifecycle=target.value; self.version+=1; self.updated_at=now; e=self._event(c,"EvidenceLifecycleTransitioned",now); return EvidenceResult(self.id,prev,self.version,type(c).__name__,c.metadata.correlation_id,(e,))
    def link_supporting_files(self,c:LinkEvidenceSupportingFiles,now:datetime):
        if c.evidence_id != self.id or c.expected_version != self.version:
            raise EvidenceVersionMismatch()
        if self.lifecycle != EvidenceLifecycle.PROPOSED.value or self.supporting_file_links_sealed_at is not None:
            raise EvidenceTransitionRejected("Supporting File links are sealed")
        previous=self.version; self.version += 1; self.updated_at=now
        event=self._event(c,"EvidenceSupportingFilesLinked",now)
        event=EvidenceEvent(event.event_id,event.event_type,event.evidence_id,event.aggregate_version,event.occurred_at,event.actor_id,event.correlation_id,event.causation_id,event.organization_id,{"lifecycle":self.lifecycle,"supporting_file_count":len(c.asset_ids)})
        return EvidenceResult(self.id,previous,self.version,type(c).__name__,c.metadata.correlation_id,(event,))
    def _event(self,c,t,now): return EvidenceEvent(uuid4(),t,self.id,self.version,now,c.metadata.actor.actor_id,c.metadata.correlation_id,c.metadata.command_id,self.organization_id,{"lifecycle":self.lifecycle})
