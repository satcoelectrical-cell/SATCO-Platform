"""Evidence commands, events, and durable command records."""
from dataclasses import dataclass
from datetime import datetime
from typing import Mapping
from uuid import UUID, uuid4
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func
from app.core.database import Base
from app.enums import EvidenceLifecycle, EvidenceSourceKind, EvidenceSourceStanding

Scalar=str|int|bool|UUID|datetime|None
class EvidenceCommandError(ValueError): pass
class EvidenceVersionMismatch(EvidenceCommandError): pass
class EvidenceTransitionRejected(EvidenceCommandError): pass
@dataclass(frozen=True, slots=True)
class EvidenceActor:
    actor_id:int; organization_id:UUID
@dataclass(frozen=True, slots=True)
class EvidenceMetadata:
    actor:EvidenceActor; rationale:str; correlation_id:UUID; idempotency_id:UUID; command_id:UUID
    def __post_init__(self):
        if not self.rationale.strip(): raise ValueError("rationale must not be empty")
@dataclass(frozen=True, slots=True)
class CreateEvidence:
    metadata:EvidenceMetadata; organization_id:UUID; project_id:int|None; workspace_id:int|None; source_kind:EvidenceSourceKind; source_reference:str; source_revision:str; source_standing:EvidenceSourceStanding; effective_at:datetime|None; supported_fact:str; creator_id:int
@dataclass(frozen=True, slots=True)
class TransitionEvidenceLifecycle:
    metadata:EvidenceMetadata; evidence_id:UUID; expected_version:int; lifecycle:EvidenceLifecycle; replacement_evidence_id:UUID|None=None
@dataclass(frozen=True, slots=True)
class EvidenceEvent:
    event_id:UUID; event_type:str; evidence_id:UUID; aggregate_version:int; occurred_at:datetime; actor_id:int; correlation_id:UUID; causation_id:UUID; organization_id:UUID; payload:Mapping[str,Scalar]
@dataclass(frozen=True, slots=True)
class EvidenceResult:
    evidence_id:UUID; previous_version:int|None; version:int; command_type:str; correlation_id:UUID; events:tuple[EvidenceEvent,...]
@dataclass(frozen=True, slots=True)
class EvidenceOutcome:
    result:EvidenceResult; authorized_state:Mapping[str,object]
class EvidenceOutbox(Base):
    __tablename__="evidence_outbox"; __table_args__=(UniqueConstraint("event_id",name="uq_evidence_outbox_event"),CheckConstraint("aggregate_version>=1",name="ck_evidence_outbox_version"))
    id=Column(PGUUID(as_uuid=True),primary_key=True,default=uuid4); event_id=Column(PGUUID(as_uuid=True),nullable=False); aggregate_id=Column(PGUUID(as_uuid=True),ForeignKey("evidence.id",ondelete="RESTRICT"),nullable=False); aggregate_version=Column(Integer,nullable=False); event_type=Column(String(96),nullable=False); payload=Column(JSON,nullable=False); occurred_at=Column(DateTime(timezone=True),nullable=False); published_at=Column(DateTime(timezone=True)); created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
class EvidenceIdempotency(Base):
    __tablename__="evidence_idempotency"; __table_args__=(UniqueConstraint("actor_id","command_type","idempotency_id",name="uq_evidence_idempotency_scope"),CheckConstraint("status IN ('pending','completed')",name="ck_evidence_idempotency_status"))
    id=Column(PGUUID(as_uuid=True),primary_key=True,default=uuid4); actor_id=Column(Integer,ForeignKey("users.id",ondelete="RESTRICT"),nullable=False); command_type=Column(String(64),nullable=False); idempotency_id=Column(PGUUID(as_uuid=True),nullable=False); request_fingerprint=Column(String(64),nullable=False); status=Column(String(16),server_default="pending",nullable=False); aggregate_id=Column(PGUUID(as_uuid=True),ForeignKey("evidence.id",ondelete="RESTRICT")); result=Column(JSON); created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False); updated_at=Column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now(),nullable=False)
