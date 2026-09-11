"""Governed orchestration primitives for PATCH-053 Batch 1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable
from uuid import UUID, uuid4

from sqlalchemy import select

from app.adapters.cross_discipline_sources import SqlAlchemyCrossDisciplineAuthorizer
from app.discipline_packages.cross_discipline.canonical import canonical_json, digest
from app.discipline_packages.cross_discipline.definitions.eic_v1 import (
    load_batch_four_definition_set, load_batch_one_definition_set, load_batch_three_definition_set, load_batch_two_definition_set,
    validate_batch_four_definition_set, validate_batch_three_definition_set, validate_batch_two_definition_set,
)
from app.discipline_packages.cross_discipline.evaluator import GenericEvaluator, batch_four_evaluator, batch_three_evaluator, batch_two_evaluator
from app.discipline_packages.cross_discipline.contracts import EvaluationInputV1
from app.models.audit_log import AuditLog
from app.models.discipline_package import RegistryRelease
from app.models.project_control import ProjectDecision
from app.models.cross_discipline_intelligence import (
    CrossDisciplineAssessment, CrossDisciplineAssessmentWorkspace,
    CrossDisciplineDisposition, CrossDisciplineFindingCurrent,
    CrossDisciplineIdempotency, CrossDisciplineLineage,
    CrossDisciplineOutbox, CrossDisciplineSnapshot,
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

    def __init__(self, *, evaluator=None, now=None):
        # The generic, zero-rule evaluator is a retained Batch-1 artifact.
        # Batch-2 is deliberately opt-in so historical creation/replay keeps
        # resolving its exact Batch-1 definition and evaluator identity.
        self.evaluator = evaluator or GenericEvaluator()
        self._batch_two_evaluator = batch_two_evaluator()
        self._batch_three_evaluator = batch_three_evaluator()
        self._batch_four_evaluator = batch_four_evaluator()
        self._now = now or (lambda: datetime.now(timezone.utc))

    def readiness(self, session=None):
        try:
            definition = load_batch_four_definition_set()
            validate_batch_four_definition_set(definition)
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
            return self.unsupported_create()
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
                    replay = self.evaluator.evaluate(EvaluationInputV1(
                        str(snapshot.execution_id), str(snapshot.snapshot_id), {},
                    ))
                    if replay.result_digest != snapshot.result_digest:
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
        definition = load_batch_one_definition_set()
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
