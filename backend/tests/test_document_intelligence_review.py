from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.document_intelligence import (
    DocumentAnalysisRun,
    DocumentCandidateReview,
    DocumentEngineeringCandidate,
    DocumentIntelligenceIdempotency,
    DocumentIntelligenceOutbox,
    SourceLocatorRecord,
)
from app.schemas.document_intelligence import (
    CandidateCorrection,
    CandidateReviewRequest,
    EngineeringCandidateValue,
)
from app.services.document_intelligence_service import (
    DocumentIntelligenceConflict,
    DocumentIntelligenceProtectedNotFound,
    DocumentIntelligenceService,
)


def _records():
    now = datetime.now(timezone.utc)
    run = DocumentAnalysisRun(
        id=uuid4(), organization_id=uuid4(), project_id=4, workspace_id=8,
        supporting_file_asset_id=uuid4(), source_asset_version=2,
        source_storage_object_version="object-v2", source_content_digest="a" * 64,
        safe_filename="source.pdf", media_type="application/pdf",
        state="requires_review", progress_completed=1, progress_total=1,
        customer_message="1 candidate requires review", page_count=1,
        candidate_count=1, unreviewed_count=1, limitations=[],
        created_by_id=2, version=3, created_at=now, updated_at=now,
    )
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
        asset_version_at_analysis=2, storage_object_version="object-v2",
        digest_algorithm="sha256", content_digest="a" * 64,
        media_type="application/pdf", page_index=0, page_label="1",
        section_path=[], table_key="page-1-table-1", row_index=1,
        row_label="Item A", column_index=1, column_label="Pressure",
        text_excerpt="12 bar", extraction_method="deterministic",
        locator_digest="b" * 64, created_at=now,
    )
    return run, candidate, locator


def _service(run, candidate, locator):
    session = MagicMock()
    added = []
    session.add.side_effect = added.append
    service = DocumentIntelligenceService(session)
    service._authorize_scope = MagicMock()
    service.repository = MagicMock()
    service.repository.get_run.return_value = run
    service.repository.get_candidate.return_value = candidate
    service.repository.idempotency.return_value = None
    service.repository.candidate_locators.return_value = [
        (SimpleNamespace(candidate_id=candidate.id), locator)
    ]
    return service, added


def _review(service, run, candidate, action, expected_version=None, correction=None):
    return service.review_candidate(
        project_id=run.project_id, run_id=run.id, candidate_id=candidate.id,
        data=CandidateReviewRequest(
            expected_version=expected_version or candidate.version,
            action=action, rationale=f"Human chose {action}", correction=correction,
        ),
        user=SimpleNamespace(id=17, is_active=True, role="engineer"),
        organization_id=run.organization_id,
        idempotency_id=uuid4(), correlation_id=uuid4(),
    )


@pytest.mark.parametrize("action,state", [
    ("accept", "accepted"), ("reject", "rejected"),
])
def test_terminal_human_review_is_audited_without_automatic_promotion(action, state):
    run, candidate, locator = _records()
    service, added = _service(run, candidate, locator)

    result = _review(service, run, candidate, action)

    assert result.review_state.value == state
    assert result.allowed_actions == ()
    assert run.unreviewed_count == 0
    assert run.state == "completed"
    assert any(isinstance(value, DocumentCandidateReview) for value in added)
    assert any(isinstance(value, DocumentIntelligenceIdempotency) for value in added)
    assert any(isinstance(value, DocumentIntelligenceOutbox) for value in added)
    assert not any(value.__class__.__name__ in {"Evidence", "EngineeringContext"} for value in added)
    service.repository.commit.assert_called_once()


def test_defer_remains_reviewable_then_human_can_accept():
    run, candidate, locator = _records()
    service, added = _service(run, candidate, locator)

    deferred = _review(service, run, candidate, "defer")
    assert deferred.review_state.value == "deferred"
    assert run.unreviewed_count == 1
    assert run.state == "requires_review"
    assert tuple(action.value for action in deferred.allowed_actions) == (
        "accept", "correct", "reject", "defer",
    )

    accepted = _review(service, run, candidate, "accept")
    assert accepted.review_state.value == "accepted"
    assert run.unreviewed_count == 0
    reviews = [value for value in added if isinstance(value, DocumentCandidateReview)]
    assert [review.candidate_version for review in reviews] == [1, 2]


def test_correct_records_before_and_after_and_updates_only_candidate():
    run, candidate, locator = _records()
    service, added = _service(run, candidate, locator)
    correction = CandidateCorrection(
        subject_key="item_a",
        subject_label="Item A",
        value=EngineeringCandidateValue(
            raw_value="12.5 bar", normalized_value="12.5",
            numeric_value=Decimal("12.5"), unit="bar", quantity_type="pressure",
        ),
        uncertainty="Confirmed against the source cell",
    )

    result = _review(service, run, candidate, "correct", correction=correction)

    assert result.review_state.value == "corrected"
    assert result.value.numeric_value == Decimal("12.5")
    review = next(value for value in added if isinstance(value, DocumentCandidateReview))
    assert review.correction["before"]["numeric_value"] == "12"
    assert review.correction["after"]["numeric_value"] == "12.5"


def test_review_enforces_optimistic_version():
    run, candidate, locator = _records()
    service, _added = _service(run, candidate, locator)
    with pytest.raises(DocumentIntelligenceConflict):
        _review(service, run, candidate, "accept", expected_version=99)
    service.repository.commit.assert_not_called()


def test_review_hides_candidate_until_scope_authorization_succeeds():
    run, candidate, locator = _records()
    service, _added = _service(run, candidate, locator)
    service._authorize_scope.side_effect = DocumentIntelligenceProtectedNotFound()

    with pytest.raises(DocumentIntelligenceProtectedNotFound):
        _review(service, run, candidate, "accept")

    service.repository.get_candidate.assert_not_called()
