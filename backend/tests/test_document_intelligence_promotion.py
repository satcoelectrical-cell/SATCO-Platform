from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.models.document_intelligence import (
    DocumentAnalysisRun,
    DocumentEngineeringCandidate,
    DocumentPromotionReceipt,
    EvidenceSourceLocatorLink,
    SourceLocatorRecord,
)
from app.models.evidence import Evidence
from app.models.supporting_file import EvidenceSupportingFileLink
from app.schemas.document_intelligence import DocumentPromotionRequest
from app.services.document_intelligence_service import (
    DocumentIntelligenceConflict,
    DocumentIntelligenceInvalidRequest,
    DocumentIntelligenceService,
)


def _records(review_state="accepted"):
    now = datetime.now(timezone.utc)
    run = DocumentAnalysisRun(
        id=uuid4(), organization_id=uuid4(), project_id=4, workspace_id=8,
        supporting_file_asset_id=uuid4(), source_asset_version=2,
        source_storage_object_version="object-v2", source_content_digest="a" * 64,
        safe_filename="source.pdf", media_type="application/pdf",
        state="completed", progress_completed=1, progress_total=1,
        customer_message="Human review completed", page_count=1,
        candidate_count=1, unreviewed_count=0, limitations=[],
        created_by_id=2, version=4, created_at=now, updated_at=now,
    )
    candidate = DocumentEngineeringCandidate(
        id=uuid4(), analysis_run_id=run.id, ordinal=0,
        kind="engineering_value", assertion_mode="direct",
        review_state=review_state, subject_key="item_a", subject_label="Item A",
        raw_value="12 bar", normalized_value="12", numeric_value=Decimal("12"),
        unit="bar", quantity_type="pressure", condition="Normal operation",
        confidence=Decimal("0.9000"), confidence_rationale="Direct table cell",
        assumptions=[], proposed_canonical_target="engineering_context_value",
        reviewed_by_id=17, reviewed_at=now, version=2,
        created_at=now, updated_at=now,
    )
    locator = SourceLocatorRecord(
        id=uuid4(), schema_version=1, locator_kind="table_cell",
        supporting_file_asset_id=run.supporting_file_asset_id,
        asset_version_at_analysis=2, storage_object_version="object-v2",
        digest_algorithm="sha256", content_digest="a" * 64,
        media_type="application/pdf", page_index=0, page_label="1",
        section_path=[], table_key="page-1-table-1", row_index=1,
        row_label="Item A", column_index=1, column_label="Pressure",
        text_excerpt="12 bar", extraction_method="deterministic",
        locator_digest="b" * 64, created_at=now,
    )
    asset = SimpleNamespace(
        id=run.supporting_file_asset_id, version=2, lifecycle="available",
        object_version=run.source_storage_object_version,
        content_digest=run.source_content_digest,
    )
    return run, candidate, locator, asset


def _service(run, candidate, locator, asset):
    session = MagicMock()
    session.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = asset
    added = []
    session.add.side_effect = added.append
    service = DocumentIntelligenceService(session)
    service._authorize_scope = MagicMock()
    service.repository = MagicMock()
    service.repository.get_run.return_value = run
    service.repository.get_candidate.return_value = candidate
    service.repository.idempotency.return_value = None
    service.repository.promotion_receipt.return_value = None
    service.repository.candidate_locators.return_value = [
        (SimpleNamespace(candidate_id=candidate.id), locator)
    ]
    return service, added


def _promote(service, run, candidate, include_context=True):
    return service.promote_candidate(
        project_id=run.project_id, run_id=run.id, candidate_id=candidate.id,
        data=DocumentPromotionRequest(
            expected_candidate_version=candidate.version,
            include_engineering_context=include_context,
            rationale="Promote the exact Human-reviewed assertion",
        ),
        user=SimpleNamespace(id=17, is_active=True, role="engineer"),
        organization_id=run.organization_id,
        idempotency_id=uuid4(), correlation_id=uuid4(),
    )


def test_reviewed_candidate_promotes_atomically_to_evidence_and_context():
    run, candidate, locator, asset = _records()
    service, added = _service(run, candidate, locator, asset)
    with patch(
        "app.services.document_intelligence_service.EngineeringContextService.create_context",
        return_value={"id": 501},
    ) as create_context:
        result = _promote(service, run, candidate)

    evidence = next(value for value in added if isinstance(value, Evidence))
    receipt = next(value for value in added if isinstance(value, DocumentPromotionReceipt))
    file_link = next(value for value in added if isinstance(value, EvidenceSupportingFileLink))
    locator_link = next(value for value in added if isinstance(value, EvidenceSourceLocatorLink))
    assert result.promotion_receipt_id == receipt.id
    assert result.evidence_id == evidence.id == file_link.evidence_id == locator_link.evidence_id
    assert result.evidence_version == evidence.version == 2
    assert result.evidence_lifecycle == "proposed"
    assert result.engineering_context_id == 501
    assert locator_link.source_locator_id == locator.id
    assert evidence.source_revision.endswith(run.source_content_digest)
    assert evidence.lifecycle == "proposed"
    assert create_context.call_args.kwargs["commit"] is False
    assert create_context.call_args.kwargs["authority"].value == "authoritative_fact"
    service.session.flush.assert_called_once_with()
    service.repository.commit.assert_called_once()


def test_evidence_only_promotion_does_not_create_engineering_context():
    run, candidate, locator, asset = _records()
    service, added = _service(run, candidate, locator, asset)
    with patch(
        "app.services.document_intelligence_service.EngineeringContextService.create_context"
    ) as create_context:
        result = _promote(service, run, candidate, include_context=False)
    assert result.engineering_context_id is None
    create_context.assert_not_called()
    assert any(isinstance(value, Evidence) for value in added)
    service.session.flush.assert_called_once_with()


@pytest.mark.parametrize("state", ["unreviewed", "deferred", "rejected"])
def test_non_accepted_candidate_cannot_promote(state):
    run, candidate, locator, asset = _records(state)
    service, added = _service(run, candidate, locator, asset)
    with pytest.raises(DocumentIntelligenceInvalidRequest):
        _promote(service, run, candidate)
    assert added == []
    service.repository.commit.assert_not_called()


def test_promotion_refuses_source_version_rebinding():
    run, candidate, locator, asset = _records()
    asset.version = 3
    service, added = _service(run, candidate, locator, asset)
    with pytest.raises(DocumentIntelligenceConflict):
        _promote(service, run, candidate)
    assert added == []
