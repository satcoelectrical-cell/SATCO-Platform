"""Canonical identities for deterministic extracted table cells."""

from hashlib import sha256
import json


def table_cell_locator_id(
    document_digest: str,
    page_index: int,
    table_index: int,
    row_index: int,
    column_index: int,
) -> str:
    """Return the stable identity shared by extraction and alignment.

    Cell values and processing-layer names are deliberately excluded: the
    locator identifies a position in one immutable document representation.
    """

    payload = {
        "column_index": column_index,
        "document_digest": document_digest,
        "page_index": page_index,
        "row_index": row_index,
        "table_index": table_index,
    }
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
