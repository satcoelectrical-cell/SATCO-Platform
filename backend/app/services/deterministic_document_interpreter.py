"""Generic deterministic adapters from extracted document structure to candidates."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re
from uuid import UUID, NAMESPACE_URL, uuid5

from app.enums.document_intelligence import (
    CandidateAssertionMode,
    CandidateKind,
    DocumentFamily,
    SourceLocatorKind,
)
from app.ports.document_intelligence import AuthorizedDocumentSource
from app.schemas.document_intelligence import ExtractedDocumentV1
from app.schemas.source_locator import SourceLocatorV1


@dataclass(frozen=True, slots=True)
class DeterministicCandidateDraft:
    kind: CandidateKind
    assertion_mode: CandidateAssertionMode
    subject_key: str | None
    subject_label: str | None
    raw_value: str
    normalized_value: str | None
    numeric_value: Decimal | None
    unit: str | None
    quantity_type: str | None
    condition: str | None
    confidence: Decimal
    confidence_rationale: str
    uncertainty: str | None
    assumptions: tuple[str, ...]
    proposed_canonical_target: str
    locators: tuple[SourceLocatorV1, ...]
    locator_digests: tuple[str, ...]


_NUMBER_WITH_UNIT = re.compile(
    r"^\s*([-+]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?)\s*([^\d\s].{0,62})?\s*$"
)
_HEADING = re.compile(r"^(?:\d+(?:\.\d+)*\s+)?[A-Z][A-Z0-9 /&()_-]{2,119}$")
_ASSUMPTION = re.compile(r"\b(?:assum(?:e|ed|ption)|presum(?:e|ed)|subject to)\b", re.I)


def _normalized_key(value: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    if key:
        return key[:200]
    return f"value_{sha256(value.encode()).hexdigest()[:16]}"


def _locator_digest(locator: dict) -> str:
    return sha256(
        json.dumps(locator, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def _locator(source: AuthorizedDocumentSource, created_at: datetime, **fields):
    core = {
        "schema_version": 1,
        "supporting_file_asset_id": source.asset_id,
        "asset_version_at_analysis": source.asset_version,
        "storage_object_version": source.storage_object_version,
        "digest_algorithm": "sha256",
        "content_digest": source.content_digest,
        "media_type": source.media_type,
        "extraction_method": "deterministic",
        **fields,
    }
    digest = _locator_digest(core)
    value = SourceLocatorV1(
        locator_id=uuid5(NAMESPACE_URL, f"satco:source-locator:{digest}"),
        created_at=created_at,
        **core,
    )
    return value, digest


def source_page_locator(source: AuthorizedDocumentSource, created_at: datetime, page):
    """Create a provider-safe page locator from the server-owned page inventory."""
    return _locator(
        source, created_at,
        locator_kind=SourceLocatorKind.PAGE,
        page_index=page.page_index,
        page_label=page.page_label,
        extraction_method="provider",
    )


def source_table_cell_locator(
    source: AuthorizedDocumentSource,
    created_at: datetime,
    page,
    *,
    table_index: int,
    row_index: int,
    column_index: int,
):
    """Create a provider locator only from validated server-owned coordinates."""

    table = page.tables[table_index]
    row = table[row_index]
    value = row[column_index].strip()
    header = table[0] if table else ()
    column_label = (
        header[column_index].strip()
        if column_index < len(header) and header[column_index].strip()
        else f"Column {column_index + 1}"
    )
    row_label = " ".join(cell.strip() for cell in row[:3] if cell.strip())[:256]
    return _locator(
        source,
        created_at,
        locator_kind=SourceLocatorKind.TABLE_CELL,
        page_index=page.page_index,
        page_label=page.page_label,
        table_key=f"page-{page.page_index + 1}-table-{table_index + 1}",
        row_index=row_index,
        row_label=row_label or None,
        column_index=column_index,
        column_label=column_label[:256],
        text_excerpt=value[:500],
        extraction_method="provider",
    )


def _number(value: str) -> tuple[Decimal | None, str | None]:
    match = _NUMBER_WITH_UNIT.match(value.replace(",", ""))
    if match is None:
        return None, None
    try:
        return Decimal(match.group(1)), (match.group(2) or None)
    except InvalidOperation:
        return None, None


class DeterministicDocumentInterpreter:
    adapter_id = "satco.generic-structure"
    adapter_version = "1"

    @staticmethod
    def classify(document: ExtractedDocumentV1) -> DocumentFamily:
        nonempty_tables = 0
        populated_cells = 0
        for page in document.pages:
            for table in page.tables:
                populated = sum(bool(cell.strip()) for row in table for cell in row)
                if len(table) >= 2 and max((len(row) for row in table), default=0) >= 2:
                    nonempty_tables += 1
                    populated_cells += populated
        if nonempty_tables and populated_cells >= 6:
            return DocumentFamily.TABULAR_ENGINEERING
        return DocumentFamily.NARRATIVE_ENGINEERING

    def interpret(
        self,
        *,
        document: ExtractedDocumentV1,
        source: AuthorizedDocumentSource,
        created_at: datetime,
        maximum_candidates: int = 5000,
    ) -> tuple[DocumentFamily, tuple[DeterministicCandidateDraft, ...]]:
        family = self.classify(document)
        if family is DocumentFamily.TABULAR_ENGINEERING:
            drafts = self._tabular(document, source, created_at, maximum_candidates)
        else:
            drafts = self._narrative(document, source, created_at, maximum_candidates)
        return family, tuple(drafts)

    def _tabular(self, document, source, created_at, maximum):
        drafts: list[DeterministicCandidateDraft] = []
        for page in document.pages:
            for table_index, table in enumerate(page.tables):
                if len(table) < 2:
                    continue
                width = max((len(row) for row in table), default=0)
                headers = tuple(
                    (table[0][column].strip() if column < len(table[0]) else "")
                    or f"Column {column + 1}"
                    for column in range(width)
                )
                table_key = f"page-{page.page_index + 1}-table-{table_index + 1}"
                for row_index, row in enumerate(table[1:], start=1):
                    populated = tuple(
                        (column_index, cell.strip())
                        for column_index, cell in enumerate(row)
                        if cell.strip()
                    )
                    textual = tuple(
                        item for item in populated
                        if _number(item[1])[0] is None and item[1] not in {"-", "—"}
                    )
                    subject_column, subject_label = (
                        textual[0] if textual else populated[0] if populated else (None, None)
                    )
                    if subject_label is None:
                        continue
                    for column_index, raw in enumerate(row):
                        value = raw.strip()
                        if not value or column_index == subject_column:
                            continue
                        numeric, unit = _number(value)
                        column_label = headers[column_index]
                        locator, digest = _locator(
                            source,
                            created_at,
                            locator_kind=SourceLocatorKind.TABLE_CELL,
                            page_index=page.page_index,
                            page_label=page.page_label,
                            table_key=table_key,
                            row_index=row_index,
                            row_label=subject_label[:256],
                            column_index=column_index,
                            column_label=column_label[:256],
                            text_excerpt=value[:500],
                        )
                        drafts.append(DeterministicCandidateDraft(
                            kind=(CandidateKind.ENGINEERING_VALUE if numeric is not None
                                  else CandidateKind.ENGINEERING_FACT),
                            assertion_mode=CandidateAssertionMode.DIRECT,
                            subject_key=_normalized_key(subject_label),
                            subject_label=subject_label[:500],
                            raw_value=value[:4000],
                            normalized_value=(str(numeric) if numeric is not None else value[:4000]),
                            numeric_value=numeric,
                            unit=unit,
                            quantity_type=_normalized_key(column_label)[:128],
                            condition=None,
                            confidence=Decimal("0.9000"),
                            confidence_rationale="Value is read directly from a bounded extracted table cell.",
                            uncertainty=None,
                            assumptions=(),
                            proposed_canonical_target=(
                                "engineering_context_value" if numeric is not None
                                else "engineering_context_fact"
                            ),
                            locators=(locator,),
                            locator_digests=(digest,),
                        ))
                        if len(drafts) >= maximum:
                            return drafts
        return drafts

    def _narrative(self, document, source, created_at, maximum):
        drafts: list[DeterministicCandidateDraft] = []
        section_path: tuple[str, ...] = ()
        for page in document.pages:
            for match in re.finditer(r"(?m)^\s*(\S[^\n\r]{2,999})\s*$", page.text):
                value = match.group(1).strip()
                if _HEADING.match(value):
                    section_path = (value[:500],)
                    continue
                if len(value) < 20:
                    continue
                excerpt = value[:500]
                excerpt_digest = sha256(excerpt.encode()).hexdigest()
                locator, digest = _locator(
                    source,
                    created_at,
                    locator_kind=SourceLocatorKind.TEXT_SPAN,
                    page_index=page.page_index,
                    page_label=page.page_label,
                    section_path=section_path,
                    section_title=(section_path[-1] if section_path else None),
                    text_start=match.start(1),
                    text_end=match.start(1) + len(excerpt),
                    text_excerpt=excerpt,
                    text_excerpt_digest=excerpt_digest,
                )
                is_assumption = bool(_ASSUMPTION.search(value))
                drafts.append(DeterministicCandidateDraft(
                    kind=(CandidateKind.ASSUMPTION if is_assumption
                          else CandidateKind.ENGINEERING_FACT),
                    assertion_mode=CandidateAssertionMode.DIRECT,
                    subject_key=(_normalized_key(section_path[-1]) if section_path else None),
                    subject_label=(section_path[-1] if section_path else None),
                    raw_value=value[:4000],
                    normalized_value=value[:4000],
                    numeric_value=None,
                    unit=None,
                    quantity_type=None,
                    condition=None,
                    confidence=Decimal("0.8000"),
                    confidence_rationale="Statement is read directly from bounded page text.",
                    uncertainty=("Deterministic text extraction does not establish engineering authority."),
                    assumptions=(),
                    proposed_canonical_target=(
                        "engineering_context_assumption" if is_assumption
                        else "engineering_context_fact"
                    ),
                    locators=(locator,),
                    locator_digests=(digest,),
                ))
                if len(drafts) >= maximum:
                    return drafts
        return drafts
