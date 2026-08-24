from datetime import datetime, timezone
from hashlib import sha256
import json
from uuid import uuid4

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.enums.engineering_deliverable import revision_transition_allowed
from app.models.engineering_deliverable import EngineeringDeliverable, EngineeringDeliverableRevision, EngineeringDeliverableHistory, EngineeringDeliverableIdempotency, EngineeringDeliverableOutbox
from app.schemas.engineering_deliverable import DeliverableDTO, DeliverableIdempotencyConflictResult, DeliverableInvalidResult, DeliverableListResponse, DeliverableMutationSuccess, DeliverableProtectedResult, DeliverableRevisionDTO, DeliverableUnavailableResult, DeliverableVersionConflictResult


class EngineeringDeliverableService:
    def __init__(self, *, uow_factory, authorization, supporting_files=None, clock=None): self.uow_factory=uow_factory; self.authorization=authorization; self.supporting_files=supporting_files; self.clock=clock or (lambda: datetime.now(timezone.utc))
    def list(self, *, project_id, actor):
        try:
            with self.uow_factory() as uow:
                project=self.authorization.project(actor=actor, project_id=project_id)
                if not self.authorization.can_read(actor=actor, project=project): return DeliverableProtectedResult()
                visible=[]
                for row in uow.repository.list(organization_id=actor.organization_id,project_id=project_id):
                    revision=uow.repository.get_current_revision(deliverable=row)
                    if self._revision_visible(actor=actor,project=project,workspace_id=row.workspace_id,revision=revision): visible.append(self._dto(row,revision))
                return DeliverableListResponse(items=tuple(visible), visible_count=len(visible))
        except SQLAlchemyError: return DeliverableUnavailableResult()
    def get(self, *, project_id, deliverable_id, actor):
        try:
            with self.uow_factory() as uow:
                project=self.authorization.project(actor=actor, project_id=project_id)
                row=uow.repository.get(deliverable_id=deliverable_id,organization_id=actor.organization_id)
                revision=uow.repository.get_current_revision(deliverable=row) if row is not None else None
                if not self.authorization.can_read(actor=actor,project=project) or row is None or row.project_id!=project_id or not self._revision_visible(actor=actor,project=project,workspace_id=row.workspace_id,revision=revision): return DeliverableProtectedResult()
                return self._dto(row,revision)
        except SQLAlchemyError: return DeliverableUnavailableResult()
    def history(self, *, project_id, deliverable_id, actor):
        result=self.get(project_id=project_id,deliverable_id=deliverable_id,actor=actor)
        if not isinstance(result, DeliverableDTO): return result
        try:
            with self.uow_factory() as uow:
                row=uow.repository.get(deliverable_id=deliverable_id,organization_id=actor.organization_id)
                revisions=uow.repository.revisions(deliverable_id=row.id)
                project=self.authorization.project(actor=actor,project_id=project_id)
                if any(not self._revision_visible(actor=actor,project=project,workspace_id=row.workspace_id,revision=item) for item in revisions): return DeliverableProtectedResult()
                return DeliverableListResponse(items=tuple(self._dto(row,item) for item in revisions),visible_count=len(revisions))
        except SQLAlchemyError: return DeliverableUnavailableResult()
    def create(self, *, project_id,data,actor,idempotency_key): return self._mutate("create_deliverable",project_id,data,actor,idempotency_key,self._create)
    def update(self, *, project_id,deliverable_id,data,actor,idempotency_key): return self._mutate("update_deliverable",project_id,data,actor,idempotency_key,lambda uow,p,now: self._update(uow,p,deliverable_id,data,actor,now))
    def create_revision(self, *, project_id,deliverable_id,data,actor,idempotency_key): return self._mutate("create_revision",project_id,data,actor,idempotency_key,lambda uow,p,now: self._create_revision(uow,p,deliverable_id,data,actor,now))
    def transition_revision(self, *, project_id,deliverable_id,revision_id,data,actor,idempotency_key): return self._mutate("transition_revision",project_id,data,actor,idempotency_key,lambda uow,p,now: self._transition_revision(uow,p,deliverable_id,revision_id,data,actor,now))
    def _mutate(self, operation,project_id,data,actor,key,handler):
        now=self.clock() if callable(self.clock) else self.clock.now()
        try:
            with self.uow_factory() as uow:
                project=self.authorization.project(actor=actor,project_id=project_id,lock=True)
                if not self.authorization.can_mutate(actor=actor,project=project) or project.status in {"completed","cancelled"}: return DeliverableProtectedResult()
                fp=sha256(json.dumps({"operation":operation,"project":project_id,"organization":str(actor.organization_id),"data":data.model_dump(mode="json")},sort_keys=True,separators=(",", ":")).encode()).hexdigest()
                prior=uow.repository.get_idempotency(organization_id=actor.organization_id,actor_id=actor.actor_id,operation=operation,idempotency_key=key)
                if prior:
                    if prior.fingerprint!=fp: return DeliverableIdempotencyConflictResult()
                    return DeliverableMutationSuccess(**prior.replay_json)
                result=handler(uow,project,now)
                if not isinstance(result,DeliverableMutationSuccess): return result
                uow.repository.add(EngineeringDeliverableIdempotency(id=uuid4(),organization_id=actor.organization_id,actor_id=actor.actor_id,operation=operation,idempotency_key=key,fingerprint=fp,replay_json=result.model_dump(mode="json"),created_at=now))
                uow.stage_audit(actor_id=actor.actor_id,project_id=project_id,operation="ENGINEERING_DELIVERABLE",details={"operation":operation,"version":result.deliverable_version,"changed_categories":["deliverable"]})
                uow.repository.add(EngineeringDeliverableOutbox(id=uuid4(),event_id=uuid4(),deliverable_id=result.deliverable_id,aggregate_version=result.deliverable_version,event_type=f"Deliverable{operation.title()}",payload={"deliverable_id":str(result.deliverable_id),"version":result.deliverable_version},occurred_at=now))
                uow.repository.flush(); uow.commit(); return result
        except IntegrityError: return DeliverableVersionConflictResult()
        except SQLAlchemyError: return DeliverableUnavailableResult()
    def _create(self,uow,project,now):
        # data is captured by _mutate's closure only for the creation endpoint
        raise RuntimeError("creation handler must be bound")
    def create(self, *, project_id,data,actor,idempotency_key):
        return self._mutate("create_deliverable",project_id,data,actor,idempotency_key,lambda uow,p,now:self._create_bound(uow,p,data,actor,now))
    def _create_bound(self,uow,project,data,actor,now):
        if not self.authorization.valid_links(project=project,data=data) or not self._supporting_file_visible(actor=actor,project=project,workspace_id=data.workspace_id,asset_id=data.supporting_file_id): return DeliverableInvalidResult()
        row=EngineeringDeliverable(id=uuid4(),organization_id=actor.organization_id,project_id=project.id,workspace_id=data.workspace_id,activity_id=data.activity_id,milestone_id=data.milestone_id,code=data.code,title=data.title,discipline=data.discipline,deliverable_type=data.deliverable_type,purpose=data.purpose,external_authority=data.external_authority.value,responsible_user_id=data.responsible_user_id,target_date=data.target_date,standing="planned",current_revision_sequence=1,version=1,created_by_id=actor.actor_id,created_at=now,updated_by_id=actor.actor_id,updated_at=now)
        revision=EngineeringDeliverableRevision(id=uuid4(),deliverable_id=row.id,organization_id=actor.organization_id,project_id=project.id,sequence=1,external_label=data.initial_external_label,source_reference=data.source_reference,supporting_file_id=data.supporting_file_id,standing="draft",version=1,rationale=data.rationale,created_by_id=actor.actor_id,created_at=now,transitioned_by_id=actor.actor_id,transitioned_at=now)
        uow.repository.add(row);uow.repository.add(revision);uow.repository.add(EngineeringDeliverableHistory(id=uuid4(),deliverable_id=row.id,organization_id=actor.organization_id,aggregate_version=1,event_type="deliverable_created",revision_id=revision.id,actor_id=actor.actor_id,occurred_at=now));return DeliverableMutationSuccess(deliverable_id=row.id,deliverable_version=1,revision_id=revision.id,revision_version=1,standing="planned",revision_standing="draft")
    def _update(self,uow,project,ident,data,actor,now):
        row=uow.repository.get(deliverable_id=ident,organization_id=actor.organization_id,lock=True)
        if row is None or row.project_id!=project.id:return DeliverableProtectedResult()
        if row.version!=data.expected_version:return DeliverableVersionConflictResult()
        if not self.authorization.valid_links(project=project,data=data):return DeliverableInvalidResult()
        for name in ("code","title","discipline","deliverable_type","purpose","external_authority","workspace_id","activity_id","milestone_id","responsible_user_id","target_date"):
            value=getattr(data,name);setattr(row,name,value.value if name=="external_authority" else value)
        row.version+=1;row.updated_by_id=actor.actor_id;row.updated_at=now;uow.repository.add(EngineeringDeliverableHistory(id=uuid4(),deliverable_id=row.id,organization_id=actor.organization_id,aggregate_version=row.version,event_type="deliverable_updated",revision_id=None,actor_id=actor.actor_id,occurred_at=now));return DeliverableMutationSuccess(deliverable_id=row.id,deliverable_version=row.version,standing=row.standing)
    def _create_revision(self,uow,project,ident,data,actor,now):
        row=uow.repository.get(deliverable_id=ident,organization_id=actor.organization_id,lock=True)
        if row is None or row.project_id!=project.id:return DeliverableProtectedResult()
        current=uow.repository.get_current_revision(deliverable=row,lock=True)
        if row.version!=data.expected_deliverable_version or current is None or current.version!=data.expected_current_revision_version:return DeliverableVersionConflictResult()
        if current.standing in {"withdrawn","superseded"} or not self._supporting_file_visible(actor=actor,project=project,workspace_id=row.workspace_id,asset_id=data.supporting_file_id):return DeliverableInvalidResult()
        current.standing="superseded";current.version+=1;current.transitioned_by_id=actor.actor_id;current.transitioned_at=now
        row.current_revision_sequence+=1;row.version+=1;row.updated_by_id=actor.actor_id;row.updated_at=now
        revision=EngineeringDeliverableRevision(id=uuid4(),deliverable_id=row.id,organization_id=row.organization_id,project_id=row.project_id,sequence=row.current_revision_sequence,external_label=data.external_label,source_reference=data.source_reference,supporting_file_id=data.supporting_file_id,standing="draft",version=1,rationale=data.rationale,created_by_id=actor.actor_id,created_at=now,transitioned_by_id=actor.actor_id,transitioned_at=now)
        uow.repository.add(revision);uow.repository.add(EngineeringDeliverableHistory(id=uuid4(),deliverable_id=row.id,organization_id=row.organization_id,aggregate_version=row.version,event_type="revision_created",revision_id=revision.id,actor_id=actor.actor_id,occurred_at=now));return DeliverableMutationSuccess(deliverable_id=row.id,deliverable_version=row.version,revision_id=revision.id,revision_version=1,standing=row.standing,revision_standing="draft")
    def _transition_revision(self,uow,project,ident,revision_id,data,actor,now):
        row=uow.repository.get(deliverable_id=ident,organization_id=actor.organization_id,lock=True)
        if row is None or row.project_id!=project.id:return DeliverableProtectedResult()
        revision=next((r for r in uow.repository.revisions(deliverable_id=row.id) if r.id==revision_id),None)
        if revision is None:return DeliverableProtectedResult()
        if row.version!=data.expected_deliverable_version or revision.version!=data.expected_revision_version:return DeliverableVersionConflictResult()
        if revision.sequence!=row.current_revision_sequence or not revision_transition_allowed(revision.standing,data.target_standing.value):return DeliverableInvalidResult()
        revision.standing=data.target_standing.value;revision.version+=1;revision.transitioned_by_id=actor.actor_id;revision.transitioned_at=now;row.version+=1;row.updated_by_id=actor.actor_id;row.updated_at=now
        if revision.standing in {"ready_for_review","reviewed"}:row.standing=revision.standing
        elif revision.standing=="issued":row.standing="issued"
        elif revision.standing=="withdrawn":row.standing="withdrawn"
        uow.repository.add(EngineeringDeliverableHistory(id=uuid4(),deliverable_id=row.id,organization_id=row.organization_id,aggregate_version=row.version,event_type="revision_transitioned",revision_id=revision.id,actor_id=actor.actor_id,occurred_at=now));return DeliverableMutationSuccess(deliverable_id=row.id,deliverable_version=row.version,revision_id=revision.id,revision_version=revision.version,standing=row.standing,revision_standing=revision.standing)
    def _supporting_file_visible(self, *, actor, project, workspace_id, asset_id):
        return asset_id is None or (self.supporting_files is not None and self.supporting_files.visible(actor=actor,project=project,workspace_id=workspace_id,asset_id=asset_id))
    def _revision_visible(self, *, actor, project, workspace_id, revision):
        return revision is not None and self._supporting_file_visible(actor=actor,project=project,workspace_id=workspace_id,asset_id=revision.supporting_file_id)
    @staticmethod
    def _revision(row): return DeliverableRevisionDTO(id=row.id,sequence=row.sequence,external_label=row.external_label,source_reference=row.source_reference,representation_available=row.supporting_file_id is not None,standing=row.standing,version=row.version,created_at=row.created_at,transitioned_at=row.transitioned_at)
    def _dto(self,row,revision): return DeliverableDTO(id=row.id,project_id=row.project_id,workspace_id=row.workspace_id,code=row.code,title=row.title,discipline=row.discipline,deliverable_type=row.deliverable_type,purpose=row.purpose,external_authority=row.external_authority,responsible_user_id=row.responsible_user_id,target_date=row.target_date,standing=row.standing,version=row.version,activity_id=row.activity_id,milestone_id=row.milestone_id,current_revision=self._revision(revision))
