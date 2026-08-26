from hashlib import sha256
import json
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.engineering_execution_plan import (
    EngineeringExecutionActivity, EngineeringExecutionDependency,
    EngineeringExecutionIdempotency,
    EngineeringExecutionMilestone, EngineeringExecutionMilestoneActivity,
    EngineeringExecutionPlan, EngineeringExecutionPlanRevision,
)


def canonical_plan_config(*, activities, milestones, dependency_edges) -> tuple[dict, str]:
    payload = {
        "schema": "execution.plan.config.v1",
        "activities": [
            {"id": str(row.id), "title": row.title, "description": row.description,
             "ordinal": row.ordinal, "workspace_id": row.workspace_id,
             "responsible_user_id": row.responsible_user_id,
             "target_date": row.target_date.isoformat() if row.target_date else None,
             "completion_basis": row.completion_basis}
            for row in sorted(activities, key=lambda item: (item.ordinal, str(item.id)))
        ],
        "milestones": [
            {"id": str(row.id), "title": row.title, "completion_basis": row.completion_basis,
             "ordinal": row.ordinal, "target_date": row.target_date.isoformat() if row.target_date else None,
             "activity_ids": [str(link.activity_id) for link in sorted(row.links, key=lambda link: link.ordinal)]}
            for row in sorted(milestones, key=lambda item: (item.ordinal, str(item.id)))
        ],
        "dependencies": [
            {"predecessor_activity_id": str(row.predecessor_activity_id), "dependent_activity_id": str(row.dependent_activity_id)}
            for row in sorted(dependency_edges, key=lambda item: (str(item.predecessor_activity_id), str(item.dependent_activity_id)))
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return payload, sha256(encoded).hexdigest()


class EngineeringExecutionPlanRepository:
    """No-commit persistence for the Project-subordinate execution plan."""
    def __init__(self, session: Session): self.session = session

    def get_plan(self, *, project_id: int, organization_id: UUID, lock: bool = False):
        query = self.session.query(EngineeringExecutionPlan).filter_by(project_id=project_id, organization_id=organization_id)
        return (query.with_for_update() if lock else query).first()

    def get_activity(self, *, activity_id: UUID, plan_id: UUID, organization_id: UUID, lock: bool = False):
        query = self.session.query(EngineeringExecutionActivity).filter_by(id=activity_id, plan_id=plan_id, organization_id=organization_id)
        return (query.with_for_update() if lock else query).first()

    def get_milestone(self, *, milestone_id: UUID, plan_id: UUID, organization_id: UUID, lock: bool = False):
        query = self.session.query(EngineeringExecutionMilestone).filter_by(id=milestone_id, plan_id=plan_id, organization_id=organization_id)
        return (query.with_for_update() if lock else query).first()

    def get_milestone_activity_standings(self, *, milestone_id: UUID, organization_id: UUID) -> tuple[str, ...]:
        """Only the exact milestone's linked activity standings; never plan scan."""
        rows = (self.session.query(EngineeringExecutionActivity.standing)
                .join(EngineeringExecutionMilestoneActivity, EngineeringExecutionMilestoneActivity.activity_id == EngineeringExecutionActivity.id)
                .filter(EngineeringExecutionMilestoneActivity.milestone_id == milestone_id,
                        EngineeringExecutionMilestoneActivity.organization_id == organization_id,
                        EngineeringExecutionActivity.organization_id == organization_id)
                .order_by(EngineeringExecutionMilestoneActivity.ordinal, EngineeringExecutionActivity.id).all())
        return tuple(row[0] for row in rows)

    def list_graph_incident(self, *, selector_kind: str, selector_id: UUID,
                            project_id: int, organization_id: UUID, limit: int = 91):
        """Exact indexed incident read; never scans a serialized plan aggregate."""
        plan = self.get_plan(project_id=project_id, organization_id=organization_id)
        if plan is None or selector_kind not in {"execution_plan", "activity", "milestone"}:
            return (), False
        rows: list[tuple[str, str, UUID, str, UUID, int]] = []
        if selector_kind == "execution_plan":
            if selector_id != plan.id:
                return (), False
            activities = (self.session.query(EngineeringExecutionActivity)
                          .filter_by(plan_id=plan.id, organization_id=organization_id)
                          .order_by(EngineeringExecutionActivity.id).limit(limit + 1).all())
            rows.extend(("plan_activity", "execution_plan", plan.id, "activity", item.id, plan.version)
                        for item in activities)
            remaining = max(0, limit + 1 - len(rows))
            if remaining:
                milestones = (self.session.query(EngineeringExecutionMilestone)
                              .filter_by(plan_id=plan.id, organization_id=organization_id)
                              .order_by(EngineeringExecutionMilestone.id).limit(remaining).all())
                rows.extend(("plan_milestone", "execution_plan", plan.id, "milestone", item.id, plan.version)
                            for item in milestones)
        elif selector_kind == "activity":
            activity = self.get_activity(activity_id=selector_id, plan_id=plan.id, organization_id=organization_id)
            if activity is None:
                return (), False
            rows.append(("plan_activity", "execution_plan", plan.id, "activity", activity.id, plan.version))
            dependencies = (self.session.query(EngineeringExecutionDependency)
                            .filter(EngineeringExecutionDependency.organization_id == organization_id,
                                    EngineeringExecutionDependency.plan_id == plan.id,
                                    ((EngineeringExecutionDependency.predecessor_activity_id == activity.id) |
                                     (EngineeringExecutionDependency.dependent_activity_id == activity.id)))
                            .order_by(EngineeringExecutionDependency.predecessor_activity_id,
                                      EngineeringExecutionDependency.dependent_activity_id)
                            .limit(limit + 1).all())
            rows.extend(("activity_dependency", "activity", item.predecessor_activity_id,
                         "activity", item.dependent_activity_id, plan.version) for item in dependencies)
            links = (self.session.query(EngineeringExecutionMilestoneActivity)
                     .filter_by(activity_id=activity.id, organization_id=organization_id)
                     .order_by(EngineeringExecutionMilestoneActivity.milestone_id).limit(limit + 1).all())
            rows.extend(("milestone_activity", "milestone", item.milestone_id,
                         "activity", activity.id, plan.version) for item in links)
        else:
            milestone = self.get_milestone(milestone_id=selector_id, plan_id=plan.id, organization_id=organization_id)
            if milestone is None:
                return (), False
            rows.append(("plan_milestone", "execution_plan", plan.id, "milestone", milestone.id, plan.version))
            links = (self.session.query(EngineeringExecutionMilestoneActivity)
                     .filter_by(milestone_id=milestone.id, organization_id=organization_id)
                     .order_by(EngineeringExecutionMilestoneActivity.ordinal,
                               EngineeringExecutionMilestoneActivity.activity_id)
                     .limit(limit + 1).all())
            rows.extend(("milestone_activity", "milestone", milestone.id,
                         "activity", item.activity_id, plan.version) for item in links)
        ordered = sorted(set(rows), key=lambda item: (item[0], str(item[2]), str(item[4])))
        return tuple(ordered[:limit]), len(ordered) > limit

    def load_plan_children(self, *, plan_id: UUID, organization_id: UUID):
        activities = self.session.query(EngineeringExecutionActivity).filter_by(plan_id=plan_id, organization_id=organization_id).order_by(EngineeringExecutionActivity.ordinal, EngineeringExecutionActivity.id).all()
        milestones = self.session.query(EngineeringExecutionMilestone).filter_by(plan_id=plan_id, organization_id=organization_id).order_by(EngineeringExecutionMilestone.ordinal, EngineeringExecutionMilestone.id).all()
        for milestone in milestones:
            milestone.links = self.session.query(EngineeringExecutionMilestoneActivity).filter_by(milestone_id=milestone.id, organization_id=organization_id).order_by(EngineeringExecutionMilestoneActivity.ordinal).all()
        dependencies = self.session.query(EngineeringExecutionDependency).filter_by(plan_id=plan_id, organization_id=organization_id).order_by(EngineeringExecutionDependency.predecessor_activity_id, EngineeringExecutionDependency.dependent_activity_id).all()
        return activities, milestones, dependencies

    def append_revision(self, *, plan, actor_id: int, rationale: str, now) -> EngineeringExecutionPlanRevision:
        activities, milestones, dependencies = self.load_plan_children(plan_id=plan.id, organization_id=plan.organization_id)
        config, digest = canonical_plan_config(activities=activities, milestones=milestones, dependency_edges=dependencies)
        revision = EngineeringExecutionPlanRevision(plan_id=plan.id, organization_id=plan.organization_id,
            revision_number=plan.version, config_json=config, config_digest=digest,
            rationale=rationale, actor_id=actor_id, created_at=now)
        self.session.add(revision)
        return revision

    def get_idempotency(self, *, organization_id, actor_id: int, operation: str, idempotency_key, lock: bool = True):
        query = self.session.query(EngineeringExecutionIdempotency).filter_by(
            organization_id=organization_id, actor_id=actor_id,
            operation=operation, idempotency_key=idempotency_key,
        )
        return (query.with_for_update() if lock else query).first()

    def replace_dependencies(self, *, plan_id, organization_id, edges):
        self.session.query(EngineeringExecutionDependency).filter_by(plan_id=plan_id, organization_id=organization_id).delete(synchronize_session=False)
        for predecessor, dependent in edges:
            self.session.add(EngineeringExecutionDependency(
                plan_id=plan_id, organization_id=organization_id,
                predecessor_activity_id=predecessor, dependent_activity_id=dependent,
            ))

    def replace_milestone_links(self, *, milestone_id, organization_id, activity_ids):
        self.session.query(EngineeringExecutionMilestoneActivity).filter_by(milestone_id=milestone_id, organization_id=organization_id).delete(synchronize_session=False)
        for ordinal, activity_id in enumerate(activity_ids):
            self.session.add(EngineeringExecutionMilestoneActivity(
                milestone_id=milestone_id, activity_id=activity_id,
                organization_id=organization_id, ordinal=ordinal,
            ))

    def add(self, item: object) -> None: self.session.add(item)
    def flush(self) -> None: self.session.flush()
