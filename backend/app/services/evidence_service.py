"""Evidence application orchestration."""
from hashlib import sha256
import json
from uuid import UUID, uuid4
from app.exceptions.evidence import EvidenceInvalidTransition, EvidenceProtectedNotFound, EvidenceVersionConflict
from app.models.evidence import Evidence
from app.models.evidence_command import CreateEvidence, EvidenceCommandError, EvidenceMetadata, EvidenceVersionMismatch, LinkEvidenceSupportingFiles, TransitionEvidenceLifecycle
from app.schemas.evidence import EvidenceListResponse, EvidenceResponse

def _fingerprint(command_type,data): return sha256(json.dumps({"command_type":command_type,"data":data},sort_keys=True,default=str,separators=(",",":")).encode()).hexdigest()
def _response(item,actions=()):
    data={c.name:getattr(item,c.name) for c in item.__table__.columns if c.name != "supporting_file_links_sealed_at"}; data["allowed_actions"]=actions
    return EvidenceResponse.model_validate(data)

class EvidenceService:
    def __init__(self,*,uow_factory,authorization,validator,clock): self.uow_factory=uow_factory; self.authorization=authorization; self.validator=validator; self.clock=clock
    def create(self,*,data,actor,correlation_id,idempotency_id):
        self.validator.validate_scope(actor=actor,project_id=data.project_id,workspace_id=data.workspace_id)
        if not self.authorization.authorize(actor=actor,operation="CreateEvidence",evidence=None,project_id=data.project_id,workspace_id=data.workspace_id): raise EvidenceProtectedNotFound()
        fp=_fingerprint("CreateEvidence",data.model_dump()); metadata=EvidenceMetadata(actor,data.rationale,correlation_id,idempotency_id,uuid4())
        with self.uow_factory() as uow:
            prior=uow.idempotency.find(actor_id=actor.actor_id,command_type="CreateEvidence",idempotency_id=idempotency_id,request_fingerprint=fp)
            if prior: return EvidenceResponse.model_validate(prior.authorized_state)
            uow.idempotency.reserve(actor_id=actor.actor_id,command_type="CreateEvidence",idempotency_id=idempotency_id,request_fingerprint=fp)
            aggregate,result=Evidence.create(CreateEvidence(metadata,actor.organization_id,data.project_id,data.workspace_id,data.source_kind,data.source_reference,data.source_revision,data.source_standing,data.effective_at,data.supported_fact,actor.actor_id),self.clock.now())
            uow.evidence.add(aggregate); response=_response(aggregate,("transition_lifecycle",)); self._stage(uow,result,metadata,response); uow.commit(); return response
    def transition_lifecycle(self,evidence_id,data,actor,correlation_id,idempotency_id):
        fp=_fingerprint("TransitionEvidenceLifecycle",data.model_dump()); metadata=EvidenceMetadata(actor,data.rationale,correlation_id,idempotency_id,uuid4())
        with self.uow_factory() as uow:
            prior=uow.idempotency.find(actor_id=actor.actor_id,command_type="TransitionEvidenceLifecycle",idempotency_id=idempotency_id,request_fingerprint=fp)
            aggregate=uow.evidence.get_scoped(evidence_id,actor.organization_id)
            if aggregate is None or not self.authorization.authorize(actor=actor,operation="TransitionEvidenceLifecycle",evidence=aggregate,project_id=aggregate.project_id,workspace_id=aggregate.workspace_id): raise EvidenceProtectedNotFound(evidence_id)
            if prior: return EvidenceResponse.model_validate(prior.authorized_state)
            uow.idempotency.reserve(actor_id=actor.actor_id,command_type="TransitionEvidenceLifecycle",idempotency_id=idempotency_id,request_fingerprint=fp)
            try: result=aggregate.transition_lifecycle(TransitionEvidenceLifecycle(metadata,evidence_id,data.expected_version,data.lifecycle,data.replacement_evidence_id),self.clock.now())
            except EvidenceVersionMismatch as exc: raise EvidenceVersionConflict() from exc
            except EvidenceCommandError as exc: raise EvidenceInvalidTransition(str(exc)) from exc
            if not uow.evidence.persist_expected_version(aggregate,data.expected_version): raise EvidenceVersionConflict()
            response=_response(aggregate); self._stage(uow,result,metadata,response); uow.commit(); return response
    def link_supporting_files(self,evidence_id,data,actor,correlation_id,idempotency_id):
        fp=_fingerprint("LinkEvidenceSupportingFiles",data.model_dump()); metadata=EvidenceMetadata(actor,data.rationale,correlation_id,idempotency_id,uuid4())
        with self.uow_factory() as uow:
            prior=uow.idempotency.find(actor_id=actor.actor_id,command_type="LinkEvidenceSupportingFiles",idempotency_id=idempotency_id,request_fingerprint=fp)
            aggregate=uow.evidence.get_scoped_for_update(evidence_id,actor.organization_id)
            if aggregate is None or aggregate.project_id is None or not self.authorization.authorize(actor=actor,operation="LinkEvidenceSupportingFiles",evidence=aggregate,project_id=aggregate.project_id,workspace_id=aggregate.workspace_id): raise EvidenceProtectedNotFound(evidence_id)
            if prior: return EvidenceResponse.model_validate(prior.authorized_state)
            uow.idempotency.reserve(actor_id=actor.actor_id,command_type="LinkEvidenceSupportingFiles",idempotency_id=idempotency_id,request_fingerprint=fp)
            uow.supporting_files.authorize_and_lock_for_evidence(actor_id=actor.actor_id,organization_id=actor.organization_id,project_id=aggregate.project_id,workspace_id=aggregate.workspace_id,asset_ids=data.asset_ids)
            try: result=aggregate.link_supporting_files(LinkEvidenceSupportingFiles(metadata,evidence_id,data.expected_version,data.asset_ids),self.clock.now())
            except EvidenceVersionMismatch as exc: raise EvidenceVersionConflict() from exc
            except EvidenceCommandError as exc: raise EvidenceInvalidTransition(str(exc)) from exc
            if not uow.evidence.persist_expected_version(aggregate,data.expected_version): raise EvidenceVersionConflict()
            uow.evidence.stage_supporting_file_links(evidence=aggregate,asset_ids=data.asset_ids,actor_id=actor.actor_id,linked_at=aggregate.updated_at)
            response=_response(aggregate); self._stage(uow,result,metadata,response); uow.commit(); return response
    def authorize_supporting_file_history(self, evidence_id, actor, historical):
        """Authorize the exact nested file basis through Evidence + file contracts."""
        with self.uow_factory() as uow:
            aggregate=uow.evidence.get_scoped_for_update(evidence_id,actor.organization_id)
            if aggregate is None or aggregate.project_id is None or not self.authorization.authorize(actor=actor,operation="ReadEvidence",evidence=aggregate,project_id=aggregate.project_id,workspace_id=aggregate.workspace_id):
                raise EvidenceProtectedNotFound(evidence_id)
            return uow.supporting_files.authorize_historical_for_evidence(
                actor_id=actor.actor_id, evidence_id=evidence_id,
                organization_id=actor.organization_id,
                project_id=aggregate.project_id,
                workspace_id=aggregate.workspace_id,
                historical=historical,
            )
    def get(self,evidence_id,actor):
        with self.uow_factory() as uow:
            item=uow.evidence.get_scoped(evidence_id,actor.organization_id)
            if item is None or not self.authorization.authorize(actor=actor,operation="ReadEvidence",evidence=item,project_id=item.project_id,workspace_id=item.workspace_id): raise EvidenceProtectedNotFound(evidence_id)
            return _response(item,("transition_lifecycle",))
    def list(self,*,project_id,filters,page,size,actor):
        if not self.authorization.authorize(actor=actor,operation="ListEvidence",evidence=None,project_id=project_id,workspace_id=filters.workspace_id): raise EvidenceProtectedNotFound()
        with self.uow_factory() as uow:
            items,total=uow.evidence.list_scoped(organization_id=actor.organization_id,project_id=project_id,filters=filters.model_dump(),page=page,size=size)
            visible=[_response(x,("transition_lifecycle",)) for x in items if self.authorization.authorize(actor=actor,operation="ReadEvidence",evidence=x,project_id=x.project_id,workspace_id=x.workspace_id)]
            return EvidenceListResponse(items=visible,total=len(visible) if len(visible)!=len(items) else total,page=page,size=size)
    @staticmethod
    def _stage(uow,result,metadata,response):
        uow.audit.record(command_type=result.command_type,actor=metadata.actor,evidence_id=result.evidence_id,correlation_id=metadata.correlation_id,idempotency_id=metadata.idempotency_id,rationale=metadata.rationale,previous_version=result.previous_version,version=result.version)
        uow.domain_events.record(result.events); uow.idempotency.record_result(result,response.model_dump())
