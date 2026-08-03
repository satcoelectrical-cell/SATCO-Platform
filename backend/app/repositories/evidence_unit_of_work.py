"""Atomic Evidence Unit of Work and persistence adapters."""
from datetime import datetime, timezone
from typing import Mapping, Self
from uuid import UUID
from sqlalchemy.orm import Session
from app.exceptions.evidence import EvidenceIdempotencyConflict, EvidenceValidationError
from app.models.audit_log import AuditLog
from app.models.evidence import Evidence
from app.models.evidence_command import EvidenceActor, EvidenceEvent, EvidenceIdempotency, EvidenceOutcome, EvidenceOutbox, EvidenceResult
from app.models.engineering_workspace import EngineeringWorkspace, EngineeringWorkspaceMember
from app.models.project import Project
from app.models.user import User
from app.repositories.evidence_repository import SqlAlchemyEvidenceRepository

def _json(value):
    if isinstance(value,(UUID,datetime)): return value.isoformat() if isinstance(value,datetime) else str(value)
    if isinstance(value,Mapping): return {k:_json(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)): return [_json(v) for v in value]
    return value

class SqlAlchemyEvidenceAuditRecorder:
    def __init__(self,session): self.session=session
    def record(self,**values):
        actor=values.pop("actor"); evidence_id=values.pop("evidence_id"); action=values.pop("command_type")
        self.session.add(AuditLog(user_id=actor.actor_id,action=action,entity="EVIDENCE",entity_uuid=evidence_id,details=_json(values)))

class SqlAlchemyEvidenceEventRecorder:
    def __init__(self,session): self.session=session
    def record(self,events:tuple[EvidenceEvent,...]):
        for event in events:
            self.session.add(EvidenceOutbox(event_id=event.event_id,aggregate_id=event.evidence_id,aggregate_version=event.aggregate_version,event_type=event.event_type,payload=_json(event.payload),occurred_at=event.occurred_at))

class SqlAlchemyEvidenceIdempotencyStore:
    def __init__(self,session): self.session=session; self.reservation=None
    def find(self,*,actor_id,command_type,idempotency_id,request_fingerprint):
        row=self.session.query(EvidenceIdempotency).filter_by(actor_id=actor_id,command_type=command_type,idempotency_id=idempotency_id).first()
        if row is None: return None
        if row.request_fingerprint!=request_fingerprint or row.status!="completed" or row.result is None: raise EvidenceIdempotencyConflict()
        data=row.result
        return EvidenceOutcome(EvidenceResult(UUID(data["evidence_id"]),data["previous_version"],data["version"],data["command_type"],UUID(data["correlation_id"]),()),data["authorized_state"])
    def reserve(self,**values):
        self.reservation=EvidenceIdempotency(**values,status="pending"); self.session.add(self.reservation); self.session.flush()
    def record_result(self,result,authorized_state):
        if self.reservation is None: raise RuntimeError("Idempotency reservation is required")
        self.reservation.status="completed"; self.reservation.aggregate_id=result.evidence_id; self.reservation.result=_json({"evidence_id":result.evidence_id,"previous_version":result.previous_version,"version":result.version,"command_type":result.command_type,"correlation_id":result.correlation_id,"authorized_state":authorized_state})

class UtcEvidenceClock:
    def now(self): return datetime.now(timezone.utc)

class SqlAlchemyEvidenceAuthorizationPolicy:
    def __init__(self,session): self.session=session
    def authorize(self,*,actor:EvidenceActor,operation:str,evidence:Evidence|None,project_id:int|None,workspace_id:int|None):
        user=self.session.get(User,actor.actor_id)
        if user is None or not user.is_active: return False
        if evidence is not None and evidence.organization_id!=actor.organization_id: return False
        if project_id is None: return True
        project=self.session.query(Project).filter_by(
            id=project_id, organization_id=actor.organization_id
        ).first()
        if project is None: return False
        if user.role=="admin": return True
        if actor.actor_id in {project.owner_id,project.primary_assignee_id}: return True
        if workspace_id is None: return False
        workspace=self.session.get(EngineeringWorkspace,workspace_id)
        return workspace is not None and workspace.project_id==project_id and (actor.actor_id in {workspace.owner_id,workspace.primary_assignee_id} or self.session.get(EngineeringWorkspaceMember,(workspace.id,actor.actor_id)) is not None)

class SqlAlchemyEvidenceValidator:
    def __init__(self,session): self.session=session
    def validate_scope(self,*,actor,project_id,workspace_id):
        if workspace_id is not None and project_id is None: raise EvidenceValidationError("Workspace requires Project")
        project = None if project_id is None else self.session.query(Project).filter_by(
            id=project_id, organization_id=actor.organization_id
        ).first()
        if project_id is not None and project is None: raise EvidenceValidationError("Project is invalid")
        if workspace_id is not None:
            workspace=self.session.query(EngineeringWorkspace).join(
                Project, Project.id == EngineeringWorkspace.project_id
            ).filter(
                EngineeringWorkspace.id == workspace_id,
                EngineeringWorkspace.project_id == project_id,
                Project.organization_id == actor.organization_id,
            ).first()
            if workspace is None: raise EvidenceValidationError("Workspace is invalid")
    def validate_reference(self,*,actor,evidence_id,project_id,workspace_ids):
        evidence=self.session.query(Evidence).filter_by(id=evidence_id,organization_id=actor.organization_id).first()
        if evidence is None: raise EvidenceValidationError("Evidence is unavailable")
        if evidence.lifecycle!="current" or evidence.source_standing!="current": raise EvidenceValidationError("Evidence is not acceptable")
        if evidence.project_id is not None and evidence.project_id!=project_id: raise EvidenceValidationError("Cross-Project Evidence is denied")
        if evidence.workspace_id is not None and evidence.workspace_id not in workspace_ids: raise EvidenceValidationError("Evidence Workspace is incompatible")
        return evidence

class SqlAlchemyEvidenceUnitOfWork:
    def __init__(self,session_factory): self.session_factory=session_factory
    def __enter__(self)->Self:
        self.session=self.session_factory(); self.evidence=SqlAlchemyEvidenceRepository(self.session); self.audit=SqlAlchemyEvidenceAuditRecorder(self.session); self.domain_events=SqlAlchemyEvidenceEventRecorder(self.session); self.idempotency=SqlAlchemyEvidenceIdempotencyStore(self.session); return self
    def __exit__(self,exc_type,exc_value,traceback):
        if exc_type is not None: self.rollback()
        self.session.close()
    def commit(self): self.session.commit()
    def rollback(self): self.session.rollback()
