from types import SimpleNamespace
from uuid import UUID

from app.adapters.engineering_execution_plan import ProjectFoundationApplicationAdapter
from app.schemas.engineering_execution_plan import ExecutionActor


def test_foundation_adapter_uses_canonical_application_result_only():
    calls=[]
    class Service:
        def get(self, **kwargs): calls.append(kwargs); return SimpleNamespace(outcome="success", availability="established")
    adapter=ProjectFoundationApplicationAdapter(SimpleNamespace(service=Service()))
    actor=ExecutionActor(actor_id=4, organization_id=UUID("02810000-0000-4000-8000-000000000001"))
    assert adapter.is_established(actor=actor, project_id=7)
    assert calls[0]["project_id"] == 7 and calls[0]["actor"].actor_id == 4
