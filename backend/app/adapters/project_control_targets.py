"""Canonical application-boundary target resolution for PATCH-047 Change Impact."""
from dataclasses import dataclass

from app.models.supporting_file_command import SupportingFileScope
from app.schemas.engineering_deliverable import DeliverableActor
from app.schemas.engineering_execution_plan import ExecutionActor


class TargetProtected(Exception):
    """The target is missing, denied, malformed, or outside the trusted scope."""


class TargetUnavailable(Exception):
    """A canonical target dependency could not complete safely."""


class TargetInvalid(Exception):
    """The supplied target discriminator is outside the closed V1 contract."""


@dataclass(frozen=True)
class ResolvedChangeImpactTarget:
    kind: str
    target_id: object
    project_id: int
    workspace_id: int | None


class CanonicalProjectControlTargetAdapter:
    """Dispatches only through owning application services; never persistence."""

    _supported = frozenset({"activity", "milestone", "deliverable", "deliverable_revision", "evidence", "supporting_file"})

    def __init__(self, *, execution, deliverables, evidence, supporting_files):
        self.execution = execution
        self.deliverables = deliverables
        self.evidence = evidence
        self.supporting_files = supporting_files

    def authorize_exact(self, *, actor, project_id, workspace_id, target_kind, target_id, deliverable_id=None):
        kind = getattr(target_kind, "value", target_kind)
        if kind not in self._supported:
            raise TargetInvalid()
        try:
            if kind in {"activity", "milestone"}:
                return self._execution(actor=actor, project_id=project_id, workspace_id=workspace_id, kind=kind, target_id=target_id)
            if kind == "deliverable":
                return self._deliverable(actor=actor, project_id=project_id, workspace_id=workspace_id, target_id=target_id)
            if kind == "deliverable_revision":
                return self._revision(actor=actor, project_id=project_id, workspace_id=workspace_id, target_id=target_id, deliverable_id=deliverable_id)
            if kind == "evidence":
                return self._evidence(actor=actor, project_id=project_id, workspace_id=workspace_id, target_id=target_id)
            return self._supporting_file(actor=actor, project_id=project_id, workspace_id=workspace_id, target_id=target_id)
        except TargetProtected:
            raise
        except TargetUnavailable:
            raise
        except Exception as error:  # Canonical exceptions never cross the control boundary.
            name = error.__class__.__name__.lower()
            if "unavailable" in name or "integrity" in name or "sql" in name:
                raise TargetUnavailable() from error
            raise TargetProtected() from error

    @staticmethod
    def _workspace_compatible(expected, actual):
        return actual is None or actual == expected

    def _execution(self, *, actor, project_id, workspace_id, kind, target_id):
        result = self.execution.get(project_id=project_id, actor=ExecutionActor(actor_id=actor.actor_id, organization_id=actor.organization_id))
        outcome = getattr(result, "outcome", None)
        if outcome == "unavailable": raise TargetUnavailable()
        if getattr(result, "availability", None) != "established" or getattr(result, "project_id", None) != project_id: raise TargetProtected()
        values = getattr(result, "activities", ()) if kind == "activity" else getattr(result, "milestones", ())
        matches = tuple(value for value in values if getattr(value, "id", None) == target_id and self._workspace_compatible(workspace_id, getattr(value, "workspace_id", None)))
        if len(matches) != 1: raise TargetProtected()
        return ResolvedChangeImpactTarget(kind=kind, target_id=target_id, project_id=project_id, workspace_id=getattr(matches[0], "workspace_id", None))

    def _deliverable(self, *, actor, project_id, workspace_id, target_id):
        result = self.deliverables.get(project_id=project_id, deliverable_id=target_id, actor=DeliverableActor(actor_id=actor.actor_id, organization_id=actor.organization_id))
        outcome = getattr(result, "outcome", None)
        if outcome == "unavailable": raise TargetUnavailable()
        if outcome is not None or getattr(result, "id", None) != target_id or getattr(result, "project_id", None) != project_id or not self._workspace_compatible(workspace_id, getattr(result, "workspace_id", None)): raise TargetProtected()
        return ResolvedChangeImpactTarget(kind="deliverable", target_id=target_id, project_id=project_id, workspace_id=getattr(result, "workspace_id", None))

    def _revision(self, *, actor, project_id, workspace_id, target_id, deliverable_id):
        if deliverable_id is None: raise TargetProtected()
        result = self.deliverables.history(project_id=project_id, deliverable_id=deliverable_id, actor=DeliverableActor(actor_id=actor.actor_id, organization_id=actor.organization_id))
        outcome = getattr(result, "outcome", None)
        if outcome == "unavailable": raise TargetUnavailable()
        if outcome != "success": raise TargetProtected()
        matches = tuple(item for item in getattr(result, "items", ()) if getattr(item, "id", None) == deliverable_id and getattr(getattr(item, "current_revision", None), "id", None) == target_id and getattr(item, "project_id", None) == project_id and self._workspace_compatible(workspace_id, getattr(item, "workspace_id", None)))
        if len(matches) != 1: raise TargetProtected()
        return ResolvedChangeImpactTarget(kind="deliverable_revision", target_id=target_id, project_id=project_id, workspace_id=getattr(matches[0], "workspace_id", None))

    def _evidence(self, *, actor, project_id, workspace_id, target_id):
        result = self.evidence.get(target_id, actor)
        if getattr(result, "id", None) != target_id or getattr(result, "organization_id", None) != actor.organization_id or getattr(result, "project_id", None) != project_id or not self._workspace_compatible(workspace_id, getattr(result, "workspace_id", None)): raise TargetProtected()
        return ResolvedChangeImpactTarget(kind="evidence", target_id=target_id, project_id=project_id, workspace_id=getattr(result, "workspace_id", None))

    def _supporting_file(self, *, actor, project_id, workspace_id, target_id):
        scope = SupportingFileScope(actor.organization_id, project_id, workspace_id)
        result = self.supporting_files.get_metadata(actor_id=actor.actor_id, scope=scope, asset_id=target_id)
        if getattr(result, "id", None) != target_id or getattr(result, "organization_id", None) != actor.organization_id or getattr(result, "project_id", None) != project_id or not self._workspace_compatible(workspace_id, getattr(result, "workspace_id", None)): raise TargetProtected()
        return ResolvedChangeImpactTarget(kind="supporting_file", target_id=target_id, project_id=project_id, workspace_id=getattr(result, "workspace_id", None))
