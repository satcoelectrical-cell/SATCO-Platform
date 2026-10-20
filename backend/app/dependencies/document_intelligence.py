"""Request-scoped Document Intelligence composition."""

from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Depends
from sqlalchemy.orm import Session

from app.adapters.pdf_document_content_extractor import PdfPlumberDocumentContentExtractor
from app.adapters.supporting_file_object_store import S3PrivateSupportingFileObjectStore
from app.core.config import settings
from app.core.database import get_db
from app.core.database import SessionLocal
from app.dependencies.auth import (
    AuthenticatedOrganizationContext,
    get_current_user_organization_context,
)
from app.enums.document_intelligence import DocumentAnalysisState
from app.models.document_intelligence import DocumentAnalysisRun
from app.services.document_intelligence_service import (
    DocumentIntelligenceService,
    DocumentIntelligenceUnavailable,
)
from app.services.deterministic_document_interpreter import DeterministicDocumentInterpreter
from app.services.document_analysis_worker import DocumentAnalysisWorker
from app.adapters.document_semantic_provider import (
    DisabledDocumentSemanticProvider,
    OllamaDocumentSemanticProvider,
    UnavailableDocumentSemanticProvider,
)


@dataclass(frozen=True, slots=True)
class DocumentIntelligenceApplication:
    service: DocumentIntelligenceService
    context: AuthenticatedOrganizationContext


@dataclass(frozen=True, slots=True)
class DocumentIntelligenceSourceApplication:
    service: DocumentIntelligenceService
    context: AuthenticatedOrganizationContext
    objects: S3PrivateSupportingFileObjectStore


def _document_objects() -> S3PrivateSupportingFileObjectStore:
    try:
        return S3PrivateSupportingFileObjectStore(
            endpoint_url=settings.SUPPORTING_FILE_OBJECT_ENDPOINT,
            bucket=settings.SUPPORTING_FILE_OBJECT_BUCKET,
            region=settings.SUPPORTING_FILE_OBJECT_REGION,
            access_key=settings.resolved_supporting_file_object_access_key(),
            secret_key=settings.resolved_supporting_file_object_secret_key(),
        )
    except Exception:
        raise DocumentIntelligenceUnavailable() from None


def get_document_intelligence_application(
    db: Session = Depends(get_db),
    context: AuthenticatedOrganizationContext = Depends(
        get_current_user_organization_context
    ),
) -> DocumentIntelligenceApplication:
    return DocumentIntelligenceApplication(
        service=DocumentIntelligenceService(db), context=context,
    )


def get_document_intelligence_source_application(
    db: Session = Depends(get_db),
    context: AuthenticatedOrganizationContext = Depends(
        get_current_user_organization_context
    ),
) -> DocumentIntelligenceSourceApplication:
    return DocumentIntelligenceSourceApplication(
        service=DocumentIntelligenceService(db),
        context=context,
        objects=_document_objects(),
    )


def _document_semantic_provider():
    if not settings.DOCUMENT_SEMANTIC_PROVIDER_ENABLED:
        return DisabledDocumentSemanticProvider()
    try:
        return OllamaDocumentSemanticProvider(
            endpoint=settings.DOCUMENT_SEMANTIC_PROVIDER_ENDPOINT,
            model_id=settings.DOCUMENT_SEMANTIC_PROVIDER_MODEL,
            timeout_seconds=settings.DOCUMENT_SEMANTIC_PROVIDER_TIMEOUT_SECONDS,
            maximum_input_characters=(
                settings.DOCUMENT_SEMANTIC_PROVIDER_MAX_INPUT_CHARACTERS
            ),
        )
    except ValueError:
        return UnavailableDocumentSemanticProvider()


def process_document_analysis_job(run_id) -> None:
    """Background composition uses a fresh transaction and an exact-key store."""
    with SessionLocal() as session:
        try:
            objects = _document_objects()
            DocumentAnalysisWorker(
                session=session,
                objects=objects,
                extractor=PdfPlumberDocumentContentExtractor(),
                interpreter=DeterministicDocumentInterpreter(),
                semantic_provider=_document_semantic_provider(),
            ).process(run_id)
        except Exception:
            session.rollback()
            # Keep technical configuration details out of customer responses.
            run = session.query(DocumentAnalysisRun).filter_by(id=run_id).first()
            if run is not None:
                run.state = DocumentAnalysisState.FAILED_RETRYABLE.value
                run.customer_message = (
                    "Analysis service is temporarily unavailable; retry is available"
                )
                run.version += 1
                run.updated_at = datetime.now(timezone.utc)
                session.commit()
