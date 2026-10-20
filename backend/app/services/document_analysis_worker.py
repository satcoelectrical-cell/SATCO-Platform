"""Internal deterministic worker; document bytes are data and never instructions."""

from datetime import datetime, timezone
from uuid import UUID, uuid5

from sqlalchemy.orm import Session

from app.adapters.pdf_document_content_extractor import (
    DocumentExtractionError,
    DocumentExtractionLimitExceeded,
)
from app.enums.document_intelligence import (
    CandidateKind,
    DocumentAnalysisState,
    ExtractionStatus,
    SemanticProviderStatus,
)
from app.models.document_intelligence import (
    CandidateSourceLocatorLink,
    DocumentAnalysisPageRecord,
    DocumentAnalysisRun,
    DocumentEngineeringCandidate,
    SourceLocatorRecord,
)
from app.models.supporting_file import SupportingFileAsset
from app.ports.document_intelligence import (
    AuthorizedDocumentSource,
    DocumentContentExtractor,
    DocumentSemanticProvider,
    ExtractionPolicyV1,
)
from app.schemas.document_intelligence import SemanticDocumentRequestV1
from app.ports.supporting_file import SupportingFileObjectStore
from app.services.deterministic_document_interpreter import (
    DeterministicCandidateDraft,
    DeterministicDocumentInterpreter,
    source_page_locator,
    source_table_cell_locator,
)
from app.adapters.document_semantic_provider import validate_semantic_response


class DocumentAnalysisWorker:
    def __init__(
        self,
        *,
        session: Session,
        objects: SupportingFileObjectStore,
        extractor: DocumentContentExtractor,
        interpreter: DeterministicDocumentInterpreter,
        semantic_provider: DocumentSemanticProvider | None = None,
        policy: ExtractionPolicyV1 = ExtractionPolicyV1(),
    ):
        self.session = session
        self.objects = objects
        self.extractor = extractor
        self.interpreter = interpreter
        self.semantic_provider = semantic_provider
        self.policy = policy

    def process(self, run_id: UUID) -> None:
        run = self.session.query(DocumentAnalysisRun).filter_by(id=run_id).with_for_update().first()
        if run is None or run.state != DocumentAnalysisState.QUEUED.value:
            self.session.rollback()
            return
        run.state = DocumentAnalysisState.EXTRACTING.value
        run.customer_message = "Extracting document pages"
        run.version += 1
        run.updated_at = datetime.now(timezone.utc)
        self.session.commit()

        try:
            run = self.session.query(DocumentAnalysisRun).filter_by(id=run_id).first()
            asset = self.session.query(SupportingFileAsset).filter_by(
                id=run.supporting_file_asset_id,
                organization_id=run.organization_id,
                project_id=run.project_id,
                workspace_id=run.workspace_id,
            ).first()
            if asset is None:
                self._fail(run_id, DocumentAnalysisState.FAILED_TERMINAL, "Document source is unavailable")
                return
            if (
                asset.lifecycle != "available"
                or asset.version != run.source_asset_version
                or asset.object_version != run.source_storage_object_version
                or asset.content_digest != run.source_content_digest
            ):
                self._fail(run_id, DocumentAnalysisState.SOURCE_CHANGED, "Source revision changed; start a new analysis")
                return
            receipt = self.objects.head_exact(asset.storage_key, asset.object_version)
            if receipt is None or (
                receipt.byte_size != asset.byte_size
                or receipt.sha256 != run.source_content_digest
            ):
                self._fail(run_id, DocumentAnalysisState.FAILED_RETRYABLE, "Document source is temporarily unavailable")
                return
            stream = self.objects.open_exact(asset.storage_key, asset.object_version)
            try:
                source = AuthorizedDocumentSource(
                    analysis_run_id=run.id,
                    asset_id=asset.id,
                    asset_version=run.source_asset_version,
                    storage_object_version=run.source_storage_object_version,
                    content_digest=run.source_content_digest,
                    media_type=run.media_type,
                    stream=stream,
                )
                document = self.extractor.extract(source, self.policy)
            finally:
                stream.close()
            if document.status is ExtractionStatus.FAILED:
                raise DocumentExtractionError("all pages failed extraction")

            run.state = DocumentAnalysisState.INTERPRETING.value
            run.customer_message = "Preparing review candidates"
            run.page_count = document.page_count
            run.progress_total = document.page_count
            run.progress_completed = document.page_count
            run.parser_id = document.parser_id
            run.parser_version = document.parser_version
            run.output_digest = document.output_digest
            run.version += 1
            run.updated_at = datetime.now(timezone.utc)
            self.session.commit()

            run = self.session.query(DocumentAnalysisRun).filter_by(id=run_id).first()
            now = datetime.now(timezone.utc)
            family, drafts = self.interpreter.interpret(
                document=document, source=source, created_at=now,
            )
            provider_status = SemanticProviderStatus.DISABLED
            provider_drafts = []
            if self.semantic_provider is not None:
                semantic_request = SemanticDocumentRequestV1(
                    request_id=uuid5(run.id, "semantic-request:v1"),
                    analysis_run_id=run.id,
                    document_family=family,
                    document=document,
                    allowed_candidate_kinds=tuple(CandidateKind),
                )
                response = validate_semantic_response(
                    semantic_request,
                    self.semantic_provider.analyze(semantic_request),
                )
                provider_status = response.status
                if response.status in {SemanticProviderStatus.SUCCESS, SemanticProviderStatus.PARTIAL}:
                    for candidate in response.candidates:
                        if candidate.source_cell_references:
                            located = tuple(
                                source_table_cell_locator(
                                    source,
                                    now,
                                    document.pages[reference.page_index],
                                    table_index=reference.table_index,
                                    row_index=reference.row_index,
                                    column_index=reference.column_index,
                                )
                                for reference in candidate.source_cell_references
                            )
                        else:
                            located = tuple(
                                source_page_locator(source, now, document.pages[index])
                                for index in candidate.locator_indexes
                            )
                        provider_drafts.append(DeterministicCandidateDraft(
                            kind=candidate.kind,
                            assertion_mode=candidate.assertion_mode,
                            subject_key=candidate.subject_key,
                            subject_label=candidate.subject_label,
                            raw_value=candidate.value.raw_value,
                            normalized_value=candidate.value.normalized_value,
                            numeric_value=candidate.value.numeric_value,
                            unit=candidate.value.unit,
                            quantity_type=candidate.value.quantity_type,
                            condition=candidate.value.condition,
                            confidence=candidate.confidence,
                            confidence_rationale=candidate.confidence_rationale,
                            uncertainty=candidate.uncertainty,
                            assumptions=candidate.assumptions,
                            proposed_canonical_target=candidate.proposed_canonical_target,
                            locators=tuple(item[0] for item in located),
                            locator_digests=tuple(item[1] for item in located),
                        ))
            drafts = tuple(drafts) + tuple(provider_drafts)
            for page in document.pages:
                self.session.add(DocumentAnalysisPageRecord(
                    analysis_run_id=run.id,
                    page_index=page.page_index,
                    page_label=page.page_label,
                    status=page.status.value,
                    extracted_text=page.text,
                    tables=[[list(row) for row in table] for table in page.tables],
                    warnings=list(page.warnings),
                    created_at=now,
                ))
            locator_cache: dict[str, SourceLocatorRecord] = {}
            pending_locator_links: list[CandidateSourceLocatorLink] = []
            for ordinal, draft in enumerate(drafts):
                candidate = DocumentEngineeringCandidate(
                    id=uuid5(run.id, f"candidate:{ordinal}"),
                    analysis_run_id=run.id,
                    ordinal=ordinal,
                    kind=draft.kind.value,
                    assertion_mode=draft.assertion_mode.value,
                    review_state="unreviewed",
                    subject_key=draft.subject_key,
                    subject_label=draft.subject_label,
                    raw_value=draft.raw_value,
                    normalized_value=draft.normalized_value,
                    numeric_value=draft.numeric_value,
                    unit=draft.unit,
                    quantity_type=draft.quantity_type,
                    condition=draft.condition,
                    confidence=draft.confidence,
                    confidence_rationale=draft.confidence_rationale,
                    uncertainty=draft.uncertainty,
                    assumptions=list(draft.assumptions),
                    proposed_canonical_target=draft.proposed_canonical_target,
                    version=1,
                    created_at=now,
                    updated_at=now,
                )
                self.session.add(candidate)
                for locator_ordinal, (locator, locator_digest) in enumerate(
                    zip(draft.locators, draft.locator_digests, strict=True)
                ):
                    record = locator_cache.get(locator_digest)
                    if record is None:
                        record = self.session.query(SourceLocatorRecord).filter_by(
                            locator_digest=locator_digest
                        ).first()
                    if record is None:
                        box = locator.bounding_box
                        record = SourceLocatorRecord(
                            id=locator.locator_id,
                            schema_version=1,
                            locator_kind=locator.locator_kind.value,
                            supporting_file_asset_id=locator.supporting_file_asset_id,
                            asset_version_at_analysis=locator.asset_version_at_analysis,
                            storage_object_version=locator.storage_object_version,
                            digest_algorithm="sha256",
                            content_digest=locator.content_digest,
                            media_type=locator.media_type,
                            page_index=locator.page_index,
                            page_label=locator.page_label,
                            section_path=list(locator.section_path),
                            section_title=locator.section_title,
                            table_key=locator.table_key,
                            table_title=locator.table_title,
                            row_index=locator.row_index,
                            row_label=locator.row_label,
                            column_index=locator.column_index,
                            column_label=locator.column_label,
                            text_start=locator.text_start,
                            text_end=locator.text_end,
                            text_excerpt=locator.text_excerpt,
                            text_excerpt_digest=locator.text_excerpt_digest,
                            bbox_x0=(box.x0 if box else None),
                            bbox_y0=(box.y0 if box else None),
                            bbox_x1=(box.x1 if box else None),
                            bbox_y1=(box.y1 if box else None),
                            source_revision_label=locator.source_revision_label,
                            extraction_method=locator.extraction_method,
                            locator_digest=locator_digest,
                            created_at=locator.created_at,
                        )
                        self.session.add(record)
                    locator_cache[locator_digest] = record
                    pending_locator_links.append(CandidateSourceLocatorLink(
                        candidate_id=candidate.id,
                        source_locator_id=record.id,
                        ordinal=locator_ordinal,
                    ))

            # These models intentionally have no mutable ORM relationships.
            # Flush the immutable candidate/locator parents before their
            # identifier-only association rows so PostgreSQL foreign keys do
            # not depend on mapper ordering.
            self.session.flush()
            for link in pending_locator_links:
                self.session.add(link)

            limitations = list(document.warnings)
            if document.status is ExtractionStatus.PARTIAL:
                limitations.append("Some PDF content could not be extracted completely")
            if run.family_hint and run.family_hint != family.value:
                limitations.append("Detected document structure differs from the requested family hint")
            provider_message = {
                SemanticProviderStatus.DISABLED: "Semantic provider is disabled; candidates are deterministic extraction only",
                SemanticProviderStatus.UNAVAILABLE: "Semantic interpretation is temporarily unavailable; deterministic extraction remains reviewable",
                SemanticProviderStatus.TIMED_OUT: "Semantic interpretation timed out; deterministic extraction remains reviewable",
                SemanticProviderStatus.REFUSED: "Semantic interpretation was safely refused; deterministic extraction remains reviewable",
                SemanticProviderStatus.INVALID_RESPONSE: "Semantic interpretation response was rejected; deterministic extraction remains reviewable",
                SemanticProviderStatus.PARTIAL: "Semantic interpretation completed with disclosed limitations",
            }.get(provider_status)
            if provider_message:
                limitations.append(provider_message)
            run.document_family = family.value
            run.provider_status = provider_status.value
            run.candidate_count = len(drafts)
            run.unreviewed_count = len(drafts)
            run.limitations = limitations
            run.state = (
                DocumentAnalysisState.REQUIRES_REVIEW.value if drafts
                else DocumentAnalysisState.COMPLETED_WITH_LIMITATIONS.value
            )
            run.customer_message = (
                f"{len(drafts)} candidates require review" if drafts
                else "Extraction completed with no reviewable candidates"
            )
            run.version += 1
            run.updated_at = now
            self.session.commit()
        except DocumentExtractionLimitExceeded:
            self.session.rollback()
            self._fail(run_id, DocumentAnalysisState.FAILED_TERMINAL, "Document exceeds safe extraction limits")
        except DocumentExtractionError:
            self.session.rollback()
            self._fail(run_id, DocumentAnalysisState.FAILED_TERMINAL, "Document could not be safely extracted")
        except Exception:
            self.session.rollback()
            self._fail(run_id, DocumentAnalysisState.FAILED_RETRYABLE, "Analysis could not be completed; retry is available")

    def _fail(self, run_id: UUID, state: DocumentAnalysisState, message: str) -> None:
        run = self.session.query(DocumentAnalysisRun).filter_by(id=run_id).first()
        if run is None:
            self.session.rollback()
            return
        run.state = state.value
        run.customer_message = message
        run.version += 1
        run.updated_at = datetime.now(timezone.utc)
        self.session.commit()
