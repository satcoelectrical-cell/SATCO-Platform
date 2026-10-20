"""Application service for the Human-governed document-analysis lifecycle."""

from datetime import datetime, timezone
from hashlib import sha256
import json
import unicodedata
from uuid import UUID, NAMESPACE_URL, uuid4, uuid5

from sqlalchemy.orm import Session

from app.enums import (
    ContextAuthority,
    ContextKind,
    EvidenceSourceKind,
    EvidenceSourceStanding,
)
from app.enums.document_intelligence import DocumentAnalysisState
from app.exceptions.engineering_context import (
    ContextForbidden,
    InvalidContext,
    InvalidContextResponsibility,
)
from app.models.audit_log import AuditLog
from app.models.document_intelligence import (
    EvidenceSourceLocatorLink,
    DocumentAnalysisRun,
    DocumentCandidateReview,
    DocumentEngineeringCandidate,
    DocumentIntelligenceIdempotency,
    DocumentIntelligenceOutbox,
    DocumentPromotionReceipt,
    DocumentCorrelation,
    DocumentFindingRecord,
)
from app.models.evidence import Evidence
from app.models.evidence_command import (
    CreateEvidence,
    EvidenceActor,
    EvidenceMetadata,
    EvidenceOutbox,
    LinkEvidenceSupportingFiles,
)
from app.models.engineering_workspace import EngineeringWorkspace, EngineeringWorkspaceMember
from app.models.project import Project
from app.models.supporting_file import EvidenceSupportingFileLink, SupportingFileAsset
from app.models.user import User
from app.repositories.document_intelligence_unit_of_work import DocumentIntelligenceRepository
from app.ports.supporting_file import SupportingFileObjectStore
from app.schemas.document_intelligence import (
    DocumentAnalysisCreate,
    DocumentAnalysisListResponse,
    DocumentAnalysisProgress,
    DocumentAnalysisSummary,
    CandidateReviewRequest,
    EngineeringCandidate,
    EngineeringCandidateListResponse,
    EngineeringCandidateValue,
    DocumentPromotionRequest,
    DocumentPromotionResponse,
    DocumentCorrelationRequest,
    DocumentCorrelationEvaluation,
    DocumentCorrelationView,
    DocumentCorrelationPage,
    DocumentFinding,
    DocumentFindingPage,
    DocumentEvidenceSource,
)
from app.schemas.source_locator import NormalizedBoundingBoxV1, SourceLocatorV1
from app.services.engineering_context_service import EngineeringContextService
from app.services.document_rule_pack import (
    DocumentRulePackV2,
    ReviewedRuleCandidate,
    RULE_PACK_ID,
    RULE_PACK_VERSION,
)
from app.enums.technical_report import (
    TechnicalReportAvailabilityStatus,
    TechnicalReportIntegrityAlgorithm,
    TechnicalReportPurpose,
    TechnicalReportSourceClass,
    TechnicalReportSourceType,
    TechnicalReportVerificationStatus,
)
from app.models.technical_report_command import (
    CreateTechnicalReportDraft,
    ExternalHumanLocator,
    PreliminaryQualification,
    TechnicalReportCommandMetadata,
    TechnicalReportContent,
    TechnicalReportProvenanceEntry,
    canonical_json,
)
from app.schemas.document_intelligence import (
    DocumentReportDraftRequest,
    DocumentReportDraftResponse,
)


class DocumentIntelligenceProtectedNotFound(Exception):
    pass


class DocumentIntelligenceInvalidRequest(Exception):
    pass


class DocumentIntelligenceConflict(Exception):
    pass


class DocumentIntelligenceUnavailable(Exception):
    pass


def _fingerprint(operation: str, payload: dict) -> str:
    encoded = json.dumps(
        {"operation": operation, "payload": payload},
        sort_keys=True, default=str, separators=(",", ":"),
    ).encode()
    return sha256(encoded).hexdigest()


class DocumentIntelligenceService:
    def __init__(self, session: Session):
        self.session = session
        self.repository = DocumentIntelligenceRepository(session)

    def _authorize_scope(self, *, user: User, organization_id: UUID,
                         project_id: int, workspace_id: int | None) -> Project:
        if user is None or not user.is_active:
            raise DocumentIntelligenceProtectedNotFound()
        project = self.session.query(Project).filter_by(
            id=project_id, organization_id=organization_id,
        ).first()
        if project is None:
            raise DocumentIntelligenceProtectedNotFound()
        if user.role == "admin" or user.id in {
            project.owner_id, project.primary_assignee_id,
        }:
            if workspace_id is not None:
                workspace = self.session.query(EngineeringWorkspace).filter_by(
                    id=workspace_id, project_id=project_id,
                ).first()
                if workspace is None:
                    raise DocumentIntelligenceProtectedNotFound()
            return project
        if workspace_id is None:
            raise DocumentIntelligenceProtectedNotFound()
        workspace = self.session.query(EngineeringWorkspace).filter_by(
            id=workspace_id, project_id=project_id,
        ).first()
        if workspace is None or (
            user.id not in {workspace.owner_id, workspace.primary_assignee_id}
            and self.session.get(EngineeringWorkspaceMember, (workspace.id, user.id)) is None
        ):
            raise DocumentIntelligenceProtectedNotFound()
        return project

    @staticmethod
    def _allowed_actions(run: DocumentAnalysisRun) -> tuple[str, ...]:
        actions = ["open"]
        if run.state in {
            DocumentAnalysisState.PROVIDER_UNAVAILABLE.value,
            DocumentAnalysisState.FAILED_RETRYABLE.value,
        }:
            actions.append("retry")
        elif (
            run.state == DocumentAnalysisState.COMPLETED_WITH_LIMITATIONS.value
            and run.provider_status in {"unavailable", "timed_out"}
        ):
            actions.append("retry")
        if run.state == DocumentAnalysisState.SOURCE_CHANGED.value:
            actions.append("start_new_analysis")
        if run.state in {
            DocumentAnalysisState.REQUIRES_REVIEW.value,
            DocumentAnalysisState.COMPLETED_WITH_LIMITATIONS.value,
            DocumentAnalysisState.COMPLETED.value,
        }:
            actions.append("review_candidates")
        return tuple(actions)

    @classmethod
    def summary(cls, run: DocumentAnalysisRun) -> DocumentAnalysisSummary:
        return DocumentAnalysisSummary(
            analysis_run_id=run.id, project_id=run.project_id,
            workspace_id=run.workspace_id,
            supporting_file_asset_id=run.supporting_file_asset_id,
            source_asset_version=run.source_asset_version,
            source_content_digest=run.source_content_digest,
            safe_filename=run.safe_filename, state=run.state,
            document_family=run.document_family,
            progress=DocumentAnalysisProgress(
                completed_units=run.progress_completed,
                total_units=run.progress_total,
                customer_message=run.customer_message,
            ),
            page_count=run.page_count, candidate_count=run.candidate_count,
            unreviewed_count=run.unreviewed_count,
            limitations=tuple(run.limitations or ()),
            allowed_actions=cls._allowed_actions(run), version=run.version,
            created_at=run.created_at, updated_at=run.updated_at,
        )

    def create(self, *, project_id: int, data: DocumentAnalysisCreate,
               user: User, organization_id: UUID, idempotency_id: UUID,
               correlation_id: UUID) -> DocumentAnalysisSummary:
        self._authorize_scope(
            user=user, organization_id=organization_id, project_id=project_id,
            workspace_id=data.workspace_id,
        )
        asset = self.session.query(SupportingFileAsset).filter_by(
            id=data.supporting_file_asset_id, organization_id=organization_id,
            project_id=project_id, workspace_id=data.workspace_id,
        ).first()
        if asset is None:
            raise DocumentIntelligenceProtectedNotFound()
        if asset.lifecycle != "available" or asset.media_type != "application/pdf":
            raise DocumentIntelligenceInvalidRequest()
        if (
            asset.version != data.expected_asset_version
            or asset.content_digest != data.expected_content_digest
        ):
            raise DocumentIntelligenceConflict()
        payload = data.model_dump(mode="json")
        fingerprint = _fingerprint("create_analysis", payload)
        prior = self.repository.idempotency(
            organization_id=organization_id, actor_id=user.id,
            operation="create_analysis", idempotency_id=idempotency_id,
        )
        if prior is not None:
            if prior.request_fingerprint != fingerprint or prior.status != "completed":
                raise DocumentIntelligenceConflict()
            run = self.repository.get_run(
                run_id=prior.aggregate_id, organization_id=organization_id,
            )
            if run is None:
                raise DocumentIntelligenceConflict()
            return self.summary(run)
        now = datetime.now(timezone.utc)
        run = DocumentAnalysisRun(
            id=uuid4(), organization_id=organization_id, project_id=project_id,
            workspace_id=data.workspace_id, supporting_file_asset_id=asset.id,
            source_asset_version=asset.version,
            source_storage_object_version=asset.object_version,
            source_content_digest=asset.content_digest,
            safe_filename=asset.safe_filename, media_type=asset.media_type,
            family_hint=data.family_hint.value if data.family_hint else None,
            state=DocumentAnalysisState.QUEUED.value, progress_completed=0,
            progress_total=None, customer_message="Analysis queued",
            limitations=[], candidate_count=0, unreviewed_count=0,
            created_by_id=user.id, version=1, created_at=now, updated_at=now,
        )
        self.repository.add_run(run)
        self.session.add(DocumentIntelligenceOutbox(
            aggregate_id=run.id, aggregate_version=1,
            event_type="DocumentAnalysisQueued",
            payload={
                "project_id": project_id, "workspace_id": data.workspace_id,
                "asset_id": str(asset.id), "asset_version": asset.version,
                "content_digest": asset.content_digest,
                "correlation_id": str(correlation_id),
            }, occurred_at=now,
        ))
        self.session.add(DocumentIntelligenceIdempotency(
            organization_id=organization_id, actor_id=user.id,
            operation="create_analysis", idempotency_id=idempotency_id,
            request_fingerprint=fingerprint, status="completed",
            aggregate_id=run.id,
            result={"analysis_run_id": str(run.id)},
        ))
        self.repository.commit()
        self.session.refresh(run)
        return self.summary(run)

    def list(self, *, project_id: int, workspace_id: int | None,
             user: User, organization_id: UUID) -> DocumentAnalysisListResponse:
        self._authorize_scope(
            user=user, organization_id=organization_id, project_id=project_id,
            workspace_id=workspace_id,
        )
        items = self.repository.list_runs(
            organization_id=organization_id, project_id=project_id,
            workspace_id=workspace_id,
        )
        return DocumentAnalysisListResponse(
            items=tuple(self.summary(item) for item in items), total=len(items),
        )

    def get(self, *, project_id: int, run_id: UUID, user: User,
            organization_id: UUID) -> DocumentAnalysisSummary:
        run = self.repository.get_run(
            run_id=run_id, organization_id=organization_id,
        )
        if run is None or run.project_id != project_id:
            raise DocumentIntelligenceProtectedNotFound()
        self._authorize_scope(
            user=user, organization_id=organization_id, project_id=project_id,
            workspace_id=run.workspace_id,
        )
        return self.summary(run)

    @staticmethod
    def _locator(record) -> SourceLocatorV1:
        box_values = (
            record.bbox_x0, record.bbox_y0, record.bbox_x1, record.bbox_y1,
        )
        box = None
        if all(value is not None for value in box_values):
            box = NormalizedBoundingBoxV1(
                x0=float(record.bbox_x0), y0=float(record.bbox_y0),
                x1=float(record.bbox_x1), y1=float(record.bbox_y1),
            )
        return SourceLocatorV1(
            locator_id=record.id,
            schema_version=record.schema_version,
            locator_kind=record.locator_kind,
            supporting_file_asset_id=record.supporting_file_asset_id,
            asset_version_at_analysis=record.asset_version_at_analysis,
            storage_object_version=record.storage_object_version,
            digest_algorithm=record.digest_algorithm,
            content_digest=record.content_digest,
            media_type=record.media_type,
            page_index=record.page_index,
            page_label=record.page_label,
            section_path=tuple(record.section_path or ()),
            section_title=record.section_title,
            table_key=record.table_key,
            table_title=record.table_title,
            row_index=record.row_index,
            row_label=record.row_label,
            column_index=record.column_index,
            column_label=record.column_label,
            text_start=record.text_start,
            text_end=record.text_end,
            text_excerpt=record.text_excerpt,
            text_excerpt_digest=record.text_excerpt_digest,
            bounding_box=box,
            source_revision_label=record.source_revision_label,
            extraction_method=record.extraction_method,
            created_at=record.created_at,
        )

    @classmethod
    def _candidate(cls, record: DocumentEngineeringCandidate, locators,
                   promotion=None) -> EngineeringCandidate:
        actions = ()
        if record.review_state in {"unreviewed", "deferred"}:
            actions = ("accept", "correct", "reject", "defer")
        promotions = ()
        if promotion is None and record.review_state in {"accepted", "corrected"}:
            promotions = ("evidence",)
            if record.proposed_canonical_target.startswith("engineering_context_"):
                promotions = ("evidence", "evidence_and_context")
        return EngineeringCandidate(
            candidate_id=record.id,
            analysis_run_id=record.analysis_run_id,
            version=record.version,
            ordinal=record.ordinal,
            kind=record.kind,
            assertion_mode=record.assertion_mode,
            review_state=record.review_state,
            subject_key=record.subject_key,
            subject_label=record.subject_label,
            value=EngineeringCandidateValue(
                raw_value=record.raw_value,
                normalized_value=record.normalized_value,
                numeric_value=record.numeric_value,
                unit=record.unit,
                quantity_type=record.quantity_type,
                condition=record.condition,
            ),
            confidence=record.confidence,
            confidence_rationale=record.confidence_rationale,
            uncertainty=record.uncertainty,
            assumptions=tuple(record.assumptions or ()),
            proposed_canonical_target=record.proposed_canonical_target,
            locators=tuple(cls._locator(locator) for locator in locators),
            allowed_actions=actions,
            reviewed_by_id=record.reviewed_by_id,
            reviewed_at=record.reviewed_at,
            promotion_receipt_id=(promotion.id if promotion else None),
            promoted_evidence_id=(promotion.evidence_id if promotion else None),
            promoted_engineering_context_id=(
                promotion.engineering_context_id if promotion else None
            ),
            allowed_promotions=promotions,
        )

    def list_candidates(self, *, project_id: int, run_id: UUID,
                        user: User, organization_id: UUID) -> EngineeringCandidateListResponse:
        run = self.repository.get_run(run_id=run_id, organization_id=organization_id)
        if run is None or run.project_id != project_id:
            raise DocumentIntelligenceProtectedNotFound()
        self._authorize_scope(
            user=user, organization_id=organization_id, project_id=project_id,
            workspace_id=run.workspace_id,
        )
        records = self.repository.list_candidates(run_id=run_id)
        locator_rows = self.repository.candidate_locators(
            candidate_ids=tuple(record.id for record in records),
        )
        by_candidate: dict[UUID, list] = {record.id: [] for record in records}
        for link, locator in locator_rows:
            by_candidate[link.candidate_id].append(locator)
        items = tuple(
            self._candidate(
                record,
                by_candidate[record.id],
                self.repository.promotion_receipt(
                    candidate_id=record.id, candidate_version=record.version,
                ),
            ) for record in records
        )
        reviewed = sum(
            item.review_state.value in {"accepted", "corrected", "rejected"}
            for item in items
        )
        return EngineeringCandidateListResponse(
            items=items,
            total=len(items),
            reviewed_count=reviewed,
            unreviewed_count=len(items) - reviewed,
        )

    @staticmethod
    def _candidate_snapshot(record: DocumentEngineeringCandidate) -> dict:
        return {
            "version": record.version,
            "kind": record.kind,
            "assertion_mode": record.assertion_mode,
            "review_state": record.review_state,
            "subject_key": record.subject_key,
            "subject_label": record.subject_label,
            "raw_value": record.raw_value,
            "normalized_value": record.normalized_value,
            "numeric_value": (
                str(record.numeric_value) if record.numeric_value is not None else None
            ),
            "unit": record.unit,
            "quantity_type": record.quantity_type,
            "condition": record.condition,
            "uncertainty": record.uncertainty,
        }

    def review_candidate(self, *, project_id: int, run_id: UUID,
                         candidate_id: UUID, data: CandidateReviewRequest,
                         user: User, organization_id: UUID,
                         idempotency_id: UUID,
                         correlation_id: UUID) -> EngineeringCandidate:
        run = self.repository.get_run(run_id=run_id, organization_id=organization_id)
        if run is None or run.project_id != project_id:
            raise DocumentIntelligenceProtectedNotFound()
        self._authorize_scope(
            user=user, organization_id=organization_id, project_id=project_id,
            workspace_id=run.workspace_id,
        )
        payload = {
            "run_id": str(run_id), "candidate_id": str(candidate_id),
            **data.model_dump(mode="json"),
        }
        fingerprint = _fingerprint("review_candidate", payload)
        prior = self.repository.idempotency(
            organization_id=organization_id, actor_id=user.id,
            operation="review_candidate", idempotency_id=idempotency_id,
        )
        if prior is not None:
            if prior.request_fingerprint != fingerprint:
                raise DocumentIntelligenceConflict()
            candidate = self.repository.get_candidate(
                candidate_id=candidate_id, run_id=run_id,
            )
            if (
                candidate is None
                or prior.result is None
                or candidate.version != prior.result.get("candidate_version")
            ):
                raise DocumentIntelligenceConflict()
            locators = [
                locator for _link, locator in self.repository.candidate_locators(
                    candidate_ids=(candidate.id,)
                )
            ]
            return self._candidate(candidate, locators)

        candidate = self.repository.get_candidate(
            candidate_id=candidate_id, run_id=run_id, for_update=True,
        )
        if candidate is None:
            raise DocumentIntelligenceProtectedNotFound()
        if candidate.version != data.expected_version:
            raise DocumentIntelligenceConflict()
        if candidate.review_state not in {"unreviewed", "deferred"}:
            raise DocumentIntelligenceInvalidRequest()
        before = self._candidate_snapshot(candidate)
        now = datetime.now(timezone.utc)
        action = data.action.value
        if data.correction is not None:
            correction = data.correction
            candidate.subject_key = correction.subject_key
            candidate.subject_label = correction.subject_label
            candidate.raw_value = correction.value.raw_value
            candidate.normalized_value = correction.value.normalized_value
            candidate.numeric_value = correction.value.numeric_value
            candidate.unit = correction.value.unit
            candidate.quantity_type = correction.value.quantity_type
            candidate.condition = correction.value.condition
            candidate.uncertainty = correction.uncertainty
        candidate.review_state = {
            "accept": "accepted", "correct": "corrected",
            "reject": "rejected", "defer": "deferred",
        }[action]
        candidate.reviewed_by_id = user.id
        candidate.reviewed_at = now
        candidate.version += 1
        candidate.updated_at = now
        after = self._candidate_snapshot(candidate)
        self.session.add(DocumentCandidateReview(
            candidate_id=candidate.id,
            candidate_version=data.expected_version,
            action=action,
            rationale=data.rationale,
            correction={"before": before, "after": after},
            actor_id=user.id,
            occurred_at=now,
        ))
        if action != "defer" and run.unreviewed_count > 0:
            run.unreviewed_count -= 1
        run.state = (
            DocumentAnalysisState.COMPLETED.value
            if run.unreviewed_count == 0
            else DocumentAnalysisState.REQUIRES_REVIEW.value
        )
        run.customer_message = (
            "Human review completed"
            if run.unreviewed_count == 0
            else f"{run.unreviewed_count} candidates require review"
        )
        run.version += 1
        run.updated_at = now
        self.session.add(DocumentIntelligenceIdempotency(
            organization_id=organization_id,
            actor_id=user.id,
            operation="review_candidate",
            idempotency_id=idempotency_id,
            request_fingerprint=fingerprint,
            status="completed",
            aggregate_id=run.id,
            result={
                "candidate_id": str(candidate.id),
                "candidate_version": candidate.version,
            },
        ))
        self.session.add(DocumentIntelligenceOutbox(
            aggregate_id=run.id,
            aggregate_version=run.version,
            event_type="DocumentCandidateReviewed",
            payload={
                "candidate_id": str(candidate.id),
                "candidate_version": candidate.version,
                "action": action,
                "actor_id": user.id,
                "correlation_id": str(correlation_id),
            },
            occurred_at=now,
        ))
        self.repository.commit()
        locators = [
            locator for _link, locator in self.repository.candidate_locators(
                candidate_ids=(candidate.id,)
            )
        ]
        return self._candidate(candidate, locators)

    @staticmethod
    def _promotion_response(receipt, locators, evidence_version: int = 2):
        return DocumentPromotionResponse(
            promotion_receipt_id=receipt.id,
            candidate_id=receipt.candidate_id,
            candidate_version=receipt.candidate_version,
            evidence_id=receipt.evidence_id,
            evidence_version=evidence_version,
            evidence_lifecycle="proposed",
            engineering_context_id=receipt.engineering_context_id,
            source_locator_ids=tuple(locator.id for locator in locators),
            promoted_at=receipt.promoted_at,
            promoted_by_id=receipt.promoted_by_id,
        )

    @staticmethod
    def _context_spec(candidate: DocumentEngineeringCandidate):
        target = candidate.proposed_canonical_target
        if target == "engineering_context_fact":
            return (
                ContextKind.QUALIFIED_FACT,
                ContextAuthority.AUTHORITATIVE_FACT,
                {
                    "statement": candidate.normalized_value or candidate.raw_value,
                    "uncertainty": candidate.uncertainty,
                },
            )
        if target == "engineering_context_value":
            if (
                candidate.numeric_value is None
                or not candidate.unit
                or not candidate.quantity_type
            ):
                raise DocumentIntelligenceInvalidRequest()
            return (
                ContextKind.QUALIFIED_ENGINEERING_VALUE,
                ContextAuthority.AUTHORITATIVE_FACT,
                {
                    "numeric_value": candidate.numeric_value,
                    "unit": candidate.unit,
                    "quantity_type": candidate.quantity_type,
                    "basis": "Human-reviewed document source",
                    "condition_type": "documented_condition",
                    "condition": candidate.condition or "As documented",
                    "uncertainty": candidate.uncertainty,
                },
            )
        if target == "engineering_context_assumption":
            return (
                ContextKind.ASSUMPTION,
                ContextAuthority.ASSUMPTION,
                {
                    "statement": candidate.normalized_value or candidate.raw_value,
                    "reason": "Recorded from a Human-reviewed document candidate",
                    "consequence": "Retains assumption authority until separately confirmed",
                    "confirmation_condition": "Confirmation by the responsible engineer",
                },
            )
        raise DocumentIntelligenceInvalidRequest()

    def promote_candidate(self, *, project_id: int, run_id: UUID,
                          candidate_id: UUID, data: DocumentPromotionRequest,
                          user: User, organization_id: UUID,
                          idempotency_id: UUID,
                          correlation_id: UUID) -> DocumentPromotionResponse:
        run = self.repository.get_run(run_id=run_id, organization_id=organization_id)
        if run is None or run.project_id != project_id:
            raise DocumentIntelligenceProtectedNotFound()
        self._authorize_scope(
            user=user, organization_id=organization_id, project_id=project_id,
            workspace_id=run.workspace_id,
        )
        payload = {
            "run_id": str(run_id), "candidate_id": str(candidate_id),
            **data.model_dump(mode="json"),
        }
        fingerprint = _fingerprint("promote_candidate", payload)
        prior = self.repository.idempotency(
            organization_id=organization_id, actor_id=user.id,
            operation="promote_candidate", idempotency_id=idempotency_id,
        )
        candidate = self.repository.get_candidate(
            candidate_id=candidate_id, run_id=run_id, for_update=True,
        )
        if candidate is None:
            raise DocumentIntelligenceProtectedNotFound()
        if prior is not None:
            if prior.request_fingerprint != fingerprint or prior.result is None:
                raise DocumentIntelligenceConflict()
            receipt = self.repository.promotion_receipt(
                candidate_id=candidate.id,
                candidate_version=data.expected_candidate_version,
            )
            if receipt is None or str(receipt.id) != prior.result.get("receipt_id"):
                raise DocumentIntelligenceConflict()
            locators = [
                locator for _link, locator in self.repository.candidate_locators(
                    candidate_ids=(candidate.id,)
                )
            ]
            return self._promotion_response(
                receipt, locators,
                int(prior.result.get("evidence_version", 2)),
            )
        if candidate.version != data.expected_candidate_version:
            raise DocumentIntelligenceConflict()
        if candidate.review_state not in {"accepted", "corrected"}:
            raise DocumentIntelligenceInvalidRequest()
        if len(candidate.normalized_value or candidate.raw_value) > 2000:
            raise DocumentIntelligenceInvalidRequest()
        existing = self.repository.promotion_receipt(
            candidate_id=candidate.id, candidate_version=candidate.version,
        )
        if existing is not None:
            raise DocumentIntelligenceConflict()
        locator_rows = self.repository.candidate_locators(
            candidate_ids=(candidate.id,)
        )
        locators = [locator for _link, locator in locator_rows]
        if not locators:
            raise DocumentIntelligenceInvalidRequest()
        asset = self.session.query(SupportingFileAsset).filter_by(
            id=run.supporting_file_asset_id,
            organization_id=organization_id,
            project_id=project_id,
            workspace_id=run.workspace_id,
            object_version=run.source_storage_object_version,
            content_digest=run.source_content_digest,
            lifecycle="available",
        ).with_for_update().first()
        if asset is None or asset.version != run.source_asset_version:
            raise DocumentIntelligenceConflict()

        now = datetime.now(timezone.utc)
        actor = EvidenceActor(user.id, organization_id)
        metadata = EvidenceMetadata(
            actor=actor, rationale=data.rationale,
            correlation_id=correlation_id, idempotency_id=idempotency_id,
            command_id=uuid4(),
        )
        try:
            evidence, create_result = Evidence.create(CreateEvidence(
                metadata=metadata,
                organization_id=organization_id,
                project_id=project_id,
                workspace_id=run.workspace_id,
                source_kind=EvidenceSourceKind.HUMAN_REVIEW,
                source_reference=(
                    f"supporting-file:{asset.id}#locator:{locators[0].id}"
                ),
                source_revision=(
                    f"asset-v{run.source_asset_version}:sha256:{run.source_content_digest}"
                ),
                source_standing=EvidenceSourceStanding.CURRENT,
                effective_at=None,
                supported_fact=candidate.normalized_value or candidate.raw_value,
                creator_id=user.id,
            ), now)
            link_result = evidence.link_supporting_files(
                LinkEvidenceSupportingFiles(
                    metadata=metadata, evidence_id=evidence.id,
                    expected_version=1, asset_ids=(asset.id,),
                ),
                now,
            )
        except ValueError as exc:
            raise DocumentIntelligenceInvalidRequest() from exc
        self.session.add(evidence)
        # Evidence and its provenance rows deliberately have no mutable ORM
        # relationships. Persist the aggregate parent before staging
        # identifier-only links, outbox records, and the promotion receipt.
        self.session.flush()
        self.session.add(EvidenceSupportingFileLink(
            evidence_id=evidence.id,
            asset_id=asset.id,
            organization_id=organization_id,
            project_id=project_id,
            workspace_id=run.workspace_id,
            evidence_version=evidence.version,
            ordinal=0,
            linked_by_id=user.id,
            linked_at=now,
        ))
        for ordinal, locator in enumerate(locators):
            self.session.add(EvidenceSourceLocatorLink(
                evidence_id=evidence.id,
                source_locator_id=locator.id,
                ordinal=ordinal,
                evidence_version=evidence.version,
                linked_by_id=user.id,
                linked_at=now,
            ))
        for event in (*create_result.events, *link_result.events):
            self.session.add(EvidenceOutbox(
                event_id=event.event_id,
                aggregate_id=event.evidence_id,
                aggregate_version=event.aggregate_version,
                event_type=event.event_type,
                payload=dict(event.payload),
                occurred_at=event.occurred_at,
            ))
        self.session.add(AuditLog(
            user_id=user.id,
            action="CreateEvidenceFromReviewedDocumentCandidate",
            entity="EVIDENCE",
            entity_uuid=evidence.id,
            details={
                "candidate_id": str(candidate.id),
                "candidate_version": candidate.version,
                "analysis_run_id": str(run.id),
                "correlation_id": str(correlation_id),
                "rationale": data.rationale,
            },
        ))

        context_id = None
        if data.include_engineering_context:
            kind, authority, context_payload = self._context_spec(candidate)
            try:
                context = EngineeringContextService(self.session).create_context(
                    project_id=project_id,
                    workspace_id=run.workspace_id,
                    kind=kind,
                    authority=authority,
                    owner_id=user.id,
                    steward_id=user.id,
                    current_user=user,
                    payload=context_payload,
                    sources=[{
                        "source_kind": "customer_document",
                        "source_key": f"supporting-file:{asset.id}",
                        "revision": (
                            f"asset-v{run.source_asset_version}:"
                            f"sha256:{run.source_content_digest}"
                        ),
                        "applicability": (
                            f"Human-reviewed candidate {candidate.id}; "
                            f"source locator {locators[0].id}"
                        ),
                        "limitations": candidate.uncertainty,
                    }],
                    purpose="Promoted from a Human-reviewed document candidate",
                    commit=False,
                )
                context_id = context["id"]
            except (ContextForbidden, InvalidContext, InvalidContextResponsibility) as exc:
                self.session.rollback()
                raise DocumentIntelligenceInvalidRequest() from exc

        receipt = DocumentPromotionReceipt(
            id=uuid4(),
            candidate_id=candidate.id,
            candidate_version=candidate.version,
            evidence_id=evidence.id,
            engineering_context_id=context_id,
            promoted_by_id=user.id,
            rationale=data.rationale,
            promoted_at=now,
        )
        self.session.add(receipt)
        self.session.add(DocumentIntelligenceIdempotency(
            organization_id=organization_id,
            actor_id=user.id,
            operation="promote_candidate",
            idempotency_id=idempotency_id,
            request_fingerprint=fingerprint,
            status="completed",
            aggregate_id=run.id,
            result={
                "receipt_id": str(receipt.id),
                "evidence_version": evidence.version,
            },
        ))
        self.session.add(DocumentIntelligenceOutbox(
            aggregate_id=run.id,
            aggregate_version=run.version,
            event_type="DocumentCandidatePromoted",
            payload={
                "candidate_id": str(candidate.id),
                "candidate_version": candidate.version,
                "evidence_id": str(evidence.id),
                "engineering_context_id": context_id,
                "actor_id": user.id,
                "correlation_id": str(correlation_id),
            },
            occurred_at=now,
        ))
        self.repository.commit()
        return self._promotion_response(receipt, locators, evidence.version)

    def _correlation_view(self, correlation, finding=None):
        candidate_ids = tuple(
            value for value in (
                correlation.left_candidate_id, correlation.right_candidate_id,
            ) if value is not None
        )
        candidates = {
            item.id: item for item in self.session.query(
                DocumentEngineeringCandidate
            ).filter(DocumentEngineeringCandidate.id.in_(candidate_ids)).all()
        }
        locator_rows = self.repository.candidate_locators(candidate_ids=candidate_ids)
        evidence_sources = self._bound_evidence_sources(candidates, locator_rows)
        locators = tuple(item.locator for item in evidence_sources)
        run_ids = tuple(dict.fromkeys(
            candidates[candidate_id].analysis_run_id
            for candidate_id in candidate_ids if candidate_id in candidates
        ))
        result = correlation.result or {}
        return DocumentCorrelationView(
            correlation_id=correlation.id,
            analysis_run_ids=run_ids,
            rule_id=correlation.rule_id,
            rule_version=correlation.rule_version,
            status=result["status"],
            summary=result["summary"],
            applicability=correlation.applicability,
            reason_codes=tuple(result.get("reason_codes", ())),
            uncertainty=(finding.uncertainty if finding else result.get("uncertainty")),
            evidence_sources=evidence_sources,
            evidence=locators,
            finding_id=(finding.id if finding else None),
        )

    @classmethod
    def _bound_evidence_sources(cls, candidates, locator_rows):
        """Bind every locator to its candidate/run; row order has no semantics."""

        return tuple(
            DocumentEvidenceSource(
                analysis_run_id=candidates[link.candidate_id].analysis_run_id,
                candidate_id=link.candidate_id,
                locator=cls._locator(locator),
            )
            for link, locator in locator_rows
            if link.candidate_id in candidates
        )

    def _finding(self, correlation, finding):
        view = self._correlation_view(correlation, finding)
        return DocumentFinding(
            finding_id=finding.id,
            analysis_run_ids=view.analysis_run_ids,
            kind=finding.kind,
            state=finding.state,
            title=finding.title,
            explanation=finding.explanation,
            rule_id=correlation.rule_id,
            rule_version=correlation.rule_version,
            applicability=correlation.applicability,
            uncertainty=finding.uncertainty,
            evidence_sources=view.evidence_sources,
            evidence=view.evidence,
        )

    def correlate_documents(self, *, project_id: int,
                            data: DocumentCorrelationRequest,
                            user: User, organization_id: UUID,
                            idempotency_id: UUID,
                            correlation_id: UUID) -> DocumentCorrelationEvaluation:
        run_ids = tuple(data.analysis_run_ids)
        runs = self.session.query(DocumentAnalysisRun).filter(
            DocumentAnalysisRun.id.in_(run_ids),
            DocumentAnalysisRun.organization_id == organization_id,
            DocumentAnalysisRun.project_id == project_id,
        ).order_by(DocumentAnalysisRun.id.asc()).all()
        if len(runs) != len(run_ids):
            raise DocumentIntelligenceProtectedNotFound()
        workspace_ids = {run.workspace_id for run in runs}
        if len(workspace_ids) != 1:
            raise DocumentIntelligenceInvalidRequest()
        workspace_id = next(iter(workspace_ids))
        self._authorize_scope(
            user=user, organization_id=organization_id, project_id=project_id,
            workspace_id=workspace_id,
        )
        if any(run.state not in {
            "requires_review", "completed", "completed_with_limitations",
        } for run in runs):
            raise DocumentIntelligenceInvalidRequest()

        payload = data.model_dump(mode="json")
        fingerprint = _fingerprint("correlate_documents", payload)
        prior = self.repository.idempotency(
            organization_id=organization_id, actor_id=user.id,
            operation="correlate_documents", idempotency_id=idempotency_id,
        )
        if prior is not None:
            if prior.request_fingerprint != fingerprint or prior.result is None:
                raise DocumentIntelligenceConflict()
            correlation_ids = tuple(UUID(value) for value in prior.result.get("correlation_ids", ()))
            correlations = self.session.query(DocumentCorrelation).filter(
                DocumentCorrelation.id.in_(correlation_ids),
                DocumentCorrelation.organization_id == organization_id,
                DocumentCorrelation.project_id == project_id,
            ).all()
            findings = self.session.query(DocumentFindingRecord).filter(
                DocumentFindingRecord.correlation_id.in_(correlation_ids),
            ).all()
            by_correlation = {item.correlation_id: item for item in findings}
            views = tuple(self._correlation_view(item, by_correlation.get(item.id)) for item in correlations)
            return DocumentCorrelationEvaluation(
                rule_pack_id=RULE_PACK_ID, rule_pack_version=RULE_PACK_VERSION,
                evaluated_run_ids=run_ids, correlations=views,
                findings=tuple(
                    self._finding(item, by_correlation[item.id])
                    for item in correlations if item.id in by_correlation
                ),
            )

        records = self.session.query(DocumentEngineeringCandidate).filter(
            DocumentEngineeringCandidate.analysis_run_id.in_(run_ids),
            DocumentEngineeringCandidate.review_state.in_(("accepted", "corrected")),
        ).all()
        inputs = tuple(ReviewedRuleCandidate(
            candidate_id=item.id,
            analysis_run_id=item.analysis_run_id,
            kind=item.kind,
            subject_key=item.subject_key,
            subject_label=item.subject_label,
            raw_value=item.raw_value,
            normalized_value=item.normalized_value,
            numeric_value=item.numeric_value,
            unit=item.unit,
            quantity_type=item.quantity_type,
            uncertainty=item.uncertainty,
            condition=item.condition,
            review_state=item.review_state,
        ) for item in records)
        outcomes = DocumentRulePackV2().evaluate(inputs)
        now = datetime.now(timezone.utc)
        correlations = []
        findings = []
        for outcome in outcomes:
            result = {
                "status": outcome.status,
                "summary": outcome.summary,
                "reason_codes": list(outcome.reason_codes),
                "uncertainty": outcome.uncertainty,
            }
            digest = _fingerprint("document_correlation_result", {
                "organization_id": str(organization_id),
                "project_id": project_id,
                "workspace_id": workspace_id,
                "rule_id": outcome.rule_id,
                "rule_version": outcome.rule_version,
                "left_candidate_id": str(outcome.left_candidate_id),
                "right_candidate_id": str(outcome.right_candidate_id) if outcome.right_candidate_id else None,
                "result": result,
            })
            record = self.session.query(DocumentCorrelation).filter_by(
                result_digest=digest,
            ).first()
            if record is None:
                record = DocumentCorrelation(
                    id=uuid4(), organization_id=organization_id,
                    project_id=project_id, workspace_id=workspace_id,
                    left_candidate_id=outcome.left_candidate_id,
                    right_candidate_id=outcome.right_candidate_id,
                    rule_id=outcome.rule_id, rule_version=outcome.rule_version,
                    applicability=outcome.applicability, result=result,
                    result_digest=digest, created_by_id=user.id, created_at=now,
                )
                self.session.add(record)
            finding = self.session.query(DocumentFindingRecord).filter_by(
                correlation_id=record.id,
            ).first()
            if outcome.finding_kind and finding is None:
                finding = DocumentFindingRecord(
                    id=uuid4(), correlation_id=record.id,
                    kind=outcome.finding_kind, state="open",
                    title=outcome.finding_title,
                    explanation=outcome.finding_explanation,
                    uncertainty=outcome.uncertainty, created_at=now,
                )
                self.session.add(finding)
            correlations.append(record)
            if finding is not None:
                findings.append(finding)
        self.session.flush()
        self.session.add(DocumentIntelligenceIdempotency(
            organization_id=organization_id, actor_id=user.id,
            operation="correlate_documents", idempotency_id=idempotency_id,
            request_fingerprint=fingerprint, status="completed",
            aggregate_id=runs[0].id,
            result={"correlation_ids": [str(item.id) for item in correlations]},
        ))
        self.session.add(DocumentIntelligenceOutbox(
            aggregate_id=runs[0].id, aggregate_version=runs[0].version,
            event_type="DocumentCorrelationEvaluated",
            payload={
                "analysis_run_ids": [str(value) for value in run_ids],
                "rule_pack_id": RULE_PACK_ID,
                "rule_pack_version": RULE_PACK_VERSION,
                "correlation_count": len(correlations),
                "finding_count": len(findings),
                "actor_id": user.id,
                "correlation_id": str(correlation_id),
                "rationale": data.rationale,
            }, occurred_at=now,
        ))
        self.session.add(AuditLog(
            user_id=user.id,
            action="EvaluateDocumentCorrelationRules",
            entity="DOCUMENT_CORRELATION",
            entity_uuid=correlations[0].id if correlations else runs[0].id,
            details={
                "project_id": project_id,
                "workspace_id": workspace_id,
                "analysis_run_ids": [str(value) for value in run_ids],
                "rule_pack_id": RULE_PACK_ID,
                "rule_pack_version": RULE_PACK_VERSION,
                "correlation_count": len(correlations),
                "finding_count": len(findings),
                "correlation_id": str(correlation_id),
                "rationale": data.rationale,
            },
        ))
        self.repository.commit()
        by_correlation = {item.correlation_id: item for item in findings}
        views = tuple(self._correlation_view(item, by_correlation.get(item.id)) for item in correlations)
        return DocumentCorrelationEvaluation(
            rule_pack_id=RULE_PACK_ID, rule_pack_version=RULE_PACK_VERSION,
            evaluated_run_ids=run_ids, correlations=views,
            findings=tuple(
                self._finding(item, by_correlation[item.id])
                for item in correlations if item.id in by_correlation
            ),
        )

    def list_correlations(self, *, project_id: int, workspace_id: int | None,
                          user: User, organization_id: UUID):
        self._authorize_scope(
            user=user, organization_id=organization_id, project_id=project_id,
            workspace_id=workspace_id,
        )
        query = self.session.query(DocumentCorrelation).filter_by(
            organization_id=organization_id, project_id=project_id,
        )
        if workspace_id is not None:
            query = query.filter(DocumentCorrelation.workspace_id == workspace_id)
        records = query.order_by(DocumentCorrelation.created_at.desc()).all()
        finding_records = self.session.query(DocumentFindingRecord).filter(
            DocumentFindingRecord.correlation_id.in_(tuple(item.id for item in records)),
        ).all() if records else []
        by_correlation = {item.correlation_id: item for item in finding_records}
        items = tuple(self._correlation_view(item, by_correlation.get(item.id)) for item in records)
        return DocumentCorrelationPage(items=items, total=len(items))

    def list_findings(self, *, project_id: int, workspace_id: int | None,
                      user: User, organization_id: UUID):
        correlations = self.list_correlations(
            project_id=project_id, workspace_id=workspace_id,
            user=user, organization_id=organization_id,
        )
        ids = tuple(item.correlation_id for item in correlations.items if item.finding_id)
        correlation_records = self.session.query(DocumentCorrelation).filter(
            DocumentCorrelation.id.in_(ids),
            DocumentCorrelation.organization_id == organization_id,
            DocumentCorrelation.project_id == project_id,
        ).all() if ids else []
        finding_records = self.session.query(DocumentFindingRecord).filter(
            DocumentFindingRecord.correlation_id.in_(ids),
        ).all() if ids else []
        by_correlation = {item.id: item for item in correlation_records}
        items = tuple(
            self._finding(by_correlation[item.correlation_id], item)
            for item in finding_records if item.correlation_id in by_correlation
        )
        return DocumentFindingPage(items=items, total=len(items))

    def create_document_report_draft(
        self, *, project_id: int, data: DocumentReportDraftRequest,
        user: User, organization_id: UUID, idempotency_id: UUID,
        correlation_id: UUID, report_service, report_actor,
    ) -> DocumentReportDraftResponse:
        self._authorize_scope(
            user=user, organization_id=organization_id, project_id=project_id,
            workspace_id=data.workspace_id,
        )
        rows = self.session.query(
            DocumentFindingRecord, DocumentCorrelation,
        ).join(
            DocumentCorrelation,
            DocumentCorrelation.id == DocumentFindingRecord.correlation_id,
        ).filter(
            DocumentFindingRecord.id.in_(data.finding_ids),
            DocumentCorrelation.organization_id == organization_id,
            DocumentCorrelation.project_id == project_id,
            DocumentCorrelation.workspace_id == data.workspace_id,
        ).all()
        if len(rows) != len(data.finding_ids):
            raise DocumentIntelligenceProtectedNotFound()
        ordered = tuple(sorted(rows, key=lambda row: str(row[0].id)))
        provenance = []
        technical_sections = []
        unresolved = []
        follow_up = []
        for ordinal, (finding, correlation) in enumerate(ordered):
            summary = self._validated_correlation_summary(correlation.result)
            candidate_ids = tuple(value for value in (
                correlation.left_candidate_id, correlation.right_candidate_id,
            ) if value is not None)
            locator_rows = self.repository.candidate_locators(candidate_ids=candidate_ids)
            source_lines = []
            for _link, locator_record in locator_rows:
                locator = self._locator(locator_record)
                source_lines.append(
                    f"asset {locator.supporting_file_asset_id} v{locator.asset_version_at_analysis} "
                    f"sha256:{locator.content_digest}; page {(locator.page_index or 0) + 1}; "
                    f"locator {locator.locator_id}"
                )
            representation = "\n".join((
                finding.title,
                finding.explanation,
                *((f"Correlation summary: {summary}",) if summary else ()),
                f"Rule: {correlation.rule_id} v{correlation.rule_version}",
                f"Applicability: {correlation.applicability}",
                *(source_lines or ("No source locator available",)),
            ))[:10000]
            locator = ExternalHumanLocator(
                report_local_source_id=finding.id,
                external_reference=f"satco-document-finding:{finding.id}",
                submitted_by_id=user.id,
                observed_at=finding.created_at,
                retrieved_at=None,
                submitted_at=None,
                minimal_representation=representation,
            )
            provenance.append(TechnicalReportProvenanceEntry(
                entry_id=uuid5(
                    NAMESPACE_URL,
                    f"satco:document-finding-report-source:{finding.id}",
                ),
                ordinal=ordinal,
                source_class=TechnicalReportSourceClass.EXTERNAL_OR_HUMAN_MATERIAL,
                source_type=TechnicalReportSourceType.EXTERNAL_OR_HUMAN,
                is_material=True,
                owning_capability=None,
                reliance_role="Human-reviewed deterministic document finding",
                verification_status=TechnicalReportVerificationStatus.VERIFIED,
                availability_status=TechnicalReportAvailabilityStatus.AVAILABLE,
                origin_attribution="SATCO Document Intelligence",
                limitations=tuple(value for value in (
                    finding.uncertainty,
                    "Advisory finding; Human engineering disposition remains required.",
                ) if value),
                locator=locator,
                integrity_algorithm=TechnicalReportIntegrityAlgorithm.SHA256,
                integrity_digest=sha256(canonical_json(locator)).hexdigest(),
            ))
            section_lines = [
                f"{ordinal + 1}. {finding.title}",
                finding.explanation,
            ]
            if summary:
                section_lines.append(f"Correlation summary: {summary}")
            section_lines.extend((
                f"Rule: {correlation.rule_id} v{correlation.rule_version}.",
                f"Applicability: {correlation.applicability}.",
            ))
            technical_sections.append("\n".join(section_lines))
            unresolved.append(finding.title)
            follow_up.append(f"Human engineering disposition required: {finding.title}")
        content = TechnicalReportContent(
            engineering_scope=(
                f"Deterministic Document Intelligence findings for project {project_id}, "
                f"workspace {data.workspace_id}."
            ),
            technical_content="\n\n".join(technical_sections),
            assumptions=(),
            uncertainty=(
                "This draft reports deterministic advisory results. It does not select "
                "engineering truth, resolve findings, or replace responsible Human review."
            ),
            limitations=(
                "Generated only from the selected persisted findings and their bound source locators.",
                "Document-family coverage is limited to Golden Demo V1 narrative and tabular extraction.",
            ),
            conclusions=f"{len(ordered)} advisory finding(s) remain open for Human review.",
            recommendations=tuple(follow_up),
        )
        qualification = PreliminaryQualification(
            is_preliminary=True,
            evidence_deficiencies=tuple(
                finding.title for finding, _correlation in ordered
                if finding.kind == "missing_information"
            ),
            unresolved_issues=tuple(unresolved),
            follow_up_requirements=tuple(follow_up),
        )
        command = CreateTechnicalReportDraft(
            TechnicalReportCommandMetadata(
                report_actor, data.rationale, correlation_id,
                idempotency_id, uuid4(),
            ),
            organization_id, data.workspace_id, project_id, user.id,
            TechnicalReportPurpose(data.purpose), content, qualification,
            tuple(provenance),
        )
        result = report_service.create_draft(command)
        return DocumentReportDraftResponse(
            report_id=result.report_id,
            version=result.version,
            draft_revision_id=result.draft_revision.revision_id,
            finding_ids=tuple(finding.id for finding, _correlation in ordered),
        )

    @staticmethod
    def _validated_correlation_summary(result: object) -> str | None:
        """Return only a summary that still satisfies the persisted API contract."""

        if not isinstance(result, dict):
            return None
        summary = result.get("summary")
        if not isinstance(summary, str):
            return None
        normalized = unicodedata.normalize("NFC", summary.strip())
        if (
            not normalized
            or len(normalized) > 2000
            or any(
                ord(character) < 32 and character not in "\n\t"
                for character in normalized
            )
        ):
            return None
        return normalized

    def open_source(self, *, project_id: int, run_id: UUID, user: User,
                    organization_id: UUID, objects: SupportingFileObjectStore):
        run = self.repository.get_run(run_id=run_id, organization_id=organization_id)
        if run is None or run.project_id != project_id:
            raise DocumentIntelligenceProtectedNotFound()
        self._authorize_scope(
            user=user, organization_id=organization_id, project_id=project_id,
            workspace_id=run.workspace_id,
        )
        asset = self.session.query(SupportingFileAsset).filter_by(
            id=run.supporting_file_asset_id,
            organization_id=organization_id,
            project_id=project_id,
            workspace_id=run.workspace_id,
        ).first()
        if (
            asset is None
            or asset.version < run.source_asset_version
            or asset.object_version != run.source_storage_object_version
            or asset.content_digest != run.source_content_digest
        ):
            raise DocumentIntelligenceProtectedNotFound()
        try:
            receipt = objects.head_exact(asset.storage_key, run.source_storage_object_version)
            if receipt is None or receipt.sha256 != run.source_content_digest:
                raise DocumentIntelligenceUnavailable()
            return run, receipt.byte_size, objects.open_exact(
                asset.storage_key, run.source_storage_object_version,
            )
        except DocumentIntelligenceUnavailable:
            raise
        except Exception:
            raise DocumentIntelligenceUnavailable() from None

    def retry(self, *, project_id: int, run_id: UUID, expected_version: int,
              user: User, organization_id: UUID, idempotency_id: UUID,
              correlation_id: UUID) -> DocumentAnalysisSummary:
        run = self.repository.get_run(run_id=run_id, organization_id=organization_id)
        if run is None or run.project_id != project_id:
            raise DocumentIntelligenceProtectedNotFound()
        self._authorize_scope(user=user, organization_id=organization_id,
                              project_id=project_id, workspace_id=run.workspace_id)
        if run.version != expected_version:
            raise DocumentIntelligenceConflict()
        if "retry" not in self._allowed_actions(run):
            raise DocumentIntelligenceInvalidRequest()
        fingerprint = _fingerprint("retry_analysis", {
            "run_id": str(run_id), "expected_version": expected_version,
        })
        prior = self.repository.idempotency(
            organization_id=organization_id, actor_id=user.id,
            operation="retry_analysis", idempotency_id=idempotency_id,
        )
        if prior is not None:
            if prior.request_fingerprint != fingerprint:
                raise DocumentIntelligenceConflict()
            successor = self.repository.get_run(
                run_id=prior.aggregate_id, organization_id=organization_id,
            )
            if successor is None:
                raise DocumentIntelligenceConflict()
            return self.summary(successor)
        asset = self.session.query(SupportingFileAsset).filter_by(
            id=run.supporting_file_asset_id, organization_id=organization_id,
            project_id=project_id, workspace_id=run.workspace_id,
        ).first()
        if asset is None:
            raise DocumentIntelligenceProtectedNotFound()
        if (
            asset.lifecycle != "available"
            or asset.version != run.source_asset_version
            or asset.object_version != run.source_storage_object_version
            or asset.content_digest != run.source_content_digest
        ):
            run.state = DocumentAnalysisState.SOURCE_CHANGED.value
            run.customer_message = "Source revision changed; start a new analysis"
            run.version += 1
            run.updated_at = datetime.now(timezone.utc)
            self.repository.commit()
            raise DocumentIntelligenceConflict()
        now = datetime.now(timezone.utc)
        successor = DocumentAnalysisRun(
            id=uuid4(), organization_id=run.organization_id,
            project_id=run.project_id, workspace_id=run.workspace_id,
            supporting_file_asset_id=run.supporting_file_asset_id,
            source_asset_version=run.source_asset_version,
            source_storage_object_version=run.source_storage_object_version,
            source_content_digest=run.source_content_digest,
            safe_filename=run.safe_filename, media_type=run.media_type,
            family_hint=run.family_hint, state=DocumentAnalysisState.QUEUED.value,
            progress_completed=0, progress_total=None,
            customer_message="Analysis queued for retry", limitations=[],
            candidate_count=0, unreviewed_count=0, created_by_id=user.id,
            version=1, created_at=now, updated_at=now,
        )
        self.repository.add_run(successor)
        run.state = DocumentAnalysisState.SUPERSEDED.value
        run.superseded_by_run_id = successor.id
        run.customer_message = "Superseded by a retry analysis"
        run.version += 1
        run.updated_at = now
        self.session.add(DocumentIntelligenceIdempotency(
            organization_id=organization_id, actor_id=user.id,
            operation="retry_analysis", idempotency_id=idempotency_id,
            request_fingerprint=fingerprint, status="completed",
            aggregate_id=successor.id,
            result={"analysis_run_id": str(successor.id)},
        ))
        self.session.add(DocumentIntelligenceOutbox(
            aggregate_id=successor.id, aggregate_version=1,
            event_type="DocumentAnalysisRetryQueued",
            payload={
                "predecessor_run_id": str(run.id),
                "correlation_id": str(correlation_id),
            }, occurred_at=now,
        ))
        self.repository.commit()
        self.session.refresh(successor)
        return self.summary(successor)
