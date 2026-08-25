from uuid import uuid4
import pytest
from pydantic import ValidationError
from app.schemas.project_control import ChangeCommand, ConfirmImpactCommand, ImpactCommand, Protected, RiskCommand

def test_risk_contract_is_closed_and_qualitative():
    value=RiskCommand(statement="Late vendor data",category="interface",likelihood="high",impact="medium",rationale="Human engineering assessment")
    assert value.likelihood=="high"
    with pytest.raises(ValidationError): RiskCommand(statement="x",category="c",likelihood="numeric",impact="high",rationale="r")
def test_impact_contract_has_closed_target_and_protected_outcome_is_empty():
    value=ImpactCommand(change_id=uuid4(),target_kind="deliverable",target_id=uuid4(),statement="Review load list",rationale="Human recorded potential impact",expected_version=1)
    assert value.standing=="potential" and Protected().model_dump()=={"outcome":"protected_not_found"}

def test_change_impact_closes_foundation_and_revision_owner_context():
    with pytest.raises(ValidationError): ImpactCommand(change_id=uuid4(),target_kind="foundation",target_id=uuid4(),statement="Foundation is affected",rationale="Human statement",expected_version=1)
    with pytest.raises(ValidationError): ImpactCommand(change_id=uuid4(),target_kind="deliverable_revision",target_id=uuid4(),statement="Revision may be affected",rationale="Human statement",expected_version=1)
    with pytest.raises(ValidationError): ImpactCommand(change_id=uuid4(),target_kind="activity",target_id=uuid4(),deliverable_id=uuid4(),statement="Activity may be affected",rationale="Human statement",expected_version=1)
    value=ImpactCommand(change_id=uuid4(),target_kind="deliverable_revision",target_id=uuid4(),deliverable_id=uuid4(),statement="Revision may be affected",rationale="Human statement",expected_version=1)
    assert value.deliverable_id is not None and ConfirmImpactCommand(expected_change_version=1,rationale="Human confirmation").deliverable_id is None

def test_change_command_preserves_human_statement_and_rationale():
    value=ChangeCommand(statement="Cable route changed after inspection",rationale="Human records changed condition")
    assert value.predecessor_id is None
