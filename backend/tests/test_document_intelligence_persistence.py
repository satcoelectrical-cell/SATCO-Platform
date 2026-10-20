from datetime import datetime, timezone
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.core.database import Base
from app.enums.document_intelligence import DocumentAnalysisState
from app.models.document_intelligence import DocumentAnalysisRun
from app.services.document_intelligence_service import (
    DocumentIntelligenceConflict,
    DocumentIntelligenceService,
    _fingerprint,
)


def _run(state: str = DocumentAnalysisState.FAILED_RETRYABLE.value):
    now = datetime.now(timezone.utc)
    return DocumentAnalysisRun(
        id=uuid4(),
        organization_id=uuid4(),
        project_id=7,
        workspace_id=13,
        supporting_file_asset_id=uuid4(),
        source_asset_version=2,
        source_storage_object_version="object-v2",
        source_content_digest="a" * 64,
        safe_filename="engineering-source.pdf",
        media_type="application/pdf",
        state=state,
        progress_completed=1,
        progress_total=1,
        customer_message="Retry available",
        limitations=[],
        candidate_count=0,
        unreviewed_count=0,
        created_by_id=23,
        version=4,
        created_at=now,
        updated_at=now,
    )


def _service_for_retry(run, asset):
    session = MagicMock()
    session.query.return_value.filter_by.return_value.first.return_value = asset
    service = DocumentIntelligenceService(session)
    service._authorize_scope = MagicMock()
    service.repository = MagicMock()
    service.repository.get_run.side_effect = lambda **kwargs: (
        run if kwargs["run_id"] == run.id else None
    )
    service.repository.idempotency.return_value = None
    return service


def test_document_intelligence_metadata_registers_append_only_history():
    expected = {
        "document_analysis_runs",
        "document_analysis_pages",
        "source_locators",
        "document_engineering_candidates",
        "candidate_source_locator_links",
        "evidence_source_locator_links",
        "document_candidate_reviews",
        "document_promotion_receipts",
        "document_correlations",
        "document_findings",
        "document_intelligence_idempotency",
        "document_intelligence_outbox",
    }
    assert expected <= set(Base.metadata.tables)


def test_retry_creates_successor_and_supersedes_predecessor():
    run = _run()
    asset = SimpleNamespace(
        id=run.supporting_file_asset_id,
        lifecycle="available",
        version=run.source_asset_version,
        object_version=run.source_storage_object_version,
        content_digest=run.source_content_digest,
    )
    service = _service_for_retry(run, asset)

    result = service.retry(
        project_id=run.project_id,
        run_id=run.id,
        expected_version=run.version,
        user=SimpleNamespace(id=23, is_active=True, role="engineer"),
        organization_id=run.organization_id,
        idempotency_id=uuid4(),
        correlation_id=uuid4(),
    )

    successor = service.repository.add_run.call_args.args[0]
    assert result.analysis_run_id == successor.id
    assert result.state is DocumentAnalysisState.QUEUED
    assert successor.source_content_digest == run.source_content_digest
    assert run.state == DocumentAnalysisState.SUPERSEDED.value
    assert run.superseded_by_run_id == successor.id
    service.repository.commit.assert_called_once()


def test_retry_refuses_to_rebind_history_after_source_revision():
    run = _run()
    asset = SimpleNamespace(
        id=run.supporting_file_asset_id,
        lifecycle="available",
        version=run.source_asset_version + 1,
        object_version="object-v3",
        content_digest="b" * 64,
    )
    service = _service_for_retry(run, asset)

    with pytest.raises(DocumentIntelligenceConflict):
        service.retry(
            project_id=run.project_id,
            run_id=run.id,
            expected_version=run.version,
            user=SimpleNamespace(id=23, is_active=True, role="engineer"),
            organization_id=run.organization_id,
            idempotency_id=uuid4(),
            correlation_id=uuid4(),
        )

    assert run.state == DocumentAnalysisState.SOURCE_CHANGED.value
    assert DocumentIntelligenceService._allowed_actions(run) == (
        "open",
        "start_new_analysis",
    )
    service.repository.commit.assert_called_once()


def test_idempotency_fingerprint_is_canonical_and_operation_bound():
    assert _fingerprint("create", {"a": 1, "b": 2}) == _fingerprint(
        "create", {"b": 2, "a": 1}
    )
    assert _fingerprint("create", {"a": 1}) != _fingerprint(
        "retry", {"a": 1}
    )


def test_migration_is_linear_append_only_and_runtime_delete_free():
    backend_root = Path(
        os.environ.get("SATCO_TEST_SOURCE_ROOT", Path(__file__).parents[1])
    )
    migration = backend_root / "migrations" / "versions" / (
        "di0000000001_document_intelligence_foundation.py"
    )
    source = migration.read_text()
    assert 'down_revision = "e05900000002"' in source
    assert "document_intelligence_immutable_history_guard" in source
    assert "BEFORE UPDATE OR DELETE" in source
    assert "GRANT UPDATE(published_at)" in source
    assert "GRANT DELETE" not in source
    assert "Cannot discard populated Document Intelligence history" in source
