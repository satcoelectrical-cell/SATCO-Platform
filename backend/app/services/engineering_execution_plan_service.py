from datetime import datetime, timezone
from hashlib import sha256
import json
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.enums.engineering_execution_plan import ExecutionActivityStanding, ExecutionMilestoneStanding, valid_activity_transition
from app.exceptions.engineering_execution_plan import ExecutionPlanUnavailable
from app.models.engineering_execution_plan import (
    EngineeringExecutionActivity, EngineeringExecutionActivityHistory,
    EngineeringExecutionIdempotency, EngineeringExecutionMilestone,
    EngineeringExecutionPlan,
)
from app.schemas.engineering_execution_plan import (
    ExecutionActivityDTO, ExecutionDependencyDTO, ExecutionMilestoneDTO,
    ExecutionPlanEstablished, ExecutionPlanIdempotencyConflictResult,
    ExecutionPlanInvalidResult, ExecutionPlanMutationSuccess,
    ExecutionPlanNotEstablished, ExecutionPlanProtectedResult,
    ExecutionPlanUnavailableResult, ExecutionPlanVersionConflictResult,
    ExecutionProgressDTO, ExecutionActivityGraphSummary, ExecutionMilestoneGraphSummary,
    ExecutionGraphIncidentLink, ExecutionGraphIncidentPage,
)


class UtcExecutionPlanClock:
    def now(self): return datetime.now(timezone.utc)


class EngineeringExecutionPlanService:
    def __init__(self, *, uow_factory, authorization, foundation, clock=None):
        self.uow_factory, self.authorization, self.foundation = uow_factory, authorization, foundation
        self.clock = clock or UtcExecutionPlanClock()

    def get(self, *, project_id, actor):
        try:
            with self.uow_factory() as uow:
                project = self.authorization.get_project(actor=actor, project_id=project_id)
                if project is None or not self.authorization.can_read(actor=actor, project=project): return ExecutionPlanProtectedResult()
                plan = uow.repository.get_plan(project_id=project_id, organization_id=actor.organization_id)
                if plan is None: return ExecutionPlanNotEstablished(project_id=project_id, allowed_actions=("establish",) if self._mutable(actor, project) and self.foundation.is_established(actor=actor, project_id=project_id) else ())
                activities, milestones, dependencies = uow.repository.load_plan_children(plan_id=plan.id, organization_id=actor.organization_id)
                return self._read(plan, activities, milestones, dependencies)
        except (SQLAlchemyError, ExecutionPlanUnavailable): return ExecutionPlanUnavailableResult()

    def get_activity_graph_summary(self, *, actor, project_id, activity_id):
        """Exact authorized lookup; intentionally never loads plan children."""
        try:
            with self.uow_factory() as uow:
                project = self.authorization.get_project(actor=actor, project_id=project_id)
                if project is None or not self.authorization.can_read(actor=actor, project=project): return ExecutionPlanProtectedResult()
                plan = uow.repository.get_plan(project_id=project_id, organization_id=actor.organization_id)
                if plan is None: return ExecutionPlanProtectedResult()
                row = uow.repository.get_activity(activity_id=activity_id, plan_id=plan.id, organization_id=actor.organization_id)
                if row is None or (row.workspace_id is not None and not self.authorization.validate_workspace(actor=actor, project=project, workspace_id=row.workspace_id)): return ExecutionPlanProtectedResult()
                return ExecutionActivityGraphSummary(id=row.id, plan_id=row.plan_id, project_id=row.project_id, workspace_id=row.workspace_id, title=row.title, ordinal=row.ordinal, standing=row.standing, version=row.version, target_date=row.target_date, blocker_present=row.standing == "blocked")
        except (SQLAlchemyError, ExecutionPlanUnavailable): return ExecutionPlanUnavailableResult()

    def get_milestone_graph_summary(self, *, actor, project_id, milestone_id):
        """Exact authorized lookup; intentionally never scans milestone children."""
        try:
            with self.uow_factory() as uow:
                project = self.authorization.get_project(actor=actor, project_id=project_id)
                if project is None or not self.authorization.can_read(actor=actor, project=project): return ExecutionPlanProtectedResult()
                plan = uow.repository.get_plan(project_id=project_id, organization_id=actor.organization_id)
                if plan is None: return ExecutionPlanProtectedResult()
                row = uow.repository.get_milestone(milestone_id=milestone_id, plan_id=plan.id, organization_id=actor.organization_id)
                if row is None: return ExecutionPlanProtectedResult()
                linked_standings = uow.repository.get_milestone_activity_standings(milestone_id=row.id, organization_id=actor.organization_id)
                standing = "achieved" if linked_standings and all(item == "completed" for item in linked_standings) else "blocked" if any(item == "blocked" for item in linked_standings) else "not_ready"
                return ExecutionMilestoneGraphSummary(id=row.id, plan_id=row.plan_id, project_id=row.project_id, title=row.title, ordinal=row.ordinal, standing=standing, target_date=row.target_date)
        except (SQLAlchemyError, ExecutionPlanUnavailable): return ExecutionPlanUnavailableResult()

    def list_authorized_incident_graph_links(self, *, actor, project_id, selector_kind,
                                             selector_id, limit=91):
        """Canonical owner incident read for the closed execution vocabulary."""
        if selector_kind not in {"execution_plan", "activity", "milestone"} or not 1 <= limit <= 91:
            return ExecutionPlanInvalidResult()
        try:
            with self.uow_factory() as uow:
                project = self.authorization.get_project(actor=actor, project_id=project_id)
                if project is None or not self.authorization.can_read(actor=actor, project=project):
                    return ExecutionPlanProtectedResult()
                rows, has_more = uow.repository.list_graph_incident(
                    selector_kind=selector_kind, selector_id=selector_id,
                    project_id=project_id, organization_id=actor.organization_id,
                    limit=limit,
                )
                return ExecutionGraphIncidentPage(items=tuple(
                    ExecutionGraphIncidentLink(
                        relationship=row[0], relationship_selector=f"{row[2]}:{row[4]}",
                        source_kind=row[1], source_id=row[2], target_kind=row[3],
                        target_id=row[4], owner_version=row[5],
                    ) for row in rows
                ), has_more=has_more)
        except (SQLAlchemyError, ExecutionPlanUnavailable):
            return ExecutionPlanUnavailableResult()

    def establish(self, *, project_id, data, actor, idempotency_key: UUID):
        return self._mutate(operation="establish_plan", project_id=project_id, actor=actor, data=data, idempotency_key=idempotency_key, handler=self._establish)

    def create_activity(self, *, project_id, data, actor, idempotency_key: UUID):
        return self._mutate(operation="create_activity", project_id=project_id, actor=actor, data=data, idempotency_key=idempotency_key, handler=self._create_activity)

    def update_activity(self, *, project_id, activity_id, data, actor, idempotency_key: UUID):
        return self._mutate(operation="update_activity", project_id=project_id, actor=actor, data=data, idempotency_key=idempotency_key, handler=lambda uow, project, plan, now, data, actor: self._update_activity(uow, project, plan, activity_id, data, actor, now))

    def transition_activity(self, *, project_id, activity_id, data, actor, idempotency_key: UUID):
        return self._mutate(operation="transition_activity", project_id=project_id, actor=actor, data=data, idempotency_key=idempotency_key, handler=lambda uow, project, plan, now, data, actor: self._transition_activity(uow, project, plan, activity_id, data, actor, now))

    def replace_dependencies(self, *, project_id, data, actor, idempotency_key: UUID):
        return self._mutate(operation="replace_dependencies", project_id=project_id, actor=actor, data=data, idempotency_key=idempotency_key, handler=self._replace_dependencies)

    def create_milestone(self, *, project_id, data, actor, idempotency_key: UUID):
        return self._mutate(operation="create_milestone", project_id=project_id, actor=actor, data=data, idempotency_key=idempotency_key, handler=self._create_milestone)

    def update_milestone(self, *, project_id, milestone_id, data, actor, idempotency_key: UUID):
        return self._mutate(operation="update_milestone", project_id=project_id, actor=actor, data=data, idempotency_key=idempotency_key, handler=lambda uow, project, plan, now, data, actor: self._update_milestone(uow, project, plan, milestone_id, data, actor, now))

    def _mutate(self, *, operation, project_id, actor, data, idempotency_key, handler):
        now = self.clock.now()
        try:
            with self.uow_factory() as uow:
                project = self.authorization.get_project(actor=actor, project_id=project_id, lock=True)
                if project is None or not self._mutable(actor, project): return ExecutionPlanProtectedResult()
                fingerprint = self._fingerprint(operation, project_id, actor, data)
                replay = uow.repository.get_idempotency(organization_id=actor.organization_id, actor_id=actor.actor_id, operation=operation, idempotency_key=idempotency_key)
                if replay is not None:
                    if replay.fingerprint != fingerprint: return ExecutionPlanIdempotencyConflictResult()
                    return ExecutionPlanMutationSuccess(**replay.replay_json["result"])
                if not self.foundation.is_established(actor=actor, project_id=project_id): return ExecutionPlanInvalidResult()
                plan = uow.repository.get_plan(project_id=project_id, organization_id=actor.organization_id, lock=True)
                result = handler(uow, project, plan, now, data, actor)
                if not isinstance(result, ExecutionPlanMutationSuccess): return result
                uow.repository.add(EngineeringExecutionIdempotency(
                    id=uuid4(), organization_id=actor.organization_id, actor_id=actor.actor_id,
                    operation=operation, idempotency_key=idempotency_key, fingerprint=fingerprint,
                    replay_json={"schema": "execution.idempotency.v1", "operation": operation, "result": result.model_dump(mode="json")}, created_at=now,
                ))
                self._audit(uow, actor, project_id, operation, result.plan_version)
                uow.repository.flush(); uow.commit()
                return result
        except IntegrityError: return ExecutionPlanVersionConflictResult()
        except (SQLAlchemyError, ExecutionPlanUnavailable): return ExecutionPlanUnavailableResult()

    def _establish(self, uow, project, plan, now, data, actor):
        if plan is not None: return ExecutionPlanVersionConflictResult()
        plan = EngineeringExecutionPlan(id=uuid4(), project_id=project.id, organization_id=project.organization_id,
            version=1, established_by_id=actor.actor_id, established_at=now,
            updated_by_id=actor.actor_id, updated_at=now)
        uow.repository.add(plan); uow.repository.flush()
        uow.repository.append_revision(plan=plan, actor_id=actor.actor_id, rationale=data.rationale, now=now)
        return ExecutionPlanMutationSuccess(project_id=project.id, plan_id=plan.id, plan_version=1)

    def _create_activity(self, uow, project, plan, now, data, actor):
        if plan is None: return ExecutionPlanInvalidResult()
        if plan.version != data.expected_plan_version: return ExecutionPlanVersionConflictResult()
        activities, _, _ = uow.repository.load_plan_children(plan_id=plan.id, organization_id=actor.organization_id)
        if len(activities) >= 200 or data.ordinal > len(activities) or any(row.title.casefold() == data.title.casefold() for row in activities): return ExecutionPlanInvalidResult()
        if not self.authorization.validate_workspace(actor=actor, project=project, workspace_id=data.workspace_id) or not self.authorization.validate_responsible_user(project=project, user_id=data.responsible_user_id): return ExecutionPlanInvalidResult()
        for row in reversed(activities):
            if row.ordinal >= data.ordinal:
                previous = row.standing; row.ordinal += 1; row.version += 1; row.updated_by_id=actor.actor_id; row.updated_at=now
                uow.repository.add(EngineeringExecutionActivityHistory(id=uuid4(), activity_id=row.id, plan_id=plan.id, organization_id=actor.organization_id, from_standing=previous, to_standing=previous, activity_version=row.version, rationale=data.rationale, actor_id=actor.actor_id, transitioned_at=now))
        activity = EngineeringExecutionActivity(id=uuid4(), plan_id=plan.id, project_id=project.id, organization_id=actor.organization_id,
            title=data.title, description=data.description, ordinal=data.ordinal, workspace_id=data.workspace_id,
            responsible_user_id=data.responsible_user_id, target_date=data.target_date, completion_basis=data.completion_basis,
            standing="planned", version=1, created_by_id=actor.actor_id, created_at=now, updated_by_id=actor.actor_id, updated_at=now)
        uow.repository.add(activity); uow.repository.flush()
        uow.repository.add(EngineeringExecutionActivityHistory(id=uuid4(), activity_id=activity.id, plan_id=plan.id, organization_id=actor.organization_id, from_standing=None, to_standing="planned", activity_version=1, rationale=data.rationale, actor_id=actor.actor_id, transitioned_at=now))
        plan.version += 1; plan.updated_by_id=actor.actor_id; plan.updated_at=now
        uow.repository.flush(); uow.repository.append_revision(plan=plan, actor_id=actor.actor_id, rationale=data.rationale, now=now)
        return ExecutionPlanMutationSuccess(project_id=project.id, plan_id=plan.id, plan_version=plan.version, activity_id=activity.id, activity_version=1, standing="planned")

    def _update_activity(self, uow, project, plan, activity_id, data, actor, now):
        if plan is None or plan.version != data.expected_plan_version: return ExecutionPlanVersionConflictResult()
        activity = uow.repository.get_activity(activity_id=activity_id, plan_id=plan.id, organization_id=actor.organization_id, lock=True)
        if activity is None: return ExecutionPlanProtectedResult()
        if activity.version != data.expected_activity_version: return ExecutionPlanVersionConflictResult()
        if activity.standing in {"completed", "cancelled"}: return ExecutionPlanInvalidResult()
        activities, _, _ = uow.repository.load_plan_children(plan_id=plan.id, organization_id=actor.organization_id)
        if data.ordinal >= len(activities) or any(row.id != activity.id and row.title.casefold() == data.title.casefold() for row in activities): return ExecutionPlanInvalidResult()
        if not self.authorization.validate_workspace(actor=actor, project=project, workspace_id=data.workspace_id) or not self.authorization.validate_responsible_user(project=project, user_id=data.responsible_user_id): return ExecutionPlanInvalidResult()
        ordered = [row for row in activities if row.id != activity.id]; ordered.insert(data.ordinal, activity)
        changed = []
        for ordinal, row in enumerate(ordered):
            if row.ordinal != ordinal or row.id == activity.id:
                row.ordinal = ordinal; row.version += 1; row.updated_by_id=actor.actor_id; row.updated_at=now; changed.append(row)
        activity.title, activity.description, activity.workspace_id, activity.responsible_user_id, activity.target_date, activity.completion_basis = data.title, data.description, data.workspace_id, data.responsible_user_id, data.target_date, data.completion_basis
        for row in changed:
            uow.repository.add(EngineeringExecutionActivityHistory(id=uuid4(), activity_id=row.id, plan_id=plan.id, organization_id=actor.organization_id, from_standing=row.standing, to_standing=row.standing, activity_version=row.version, rationale=data.rationale, actor_id=actor.actor_id, transitioned_at=now))
        plan.version += 1; plan.updated_by_id=actor.actor_id; plan.updated_at=now
        uow.repository.flush(); uow.repository.append_revision(plan=plan, actor_id=actor.actor_id, rationale=data.rationale, now=now)
        return ExecutionPlanMutationSuccess(project_id=project.id, plan_id=plan.id, plan_version=plan.version, activity_id=activity.id, activity_version=activity.version, standing=activity.standing)

    def _transition_activity(self, uow, project, plan, activity_id, data, actor, now):
        if plan is None: return ExecutionPlanInvalidResult()
        activity = uow.repository.get_activity(activity_id=activity_id, plan_id=plan.id, organization_id=actor.organization_id, lock=True)
        if activity is None: return ExecutionPlanProtectedResult()
        if activity.version != data.expected_activity_version: return ExecutionPlanVersionConflictResult()
        target = data.target_standing
        if not valid_activity_transition(ExecutionActivityStanding(activity.standing), target): return ExecutionPlanInvalidResult()
        if activity.standing == "blocked" and target.value not in {activity.blocked_return_standing, "cancelled"}: return ExecutionPlanInvalidResult()
        if target.value in {"ready", "in_progress", "completed"} and self._dependencies_unresolved(uow, activity): return ExecutionPlanInvalidResult()
        previous = activity.standing
        if target is ExecutionActivityStanding.BLOCKED:
            activity.blocked_return_standing = previous; activity.blocker_rationale = data.rationale
        else:
            activity.blocked_return_standing = None; activity.blocker_rationale = None
        if target is ExecutionActivityStanding.COMPLETED: activity.completion_rationale = data.rationale
        activity.standing = target.value; activity.version += 1; activity.updated_by_id=actor.actor_id; activity.updated_at=now
        uow.repository.add(EngineeringExecutionActivityHistory(id=uuid4(), activity_id=activity.id, plan_id=plan.id, organization_id=actor.organization_id, from_standing=previous, to_standing=target.value, activity_version=activity.version, rationale=data.rationale, actor_id=actor.actor_id, transitioned_at=now))
        return ExecutionPlanMutationSuccess(project_id=project.id, plan_id=plan.id, plan_version=plan.version, activity_id=activity.id, activity_version=activity.version, standing=target)

    def _replace_dependencies(self, uow, project, plan, now, data, actor):
        if plan is None or plan.version != data.expected_plan_version: return ExecutionPlanVersionConflictResult()
        activities, _, _ = uow.repository.load_plan_children(plan_id=plan.id, organization_id=actor.organization_id)
        ids = {row.id for row in activities}
        edges = tuple((edge.predecessor_activity_id, edge.dependent_activity_id) for edge in data.dependencies)
        if any(left not in ids or right not in ids for left, right in edges) or self._has_cycle(edges): return ExecutionPlanInvalidResult()
        uow.repository.replace_dependencies(plan_id=plan.id, organization_id=actor.organization_id, edges=edges)
        plan.version += 1; plan.updated_by_id=actor.actor_id; plan.updated_at=now; uow.repository.flush(); uow.repository.append_revision(plan=plan, actor_id=actor.actor_id, rationale=data.rationale, now=now)
        return ExecutionPlanMutationSuccess(project_id=project.id, plan_id=plan.id, plan_version=plan.version)

    def _create_milestone(self, uow, project, plan, now, data, actor):
        if plan is None or plan.version != data.expected_plan_version: return ExecutionPlanVersionConflictResult()
        activities, milestones, _ = uow.repository.load_plan_children(plan_id=plan.id, organization_id=actor.organization_id)
        if len(milestones) >= 50 or data.ordinal > len(milestones) or any(row.title.casefold() == data.title.casefold() for row in milestones) or not set(data.activity_ids) <= {row.id for row in activities}: return ExecutionPlanInvalidResult()
        for row in reversed(milestones):
            if row.ordinal >= data.ordinal: row.ordinal += 1
        milestone = EngineeringExecutionMilestone(id=uuid4(), plan_id=plan.id, project_id=project.id, organization_id=actor.organization_id, title=data.title, completion_basis=data.completion_basis, target_date=data.target_date, ordinal=data.ordinal, created_by_id=actor.actor_id, created_at=now, updated_by_id=actor.actor_id, updated_at=now)
        uow.repository.add(milestone); uow.repository.flush(); uow.repository.replace_milestone_links(milestone_id=milestone.id, organization_id=actor.organization_id, activity_ids=data.activity_ids)
        plan.version += 1; plan.updated_by_id=actor.actor_id; plan.updated_at=now; uow.repository.flush(); uow.repository.append_revision(plan=plan, actor_id=actor.actor_id, rationale=data.rationale, now=now)
        return ExecutionPlanMutationSuccess(project_id=project.id, plan_id=plan.id, plan_version=plan.version, milestone_id=milestone.id)

    def _update_milestone(self, uow, project, plan, milestone_id, data, actor, now):
        if plan is None or plan.version != data.expected_plan_version: return ExecutionPlanVersionConflictResult()
        _, milestones, _ = uow.repository.load_plan_children(plan_id=plan.id, organization_id=actor.organization_id)
        milestone = next((row for row in milestones if row.id == milestone_id), None)
        activities, _, _ = uow.repository.load_plan_children(plan_id=plan.id, organization_id=actor.organization_id)
        if milestone is None: return ExecutionPlanProtectedResult()
        if data.ordinal >= len(milestones) or any(row.id != milestone.id and row.title.casefold() == data.title.casefold() for row in milestones) or not set(data.activity_ids) <= {row.id for row in activities}: return ExecutionPlanInvalidResult()
        ordered = [row for row in milestones if row.id != milestone.id]; ordered.insert(data.ordinal, milestone)
        for ordinal, row in enumerate(ordered): row.ordinal = ordinal
        milestone.title, milestone.completion_basis, milestone.target_date = data.title, data.completion_basis, data.target_date; milestone.updated_by_id=actor.actor_id; milestone.updated_at=now
        uow.repository.replace_milestone_links(milestone_id=milestone.id, organization_id=actor.organization_id, activity_ids=data.activity_ids)
        plan.version += 1; plan.updated_by_id=actor.actor_id; plan.updated_at=now; uow.repository.flush(); uow.repository.append_revision(plan=plan, actor_id=actor.actor_id, rationale=data.rationale, now=now)
        return ExecutionPlanMutationSuccess(project_id=project.id, plan_id=plan.id, plan_version=plan.version, milestone_id=milestone.id)

    @staticmethod
    def _has_cycle(edges):
        adjacency = {}
        for predecessor, dependent in edges: adjacency.setdefault(predecessor, set()).add(dependent)
        visiting, visited = set(), set()
        def visit(node):
            if node in visiting: return True
            if node in visited: return False
            visiting.add(node); result = any(visit(child) for child in adjacency.get(node, ())); visiting.remove(node); visited.add(node); return result
        return any(visit(node) for node in adjacency)

    @staticmethod
    def _dependencies_unresolved(uow, activity):
        _, _, dependencies = uow.repository.load_plan_children(plan_id=activity.plan_id, organization_id=activity.organization_id)
        predecessors = {edge.predecessor_activity_id for edge in dependencies if edge.dependent_activity_id == activity.id}
        activities, _, _ = uow.repository.load_plan_children(plan_id=activity.plan_id, organization_id=activity.organization_id)
        return any(row.id in predecessors and row.standing not in {"completed", "cancelled"} for row in activities)

    def _mutable(self, actor, project):
        return self.authorization.can_mutate(actor=actor, project=project) and project.status not in {"completed", "cancelled"}

    def _read(self, plan, activities, milestones, dependencies):
        activity_dtos = tuple(ExecutionActivityDTO(id=row.id, title=row.title, description=row.description, ordinal=row.ordinal, workspace_id=row.workspace_id, responsible_user_id=row.responsible_user_id, target_date=row.target_date, completion_basis=row.completion_basis, standing=row.standing, version=row.version, blocker_rationale=row.blocker_rationale, updated_at=row.updated_at) for row in activities)
        standings = {row.id: row.standing for row in activities}
        milestone_dtos = tuple(ExecutionMilestoneDTO(id=row.id, title=row.title, completion_basis=row.completion_basis, target_date=row.target_date, ordinal=row.ordinal, activity_ids=tuple(link.activity_id for link in row.links), standing=("achieved" if row.links and all(standings.get(link.activity_id) == "completed" for link in row.links) else "blocked" if any(standings.get(link.activity_id) == "blocked" for link in row.links) else "not_ready")) for row in milestones)
        eligible = [row for row in activities if row.standing != "cancelled"]; completed = [row for row in eligible if row.standing == "completed"]
        return ExecutionPlanEstablished(project_id=plan.project_id, plan_id=plan.id, version=plan.version, activities=activity_dtos, milestones=milestone_dtos, dependencies=tuple(ExecutionDependencyDTO(predecessor_activity_id=row.predecessor_activity_id, dependent_activity_id=row.dependent_activity_id) for row in dependencies), progress=ExecutionProgressDTO(completed_count=len(completed), eligible_count=len(eligible), percent=0 if not eligible else (100 * len(completed)) // len(eligible)))

    @staticmethod
    def _fingerprint(operation, project_id, actor, data):
        raw = json.dumps({"operation": operation, "project_id": project_id, "organization_id": str(actor.organization_id), "body": data.model_dump(mode="json")}, sort_keys=True, separators=(",", ":")).encode()
        return sha256(raw).hexdigest()

    @staticmethod
    def _audit(uow, actor, project_id, operation, version):
        uow.stage_audit(actor_id=actor.actor_id, project_id=project_id, operation="EXECUTION_PLAN", details={"operation": operation, "version": version, "changed_categories": ["execution_plan"]})
