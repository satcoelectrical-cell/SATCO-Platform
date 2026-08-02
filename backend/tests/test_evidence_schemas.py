import pytest
from pydantic import ValidationError
from app.schemas.evidence import EvidenceCreate
def test_workspace_requires_project():
    with pytest.raises(ValidationError): EvidenceCreate(workspace_id=1,source_kind="engineering_record",source_reference="R",source_revision="1",source_standing="current",supported_fact="fact",rationale="reason")
def test_system_scope_is_forbidden():
    with pytest.raises(ValidationError): EvidenceCreate(organization_id="00000000-0000-0000-0000-000000000001",source_kind="engineering_record",source_reference="R",source_revision="1",source_standing="current",supported_fact="fact",rationale="reason")
