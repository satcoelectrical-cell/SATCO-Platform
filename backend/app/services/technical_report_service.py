"""Authorized PATCH-032 Technical Report application orchestration."""

from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Callable
from uuid import UUID, uuid4

from app.enums.technical_report import (
    TechnicalReportAvailabilityStatus,
    TechnicalReportIntegrityAlgorithm,
    TechnicalReportLifecycle,
    TechnicalReportSourceClass,
    TechnicalReportSourceType,
    TechnicalReportVerificationStatus,
)
from app.exceptions.technical_report import (
    TechnicalReportAcceptanceAuthorityDenied,
    TechnicalReportAcceptedImmutable,
    TechnicalReportAssistantUnavailable,
    TechnicalReportAuthorizationDenied,
    TechnicalReportHistoricalBasisIncomplete,
    TechnicalReportVersionConflict,
)
from app.models.technical_report import TechnicalReport
from app.standards.handles import issue_handle
from app.ai.technical_report_assistant import safe_report_source_context
from app.models.technical_report_command import (
    AcceptExactTechnicalReportDraft,
    CaptureHistoricalBasisV1,
    CaptureHistoricalBasisV2,
    CreateTechnicalReportDraft,
    CreateTechnicalReportSuccessor,
    EngineeringObjectHistoricalBasisV1,
    EngineeringObjectHistoricalBasisV2,
    EngineeringRelationshipHistoricalBasisV1,
    EngineeringRelationshipHistoricalBasisV2,
    CrossDisciplineAssessmentHistoricalBasisV1,
    EvidenceHistoricalBasisV1,
    EvidenceHistoricalBasisV2,
    ReviseTechnicalReportDraft,
    ReviseTechnicalReportStandardsBasis,
    StandardHistoricalBasisV1,
    StandardLocator,
    TechnicalReportStandardBasisSelection,
    TechnicalReportActor,
    TechnicalReportCommandResult,
    TechnicalReportProvenanceEntry,
    canonical_json,
    standard_basis_payload_digest,
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
    CaptureHistoricalBasisV2,
    EvidenceHistoricalBasisV1,
    EvidenceHistoricalBasisV2,
    EngineeringObjectHistoricalBasisV1,
    EngineeringObjectHistoricalBasisV2,
    EngineeringRelationshipHistoricalBasisV1,
    EngineeringRelationshipHistoricalBasisV2,
    CrossDisciplineAssessmentHistoricalBasisV1,
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
                acceptance_now = self._clock.now()
                authority = AcceptExactDraftHistoricalAuthority(report.id, report.owner_id)
                requests = self._validate_provenance(
                    uow, command.metadata.actor, scope, authority, report.provenance
                )
                self._recheck_standards_basis(
                    uow, command.metadata.actor, scope, report, acceptance_now,
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
                result = report.accept_exact_draft(command, acceptance_now)
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
                uow, command, TechnicalReportRejectionReason.ACCEPTED_STATE_MUTATION,
                command.report_id,
            )
            raise

    def standards_candidates(self, actor: TechnicalReportActor, report_id: UUID) -> tuple[dict, ...]:
        """RPT-01: bound opaque choices only; no provider or raw locator input."""
        with self._uow_factory() as uow:
            report, scope = self._protected_report(uow, actor, report_id, "get")
            if report.lifecycle is not TechnicalReportLifecycle.DRAFT or scope.project_id is None:
                raise TechnicalReportAuthorizationDenied()
            result = []
            now = self._clock.now()
            for source, edition, identity, standing, rights in uow.standards.list_candidates(
                actor, scope, now,
            ):
                material = source.request_purpose == "material_support"
                acknowledgement = standing.standing in {"superseded", "withdrawn"}
                eligibility = (
                    "standing_acknowledgement_required"
                    if acknowledgement and material else "eligible"
                )
                result.append({
                    "authorized_handle": issue_handle(actor_id=actor.actor_id, organization_id=str(scope.organization_id), project_id=scope.project_id, operation="RPT-02", resource_id=str(source.id), edition_id=str(edition.id), rights_binding_id=str(rights.id), rights_version=rights.version, rights_digest=rights.rights_digest, purpose=source.request_purpose, provider_id=source.source_provider_id, source_location=source.source_location, integrity_digest=source.snapshot_digest),
                    "standard_identity_id": identity.id, "edition_id": edition.id,
                    "issuer": identity.issuer_display, "designation": identity.designation,
                    "edition_designation": edition.edition_designation, "standing": standing.standing,
                    "materiality": source.request_purpose, "eligibility": eligibility,
                    "warnings": ([] if eligibility == "eligible" else [eligibility.upper()]),
                })
            return tuple(result)

    def attach_standards_basis(self, command: ReviseTechnicalReportStandardsBasis) -> TechnicalReportMutationResponse:
        """RPT-02: compose and freeze every basis field inside one report lock."""
        with self._uow_factory() as uow:
            actor = command.metadata.actor
            report, scope = self._protected_report(uow, actor, command.report_id, "revise_draft")
            replay, key, fingerprint = self._idempotency(uow, command)
            if replay is not None:
                current = uow.technical_reports.get_scoped(replay.report_id, actor.organization_id)
                if current is None:
                    raise TechnicalReportAuthorizationDenied()
                return TechnicalReportMutationResponse(self._view(uow, actor, current), replay)
            if (scope.project_id is None or report.version != command.expected_version
                    or report.draft_revision_id != command.expected_draft_revision_id):
                raise TechnicalReportVersionConflict()
            uow.idempotency.reserve(key, fingerprint)
            now = self._clock.now()
            next_revision_id = uuid4()
            standard_entries = tuple(
                self._compose_standard_entry(
                    uow, actor, scope, report, selection, next_revision_id, now, ordinal,
                )
                for ordinal, selection in enumerate(command.selections)
            )
            source_keys = tuple(
                (
                    item.locator.standard_edition_id,
                    item.locator.source_provider_id,
                    item.locator.source_location,
                )
                for item in standard_entries
            )
            if len(set(source_keys)) != len(source_keys):
                raise TechnicalReportHistoricalBasisIncomplete(
                    "duplicate or conflicting standards sources are prohibited",
                )
            retained = tuple(
                entry for entry in report.provenance
                if entry.source_type is not TechnicalReportSourceType.STANDARD
            )
            if len(retained) + len(standard_entries) > 32:
                raise TechnicalReportHistoricalBasisIncomplete("Technical Report provenance limit exceeded")
            provenance = tuple(
                replace(entry, ordinal=index)
                for index, entry in enumerate(retained + standard_entries)
            )
            result = report.revise_standards_basis(
                command, provenance, now, next_revision_id=next_revision_id,
            )
            if not uow.technical_reports.persist_draft_expected_version(
                report, command.expected_version,
            ):
                raise TechnicalReportVersionConflict()
            self._stage_success(uow, command, result)
            uow.commit()
            return TechnicalReportMutationResponse(self._view(uow, actor, report), result)

    @staticmethod
    def _compose_standard_entry(uow, actor, scope, report, selection, revision_id, now, ordinal):
        source, edition, identity, standing, rights, applicability, assertion, verifier, sealed = (
            uow.standards.resolve_selection(
                actor, scope, selection.authorized_handle, selection.materiality,
                selection.assertion_id, now,
            )
        )
        noncurrent = standing.standing in {"superseded", "withdrawn"}
        if selection.materiality == "material_support" and (
            (noncurrent and (applicability is None or not selection.standing_acknowledgement))
            or standing.standing == "unknown"
        ):
            raise TechnicalReportHistoricalBasisIncomplete()
        if selection.materiality == "material_support" and assertion is not None and (
            assertion.verification_status != "human_verified"
            or assertion.retained_derived_use_eligible is not True
            or verifier is None
        ):
            raise TechnicalReportHistoricalBasisIncomplete()
        capabilities = {
            "metadata_visibility": bool(rights.allow_metadata_visibility),
            "content_storage": bool(rights.allow_content_storage),
            "indexing": bool(rights.allow_indexing),
            "excerpt_display": bool(rights.allow_excerpt_display),
            "source_retrieval": bool(rights.allow_source_retrieval),
            "derived_retention": bool(rights.allow_derived_retention),
            "derived_current_use": bool(rights.allow_derived_current_use),
        }
        payload = {
            "schema_version": "standard_historical_basis_v1",
            "basis_id": uuid4(), "materiality": selection.materiality,
            "selection_rationale": selection.selection_rationale,
            "standard_identity_id": identity.id, "issuer": identity.issuer_display,
            "designation": identity.designation, "title": identity.title,
            "identity_digest": identity.identity_digest,
            "standard_edition_id": edition.id,
            "edition_designation": edition.edition_designation,
            "official_publication_identifier": edition.official_publication_identifier,
            "publication_date": edition.publication_date,
            "edition_digest": edition.edition_digest,
            "standing_observation_id": standing.id, "standing": standing.standing,
            "standing_observation_digest": standing.observation_digest,
            "standing_acknowledged_by_id": actor.actor_id if noncurrent else None,
            "standing_acknowledgement_rationale": selection.standing_acknowledgement if noncurrent else None,
            "source_snapshot_id": source.id,
            "source_provider_id": source.source_provider_id,
            "source_location": source.source_location,
            "immutable_provider_token": None if sealed is None else base64.b64encode(sealed).decode("ascii"),
            "provider_version_digest": (
                source.provider_version_digest if sealed is not None else None
            ),
            "provider_handle_key_version": (
                source.provider_handle_key_version if sealed is not None else None
            ),
            "source_availability_status": source.availability_status,
            "byte_count": source.byte_count, "snapshot_digest": source.snapshot_digest,
            "content_digest": source.content_sha256,
            "rights_binding_id": rights.id, "rights_binding_version": rights.version,
            "rights_digest": rights.rights_digest, "rights_basis": rights.rights_basis,
            "rights_status": rights.rights_status,
            "evaluated_capabilities": capabilities,
            "ai_processing_permission": rights.ai_processing_permission,
            "rights_decided_at": now,
            "applicability_id": None if applicability is None else applicability.id,
            "applicability_revision": None if applicability is None else applicability.revision,
            "applicability_digest": None if applicability is None else applicability.applicability_digest,
            "applicability_status": None if applicability is None else applicability.status,
            "applicability_role": None if applicability is None else applicability.applicability_role,
            "assertion_id": None if assertion is None else assertion.id,
            "assertion_kind": None if assertion is None else assertion.assertion_kind,
            "assertion_digest": None if assertion is None else assertion.assertion_digest,
            "assertion_origin": None if assertion is None else assertion.assertion_origin,
            "assertion_verification_status": None if assertion is None else assertion.verification_status,
            "assertion_verified_by_id": None if verifier is None else verifier.verified_by,
            "assertion_current_use_eligible": None if assertion is None else assertion.retained_derived_use_eligible,
            "intelligence_interaction_id": None, "intelligence_provider_id": None,
            "intelligence_model": None, "intelligence_template_digest": None,
            "intelligence_input_digest": None, "intelligence_output_digest": None,
            "intelligence_processor_decision": None,
            "selected_by_id": actor.actor_id, "selected_at": now,
            "report_revision_id": revision_id,
            "accepted_report_id": None, "accepted_report_version": None,
            "accepted_at": None,
        }
        basis = StandardHistoricalBasisV1(
            **payload, basis_digest=standard_basis_payload_digest(payload),
        )
        material = selection.materiality == "material_support"
        return TechnicalReportProvenanceEntry(
            basis.basis_id, ordinal, TechnicalReportSourceClass.STANDARDS_MATERIAL,
            TechnicalReportSourceType.STANDARD, material, None,
            f"standards_{selection.materiality}",
            TechnicalReportVerificationStatus.VERIFIED,
            (TechnicalReportAvailabilityStatus.AVAILABLE
             if source.availability_status == "available"
             else TechnicalReportAvailabilityStatus.UNAVAILABLE),
            identity.issuer_display,
            (("reference_only; not claim-supporting material",) if not material else ()),
            basis,
            TechnicalReportIntegrityAlgorithm.SHA256 if material else None,
            hashlib.sha256(canonical_json(basis)).hexdigest() if material else None,
        )

    def _recheck_standards_basis(self, uow, actor, scope, report, now):
        if any(isinstance(item.locator, StandardLocator) for item in report.provenance):
            raise TechnicalReportHistoricalBasisIncomplete(
                "legacy standards provenance must be converted before acceptance",
            )
        bases = tuple(
            item.locator for item in report.provenance
            if isinstance(item.locator, StandardHistoricalBasisV1)
        )
        if bases:
            if any(item.report_revision_id != report.draft_revision_id for item in bases):
                raise TechnicalReportHistoricalBasisIncomplete()
            uow.standards.require_current(actor, scope, bases, now)
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
            if any(item.source_type is TechnicalReportSourceType.STANDARD for item in selected):
                raise TechnicalReportHistoricalBasisIncomplete(
                    "successor Reports require a new canonical standards selection",
                )
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
                *(safe_report_source_context(selected[item].locator) for item in selected_source_entry_ids),
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
        if isinstance(locator, (CaptureHistoricalBasisV1, CaptureHistoricalBasisV2)): identity = locator.capture_id
        elif isinstance(locator, (EvidenceHistoricalBasisV1, EvidenceHistoricalBasisV2)): identity = locator.evidence_id
        elif isinstance(locator, (EngineeringObjectHistoricalBasisV1, EngineeringObjectHistoricalBasisV2)): identity = locator.engineering_object_id
        elif isinstance(locator, CrossDisciplineAssessmentHistoricalBasisV1): identity = locator.assessment_id
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
        # Correlation and command identities are transport-generated per
        # attempt.  They must not turn the same authorized idempotent request
        # into a digest mismatch on retry; the original values remain frozen
        # in the stored canonical result and events.
        stable_metadata = replace(
            metadata, correlation_id=UUID(int=0), command_id=UUID(int=0),
        )
        fingerprint = hashlib.sha256(canonical_json(
            replace(command, metadata=stable_metadata),
        )).hexdigest()
        return uow.idempotency.find(key, fingerprint), key, fingerprint

    def _stage_success(self, uow, command, result):
        metadata = command.metadata
        now = result.occurred_at
        uow.audit.record(
            TechnicalReportAuditRecord(
                metadata.actor.actor_id,
                metadata.actor.organization_id,
                result.report_id,
                type(command).__name__,
                metadata.command_id,
                metadata.correlation_id,
                now,
                result.events[0].event_id,
                getattr(result.events[0], "standards_basis_digest", None),
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
