from datetime import datetime, timezone
from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.adapters.supporting_file_object_store import InMemoryPrivateSupportingFileObjectStore
from app.models.document_intelligence import (
    DocumentAnalysisRun,
    DocumentEngineeringCandidate,
    SourceLocatorRecord,
)
from app.services.document_intelligence_service import (
    DocumentIntelligenceProtectedNotFound,
    DocumentIntelligenceService,
)


def _run():
    now = datetime.now(timezone.utc)
    return DocumentAnalysisRun(
        id=uuid4(), organization_id=uuid4(), project_id=4, workspace_id=8,
        supporting_file_asset_id=uuid4(), source_asset_version=2,
        source_storage_object_version="object-v2", source_content_digest="a" * 64,
        safe_filename="engineering source.pdf", media_type="application/pdf",
        state="requires_review", progress_completed=1, progress_total=1,
        customer_message="Review required", page_count=1, candidate_count=1,
        unreviewed_count=1, limitations=[], provider_status="disabled",
        created_by_id=2, version=3, created_at=now, updated_at=now,
    )


def test_candidate_projection_includes_exact_immutable_locator():
    run = _run()
    now = datetime.now(timezone.utc)
    candidate = DocumentEngineeringCandidate(
        id=uuid4(), analysis_run_id=run.id, ordinal=0,
        kind="engineering_value", assertion_mode="direct",
        review_state="unreviewed", subject_key="item_a", subject_label="Item A",
        raw_value="12 bar", normalized_value="12", numeric_value=Decimal("12"),
        unit="bar", quantity_type="pressure", confidence=Decimal("0.9000"),
        confidence_rationale="Direct table cell", assumptions=[],
        proposed_canonical_target="engineering_context_value",
        version=1, created_at=now, updated_at=now,
    )
    locator = SourceLocatorRecord(
        id=uuid4(), schema_version=1, locator_kind="table_cell",
        supporting_file_asset_id=run.supporting_file_asset_id,
        asset_version_at_analysis=run.source_asset_version,
        storage_object_version=run.source_storage_object_version,
        digest_algorithm="sha256", content_digest=run.source_content_digest,
        media_type="application/pdf", page_index=0, page_label="1",
        section_path=[], table_key="page-1-table-1", row_index=1,
        row_label="Item A", column_index=1, column_label="Pressure",
        text_excerpt="12 bar", extraction_method="deterministic",
        locator_digest="b" * 64, created_at=now,
    )
    session = MagicMock()
    service = DocumentIntelligenceService(session)
    service._authorize_scope = MagicMock()
    service.repository = MagicMock()
    service.repository.get_run.return_value = run
    service.repository.list_candidates.return_value = [candidate]
    service.repository.promotion_receipt.return_value = None
    service.repository.candidate_locators.return_value = [
        (SimpleNamespace(candidate_id=candidate.id), locator)
    ]

    result = service.list_candidates(
        project_id=run.project_id, run_id=run.id,
        user=SimpleNamespace(id=2, is_active=True, role="engineer"),
        organization_id=run.organization_id,
    )

    assert result.total == result.unreviewed_count == 1
    projected = result.items[0]
    assert tuple(action.value for action in projected.allowed_actions) == (
        "accept", "correct", "reject", "defer",
    )
    assert projected.locators[0].page_index == 0
    assert projected.locators[0].row_index == 1
    assert projected.locators[0].column_index == 1
    assert projected.locators[0].content_digest == run.source_content_digest


def test_source_preview_uses_bound_object_after_lifecycle_version_change():
    payload = b"%PDF-1.4 exact immutable source"
    objects = InMemoryPrivateSupportingFileObjectStore()
    receipt = objects.put_private(
        key=f"objects/{'c' * 64}", content=BytesIO(payload),
        media_type="application/pdf",
    )
    run = _run()
    run.source_storage_object_version = receipt.version
    run.source_content_digest = receipt.sha256
    asset = SimpleNamespace(
        id=run.supporting_file_asset_id, version=3, lifecycle="withdrawn",
        object_version=receipt.version, content_digest=receipt.sha256,
        storage_key=receipt.key,
    )
    session = MagicMock()
    session.query.return_value.filter_by.return_value.first.return_value = asset
    service = DocumentIntelligenceService(session)
    service._authorize_scope = MagicMock()
    service.repository = MagicMock()
    service.repository.get_run.return_value = run

    returned_run, byte_size, stream = service.open_source(
        project_id=run.project_id, run_id=run.id,
        user=SimpleNamespace(id=2, is_active=True, role="engineer"),
        organization_id=run.organization_id, objects=objects,
    )

    assert returned_run is run
    assert byte_size == len(payload)
    assert stream.read() == payload


def test_source_preview_authorizes_before_object_access():
    service = DocumentIntelligenceService(MagicMock())
    service.repository = MagicMock()
    service.repository.get_run.return_value = None
    objects = MagicMock()

    with pytest.raises(DocumentIntelligenceProtectedNotFound):
        service.open_source(
            project_id=4, run_id=uuid4(),
            user=SimpleNamespace(id=2, is_active=True, role="engineer"),
            organization_id=uuid4(), objects=objects,
        )

    objects.head_exact.assert_not_called()
