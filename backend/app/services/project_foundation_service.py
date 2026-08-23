from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.enums.project_foundation import (
    PROJECT_STAGE_ORDER, PROJECT_STAGE_RANK, ProjectEngineeringStage,
    ProjectInputSourceKind, ProjectInputStanding, ProjectReadinessBlockerCode,
    ProjectReadinessState, ProjectScopeKind, is_forward_stage, stages_are_adjacent,
)
from app.exceptions.project_foundation import ProjectFoundationProtectedNotFound, ProjectFoundationUnavailable
from app.models.project_foundation import ProjectFoundation, ProjectRequiredInput, ProjectStageHistory, valid_input_transition
from app.schemas.project_foundation import (
    ProjectCompletionCriterionDTO, ProjectFoundationActor, ProjectFoundationConflictResult,
    ProjectFoundationEstablished, ProjectFoundationInvalidResult, ProjectFoundationNotEstablished,
    ProjectFoundationProtectedResult, ProjectFoundationUnavailableResult, ProjectInputMutationSuccess,
    ProjectInputReorderSuccess, ProjectInputSafeSource, ProjectInputSourceCandidatePage,
    ProjectReadinessBlocker, ProjectRequiredInputDTO, ProjectScopeItemDTO,
    ProjectStageReadiness, ProjectStageTransitionSuccess,
)


class UtcProjectFoundationClock:
    def now(self):
        return datetime.now(timezone.utc)


class ProjectFoundationService:
    def __init__(self, *, uow_factory, authorization, sources, clock=None):
        self.uow_factory = uow_factory
        self.authorization = authorization
        self.sources = sources
        self.clock = clock or UtcProjectFoundationClock()

    def get(self, *, project_id: int, actor: ProjectFoundationActor):
        try:
            with self.uow_factory() as uow:
                project = uow.repository.get_project(project_id, actor.organization_id)
                if project is None or not self.authorization.can_read(actor=actor, project=project):
                    return ProjectFoundationProtectedResult()
                root = uow.repository.get_foundation(project_id, actor.organization_id)
                can_mutate = self.authorization.can_mutate(actor=actor, project=project) and project.status not in {"completed", "cancelled"}
                if root is None:
                    return ProjectFoundationNotEstablished(project_id=project_id, allowed_actions=("establish",) if can_mutate else ())
                scope, criteria, inputs = uow.repository.load_children(project_id, actor.organization_id)
            return self._established(root, scope, criteria, inputs, actor, can_mutate)
        except ProjectFoundationUnavailable:
            return ProjectFoundationUnavailableResult()
        except SQLAlchemyError:
            return ProjectFoundationUnavailableResult()

    def put(self, *, project_id, data, actor):
        now = self.clock.now()
        try:
            with self.uow_factory() as uow:
                project = self._mutable_project(uow, project_id, actor)
                if project is None:
                    return ProjectFoundationProtectedResult()
                root = uow.repository.get_foundation(project_id, actor.organization_id, lock=True)
                if root is None:
                    if data.expected_version != 0:
                        return ProjectFoundationConflictResult()
                    root = ProjectFoundation(
                        project_id=project_id, organization_id=actor.organization_id,
                        purpose=data.purpose, engineering_basis=data.engineering_basis,
                        stage="definition", version=1, established_by_id=actor.actor_id,
                        established_at=now, updated_by_id=actor.actor_id, updated_at=now,
                    )
                    uow.repository.add(root)
                    uow.repository.flush()
                    uow.repository.add(ProjectStageHistory(
                        id=uuid4(), project_id=project_id, organization_id=actor.organization_id,
                        from_stage=None, to_stage="definition", foundation_version=1,
                        actor_id=actor.actor_id, rationale=data.rationale, transitioned_at=now,
                    ))
                    operation = "CREATE"
                else:
                    if root.version != data.expected_version:
                        return ProjectFoundationConflictResult()
                    if root.stage not in {"definition", "preparation"}:
                        return ProjectFoundationInvalidResult()
                    root.purpose, root.engineering_basis = data.purpose, data.engineering_basis
                    root.version += 1
                    root.updated_by_id, root.updated_at = actor.actor_id, now
                    operation = "UPDATE"
                uow.repository.replace_basis_children(
                    root, in_scope=data.in_scope, out_of_scope=data.out_of_scope,
                    completion_criteria=data.completion_criteria, actor_id=actor.actor_id, now=now,
                )
                uow.stage_audit(actor_id=actor.actor_id, project_id=project_id, operation=operation, details={
                    "operation": "put_basis", "version": root.version,
                    "changed_categories": ["definition", "scope", "completion_basis"],
                    "rationale": data.rationale,
                })
                uow.repository.flush(); uow.commit()
            return self.get(project_id=project_id, actor=actor)
        except IntegrityError:
            return ProjectFoundationConflictResult()
        except SQLAlchemyError:
            return ProjectFoundationUnavailableResult()

    def create_input(self, *, project_id, data, actor):
        now = self.clock.now()
        try:
            with self.uow_factory() as uow:
                project, root = self._locked_root(uow, project_id, actor, data.expected_foundation_version)
                if project is None:
                    return ProjectFoundationProtectedResult()
                if root is None:
                    return ProjectFoundationConflictResult()
                _, _, inputs = uow.repository.load_children(project_id, actor.organization_id)
                if len(inputs) >= 100 or data.ordinal > len(inputs) or any(item.title.casefold() == data.title.casefold() for item in inputs):
                    return ProjectFoundationInvalidResult()
                for item in reversed(inputs):
                    if item.ordinal >= data.ordinal:
                        item.ordinal += 1; item.version += 1; item.updated_by_id=actor.actor_id; item.updated_at=now
                item = ProjectRequiredInput(
                    id=uuid4(), project_id=project_id, organization_id=actor.organization_id,
                    title=data.title, description=data.description, ordinal=data.ordinal,
                    required_by_stage=data.required_by_stage.value, standing="missing",
                    standing_rationale=data.rationale, standing_changed_by_id=actor.actor_id,
                    standing_changed_at=now, version=1, created_by_id=actor.actor_id,
                    created_at=now, updated_by_id=actor.actor_id, updated_at=now,
                )
                uow.repository.add(item); root.version += 1; root.updated_by_id=actor.actor_id; root.updated_at=now
                self._audit(uow, actor, project_id, "CREATE", "create_input", root.version, data.rationale, item.id)
                uow.repository.flush(); uow.commit()
            return ProjectInputMutationSuccess(project_id=project_id, foundation_version=root.version, item=self._input_dto(item, None))
        except IntegrityError:
            return ProjectFoundationConflictResult()
        except SQLAlchemyError:
            return ProjectFoundationUnavailableResult()

    def update_input(self, *, project_id, input_id, data, actor):
        now = self.clock.now()
        try:
            with self.uow_factory() as uow:
                project, root = self._locked_root(uow, project_id, actor, data.expected_foundation_version)
                if project is None: return ProjectFoundationProtectedResult()
                if root is None: return ProjectFoundationConflictResult()
                item = uow.repository.get_input(input_id, project_id, actor.organization_id, lock=True)
                if item is None: return ProjectFoundationProtectedResult()
                if item.version != data.expected_input_version: return ProjectFoundationConflictResult()
                if item.standing not in {"missing", "clarification_required"}: return ProjectFoundationInvalidResult()
                _, _, inputs = uow.repository.load_children(project_id, actor.organization_id)
                if data.ordinal >= len(inputs) or any(other.id != item.id and other.title.casefold() == data.title.casefold() for other in inputs): return ProjectFoundationInvalidResult()
                ordered = [other for other in inputs if other.id != item.id]
                ordered.insert(data.ordinal, item)
                for ordinal, other in enumerate(ordered):
                    other.ordinal=ordinal; other.updated_by_id=actor.actor_id; other.updated_at=now
                item.title, item.description, item.required_by_stage = data.title, data.description, data.required_by_stage.value
                item.version += 1; item.updated_by_id=actor.actor_id; item.updated_at=now
                root.version += 1; root.updated_by_id=actor.actor_id; root.updated_at=now
                self._audit(uow, actor, project_id, "UPDATE", "update_input", root.version, data.rationale, item.id)
                uow.repository.flush(); uow.commit()
            return ProjectInputMutationSuccess(project_id=project_id, foundation_version=root.version, item=self._input_dto(item, None))
        except IntegrityError: return ProjectFoundationConflictResult()
        except SQLAlchemyError: return ProjectFoundationUnavailableResult()

    def reorder_inputs(self, *, project_id, data, actor):
        now=self.clock.now()
        try:
            with self.uow_factory() as uow:
                project, root=self._locked_root(uow,project_id,actor,data.expected_foundation_version)
                if project is None: return ProjectFoundationProtectedResult()
                if root is None: return ProjectFoundationConflictResult()
                if not uow.repository.reorder_inputs(project_id,actor.organization_id,data.ordered_input_ids,actor.actor_id,now): return ProjectFoundationInvalidResult()
                root.version+=1; root.updated_by_id=actor.actor_id; root.updated_at=now
                self._audit(uow,actor,project_id,"UPDATE","reorder_inputs",root.version,data.rationale)
                uow.repository.flush(); uow.commit()
            return ProjectInputReorderSuccess(project_id=project_id,foundation_version=root.version,ordered_input_ids=data.ordered_input_ids)
        except IntegrityError: return ProjectFoundationConflictResult()
        except SQLAlchemyError: return ProjectFoundationUnavailableResult()

    def transition_input(self, *, project_id, input_id, data, actor):
        now=self.clock.now()
        try:
            with self.uow_factory() as uow:
                project,root=self._locked_root(uow,project_id,actor,data.expected_foundation_version)
                if project is None: return ProjectFoundationProtectedResult()
                if root is None: return ProjectFoundationConflictResult()
                item=uow.repository.get_input(input_id,project_id,actor.organization_id,lock=True)
                if item is None: return ProjectFoundationProtectedResult()
                if item.version!=data.expected_input_version: return ProjectFoundationConflictResult()
                target=data.target_standing
                if not valid_input_transition(ProjectInputStanding(item.standing),target): return ProjectFoundationInvalidResult()
                source=None
                if target is ProjectInputStanding.RECEIVED:
                    try:
                        source=self.sources.authorize_exact(actor=actor,project_id=project_id,kind=data.source_kind,source_id=data.source_id,workspace_id=data.source_workspace_id)
                        source=self.sources.authorize_exact(actor=actor,project_id=project_id,kind=data.source_kind,source_id=data.source_id,workspace_id=data.source_workspace_id)
                    except ProjectFoundationProtectedNotFound: return ProjectFoundationProtectedResult()
                    except ProjectFoundationUnavailable: return ProjectFoundationUnavailableResult()
                    item.source_kind=source.kind.value; item.source_id=source.source_id; item.source_version=source.version; item.source_workspace_id=source.workspace_id
                else:
                    item.source_kind=item.source_id=item.source_version=item.source_workspace_id=None
                item.standing=target.value; item.standing_rationale=data.rationale
                item.standing_changed_by_id=actor.actor_id; item.standing_changed_at=now
                item.version+=1; item.updated_by_id=actor.actor_id; item.updated_at=now
                root.version+=1; root.updated_by_id=actor.actor_id; root.updated_at=now
                self._audit(uow,actor,project_id,"TRANSITION","transition_input",root.version,data.rationale,item.id,{"standing":target.value})
                uow.repository.flush(); uow.commit()
            return ProjectInputMutationSuccess(project_id=project_id,foundation_version=root.version,item=self._input_dto(item,source))
        except IntegrityError: return ProjectFoundationConflictResult()
        except SQLAlchemyError: return ProjectFoundationUnavailableResult()

    def transition_stage(self, *, project_id, data, actor):
        now=self.clock.now()
        try:
            with self.uow_factory() as uow:
                project,root=self._locked_root(uow,project_id,actor,data.expected_foundation_version)
                if project is None: return ProjectFoundationProtectedResult()
                if root is None: return ProjectFoundationConflictResult()
                current=ProjectEngineeringStage(root.stage); target=data.target_stage
                if not stages_are_adjacent(current,target): return ProjectFoundationInvalidResult()
                scope,criteria,inputs=uow.repository.load_children(project_id,actor.organization_id)
                if is_forward_stage(current,target):
                    readiness=self._readiness(root,scope,criteria,inputs,actor,target)
                    if readiness.state is not ProjectReadinessState.READY: return ProjectFoundationInvalidResult()
                previous=root.stage; root.stage=target.value; root.version+=1; root.updated_by_id=actor.actor_id; root.updated_at=now
                uow.repository.add(ProjectStageHistory(id=uuid4(),project_id=project_id,organization_id=actor.organization_id,from_stage=previous,to_stage=target.value,foundation_version=root.version,actor_id=actor.actor_id,rationale=data.rationale,transitioned_at=now))
                self._audit(uow,actor,project_id,"TRANSITION","transition_stage",root.version,data.rationale,extra={"from_stage":previous,"to_stage":target.value})
                uow.repository.flush(); uow.commit()
            return ProjectStageTransitionSuccess(project_id=project_id,previous_stage=previous,stage=target,foundation_version=root.version)
        except ProjectFoundationUnavailable: return ProjectFoundationUnavailableResult()
        except IntegrityError: return ProjectFoundationConflictResult()
        except SQLAlchemyError: return ProjectFoundationUnavailableResult()

    def list_source_candidates(self, *, project_id, kind, workspace_id, limit, actor):
        try:
            with self.uow_factory() as uow:
                project=uow.repository.get_project(project_id,actor.organization_id)
                if project is None or not self.authorization.can_read(actor=actor,project=project): return ProjectFoundationProtectedResult()
            items=self.sources.list_authorized(actor=actor,project_id=project_id,kind=kind,workspace_id=workspace_id,limit=limit)
            return ProjectInputSourceCandidatePage(items=items,visible_count=len(items))
        except ProjectFoundationProtectedNotFound: return ProjectFoundationProtectedResult()
        except Exception: return ProjectFoundationUnavailableResult()

    def _mutable_project(self,uow,project_id,actor):
        project=uow.repository.get_project(project_id,actor.organization_id,lock=True)
        if project is None or not self.authorization.can_mutate(actor=actor,project=project) or project.status in {"completed","cancelled"}: return None
        return project

    def _locked_root(self,uow,project_id,actor,expected):
        project=self._mutable_project(uow,project_id,actor)
        if project is None: return None,None
        root=uow.repository.get_foundation(project_id,actor.organization_id,lock=True)
        if root is None or root.version!=expected: return project,None
        return project,root

    def _established(self,root,scope,criteria,inputs,actor,can_mutate):
        source_map={}
        for item in inputs:
            if item.standing=="received":
                try: source_map[item.id]=self.sources.authorize_exact(actor=actor,project_id=root.project_id,kind=ProjectInputSourceKind(item.source_kind),source_id=item.source_id,workspace_id=item.source_workspace_id)
                except ProjectFoundationProtectedNotFound: source_map[item.id]=None
                except ProjectFoundationUnavailable: raise
        current=ProjectEngineeringStage(root.stage)
        target=None if current is ProjectEngineeringStage.COMPLETION_READINESS else PROJECT_STAGE_ORDER[PROJECT_STAGE_RANK[current]+1]
        readiness=self._readiness(root,scope,criteria,inputs,actor,target,source_map)
        in_scope=tuple(ProjectScopeItemDTO.model_validate(item,from_attributes=True) for item in scope if item.kind==ProjectScopeKind.IN_SCOPE.value)
        out_scope=tuple(ProjectScopeItemDTO.model_validate(item,from_attributes=True) for item in scope if item.kind==ProjectScopeKind.OUT_OF_SCOPE.value)
        criteria_dto=tuple(ProjectCompletionCriterionDTO.model_validate(item,from_attributes=True) for item in criteria)
        return ProjectFoundationEstablished(project_id=root.project_id,version=root.version,purpose=root.purpose,engineering_basis=root.engineering_basis,stage=current,in_scope=in_scope,out_of_scope=out_scope,completion_criteria=criteria_dto,inputs=tuple(self._input_dto(item,source_map.get(item.id)) for item in inputs),next_stage_readiness=readiness,allowed_actions=("edit_basis","manage_inputs","transition_stage") if can_mutate else (),established_at=root.established_at,updated_at=root.updated_at)

    def _readiness(self,root,scope,criteria,inputs,actor,target,source_map=None):
        if target is None: return ProjectStageReadiness(state="not_applicable",target_stage=None,blockers=())
        blockers=[]
        if not root.purpose.strip() or not root.engineering_basis.strip(): blockers.append(ProjectReadinessBlocker(code="definition_incomplete"))
        if not any(item.kind=="in_scope" for item in scope): blockers.append(ProjectReadinessBlocker(code="scope_incomplete"))
        if not criteria: blockers.append(ProjectReadinessBlocker(code="completion_basis_incomplete"))
        if not inputs: blockers.append(ProjectReadinessBlocker(code="required_inputs_not_defined"))
        sources={} if source_map is None else source_map
        for item in inputs:
            if PROJECT_STAGE_RANK[ProjectEngineeringStage(item.required_by_stage)]>PROJECT_STAGE_RANK[target]: continue
            if item.standing=="not_applicable": continue
            if item.standing=="missing": blockers.append(ProjectReadinessBlocker(code="input_missing",input_id=item.id,input_title=item.title)); continue
            if item.standing=="clarification_required": blockers.append(ProjectReadinessBlocker(code="input_clarification_required",input_id=item.id,input_title=item.title)); continue
            if item.id not in sources:
                try: sources[item.id]=self.sources.authorize_exact(actor=actor,project_id=root.project_id,kind=ProjectInputSourceKind(item.source_kind),source_id=item.source_id,workspace_id=item.source_workspace_id)
                except ProjectFoundationProtectedNotFound: sources[item.id]=None
                except ProjectFoundationUnavailable: raise
            if sources[item.id] is None: blockers.append(ProjectReadinessBlocker(code="input_source_reauthorization_required",input_id=item.id,input_title=item.title))
        return ProjectStageReadiness(state="blocked" if blockers else "ready",target_stage=target,blockers=tuple(blockers))

    @staticmethod
    def _input_dto(item,source):
        condition="authorized_current" if source is not None else "source_reauthorization_required" if item.standing=="received" else "not_required"
        return ProjectRequiredInputDTO(id=item.id,title=item.title,description=item.description,ordinal=item.ordinal,required_by_stage=item.required_by_stage,standing=item.standing,source_condition=condition,source=source,version=item.version,standing_changed_at=item.standing_changed_at,updated_at=item.updated_at)

    @staticmethod
    def _audit(uow,actor,project_id,action,operation,version,rationale,input_id=None,extra=None):
        details={"operation":operation,"version":version,"rationale":rationale}
        if input_id is not None: details["input_id"]=str(input_id)
        details.update(extra or {})
        uow.stage_audit(actor_id=actor.actor_id,project_id=project_id,operation=action,details=details)
