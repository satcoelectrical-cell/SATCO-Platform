from datetime import datetime, timezone
from hashlib import sha256
import json
from uuid import uuid4

from sqlalchemy.exc import DBAPIError, IntegrityError, SQLAlchemyError

from app.enums.engineering_deliverable import revision_transition_allowed
from app.models.engineering_deliverable import EngineeringDeliverable, EngineeringDeliverableRevision, EngineeringDeliverableHistory, EngineeringDeliverableIdempotency, EngineeringDeliverableOutbox
from app.discipline_packages.descriptors.eic_v1 import DESCRIPTORS_V1
from app.schemas.engineering_deliverable import DeliverableDTO, DeliverableIdempotencyConflictResult, DeliverableInvalidResult, DeliverableListResponse, DeliverableMutationSuccess, DeliverableProtectedResult, DeliverableRevisionDTO, DeliverableRevisionGraphSummary, DeliverableRepresentationGraphLink, DeliverableUnavailableResult, DeliverableVersionConflictResult, DeliverableGraphIncidentLink, DeliverableGraphIncidentPage
from app.services.patch_052_mutation_guard import (
    Patch052MutationProtected,
    Patch052MutationUnavailable,
    lock_package_context,
)


class EngineeringDeliverableService:
    def __init__(self, *, uow_factory, authorization, supporting_files=None, clock=None, package_uow_factory=None): self.uow_factory=uow_factory; self.authorization=authorization; self.supporting_files=supporting_files; self.clock=clock or (lambda: datetime.now(timezone.utc)); self.package_uow_factory=package_uow_factory
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
    def get_authorized_revision(self, *, project_id, revision_id, actor):
        """Exact revision UUID read through the canonical Deliverable authority."""
        try:
            with self.uow_factory() as uow:
                revision = uow.repository.get_revision(
                    revision_id=revision_id, organization_id=actor.organization_id,
                )
                if revision is None or revision.project_id != project_id:
                    return DeliverableProtectedResult()
                row = uow.repository.get(
                    deliverable_id=revision.deliverable_id,
                    organization_id=actor.organization_id,
                )
                project = self.authorization.project(actor=actor, project_id=project_id)
                if row is None or project is None or row.project_id != project_id or not self.authorization.can_read(actor=actor, project=project):
                    return DeliverableProtectedResult()
                if not self._revision_visible(actor=actor, project=project, workspace_id=row.workspace_id, revision=revision):
                    return DeliverableProtectedResult()
                return DeliverableRevisionGraphSummary(
                    id=revision.id, deliverable_id=row.id, project_id=row.project_id,
                    workspace_id=row.workspace_id, sequence=revision.sequence,
                    external_label=revision.external_label, standing=revision.standing,
                    version=revision.version,
                    representation_available=revision.supporting_file_id is not None,
                    external_authority=row.external_authority,
                    created_at=revision.created_at, transitioned_at=revision.transitioned_at,
                )
        except SQLAlchemyError:
            return DeliverableUnavailableResult()
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
    def get_authorized_representation_link(self, *, project_id, actor, revision_id=None, asset_id=None):
        """Exact canonical relation read; exactly one endpoint selector is supplied."""
        if (revision_id is None)==(asset_id is None): return DeliverableInvalidResult()
        try:
            with self.uow_factory() as uow:
                revision=(uow.repository.get_revision(revision_id=revision_id,organization_id=actor.organization_id) if revision_id is not None else uow.repository.get_revision_by_supporting_file(asset_id=asset_id,organization_id=actor.organization_id))
                if revision is None or revision.project_id!=project_id or revision.supporting_file_id is None:return DeliverableProtectedResult()
                row=uow.repository.get(deliverable_id=revision.deliverable_id,organization_id=actor.organization_id);project=self.authorization.project(actor=actor,project_id=project_id)
                if row is None or project is None or not self.authorization.can_read(actor=actor,project=project) or not self._revision_visible(actor=actor,project=project,workspace_id=row.workspace_id,revision=revision):return DeliverableProtectedResult()
                return DeliverableRepresentationGraphLink(revision_id=revision.id,asset_id=revision.supporting_file_id,deliverable_id=row.id,project_id=row.project_id,workspace_id=row.workspace_id,revision_version=revision.version)
        except SQLAlchemyError:return DeliverableUnavailableResult()
    def list_authorized_incident_graph_links(self, *, project_id, actor, selector_kind, selector_id, limit=91):
        if selector_kind not in {"deliverable","deliverable_revision","activity","milestone","supporting_file"} or not 1<=limit<=91:return DeliverableInvalidResult()
        try:
            with self.uow_factory() as uow:
                project=self.authorization.project(actor=actor,project_id=project_id)
                if project is None or not self.authorization.can_read(actor=actor,project=project):return DeliverableProtectedResult()
                rows,has_more=uow.repository.list_graph_incident(selector_kind=selector_kind,selector_id=selector_id,organization_id=actor.organization_id,project_id=project_id,limit=limit)
                return DeliverableGraphIncidentPage(items=tuple(DeliverableGraphIncidentLink(relationship=row[0],relationship_selector=f"{row[2]}:{row[4]}",source_kind=row[1],source_id=row[2],target_kind=row[3],target_id=row[4],owner_version=row[5]) for row in rows),has_more=has_more)
        except SQLAlchemyError:return DeliverableUnavailableResult()
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
    def create_package_electrical(self, *, project_id, data, actor, idempotency_key, correlation_id):
        return self._create_package(
            package_key="electrical", project_id=project_id, data=data,
            actor=actor, idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
    def create_package_instrumentation(self, *, project_id, data, actor, idempotency_key, correlation_id):
        return self._create_package(
            package_key="instrumentation", project_id=project_id, data=data,
            actor=actor, idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
    def create_package_control_automation(self, *, project_id, data, actor, idempotency_key, correlation_id):
        return self._create_package(
            package_key="control_automation", project_id=project_id, data=data,
            actor=actor, idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
    def _create_package(self, *, package_key, project_id, data, actor, idempotency_key, correlation_id):
        if self.package_uow_factory is None:
            raise RuntimeError("package UoW factory is required")
        for attempt in range(3):
            try:
                return self._create_package_once(
                    package_key=package_key,
                    project_id=project_id, data=data, actor=actor,
                    idempotency_key=idempotency_key,
                    correlation_id=correlation_id,
                )
            except DBAPIError as exc:
                sqlstate=getattr(exc.orig,"pgcode",None) or getattr(exc.orig,"sqlstate",None)
                if sqlstate in {"23505","40001","40P01"} and attempt<2:continue
                if isinstance(exc,IntegrityError) or sqlstate in {"23505","40001","40P01"}:return DeliverableVersionConflictResult()
                return DeliverableUnavailableResult()
        return DeliverableVersionConflictResult()
    def _create_package_electrical_once(self,*,project_id,data,actor,idempotency_key,correlation_id):
        return self._create_package_once(package_key="electrical",project_id=project_id,data=data,actor=actor,idempotency_key=idempotency_key,correlation_id=correlation_id)
    def _create_package_once(self,*,package_key,project_id,data,actor,idempotency_key,correlation_id):
        now=self.clock() if callable(self.clock) else self.clock.now()
        operation = (
            "pkg_control_automation_create"
            if package_key == "control_automation"
            else f"package_{package_key}_create"
        )
        fp=sha256(json.dumps({"operation":operation,"project":project_id,"organization":str(actor.organization_id),"data":data.model_dump(mode="json")},sort_keys=True,separators=(",", ":")).encode()).hexdigest()
        try:
            with self.package_uow_factory() as uow:
                context=lock_package_context(uow,package_key=package_key,actor_id=actor.actor_id,organization_id=actor.organization_id,auth_version=actor.auth_version,project_id=project_id,workspace_id=data.workspace_id)
                project=context.project;selection=context.selection;registry=context.registry
                prior=uow.repository.get_idempotency(organization_id=actor.organization_id,actor_id=actor.actor_id,operation=operation,idempotency_key=idempotency_key)
                if prior:
                    if prior.fingerprint!=fp:return DeliverableIdempotencyConflictResult()
                    return DeliverableMutationSuccess(**prior.replay_json)
                result=self._stage_package(uow,package_key,project,data,actor,now,correlation_id,selection,registry)
                if not isinstance(result,DeliverableMutationSuccess):return result
                uow.repository.add(EngineeringDeliverableIdempotency(id=uuid4(),organization_id=actor.organization_id,actor_id=actor.actor_id,operation=operation,idempotency_key=idempotency_key,fingerprint=fp,replay_json=result.model_dump(mode="json"),created_at=now))
                uow.stage_audit(actor_id=actor.actor_id,project_id=project_id,operation="ENGINEERING_DELIVERABLE",details={"operation":operation,"version":result.deliverable_version,"changed_categories":["deliverable"]})
                uow.repository.add(EngineeringDeliverableOutbox(id=uuid4(),event_id=uuid4(),deliverable_id=result.deliverable_id,aggregate_version=result.deliverable_version,event_type=f"DeliverablePackage_{package_key.title()}_Create",payload={"deliverable_id":str(result.deliverable_id),"version":result.deliverable_version},occurred_at=now))
                uow.repository.flush();uow.commit();return result
        except Patch052MutationProtected:return DeliverableProtectedResult()
        except Patch052MutationUnavailable:return DeliverableUnavailableResult()
    def _stage_package_electrical(self,uow,project,data,actor,now,correlation_id,selection,registry):
        return self._stage_package(uow,"electrical",project,data,actor,now,correlation_id,selection,registry)
    def _stage_package(self,uow,package_key,project,data,actor,now,correlation_id,selection,registry):
        descriptor=next(item for item in DESCRIPTORS_V1 if item.package_key==package_key)
        declaration=next((item for item in descriptor.contributions.deliverables if item.id==data.declaration_id),None)
        owner_discipline = "industrial_automation" if package_key == "control_automation" else package_key
        if declaration is None or data.discipline!=owner_discipline or data.deliverable_type!=declaration.deliverable_type_id or data.external_authority.value not in declaration.output_representation_ids:return DeliverableInvalidResult()
        if not self._valid_package_links(uow.repository.session,project,data):return DeliverableInvalidResult()
        origin={"origin_package_key":package_key,"origin_project_configuration_revision":selection.configuration_revision,"origin_declaration_id":declaration.id}
        result=self._create_bound(uow,project,data,actor,now,origin=origin,links_validated=True)
        if isinstance(result,DeliverableMutationSuccess):
            uow.stage_audit(actor_id=actor.actor_id,project_id=project.id,operation="DISCIPLINE_PACKAGE_OPERATION",details={"package_key":package_key,"package_version":selection.package_version,"descriptor_digest":selection.descriptor_digest,"registry_digest":registry.registry_digest,"project_configuration_revision":selection.configuration_revision,"declaration_id":declaration.id,"aggregate_id":str(result.deliverable_id),"aggregate_version":result.deliverable_version,"actor_id":actor.actor_id,"correlation_id":str(correlation_id),"outcome":"success"})
        return result
    @staticmethod
    def _valid_package_links(session,project,data):
        if data.responsible_user_id not in {None,project.owner_id,project.primary_assignee_id}:return False
        if data.activity_id is not None and session.execute(__import__('sqlalchemy').text("SELECT 1 FROM engineering_execution_activities WHERE id=:id AND project_id=:project FOR SHARE"),{"id":str(data.activity_id),"project":project.id}).first() is None:return False
        if data.milestone_id is not None and session.execute(__import__('sqlalchemy').text("SELECT 1 FROM engineering_execution_milestones WHERE id=:id AND project_id=:project FOR SHARE"),{"id":str(data.milestone_id),"project":project.id}).first() is None:return False
        return True
    def _create_bound(self,uow,project,data,actor,now,origin=None,links_validated=False):
        if (not links_validated and not self.authorization.valid_links(project=project,data=data)) or not self._supporting_file_visible(actor=actor,project=project,workspace_id=data.workspace_id,asset_id=data.supporting_file_id): return DeliverableInvalidResult()
        row=EngineeringDeliverable(id=uuid4(),organization_id=actor.organization_id,project_id=project.id,workspace_id=data.workspace_id,activity_id=data.activity_id,milestone_id=data.milestone_id,code=data.code,title=data.title,discipline=data.discipline,deliverable_type=data.deliverable_type,purpose=data.purpose,external_authority=data.external_authority.value,responsible_user_id=data.responsible_user_id,target_date=data.target_date,standing="planned",current_revision_sequence=1,version=1,created_by_id=actor.actor_id,created_at=now,updated_by_id=actor.actor_id,updated_at=now,**(origin or {}))
        revision=EngineeringDeliverableRevision(id=uuid4(),deliverable_id=row.id,organization_id=actor.organization_id,project_id=project.id,sequence=1,external_label=data.initial_external_label,source_reference=data.source_reference,supporting_file_id=data.supporting_file_id,standing="draft",version=1,rationale=data.rationale,created_by_id=actor.actor_id,created_at=now,transitioned_by_id=actor.actor_id,transitioned_at=now)
        uow.repository.add(row);uow.repository.flush();uow.repository.add(revision);uow.repository.flush();uow.repository.add(EngineeringDeliverableHistory(id=uuid4(),deliverable_id=row.id,organization_id=actor.organization_id,aggregate_version=1,event_type="deliverable_created",revision_id=revision.id,actor_id=actor.actor_id,occurred_at=now));return DeliverableMutationSuccess(deliverable_id=row.id,deliverable_version=1,revision_id=revision.id,revision_version=1,standing="planned",revision_standing="draft")
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
    def _dto(self,row,revision): return DeliverableDTO(id=row.id,project_id=row.project_id,workspace_id=row.workspace_id,code=row.code,title=row.title,discipline=row.discipline,deliverable_type=row.deliverable_type,purpose=row.purpose,external_authority=row.external_authority,responsible_user_id=row.responsible_user_id,target_date=row.target_date,standing=row.standing,version=row.version,activity_id=row.activity_id,milestone_id=row.milestone_id,current_revision=self._revision(revision),origin_package_key=row.origin_package_key,origin_project_configuration_revision=row.origin_project_configuration_revision,origin_declaration_id=row.origin_declaration_id)
