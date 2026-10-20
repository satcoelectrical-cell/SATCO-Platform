from datetime import datetime, timezone
from hashlib import sha256
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.enums.document_intelligence import CandidateReviewAction, SourceLocatorKind
from app.schemas.document_intelligence import CandidateReviewRequest
from app.schemas.source_locator import SourceLocatorV1


def locator(**overrides):
    excerpt = "Pump discharge pressure"
    values = dict(
        locator_id=uuid4(), locator_kind=SourceLocatorKind.TEXT_SPAN,
        supporting_file_asset_id=uuid4(), asset_version_at_analysis=2,
        storage_object_version="private-object-version", content_digest="a" * 64,
        media_type="application/pdf", page_index=0, text_start=0,
        text_end=len(excerpt), text_excerpt=excerpt,
        text_excerpt_digest=sha256(excerpt.encode()).hexdigest(),
        extraction_method="deterministic", created_at=datetime.now(timezone.utc),
    )
    values.update(overrides)
    return values


def test_source_locator_binds_exact_source_and_page():
    item = SourceLocatorV1(**locator())
    assert item.page_index == 0
    assert item.digest_algorithm == "sha256"
    assert item.model_config["frozen"] is True


def test_non_document_locator_requires_page():
    with pytest.raises(ValidationError):
        SourceLocatorV1(**locator(page_index=None))


def test_table_cell_requires_complete_coordinates():
    with pytest.raises(ValidationError):
        SourceLocatorV1(**locator(
            locator_kind="table_cell", table_key="T1", row_index=0,
            column_index=None,
        ))


def test_review_correction_is_explicit_and_strict():
    with pytest.raises(ValidationError):
        CandidateReviewRequest(
            expected_version=1, action=CandidateReviewAction.CORRECT,
            rationale="Correct the normalized unit",
        )


def test_non_correction_rejects_correction_payload():
    with pytest.raises(ValidationError):
        CandidateReviewRequest(
            expected_version=1, action=CandidateReviewAction.ACCEPT,
            rationale="Reviewed against source",
            correction={"value": {"raw_value": "10 bar"}},
        )
