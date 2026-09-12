from datetime import datetime, timezone

from app.models.standards import OrganizationRightsBinding
from app.services.standards_service import StandardsService


def test_rights_evaluator_fails_closed_for_unknown_status():
    row = OrganizationRightsBinding(rights_basis="organization_license", rights_status="unknown", is_current=True, effective_from=datetime.now(timezone.utc), allow_source_retrieval=True)
    assert StandardsService.evaluate_capability(row, "source_retrieval") is False


def test_rights_evaluator_fails_closed_for_metadata_only():
    row = OrganizationRightsBinding(rights_basis="metadata_only", rights_status="active", is_current=True, effective_from=datetime.now(timezone.utc), allow_source_retrieval=True)
    assert StandardsService.evaluate_capability(row, "source_retrieval") is False
