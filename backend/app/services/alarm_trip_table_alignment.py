"""Bounded alignment for the SATCO alarm/trip table profile.

This module intentionally does not perform PDF extraction.  It accepts the raw
pdfplumber grid plus row-cell geometry and produces an aligned logical grid,
explicit repair events, and fail-closed Tag-to-setpoint bindings.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import re

from app.services.table_cell_provenance import table_cell_locator_id


TAG_COLUMN = 9
MERGED_LEFT_COLUMN = 8
SETPOINT_COLUMNS = (18, 19, 20, 21, 22)
SETPOINT_LABELS = ("LL", "L", "M", "H", "HH")
TAG_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+$")
PROFILE_HEADERS = {
    9: "TAG NO. Merged",
    10: "COMPONENT\nFUNCTION",
    11: "INTERLOCK/LOOP\nID",
    12: "P & ID NO.",
    17: "OPERATING\nRANGE",
    18: "ALARM/TRIP SETPOINT",
    23: "UNIT",
    24: "NOTES",
    25: "Rev.",
}
def _digest(payload: object) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def raw_locator_id(document_digest: str, page_index: int, table_index: int,
                   row_index: int, column_index: int) -> str:
    return table_cell_locator_id(
        document_digest, page_index, table_index, row_index, column_index
    )


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _same(a: float, b: float, tolerance: float = 0.01) -> bool:
    return abs(a - b) <= tolerance


def _interval(cell):
    return None if cell is None else (cell[0], cell[2])


def _profile_header_rows(rows):
    return [
        index for index, row in enumerate(rows)
        if len(row) > SETPOINT_COLUMNS[-1]
        and row[TAG_COLUMN] == "TAG NO. Merged"
        and row[SETPOINT_COLUMNS[0]] == "ALARM/TRIP SETPOINT"
    ]


def profile_tables_from_extracted_document(document):
    """Build alignment input only when extractor provenance is coherent.

    Missing geometry is retained as ``None`` so downstream checks abstain;
    mismatched IDs or unresolved coordinates reject the entire conversion.
    """

    profiles = []
    for page in document.pages:
        by_position = {
            (item.table_index, item.row_index, item.column_index): item
            for item in page.cell_locators
        }
        expected_cells = sum(len(row) for table in page.tables for row in table)
        if page.tables and len(by_position) != expected_cells:
            raise ValueError("extracted cell locator coverage is incomplete")
        for table_index, table in enumerate(page.tables):
            rows = [[_text(cell) for cell in row] for row in table]
            if not _profile_header_rows(rows):
                continue
            row_cells = []
            for row_index, row in enumerate(rows):
                geometry_row = []
                for column_index, value in enumerate(row):
                    item = by_position.get((table_index, row_index, column_index))
                    if item is None or item.raw_value != value:
                        raise ValueError("extracted cell locator does not resolve")
                    expected_id = table_cell_locator_id(
                        document.input_digest,
                        page.page_index,
                        table_index,
                        row_index,
                        column_index,
                    )
                    if item.locator_id != expected_id:
                        raise ValueError("extracted cell locator identity mismatch")
                    bbox = item.bounding_box
                    geometry_row.append(
                        None if bbox is None else (bbox.x0, bbox.top, bbox.x1, bbox.bottom)
                    )
                row_cells.append(geometry_row)
            profiles.append({
                "page_index": page.page_index,
                "table_index": table_index,
                "table": rows,
                "row_cells": row_cells,
            })
    return profiles


def _merged_span_is_proven(row_cells, reference_left, reference_right) -> bool:
    if row_cells is None or len(row_cells) <= TAG_COLUMN:
        return False
    merged = row_cells[MERGED_LEFT_COLUMN]
    missing_target = row_cells[TAG_COLUMN] is None
    if merged is None or not missing_target or reference_left is None or reference_right is None:
        return False
    return (
        _same(merged[0], reference_left[0])
        and _same(merged[2], reference_right[2])
        and merged[2] > reference_left[2]
    )


def align_alarm_trip_table(table, row_cells=None, *, document_digest: str = "",
                           page_index: int = 0, table_index: int = 0):
    """Align the exact SATCO profile and bind tags to five setpoint cells.

    The fallback from column 8 to column 9 is permitted only when geometry
    proves a single PDF cell spans both canonical columns.  Any candidate that
    cannot be proven or bound to all five setpoint positions is rejected.
    """

    rows = [[_text(cell) for cell in row] for row in deepcopy(table)]
    header_rows = _profile_header_rows(rows)
    if not header_rows:
        return {
            "applicable": False,
            "qualified": True,
            "table": rows,
            "events": [],
            "bindings": [],
            "errors": [],
        }
    if len(header_rows) != 1:
        return {
            "applicable": True,
            "qualified": False,
            "table": rows,
            "events": [],
            "bindings": [],
            "errors": [{"reason": "non_unique_profile_header", "rows": header_rows}],
        }

    header = header_rows[0]
    subheader = header + 1
    if subheader >= len(rows) or tuple(rows[subheader][i] for i in SETPOINT_COLUMNS) != SETPOINT_LABELS:
        return {
            "applicable": True,
            "qualified": False,
            "table": rows,
            "events": [],
            "bindings": [],
            "errors": [{"reason": "setpoint_subheader_mismatch", "row_index": subheader}],
        }

    reference_left = reference_right = None
    if row_cells is not None:
        for index in range(subheader + 1, len(rows)):
            cells = row_cells[index]
            if len(cells) > TAG_COLUMN and cells[MERGED_LEFT_COLUMN] is not None and cells[TAG_COLUMN] is not None:
                reference_left = cells[MERGED_LEFT_COLUMN]
                reference_right = cells[TAG_COLUMN]
                break

    events = []
    bindings = []
    errors = []
    for row_index in range(subheader + 1, len(rows)):
        row = rows[row_index]
        if len(row) <= SETPOINT_COLUMNS[-1]:
            errors.append({"reason": "short_data_row", "row_index": row_index})
            continue
        is_data = bool(row[0] and row[3] and row[10])
        if not is_data:
            continue

        target_tag = row[TAG_COLUMN]
        source_column = TAG_COLUMN
        if not target_tag:
            candidate = row[MERGED_LEFT_COLUMN]
            geometry_ok = _merged_span_is_proven(
                row_cells[row_index] if row_cells is not None else None,
                reference_left,
                reference_right,
            )
            if not candidate or TAG_PATTERN.fullmatch(candidate) is None or not geometry_ok:
                errors.append({
                    "reason": "unproven_or_invalid_merged_tag",
                    "row_index": row_index,
                    "candidate": candidate,
                    "geometry_proven": geometry_ok,
                })
                continue
            source_column = MERGED_LEFT_COLUMN
            row[TAG_COLUMN] = candidate
            row[MERGED_LEFT_COLUMN] = ""
            target_tag = candidate
            events.append({
                "kind": "merged_cell_right_alignment",
                "row_index": row_index,
                "source_column_index": MERGED_LEFT_COLUMN,
                "target_column_index": TAG_COLUMN,
                "value": candidate,
                "source_locator_id": raw_locator_id(
                    document_digest, page_index, table_index, row_index, MERGED_LEFT_COLUMN
                ),
            })

        if TAG_PATTERN.fullmatch(target_tag) is None:
            errors.append({
                "reason": "invalid_canonical_tag",
                "row_index": row_index,
                "value": target_tag,
            })
            continue
        setpoints = [row[index] for index in SETPOINT_COLUMNS]
        if any(value == "" for value in setpoints):
            errors.append({
                "reason": "incomplete_setpoint_tuple",
                "row_index": row_index,
                "tag": target_tag,
                "values": setpoints,
            })
            continue
        bindings.append({
            "row_index": row_index,
            "tag": target_tag,
            "tag_logical_column_index": TAG_COLUMN,
            "tag_source_column_index": source_column,
            "tag_source_locator_id": raw_locator_id(
                document_digest, page_index, table_index, row_index, source_column
            ),
            "setpoints": [
                {
                    "label": label,
                    "column_index": column_index,
                    "value": row[column_index],
                    "source_locator_id": raw_locator_id(
                        document_digest, page_index, table_index, row_index, column_index
                    ),
                }
                for label, column_index in zip(SETPOINT_LABELS, SETPOINT_COLUMNS)
            ],
        })

    data_rows = sum(
        bool(row[0] and row[3] and row[10])
        for row in rows[subheader + 1:]
        if len(row) > 10
    )
    qualified = not errors and len(bindings) == data_rows
    if len(bindings) != data_rows and not errors:
        errors.append({
            "reason": "binding_count_mismatch",
            "data_rows": data_rows,
            "bindings": len(bindings),
        })
        qualified = False
    return {
        "applicable": True,
        "qualified": qualified,
        "table": rows,
        "events": events,
        "bindings": bindings,
        "errors": errors,
    }


def _metadata_errors(rows, *, page_number: int, total_pages: int, expected_metadata: dict):
    expected = (
        (1, 11, expected_metadata["document_title"], "document_title_mismatch"),
        (1, 24, expected_metadata["document_revision"], "document_revision_mismatch"),
        (2, 11, expected_metadata["document_number"], "document_number_mismatch"),
        (2, 24, f"Page {page_number} of {total_pages}", "page_label_mismatch"),
    )
    errors = []
    for row_index, column_index, value, reason in expected:
        actual = rows[row_index][column_index] if row_index < len(rows) and column_index < len(rows[row_index]) else None
        if actual != value:
            errors.append({
                "reason": reason,
                "row_index": row_index,
                "column_index": column_index,
                "expected": value,
                "actual": actual,
            })
    return errors


def _header_errors(rows, header_index: int):
    errors = []
    if header_index >= len(rows):
        return [{"reason": "missing_profile_header"}]
    row = rows[header_index]
    for column_index, expected in PROFILE_HEADERS.items():
        actual = row[column_index] if column_index < len(row) else None
        if actual != expected:
            errors.append({
                "reason": "profile_header_mismatch",
                "row_index": header_index,
                "column_index": column_index,
                "expected": expected,
                "actual": actual,
            })
    return errors


def _derive_anchor_layout(rows, row_cells, header_index: int):
    if row_cells is None or len(row_cells) != len(rows):
        return None, [{"reason": "anchor_geometry_missing"}]
    relevant = (TAG_COLUMN, *SETPOINT_COLUMNS)
    for row_index in range(header_index + 2, len(rows)):
        cells = row_cells[row_index]
        if len(cells) > SETPOINT_COLUMNS[-1] and all(cells[index] is not None for index in relevant):
            intervals = {index: _interval(cells[index]) for index in relevant}
            return {
                "columns": intervals,
                "source_row_index": row_index,
            }, []
    return None, [{"reason": "anchor_reference_geometry_missing"}]


def _geometry_errors(row_cells, start_row: int, rows, layout, tolerance: float):
    errors = []
    if row_cells is None or len(row_cells) != len(rows):
        return [{"reason": "continuation_geometry_missing"}]
    for row_index in range(start_row, len(rows)):
        row = rows[row_index]
        if len(row) <= SETPOINT_COLUMNS[-1] or not (row[0] and row[3] and row[10]):
            continue
        cells = row_cells[row_index]
        for column_index in (TAG_COLUMN, *SETPOINT_COLUMNS):
            actual = _interval(cells[column_index]) if len(cells) > column_index else None
            expected = layout["columns"][column_index]
            if actual is None or not (_same(actual[0], expected[0], tolerance) and _same(actual[1], expected[1], tolerance)):
                errors.append({
                    "reason": "logical_column_geometry_mismatch",
                    "row_index": row_index,
                    "column_index": column_index,
                    "expected": expected,
                    "actual": actual,
                })
    return errors


def _bind_continuation_rows(rows, *, start_row: int, document_digest: str,
                            page_index: int, table_index: int,
                            schema_provenance: dict):
    bindings = []
    errors = []
    data_rows = 0
    for row_index in range(start_row, len(rows)):
        row = rows[row_index]
        if len(row) <= SETPOINT_COLUMNS[-1]:
            errors.append({"reason": "short_data_row", "row_index": row_index})
            continue
        if not (row[0] and row[3] and row[10]):
            continue
        data_rows += 1
        tag = row[TAG_COLUMN]
        if TAG_PATTERN.fullmatch(tag) is None:
            errors.append({"reason": "invalid_canonical_tag", "row_index": row_index, "value": tag})
            continue
        setpoints = [row[index] for index in SETPOINT_COLUMNS]
        if any(value == "" for value in setpoints):
            errors.append({
                "reason": "incomplete_setpoint_tuple",
                "row_index": row_index,
                "tag": tag,
                "values": setpoints,
            })
            continue
        bindings.append({
            "row_index": row_index,
            "tag": tag,
            "tag_logical_column_index": TAG_COLUMN,
            "tag_source_column_index": TAG_COLUMN,
            "tag_source_locator_id": raw_locator_id(
                document_digest, page_index, table_index, row_index, TAG_COLUMN
            ),
            "schema_provenance": schema_provenance,
            "setpoints": [
                {
                    "label": label,
                    "column_index": column_index,
                    "value": row[column_index],
                    "source_locator_id": raw_locator_id(
                        document_digest, page_index, table_index, row_index, column_index
                    ),
                }
                for label, column_index in zip(SETPOINT_LABELS, SETPOINT_COLUMNS)
            ],
        })
    if len(bindings) != data_rows and not errors:
        errors.append({"reason": "binding_count_mismatch", "data_rows": data_rows, "bindings": len(bindings)})
    return bindings, errors, data_rows


def align_alarm_trip_document(profile_tables, *, document_digest: str,
                              expected_metadata: dict,
                              anchor_page_index: int = 5,
                              last_page_index: int = 20,
                              total_pages: int = 21,
                              geometry_tolerance: float = 0.02):
    """Qualify an anchored sequence of SATCO Alarm & Trip continued tables.

    `expected_metadata` is authoritative caller input, never inferred from a
    filename or profile value. `profile_tables` contains page/table/grid and
    and row_cells.  A continuation inherits LL/L/M/H/HH only from the locally
    labelled anchor and only while metadata, page order, headers, and the six
    relevant ruled-column intervals remain invariant.  A failure breaks the
    chain and all later pages abstain.
    """

    items_by_page = {}
    duplicate_pages = []
    for item in profile_tables:
        page_index = item["page_index"]
        if page_index in items_by_page:
            duplicate_pages.append(page_index)
        items_by_page[page_index] = item
    required_metadata = ("document_title", "document_number", "document_revision")
    missing_metadata = [
        key for key in required_metadata
        if not str(expected_metadata.get(key, "")).strip()
    ]
    global_errors = []
    if missing_metadata:
        global_errors.append({
            "reason": "authoritative_metadata_missing",
            "fields": missing_metadata,
        })
    if duplicate_pages:
        global_errors.append({"reason": "duplicate_profile_page", "page_indexes": sorted(set(duplicate_pages))})
    expected_pages = list(range(anchor_page_index, last_page_index + 1))
    missing_pages = [page for page in expected_pages if page not in items_by_page]
    if missing_pages:
        global_errors.append({"reason": "missing_profile_page", "page_indexes": missing_pages})

    page_results = []
    anchor_item = items_by_page.get(anchor_page_index)
    if anchor_item is None or global_errors:
        return {
            "qualified": False,
            "pages_expected": len(expected_pages),
            "pages_qualified": 0,
            "bindings": [],
            "events": [],
            "page_results": [],
            "errors": global_errors or [{"reason": "anchor_missing"}],
        }

    anchor_rows = [[_text(cell) for cell in row] for row in deepcopy(anchor_item["table"])]
    anchor_headers = _profile_header_rows(anchor_rows)
    anchor_result = align_alarm_trip_table(
        anchor_rows,
        anchor_item.get("row_cells"),
        document_digest=document_digest,
        page_index=anchor_page_index,
        table_index=anchor_item["table_index"],
    )
    anchor_errors = _metadata_errors(
        anchor_rows, page_number=anchor_page_index + 1, total_pages=total_pages,
        expected_metadata=expected_metadata,
    )
    if len(anchor_headers) != 1:
        anchor_errors.append({"reason": "anchor_profile_header_not_unique", "rows": anchor_headers})
        layout = None
    else:
        anchor_errors.extend(_header_errors(anchor_rows, anchor_headers[0]))
        layout, layout_errors = _derive_anchor_layout(
            anchor_rows, anchor_item.get("row_cells"), anchor_headers[0]
        )
        anchor_errors.extend(layout_errors)
    anchor_errors.extend(anchor_result["errors"])
    anchor_qualified = anchor_result["qualified"] and not anchor_errors and layout is not None
    page_results.append({
        "page_number": anchor_page_index + 1,
        "page_index": anchor_page_index,
        "table_index": anchor_item["table_index"],
        "kind": "anchor",
        "qualified": anchor_qualified,
        "data_rows": len(anchor_result["bindings"]),
        "bindings": anchor_result["bindings"] if anchor_qualified else [],
        "events": anchor_result["events"] if anchor_qualified else [],
        "errors": anchor_errors,
    })
    chain_valid = anchor_qualified
    schema_provenance = None
    if chain_valid:
        schema_provenance = {
            "kind": "anchored_continued_table_schema",
            "anchor_page_index": anchor_page_index,
            "anchor_table_index": anchor_item["table_index"],
            "anchor_header_row_index": anchor_headers[0],
            "anchor_subheader_row_index": anchor_headers[0] + 1,
            "label_locator_ids": [
                raw_locator_id(
                    document_digest, anchor_page_index, anchor_item["table_index"],
                    anchor_headers[0] + 1, column_index
                )
                for column_index in SETPOINT_COLUMNS
            ],
            "labels": list(SETPOINT_LABELS),
            "column_intervals": {str(key): list(value) for key, value in layout["columns"].items()},
            "proof_digest": _digest({
                "document_digest": document_digest,
                "anchor_page_index": anchor_page_index,
                "labels": SETPOINT_LABELS,
                "columns": layout["columns"],
                "headers": PROFILE_HEADERS,
            }),
        }

    for page_index in range(anchor_page_index + 1, last_page_index + 1):
        item = items_by_page.get(page_index)
        errors = []
        bindings = []
        data_rows = 0
        if not chain_valid:
            errors.append({"reason": "continuation_chain_broken"})
        elif item is None:
            errors.append({"reason": "missing_profile_page"})
        else:
            rows = [[_text(cell) for cell in row] for row in deepcopy(item["table"])]
            headers = _profile_header_rows(rows)
            if len(headers) != 1:
                errors.append({"reason": "continuation_profile_header_not_unique", "rows": headers})
                header_index = None
            else:
                header_index = headers[0]
                errors.extend(_header_errors(rows, header_index))
                errors.extend(_metadata_errors(
                    rows, page_number=page_index + 1, total_pages=total_pages,
                    expected_metadata=expected_metadata,
                ))
                if header_index + 1 < len(rows) and tuple(
                    rows[header_index + 1][column] for column in SETPOINT_COLUMNS
                ) == SETPOINT_LABELS:
                    errors.append({"reason": "unexpected_repeated_subheader"})
                start_row = header_index + 1
                errors.extend(_geometry_errors(
                    item.get("row_cells"), start_row, rows, layout, geometry_tolerance
                ))
                if not errors:
                    bindings, binding_errors, data_rows = _bind_continuation_rows(
                        rows,
                        start_row=start_row,
                        document_digest=document_digest,
                        page_index=page_index,
                        table_index=item["table_index"],
                        schema_provenance=schema_provenance,
                    )
                    errors.extend(binding_errors)
        qualified = not errors and bool(bindings)
        if not qualified:
            bindings = []
            chain_valid = False
        page_results.append({
            "page_number": page_index + 1,
            "page_index": page_index,
            "table_index": item["table_index"] if item is not None else None,
            "kind": "continuation",
            "qualified": qualified,
            "data_rows": data_rows,
            "bindings": bindings,
            "events": ([{
                "kind": "continued_table_schema_inheritance",
                "schema_proof_digest": schema_provenance["proof_digest"],
                "anchor_page_index": anchor_page_index,
                "page_index": page_index,
            }] if qualified else []),
            "errors": errors,
        })

    all_bindings = [
        {"page_index": page["page_index"], **binding}
        for page in page_results for binding in page["bindings"]
    ]
    all_events = [event for page in page_results for event in page["events"]]
    all_errors = [
        {"page_index": page["page_index"], **error}
        for page in page_results for error in page["errors"]
    ]
    pages_qualified = sum(page["qualified"] for page in page_results)
    return {
        "qualified": not global_errors and pages_qualified == len(expected_pages),
        "pages_expected": len(expected_pages),
        "pages_qualified": pages_qualified,
        "bindings": all_bindings,
        "events": all_events,
        "page_results": page_results,
        "schema_provenance": schema_provenance,
        "errors": [*global_errors, *all_errors],
    }
