from datetime import datetime, timezone
import os
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

# Import-time database configuration is validated, but this pure unit test
# never opens a connection.
os.environ.setdefault("DATABASE_HOST", "127.0.0.1")
os.environ.setdefault("DATABASE_PORT", "55433")
os.environ.setdefault("DATABASE_USER", "unit_test")
os.environ.setdefault("DATABASE_PASSWORD", "unit_test")
os.environ.setdefault("DATABASE_NAME", "satco_platform_patch02022_test")

from app.services.document_intelligence_service import DocumentIntelligenceService


def _locator(*, excerpt: str):
    return SimpleNamespace(
        id=uuid4(), schema_version=1, locator_kind="text_span",
        supporting_file_asset_id=uuid4(), asset_version_at_analysis=2,
        storage_object_version="object-version", digest_algorithm="sha256",
        content_digest="c" * 64, media_type="application/pdf",
        page_index=0, page_label="1", section_path=[], section_title=None,
        table_key=None, table_title=None, row_index=None, row_label=None,
        column_index=None, column_label=None, text_start=0,
        text_end=len(excerpt), text_excerpt=excerpt,
        text_excerpt_digest="d" * 64, bbox_x0=None, bbox_y0=None,
        bbox_x1=None, bbox_y1=None, source_revision_label=None,
        extraction_method="deterministic", created_at=datetime.now(timezone.utc),
    )


def test_evidence_binding_survives_reversed_uuid_order_and_multiple_locators():
    high_candidate_id = UUID("ffffffff-ffff-4fff-8fff-ffffffffffff")
    low_candidate_id = UUID("00000000-0000-4000-8000-000000000001")
    pid_run_id, control_run_id = uuid4(), uuid4()
    candidates = {
        high_candidate_id: SimpleNamespace(analysis_run_id=pid_run_id),
        low_candidate_id: SimpleNamespace(analysis_run_id=control_run_id),
    }
    pid_first = _locator(excerpt="P&ID fail position: Fail Closed")
    pid_second = _locator(excerpt="P&ID design pressure: 12 bar")
    control = _locator(excerpt="Control Narrative fail position: Fail Open")
    # Repository ordering is UUID/ordinal based and intentionally differs from
    # the correlation's left/right run order.
    rows = (
        (SimpleNamespace(candidate_id=low_candidate_id), control),
        (SimpleNamespace(candidate_id=high_candidate_id), pid_first),
        (SimpleNamespace(candidate_id=high_candidate_id), pid_second),
    )

    bound = DocumentIntelligenceService._bound_evidence_sources(candidates, rows)

    assert [item.analysis_run_id for item in bound] == [
        control_run_id, pid_run_id, pid_run_id,
    ]
    assert [item.candidate_id for item in bound] == [
        low_candidate_id, high_candidate_id, high_candidate_id,
    ]
    assert [item.locator.text_excerpt for item in bound] == [
        "Control Narrative fail position: Fail Open",
        "P&ID fail position: Fail Closed",
        "P&ID design pressure: 12 bar",
    ]
    with pytest.raises(ValidationError):
        bound[0].candidate_id = high_candidate_id
