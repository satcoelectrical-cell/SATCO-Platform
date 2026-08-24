from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.enums.engineering_deliverable import revision_transition_allowed
from app.schemas.engineering_deliverable import CreateDeliverableRequest, DeliverableInvalidResult, DeliverableProtectedResult


def payload():
    return {"code":"EL-SLD-001","title":"Single Line Diagram","discipline":"electrical","deliverable_type":"drawing","purpose":None,"external_authority":"cad","workspace_id":None,"activity_id":None,"milestone_id":None,"responsible_user_id":None,"target_date":None,"initial_external_label":"Rev A","rationale":"Initial governed registration"}


def test_deliverable_contract_is_closed_and_normalized():
    value=CreateDeliverableRequest(**payload())
    assert value.code=="EL-SLD-001" and value.initial_external_label=="Rev A"
    with pytest.raises(ValidationError): CreateDeliverableRequest(**(payload()|{"unexpected":True}))
    with pytest.raises(ValidationError): CreateDeliverableRequest(**(payload()|{"rationale":"   "}))


def test_revision_lifecycle_is_external_label_agnostic_and_closed():
    assert revision_transition_allowed("draft","ready_for_review")
    assert revision_transition_allowed("reviewed","issued")
    assert not revision_transition_allowed("issued","draft")
    assert DeliverableProtectedResult().model_dump()=={"outcome":"protected_not_found"}
    assert DeliverableInvalidResult().model_dump()=={"outcome":"invalid_request"}


def test_revision_read_contract_never_contains_a_raw_supporting_file_identity():
    from app.schemas.engineering_deliverable import DeliverableRevisionDTO

    assert "supporting_file_id" not in DeliverableRevisionDTO.model_fields
    assert "representation_available" in DeliverableRevisionDTO.model_fields
