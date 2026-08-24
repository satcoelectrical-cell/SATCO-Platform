from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.schemas.engineering_deliverable import CreateDeliverableRequest, DeliverableActor
from app.adapters.engineering_deliverable import SupportingFileApplicationAdapter
from app.exceptions.supporting_file import SupportingFileProtectedNotFound
from app.services.engineering_deliverable_service import EngineeringDeliverableService


class Repository:
    def __init__(self): self.items=[]; self.replays=[]
    def add(self,item): self.items.append(item)
    def flush(self): pass
    def get_idempotency(self,**kwargs): return next((item for item in self.replays if all(getattr(item,key)==value for key,value in kwargs.items())),None)
    def get(self,**kwargs): return None
    def get_current_revision(self,**kwargs): return None

class Uow:
    def __init__(self,repo): self.repository=repo;self.committed=False;self.audit=[]
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def stage_audit(self,**kwargs): self.audit.append(kwargs)
    def commit(self): self.committed=True
    def rollback(self): pass

class Authorization:
    def project(self,**kwargs): return SimpleNamespace(id=7,status="active",owner_id=2,primary_assignee_id=None)
    def can_mutate(self,**kwargs): return True
    def valid_links(self,**kwargs): return True

def request(): return CreateDeliverableRequest(code="EL-001",title="Load list",discipline="electrical",deliverable_type="schedule",purpose=None,external_authority="spreadsheet",workspace_id=None,activity_id=None,milestone_id=None,responsible_user_id=None,target_date=None,initial_external_label="A",source_reference=None,supporting_file_id=None,rationale="Register controlled external work")

def test_create_is_human_governed_idempotent_and_external_authority_only():
    repo=Repository();uow=Uow(repo);actor=DeliverableActor(actor_id=2,organization_id=uuid4())
    service=EngineeringDeliverableService(uow_factory=lambda:uow,authorization=Authorization(),clock=lambda:datetime(2026,1,1,tzinfo=timezone.utc))
    result=service.create(project_id=7,data=request(),actor=actor,idempotency_key=uuid4())
    assert result.outcome=="success" and result.revision_standing.value=="draft"
    assert uow.committed and any(item.__class__.__name__=="EngineeringDeliverableRevision" for item in repo.items)
    revision=next(item for item in repo.items if item.__class__.__name__=="EngineeringDeliverableRevision")
    assert revision.external_label=="A" and revision.source_reference is None


def test_supporting_file_adapter_rechecks_trusted_scope_and_fails_closed():
    asset_id = uuid4()
    actor = DeliverableActor(actor_id=2, organization_id=uuid4())
    project = SimpleNamespace(id=7)

    class Service:
        def __init__(self, asset): self.asset = asset; self.calls = []
        def get_metadata(self, **kwargs): self.calls.append(kwargs); return self.asset

    service = Service(SimpleNamespace(lifecycle="available"))
    adapter = SupportingFileApplicationAdapter(SimpleNamespace(service=service))
    assert adapter.visible(actor=actor, project=project, workspace_id=9, asset_id=asset_id)
    call = service.calls[0]
    assert call["actor_id"] == actor.actor_id and call["asset_id"] == asset_id
    assert call["scope"].organization_id == actor.organization_id
    assert call["scope"].project_id == project.id and call["scope"].workspace_id == 9

    denied = SupportingFileApplicationAdapter(SimpleNamespace(service=SimpleNamespace(
        get_metadata=lambda **_kwargs: (_ for _ in ()).throw(SupportingFileProtectedNotFound())
    )))
    assert not denied.visible(actor=actor, project=project, workspace_id=9, asset_id=asset_id)
