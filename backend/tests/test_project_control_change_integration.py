from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.adapters.project_control_targets import CanonicalProjectControlTargetAdapter, TargetInvalid, TargetUnavailable
from app.schemas.project_control import ControlActor


ORG=UUID("04700000-0000-4000-8000-000000000001")


class Execution:
    def __init__(self, activity, milestone): self.activity=activity; self.milestone=milestone; self.calls=[]
    def get(self, *, project_id, actor):
        self.calls.append((project_id,actor))
        return SimpleNamespace(outcome="success",availability="established",project_id=project_id,activities=(SimpleNamespace(id=self.activity,workspace_id=None),),milestones=(SimpleNamespace(id=self.milestone,workspace_id=None),))


class Deliverables:
    def __init__(self, deliverable, revision): self.deliverable=deliverable; self.revision=revision; self.calls=[]
    def get(self, *, project_id, deliverable_id, actor):
        self.calls.append(("get",project_id,deliverable_id,actor))
        return SimpleNamespace(id=self.deliverable,project_id=project_id,workspace_id=None)
    def history(self, *, project_id, deliverable_id, actor):
        self.calls.append(("history",project_id,deliverable_id,actor))
        return SimpleNamespace(outcome="success",items=(SimpleNamespace(id=self.deliverable,project_id=project_id,workspace_id=None,current_revision=SimpleNamespace(id=self.revision)),))


class Evidence:
    def __init__(self, evidence): self.evidence=evidence; self.calls=[]
    def get(self, evidence_id, actor):
        self.calls.append((evidence_id,actor))
        return SimpleNamespace(id=self.evidence,organization_id=actor.organization_id,project_id=47,workspace_id=None)


class Files:
    def __init__(self, asset): self.asset=asset; self.calls=[]
    def get_metadata(self, *, actor_id, scope, asset_id):
        self.calls.append((actor_id,scope,asset_id))
        return SimpleNamespace(id=self.asset,organization_id=scope.organization_id,project_id=scope.project_id,workspace_id=None)


def adapter():
    ids={kind:uuid4() for kind in ("activity","milestone","deliverable","revision","evidence","supporting_file")}
    execution=Execution(ids["activity"],ids["milestone"]); deliverables=Deliverables(ids["deliverable"],ids["revision"]); evidence=Evidence(ids["evidence"]); files=Files(ids["supporting_file"])
    return CanonicalProjectControlTargetAdapter(execution=execution,deliverables=deliverables,evidence=evidence,supporting_files=files),ids,(execution,deliverables,evidence,files)


@pytest.mark.parametrize("kind,key", (("activity","activity"),("milestone","milestone"),("deliverable","deliverable"),("deliverable_revision","revision"),("evidence","evidence"),("supporting_file","supporting_file")))
def test_all_six_targets_use_exact_canonical_application_dispatch(kind,key):
    value,ids,services=adapter(); actor=ControlActor(actor_id=47,organization_id=ORG)
    result=value.authorize_exact(actor=actor,project_id=47,workspace_id=None,target_kind=kind,target_id=ids[key],deliverable_id=ids["deliverable"] if kind=="deliverable_revision" else None)
    assert result.kind==kind and result.target_id==ids[key]
    assert any(getattr(service,"calls",()) for service in services)


def test_adapter_is_closed_and_fails_before_disclosure_for_unknown_or_unavailable_target():
    value,ids,_=adapter(); actor=ControlActor(actor_id=47,organization_id=ORG)
    with pytest.raises(TargetInvalid): value.authorize_exact(actor=actor,project_id=47,workspace_id=None,target_kind="foundation",target_id=ids["activity"])
    value.execution.get=lambda **_: SimpleNamespace(outcome="unavailable")
    with pytest.raises(TargetUnavailable): value.authorize_exact(actor=actor,project_id=47,workspace_id=None,target_kind="activity",target_id=ids["activity"])
