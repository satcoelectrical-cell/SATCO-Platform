from uuid import uuid4
from types import SimpleNamespace
from datetime import datetime, timezone
import pytest
from app.adapters.engineering_performance import (
    EngineeringPerformanceProtectedNotFound,
    EngineeringPerformanceScope,
    EngineeringPerformanceSourceAdapter,
)
from app.schemas.engineering_execution_plan import ExecutionActivityEvidenceDTO, ExecutionActivityEvidencePage

class Query:
    def __init__(self, result): self.result=result
    def filter(self,*args): return self
    def first(self): return self.result
    def all(self): return self.result

class DB:
    def __init__(self, results): self.results=list(results); self.calls=0
    def query(self,*args):
        self.calls += 1
        return Query(self.results.pop(0))

class Policy:
    def __init__(self, *, project=True, workspace=True):
        self.project=project; self.workspace=workspace; self.calls=[]
    def authorize(self, *, actor, operation, project_id, workspace_id):
        self.calls.append((actor.actor_id, project_id, workspace_id))
        return self.project if workspace_id is None else self.workspace

class Foundation:
    def __init__(self, standings=("received", "missing")):
        self.standings=standings; self.calls=0
    def get(self, *, project_id, actor):
        self.calls+=1
        return SimpleNamespace(outcome="success", availability="established", inputs=tuple(
            SimpleNamespace(standing=value, source_condition="authorized_current" if value=="received" else "not_required")
            for value in self.standings
        ))

def scope(workspace_id=None):
    return EngineeringPerformanceScope(uuid4(), 7, workspace_id, 4)

def test_p056_sec_01_foreign_or_missing_project_fails_before_source_selection():
    db=DB([]); policy=Policy(project=False); adapter=EngineeringPerformanceSourceAdapter(db,policy)
    with pytest.raises(EngineeringPerformanceProtectedNotFound):
        adapter.required_input_standings(scope())
    assert db.calls == 0 and len(policy.calls)==1

def test_p056_sec_02_workspace_scope_is_authorized_before_source_selection():
    db=DB([]); policy=Policy(workspace=False); adapter=EngineeringPerformanceSourceAdapter(db,policy)
    with pytest.raises(EngineeringPerformanceProtectedNotFound):
        adapter.execution_activity_rows(scope(11))
    assert db.calls == 0 and len(policy.calls)==2

def test_p056_sec_03_authorized_project_then_reads_only_scoped_required_inputs():
    db=DB([]); foundation=Foundation()
    assert EngineeringPerformanceSourceAdapter(db,Policy(),foundation).required_input_standings(scope()) == ["received","missing"]
    assert db.calls == 0 and foundation.calls == 1

def test_p056_sec_04_authorized_workspace_then_reads_scoped_execution():
    db=DB([]); s=scope(11); now=datetime.now(timezone.utc)
    class Execution:
        calls=0
        def list_authorized_activity_evidence(self, **kwargs):
            self.calls+=1
            return ExecutionActivityEvidencePage(items=(ExecutionActivityEvidenceDTO(
                id=uuid4(),organization_id=s.organization_id,project_id=7,workspace_id=11,
                standing="blocked",version=1,target_date=None,blocked_since=now,
                blocker_event_id=uuid4(),updated_at=now,
            ),))
    execution=Execution()
    rows=EngineeringPerformanceSourceAdapter(db,Policy(),execution_service=execution).execution_activity_rows(s)
    assert len(rows)==1 and db.calls==0 and execution.calls==1

def test_p056_sec_05_protected_not_found_exposes_no_hidden_count():
    error=EngineeringPerformanceProtectedNotFound()
    assert str(error)=="" and error.args==()


def test_p056_completeness_adapter_consumes_owner_read_without_canonical_write():
    db = DB([])
    current_user = SimpleNamespace(id=4)

    class Owner:
        def __init__(self): self.reads = 0
        def list_authorized_observation_history(self, **kwargs):
            self.reads += 1
            assert kwargs["window_days"] == 30
            assert kwargs["current_user"] is current_user
            return {"outcome": "success", "source_cutoff": datetime.now(timezone.utc),
                    "observations": ()}
        def record_authorized_observation(self, **_kwargs):
            raise AssertionError("PATCH-056 must not record canonical completeness")

    owner = Owner()
    adapter = EngineeringPerformanceSourceAdapter(
        db, Policy(), completeness_service=owner, current_user=current_user,
    )
    assert adapter.completeness_history(scope(), window_days=30)["observations"] == ()
    assert owner.reads == 1 and db.calls == 0
    denied = EngineeringPerformanceSourceAdapter(
        db, Policy(project=False), completeness_service=owner, current_user=current_user,
    )
    with pytest.raises(EngineeringPerformanceProtectedNotFound):
        denied.completeness_history(scope(), window_days=30)
    assert owner.reads == 1 and db.calls == 0
