"""Authorized PATCH-032 Technical Report application orchestration."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Callable
from uuid import UUID

from app.enums.technical_report import TechnicalReportLifecycle, TechnicalReportSourceClass
from app.exceptions.technical_report import (
    TechnicalReportAcceptanceAuthorityDenied,
    TechnicalReportAcceptedImmutable,
    TechnicalReportAssistantUnavailable,
    TechnicalReportAuthorizationDenied,
    TechnicalReportVersionConflict,
)
from app.models.technical_report import TechnicalReport
from app.models.technical_report_command import (
    AcceptExactTechnicalReportDraft,
    CaptureHistoricalBasisV1,
    CreateTechnicalReportDraft,
    CreateTechnicalReportSuccessor,
    EngineeringObjectHistoricalBasisV1,
    EngineeringRelationshipHistoricalBasisV1,
    EvidenceHistoricalBasisV1,
    EvidenceHistoricalBasisV2,
    ReviseTechnicalReportDraft,
    TechnicalReportActor,
    TechnicalReportCommandResult,
    TechnicalReportProvenanceEntry,
    canonical_json,
)
from app.ports.technical_report import (
    AcceptExactDraftHistoricalAuthority,
    CreateDraftHistoricalAuthority,
    CreateSuccessorHistoricalAuthority,
    ReviseDraftHistoricalAuthority,
    RequestAIProposalHistoricalAuthority,
    TechnicalReportAIProposal,
    TechnicalReportAIRequest,
    AcceptedTechnicalReportSummary,
    AcceptedTechnicalReportSummaryPage,
    TechnicalReportGraphProvenanceLink,
    TechnicalReportAuditRecord,
    TechnicalReportAuthorizationRequest,
    TechnicalReportClock,
    TechnicalReportDraftAssistant,
    TechnicalReportFinalRecheckRequest,
    TechnicalReportHistoricalRequest,
    TechnicalReportIdempotencyKey,
    TechnicalReportReadCriteria,
    TechnicalReportReadPage,
    TechnicalReportReferenceRequest,
    TechnicalReportRejectionAuditRecord,
    TechnicalReportRejectionReason,
    TechnicalReportScope,
    TechnicalReportUnitOfWork,
)


@dataclass(frozen=True, slots=True)
class TechnicalReportLineage:
    subject: TechnicalReport
    predecessor: TechnicalReport | None
    successors: TechnicalReportReadPage


@dataclass(frozen=True, slots=True)
class TechnicalReportMutationResponse:
    report: object
    result: TechnicalReportCommandResult

    @property
    def report_id(self): return self.result.report_id
    @property
    def version(self): return self.result.version
    @property
    def draft_revision(self): return self.result.draft_revision


@dataclass(frozen=True, slots=True)
class TechnicalReportDetailPage:
    items: tuple[object, ...]
    total: int
    page: int
    size: int


@dataclass(frozen=True, slots=True)
class TechnicalReportDetailedLineage:
    subject: object
    predecessor: object | None
    successors: TechnicalReportDetailPage


@dataclass(frozen=True, slots=True)
class TechnicalReportResponseState:
    """Application projection reconstructed without persisting response plaintext."""

    id: UUID
    organization_id: UUID
    workspace_id: int
    project_id: int | None
    owner_id: int
    purpose: object
    content: object
    qualification: object
    provenance: tuple[TechnicalReportProvenanceEntry, ...]
    draft_revision: object
    lifecycle: TechnicalReportLifecycle
    predecessor_report_id: UUID | None
    version: int
    created_at: datetime
    updated_at: datetime
    accepted_snapshot: object | None = None
    acceptance_record: object | None = None
    allowed_actions: tuple[str, ...] = ()

    @property
    def draft_revision_id(self): return self.draft_revision.revision_id


@dataclass(frozen=True, slots=True)
class TechnicalReportAuthorizedView:
    report: TechnicalReport
    allowed_actions: tuple[str, ...]

    def __getattr__(self, name):
        return getattr(self.report, name)


_CANONICAL_LOCATORS = (
    CaptureHistoricalBasisV1,
    EvidenceHistoricalBasisV1,
    EvidenceHistoricalBasisV2,
    EngineeringObjectHistoricalBasisV1,
    EngineeringRelationshipHistoricalBasisV1,
)


class TechnicalReportService:
    """Coordinate ports and one Aggregate command without owning domain policy."""

    def __init__(
        self,
        uow_factory: Callable[[], TechnicalReportUnitOfWork],
        clock: TechnicalReportClock,
        assistant: TechnicalReportDraftAssistant | None = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._clock = clock
        self._assistant = assistant

    def create_draft(self, command: CreateTechnicalReportDraft):
        scope = TechnicalReportScope(
            command.organization_id, command.workspace_id, command.project_id
        )
        authority = CreateDraftHistoricalAuthority()
        uow = self._uow_factory()
        try:
            with uow:
                uow.authorization.require(
                    TechnicalReportAuthorizationRequest(
                        command.metadata.actor, "create_draft", scope
                    )
                )
                self._validate_provenance(uow, command.metadata.actor, scope, authority, command.provenance)
                replay, key, fingerprint = self._idempotency(uow, command)
                if replay is not None:
                    report = uow.technical_reports.get_scoped(replay.report_id, command.organization_id)
                    if report is None: raise TechnicalReportAuthorizationDenied()
                    state = self._replay_state(command, replay, report)
                    return TechnicalReportMutationResponse(self._view(uow, command.metadata.actor, state), replay)
                uow.idempotency.reserve(key, fingerprint)
                report, result = TechnicalReport.create(command, self._clock.now())
                uow.technical_reports.add(report)
                self._stage_success(uow, command, result)
                uow.commit()
                return TechnicalReportMutationResponse(self._view(uow, command.metadata.actor, report), result)
        except TechnicalReportAuthorizationDenied:
            if command.organization_id != command.metadata.actor.organization_id:
                self._record_rejection(uow, command, TechnicalReportRejectionReason.CROSS_ORGANIZATION)
            raise

    def revise_draft(self, command: ReviseTechnicalReportDraft):
        uow = self._uow_factory()
        try:
            with uow:
                report, scope = self._protected_report(uow, command.metadata.actor, command.report_id, "revise_draft")
                replay, key, fingerprint = self._idempotency(uow, command)
                if replay is not None:
                    state = self._replay_state(command, replay, report)
                    return TechnicalReportMutationResponse(self._view(uow, command.metadata.actor, state), replay)
                authority = ReviseDraftHistoricalAuthority(report.id, report.owner_id)
                self._validate_provenance(uow, command.metadata.actor, scope, authority, command.provenance)
                uow.idempotency.reserve(key, fingerprint)
                result = report.revise(command, self._clock.now())
                if not uow.technical_reports.persist_draft_expected_version(report, command.expected_version):
                    raise TechnicalReportVersionConflict()
                self._stage_success(uow, command, result)
                uow.commit()
                return TechnicalReportMutationResponse(self._view(uow, command.metadata.actor, report), result)
        except TechnicalReportAcceptedImmutable:
            self._record_rejection(uow, command, TechnicalReportRejectionReason.ACCEPTED_STATE_MUTATION, command.report_id)
            raise

    def accept_exact_draft(self, command: AcceptExactTechnicalReportDraft):
        uow = self._uow_factory()
        try:
            with uow:
                report, scope = self._protected_report(uow, command.metadata.actor, command.report_id, "accept_exact_draft")
                replay, key, fingerprint = self._idempotency(uow, command)
                if replay is not None:
                    state = self._replay_state(command, replay, report)
                    return TechnicalReportMutationResponse(self._view(uow, command.metadata.actor, state), replay)
                authority = AcceptExactDraftHistoricalAuthority(report.id, report.owner_id)
                requests = self._validate_provenance(
                    uow, command.metadata.actor, scope, authority, report.provenance
                )
                uow.idempotency.reserve(key, fingerprint)
                uow.final_recheck.require_current(
                    TechnicalReportFinalRecheckRequest(
                        actor=command.metadata.actor,
                        scope=scope,
                        report_id=report.id,
                        owner_id=report.owner_id,
                        expected_version=command.confirmation.expected_version,
                        expected_draft_revision_id=command.confirmation.exact_draft_revision_id,
                        sources=requests,
                    )
                )
                result = report.accept_exact_draft(command, self._clock.now())
                if not uow.technical_reports.persist_acceptance_expected_version(
                    report, command.confirmation.expected_version
                ):
                    raise TechnicalReportVersionConflict()
                self._stage_success(uow, command, result)
                uow.commit()
                return TechnicalReportMutationResponse(self._view(uow, command.metadata.actor, report), result)
        except TechnicalReportAcceptanceAuthorityDenied:
            self._record_rejection(uow, command, TechnicalReportRejectionReason.NON_OWNER_ACCEPTANCE)
            raise
        except TechnicalReportAcceptedImmutable:
            self._record_rejection(
                uow,
                command,
                TechnicalReportRejectionReason.ACCEPTED_STATE_MUTATION,
                command.report_id,
            )
            raise

    def create_successor(self, command: CreateTechnicalReportSuccessor):
        with self._uow_factory() as uow:
            predecessor, scope = self._protected_report(
                uow, command.metadata.actor, command.predecessor_report_id, "create_successor"
            )
            authority = CreateSuccessorHistoricalAuthority(predecessor.id, True)
            selected_by_id = {item.entry_id: item for item in predecessor.provenance}
            try:
                selected = tuple(selected_by_id[item] for item in command.selected_copy_references)
            except KeyError as exc:
                raise TechnicalReportAuthorizationDenied() from exc
            self._validate_provenance(uow, command.metadata.actor, scope, authority, selected)
            self._validate_provenance(uow, command.metadata.actor, scope, authority, command.provenance)
            combined = command.provenance + selected
            if len({item.entry_id for item in combined}) != len(combined):
                raise TechnicalReportAuthorizationDenied()
            combined = tuple(replace(item, ordinal=index) for index, item in enumerate(combined))
            effective_command = replace(command, provenance=combined)
            replay, key, fingerprint = self._idempotency(uow, command)
            if replay is not None:
                report = uow.technical_reports.get_scoped(replay.report_id, command.metadata.actor.organization_id)
                if report is None: raise TechnicalReportAuthorizationDenied()
                state = self._replay_state(effective_command, replay, report)
                return TechnicalReportMutationResponse(self._view(uow, command.metadata.actor, state), replay)
            uow.idempotency.reserve(key, fingerprint)
            successor, result = predecessor.create_successor(effective_command, self._clock.now())
            uow.technical_reports.add(successor)
            self._stage_success(uow, command, result)
            uow.commit()
            return TechnicalReportMutationResponse(self._view(uow, command.metadata.actor, successor), result)

    def get_report(self, actor: TechnicalReportActor, report_id: UUID) -> TechnicalReport:
        with self._uow_factory() as uow:
            report, _ = self._protected_report(uow, actor, report_id, "get")
            return self._view(uow, actor, report)

    def list_reports(self, actor: TechnicalReportActor, criteria: TechnicalReportReadCriteria) -> TechnicalReportReadPage:
        with self._uow_factory() as uow:
            uow.authorization.require(
                TechnicalReportAuthorizationRequest(actor, "list", criteria.scope)
            )
            return uow.technical_reports.list_scoped(criteria)

    def list_accepted_summaries(
        self, actor: TechnicalReportActor, criteria: TechnicalReportReadCriteria,
    ) -> AcceptedTechnicalReportSummaryPage:
        """Return only the accepted safe projection for a bounded owner read."""
        if not 1 <= criteria.page or not 1 <= criteria.size <= 100:
            raise TechnicalReportAuthorizationDenied()
        accepted_criteria = replace(
            criteria, lifecycle=TechnicalReportLifecycle.ACCEPTED,
        )
        with self._uow_factory() as uow:
            uow.authorization.require(
                TechnicalReportAuthorizationRequest(
                    actor, "list_accepted_summaries", accepted_criteria.scope,
                )
            )
            page = uow.technical_reports.list_scoped(accepted_criteria)
            summaries = []
            for item in page.items:
                report = uow.technical_reports.get_scoped(
                    item.report_id, actor.organization_id,
                )
                if report is None or report.lifecycle is not TechnicalReportLifecycle.ACCEPTED:
                    raise TechnicalReportAuthorizationDenied()
                record = report.acceptance_record
                if record is None or report.accepted_at is None:
                    raise TechnicalReportAuthorizationDenied()
                summaries.append(AcceptedTechnicalReportSummary(
                    report_id=report.id,
                    workspace_id=report.workspace_id,
                    project_id=report.project_id,
                    version=report.version,
                    accepted_digest=record.snapshot_digest,
                    accepted_at=report.accepted_at,
                    purpose=report.purpose,
                ))
            return AcceptedTechnicalReportSummaryPage(
                items=tuple(summaries), page=page.page, size=page.size,
                has_more=page.total > page.page * page.size,
            )

    def list_authorized_graph_provenance(self, *, actor, scope, source_kind, source_id):
        """One bounded canonical-owner read for report provenance incidence."""
        if source_kind not in {"evidence","engineering_object"}: raise TechnicalReportAuthorizationDenied()
        with self._uow_factory() as uow:
            uow.authorization.require(TechnicalReportAuthorizationRequest(actor,"list",scope))
            links=uow.technical_reports.list_graph_provenance_links(scope=scope,source_kind=source_kind,source_id=source_id,limit=91)
            visible=[]
            for link in links:
                report,_=self._protected_report(uow,actor,link.report_id,"get")
                if report.lifecycle is TechnicalReportLifecycle.ACCEPTED:visible.append(link)
            return tuple(visible)

    def list_report_details(self, actor, criteria):
        with self._uow_factory() as uow:
            uow.authorization.require(TechnicalReportAuthorizationRequest(actor, "list", criteria.scope))
            page = uow.technical_reports.list_scoped(criteria)
            items = []
            for item in page.items:
                report = uow.technical_reports.get_scoped(item.report_id, actor.organization_id)
                if report is None: raise TechnicalReportAuthorizationDenied()
                items.append(self._view(uow, actor, report))
            return TechnicalReportDetailPage(tuple(items), page.total, page.page, page.size)

    def retrieve_lineage(
        self, actor: TechnicalReportActor, report_id: UUID, *, page: int = 1, size: int = 100
    ) -> TechnicalReportLineage:
        with self._uow_factory() as uow:
            subject, _ = self._protected_report(uow, actor, report_id, "retrieve_lineage")
            predecessor = None
            if subject.predecessor_report_id is not None:
                predecessor, _ = self._protected_report(
                    uow, actor, subject.predecessor_report_id, "retrieve_lineage"
                )
            criteria = TechnicalReportReadCriteria(
                TechnicalReportScope(subject.organization_id, subject.workspace_id, subject.project_id),
                page,
                size,
            )
            raw = uow.technical_reports.list_successors_scoped(subject.id, criteria)
            for item in raw.items:
                self._protected_report(uow, actor, item.report_id, "retrieve_lineage")
            return TechnicalReportLineage(subject, predecessor, raw)

    def retrieve_lineage_details(self, actor, report_id, *, page=1, size=100):
        with self._uow_factory() as uow:
            subject, _ = self._protected_report(uow, actor, report_id, "retrieve_lineage")
            predecessor = None
            if subject.predecessor_report_id is not None:
                predecessor, _ = self._protected_report(uow, actor, subject.predecessor_report_id, "retrieve_lineage")
            criteria = TechnicalReportReadCriteria(
                TechnicalReportScope(subject.organization_id, subject.workspace_id, subject.project_id), page, size
            )
            raw = uow.technical_reports.list_successors_scoped(subject.id, criteria)
            successors = []
            for item in raw.items:
                successor, _ = self._protected_report(uow, actor, item.report_id, "retrieve_lineage")
                successors.append(self._view(uow, actor, successor))
            return TechnicalReportDetailedLineage(
                self._view(uow, actor, subject),
                None if predecessor is None else self._view(uow, actor, predecessor),
                TechnicalReportDetailPage(tuple(successors), raw.total, raw.page, raw.size),
            )

    def request_ai_proposal(
        self,
        actor: TechnicalReportActor,
        report_id: UUID,
        *,
        expected_version: int,
        expected_draft_revision_id: UUID,
        human_instruction: str,
        selected_source_entry_ids: tuple[UUID, ...] = (),
    ) -> TechnicalReportAIProposal:
        if self._assistant is None:
            raise TechnicalReportAssistantUnavailable()
        with self._uow_factory() as uow:
            report, _ = self._protected_report(uow, actor, report_id, "request_ai_proposal")
            if (
                report.lifecycle is not TechnicalReportLifecycle.DRAFT
                or report.version != expected_version
                or report.draft_revision_id != expected_draft_revision_id
            ):
                raise TechnicalReportVersionConflict()
            if len(selected_source_entry_ids) != len(set(selected_source_entry_ids)):
                raise TechnicalReportAuthorizationDenied()
            selected = {
                entry.entry_id: entry for entry in report.provenance
                if entry.entry_id in selected_source_entry_ids
            }
            if len(selected) != len(set(selected_source_entry_ids)):
                raise TechnicalReportAuthorizationDenied()
            authority = RequestAIProposalHistoricalAuthority(report.id, report.owner_id)
            self._validate_provenance(
                uow, actor, TechnicalReportScope(
                    report.organization_id, report.workspace_id, report.project_id
                ), authority, tuple(selected[item] for item in selected_source_entry_ids)
            )
            bounded_context = (
                human_instruction,
                canonical_json({
                    "report_id": report.id,
                    "purpose": report.purpose,
                    "workspace_id": report.workspace_id,
                    "project_id": report.project_id,
                    "version": report.version,
                    "draft_revision_id": report.draft_revision_id,
                    "draft_content": report.content,
                }).decode("utf-8"),
                *(canonical_json(selected[item].locator).decode("utf-8") for item in selected_source_entry_ids),
            )
        return self._assistant.propose(
            TechnicalReportAIRequest(actor, report_id, bounded_context)
        )

    @staticmethod
    def _replay_state(command, result, current):
        """Reconstruct the original safe response from request plus stored facts."""

        if isinstance(command, AcceptExactTechnicalReportDraft):
            if current.version != result.version or current.lifecycle is not TechnicalReportLifecycle.ACCEPTED:
                raise TechnicalReportVersionConflict()
            return current
        if isinstance(command, CreateTechnicalReportDraft):
            return TechnicalReportResponseState(
                result.report_id, command.organization_id, command.workspace_id,
                command.project_id, command.owner_id, command.purpose,
                command.content, command.qualification, command.provenance,
                result.draft_revision, result.safe_lifecycle, None, result.version,
                result.occurred_at, result.occurred_at,
            )
        if isinstance(command, ReviseTechnicalReportDraft):
            return TechnicalReportResponseState(
                result.report_id, current.organization_id, current.workspace_id,
                current.project_id, current.owner_id, current.purpose,
                command.content, command.qualification, command.provenance,
                result.draft_revision, result.safe_lifecycle,
                current.predecessor_report_id, result.version,
                current.created_at, result.occurred_at,
            )
        if isinstance(command, CreateTechnicalReportSuccessor):
            return TechnicalReportResponseState(
                result.report_id, command.metadata.actor.organization_id,
                command.workspace_id, command.project_id,
                command.metadata.actor.actor_id, command.purpose,
                command.content, command.qualification, command.provenance,
                result.draft_revision, result.safe_lifecycle,
                command.predecessor_report_id, result.version,
                result.occurred_at, result.occurred_at,
            )
        raise TechnicalReportAuthorizationDenied()

    @staticmethod
    def _view(uow, actor, report):
        actions: list[str] = []
        candidates = (
            (("revise_draft", "revise"), ("accept_exact_draft", "accept"),
             ("request_ai_proposal", "request_ai_proposal"))
            if report.lifecycle is TechnicalReportLifecycle.DRAFT
            else (("create_successor", "create_successor"),)
        )
        scope = TechnicalReportScope(
            report.organization_id, report.workspace_id, report.project_id
        )
        for operation, action in candidates:
            try:
                uow.authorization.require(TechnicalReportAuthorizationRequest(
                    actor, operation, scope, report.id
                ))
            except TechnicalReportAuthorizationDenied:
                continue
            actions.append(action)
        if isinstance(report, TechnicalReportResponseState):
            return replace(report, allowed_actions=tuple(actions))
        return TechnicalReportAuthorizedView(report, tuple(actions))

    def _protected_report(self, uow, actor, report_id, operation):
        report = uow.technical_reports.get_scoped(report_id, actor.organization_id)
        if report is None:
            raise TechnicalReportAuthorizationDenied()
        scope = TechnicalReportScope(report.organization_id, report.workspace_id, report.project_id)
        uow.authorization.require(
            TechnicalReportAuthorizationRequest(actor, operation, scope, report.id)
        )
        return report, scope

    def _validate_provenance(self, uow, actor, scope, authority, entries):
        requests = []
        for entry in entries:
            if entry.source_class is not TechnicalReportSourceClass.CANONICAL_MATERIAL:
                continue
            request = self._historical_request(actor, scope, authority, entry)
            uow.references.validate(
                TechnicalReportReferenceRequest(
                    actor, scope, request.source_type, request.source_id
                )
            )
            resolved = uow.historical.resolve(request)
            if resolved != entry.locator:
                raise TechnicalReportAuthorizationDenied()
            requests.append(request)
        return tuple(requests)

    @staticmethod
    def _historical_request(actor, scope, authority, entry):
        locator = entry.locator
        if not isinstance(locator, _CANONICAL_LOCATORS):
            raise TechnicalReportAuthorizationDenied()
        if isinstance(locator, CaptureHistoricalBasisV1): identity = locator.capture_id
        elif isinstance(locator, (EvidenceHistoricalBasisV1, EvidenceHistoricalBasisV2)): identity = locator.evidence_id
        elif isinstance(locator, EngineeringObjectHistoricalBasisV1): identity = locator.engineering_object_id
        else: identity = locator.engineering_relationship_id
        return TechnicalReportHistoricalRequest(
            actor, scope, authority, entry.source_type.value, identity, locator.source_version
        )

    @staticmethod
    def _idempotency(uow, command):
        metadata = command.metadata
        key = TechnicalReportIdempotencyKey(
            metadata.actor.organization_id,
            metadata.actor.actor_id,
            type(command).__name__,
            metadata.idempotency_id,
        )
        fingerprint = hashlib.sha256(canonical_json(command)).hexdigest()
        return uow.idempotency.find(key, fingerprint), key, fingerprint

    def _stage_success(self, uow, command, result):
        metadata = command.metadata
        now = self._clock.now()
        uow.audit.record(
            TechnicalReportAuditRecord(
                metadata.actor.actor_id,
                metadata.actor.organization_id,
                result.report_id,
                type(command).__name__,
                metadata.command_id,
                metadata.correlation_id,
                now,
            )
        )
        uow.domain_events.record(result.events)
        key = TechnicalReportIdempotencyKey(
            metadata.actor.organization_id,
            metadata.actor.actor_id,
            type(command).__name__,
            metadata.idempotency_id,
        )
        uow.idempotency.record_result(key, result)

    def _record_rejection(self, uow, command, reason, report_id=None):
        metadata = command.metadata
        try:
            uow.rejection_audit.record_rejection(
                TechnicalReportRejectionAuditRecord(
                    actor_id=metadata.actor.actor_id,
                    organization_id=metadata.actor.organization_id,
                    operation=type(command).__name__,
                    reason=reason,
                    report_id=report_id,
                    command_id=metadata.command_id,
                    correlation_id=metadata.correlation_id,
                    occurred_at=self._clock.now(),
                )
            )
        except Exception:
            pass
