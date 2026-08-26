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
    def get_revision(self,**kwargs): return getattr(self,"revision",None)
    def get_revision_by_supporting_file(self,**kwargs): return getattr(self,"revision",None)
    def list_graph_incident(self,**kwargs):
        row=getattr(self,"graph_row",None)
        return (() if row is None else (row,)),False

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
    def can_read(self,**kwargs): return True

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


def test_exact_revision_graph_read_is_owner_authorized_and_payload_safe():
    now=datetime(2026,1,1,tzinfo=timezone.utc); organization_id=uuid4(); deliverable_id=uuid4(); revision_id=uuid4()
    repo=Repository()
    repo.revision=SimpleNamespace(id=revision_id,deliverable_id=deliverable_id,organization_id=organization_id,project_id=7,sequence=2,external_label="B",standing="issued",version=3,supporting_file_id=None,created_at=now,transitioned_at=now)
    repo.get=lambda **kwargs: SimpleNamespace(id=deliverable_id,project_id=7,workspace_id=None,external_authority="cad")
    uow=Uow(repo); actor=DeliverableActor(actor_id=2,organization_id=organization_id)
    service=EngineeringDeliverableService(uow_factory=lambda:uow,authorization=Authorization(),clock=lambda:now)
    result=service.get_authorized_revision(project_id=7,revision_id=revision_id,actor=actor)
    assert result.id==revision_id and result.deliverable_id==deliverable_id and result.external_authority.value=="cad"
    assert not uow.committed and repo.get_revision(revision_id=revision_id,organization_id=organization_id) is repo.revision
    assert not ({"supporting_file_id","source_reference","created_by_id","transitioned_by_id"}&set(result.model_dump()))


def test_exact_revision_graph_read_fails_closed_for_missing_or_foreign_project():
    organization_id=uuid4(); repo=Repository(); uow=Uow(repo); actor=DeliverableActor(actor_id=2,organization_id=organization_id)
    service=EngineeringDeliverableService(uow_factory=lambda:uow,authorization=Authorization())
    assert service.get_authorized_revision(project_id=7,revision_id=uuid4(),actor=actor).outcome=="protected_not_found"
    repo.revision=SimpleNamespace(id=uuid4(),deliverable_id=uuid4(),organization_id=organization_id,project_id=8)
    assert service.get_authorized_revision(project_id=7,revision_id=repo.revision.id,actor=actor).outcome=="protected_not_found"

def test_representation_graph_relation_is_exact_authorized_and_has_no_storage_payload():
    now=datetime(2026,1,1,tzinfo=timezone.utc); organization_id=uuid4(); deliverable_id=uuid4(); revision_id=uuid4(); asset_id=uuid4()
    repo=Repository();repo.revision=SimpleNamespace(id=revision_id,deliverable_id=deliverable_id,organization_id=organization_id,project_id=7,sequence=1,standing="issued",version=2,supporting_file_id=asset_id,created_at=now,transitioned_at=now)
    repo.get=lambda **kwargs:SimpleNamespace(id=deliverable_id,project_id=7,workspace_id=None,external_authority="cad")
    service=EngineeringDeliverableService(uow_factory=lambda:Uow(repo),authorization=Authorization(),supporting_files=SimpleNamespace(visible=lambda **kwargs:True));actor=DeliverableActor(actor_id=2,organization_id=organization_id)
    result=service.get_authorized_representation_link(project_id=7,actor=actor,revision_id=revision_id)
    assert (result.revision_id,result.asset_id)==(revision_id,asset_id)
    assert set(result.model_dump())=={"revision_id","asset_id","deliverable_id","project_id","workspace_id","revision_version"}


def test_deliverable_incident_read_is_typed_and_never_calls_project_list():
    organization_id=uuid4();repo=Repository();deliverable_id=uuid4();activity_id=uuid4()
    repo.graph_row=("deliverable_activity","deliverable",deliverable_id,"activity",activity_id,2)
    repo.list=lambda **kwargs: (_ for _ in ()).throw(AssertionError("broad list forbidden"))
    service=EngineeringDeliverableService(uow_factory=lambda:Uow(repo),authorization=Authorization())
    page=service.list_authorized_incident_graph_links(project_id=7,actor=DeliverableActor(actor_id=2,organization_id=organization_id),selector_kind="activity",selector_id=activity_id)
    assert page.items[0].source_id==deliverable_id and page.items[0].target_id==activity_id
