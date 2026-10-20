from datetime import datetime, timezone
from hashlib import sha256
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.document_intelligence import (
    DocumentCorrelation,
    DocumentFindingRecord,
    SourceLocatorRecord,
)
from app.models.technical_report_command import TechnicalReportActor, canonical_json
from app.schemas.document_intelligence import DocumentReportDraftRequest
from app.services.document_intelligence_service import DocumentIntelligenceService


def _create_report(result_payload):
    now = datetime.now(timezone.utc)
    organization_id = uuid4()
    candidate_id = uuid4()
    is_discrepancy = (
        isinstance(result_payload, dict)
        and result_payload.get("status") == "discrepant"
    )
    correlation = DocumentCorrelation(
        id=uuid4(), organization_id=organization_id, project_id=7,
        workspace_id=9, left_candidate_id=candidate_id,
        right_candidate_id=None,
        rule_id=(
            "document.reviewed-assertion-consistency"
            if is_discrepancy else "document.explicit-missing-placeholder"
        ),
        rule_version=(2 if is_discrepancy else 1),
        applicability="Human-reviewed assertions only.",
        result=result_payload,
        result_digest="a" * 64, created_by_id=17, created_at=now,
    )
    finding = DocumentFindingRecord(
        id=uuid4(), correlation_id=correlation.id,
        kind=("discrepancy" if is_discrepancy else "missing_information"),
        state="open",
        title=(
            "Conflicting reviewed values: 10-P-101 discharge pressure"
            if is_discrepancy else "Missing information: pressure"
        ),
        explanation=(
            "The Human-reviewed source assertions disagree."
            if is_discrepancy else "The bound source explicitly records TBD."
        ),
        uncertainty="Responsible engineer must determine the governing value.",
        created_at=now,
    )
    locator = SourceLocatorRecord(
        id=uuid4(), schema_version=1, locator_kind="table_cell",
        supporting_file_asset_id=uuid4(), asset_version_at_analysis=2,
        storage_object_version="object-v2", digest_algorithm="sha256",
        content_digest="b" * 64, media_type="application/pdf",
        page_index=2, page_label="3", section_path=[],
        table_key="page-3-table-1", row_index=1, row_label="Line A",
        column_index=2, column_label="Pressure", text_excerpt="TBD",
        extraction_method="deterministic", locator_digest="c" * 64,
        created_at=now,
    )
    session = MagicMock()
    session.query.return_value.join.return_value.filter.return_value.all.return_value = [
        (finding, correlation)
    ]
    service = DocumentIntelligenceService(session)
    service._authorize_scope = MagicMock()
    service.repository = MagicMock()
    service.repository.candidate_locators.return_value = [(SimpleNamespace(candidate_id=candidate_id), locator)]
    report_service = MagicMock()
    report_id, revision_id = uuid4(), uuid4()
    report_service.create_draft.return_value = SimpleNamespace(
        report_id=report_id, version=1,
        draft_revision=SimpleNamespace(revision_id=revision_id),
    )

    response = service.create_document_report_draft(
        project_id=7,
        data=DocumentReportDraftRequest(
            workspace_id=9, finding_ids=(finding.id,),
            purpose="engineering_analysis",
            rationale="Generate a reviewable preliminary engineering report",
        ),
        user=SimpleNamespace(id=17, is_active=True, role="engineer"),
        organization_id=organization_id,
        idempotency_id=uuid4(), correlation_id=uuid4(),
        report_service=report_service,
        report_actor=TechnicalReportActor(17, organization_id),
    )

    command = report_service.create_draft.call_args.args[0]
    return response, command, finding, locator


def test_deterministic_finding_report_includes_persisted_summary_and_stays_preliminary():
    summary = (
        "10-P-101 discharge pressure is 12 bar in the datasheet and 15 bar "
        "in the equipment list."
    )
    result, command, finding, locator = _create_report({
        "status": "discrepant",
        "summary": summary,
        "reason_codes": ["reviewed_value_conflict"],
    })

    assert result.report_id
    assert result.lifecycle == "draft"
    assert result.preliminary is True
    assert command.qualification.is_preliminary is True
    assert command.qualification.unresolved_issues == (finding.title,)
    assert "does not select engineering truth" in command.content.uncertainty
    assert summary in command.content.technical_content
    assert "12 bar" in command.content.technical_content
    assert "15 bar" in command.content.technical_content
    assert command.provenance[0].locator.report_local_source_id == finding.id
    assert summary in command.provenance[0].locator.minimal_representation
    assert command.provenance[0].integrity_digest == sha256(
        canonical_json(command.provenance[0].locator)
    ).hexdigest()
    assert command.provenance[0].locator.minimal_representation.endswith(
        f"locator {locator.id}"
    )


@pytest.mark.parametrize("result_payload", (
    None,
    ["summary"],
    {},
    {"summary": None},
    {"summary": 12},
    {"summary": "   "},
    {"summary": "invalid\x01summary"},
    {"summary": "x" * 2001},
))
def test_missing_or_malformed_summary_does_not_break_report_generation(result_payload):
    result, command, _finding, _locator = _create_report(result_payload)

    assert result.lifecycle == "draft"
    assert result.preliminary is True
    assert command.qualification.is_preliminary is True
    assert "Correlation summary:" not in command.content.technical_content
    assert "Correlation summary:" not in (
        command.provenance[0].locator.minimal_representation
    )
    assert command.provenance[0].integrity_digest == sha256(
        canonical_json(command.provenance[0].locator)
    ).hexdigest()
