"""Provider-neutral ports for untrusted engineering-document analysis."""

from dataclasses import dataclass
from datetime import datetime
from typing import BinaryIO, Protocol
from uuid import UUID

from app.enums.document_intelligence import CandidateKind, DocumentFamily
from app.schemas.document_intelligence import (
    ExtractedDocumentV1,
    SemanticDocumentRequestV1,
    SemanticDocumentResponseV1,
)


@dataclass(frozen=True, slots=True)
class AuthorizedDocumentSource:
    analysis_run_id: UUID
    asset_id: UUID
    asset_version: int
    storage_object_version: str
    content_digest: str
    media_type: str
    stream: BinaryIO


@dataclass(frozen=True, slots=True)
class ExtractionPolicyV1:
    maximum_bytes: int = 25 * 1024 * 1024
    maximum_pages: int = 500
    maximum_characters: int = 2_000_000
    maximum_tables: int = 500
    maximum_cells: int = 200_000
    timeout_seconds: float = 60.0
    require_tables: bool = False


class DocumentContentExtractor(Protocol):
    def extract(
        self,
        source: AuthorizedDocumentSource,
        policy: ExtractionPolicyV1,
    ) -> ExtractedDocumentV1: ...


class DocumentSemanticProvider(Protocol):
    """Returns advisory proposals only; it owns no SATCO authority command."""

    def analyze(
        self,
        request: SemanticDocumentRequestV1,
    ) -> SemanticDocumentResponseV1: ...


class DocumentIntelligenceClock(Protocol):
    def now(self) -> datetime: ...


@dataclass(frozen=True, slots=True)
class FamilyAdapterDescriptor:
    family: DocumentFamily
    adapter_id: str
    adapter_version: str
    supported_candidate_kinds: tuple[CandidateKind, ...]
