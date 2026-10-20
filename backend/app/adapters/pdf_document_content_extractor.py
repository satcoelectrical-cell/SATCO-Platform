"""Bounded deterministic PDF extraction for untrusted document data."""

from hashlib import sha256
from io import BytesIO
import json
import time

import pdfplumber

from app.enums.document_intelligence import ExtractionStatus
from app.ports.document_intelligence import (
    AuthorizedDocumentSource,
    DocumentContentExtractor,
    ExtractionPolicyV1,
)
from app.schemas.document_intelligence import (
    ExtractedCellBoundingBoxV1,
    ExtractedDocumentV1,
    ExtractedPageV1,
    ExtractedTableCellLocatorV1,
)
from app.services.table_cell_provenance import table_cell_locator_id


class DocumentExtractionError(Exception):
    """Safe extraction failure category; never includes document contents."""


class DocumentExtractionLimitExceeded(DocumentExtractionError):
    pass


def _safe_text(value: object, maximum: int = 2_000_000) -> str:
    text = "" if value is None else str(value)
    return "".join(
        character for character in text[:maximum]
        if character in "\n\r\t" or ord(character) >= 32
    ).strip()


def _digest_document(payload: dict) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


_TEXT_ALIGNED_TABLE_SETTINGS = {
    "vertical_strategy": "text",
    "horizontal_strategy": "text",
    "min_words_vertical": 2,
    "min_words_horizontal": 1,
    "intersection_tolerance": 8,
    "snap_tolerance": 4,
    "join_tolerance": 4,
}


def _table_width(table) -> int:
    return max((len(row) for row in table), default=0)


def _nonempty_rows(table) -> int:
    return sum(any(_safe_text(cell) for cell in row) for row in table)


def _looks_structurally_collapsed(tables) -> bool:
    if not tables:
        return False
    widest = max((_table_width(table) for table in tables), default=0)
    rows = max((_nonempty_rows(table) for table in tables), default=0)
    largest_cell_tokens = max(
        (
            len(_safe_text(cell).split())
            for table in tables
            for row in table
            for cell in row
        ),
        default=0,
    )
    return rows >= 3 and widest <= 3 and largest_cell_tokens >= 8


def _prefer_text_aligned_tables(default_tables, text_aligned_tables):
    """Recover visibly wide tables whose PDF rulings collapse most columns.

    The decision is structural only.  It neither recognizes engineering labels
    nor supplies values, units, or comparison keys.
    """

    if not default_tables or not text_aligned_tables:
        return default_tables, False
    widest_default = max((_table_width(table) for table in default_tables), default=0)
    default_rows = max((_nonempty_rows(table) for table in default_tables), default=0)
    widest_text = max((_table_width(table) for table in text_aligned_tables), default=0)
    text_rows = max((_nonempty_rows(table) for table in text_aligned_tables), default=0)
    collapsed = (
        _looks_structurally_collapsed(default_tables)
        and widest_text >= max(4, widest_default * 2)
        and text_rows >= default_rows
    )
    return (text_aligned_tables, True) if collapsed else (default_tables, False)


def _normalized_bbox(cell, *, page_width: float, page_height: float):
    if cell is None or page_width <= 0 or page_height <= 0:
        return None
    x0, top, x1, bottom = (float(value) for value in cell)
    return ExtractedCellBoundingBoxV1(
        x0=x0 / page_width,
        top=top / page_height,
        x1=x1 / page_width,
        bottom=bottom / page_height,
    )


def _table_row_cells(page, settings=None):
    """Return geometry without making it authoritative over extracted text."""

    return [
        [tuple(row.cells) for row in table.rows]
        for table in page.find_tables(settings)
    ]


class PdfPlumberDocumentContentExtractor(DocumentContentExtractor):
    parser_id = "pdfplumber"

    def extract(
        self,
        source: AuthorizedDocumentSource,
        policy: ExtractionPolicyV1,
    ) -> ExtractedDocumentV1:
        if source.media_type != "application/pdf":
            raise DocumentExtractionError("unsupported media type")
        payload = source.stream.read(policy.maximum_bytes + 1)
        if len(payload) > policy.maximum_bytes:
            raise DocumentExtractionLimitExceeded("document exceeds extraction byte limit")
        if not payload.startswith(b"%PDF-"):
            raise DocumentExtractionError("invalid PDF signature")
        if sha256(payload).hexdigest() != source.content_digest:
            raise DocumentExtractionError("source integrity check failed")

        started = time.monotonic()
        pages: list[ExtractedPageV1] = []
        total_characters = 0
        total_tables = 0
        total_cells = 0
        document_warnings: list[str] = []
        try:
            with pdfplumber.open(BytesIO(payload)) as document:
                if (document.metadata or {}).get("IsAcroForm"):
                    document_warnings.append("Interactive form fields are not interpreted")
                if len(document.pages) > policy.maximum_pages:
                    raise DocumentExtractionLimitExceeded("document exceeds page limit")
                for page_index, page in enumerate(document.pages):
                    if time.monotonic() - started > policy.timeout_seconds:
                        raise DocumentExtractionLimitExceeded("document extraction time limit exceeded")
                    warnings: list[str] = []
                    try:
                        text = _safe_text(page.extract_text() or "")
                        raw_tables = page.extract_tables() or []
                        raw_geometry = _table_row_cells(page)
                        text_aligned_tables = (
                            page.extract_tables(_TEXT_ALIGNED_TABLE_SETTINGS) or []
                            if _looks_structurally_collapsed(raw_tables)
                            else []
                        )
                        text_aligned_geometry = (
                            _table_row_cells(page, _TEXT_ALIGNED_TABLE_SETTINGS)
                            if text_aligned_tables
                            else []
                        )
                        raw_tables, recovered_collapsed_table = _prefer_text_aligned_tables(
                            raw_tables, text_aligned_tables
                        )
                        selected_geometry = (
                            text_aligned_geometry if recovered_collapsed_table else raw_geometry
                        )
                        if recovered_collapsed_table:
                            warnings.append(
                                "Collapsed ruled table recovered from deterministic text alignment"
                            )
                        tables: list[tuple[tuple[str, ...], ...]] = []
                        cell_locators: list[ExtractedTableCellLocatorV1] = []
                        for table_index, raw_table in enumerate(raw_tables):
                            rows = tuple(
                                tuple(_safe_text(cell, maximum=4000) for cell in row)
                                for row in raw_table
                            )
                            cell_count = sum(len(row) for row in rows)
                            if total_tables + 1 > policy.maximum_tables:
                                warnings.append("Additional tables omitted by extraction limit")
                                break
                            if total_cells + cell_count > policy.maximum_cells:
                                warnings.append("Additional table cells omitted by extraction limit")
                                break
                            tables.append(rows)
                            geometry_rows = (
                                selected_geometry[table_index]
                                if table_index < len(selected_geometry)
                                else []
                            )
                            for row_index, row in enumerate(rows):
                                geometry_row = (
                                    geometry_rows[row_index]
                                    if row_index < len(geometry_rows)
                                    else ()
                                )
                                for column_index, cell in enumerate(row):
                                    geometry = (
                                        geometry_row[column_index]
                                        if column_index < len(geometry_row)
                                        else None
                                    )
                                    cell_locators.append(ExtractedTableCellLocatorV1(
                                        locator_id=table_cell_locator_id(
                                            source.content_digest,
                                            page_index,
                                            table_index,
                                            row_index,
                                            column_index,
                                        ),
                                        document_digest=source.content_digest,
                                        page_index=page_index,
                                        table_index=table_index,
                                        row_index=row_index,
                                        column_index=column_index,
                                        raw_value=cell,
                                        bounding_box=_normalized_bbox(
                                            geometry,
                                            page_width=float(page.width),
                                            page_height=float(page.height),
                                        ),
                                    ))
                            total_tables += 1
                            total_cells += cell_count
                        remaining = policy.maximum_characters - total_characters
                        status = ExtractionStatus.COMPLETE
                        if len(text) > remaining:
                            text = text[:max(0, remaining)]
                            warnings.append("Page text truncated by extraction limit")
                            status = ExtractionStatus.PARTIAL
                        total_characters += len(text)
                        if warnings and status is ExtractionStatus.COMPLETE:
                            status = ExtractionStatus.PARTIAL
                        pages.append(ExtractedPageV1(
                            page_index=page_index,
                            page_label=str(page_index + 1),
                            status=status,
                            text=text,
                            tables=tuple(tables),
                            cell_locators=tuple(cell_locators),
                            warnings=tuple(warnings),
                        ))
                    except DocumentExtractionLimitExceeded:
                        raise
                    except Exception:
                        pages.append(ExtractedPageV1(
                            page_index=page_index,
                            page_label=str(page_index + 1),
                            status=ExtractionStatus.FAILED,
                            text="",
                            warnings=("Page content could not be extracted",),
                        ))
        except DocumentExtractionError:
            raise
        except Exception as exc:
            raise DocumentExtractionError("PDF parsing failed") from exc

        failed_pages = sum(page.status is ExtractionStatus.FAILED for page in pages)
        partial_pages = sum(page.status is ExtractionStatus.PARTIAL for page in pages)
        if failed_pages == len(pages) and pages:
            status = ExtractionStatus.FAILED
        elif failed_pages or partial_pages:
            status = ExtractionStatus.PARTIAL
        else:
            status = ExtractionStatus.COMPLETE
        if policy.require_tables and total_tables == 0:
            document_warnings.append("No tables detected")
            if status is ExtractionStatus.COMPLETE:
                status = ExtractionStatus.PARTIAL
        core = {
            "schema_version": 1,
            "status": status.value,
            "media_type": "application/pdf",
            "page_count": len(pages),
            "pages": [page.model_dump(mode="json") for page in pages],
            "detected_languages": [],
            "warnings": document_warnings,
            "parser_id": self.parser_id,
            "parser_version": pdfplumber.__version__,
            "input_digest": source.content_digest,
        }
        return ExtractedDocumentV1(
            **core,
            output_digest=_digest_document(core),
        )
