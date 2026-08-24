from datetime import date
from types import SimpleNamespace
from uuid import UUID

from app.repositories.engineering_execution_plan_repository import canonical_plan_config


def _id(value: str) -> UUID: return UUID(value)


def test_canonical_plan_configuration_is_deterministic_and_excludes_execution_facts():
    later = SimpleNamespace(id=_id("00000000-0000-0000-0000-000000000002"), title="Later", description=None, ordinal=1, workspace_id=None, responsible_user_id=None, target_date=date(2026, 9, 2), completion_basis="Review", standing="completed")
    first = SimpleNamespace(id=_id("00000000-0000-0000-0000-000000000001"), title="First", description="Basis", ordinal=0, workspace_id=3, responsible_user_id=4, target_date=None, completion_basis="Check", standing="blocked")
    milestone = SimpleNamespace(id=_id("00000000-0000-0000-0000-000000000003"), title="Checkpoint", completion_basis="Activities complete", ordinal=0, target_date=None, links=[SimpleNamespace(activity_id=first.id, ordinal=0)])
    edge = SimpleNamespace(predecessor_activity_id=first.id, dependent_activity_id=later.id)
    one, one_digest = canonical_plan_config(activities=[later, first], milestones=[milestone], dependency_edges=[edge])
    two, two_digest = canonical_plan_config(activities=[first, later], milestones=[milestone], dependency_edges=[edge])
    assert one == two and one_digest == two_digest
    assert "standing" not in one["activities"][0]
    assert one["activities"][0]["id"] == str(first.id)
