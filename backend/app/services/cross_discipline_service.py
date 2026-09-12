"""Governed orchestration primitives for PATCH-053 Batch 1."""

from __future__ import annotations

from dataclasses import dataclass
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Callable
from uuid import UUID, NAMESPACE_URL, uuid4, uuid5

from sqlalchemy import select

from app.adapters.cross_discipline_sources import (
    SqlAlchemyCrossDisciplineAuthorizer, SqlAlchemyCrossDisciplineSourceReader,
)
from app.discipline_packages.cross_discipline.canonical import canonical_json, digest
from app.discipline_packages.cross_discipline.definitions.eic_v1 import (
    load_batch_five_definition_set, load_batch_four_definition_set, load_batch_one_definition_set, load_batch_three_definition_set, load_batch_two_definition_set,
    validate_batch_five_definition_set, validate_batch_four_definition_set, validate_batch_three_definition_set, validate_batch_two_definition_set,
)
from app.discipline_packages.cross_discipline.evaluator import GenericEvaluator, batch_five_evaluator, batch_four_evaluator, batch_three_evaluator, batch_two_evaluator, release_evaluator
from app.discipline_packages.cross_discipline.contracts import (
    EvaluationInputV1, ExplicitRelationshipV1, FindingIdentityInputV1,
    QuantityV1, RangeV1, SourceIdentityV1,
)
from app.models.audit_log import AuditLog
from app.models.discipline_package import RegistryRelease
from app.models.project_control import ProjectDecision
from app.models.cross_discipline_intelligence import (
    CrossDisciplineAssessment, CrossDisciplineAssessmentWorkspace,
    CrossDisciplineCompletenessAttestation, CrossDisciplineDisposition,
    CrossDisciplineFinding, CrossDisciplineFindingAttestation,
    CrossDisciplineFindingCurrent, CrossDisciplineFindingSource,
    CrossDisciplineIdempotency, CrossDisciplineLineage,
    CrossDisciplineOccurrence, CrossDisciplineOccurrenceSource,
    CrossDisciplineOutbox, CrossDisciplineSnapshot, CrossDisciplineSourceProjection,
)
from app.ports.cross_discipline_intelligence import ProtectedResourceError
from app.repositories.cross_discipline_unit_of_work import (
    CrossDisciplineUnitOfWork, retryable_database_error,
)


PROTECTED_RESULT = {"outcome": "protected_not_found"}
TERMINAL_VIEW_STATES = frozenset({"superseded"})
TRANSITIONS = {
    "open": frozenset({"acknowledge", "confirm", "reject_not_applicable", "dispute", "require_reassessment", "supersede"}),
    "acknowledged": frozenset({"confirm", "reject_not_applicable", "dispute", "require_reassessment", "supersede"}),
    "confirmed": frozenset({"accept_risk", "declare_resolution", "dispute", "require_reassessment", "supersede"}),
    "rejected_not_applicable": frozenset({"require_reassessment", "supersede"}),
    "risk_accepted": frozenset({"declare_resolution", "require_reassessment", "supersede"}),
    "resolution_declared": frozenset({"require_reassessment", "supersede"}),
    "disputed": frozenset({"confirm", "reject_not_applicable", "require_reassessment", "supersede"}),
    "reassessment_required": frozenset({"supersede"}),
    "superseded": frozenset(),
}
RESULTING_STATE = {
    "acknowledge": "acknowledged", "confirm": "confirmed",
    "reject_not_applicable": "rejected_not_applicable",
    "accept_risk": "risk_accepted", "declare_resolution": "resolution_declared",
    "dispute": "disputed", "require_reassessment": "reassessment_required",
    "supersede": "superseded",
}


class VersionConflict(ValueError):
    pass


class IdempotencyConflict(ValueError):
    pass


class InvalidDisposition(ValueError):
    pass


class RetryExhausted(RuntimeError):
    pass


class SourceChanged(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class DispositionDecision:
    action: str
    previous_state: str
    resulting_state: str
    next_assessment_version: int
    next_view_version: int


def request_fingerprint(operation: str, payload) -> str:
    return digest({"operation": operation, "payload": payload}, "satco:xdi-request:v1")


def disposition_transition(
    *, current_state: str, action: str, assessment_version: int,
    expected_assessment_version: int, view_version: int,
    expected_view_version: int, accepted_decision: bool = False,
    changed_source_count: int = 0, successor_valid: bool = False,
) -> DispositionDecision:
    if assessment_version != expected_assessment_version or view_version != expected_view_version:
        raise VersionConflict("version_conflict")
    if action not in TRANSITIONS.get(current_state, frozenset()):
        raise VersionConflict("version_conflict")
    if action == "accept_risk" and not accepted_decision:
        raise InvalidDisposition("accepted_decision_required")
    if action == "declare_resolution" and changed_source_count < 1:
        raise InvalidDisposition("changed_source_or_evidence_required")
    if action == "supersede" and not successor_valid:
        raise InvalidDisposition("compatible_successor_required")
    return DispositionDecision(
        action, current_state, RESULTING_STATE[action],
        assessment_version + 1, view_version + 1,
    )


def run_with_fresh_retries(
    attempt_factory: Callable[[int], object],
    *, authorize: Callable[[int], None],
    max_attempts: int = 3,
):
    if max_attempts != 3:
        raise ValueError("PATCH-053 permits exactly three total database attempts")
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            authorize(attempt)
            return attempt_factory(attempt)
        except ProtectedResourceError:
            raise
        except BaseException as error:
            if not retryable_database_error(error):
                raise
            last_error = error
    raise RetryExhausted("database retry limit exhausted") from last_error


def lineage_would_cycle(existing_edges: tuple[tuple[UUID, UUID], ...], predecessor: UUID, successor: UUID) -> bool:
    if predecessor == successor:
        return True
    adjacency = {}
    for left, right in existing_edges:
        adjacency.setdefault(left, set()).add(right)
    stack = [successor]
    visited = set()
    while stack:
        current = stack.pop()
        if current == predecessor:
            return True
        if current in visited:
            continue
        visited.add(current)
        stack.extend(sorted(adjacency.get(current, ()), key=lambda item: item.bytes, reverse=True))
    return False


def verify_retained_snapshot(*, payload, expected_snapshot_digest: str, expected_result_digest: str):
    observed_snapshot = digest(payload, "satco:cross-discipline-snapshot:v1")
    if observed_snapshot != expected_snapshot_digest:
        return {"outcome": "mismatch", "reason_code": "snapshot_digest_mismatch"}
    stored_result = payload.get("result_digest") if isinstance(payload, dict) else None
    if stored_result != expected_result_digest:
        return {"outcome": "mismatch", "reason_code": "result_digest_mismatch"}
    return {
        "outcome": "verified", "snapshot_digest": observed_snapshot,
        "result_digest": expected_result_digest,
    }


class CrossDisciplineService:
    """Shared kernel application service; pair rules are injected only later."""

    def __init__(self, *, evaluator=None, now=None, impact_handoff=None, ai_explainer=None):
        # The generic, zero-rule evaluator is a retained Batch-1 artifact.
        # Batch-2 is deliberately opt-in so historical creation/replay keeps
        # resolving its exact Batch-1 definition and evaluator identity.
        self.evaluator = evaluator or GenericEvaluator()
        self._batch_two_evaluator = batch_two_evaluator()
        self._batch_three_evaluator = batch_three_evaluator()
        self._batch_four_evaluator = batch_four_evaluator()
        self._batch_five_evaluator = batch_five_evaluator()
        self._release_evaluator = release_evaluator()
        self._impact_handoff = impact_handoff
        self._ai_explainer = ai_explainer
        self._now = now or (lambda: datetime.now(timezone.utc))

    def readiness(self, session=None):
        try:
            definition = load_batch_five_definition_set()
            validate_batch_five_definition_set(definition)
        except ValueError:
            return {"state": "not_ready", "reason_codes": ("definition_digest_mismatch",)}
        if session is not None:
            try:
                registry = session.scalar(select(RegistryRelease).where(
                    RegistryRelease.is_current.is_(True),
                    RegistryRelease.release_id == "patch-052.eic-v1",
                ))
                if registry is None:
                    return {"state": "not_ready", "reason_codes": ("registry_release_missing",)}
                # These probes verify that the three reliability stores are
                # mapped and queryable without reading Project source values.
                session.execute(select(CrossDisciplineIdempotency.id).limit(1))
                session.execute(select(CrossDisciplineOutbox.id).limit(1))
                session.execute(select(AuditLog.id).limit(1))
            except Exception:
                session.rollback()
                return {"state": "unavailable", "reason_codes": ("reliability_unavailable",)}
        return {
            "state": "ready", "reason_codes": (),
            "definition_digest": definition.digest,
        }

    def eligibility(
        self, workspace_ids, *, combination_id="cross.ei.v1",
        project_status="in_progress", package_keys=None,
    ):
        definition = load_batch_one_definition_set()
        expected_packages = {
            "cross.ei.v1": frozenset({"electrical", "instrumentation"}),
            "cross.ic.v1": frozenset({"instrumentation", "control_automation"}),
            "cross.ec.v1": frozenset({"electrical", "control_automation"}),
            "cross.eic.v1": frozenset({"electrical", "instrumentation", "control_automation"}),
        }
        if (
            not workspace_ids or len(workspace_ids) > 12
            or tuple(sorted(set(workspace_ids))) != tuple(workspace_ids)
            or any(isinstance(item, bool) or item < 1 for item in workspace_ids)
            or combination_id not in definition.supported_combinations
        ):
            return {"state": "ineligible", "reason_codes": ("invalid_scope",)}
        if package_keys is not None and frozenset(package_keys) != expected_packages[combination_id]:
            return {"state": "ineligible", "reason_codes": ("binding_mismatch",)}
        if project_status not in {"new", "in_progress", "on_hold"}:
            return {"state": "ineligible", "reason_codes": ("invalid_scope",)}
        return {
            "state": "eligible", "reason_codes": (),
            "definition_digest": definition.digest,
        }

    def unsupported_create(self):
        # Unrecognized/future pair and integrated handlers remain unavailable.
        return {"outcome": "unavailable", "reason_code": "artifact_unavailable"}

    def evaluate_batch_two(self, *, execution_id: str, snapshot_id: str, values_by_rule, sources_by_rule=None):
        """Use the retained shared evaluator; callers must already authorize/project sources."""
        return self._batch_two_evaluator.evaluate(EvaluationInputV1(
            execution_id, snapshot_id, values_by_rule, sources_by_rule or {},
        ))

    def evaluate_batch_three(self, *, execution_id: str, snapshot_id: str, values_by_rule, sources_by_rule=None):
        """Evaluate only authorized I↔C projections after caller authorization/projection."""
        return self._batch_three_evaluator.evaluate(EvaluationInputV1(
            execution_id, snapshot_id, values_by_rule, sources_by_rule or {},
        ))

    def evaluate_batch_four(self, *, execution_id: str, snapshot_id: str, values_by_rule, sources_by_rule=None):
        """Evaluate only authorized Electrical ↔ C&A projections after authorization/projection."""
        return self._batch_four_evaluator.evaluate(EvaluationInputV1(
            execution_id, snapshot_id, values_by_rule, sources_by_rule or {},
        ))

    def evaluate_batch_five(self, *, execution_id: str, snapshot_id: str, values_by_rule, sources_by_rule=None):
        """Evaluate the sole authorized integrated rule after source authorization."""
        return self._batch_five_evaluator.evaluate(EvaluationInputV1(
            execution_id, snapshot_id, values_by_rule, sources_by_rule or {},
        ))

    def explain_findings(self, findings: tuple[dict, ...]):
        """Optional advisory only; unavailable AI never changes deterministic output."""
        if self._ai_explainer is None:
            return {"outcome": "unavailable", "advisory": True}
        try:
            answer = self._ai_explainer.explain(findings)
        except ValueError:
            return {"outcome": "invalid_request", "advisory": True}
        if answer is None:
            return {"outcome": "unavailable", "advisory": True}
        return {"outcome": "success", "summary": answer.summary,
                "draft_next_actions": answer.draft_next_actions, "advisory": True}

    def handoff_potential_impact(
        self, *, session_factory, actor_id, actor_role, organization_id, project_id,
        assessment_id, finding_id, data,
    ):
        """Persist intent, call Project Control, then reconcile in a fresh UoW.

        No session, ORM row or authorization decision crosses these phases.
        """
        handoff_key = digest({"organization_id": str(organization_id), "project_id": project_id,
            "assessment_id": str(assessment_id), "finding_id": str(finding_id),
            "change_id": str(data.change_id), "target_id": str(data.target_id)}, "satco:xdi-handoff:v1")
        project_control_key = uuid5(NAMESPACE_URL, handoff_key)
        confirm_disposition_key = uuid5(NAMESPACE_URL, f"{handoff_key}:confirm")
        now = self._now()
        try:
            with CrossDisciplineUnitOfWork(session_factory) as uow:
                authorizer = SqlAlchemyCrossDisciplineAuthorizer(uow.session)
                authorizer.authorize_scope(
                    actor_id=actor_id, role=actor_role,
                    organization_id=organization_id, project_id=project_id,
                    workspace_ids=(), mutate=True,
                )
                root = uow.repository.get_assessment(assessment_id, organization_id, project_id, lock=True)
                finding = uow.repository.finding(assessment_id=assessment_id, finding_id=finding_id, organization_id=organization_id, project_id=project_id, lock=True)
                current = uow.repository.current_view(assessment_id=assessment_id, finding_id=finding_id, organization_id=organization_id, project_id=project_id, lock=True)
                if root is None or finding is None or current is None:
                    return self.safe_protected_result()
                workspace_ids = uow.repository.assessment_workspace_ids(assessment_id=assessment_id, organization_id=organization_id, project_id=project_id)
                authorizer.authorize_scope(actor_id=actor_id, role=actor_role, organization_id=organization_id, project_id=project_id, workspace_ids=workspace_ids, mutate=True)
                intent = uow.repository.handoff_by_key(handoff_key=handoff_key, organization_id=organization_id, project_id=project_id, lock=True)
                if intent is not None and intent.project_control_impact_id is not None and intent.response_json is not None:
                    return intent.response_json
                if current.current_state not in {"open", "acknowledged", "disputed"}:
                    return {"outcome": "invalid_request"}
                if intent is None:
                    intent = CrossDisciplineIdempotency(organization_id=organization_id, project_id=project_id,
                        actor_id=actor_id, operation="create_potential_impact", idempotency_key=data.idempotency_key,
                        request_digest=request_fingerprint("create_potential_impact", data.model_dump(mode="json")),
                        assessment_id=assessment_id, handoff_key=handoff_key,
                        project_control_idempotency_key=project_control_key,
                        project_control_correlation_id=data.correlation_id)
                    uow.repository.add(intent)
                    uow.commit()
                stored_key = intent.project_control_idempotency_key
        except ProtectedResourceError:
            return self.safe_protected_result()
        if self._impact_handoff is None:
            return {"outcome": "unavailable", "state": "pending", "handoff_key": handoff_key, "advisory": True}
        owner = self._impact_handoff.create_potential(project_id=project_id, workspace_id=None,
            change_id=data.change_id, change_version=data.change_version, target_kind=data.target_kind,
            target_id=data.target_id, rationale=data.rationale, idempotency_key=stored_key)
        if not isinstance(owner, dict) or owner.get("outcome") != "success":
            if isinstance(owner, dict) and owner.get("outcome") == "protected_not_found":
                return self.safe_protected_result()
            return {"outcome": "unavailable", "state": "pending", "handoff_key": handoff_key, "advisory": True}
        try:
            with CrossDisciplineUnitOfWork(session_factory) as uow:
                authorizer = SqlAlchemyCrossDisciplineAuthorizer(uow.session)
                authorizer.authorize_scope(
                    actor_id=actor_id, role=actor_role,
                    organization_id=organization_id, project_id=project_id,
                    workspace_ids=(), mutate=True,
                )
                root = uow.repository.get_assessment(assessment_id, organization_id, project_id, lock=True)
                finding = uow.repository.finding(assessment_id=assessment_id, finding_id=finding_id, organization_id=organization_id, project_id=project_id, lock=True)
                current = uow.repository.current_view(assessment_id=assessment_id, finding_id=finding_id, organization_id=organization_id, project_id=project_id, lock=True)
                if root is None or finding is None or current is None:
                    return self.safe_protected_result()
                workspace_ids = uow.repository.assessment_workspace_ids(assessment_id=assessment_id, organization_id=organization_id, project_id=project_id)
                authorizer.authorize_scope(actor_id=actor_id, role=actor_role, organization_id=organization_id, project_id=project_id, workspace_ids=workspace_ids, mutate=True)
                intent = uow.repository.handoff_by_key(handoff_key=handoff_key, organization_id=organization_id, project_id=project_id, lock=True)
                if intent is None:
                    return {"outcome": "unavailable", "state": "handoff_link_pending", "advisory": True}
                if current.current_state not in {"open", "acknowledged", "disputed"}:
                    return {"outcome": "unavailable", "state": "handoff_link_pending", "advisory": True}
                decision = disposition_transition(
                    current_state=current.current_state, action="confirm",
                    assessment_version=root.aggregate_version,
                    expected_assessment_version=root.aggregate_version,
                    view_version=current.projection_version,
                    expected_view_version=current.projection_version,
                )
                disposition_id = uuid4()
                disposition_payload = {
                    "schema_version": 1,
                    "operation": "create_potential_impact",
                    "handoff_key": handoff_key,
                    "project_control_impact_id": str(owner["id"]),
                    "project_control_impact_standing": "potential",
                    "correlation_id": str(data.correlation_id),
                    "resulting_view_state": decision.resulting_state,
                }
                uow.repository.add(CrossDisciplineDisposition(
                    id=disposition_id, organization_id=organization_id,
                    project_id=project_id, assessment_id=assessment_id,
                    finding_id=finding_id,
                    sequence=uow.repository.next_disposition_sequence(assessment_id),
                    action=decision.action,
                    resulting_view_state=decision.resulting_state,
                    actor_id=actor_id, actor_role=actor_role,
                    rationale=data.rationale,
                    expected_assessment_version=root.aggregate_version,
                    expected_view_version=current.projection_version,
                    resulting_view_version=decision.next_view_version,
                    correlation_id=data.correlation_id,
                    idempotency_key=confirm_disposition_key,
                    payload=disposition_payload,
                    disposition_digest=digest(
                        disposition_payload, "satco:xdi-disposition:v1",
                    ), created_at=now,
                ))
                current.projection_version = decision.next_view_version
                current.latest_disposition_id = disposition_id
                current.latest_action = decision.action
                current.current_state = decision.resulting_state
                current.updated_at = now
                if not uow.repository.increment_root_version(
                    assessment_id=assessment_id,
                    organization_id=organization_id, project_id=project_id,
                    expected_version=root.aggregate_version,
                ):
                    return {"outcome": "version_conflict"}
                response = {"outcome": "success", "state": "reconciled", "impact_id": str(owner["id"]), "handoff_key": handoff_key, "advisory": True}
                intent.project_control_impact_id = UUID(str(owner["id"]))
                intent.project_control_impact_snapshot_digest = digest({"impact_id": str(owner["id"]), "standing": "potential"}, "satco:xdi-impact-result:v1")
                intent.response_json = response
                intent.response_digest = digest(response, "satco:xdi-response:v1")
                intent.completed_at = now
                self._stage_event(
                    uow, actor_id=actor_id, project_id=project_id,
                    assessment_id=assessment_id,
                    event_type="cross_discipline_potential_impact_reconciled",
                    payload={
                        **disposition_payload,
                        "finding_id": str(finding_id),
                        "disposition_id": str(disposition_id),
                        "aggregate_version": decision.next_assessment_version,
                        "current_view_version": decision.next_view_version,
                    }, occurred_at=now,
                )
                uow.commit()
                return response
        except ProtectedResourceError:
            return self.safe_protected_result()
        except Exception:
            return {"outcome": "unavailable", "state": "handoff_link_pending", "advisory": True}

    def create_foundation_assessment(
        self, *, session_factory, actor_id, actor_role, organization_id,
        project_id, data, operation="create_assessment", predecessor_id=None,
        expected_predecessor_version=None, declare_supersession=False,
    ):
        """Persist a complete zero-rule Batch-1 execution in one guarded UoW.

        Any selected interface requires a later authorized production handler
        and therefore fails closed before persistence.
        """
        if data.scope.interface_definition_ids:
            return self._create_selected_assessment(
                session_factory=session_factory, actor_id=actor_id,
                actor_role=actor_role, organization_id=organization_id,
                project_id=project_id, data=data, operation=operation,
                predecessor_id=predecessor_id,
                expected_predecessor_version=expected_predecessor_version,
                declare_supersession=declare_supersession,
            )
        command_payload = data.model_dump(mode="json", exclude={"correlation_id"})
        request_digest = request_fingerprint(operation, command_payload)
        scope_digest = digest(data.scope.model_dump(mode="json"), "satco:xdi-scope:v1")
        last_error = None
        for _attempt in range(1, 4):
            try:
                with CrossDisciplineUnitOfWork(session_factory) as uow:
                    authorizer = SqlAlchemyCrossDisciplineAuthorizer(uow.session)
                    authorized = authorizer.authorize_scope(
                        actor_id=actor_id, role=actor_role,
                        organization_id=organization_id, project_id=project_id,
                        workspace_ids=tuple(data.scope.workspace_ids), mutate=True,
                    )
                    project, workspaces = authorizer.project_and_workspaces(authorized)
                    package_keys = tuple(
                        workspace.bound_package_key or workspace.canonical_discipline_id or workspace.discipline
                        for workspace in workspaces
                    )
                    eligibility = self.eligibility(
                        authorized.workspace_ids,
                        combination_id=data.scope.combination_id,
                        project_status=project.status,
                        package_keys=package_keys,
                    )
                    if eligibility["state"] != "eligible":
                        return {"outcome": "invalid_request", "reason_code": eligibility["reason_codes"][0]}
                    prior = uow.repository.get_idempotency(
                        organization_id=organization_id, project_id=project_id,
                        actor_id=actor_id, operation=operation,
                        idempotency_key=data.idempotency_key, lock=True,
                    )
                    if prior is not None:
                        if prior.request_digest != request_digest:
                            return {"outcome": "idempotency_conflict"}
                        return dict(prior.response_json)
                    registry = uow.session.scalar(select(RegistryRelease).where(
                        RegistryRelease.is_current.is_(True),
                        RegistryRelease.release_id == "patch-052.eic-v1",
                    ))
                    if registry is None:
                        return {"outcome": "unavailable", "reason_code": "artifact_unavailable"}
                    definition = load_batch_one_definition_set()
                    now = self._now()
                    assessment_id, execution_id, snapshot_id = uuid4(), uuid4(), uuid4()
                    evaluation = self.evaluator.evaluate(EvaluationInputV1(
                        str(execution_id), str(snapshot_id), {},
                    ))
                    predecessor = None
                    if predecessor_id is not None:
                        predecessor = uow.repository.get_assessment(
                            predecessor_id, organization_id, project_id, lock=True,
                        )
                        if predecessor is None:
                            raise ProtectedResourceError()
                        if predecessor.aggregate_version != expected_predecessor_version:
                            return {"outcome": "version_conflict"}
                        predecessor_workspaces = uow.repository.assessment_workspace_ids(
                            assessment_id=predecessor_id,
                            organization_id=organization_id, project_id=project_id,
                        )
                        authorizer.authorize_scope(
                            actor_id=actor_id, role=actor_role,
                            organization_id=organization_id, project_id=project_id,
                            workspace_ids=predecessor_workspaces, mutate=True,
                        )
                    snapshot_payload = {
                        "schema_version": 1, "assessment_id": str(assessment_id),
                        "execution_id": str(execution_id), "snapshot_id": str(snapshot_id),
                        "workspace_ids": authorized.workspace_ids,
                        "registry_release_id": registry.release_id,
                        "registry_digest": registry.registry_digest,
                        "definition_set_id": definition.definition_set_id,
                        "definition_digest": definition.digest,
                        "rule_ids": (), "status": evaluation.status,
                        "result_digest": evaluation.result_digest,
                    }
                    snapshot_digest = digest(snapshot_payload, "satco:cross-discipline-snapshot:v1")
                    root = CrossDisciplineAssessment(
                        id=assessment_id, organization_id=organization_id,
                        project_id=project_id, actor_id=actor_id, request_id=uuid4(),
                        purpose=str(data.scope.purpose), rationale=data.rationale,
                        correlation_id=data.correlation_id,
                        causation_id=getattr(data, "causation_id", None),
                        idempotency_key=data.idempotency_key,
                        combination_id=data.scope.combination_id,
                        request_digest=request_digest, scope_digest=scope_digest,
                        status=evaluation.status, reason_code=evaluation.reason_code,
                        aggregate_version=1, created_at=now, completed_at=now,
                    )
                    uow.repository.add(root)
                    uow.repository.add(CrossDisciplineSnapshot(
                        organization_id=organization_id, project_id=project_id,
                        assessment_id=assessment_id, execution_id=execution_id,
                        snapshot_id=snapshot_id, registry_digest=registry.registry_digest,
                        definition_digest=definition.digest,
                        source_manifest_digest=digest((), "satco:xdi-source-manifest:v1"),
                        finding_set_digest=evaluation.finding_set_digest,
                        snapshot_digest=snapshot_digest,
                        result_digest=evaluation.result_digest,
                        observed_through=now, completed_at=now, payload=snapshot_payload,
                    ))
                    for ordinal, workspace in enumerate(workspaces):
                        package_key = workspace.bound_package_key or workspace.canonical_discipline_id or workspace.discipline
                        binding_revision = workspace.bound_project_configuration_revision or 1
                        uow.repository.add(CrossDisciplineAssessmentWorkspace(
                            organization_id=organization_id, project_id=project_id,
                            assessment_id=assessment_id, workspace_id=workspace.id,
                            package_key=package_key, discipline_id=workspace.canonical_discipline_id or workspace.discipline,
                            role=f"participant_{ordinal}", binding_revision=binding_revision,
                            binding_digest=digest({
                                "workspace_id": workspace.id, "package_key": package_key,
                                "binding_revision": binding_revision,
                            }, "satco:xdi-workspace-binding:v1"),
                        ))
                    response = {
                        "outcome": "success", "assessment_id": str(assessment_id),
                        "aggregate_version": 1, "status": evaluation.status,
                        "result_digest": evaluation.result_digest,
                    }
                    event_payload = {
                        "schema_version": 1, "outcome": "success",
                        "organization_id": str(organization_id),
                        "project_id": project_id,
                        "workspace_ids": authorized.workspace_ids,
                        "assessment_id": str(assessment_id),
                        "execution_id": str(execution_id),
                        "snapshot_id": str(snapshot_id),
                        "aggregate_version": 1,
                        "correlation_id": str(data.correlation_id),
                        "idempotency_key": str(data.idempotency_key),
                        "registry_digest": registry.registry_digest,
                        "definition_digest": definition.digest,
                        "result_digest": evaluation.result_digest,
                    }
                    for event_type in (
                        "cross_discipline_assessment_requested",
                        "cross_discipline_assessment_created",
                        "cross_discipline_assessment_completed",
                    ):
                        self._stage_event(
                            uow, actor_id=actor_id, project_id=project_id,
                            assessment_id=assessment_id, event_type=event_type,
                            payload=event_payload, occurred_at=now,
                        )
                    if predecessor is not None:
                        reassessment_lineage = CrossDisciplineLineage(
                            organization_id=organization_id, project_id=project_id,
                            predecessor_id=predecessor.id, successor_id=assessment_id,
                            kind="reassessment_of", scope_family_digest=scope_digest,
                            actor_id=actor_id, rationale=data.rationale,
                            correlation_id=data.correlation_id,
                            idempotency_key=data.idempotency_key,
                            replacement_operation_id=data.idempotency_key,
                        )
                        uow.repository.add(reassessment_lineage)
                        for event_type in (
                            "cross_discipline_reassessment_created",
                            "cross_discipline_reassessment_linked",
                        ):
                            self._stage_event(
                                uow, actor_id=actor_id, project_id=project_id,
                                assessment_id=assessment_id, event_type=event_type,
                                payload=event_payload, occurred_at=now,
                            )
                        response["predecessor_assessment_id"] = str(predecessor.id)
                        response["lineage_id"] = str(reassessment_lineage.id)
                        if declare_supersession:
                            if predecessor.scope_digest != scope_digest:
                                return {"outcome": "invalid_request", "reason_code": "invalid_scope"}
                            uow.repository.add(CrossDisciplineLineage(
                                organization_id=organization_id, project_id=project_id,
                                predecessor_id=predecessor.id, successor_id=assessment_id,
                                kind="supersedes", scope_family_digest=scope_digest,
                                actor_id=actor_id, rationale=data.rationale,
                                correlation_id=data.correlation_id,
                                idempotency_key=data.idempotency_key,
                                replacement_operation_id=uuid4(),
                            ))
                            if not uow.repository.increment_root_version(
                                assessment_id=predecessor.id,
                                organization_id=organization_id, project_id=project_id,
                                expected_version=predecessor.aggregate_version,
                            ):
                                return {"outcome": "version_conflict"}
                            response["predecessor_aggregate_version"] = expected_predecessor_version + 1
                    response_digest = digest(response, "satco:xdi-response:v1")
                    uow.repository.add(CrossDisciplineIdempotency(
                        organization_id=organization_id, project_id=project_id,
                        actor_id=actor_id, operation=operation,
                        idempotency_key=data.idempotency_key,
                        request_digest=request_digest, response_json=response,
                        response_digest=response_digest, assessment_id=assessment_id,
                        completed_at=now,
                    ))
                    uow.commit()
                    return response
            except ProtectedResourceError:
                return self.safe_protected_result()
            except BaseException as error:
                if not retryable_database_error(error):
                    raise
                last_error = error
        raise RetryExhausted("database retry limit exhausted") from last_error

    def _create_selected_assessment(
        self, *, session_factory, actor_id, actor_role, organization_id, project_id,
        data, operation, predecessor_id=None, expected_predecessor_version=None,
        declare_supersession=False,
    ):
        """Run the accepted cumulative release in one assessment UoW."""
        command_payload = data.model_dump(mode="json", exclude={"correlation_id"})
        request_digest = request_fingerprint(operation, command_payload)
        scope_digest = digest(data.scope.model_dump(mode="json"), "satco:xdi-scope:v1")
        last_source_change = False
        for _attempt in range(1, 4):
            try:
                with CrossDisciplineUnitOfWork(session_factory) as uow:
                    authorizer = SqlAlchemyCrossDisciplineAuthorizer(uow.session)
                    authorized = authorizer.authorize_scope(
                        actor_id=actor_id, role=actor_role,
                        organization_id=organization_id, project_id=project_id,
                        workspace_ids=tuple(data.scope.workspace_ids), mutate=True,
                    )
                    project, workspaces = authorizer.project_and_workspaces(authorized)
                    package_keys = tuple(
                        item.bound_package_key or item.canonical_discipline_id or item.discipline
                        for item in workspaces
                    )
                    eligibility = self.eligibility(
                        authorized.workspace_ids, combination_id=data.scope.combination_id,
                        project_status=project.status, package_keys=package_keys,
                    )
                    if eligibility["state"] != "eligible":
                        return {"outcome": "invalid_request", "reason_code": eligibility["reason_codes"][0]}
                    prior = uow.repository.get_idempotency(
                        organization_id=organization_id, project_id=project_id,
                        actor_id=actor_id, operation=operation,
                        idempotency_key=data.idempotency_key, lock=True,
                    )
                    if prior is not None:
                        return dict(prior.response_json) if prior.request_digest == request_digest else {"outcome": "idempotency_conflict"}
                    registry = uow.session.scalar(select(RegistryRelease).where(
                        RegistryRelease.is_current.is_(True),
                        RegistryRelease.release_id == "patch-052.eic-v1",
                    ))
                    if registry is None:
                        return {"outcome": "unavailable", "reason_code": "artifact_unavailable"}
                    definition = load_batch_five_definition_set()
                    interfaces = {item.interface_definition_id: item for item in definition.interface_definitions}
                    interface_ids = tuple(data.scope.interface_definition_ids)
                    if (
                        not interface_ids or len(interface_ids) > 16
                        or tuple(sorted(set(interface_ids))) != interface_ids
                        or any(item not in interfaces for item in interface_ids)
                    ):
                        return {"outcome": "invalid_request", "reason_code": "invalid_scope"}
                    # A pair/integrated selection may not smuggle an unrelated
                    # interface into a different declared combination.
                    expected_interface = {
                        "cross.ei.v1": "cross.interface.ei.power_handoff.v1",
                        "cross.ic.v1": "cross.interface.ic.signal_control.v1",
                        "cross.ec.v1": "cross.interface.ec.command_power.v1",
                        "cross.eic.v1": "cross.interface.eic.change_path.v1",
                    }[data.scope.combination_id]
                    if any(item != expected_interface for item in interface_ids):
                        return {"outcome": "invalid_request", "reason_code": "invalid_scope"}
                    now = self._now()
                    assessment_id, execution_id, snapshot_id = uuid4(), uuid4(), uuid4()
                    bindings = tuple(
                        (item.id, item.canonical_discipline_id or item.discipline,
                         item.bound_project_configuration_revision or 1)
                        for item in workspaces
                    )
                    reader = SqlAlchemyCrossDisciplineSourceReader(uow.session, authorizer=authorizer)
                    acquired = reader.acquire(
                        authorized=authorized, definition=definition, interface_ids=interface_ids,
                        selectors=tuple(data.scope.endpoint_selectors),
                        purpose=str(data.scope.purpose), combination_id=data.scope.combination_id,
                        project_change_id=data.scope.project_change_id,
                        project_change_version=data.scope.project_change_version,
                        execution_id=execution_id, snapshot_id=snapshot_id,
                        registry_digest=registry.registry_digest,
                        workspace_bindings=bindings, observed_at=now,
                    )
                    if not acquired.values_by_rule:
                        return {"outcome": "invalid_request", "reason_code": "invalid_scope"}
                    evaluation = self._release_evaluator.evaluate(EvaluationInputV1(
                        str(execution_id), str(snapshot_id), acquired.values_by_rule,
                        acquired.sources_by_rule,
                    ))
                    if not reader.recheck(authorized=authorized, identities=acquired.recheck_identities):
                        raise SourceChanged()
                    root = CrossDisciplineAssessment(
                        id=assessment_id, organization_id=organization_id, project_id=project_id,
                        actor_id=actor_id, request_id=uuid4(), purpose=str(data.scope.purpose),
                        rationale=data.rationale, correlation_id=data.correlation_id,
                        causation_id=getattr(data, "causation_id", None),
                        idempotency_key=data.idempotency_key, combination_id=data.scope.combination_id,
                        request_digest=request_digest, scope_digest=scope_digest,
                        status=evaluation.status, reason_code=evaluation.reason_code,
                        aggregate_version=1, created_at=now, completed_at=now,
                    )
                    uow.repository.add(root)
                    for ordinal, workspace in enumerate(workspaces):
                        package_key = workspace.bound_package_key or workspace.canonical_discipline_id or workspace.discipline
                        binding_revision = workspace.bound_project_configuration_revision or 1
                        uow.repository.add(CrossDisciplineAssessmentWorkspace(
                            organization_id=organization_id, project_id=project_id,
                            assessment_id=assessment_id, workspace_id=workspace.id,
                            package_key=package_key, discipline_id=workspace.canonical_discipline_id or workspace.discipline,
                            role=f"participant_{ordinal}", binding_revision=binding_revision,
                            binding_digest=digest({"workspace_id": workspace.id, "package_key": package_key, "binding_revision": binding_revision}, "satco:xdi-workspace-binding:v1"),
                        ))
                    projection_rows = {}
                    for projection in acquired.projections:
                        row = CrossDisciplineSourceProjection(
                            organization_id=organization_id, project_id=project_id, assessment_id=assessment_id,
                            projection_id=projection.projection_id, owner_kind=projection.owner_kind,
                            owner_id=projection.owner_id, revision_kind="aggregate_version",
                            revision=projection.owner_revision, schema_id=projection.schema_id,
                            adapter_capability_id=projection.adapter_capability_id, sensitivity="project",
                            payload=projection.payload, projection_digest=projection.projection_digest,
                        )
                        projection_rows[projection.projection_id] = row
                        uow.repository.add(row)
                    attestation_rows = {}
                    for attestation in acquired.attestations:
                        row = CrossDisciplineCompletenessAttestation(
                            id=attestation.attestation_id, organization_id=organization_id, project_id=project_id,
                            assessment_id=assessment_id, owner_kind=attestation.owner_kind, owner_id=attestation.owner_id,
                            selector_digest=attestation.selector_digest, observed_cardinality=attestation.observed_cardinality,
                            page_count=1, non_truncated=True, negative_result=attestation.observed_cardinality == 0,
                            payload=attestation.payload, attestation_digest=attestation.attestation_digest,
                        )
                        attestation_rows[attestation.attestation_digest] = row
                        uow.repository.add(row)
                    occurrence_rows = {}
                    for occurrence in acquired.occurrences:
                        row = CrossDisciplineOccurrence(
                            id=occurrence.occurrence_id, organization_id=organization_id, project_id=project_id,
                            assessment_id=assessment_id, occurrence_key=occurrence.occurrence_key,
                            interface_definition_id=occurrence.interface_definition_id,
                            provider_workspace_id=occurrence.provider_workspace_id,
                            consumer_workspace_id=occurrence.consumer_workspace_id,
                            applicability=occurrence.applicability, payload=occurrence.payload,
                            occurrence_digest=occurrence.occurrence_digest,
                        )
                        occurrence_rows[occurrence.interface_definition_id] = row
                        uow.repository.add(row)
                    uow.repository.flush()
                    for occurrence in occurrence_rows.values():
                        for projection in projection_rows.values():
                            uow.repository.add(CrossDisciplineOccurrenceSource(
                                assessment_id=assessment_id, occurrence_id=occurrence.id,
                                projection_id=projection.id,
                            ))
                    for ordinal, finding in enumerate(evaluation.findings):
                        identity = finding.identity
                        finding_id = UUID(finding.finding_id)
                        row = CrossDisciplineFinding(
                            id=finding_id, organization_id=organization_id, project_id=project_id,
                            assessment_id=assessment_id,
                            occurrence_id=occurrence_rows[identity.interface_definition_id].id,
                            ordinal=ordinal, rule_id=identity.rule_id, rule_version=identity.rule_version,
                            rule_digest=identity.rule_digest, category=identity.category, subcode=identity.subcode,
                            severity=finding.severity, fingerprint=finding.fingerprint,
                            recurrence_key=finding.recurrence_key, affected_selector=identity.affected_selector,
                            payload=json.loads(canonical_json({"identity": identity, "comparison_outcome": finding.comparison_outcome})),
                            created_at=now,
                        )
                        uow.repository.add(row)
                        uow.repository.add(CrossDisciplineFindingCurrent(
                            organization_id=organization_id, project_id=project_id,
                            assessment_id=assessment_id, finding_id=finding_id,
                            projection_version=0, current_state="open",
                        ))
                        for projection in projection_rows.values():
                            uow.repository.add(CrossDisciplineFindingSource(
                                assessment_id=assessment_id, finding_id=finding_id,
                                projection_id=projection.id, role="evaluation_input",
                            ))
                        for attestation in attestation_rows.values():
                            uow.repository.add(CrossDisciplineFindingAttestation(
                                assessment_id=assessment_id, finding_id=finding_id,
                                attestation_id=attestation.id, role="completeness",
                            ))
                    snapshot_payload = {
                        "schema_version": 1, "assessment_id": str(assessment_id),
                        "execution_id": str(execution_id), "snapshot_id": str(snapshot_id),
                        "workspace_ids": authorized.workspace_ids, "registry_release_id": registry.release_id,
                        "registry_digest": registry.registry_digest, "definition_set_id": definition.definition_set_id,
                        "definition_digest": definition.digest, "selected_interface_ids": interface_ids,
                        "rule_ids": tuple(sorted(acquired.values_by_rule)), "status": evaluation.status,
                        "reason_code": evaluation.reason_code, "result_digest": evaluation.result_digest,
                        "source_manifest": acquired.source_manifest,
                        # Inputs are retained as canonical JSON data, never re-read from mutable owners.
                        "retained_values_by_rule": json.loads(canonical_json(acquired.values_by_rule)),
                        "retained_sources_by_rule": json.loads(canonical_json(acquired.sources_by_rule)),
                    }
                    snapshot_digest = digest(snapshot_payload, "satco:cross-discipline-snapshot:v1")
                    uow.repository.add(CrossDisciplineSnapshot(
                        organization_id=organization_id, project_id=project_id, assessment_id=assessment_id,
                        execution_id=execution_id, snapshot_id=snapshot_id, registry_digest=registry.registry_digest,
                        definition_digest=definition.digest,
                        source_manifest_digest=digest(acquired.source_manifest, "satco:xdi-source-manifest:v1"),
                        finding_set_digest=evaluation.finding_set_digest, snapshot_digest=snapshot_digest,
                        result_digest=evaluation.result_digest, observed_through=now, completed_at=now,
                        payload=snapshot_payload,
                    ))
                    response = {"outcome": "success", "assessment_id": str(assessment_id),
                        "aggregate_version": 1, "status": evaluation.status,
                        "result_digest": evaluation.result_digest}
                    event_payload = {"schema_version": 1, "outcome": "success", "organization_id": str(organization_id),
                        "project_id": project_id, "workspace_ids": authorized.workspace_ids,
                        "assessment_id": str(assessment_id), "execution_id": str(execution_id),
                        "snapshot_id": str(snapshot_id), "aggregate_version": 1,
                        "correlation_id": str(data.correlation_id), "idempotency_key": str(data.idempotency_key),
                        "registry_digest": registry.registry_digest, "definition_digest": definition.digest,
                        "result_digest": evaluation.result_digest}
                    terminal = "completed" if evaluation.status.startswith("completed_") else evaluation.status
                    for event_type in ("cross_discipline_assessment_requested", "cross_discipline_assessment_created", f"cross_discipline_assessment_{terminal}"):
                        self._stage_event(uow, actor_id=actor_id, project_id=project_id,
                            assessment_id=assessment_id, event_type=event_type,
                            payload=event_payload, occurred_at=now)
                    uow.repository.add(CrossDisciplineIdempotency(
                        organization_id=organization_id, project_id=project_id, actor_id=actor_id,
                        operation=operation, idempotency_key=data.idempotency_key,
                        request_digest=request_digest, response_json=response,
                        response_digest=digest(response, "satco:xdi-response:v1"),
                        assessment_id=assessment_id, completed_at=now,
                    ))
                    uow.commit()
                    return response
            except ProtectedResourceError:
                return self.safe_protected_result()
            except SourceChanged:
                last_source_change = True
                continue
            except BaseException as error:
                if not retryable_database_error(error):
                    raise
        if last_source_change:
            return {"outcome": "indeterminate", "reason_code": "source_changed"}
        raise RetryExhausted("database retry limit exhausted")

    def supersede_assessment(
        self, *, session_factory, actor_id, actor_role, organization_id,
        project_id, predecessor_id, data,
    ):
        payload = data.model_dump(mode="json", exclude={"correlation_id"})
        request_digest = request_fingerprint("supersede_assessment", payload)
        last_error = None
        for _attempt in range(1, 4):
            try:
                with CrossDisciplineUnitOfWork(session_factory) as uow:
                    authorizer = SqlAlchemyCrossDisciplineAuthorizer(uow.session)
                    authorizer.authorize_scope(
                        actor_id=actor_id, role=actor_role,
                        organization_id=organization_id, project_id=project_id,
                        workspace_ids=(), mutate=True,
                    )
                    roots = {}
                    for identity in sorted(
                        (predecessor_id, data.successor_assessment_id),
                        key=lambda item: item.bytes,
                    ):
                        roots[identity] = uow.repository.get_assessment(
                            identity, organization_id, project_id, lock=True,
                        )
                        if roots[identity] is None:
                            raise ProtectedResourceError()
                    predecessor = roots[predecessor_id]
                    successor = roots[data.successor_assessment_id]
                    workspace_ids = tuple(sorted(set(
                        uow.repository.assessment_workspace_ids(
                            assessment_id=predecessor.id,
                            organization_id=organization_id, project_id=project_id,
                        ) + uow.repository.assessment_workspace_ids(
                            assessment_id=successor.id,
                            organization_id=organization_id, project_id=project_id,
                        )
                    )))
                    authorizer.authorize_scope(
                        actor_id=actor_id, role=actor_role,
                        organization_id=organization_id, project_id=project_id,
                        workspace_ids=workspace_ids, mutate=True,
                    )
                    prior = uow.repository.get_idempotency(
                        organization_id=organization_id, project_id=project_id,
                        actor_id=actor_id, operation="supersede_assessment",
                        idempotency_key=data.idempotency_key, lock=True,
                    )
                    if prior is not None:
                        return dict(prior.response_json) if prior.request_digest == request_digest else {"outcome": "idempotency_conflict"}
                    if (
                        predecessor.aggregate_version != data.expected_predecessor_version
                        or successor.aggregate_version != data.expected_successor_version
                    ):
                        return {"outcome": "version_conflict"}
                    if predecessor.scope_digest != successor.scope_digest:
                        return {"outcome": "invalid_request", "reason_code": "invalid_scope"}
                    edges = uow.repository.lineage_edges(
                        organization_id=organization_id, project_id=project_id,
                    )
                    if lineage_would_cycle(edges, predecessor.id, successor.id):
                        return {"outcome": "invalid_request", "reason_code": "invalid_scope"}
                    now, lineage_id = self._now(), uuid4()
                    uow.repository.add(CrossDisciplineLineage(
                        id=lineage_id, organization_id=organization_id,
                        project_id=project_id, predecessor_id=predecessor.id,
                        successor_id=successor.id, kind="supersedes",
                        scope_family_digest=predecessor.scope_digest,
                        actor_id=actor_id, rationale=data.rationale,
                        correlation_id=data.correlation_id,
                        idempotency_key=data.idempotency_key,
                        replacement_operation_id=data.idempotency_key,
                    ))
                    if not uow.repository.increment_root_version(
                        assessment_id=predecessor.id,
                        organization_id=organization_id, project_id=project_id,
                        expected_version=predecessor.aggregate_version,
                    ):
                        return {"outcome": "version_conflict"}
                    response = {
                        "outcome": "success", "lineage_id": str(lineage_id),
                        "predecessor_assessment_id": str(predecessor.id),
                        "successor_assessment_id": str(successor.id),
                        "predecessor_aggregate_version": data.expected_predecessor_version + 1,
                        "successor_aggregate_version": successor.aggregate_version,
                    }
                    uow.repository.add(CrossDisciplineIdempotency(
                        organization_id=organization_id, project_id=project_id,
                        actor_id=actor_id, operation="supersede_assessment",
                        idempotency_key=data.idempotency_key,
                        request_digest=request_digest, response_json=response,
                        response_digest=digest(response, "satco:xdi-response:v1"),
                        assessment_id=predecessor.id, completed_at=now,
                    ))
                    event_payload = {
                        "schema_version": 1,
                        "organization_id": str(organization_id),
                        "project_id": project_id,
                        "assessment_id": str(predecessor.id),
                        "successor_assessment_id": str(successor.id),
                        "lineage_id": str(lineage_id),
                        "aggregate_version": data.expected_predecessor_version + 1,
                        "correlation_id": str(data.correlation_id),
                    }
                    self._stage_event(
                        uow, actor_id=actor_id, project_id=project_id,
                        assessment_id=predecessor.id,
                        event_type="cross_discipline_assessment_superseded",
                        payload=event_payload, occurred_at=now,
                    )
                    uow.commit()
                    return response
            except ProtectedResourceError:
                return self.safe_protected_result()
            except BaseException as error:
                if not retryable_database_error(error):
                    raise
                last_error = error
        raise RetryExhausted("database retry limit exhausted") from last_error

    def verify_historical(
        self, *, session_factory, actor_id, actor_role, organization_id,
        project_id, assessment_id, data,
    ):
        with CrossDisciplineUnitOfWork(session_factory) as uow:
            authorizer = SqlAlchemyCrossDisciplineAuthorizer(uow.session)
            authorizer.authorize_scope(
                actor_id=actor_id, role=actor_role,
                organization_id=organization_id, project_id=project_id,
                workspace_ids=(), mutate=False,
            )
            root = uow.repository.get_assessment(
                assessment_id, organization_id, project_id,
            )
            if root is None:
                return self.safe_protected_result()
            workspace_ids = uow.repository.assessment_workspace_ids(
                assessment_id=assessment_id,
                organization_id=organization_id, project_id=project_id,
            )
            authorizer.authorize_scope(
                actor_id=actor_id, role=actor_role,
                organization_id=organization_id, project_id=project_id,
                workspace_ids=workspace_ids, mutate=False,
            )
            snapshot = uow.repository.snapshot(
                assessment_id=assessment_id,
                organization_id=organization_id, project_id=project_id,
            )
            now = self._now()
            base = {
                "schema_version": 1,
                "organization_id": str(organization_id),
                "project_id": project_id,
                "assessment_id": str(assessment_id),
                "correlation_id": str(data.correlation_id),
            }
            uow.repository.add(AuditLog(
                user_id=actor_id,
                action="cross_discipline_historical_verification_attempted",
                entity="CROSS_DISCIPLINE_ASSESSMENT", entity_id=project_id,
                entity_uuid=assessment_id, details=base,
            ))
            if snapshot is None:
                result = {"outcome": "unavailable", "reason_code": "artifact_missing"}
                terminal = "cross_discipline_historical_verification_integrity_failed"
            elif snapshot.snapshot_digest != data.expected_snapshot_digest:
                result = {"outcome": "mismatch", "reason_code": "snapshot_digest_mismatch"}
                terminal = "cross_discipline_historical_verification_integrity_failed"
            else:
                verified = verify_retained_snapshot(
                    payload=snapshot.payload,
                    expected_snapshot_digest=snapshot.snapshot_digest,
                    expected_result_digest=snapshot.result_digest,
                )
                if verified["outcome"] == "verified":
                    try:
                        replay_input = self._retained_evaluation_input(snapshot)
                        evaluator = self._release_evaluator if replay_input.values_by_rule else self.evaluator
                        replay = evaluator.evaluate(replay_input)
                    except (KeyError, TypeError, ValueError):
                        replay = None
                    if replay is None or replay.result_digest != snapshot.result_digest:
                        result = {"outcome": "mismatch", "reason_code": "result_digest_mismatch"}
                        terminal = "cross_discipline_historical_verification_integrity_failed"
                    else:
                        result = verified
                        terminal = "cross_discipline_historical_verification_completed"
                else:
                    result = verified
                    terminal = "cross_discipline_historical_verification_integrity_failed"
            uow.repository.add(AuditLog(
                user_id=actor_id, action=terminal,
                entity="CROSS_DISCIPLINE_ASSESSMENT", entity_id=project_id,
                entity_uuid=assessment_id, details={**base, **result},
            ))
            uow.commit()
            return result

    @staticmethod
    def _retained_evaluation_input(snapshot) -> EvaluationInputV1:
        """Rehydrate the typed, immutable input retained in a snapshot.

        Source owners are intentionally never consulted during historical
        verification.  The JSON snapshot is the replay authority.
        """
        payload = snapshot.payload
        values = payload.get("retained_values_by_rule", {})
        sources = payload.get("retained_sources_by_rule", {})
        if not isinstance(values, dict) or not isinstance(sources, dict):
            raise ValueError("retained_input_invalid")

        def source(value):
            if not isinstance(value, dict):
                raise ValueError("retained_input_invalid")
            return SourceIdentityV1(
                value["owner_kind"], value["owner_id"], value["revision_kind"],
                value["revision"], value["projection_digest"],
            )

        def identity(value):
            if not isinstance(value, dict):
                raise ValueError("retained_input_invalid")
            return FindingIdentityInputV1(
                value["assessment_execution_id"], value["assessment_snapshot_id"],
                value["category"], value["subcode"], value["rule_id"],
                value["rule_version"], value["rule_digest"],
                value["interface_definition_id"], value["interface_version"],
                value["interface_digest"], value["occurrence_key"],
                value["affected_selector"], tuple(source(item) for item in value["sources"]),
                tuple(value.get("attestation_digests", ())),
                tuple(value["commitment"]) if value.get("commitment") is not None else None,
                tuple(value["change"]) if value.get("change") is not None else None,
                value.get("registry_digest", ""), value.get("combination_id", ""),
                value.get("project_configuration_revision", 1),
                tuple(tuple(item) for item in value.get("workspace_binding_revisions", ())),
            )

        def edge(value):
            if not isinstance(value, dict):
                raise ValueError("retained_input_invalid")
            return ExplicitRelationshipV1(
                value["relationship_owner_kind"], value["relationship_id"],
                value["aggregate_version"], value["relationship_family"],
                value["relationship_type"], value["source_object_id"],
                value["target_object_id"],
            )

        restored = {}
        for rule_id, raw in values.items():
            if not isinstance(rule_id, str) or not isinstance(raw, dict):
                raise ValueError("retained_input_invalid")
            item = dict(raw)
            item["identity"] = identity(item["identity"])
            if "edges" in item:
                item["edges"] = tuple(edge(value) for value in item["edges"])
            for key in ("electrical_voltage", "instrument_voltage"):
                if key in item:
                    value = item[key]
                    item[key] = QuantityV1(
                        value["dimension"], Decimal(value["magnitude"]),
                        value["source_unit"], Decimal(value["canonical_magnitude"]),
                    )
            for key in ("instrumentation_range", "control_accepted_range"):
                if key in item:
                    value = item[key]
                    item[key] = RangeV1(
                        Decimal(value["lower"]), Decimal(value["upper"]),
                        value.get("lower_inclusive", True), value.get("upper_inclusive", True),
                    )
            for key in ("observed_at", "reference_at"):
                if key in item and isinstance(item[key], str):
                    item[key] = datetime.fromisoformat(item[key].replace("Z", "+00:00"))
            restored[rule_id] = item
        restored_sources = {
            rule_id: tuple(source(item) for item in source_values)
            for rule_id, source_values in sources.items()
        }
        if tuple(sorted(restored)) != tuple(sorted(sources)):
            raise ValueError("retained_input_invalid")
        return EvaluationInputV1(
            str(snapshot.execution_id), str(snapshot.snapshot_id), restored, restored_sources,
        )

    @staticmethod
    def _stage_event(
        uow, *, actor_id, project_id, assessment_id, event_type, payload,
        occurred_at,
    ):
        uow.repository.add(CrossDisciplineOutbox(
            event_id=uuid4(), assessment_id=assessment_id,
            event_type=event_type, schema_version=1,
            payload=payload, occurred_at=occurred_at,
        ))
        uow.repository.add(AuditLog(
            user_id=actor_id, action=event_type,
            entity="CROSS_DISCIPLINE_ASSESSMENT", entity_id=project_id,
            entity_uuid=assessment_id, details=payload,
        ))

    def append_disposition(
        self, *, session_factory, actor_id, actor_role, organization_id,
        project_id, assessment_id, finding_id, data,
    ):
        payload = data.model_dump(mode="json", exclude={"correlation_id"})
        request_digest = request_fingerprint("append_disposition", payload)
        last_error = None
        for _attempt in range(1, 4):
            try:
                with CrossDisciplineUnitOfWork(session_factory) as uow:
                    authorizer = SqlAlchemyCrossDisciplineAuthorizer(uow.session)
                    authorizer.authorize_scope(
                        actor_id=actor_id, role=actor_role,
                        organization_id=organization_id, project_id=project_id,
                        workspace_ids=(), mutate=True,
                    )
                    root = uow.repository.get_assessment(
                        assessment_id, organization_id, project_id, lock=True,
                    )
                    if root is None:
                        raise ProtectedResourceError()
                    workspace_ids = uow.repository.assessment_workspace_ids(
                        assessment_id=assessment_id,
                        organization_id=organization_id, project_id=project_id,
                    )
                    authorizer.authorize_scope(
                        actor_id=actor_id, role=actor_role,
                        organization_id=organization_id, project_id=project_id,
                        workspace_ids=workspace_ids, mutate=True,
                    )
                    finding = uow.repository.finding(
                        assessment_id=assessment_id, finding_id=finding_id,
                        organization_id=organization_id, project_id=project_id,
                        lock=True,
                    )
                    if finding is None:
                        raise ProtectedResourceError()
                    prior = uow.repository.get_idempotency(
                        organization_id=organization_id, project_id=project_id,
                        actor_id=actor_id, operation="append_disposition",
                        idempotency_key=data.idempotency_key, lock=True,
                    )
                    if prior is not None:
                        return dict(prior.response_json) if prior.request_digest == request_digest else {"outcome": "idempotency_conflict"}
                    current = uow.repository.current_view(
                        assessment_id=assessment_id, finding_id=finding_id,
                        organization_id=organization_id, project_id=project_id,
                        lock=True,
                    )
                    accepted_decision = False
                    if data.accepted_decision_id is not None:
                        accepted_decision = uow.session.scalar(select(ProjectDecision.id).where(
                            ProjectDecision.id == data.accepted_decision_id,
                            ProjectDecision.organization_id == organization_id,
                            ProjectDecision.project_id == project_id,
                            ProjectDecision.standing == "accepted",
                        )) is not None
                    successor_valid = False
                    if data.successor_assessment_id is not None:
                        successor = uow.repository.get_assessment(
                            data.successor_assessment_id, organization_id, project_id,
                        )
                        successor_valid = successor is not None and successor.scope_digest == root.scope_digest
                        if successor_valid and data.successor_finding_id is not None:
                            successor_valid = uow.repository.finding(
                                assessment_id=successor.id,
                                finding_id=data.successor_finding_id,
                                organization_id=organization_id, project_id=project_id,
                            ) is not None
                    decision = disposition_transition(
                        current_state=current.current_state if current else "open",
                        action=str(data.action),
                        assessment_version=root.aggregate_version,
                        expected_assessment_version=data.expected_assessment_version,
                        view_version=current.projection_version if current else 0,
                        expected_view_version=data.expected_current_view_version,
                        accepted_decision=accepted_decision,
                        changed_source_count=len(data.changed_source_references),
                        successor_valid=successor_valid,
                    )
                    now, disposition_id = self._now(), uuid4()
                    disposition_payload = dict(payload)
                    disposition_payload.update({
                        "assessment_id": str(assessment_id),
                        "finding_id": str(finding_id),
                        "resulting_view_state": decision.resulting_state,
                    })
                    sequence = uow.repository.next_disposition_sequence(assessment_id)
                    uow.repository.add(CrossDisciplineDisposition(
                        id=disposition_id, organization_id=organization_id,
                        project_id=project_id, assessment_id=assessment_id,
                        finding_id=finding_id, sequence=sequence,
                        action=decision.action,
                        resulting_view_state=decision.resulting_state,
                        actor_id=actor_id, actor_role=actor_role,
                        rationale=data.rationale,
                        expected_assessment_version=data.expected_assessment_version,
                        expected_view_version=data.expected_current_view_version,
                        resulting_view_version=decision.next_view_version,
                        correlation_id=data.correlation_id,
                        causation_id=data.causation_id,
                        idempotency_key=data.idempotency_key,
                        payload=disposition_payload,
                        disposition_digest=digest(
                            disposition_payload,
                            "satco:xdi-disposition:v1",
                        ), created_at=now,
                    ))
                    if current is None:
                        uow.repository.add(CrossDisciplineFindingCurrent(
                            organization_id=organization_id, project_id=project_id,
                            assessment_id=assessment_id, finding_id=finding_id,
                            projection_version=decision.next_view_version,
                            latest_disposition_id=disposition_id,
                            latest_action=decision.action,
                            current_state=decision.resulting_state, updated_at=now,
                        ))
                    else:
                        current.projection_version = decision.next_view_version
                        current.latest_disposition_id = disposition_id
                        current.latest_action = decision.action
                        current.current_state = decision.resulting_state
                        current.updated_at = now
                    if not uow.repository.increment_root_version(
                        assessment_id=assessment_id,
                        organization_id=organization_id, project_id=project_id,
                        expected_version=root.aggregate_version,
                    ):
                        return {"outcome": "version_conflict"}
                    response = {
                        "outcome": "success", "disposition_id": str(disposition_id),
                        "assessment_version": decision.next_assessment_version,
                        "current_view_version": decision.next_view_version,
                        "current_state": decision.resulting_state,
                    }
                    uow.repository.add(CrossDisciplineIdempotency(
                        organization_id=organization_id, project_id=project_id,
                        actor_id=actor_id, operation="append_disposition",
                        idempotency_key=data.idempotency_key,
                        request_digest=request_digest, response_json=response,
                        response_digest=digest(response, "satco:xdi-response:v1"),
                        assessment_id=assessment_id, completed_at=now,
                    ))
                    event_payload = {
                        "schema_version": 1,
                        "organization_id": str(organization_id),
                        "project_id": project_id,
                        "assessment_id": str(assessment_id),
                        "finding_id": str(finding_id),
                        "disposition_id": str(disposition_id),
                        "action": decision.action,
                        "aggregate_version": decision.next_assessment_version,
                        "current_view_version": decision.next_view_version,
                        "correlation_id": str(data.correlation_id),
                    }
                    self._stage_event(
                        uow, actor_id=actor_id, project_id=project_id,
                        assessment_id=assessment_id,
                        event_type="cross_discipline_disposition_appended",
                        payload=event_payload, occurred_at=now,
                    )
                    uow.commit()
                    return response
            except (VersionConflict, InvalidDisposition) as error:
                reason = str(error)
                if isinstance(error, VersionConflict):
                    return {"outcome": "version_conflict"}
                return {"outcome": "invalid_request", "reason_code": reason}
            except ProtectedResourceError:
                return self.safe_protected_result()
            except BaseException as error:
                if not retryable_database_error(error):
                    raise
                last_error = error
        raise RetryExhausted("database retry limit exhausted") from last_error

    def definitions(self):
        definition = load_batch_five_definition_set()
        return {
            "items": ({
                "definition_set_id": definition.definition_set_id,
                "version": definition.version,
                "digest": definition.digest,
                "supported_combinations": definition.supported_combinations,
            },),
            "next_cursor": None,
        }

    @staticmethod
    def safe_protected_result():
        return dict(PROTECTED_RESULT)
