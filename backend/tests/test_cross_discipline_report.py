from datetime import datetime, timezone
from uuid import uuid4

from app.models.technical_report_command import CrossDisciplineAssessmentHistoricalBasisV1, historical_basis_from_payload


def test_cross_discipline_assessment_basis_is_closed_and_round_trips():
    basis = CrossDisciplineAssessmentHistoricalBasisV1(1, "cross_discipline_assessment", uuid4(), 1, uuid4(), 1, None, "completed_no_findings", "a" * 64, "b" * 64, "c" * 64, datetime.now(timezone.utc))
    payload = {"basis_schema_version": 1, "source_category": "cross_discipline_assessment", "assessment_id": str(basis.assessment_id), "source_version": 1, "organization_id": str(basis.organization_id), "project_id": 1, "workspace_id": None, "status": basis.status, "snapshot_digest": basis.snapshot_digest, "definition_digest": basis.definition_digest, "result_digest": basis.result_digest, "completed_at": basis.completed_at.isoformat().replace("+00:00", "Z")}
    assert historical_basis_from_payload(payload, "cross_discipline_assessment").assessment_id == basis.assessment_id
