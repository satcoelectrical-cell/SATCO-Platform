"""Accepted PATCH-047 application behavior for Project controls and Change Impact."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from uuid import uuid4

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.adapters.project_control_targets import TargetInvalid, TargetProtected, TargetUnavailable
from app.models.project_control import (
    ProjectRisk, ProjectIssue, ProjectDecision, ProjectChange,
    ProjectRiskHistory, ProjectIssueHistory, ProjectDecisionHistory,
    ProjectChangeHistory, ProjectChangeImpact, ProjectControlIdempotency,
    ProjectControlOutbox,
)
from app.schemas.project_control import (
    ControlSuccess, ControlReadSuccess, ImpactSuccess, Protected, Invalid,
    Conflict, IdempotencyConflict, Unavailable, ControlListSuccess,
    ControlHistoryEntry, ControlHistorySuccess, ImpactRead,
)


class ProjectControlService:
    """One-UoW Project Control service; canonical targets remain externally owned."""

    _models = {"risk": ProjectRisk, "issue": ProjectIssue, "decision": ProjectDecision, "change": ProjectChange}
    _history = {"risk": ProjectRiskHistory, "issue": ProjectIssueHistory, "decision": ProjectDecisionHistory, "change": ProjectChangeHistory}
    _standing = {
        "risk": {"open", "treated", "accepted", "closed"},
        "issue": {"open", "resolved", "closed"},
        "decision": {"draft", "accepted", "superseded"},
        "change": {"recorded", "confirmed", "withdrawn"},
    }

    def __init__(self, *, uow_factory, authorization, target_authorization=None, clock=None):
        self.uow_factory, self.authorization = uow_factory, authorization
        self.target_authorization = target_authorization
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def get(self, *, kind, control_id, actor, project_id=None):
        if kind not in self._models:
            return Invalid()
        try:
            with self.uow_factory() as uow:
                row = uow.repository.get(kind, id=control_id, organization_id=actor.organization_id)
                if row is None or (project_id is not None and row.project_id != project_id):
                    return Protected()
                project = uow.repository.get_project(project_id=row.project_id, organization_id=actor.organization_id)
                if project is None or not self.authorization.can_read(actor=actor, project=project):
                    return Protected()
                return self._read_success(uow, kind=kind, row=row)
        except SQLAlchemyError:
            return Unavailable()

    def list(self, *, kind, project_id, actor):
        if kind not in self._models:
            return Invalid()
        try:
            with self.uow_factory() as uow:
                project = uow.repository.get_project(project_id=project_id, organization_id=actor.organization_id)
                if project is None or not self.authorization.can_read(actor=actor, project=project):
                    return Protected()
                items = tuple(self._read_success(uow, kind=kind, row=row) for row in uow.repository.list(kind, organization_id=actor.organization_id, project_id=project_id))
                return ControlListSuccess(kind=kind, items=items, visible_count=len(items))
        except SQLAlchemyError:
            return Unavailable()

    def history(self, *, kind, control_id, actor, project_id=None):
        if kind not in self._models:
            return Invalid()
        try:
            with self.uow_factory() as uow:
                row = uow.repository.get(kind, id=control_id, organization_id=actor.organization_id)
                if row is None or (project_id is not None and row.project_id != project_id):
                    return Protected()
                project = uow.repository.get_project(project_id=row.project_id, organization_id=actor.organization_id)
                if project is None or not self.authorization.can_read(actor=actor, project=project):
                    return Protected()
                items = tuple(ControlHistoryEntry(id=item.id, aggregate_version=item.aggregate_version, event_type=item.event_type, actor_id=item.actor_id, occurred_at=item.occurred_at) for item in uow.repository.list_history(kind, control_id=control_id, organization_id=actor.organization_id, project_id=row.project_id))
                return ControlHistorySuccess(kind=kind, control_id=control_id, items=items, visible_count=len(items))
        except SQLAlchemyError:
            return Unavailable()

    def create_risk(self, *, project_id, data, actor, idempotency_key): return self._create("risk", project_id=project_id, data=data, actor=actor, idempotency_key=idempotency_key)
    def create_issue(self, *, project_id, data, actor, idempotency_key): return self._create("issue", project_id=project_id, data=data, actor=actor, idempotency_key=idempotency_key)
    def create_decision(self, *, project_id, data, actor, idempotency_key): return self._create("decision", project_id=project_id, data=data, actor=actor, idempotency_key=idempotency_key)
    def create_change(self, *, project_id, data, actor, idempotency_key):
        if data.predecessor_id is not None:
            return Invalid()
        return self._create("change", project_id=project_id, data=data, actor=actor, idempotency_key=idempotency_key)

    def transition_risk(self, *, risk_id, data, actor, idempotency_key, project_id=None): return self._transition("risk", control_id=risk_id, data=data, actor=actor, idempotency_key=idempotency_key, project_id=project_id)
    def transition_issue(self, *, issue_id, data, actor, idempotency_key, project_id=None): return self._transition("issue", control_id=issue_id, data=data, actor=actor, idempotency_key=idempotency_key, project_id=project_id)
    def transition_decision(self, *, decision_id, data, actor, idempotency_key, project_id=None): return self._transition("decision", control_id=decision_id, data=data, actor=actor, idempotency_key=idempotency_key, project_id=project_id)
    def transition_change(self, *, change_id, data, actor, idempotency_key, project_id=None): return self._transition("change", control_id=change_id, data=data, actor=actor, idempotency_key=idempotency_key, project_id=project_id)

    def create_decision_successor(self, *, decision_id, data, actor, idempotency_key, project_id=None): return self._create_successor("decision", predecessor_id=decision_id, data=data, actor=actor, idempotency_key=idempotency_key, project_id=project_id)
    def create_change_successor(self, *, change_id, data, actor, idempotency_key, project_id=None): return self._create_successor("change", predecessor_id=change_id, data=data, actor=actor, idempotency_key=idempotency_key, project_id=project_id)

    def supersede_change(self, *, predecessor_id, data, actor, idempotency_key, project_id=None):
        """Explicit Human supersession withdraws only the predecessor Change."""
        now = self.clock()
        try:
            with self.uow_factory() as uow:
                first_id, second_id = sorted((predecessor_id, data.successor_id), key=str)
                first = uow.repository.get("change", id=first_id, organization_id=actor.organization_id, lock=True)
                second = uow.repository.get("change", id=second_id, organization_id=actor.organization_id, lock=True)
                predecessor = first if first_id == predecessor_id else second
                successor = second if first_id == predecessor_id else first
                if predecessor is None or successor is None or (project_id is not None and predecessor.project_id != project_id):
                    return Protected()
                project = self._mutable_project(uow, predecessor.project_id, actor)
                if project is None or successor.project_id != predecessor.project_id:
                    return Protected()
                if predecessor.version != data.expected_predecessor_version:
                    return Conflict()
                if predecessor.standing == "withdrawn" or successor.standing == "withdrawn" or successor.predecessor_id != predecessor.id:
                    return Invalid()
                operation = "supersede_change"
                fingerprint = self._fingerprint(operation, predecessor.project_id, data)
                replay = self._replay_or_none(uow, actor=actor, project_id=predecessor.project_id, operation=operation, idempotency_key=idempotency_key, fingerprint=fingerprint)
                if replay is not None:
                    return replay
                previous = predecessor.standing
                predecessor.standing, predecessor.version = "withdrawn", predecessor.version + 1
                predecessor.updated_by_id, predecessor.updated_at = actor.actor_id, now
                self._stage_control(uow, "change", predecessor, actor, operation, data.rationale, idempotency_key, fingerprint, now, previous)
                uow.repository.flush(); uow.commit()
                return ControlSuccess(id=predecessor.id, version=predecessor.version)
        except IntegrityError:
            return Conflict()
        except SQLAlchemyError:
            return Unavailable()

    def create_change_impact(self, *, data, actor, idempotency_key, project_id=None):
        if self.target_authorization is None:
            return Unavailable()
        now = self.clock()
        try:
            with self.uow_factory() as uow:
                change = uow.repository.get("change", id=data.change_id, organization_id=actor.organization_id, lock=True)
                if change is None or (project_id is not None and change.project_id != project_id):
                    return Protected()
                project = self._mutable_project(uow, change.project_id, actor)
                if project is None:
                    return Protected()
                if change.version != data.expected_version:
                    return Conflict()
                if data.workspace_id != change.workspace_id or change.standing == "withdrawn":
                    return Invalid()
                operation = "create_change_impact"
                fingerprint = self._fingerprint(operation, change.project_id, data)
                replay = self._replay_or_none(uow, actor=actor, project_id=change.project_id, operation=operation, idempotency_key=idempotency_key, fingerprint=fingerprint)
                if replay is not None:
                    return replay
                target_result = self._authorize_target(actor=actor, change=change, target_kind=data.target_kind, target_id=data.target_id, deliverable_id=data.deliverable_id)
                if target_result is not None:
                    return target_result
                impact = ProjectChangeImpact(id=uuid4(), change_id=change.id, organization_id=change.organization_id, project_id=change.project_id, target_kind=data.target_kind.value, target_id=data.target_id, statement=data.statement, standing="potential")
                uow.repository.add(impact)
                result = ImpactSuccess(id=impact.id, change_id=change.id, standing="potential")
                self._stage_impact(uow, change=change, impact=impact, actor=actor, operation=operation, rationale=data.rationale, idempotency_key=idempotency_key, fingerprint=fingerprint, result=result, now=now)
                uow.repository.flush(); uow.commit()
                return result
        except IntegrityError:
            return Conflict()
        except SQLAlchemyError:
            return Unavailable()

    def confirm_change_impact(self, *, impact_id, data, actor, idempotency_key, project_id=None):
        if self.target_authorization is None:
            return Unavailable()
        now = self.clock()
        try:
            with self.uow_factory() as uow:
                impact = uow.repository.get_impact(impact_id=impact_id, organization_id=actor.organization_id, lock=True)
                if impact is None or (project_id is not None and impact.project_id != project_id):
                    return Protected()
                change = uow.repository.get("change", id=impact.change_id, organization_id=actor.organization_id, lock=True)
                if change is None:
                    return Protected()
                project = self._mutable_project(uow, change.project_id, actor)
                if project is None or impact.project_id != change.project_id:
                    return Protected()
                if change.version != data.expected_change_version:
                    return Conflict()
                operation = "confirm_change_impact"
                fingerprint = self._fingerprint(operation, change.project_id, data)
                replay = self._replay_or_none(uow, actor=actor, project_id=change.project_id, operation=operation, idempotency_key=idempotency_key, fingerprint=fingerprint)
                if replay is not None:
                    return replay
                if impact.standing != "potential" or change.standing == "withdrawn":
                    return Invalid()
                revision_needs_owner = impact.target_kind == "deliverable_revision"
                if revision_needs_owner != (data.deliverable_id is not None):
                    return Invalid()
                target_result = self._authorize_target(actor=actor, change=change, target_kind=impact.target_kind, target_id=impact.target_id, deliverable_id=data.deliverable_id)
                if target_result is not None:
                    return target_result
                impact.standing, impact.confirmed_by_id, impact.confirmed_at = "confirmed", actor.actor_id, now
                result = ImpactSuccess(id=impact.id, change_id=change.id, standing="confirmed")
                self._stage_impact(uow, change=change, impact=impact, actor=actor, operation=operation, rationale=data.rationale, idempotency_key=idempotency_key, fingerprint=fingerprint, result=result, now=now)
                uow.repository.flush(); uow.commit()
                return result
        except IntegrityError:
            return Conflict()
        except SQLAlchemyError:
            return Unavailable()

    def _create_successor(self, kind, *, predecessor_id, data, actor, idempotency_key, project_id=None):
        if data.predecessor_id != predecessor_id or data.expected_version not in (None, 0):
            return Invalid()
        now = self.clock()
        try:
            with self.uow_factory() as uow:
                predecessor = uow.repository.get(kind, id=predecessor_id, organization_id=actor.organization_id, lock=True)
                if predecessor is None or (project_id is not None and predecessor.project_id != project_id):
                    return Protected()
                project = self._mutable_project(uow, predecessor.project_id, actor)
                terminal = "superseded" if kind == "decision" else "withdrawn"
                if project is None or predecessor.standing == terminal:
                    return Protected() if project is None else Invalid()
                operation = f"create_{kind}_successor"
                fingerprint = self._fingerprint(operation, predecessor.project_id, data)
                replay = self._replay_or_none(uow, actor=actor, project_id=predecessor.project_id, operation=operation, idempotency_key=idempotency_key, fingerprint=fingerprint)
                if replay is not None:
                    return replay
                values = self._creation_values(kind, data)
                row = self._models[kind](id=uuid4(), organization_id=actor.organization_id, project_id=predecessor.project_id, version=1, created_by_id=actor.actor_id, created_at=now, updated_by_id=actor.actor_id, updated_at=now, **values)
                uow.repository.add(row); uow.repository.flush()
                self._stage_control(uow, kind, row, actor, operation, data.rationale, idempotency_key, fingerprint, now)
                uow.repository.flush(); uow.commit()
                return ControlSuccess(id=row.id, version=row.version)
        except IntegrityError:
            return Conflict()
        except SQLAlchemyError:
            return Unavailable()

    def _create(self, kind, *, project_id, data, actor, idempotency_key):
        if kind not in self._models or data.expected_version not in (None, 0):
            return Invalid()
        operation, now = f"create_{kind}", self.clock()
        try:
            with self.uow_factory() as uow:
                project = self._mutable_project(uow, project_id, actor)
                if project is None:
                    return Protected()
                fingerprint = self._fingerprint(operation, project_id, data)
                replay = self._replay_or_none(uow, actor=actor, project_id=project_id, operation=operation, idempotency_key=idempotency_key, fingerprint=fingerprint)
                if replay is not None:
                    return replay
                values = self._creation_values(kind, data)
                if kind in {"decision", "change"} and values.get("predecessor_id") is not None:
                    return Invalid()
                row = self._models[kind](id=uuid4(), organization_id=actor.organization_id, project_id=project_id, version=1, created_by_id=actor.actor_id, created_at=now, updated_by_id=actor.actor_id, updated_at=now, **values)
                uow.repository.add(row); uow.repository.flush()
                self._stage_control(uow, kind, row, actor, operation, data.rationale, idempotency_key, fingerprint, now)
                uow.repository.flush(); uow.commit()
                return ControlSuccess(id=row.id, version=row.version)
        except IntegrityError:
            return Conflict()
        except SQLAlchemyError:
            return Unavailable()

    def _transition(self, kind, *, control_id, data, actor, idempotency_key, project_id=None):
        if kind not in self._models or data.target_standing not in self._standing[kind]:
            return Invalid()
        operation, now = f"transition_{kind}", self.clock()
        try:
            with self.uow_factory() as uow:
                row = uow.repository.get(kind, id=control_id, organization_id=actor.organization_id, lock=True)
                if row is None or (project_id is not None and row.project_id != project_id):
                    return Protected()
                project = self._mutable_project(uow, row.project_id, actor)
                if project is None:
                    return Protected()
                fingerprint = self._fingerprint(operation, row.project_id, data)
                replay = self._replay_or_none(uow, actor=actor, project_id=row.project_id, operation=operation, idempotency_key=idempotency_key, fingerprint=fingerprint)
                if replay is not None:
                    return replay
                if row.version != data.expected_version:
                    return Conflict()
                if row.standing in {"closed", "superseded", "withdrawn"} or not self._transition_allowed(kind, row.standing, data.target_standing):
                    return Invalid()
                previous = row.standing
                row.standing, row.version = data.target_standing, row.version + 1
                row.updated_by_id, row.updated_at = actor.actor_id, now
                if kind in {"risk", "issue"} and data.target_standing in {"closed", "resolved", "accepted", "treated"}:
                    row.disposition = data.rationale
                if kind == "decision" and data.target_standing == "accepted":
                    row.accepted_by_id, row.accepted_at = actor.actor_id, now
                if kind == "change" and data.target_standing == "confirmed":
                    row.confirmed_by_id, row.confirmed_at = actor.actor_id, now
                self._stage_control(uow, kind, row, actor, operation, data.rationale, idempotency_key, fingerprint, now, previous)
                uow.repository.flush(); uow.commit()
                return ControlSuccess(id=row.id, version=row.version)
        except IntegrityError:
            return Conflict()
        except SQLAlchemyError:
            return Unavailable()

    @staticmethod
    def _transition_allowed(kind, current, target):
        if kind == "change":
            return (current, target) in {("recorded", "confirmed"), ("recorded", "withdrawn"), ("confirmed", "withdrawn")}
        return current != target

    @staticmethod
    def _creation_values(kind, data):
        values = data.model_dump(exclude={"expected_version"})
        if kind not in {"decision", "change"}:
            values.pop("rationale", None)
        values["standing"] = {"risk": "open", "issue": "open", "decision": "draft", "change": "recorded"}[kind]
        return values

    def _authorize_target(self, *, actor, change, target_kind, target_id, deliverable_id):
        try:
            self.target_authorization.authorize_exact(actor=actor, project_id=change.project_id, workspace_id=change.workspace_id, target_kind=target_kind, target_id=target_id, deliverable_id=deliverable_id)
            return None
        except TargetInvalid:
            return Invalid()
        except TargetProtected:
            return Protected()
        except TargetUnavailable:
            return Unavailable()

    def _mutable_project(self, uow, project_id, actor):
        project = uow.repository.get_project(project_id=project_id, organization_id=actor.organization_id, lock=True)
        return project if project is not None and project.status not in {"completed", "cancelled"} and self.authorization.can_mutate(actor=actor, project=project) else None

    @staticmethod
    def _impact_read(item):
        return ImpactRead(id=item.id, change_id=item.change_id, target_kind=item.target_kind, target_id=item.target_id, statement=item.statement, standing=item.standing, confirmed_by_id=item.confirmed_by_id, confirmed_at=item.confirmed_at)

    def _read_success(self, uow, *, kind, row):
        impacts = tuple(self._impact_read(item) for item in uow.repository.list_impacts(change_id=row.id, organization_id=row.organization_id, project_id=row.project_id)) if kind == "change" else ()
        return ControlReadSuccess(
            id=row.id, version=row.version, organization_id=row.organization_id,
            project_id=row.project_id, workspace_id=row.workspace_id,
            standing=row.standing, statement=row.statement,
            rationale=getattr(row, "rationale", None), predecessor_id=getattr(row, "predecessor_id", None),
            owner_id=getattr(row, "owner_id", None), disposition=getattr(row, "disposition", None),
            observed_context=getattr(row, "observed_context", None), alternatives=tuple(getattr(row, "alternatives", None) or ()),
            accepted_by_id=getattr(row, "accepted_by_id", None), accepted_at=getattr(row, "accepted_at", None),
            confirmed_by_id=getattr(row, "confirmed_by_id", None), confirmed_at=getattr(row, "confirmed_at", None), impacts=impacts,
        )

    def _stage_control(self, uow, kind, row, actor, operation, rationale, key, fingerprint, now, previous=None):
        history_kwargs = {"id": uuid4(), "organization_id": row.organization_id, "project_id": row.project_id, "aggregate_version": row.version, "event_type": operation, "actor_id": actor.actor_id, "occurred_at": now, f"{kind}_id": row.id}
        uow.repository.add(self._history[kind](**history_kwargs))
        self._stage_reliability(uow, row=row, actor=actor, operation=operation, rationale=rationale, key=key, fingerprint=fingerprint, result=ControlSuccess(id=row.id, version=row.version), now=now, aggregate_kind=kind)

    def _stage_impact(self, uow, *, change, impact, actor, operation, rationale, idempotency_key, fingerprint, result, now):
        self._stage_reliability(uow, row=change, actor=actor, operation=operation, rationale=rationale, key=idempotency_key, fingerprint=fingerprint, result=result, now=now, aggregate_kind="change", details={"kind": "change_impact", "standing": impact.standing})

    @staticmethod
    def _stage_reliability(uow, *, row, actor, operation, rationale, key, fingerprint, result, now, aggregate_kind, details=None):
        result_type = "impact" if isinstance(result, ImpactSuccess) else "control"
        uow.stage_idempotency(ProjectControlIdempotency(id=uuid4(), organization_id=row.organization_id, project_id=row.project_id, actor_id=actor.actor_id, operation=operation, idempotency_key=key, fingerprint=fingerprint, replay_json={"schema": "project_control.idempotency.v1", "result_type": result_type, "result": result.model_dump(mode="json")}, created_at=now))
        audit_details = {"kind": aggregate_kind, "rationale": rationale, "version": row.version}
        if details:
            audit_details.update(details)
        uow.stage_audit(actor_id=actor.actor_id, project_id=row.project_id, operation=operation, control_id=row.id, details=audit_details)
        uow.stage_outbox(ProjectControlOutbox(id=uuid4(), event_id=uuid4(), organization_id=row.organization_id, project_id=row.project_id, aggregate_kind=aggregate_kind, aggregate_id=row.id, aggregate_version=row.version, event_type=operation, payload={"kind": aggregate_kind, "id": str(row.id), "version": row.version, "operation": operation}, occurred_at=now))

    def _replay_or_none(self, uow, *, actor, project_id, operation, idempotency_key, fingerprint):
        replay = uow.repository.get_idempotency(organization_id=actor.organization_id, project_id=project_id, actor_id=actor.actor_id, operation=operation, idempotency_key=idempotency_key)
        return None if replay is None else self._replay(replay, fingerprint)

    @staticmethod
    def _fingerprint(operation, project_id, data):
        return sha256(json.dumps({"operation": operation, "project_id": project_id, "data": data.model_dump(mode="json")}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    @staticmethod
    def _replay(record, fingerprint):
        if record.fingerprint != fingerprint:
            return IdempotencyConflict()
        result = record.replay_json["result"]
        return ImpactSuccess(**result) if record.replay_json.get("result_type") == "impact" else ControlSuccess(**result)
