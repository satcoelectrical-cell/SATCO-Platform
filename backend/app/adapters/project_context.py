"""Narrow Project Context adapters over public canonical service boundaries."""
from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.schemas.project_context import (
    AuthorityClassification, FactProvenance, OwnerPage, OwnerProtected,
    GraphNodeResolved, OwnerInvalid, OwnerReadResult, OwnerResolved, OwnerUnavailable, ProjectContextActor,
    ProjectContextScope, SectionPageRequest, ProjectBasisItem, ExecutionPlanItem,
    DeliverableItem, ProjectControlItem, EngineeringObjectItem, EvidenceItem,
    SupportingFileItem, TechnicalReportItem, OrganizationalMemoryItem,
    TemporalClassification,
)


def _scalar(value: Any) -> Any:
    return getattr(value, "value", value)


def _values(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        return {field.name: getattr(value, field.name) for field in fields(value)}
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="python")
    if isinstance(value, dict):
        return value
    return vars(value) if hasattr(value, "__dict__") else {}


def _item(owner: str, value: Any) -> object:
    data = _values(value)
    identifier = next((data.get(key) for key in ("id", "report_id", "memory_id", "asset_id", "object_id", "evidence_id", "deliverable_id", "control_id", "plan_id", "project_id") if data.get(key) is not None), None)
    if identifier is None:
        raise ValueError("canonical owner response has no safe identity")
    observed = datetime.now(timezone.utc)
    label = next((data.get(key) for key in ("title", "name", "code", "filename", "purpose") if isinstance(data.get(key), str)), None)
    version = next((data.get(key) for key in ("version", "plan_version", "accepted_aggregate_version") if type(data.get(key)) is int and data.get(key) > 0), None)
    standing = next((data.get(key) for key in ("standing", "lifecycle", "status") if data.get(key) is not None), None)
    common = dict(selector=str(identifier), version=version, standing=str(standing) if standing is not None else None,
        provenance=FactProvenance(owner_kind=owner, selector=str(identifier), version=version,
            standing=str(standing) if standing is not None else None,
            source_observed_at=data.get("updated_at") if isinstance(data.get("updated_at"), datetime) else None,
            observed_at=observed, authority_class=AuthorityClassification.HUMAN_AUTHORITATIVE,
            temporal_class=TemporalClassification.CURRENT))
    project_id = data.get("project_id")
    if owner == "project_basis":
        readiness = data.get("next_stage_readiness")
        readiness_value = _values(readiness).get("state") if readiness is not None else data.get("readiness")
        return ProjectBasisItem(**common, project_id=project_id if type(project_id) is int and project_id > 0 else int(identifier), project_code=data.get("project_code"), project_name=data.get("project_name"), project_status=data.get("project_status"), foundation_established=True, foundation_version=version, purpose=data.get("purpose"), engineering_basis=data.get("engineering_basis"), current_stage=str(data.get("stage")) if data.get("stage") is not None else None, readiness=str(readiness_value) if readiness_value is not None else None, ordered_in_scope=tuple(str(item) for item in data.get("in_scope", ())), ordered_out_scope=tuple(str(item) for item in data.get("out_of_scope", ())), completion_basis=None, required_project_inputs=tuple(str(item) for item in data.get("inputs", ())))
    if owner == "execution":
        progress = data.get("progress")
        if not isinstance(progress, dict): raise ValueError("execution progress is required")
        from app.schemas.project_context import ExecutionProgressItem
        return ExecutionPlanItem(**common, plan_id=identifier, project_id=project_id, plan_version=version or 1,
            activities=tuple(data.get("activities", ())), milestones=tuple(data.get("milestones", ())),
            dependencies=tuple(data.get("dependencies", ())), progress=ExecutionProgressItem(**progress))
    if owner == "deliverable":
        from app.schemas.project_context import DeliverableRevisionItem
        revision=data.get("current_revision")
        return DeliverableItem(**common, deliverable_id=identifier, project_id=project_id, workspace_id=data.get("workspace_id"),
            code=data.get("code"), title=data.get("title"), discipline=data.get("discipline"), deliverable_type=data.get("deliverable_type"),
            purpose=data.get("purpose"), activity_ids=tuple(data.get("activity_ids", ())), milestone_ids=tuple(data.get("milestone_ids", ())),
            target_date=data.get("target_date"), external_authority=bool(data.get("external_authority")),
            current_revision=DeliverableRevisionItem(**revision) if isinstance(revision, dict) else None)
    if owner.startswith("project_control:"):
        return ProjectControlItem(**common, item_kind=owner, control_id=identifier, project_id=project_id, workspace_id=data.get("workspace_id"), temporal_class=TemporalClassification.HISTORICAL if data.get("standing") in {"superseded", "withdrawn"} else TemporalClassification.CURRENT, predecessor_present=bool(data.get("predecessor_id")))
    if owner == "engineering_object":
        return EngineeringObjectItem(**common, object_id=identifier, organization_id=data.get("organization_id"), project_id=project_id, workspace_id=data.get("workspace_id"), family=data.get("family"), discipline=data.get("discipline"), object_type=data.get("object_type"), object_subtype=data.get("object_subtype"), lifecycle=data.get("lifecycle"), authority_standing=data.get("authority_standing"), created_at=data.get("created_at"), updated_at=data.get("updated_at"))
    if owner == "evidence":
        return EvidenceItem(**common, evidence_id=identifier, project_id=project_id, workspace_id=data.get("workspace_id"), evidence_kind=data.get("evidence_kind") or data.get("source_kind"), safe_source_reference=data.get("safe_source_reference"), created_at=data.get("created_at"), updated_at=data.get("updated_at"))
    if owner == "supporting_file":
        return SupportingFileItem(**common, asset_id=identifier, project_id=project_id, workspace_id=data.get("workspace_id"), filename=data.get("filename"), media_type=data.get("media_type"), byte_size=data.get("byte_size"), lifecycle=data.get("lifecycle"), created_at=data.get("created_at"), updated_at=data.get("updated_at"))
    if owner == "technical_report":
        accepted_version = data.get("version")
        accepted_at = data.get("accepted_at")
        purpose = data.get("purpose")
        if type(accepted_version) is not int or accepted_version < 1 or not isinstance(accepted_at, datetime) or not isinstance(purpose, str) or not purpose:
            raise ValueError("accepted report summary is not closed")
        report_common = {**common, "version": accepted_version, "standing": "accepted"}
        return TechnicalReportItem(
            **report_common, report_id=identifier, project_id=project_id,
            workspace_id=data.get("workspace_id"), report_type=purpose,
            title_or_purpose=purpose, accepted_version_id=accepted_version,
            accepted_digest=data.get("accepted_digest"), accepted_at=accepted_at,
        )
    if owner == "organizational_memory":
        return OrganizationalMemoryItem(**common, memory_id=identifier, project_id=project_id, workspace_id=data.get("workspace_id"), limitations_present=bool(data.get("limitations_present")), source_report_id=data.get("source_report_id"), source_report_version=data.get("source_report_version"), admitted_at=data.get("admitted_at"))
    raise ValueError("unsupported Project Context owner")


def _graph_common(*, kind, selector, data, actor, scope, owner, workspace_id=None):
    from app.schemas.project_context import NodeNavigation
    version = next((data.get(key) for key in ("version", "plan_version", "accepted_version_id") if type(data.get(key)) is int and data.get(key) > 0), None)
    standing = next((_scalar(data.get(key)) for key in ("standing", "lifecycle_status", "workspace_status", "lifecycle", "status") if data.get(key) is not None), None)
    observed = datetime.now(timezone.utc)
    source_time = next((data.get(key) for key in ("updated_at", "accepted_at", "admitted_at") if isinstance(data.get(key), datetime)), None)
    temporal = TemporalClassification.HISTORICAL if str(standing) in {"withdrawn", "superseded"} else TemporalClassification.CURRENT
    authority = AuthorityClassification.CANONICAL_EVIDENCE if kind in {"evidence", "supporting_file"} else AuthorityClassification.CONTEXTUAL_ADVISORY if kind == "engineering_context" and data.get("authority") == "assumption" else AuthorityClassification.HUMAN_AUTHORITATIVE
    provenance = FactProvenance(owner_kind=owner, selector=str(selector), version=version, standing=str(standing) if standing is not None else None, source_observed_at=source_time, observed_at=observed, authority_class=authority, temporal_class=temporal)
    return dict(navigation=NodeNavigation(project_id=scope.project_id, workspace_id=workspace_id), provenance=provenance, authority_class=authority, temporal_class=temporal)


def _graph_node(kind, response, *, actor, scope, owner):
    """Fixed closed projector over an already-authorized owner response."""
    from app.schemas.project_context import (
        ActivityNode, ChangeImpactNode, ChangeNode, DecisionNode, DeliverableNode,
        DeliverableRevisionNode, EngineeringContextNode, EngineeringObjectNode,
        EvidenceNode, ExecutionPlanNode, IssueNode, MilestoneNode,
        OrganizationalMemoryNode, ProjectNode, RiskNode, SupportingFileNode,
        TechnicalReportNode, WorkspaceNode,
    )
    data = _values(response)
    selector = next((data.get(key) for key in ("id", "project_id", "workspace_id", "plan_id", "memory_id", "report_id") if data.get(key) is not None), None)
    workspace_id = data.get("workspace_id") if type(data.get("workspace_id")) is int else None
    common = _graph_common(kind=kind, selector=selector, data=data, actor=actor, scope=scope, owner=owner, workspace_id=workspace_id)
    if kind == "project": return ProjectNode(selector=data["project_id"], project_code=str(data["project_code"]), project_name=str(data["project_name"]), lifecycle_status=str(_scalar(data["lifecycle_status"])), **common)
    if kind == "workspace": return WorkspaceNode(selector=data.get("workspace_id", data.get("id")), project_id=data["project_id"], discipline=str(_scalar(data["discipline"])), workspace_status=str(_scalar(data.get("workspace_status", data.get("status")))), **common)
    if kind == "execution_plan": return ExecutionPlanNode(selector=data["plan_id"], project_id=data["project_id"], plan_version=data.get("version", data.get("plan_version")), established_standing="established", **common)
    if kind == "activity": return ActivityNode(selector=data.get("id", data.get("activity_id")), plan_id=data["plan_id"], project_id=data["project_id"], workspace_id=workspace_id, title=data["title"], ordinal=data["ordinal"], standing=str(data["standing"]), version=data["version"], target_date=data.get("target_date"), blocker_present=bool(data.get("blocker_present", data.get("standing") == "blocked")), **common)
    if kind == "milestone": return MilestoneNode(selector=data.get("id", data.get("milestone_id")), plan_id=data["plan_id"], project_id=data["project_id"], title=data["title"], ordinal=data["ordinal"], standing=str(data["standing"]), target_date=data.get("target_date"), **common)
    if kind == "deliverable": return DeliverableNode(selector=data.get("id", data.get("deliverable_id")), project_id=data["project_id"], workspace_id=workspace_id, code=data["code"], title=data["title"], discipline=str(_scalar(data["discipline"])), deliverable_type=str(_scalar(data["deliverable_type"])), standing=str(_scalar(data["standing"])), version=data["version"], external_authority=str(_scalar(data["external_authority"])) != "satco", target_date=data.get("target_date"), **common)
    if kind == "deliverable_revision": return DeliverableRevisionNode(selector=data["id"], deliverable_id=data["deliverable_id"], sequence=data["sequence"], external_label=data.get("external_label"), standing=str(data["standing"]), version=data["version"], representation_available=bool(data["representation_available"]), **common)
    if kind == "risk": return RiskNode(selector=data["id"], project_id=data["project_id"], workspace_id=workspace_id, category=data["category"], likelihood=str(_scalar(data["likelihood"])), impact=str(_scalar(data["impact"])), standing=str(_scalar(data["standing"])), version=data["version"], **common)
    if kind == "issue": return IssueNode(selector=data["id"], project_id=data["project_id"], workspace_id=workspace_id, severity=str(_scalar(data["severity"])), standing=str(_scalar(data["standing"])), version=data["version"], **common)
    if kind == "human_decision": return DecisionNode(selector=data["id"], project_id=data["project_id"], workspace_id=workspace_id, standing=str(data["standing"]), version=data["version"], predecessor_present=data.get("predecessor_id") is not None, **common)
    if kind == "change": return ChangeNode(selector=data["id"], project_id=data["project_id"], workspace_id=workspace_id, standing=str(data["standing"]), version=data["version"], predecessor_present=data.get("predecessor_id") is not None, **common)
    if kind == "change_impact": return ChangeImpactNode(selector=data["id"], change_id=data["change_id"], target_kind=str(_scalar(data["target_kind"])) if data.get("target_kind") is not None else None, standing=str(_scalar(data["standing"])), impact_class=str(_scalar(data["impact_class"])), **common)
    if kind == "engineering_object": return EngineeringObjectNode(selector=data["id"], organization_id=data["organization_id"], project_id=data["project_id"], workspace_id=workspace_id, family=str(data["family"]), discipline=str(data["discipline"]), object_type=str(data["object_type"]), object_subtype=data.get("subtype", data.get("object_subtype")), lifecycle=str(data["lifecycle"]), authority_standing=str(data["authority_standing"]), version=data["version"], created_at=data["created_at"], updated_at=data["updated_at"], **common)
    if kind == "engineering_context": return EngineeringContextNode(selector=data.get("context_id", data.get("id")), project_id=data["project_id"], workspace_id=workspace_id, context_kind=str(data.get("kind", data.get("context_kind"))), authority=str(data["authority"]), lifecycle=str(data["lifecycle"]), version=data["version"], typed_payload_present=not isinstance(data.get("payload"), type(None)), **common)
    if kind == "evidence": return EvidenceNode(selector=data.get("id", data.get("evidence_id")), project_id=data["project_id"], workspace_id=workspace_id, evidence_kind=str(data.get("source_kind", data.get("evidence_kind"))), standing=str(data.get("source_standing", data.get("standing"))), version=data["version"], created_at=data["created_at"], updated_at=data["updated_at"], **common)
    if kind == "supporting_file": return SupportingFileNode(selector=data["id"], project_id=data["project_id"], workspace_id=workspace_id, filename=data.get("safe_filename", data.get("filename")), media_type=data["media_type"], byte_size=data["byte_size"], lifecycle=str(data["lifecycle"]), version=data["version"], created_at=data["created_at"], updated_at=data["updated_at"], **common)
    if kind == "technical_report": return TechnicalReportNode(selector=data["report_id"], project_id=data["project_id"], workspace_id=data["workspace_id"], report_type=str(data["purpose"]), title_or_purpose=str(data["purpose"]), accepted_version_id=data["version"], accepted_digest=data["accepted_digest"], accepted_at=data["accepted_at"], **common)
    if kind == "organizational_memory": return OrganizationalMemoryNode(selector=data["memory_id"], project_id=data["project_id"], workspace_id=data["workspace_id"], version=data["version"], limitations_present=bool(data.get("limitations_present")), admitted_at=data["admitted_at"], **common)
    raise ValueError("unsupported graph node")


def _graph_result(response, *, kind, actor, scope, owner):
    data = _values(response)
    status = data.get("status", data.get("outcome"))
    if status in {"protected", "protected_not_found", "not_found"}: return OwnerProtected()
    if status in {"unavailable", "error"}: return OwnerUnavailable()
    if status in {"invalid", "invalid_request"}: return OwnerInvalid()
    try: return GraphNodeResolved(item=_graph_node(kind, response, actor=actor, scope=scope, owner=owner))
    except Exception: return OwnerUnavailable()


class _CanonicalAdapter:
    def __init__(self, service: object, owner_actor: object, owner: str) -> None:
        self._service, self._owner_actor, self._owner = service, owner_actor, owner

    def _translate(self, response: object, *, actor: ProjectContextActor, page: SectionPageRequest, current_user: object) -> OwnerReadResult:
        if getattr(current_user, "id", None) != actor.actor_id:
            return OwnerProtected()
        try:
            data = _values(response)
            status = data.get("status", data.get("outcome"))
            if status in {"protected_not_found", "protected", "not_found"}: return OwnerProtected()
            if status in {"unavailable", "error"}: return OwnerUnavailable()
            values = data.get("items")
            if values is None:
                if status in {"not_established", "not_found"} or data.get("availability") == "not_established": return OwnerPage(items=(), last_evaluated_key=None, observed_at=datetime.now(timezone.utc))
                return OwnerResolved(item=_item(self._owner, response))
            if not isinstance(values, (list, tuple)) or len(values) > page.page_size: return OwnerUnavailable()
            items = tuple(_item(self._owner, value) for value in values)
            return OwnerPage(items=items, last_evaluated_key=items[-1].selector if items else None, observed_at=datetime.now(timezone.utc))
        except Exception:
            return OwnerUnavailable()


class ProjectBasisProjectContextAdapter(_CanonicalAdapter):
    def get_authorized_basis(self, *, actor, scope, page, current_user): return self._translate(self._service.get(project_id=scope.project_id, actor=self._owner_actor), actor=actor, page=page, current_user=current_user)
class ExecutionProjectContextAdapter(_CanonicalAdapter):
    def get_authorized_plan(self, *, actor, scope, page, current_user): return self._translate(self._service.get(project_id=scope.project_id, actor=self._owner_actor), actor=actor, page=page, current_user=current_user)
class DeliverableProjectContextAdapter(_CanonicalAdapter):
    def list_authorized_deliverables(self, *, actor, scope, page, current_user): return self._translate(self._service.list(project_id=scope.project_id, actor=self._owner_actor), actor=actor, page=page, current_user=current_user)
class EngineeringObjectProjectContextAdapter(_CanonicalAdapter):
    def list_authorized_objects(self, *, actor, scope, page, current_user):
        from app.schemas.engineering_object import EngineeringObjectFilter
        from app.models.engineering_object_command import AuthorizationContext
        return self._translate(self._service.list(project_id=scope.project_id, filters=EngineeringObjectFilter(workspace_id=scope.workspace_id), page=1, size=page.page_size, actor=self._owner_actor, context=AuthorizationContext(operation="ReadEngineeringObject", scope={"project_id": scope.project_id, "workspace_id": scope.workspace_id})), actor=actor, page=page, current_user=current_user)
class EvidenceProjectContextAdapter(_CanonicalAdapter):
    def list_authorized_current(self, *, actor, scope, page, current_user):
        from app.schemas.evidence import EvidenceFilter
        return self._translate(self._service.list(project_id=scope.project_id, filters=EvidenceFilter(workspace_id=scope.workspace_id), page=1, size=page.page_size, actor=self._owner_actor), actor=actor, page=page, current_user=current_user)
class SupportingFileProjectContextAdapter(_CanonicalAdapter):
    def list_authorized_available(self, *, actor, scope, page, current_user):
        from app.models.supporting_file_command import SupportingFileScope
        return self._translate(self._service.list_metadata(actor_id=self._owner_actor, scope=SupportingFileScope(actor.organization_id, scope.project_id, scope.workspace_id), lifecycle="available", limit=page.page_size, continuation=page.continuation), actor=actor, page=page, current_user=current_user)
class TechnicalReportProjectContextAdapter(_CanonicalAdapter):
    def list_authorized_accepted(self, *, actor, scope, page, current_user):
        from app.models.technical_report_command import TechnicalReportActor
        from app.ports.technical_report import TechnicalReportReadCriteria, TechnicalReportScope
        if scope.workspace_id is None: return OwnerUnavailable()
        return self._translate(self._service.list_accepted_summaries(TechnicalReportActor(actor.actor_id, actor.organization_id), TechnicalReportReadCriteria(TechnicalReportScope(actor.organization_id, scope.workspace_id, scope.project_id), 1, page.page_size)), actor=actor, page=page, current_user=current_user)
class OrganizationalMemoryProjectContextAdapter(_CanonicalAdapter):
    def list_authorized_active(self, *, actor, scope, page, current_user):
        from app.models.organizational_memory_command import ListActiveMemory, MemoryActor, MemoryScope
        if scope.workspace_id is None: return OwnerUnavailable()
        return self._translate(self._service.list_active(MemoryActor(actor.actor_id, actor.organization_id), ListActiveMemory(MemoryScope(actor.organization_id, scope.workspace_id, scope.project_id), page.page_size, page.continuation)), actor=actor, page=page, current_user=current_user)


class ProjectControlProjectContextAdapter:
    def __init__(self, service: object, owner_actor: object) -> None: self._service, self._actor = service, owner_actor
    def list_authorized_controls(self, *, control_kind, actor, scope, page, current_user):
        if control_kind not in {"risk", "issue", "human_decision", "change"} or getattr(current_user, "id", None) != actor.actor_id: return OwnerProtected()
        try:
            response = self._service.list(kind="decision" if control_kind == "human_decision" else control_kind, project_id=scope.project_id, actor=self._actor)
            data = _values(response)
            status = data.get("status", data.get("outcome"))
            if status in {"protected", "protected_not_found"}: return OwnerProtected()
            if status == "unavailable": return OwnerUnavailable()
            raw = data.get("items", ())
            if not isinstance(raw, (list, tuple)) or len(raw) > page.page_size: return OwnerUnavailable()
            items = tuple(_item(f"project_control:{control_kind}", value) for value in raw)
            return OwnerPage(items=items, last_evaluated_key=items[-1].selector if items else None, observed_at=datetime.now(timezone.utc))
        except Exception: return OwnerUnavailable()


def _protected_exception(exc: Exception) -> bool:
    name = type(exc).__name__.lower()
    return any(word in name for word in ("protected", "forbidden", "notfound", "not_found", "authorizationdenied"))


class ProjectContextGraphAdapter:
    """Fixed graph reads over public canonical application services only."""

    def __init__(self, *, project, workspace, execution, execution_actor,
                 deliverables, deliverable_actor, controls, control_actor,
                 objects, object_actor, context, evidence, evidence_actor,
                 files, file_actor_id, reports, report_actor, memory,
                 memory_actor, relationships, relationship_actor,
                 context_relationships) -> None:
        self.project, self.workspace = project, workspace
        self.execution, self.execution_actor = execution, execution_actor
        self.deliverables, self.deliverable_actor = deliverables, deliverable_actor
        self.controls, self.control_actor = controls, control_actor
        self.objects, self.object_actor = objects, object_actor
        self.context, self.evidence, self.evidence_actor = context, evidence, evidence_actor
        self.files, self.file_actor_id = files, file_actor_id
        self.reports, self.report_actor = reports, report_actor
        self.memory, self.memory_actor = memory, memory_actor
        self.relationships, self.relationship_actor = relationships, relationship_actor
        self.context_relationships = context_relationships

    @staticmethod
    def _kind(selector, expected):
        from app.schemas.project_context import OwnerInvalid
        return None if selector.kind.value == expected else OwnerInvalid()

    def _call(self, kind, owner, actor, scope, callback):
        try:
            return _graph_result(callback(), kind=kind, actor=actor, scope=scope, owner=owner)
        except Exception as exc:
            return OwnerProtected() if _protected_exception(exc) else OwnerUnavailable()

    def project_node(self, *, actor, scope, selector, current_user):
        invalid=self._kind(selector,"project")
        if invalid:return invalid
        from app.schemas.project import ProjectSelectionActor
        return self._call("project","project",actor,scope,lambda:self.project.get_authorized_graph_summary(actor=ProjectSelectionActor(actor_id=actor.actor_id,organization_id=actor.organization_id),project_id=int(selector.value)))
    def workspace_node(self, *, actor, scope, selector, current_user):
        invalid=self._kind(selector,"workspace")
        if invalid:return invalid
        return self._call("workspace","engineering_workspace",actor,scope,lambda:self.workspace.get_authorized_graph_summary(workspace_id=int(selector.value),current_user=current_user))
    def execution_plan_node(self, *, actor, scope, selector, current_user):
        invalid=self._kind(selector,"execution_plan")
        if invalid:return invalid
        def read():
            value=self.execution.get(project_id=scope.project_id,actor=self.execution_actor)
            data=_values(value)
            if data.get("availability")!="established" or data.get("plan_id")!=selector.value:return {"outcome":"protected_not_found"}
            return value
        return self._call("execution_plan","engineering_execution_plan",actor,scope,read)
    def activity_node(self, *, actor, scope, selector, current_user):
        invalid=self._kind(selector,"activity")
        if invalid:return invalid
        return self._call("activity","engineering_execution_plan",actor,scope,lambda:self.execution.get_activity_graph_summary(actor=self.execution_actor,project_id=scope.project_id,activity_id=selector.value))
    def milestone_node(self, *, actor, scope, selector, current_user):
        invalid=self._kind(selector,"milestone")
        if invalid:return invalid
        return self._call("milestone","engineering_execution_plan",actor,scope,lambda:self.execution.get_milestone_graph_summary(actor=self.execution_actor,project_id=scope.project_id,milestone_id=selector.value))
    def deliverable_node(self, *, actor, scope, selector, current_user):
        invalid=self._kind(selector,"deliverable")
        if invalid:return invalid
        return self._call("deliverable","engineering_deliverable",actor,scope,lambda:self.deliverables.get(project_id=scope.project_id,deliverable_id=selector.value,actor=self.deliverable_actor))
    def deliverable_revision_node(self, *, actor, scope, selector, current_user):
        invalid=self._kind(selector,"deliverable_revision")
        if invalid:return invalid
        return self._call("deliverable_revision","engineering_deliverable",actor,scope,lambda:self.deliverables.get_authorized_revision(project_id=scope.project_id,revision_id=selector.value,actor=self.deliverable_actor))
    def _control_node(self, kind, *, actor, scope, selector):
        expected="human_decision" if kind=="decision" else kind
        invalid=self._kind(selector,expected)
        if invalid:return invalid
        return self._call(expected,"project_control",actor,scope,lambda:self.controls.get_control_graph_summary(kind=kind,actor=self.control_actor,project_id=scope.project_id,control_id=selector.value))
    def risk_node(self, **kw): return self._control_node("risk",actor=kw["actor"],scope=kw["scope"],selector=kw["selector"])
    def issue_node(self, **kw): return self._control_node("issue",actor=kw["actor"],scope=kw["scope"],selector=kw["selector"])
    def decision_node(self, **kw): return self._control_node("decision",actor=kw["actor"],scope=kw["scope"],selector=kw["selector"])
    def change_node(self, **kw): return self._control_node("change",actor=kw["actor"],scope=kw["scope"],selector=kw["selector"])
    def change_impact_node(self, *, actor, scope, selector, current_user):
        invalid=self._kind(selector,"change_impact")
        if invalid:return invalid
        return self._call("change_impact","project_control",actor,scope,lambda:self.controls.get_change_impact_graph_summary(actor=self.control_actor,project_id=scope.project_id,impact_id=selector.value))
    def engineering_object_node(self, *, actor, scope, selector, current_user):
        invalid=self._kind(selector,"engineering_object")
        if invalid:return invalid
        from app.models.engineering_object_command import AuthorizationContext
        return self._call("engineering_object","engineering_object",actor,scope,lambda:self.objects.get(selector.value,self.object_actor,AuthorizationContext(operation="ReadEngineeringObject",scope={"project_id":scope.project_id,"workspace_id":scope.workspace_id})))
    def engineering_context_node(self, *, actor, scope, selector, current_user):
        result=self.context.get_authorized_context(actor=actor,scope=scope,selector=selector,current_user=current_user)
        if isinstance(result,OwnerResolved):return _graph_result(result.item,kind="engineering_context",actor=actor,scope=scope,owner="engineering_context")
        return result
    def evidence_node(self, *, actor, scope, selector, current_user):
        invalid=self._kind(selector,"evidence")
        if invalid:return invalid
        return self._call("evidence","evidence",actor,scope,lambda:self.evidence.get(selector.value,self.evidence_actor))
    def supporting_file_node(self, *, actor, scope, selector, current_user):
        invalid=self._kind(selector,"supporting_file")
        if invalid:return invalid
        from app.models.supporting_file_command import SupportingFileScope
        return self._call("supporting_file","supporting_file",actor,scope,lambda:self.files.get_metadata(actor_id=self.file_actor_id,scope=SupportingFileScope(actor.organization_id,scope.project_id,scope.workspace_id),asset_id=selector.value))
    def technical_report_node(self, *, actor, scope, selector, current_user):
        invalid=self._kind(selector,"technical_report")
        if invalid:return invalid
        def read():
            report=self.reports.get_report(self.report_actor,selector.value)
            lifecycle=_scalar(getattr(report,"lifecycle",None))
            snapshot=getattr(report,"accepted_snapshot",None)
            if lifecycle!="accepted" or snapshot is None:return {"outcome":"protected_not_found"}
            return {"report_id":report.id,"project_id":report.project_id,"workspace_id":report.workspace_id,"purpose":_scalar(report.purpose),"version":snapshot.accepted_aggregate_version,"accepted_digest":snapshot.integrity_digest,"accepted_at":snapshot.accepted_at}
        return self._call("technical_report","technical_report",actor,scope,read)
    def organizational_memory_node(self, *, actor, scope, selector, current_user):
        invalid=self._kind(selector,"organizational_memory")
        if invalid:return invalid
        from app.models.organizational_memory_command import GetActiveMemory, MemoryScope
        def read():
            detail=self.memory.get_active(self.memory_actor,GetActiveMemory(memory_id=selector.value,scope=MemoryScope(actor.organization_id,scope.workspace_id,scope.project_id)))
            summary=getattr(detail,"summary",None)
            if summary is None:return detail
            return {"memory_id":summary.memory_id,"project_id":summary.project_id,"workspace_id":summary.workspace_id,"version":summary.version,"standing":"active","limitations_present":bool(getattr(detail,"reuse_restrictions",())),"admitted_at":summary.admitted_at}
        return self._call("organizational_memory","organizational_memory",actor,scope,read)

    @staticmethod
    def _empty_page():
        from app.schemas.project_context import GraphCandidatePage
        return GraphCandidatePage(items=(),observed_at=datetime.now(timezone.utc))

    @staticmethod
    def _candidate(*, relation, selector, source, target, owner, version=None, observed_at=None):
        from app.schemas.project_context import GraphEdgeCandidate
        key=f"{relation.value}:{source.kind.value}:{source.value}:{target.kind.value}:{target.value}:{selector}"
        provenance=FactProvenance(owner_kind=owner,selector=str(selector),version=version,standing="current",source_observed_at=observed_at,observed_at=datetime.now(timezone.utc),authority_class=AuthorityClassification.HUMAN_AUTHORITATIVE,temporal_class=TemporalClassification.CURRENT)
        return GraphEdgeCandidate(candidate_key=key,relationship_selector=str(selector),relationship_kind=relation,source=source,target=target,provenance=provenance)

    @staticmethod
    def _page_for(items, *, selector, direction, page):
        from app.schemas.project_context import GraphCandidatePage, GraphDirection
        def incident(item):
            return item.source==selector if direction is GraphDirection.OUTGOING else item.target==selector if direction is GraphDirection.INCOMING else item.source==selector or item.target==selector
        ordered=sorted((item for item in items if incident(item) and (page.continuation is None or item.candidate_key>page.continuation)),key=lambda item:item.candidate_key)
        selected=tuple(ordered[:page.page_size])
        return GraphCandidatePage(items=selected,has_more=len(ordered)>len(selected),last_evaluated_key=selected[-1].candidate_key if selected else None,observed_at=datetime.now(timezone.utc))

    def context_relationship_edges(self, *, actor, scope, selector, direction, page, current_user):
        from app.schemas.project_context import ContextNodeKind, ContextNodeSelector, GraphCandidatePage, GraphEdgeCandidate
        result=self.context_relationships.list_authorized_incident(actor=actor,scope=scope,selector=selector,direction=direction,page=page,current_user=current_user)
        if not isinstance(result,OwnerPage):return result
        kind_map={"project":ContextNodeKind.PROJECT,"workspace":ContextNodeKind.WORKSPACE,"engineering_context":ContextNodeKind.ENGINEERING_CONTEXT}
        items=[]
        for relation in result.items:
            source=ContextNodeSelector(kind=kind_map[relation.source.kind.value],value=relation.source.selector)
            target=ContextNodeSelector(kind=kind_map[relation.target.kind.value],value=relation.target.selector)
            key=f"context:{relation.relationship_id}:{source.kind.value}:{source.value}:{target.kind.value}:{target.value}"
            items.append(GraphEdgeCandidate(candidate_key=key,relationship_selector=str(relation.relationship_id),relationship_kind=relation.meaning,source=source,target=target,provenance=relation.provenance))
        return self._page_for(items,selector=selector,direction=direction,page=page)

    def engineering_relationship_edges(self, *, actor, scope, selector, direction, page, current_user):
        from app.schemas.project_context import ContextNodeKind, ContextNodeSelector, EngineeringRelationshipDiscriminator, GraphCandidatePage, GraphEdgeCandidate
        if selector.kind is not ContextNodeKind.ENGINEERING_OBJECT:return self._empty_page()
        try:
            from app.models.engineering_relationship_command import RelationshipAuthorizationContext
            from app.schemas.engineering_relationship import EngineeringRelationshipFilter
            response=self.relationships.list_for_endpoint(object_id=selector.value,filters=EngineeringRelationshipFilter(direction=direction.value,workspace_id=scope.workspace_id),page=1,size=page.page_size,actor=self.relationship_actor,context=RelationshipAuthorizationContext(operation="ListEngineeringRelationships",scope={"project_id":scope.project_id,"workspace_id":scope.workspace_id}))
            items=[]
            for relation in response.items:
                source=ContextNodeSelector(kind=ContextNodeKind.ENGINEERING_OBJECT,value=relation.source_object_id)
                target=ContextNodeSelector(kind=ContextNodeKind.ENGINEERING_OBJECT,value=relation.target_object_id)
                discriminator=EngineeringRelationshipDiscriminator(family=relation.relationship_family,relationship_type=relation.relationship_type)
                key=f"engineering:{relation.id}:{source.value}:{target.value}"
                provenance=FactProvenance(owner_kind="engineering_relationship",selector=str(relation.id),version=relation.version,standing=str(_scalar(relation.lifecycle)),source_observed_at=relation.updated_at,observed_at=datetime.now(timezone.utc),authority_class=AuthorityClassification.HUMAN_AUTHORITATIVE,temporal_class=TemporalClassification.CURRENT)
                items.append(GraphEdgeCandidate(candidate_key=key,relationship_selector=str(relation.id),relationship_kind=discriminator,source=source,target=target,provenance=provenance))
            return self._page_for(items,selector=selector,direction=direction,page=page)
        except Exception as exc:
            return OwnerProtected() if _protected_exception(exc) else OwnerUnavailable()

    def execution_edges(self, *, actor, scope, selector, direction, page, current_user):
        from app.schemas.project_context import ContextNodeKind, ContextNodeSelector, ContextRelationshipKind
        if selector.kind not in {ContextNodeKind.EXECUTION_PLAN,ContextNodeKind.ACTIVITY,ContextNodeKind.MILESTONE}:return self._empty_page()
        try:
            response=self.execution.list_authorized_incident_graph_links(actor=self.execution_actor,project_id=scope.project_id,selector_kind=selector.kind.value,selector_id=selector.value,limit=91)
            if not hasattr(response,"items"):return OwnerProtected() if _values(response).get("outcome")!="unavailable" else OwnerUnavailable()
            items=tuple(self._candidate(relation=ContextRelationshipKind(item.relationship),selector=item.relationship_selector,source=ContextNodeSelector(kind=ContextNodeKind(item.source_kind),value=item.source_id),target=ContextNodeSelector(kind=ContextNodeKind(item.target_kind),value=item.target_id),owner="engineering_execution_plan",version=item.owner_version) for item in response.items)
            result=self._page_for(items,selector=selector,direction=direction,page=page)
            return result.model_copy(update={"has_more":response.has_more or result.has_more})
        except Exception as exc:return OwnerProtected() if _protected_exception(exc) else OwnerUnavailable()

    def deliverable_edges(self, *, actor, scope, selector, direction, page, current_user):
        from app.schemas.project_context import ContextNodeKind, ContextNodeSelector, ContextRelationshipKind
        relevant={ContextNodeKind.DELIVERABLE,ContextNodeKind.DELIVERABLE_REVISION,ContextNodeKind.ACTIVITY,ContextNodeKind.MILESTONE,ContextNodeKind.SUPPORTING_FILE}
        if selector.kind not in relevant:return self._empty_page()
        try:
            response=self.deliverables.list_authorized_incident_graph_links(project_id=scope.project_id,actor=self.deliverable_actor,selector_kind=selector.kind.value,selector_id=selector.value,limit=91)
            if not hasattr(response,"items"):return OwnerProtected() if _values(response).get("outcome")!="unavailable" else OwnerUnavailable()
            items=tuple(self._candidate(relation=ContextRelationshipKind(item.relationship),selector=item.relationship_selector,source=ContextNodeSelector(kind=ContextNodeKind(item.source_kind),value=item.source_id),target=ContextNodeSelector(kind=ContextNodeKind(item.target_kind),value=item.target_id),owner="engineering_deliverable",version=item.owner_version) for item in response.items)
            result=self._page_for(items,selector=selector,direction=direction,page=page)
            return result.model_copy(update={"has_more":response.has_more or result.has_more})
        except Exception as exc:return OwnerProtected() if _protected_exception(exc) else OwnerUnavailable()

    def project_control_edges(self, *, actor, scope, selector, direction, page, current_user):
        from app.schemas.project_context import ContextNodeKind, ContextNodeSelector, ContextRelationshipKind
        relevant={ContextNodeKind.HUMAN_DECISION,ContextNodeKind.CHANGE,ContextNodeKind.CHANGE_IMPACT,ContextNodeKind.ACTIVITY,ContextNodeKind.MILESTONE,ContextNodeKind.DELIVERABLE,ContextNodeKind.DELIVERABLE_REVISION,ContextNodeKind.EVIDENCE,ContextNodeKind.SUPPORTING_FILE}
        if selector.kind not in relevant:return self._empty_page()
        try:
            response=self.controls.list_authorized_incident_graph_links(actor=self.control_actor,project_id=scope.project_id,selector_kind=selector.kind.value,selector_id=selector.value,limit=91)
            if not hasattr(response,"items"):return OwnerProtected() if _values(response).get("outcome")!="unavailable" else OwnerUnavailable()
            items=tuple(self._candidate(relation=ContextRelationshipKind(item.relationship),selector=item.relationship_selector,source=ContextNodeSelector(kind=ContextNodeKind(item.source_kind),value=item.source_id),target=ContextNodeSelector(kind=ContextNodeKind(item.target_kind),value=item.target_id),owner="project_control",version=item.owner_version) for item in response.items)
            result=self._page_for(items,selector=selector,direction=direction,page=page)
            return result.model_copy(update={"has_more":response.has_more or result.has_more})
        except Exception as exc:return OwnerProtected() if _protected_exception(exc) else OwnerUnavailable()
    def evidence_file_edges(self, *, actor, scope, selector, direction, page, current_user):
        from app.schemas.project_context import ContextNodeKind, ContextNodeSelector, ContextRelationshipKind
        if selector.kind not in {ContextNodeKind.EVIDENCE,ContextNodeKind.SUPPORTING_FILE}:return self._empty_page()
        try:
            response=(self.evidence.get_supporting_file_graph_links(evidence_id=selector.value,actor=self.evidence_actor,project_id=scope.project_id,workspace_id=scope.workspace_id) if selector.kind is ContextNodeKind.EVIDENCE else self.evidence.get_evidence_graph_links_for_file(asset_id=selector.value,actor=self.evidence_actor,project_id=scope.project_id,workspace_id=scope.workspace_id))
            items=tuple(self._candidate(relation=ContextRelationshipKind.EVIDENCE_SUPPORTING_FILE,selector=f"{item.evidence_id}:{item.asset_id}:{item.ordinal}",source=ContextNodeSelector(kind=ContextNodeKind.EVIDENCE,value=item.evidence_id),target=ContextNodeSelector(kind=ContextNodeKind.SUPPORTING_FILE,value=item.asset_id),owner="evidence",version=item.evidence_version) for item in response.items)
            return self._page_for(items,selector=selector,direction=direction,page=page)
        except Exception as exc:return OwnerProtected() if _protected_exception(exc) else OwnerUnavailable()
    def technical_report_edges(self, *, actor, scope, selector, direction, page, current_user):
        from app.models.technical_report_command import EvidenceHistoricalBasisV1, EvidenceHistoricalBasisV2, EngineeringObjectHistoricalBasisV1
        from app.schemas.project_context import ContextNodeKind, ContextNodeSelector, ContextRelationshipKind
        relevant={ContextNodeKind.TECHNICAL_REPORT,ContextNodeKind.EVIDENCE,ContextNodeKind.ENGINEERING_OBJECT}
        if selector.kind not in relevant:return self._empty_page()
        try:
            if selector.kind is not ContextNodeKind.TECHNICAL_REPORT:
                from app.ports.technical_report import TechnicalReportScope
                links=self.reports.list_authorized_graph_provenance(actor=self.report_actor,scope=TechnicalReportScope(actor.organization_id,scope.workspace_id,scope.project_id),source_kind=selector.kind.value,source_id=selector.value)
                relation=ContextRelationshipKind.REPORT_EVIDENCE_PROVENANCE if selector.kind is ContextNodeKind.EVIDENCE else ContextRelationshipKind.REPORT_OBJECT_PROVENANCE
                items=tuple(self._candidate(relation=relation,selector=link.entry_id,source=ContextNodeSelector(kind=ContextNodeKind.TECHNICAL_REPORT,value=link.report_id),target=selector,owner="technical_report",version=link.report_version,observed_at=link.accepted_at) for link in links)
                return self._page_for(items,selector=selector,direction=direction,page=page)
            report=self.reports.get_report(self.report_actor,selector.value)
            if _scalar(report.lifecycle)!="accepted":return OwnerProtected()
            report_selector=ContextNodeSelector(kind=ContextNodeKind.TECHNICAL_REPORT,value=report.id);items=[]
            for entry in report.accepted_snapshot.provenance:
                locator=entry.locator
                if isinstance(locator,(EvidenceHistoricalBasisV1,EvidenceHistoricalBasisV2)):
                    target=ContextNodeSelector(kind=ContextNodeKind.EVIDENCE,value=locator.evidence_id);relation=ContextRelationshipKind.REPORT_EVIDENCE_PROVENANCE
                elif isinstance(locator,EngineeringObjectHistoricalBasisV1):
                    target=ContextNodeSelector(kind=ContextNodeKind.ENGINEERING_OBJECT,value=locator.engineering_object_id);relation=ContextRelationshipKind.REPORT_OBJECT_PROVENANCE
                else:continue
                items.append(self._candidate(relation=relation,selector=entry.entry_id,source=report_selector,target=target,owner="technical_report",version=report.version,observed_at=report.accepted_snapshot.accepted_at))
            return self._page_for(items,selector=selector,direction=direction,page=page)
        except Exception as exc:return OwnerProtected() if _protected_exception(exc) else OwnerUnavailable()

    def organizational_memory_edges(self, *, actor, scope, selector, direction, page, current_user):
        from app.models.organizational_memory_command import GetActiveMemory, MemoryScope
        from app.schemas.project_context import ContextNodeKind, ContextNodeSelector, ContextRelationshipKind
        if selector.kind not in {ContextNodeKind.ORGANIZATIONAL_MEMORY,ContextNodeKind.TECHNICAL_REPORT}:return self._empty_page()
        try:
            if selector.kind is ContextNodeKind.TECHNICAL_REPORT:
                page_result=self.memory.get_authorized_source_report_graph_links(self.memory_actor,scope=MemoryScope(actor.organization_id,scope.workspace_id,scope.project_id),report_id=selector.value,limit=91)
                if not hasattr(page_result,"items"):return OwnerProtected() if _values(page_result).get("outcome")!="unavailable" else OwnerUnavailable()
                items=tuple(self._candidate(relation=ContextRelationshipKind.MEMORY_SOURCE_REPORT,selector=f"{item.memory_id}:{item.report_id}:{item.accepted_report_version}",source=ContextNodeSelector(kind=ContextNodeKind.ORGANIZATIONAL_MEMORY,value=item.memory_id),target=selector,owner="organizational_memory",version=item.memory_version,observed_at=item.observed_at) for item in page_result.items)
                result=self._page_for(items,selector=selector,direction=direction,page=page)
                return result.model_copy(update={"has_more":page_result.has_more or result.has_more})
            detail=self.memory.get_active(self.memory_actor,GetActiveMemory(memory_id=selector.value,scope=MemoryScope(actor.organization_id,scope.workspace_id,scope.project_id)))
            summary=getattr(detail,"summary",None)
            if summary is None:return OwnerProtected()
            item=self._candidate(relation=ContextRelationshipKind.MEMORY_SOURCE_REPORT,selector=f"{summary.memory_id}:{summary.source_report_id}:{summary.source_accepted_version}",source=ContextNodeSelector(kind=ContextNodeKind.ORGANIZATIONAL_MEMORY,value=summary.memory_id),target=ContextNodeSelector(kind=ContextNodeKind.TECHNICAL_REPORT,value=summary.source_report_id),owner="organizational_memory",version=summary.version,observed_at=summary.updated_at)
            return self._page_for((item,),selector=selector,direction=direction,page=page)
        except Exception as exc:return OwnerProtected() if _protected_exception(exc) else OwnerUnavailable()
