"""Authorized PATCH-056 read adapter. Authorization precedes every source query."""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.engineering_experience_capture_command import EngineeringExperienceCaptureActor
from app.repositories.engineering_experience_capture_unit_of_work import SqlAlchemyCaptureAuthorizationPolicy
from app.adapters.engineering_execution_plan import SqlAlchemyExecutionPlanAuthorization
from app.repositories.engineering_execution_plan_unit_of_work import SqlAlchemyEngineeringExecutionPlanUnitOfWork
from app.schemas.engineering_execution_plan import ExecutionActor, ExecutionMilestoneEvidencePage, ExecutionActivityEvidencePage
from app.services.engineering_execution_plan_service import EngineeringExecutionPlanService
from app.adapters.engineering_deliverable import SqlAlchemyDeliverableAuthorization
from app.repositories.engineering_deliverable_unit_of_work import SqlAlchemyEngineeringDeliverableUnitOfWork
from app.schemas.engineering_deliverable import DeliverableActor, DeliverableTransitionEvidencePage, DeliverableReworkEvidencePage
from app.models.evidence_command import EvidenceActor
from app.services.evidence_availability_service import EvidenceAvailabilityIncomplete, EvidenceAvailabilityService, EvidenceAvailabilitySnapshot
from app.services.engineering_deliverable_service import EngineeringDeliverableService
from app.services.engineering_performance import MilestoneEvidence
from app.dependencies.project_foundation import SqlAlchemyProjectFoundationAuthorization
from app.repositories.project_control_unit_of_work import SqlAlchemyProjectControlUnitOfWork
from app.schemas.project_control import ControlActor, ControlAgingEvidencePage
from app.services.project_control_service import ProjectControlService
from app.services.engineering_context_relationship_service import EngineeringContextRelationshipService
from app.exceptions.engineering_context_relationship import CommitmentNotFound
from app.ports.project_completeness import CompletenessActor, CompletenessAssessmentRequest
from app.models.technical_report_command import TechnicalReportActor
from app.ports.technical_report import TechnicalReportLifecycleEvidencePage
from app.exceptions.technical_report import TechnicalReportAuthorizationDenied


class EngineeringPerformanceProtectedNotFound(Exception):
    pass


@dataclass(frozen=True)
class EngineeringPerformanceScope:
    organization_id: UUID
    project_id: int
    workspace_id: int | None = None
    actor_id: int | None = None


@dataclass(frozen=True)
class ControlAgingTraversal:
    items: tuple
    source_cutoff: datetime


class EngineeringPerformanceSourceAdapter:
    def __init__(self, db: Session, authorization_policy=None, foundation_service=None, execution_service=None, deliverable_service=None, supporting_files=None, project_control_service=None, interface_commitment_service=None, completeness_service=None, technical_report_service=None, evidence_availability_service=None, current_user=None, clock=None):
        self.db = db
        self.authorization_policy = authorization_policy or SqlAlchemyCaptureAuthorizationPolicy(db)
        self.foundation_service = foundation_service
        self.execution_service = execution_service
        self.deliverable_service = deliverable_service
        self.supporting_files = supporting_files
        self.project_control_service = project_control_service
        self.interface_commitment_service = interface_commitment_service
        self.completeness_service = completeness_service
        self.technical_report_service = technical_report_service
        self.evidence_availability_service = evidence_availability_service
        self.current_user = current_user
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def authorize_scope(self, scope: EngineeringPerformanceScope) -> None:
        if scope.actor_id is None:
            raise EngineeringPerformanceProtectedNotFound()
        actor = EngineeringExperienceCaptureActor(scope.actor_id, scope.organization_id)
        policy = self.authorization_policy
        # This cross-domain aggregate currently requires whole-Project read
        # authority; Workspace-only memberships cannot authorize other sources.
        if not policy.authorize(actor=actor, operation="list", project_id=scope.project_id, workspace_id=None):
            raise EngineeringPerformanceProtectedNotFound()
        if scope.workspace_id is not None:
            if not policy.authorize(actor=actor, operation="list", project_id=scope.project_id, workspace_id=scope.workspace_id):
                raise EngineeringPerformanceProtectedNotFound()

    def required_input_standings(self, scope: EngineeringPerformanceScope) -> list[str]:
        self.authorize_scope(scope)
        if self.foundation_service is None:
            raise RuntimeError("canonical Project Foundation service is required")
        from app.schemas.project_foundation import ProjectFoundationActor
        result = self.foundation_service.get(
            project_id=scope.project_id,
            actor=ProjectFoundationActor(actor_id=scope.actor_id, organization_id=scope.organization_id),
        )
        if getattr(result, "outcome", None) == "protected_not_found":
            raise EngineeringPerformanceProtectedNotFound()
        if getattr(result, "availability", None) == "basis_not_established":
            return ["source_not_established"]
        if getattr(result, "availability", None) != "established":
            return ["source_unavailable"]
        return [
            "protected" if item.standing == "received" and item.source_condition != "authorized_current"
            else str(item.standing.value if hasattr(item.standing, "value") else item.standing)
            for item in result.inputs
        ]

    def execution_activity_rows(self, scope: EngineeringPerformanceScope):
        self.authorize_scope(scope)
        result = self._execution_service().list_authorized_activity_evidence(
            project_id=scope.project_id,
            actor=ExecutionActor(actor_id=scope.actor_id, organization_id=scope.organization_id),
        )
        if not isinstance(result, ExecutionActivityEvidencePage):
            raise EngineeringPerformanceProtectedNotFound()
        return tuple(row for row in result.items if scope.workspace_id is None or row.workspace_id == scope.workspace_id)

    def _execution_service(self):
        if self.execution_service is not None:
            return self.execution_service
        return EngineeringExecutionPlanService(
            uow_factory=lambda: SqlAlchemyEngineeringExecutionPlanUnitOfWork(self.db),
            authorization=SqlAlchemyExecutionPlanAuthorization(self.db), foundation=None,
        )

    def milestone_rows(self, scope: EngineeringPerformanceScope):
        self.authorize_scope(scope)
        result = self._execution_service().list_authorized_milestone_evidence(
            project_id=scope.project_id,
            actor=ExecutionActor(actor_id=scope.actor_id, organization_id=scope.organization_id),
        )
        if not isinstance(result, ExecutionMilestoneEvidencePage):
            raise EngineeringPerformanceProtectedNotFound()
        return tuple(MilestoneEvidence(
            target_date=row.target_date, standing=row.standing.value,
            actual_completed_at=row.actual_completed_at,
            forecast_completion_at=row.forecast_completion_at,
            source_handle=f"execution_milestone:{row.id}",
            limitations=row.limitations,
        ) for row in result.items if scope.workspace_id is None or scope.workspace_id in row.workspace_ids)

    def deliverable_transition_rows(self, scope: EngineeringPerformanceScope):
        self.authorize_scope(scope)
        service = self.deliverable_service or EngineeringDeliverableService(
            uow_factory=lambda: SqlAlchemyEngineeringDeliverableUnitOfWork(self.db),
            authorization=SqlAlchemyDeliverableAuthorization(self.db),
            supporting_files=self.supporting_files,
        )
        result = service.list_authorized_transition_evidence(
            project_id=scope.project_id, workspace_id=scope.workspace_id,
            actor=DeliverableActor(actor_id=scope.actor_id, organization_id=scope.organization_id),
        )
        if getattr(result, "outcome", None) == "protected_not_found":
            raise EngineeringPerformanceProtectedNotFound()
        if not isinstance(result, DeliverableTransitionEvidencePage):
            return None
        return result.items

    def deliverable_rework_rows(self, scope: EngineeringPerformanceScope, *, source_cutoff: datetime):
        self.authorize_scope(scope)
        service = self.deliverable_service or EngineeringDeliverableService(
            uow_factory=lambda: SqlAlchemyEngineeringDeliverableUnitOfWork(self.db),
            authorization=SqlAlchemyDeliverableAuthorization(self.db),
            supporting_files=self.supporting_files,
        )
        result = service.list_authorized_rework_evidence(
            project_id=scope.project_id, workspace_id=scope.workspace_id,
            actor=DeliverableActor(actor_id=scope.actor_id, organization_id=scope.organization_id),
            source_cutoff=source_cutoff,
        )
        if getattr(result, "outcome", None) == "protected_not_found":
            raise EngineeringPerformanceProtectedNotFound()
        if not isinstance(result, DeliverableReworkEvidencePage) or result.source_cutoff != source_cutoff:
            return None
        return result.items

    def evidence_availability_rows(self, scope: EngineeringPerformanceScope, *, source_cutoff: datetime):
        """Traverse only canonical Evidence-authorized pages, never raw candidates."""
        self.authorize_scope(scope)
        service = self.evidence_availability_service
        if service is None:
            return None
        items, cursor, seen_cursors, seen_ids = [], None, set(), set()
        actor = EvidenceActor(scope.actor_id, scope.organization_id)
        for _ in range(100):
            try:
                page = service.list_page(
                    actor=actor, project_id=scope.project_id,
                    workspace_id=scope.workspace_id, source_cutoff=source_cutoff,
                    page_size=50, cursor=cursor,
                )
            except EvidenceAvailabilityIncomplete:
                return None
            except Exception as exc:
                from app.exceptions.evidence import EvidenceProtectedNotFound
                if isinstance(exc, EvidenceProtectedNotFound):
                    raise EngineeringPerformanceProtectedNotFound() from None
                return None
            if (page.source_cutoff != source_cutoff
                    or page.traversal_complete != (page.next_cursor is None)
                    or (not page.traversal_complete and len(page.items) != 50)):
                return None
            for item in page.items:
                if (item.evidence_id in seen_ids or item.source_cutoff != source_cutoff
                        or (item.project_id not in {None, scope.project_id})
                        or (scope.workspace_id is not None and item.workspace_id != scope.workspace_id)):
                    return None
                seen_ids.add(item.evidence_id)
                items.append(item)
            if page.traversal_complete:
                return tuple(items)
            if page.next_cursor in seen_cursors:
                return None
            seen_cursors.add(page.next_cursor)
            cursor = page.next_cursor
        return None

    def issue_evidence_availability_snapshot(self, scope: EngineeringPerformanceScope):
        """Invoke the authorized owner operation; PATCH-056 never probes storage itself."""
        self.authorize_scope(scope)
        service = self.evidence_availability_service
        if service is None:
            return None
        try:
            result = service.issue_snapshot(
                actor=EvidenceActor(scope.actor_id, scope.organization_id),
                project_id=scope.project_id, workspace_id=scope.workspace_id,
            )
        except EvidenceAvailabilityIncomplete:
            return None
        except Exception as exc:
            from app.exceptions.evidence import EvidenceProtectedNotFound
            if isinstance(exc, EvidenceProtectedNotFound):
                raise EngineeringPerformanceProtectedNotFound() from None
            return None
        return result if isinstance(result, EvidenceAvailabilitySnapshot) else None

    def control_aging_rows(self, scope: EngineeringPerformanceScope):
        """Only complete owner-authorized traversals are eligible for aggregation."""
        self.authorize_scope(scope)
        service = self.project_control_service or ProjectControlService(
            uow_factory=lambda: SqlAlchemyProjectControlUnitOfWork(self.db),
            authorization=SqlAlchemyProjectFoundationAuthorization(self.db),
        )
        cutoff = self.clock()
        items = []
        actor = ControlActor(actor_id=scope.actor_id, organization_id=scope.organization_id)
        for kind in ("risk", "issue", "change"):
            continuation = None
            seen_cursors = set()
            seen_ids = set()
            for _ in range(100):
                result = service.list_authorized_aging_evidence(
                    kind=kind, project_id=scope.project_id, workspace_id=scope.workspace_id,
                    actor=actor, page_size=100, continuation=continuation,
                    source_cutoff=cutoff if continuation is None else None,
                )
                if getattr(result, "outcome", None) == "protected_not_found":
                    raise EngineeringPerformanceProtectedNotFound()
                if not isinstance(result, ControlAgingEvidencePage):
                    return None
                if (result.kind != kind or result.source_cutoff != cutoff
                        or result.complete != (result.next_continuation is None)
                        or (not result.complete and len(result.items) != 100)):
                    return None
                for row in result.items:
                    if (row.id in seen_ids or row.kind != kind
                            or row.organization_id != scope.organization_id
                            or row.project_id != scope.project_id
                            or (scope.workspace_id is not None and row.workspace_id != scope.workspace_id)):
                        return None
                    seen_ids.add(row.id)
                    items.append(row)
                if result.complete:
                    break
                if result.next_continuation in seen_cursors:
                    return None
                seen_cursors.add(result.next_continuation)
                continuation = result.next_continuation
            else:
                return None
        return ControlAgingTraversal(tuple(items), cutoff)

    def interface_commitment_rows(self, scope: EngineeringPerformanceScope):
        self.authorize_scope(scope)
        if self.current_user is None or self.current_user.id != scope.actor_id:
            raise EngineeringPerformanceProtectedNotFound()
        service = self.interface_commitment_service or EngineeringContextRelationshipService(self.db)
        try:
            result = service.list_authorized_due_evidence(
                project_id=scope.project_id, workspace_id=scope.workspace_id,
                current_user=self.current_user,
            )
        except CommitmentNotFound:
            raise EngineeringPerformanceProtectedNotFound() from None
        if result.get("outcome") != "success":
            return None
        if result.get("population_scope") != "actor_visible_only":
            return None
        if result.get("source_cutoff") is None:
            return None
        return result

    def completeness_history(self, scope: EngineeringPerformanceScope, *, window_days: int):
        self.authorize_scope(scope)
        if (self.current_user is None or self.current_user.id != scope.actor_id
                or self.completeness_service is None):
            raise EngineeringPerformanceProtectedNotFound()
        result = self.completeness_service.list_authorized_observation_history(
            actor=CompletenessActor(scope.actor_id, scope.organization_id),
            request=CompletenessAssessmentRequest(scope.project_id, scope.workspace_id),
            current_user=self.current_user, window_days=window_days,
        )
        if result.get("outcome") == "protected_not_found":
            raise EngineeringPerformanceProtectedNotFound()
        if result.get("outcome") != "success":
            return None
        rows = result.get("observations")
        if (not isinstance(rows, tuple) or len(rows) > 1000
                or any(not isinstance(row, dict)
                       or row.get("organization_id") != scope.organization_id
                       or row.get("project_id") != scope.project_id
                       or row.get("workspace_id") != scope.workspace_id
                       for row in rows)):
            return None
        return result

    def technical_report_rows(self, scope: EngineeringPerformanceScope):
        self.authorize_scope(scope)
        if self.technical_report_service is None:
            return None
        try:
            result = self.technical_report_service.list_authorized_lifecycle_evidence(
                actor=TechnicalReportActor(scope.actor_id, scope.organization_id),
                project_id=scope.project_id, workspace_id=scope.workspace_id,
            )
        except TechnicalReportAuthorizationDenied:
            raise EngineeringPerformanceProtectedNotFound() from None
        if not isinstance(result, TechnicalReportLifecycleEvidencePage) or not result.complete:
            return None
        if (result.source_cutoff.tzinfo is None or len(result.items) > 1000
                or any(row.organization_id != scope.organization_id
                       or row.project_id != scope.project_id
                       or (scope.workspace_id is not None and row.workspace_id != scope.workspace_id)
                       for row in result.items)):
            return None
        return result
