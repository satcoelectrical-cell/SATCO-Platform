from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.dependencies.project_foundation import ProjectFoundationApplication, get_project_foundation_application
from app.main import app
from app.schemas.project_foundation import ProjectFoundationActor, ProjectFoundationNotEstablished, ProjectFoundationProtectedResult


class RecordingService:
    def __init__(self): self.calls=[]
    def _call(self,name,**values): self.calls.append((name,values)); return ProjectFoundationNotEstablished(project_id=values["project_id"])
    def get(self,**values): return self._call("get",**values)
    def put(self,**values): return self._call("put",**values)
    def create_input(self,**values): return self._call("create_input",**values)
    def update_input(self,**values): return self._call("update_input",**values)
    def reorder_inputs(self,**values): return self._call("reorder_inputs",**values)
    def transition_input(self,**values): return self._call("transition_input",**values)
    def transition_stage(self,**values): return self._call("transition_stage",**values)
    def list_source_candidates(self,**values): return self._call("list_source_candidates",**values)


def client_for(service):
    app.dependency_overrides[get_project_foundation_application] = lambda: ProjectFoundationApplication(
        service=service, actor=ProjectFoundationActor(actor_id=7, organization_id=uuid4()),
    )
    return TestClient(app)


def test_exact_eight_routes_delegate_without_client_authority_fields():
    service=RecordingService(); client=client_for(service); input_id=uuid4()
    basis={"expected_version":0,"purpose":"Purpose","engineering_basis":"Basis","in_scope":["Control"],"out_of_scope":[],"completion_criteria":["Basis recorded"],"rationale":"Human rationale"}
    create={"expected_foundation_version":1,"title":"Requirements","description":None,"ordinal":0,"required_by_stage":"preparation","rationale":"Human rationale"}
    update={**create,"expected_input_version":1}
    calls=[
        client.get("/projects/7/foundation"), client.put("/projects/7/foundation",json=basis),
        client.post("/projects/7/foundation/inputs",json=create), client.put(f"/projects/7/foundation/inputs/{input_id}",json=update),
        client.post("/projects/7/foundation/inputs/reorder",json={"expected_foundation_version":1,"ordered_input_ids":[str(input_id)],"rationale":"Human rationale"}),
        client.post(f"/projects/7/foundation/inputs/{input_id}/transitions",json={"expected_foundation_version":1,"expected_input_version":1,"target_standing":"not_applicable","rationale":"Human rationale"}),
        client.post("/projects/7/foundation/stage-transitions",json={"expected_foundation_version":1,"target_stage":"preparation","rationale":"Human rationale"}),
        client.get("/projects/7/foundation/source-candidates?kind=evidence&limit=20"),
    ]
    assert all(response.status_code == 200 for response in calls)
    assert [name for name,_ in service.calls] == ["get","put","create_input","update_input","reorder_inputs","transition_input","transition_stage","list_source_candidates"]
    assert "organization_id" not in str([response.request.content for response in calls])
    app.dependency_overrides.clear()


def test_malformed_transport_is_payload_free_invalid_request():
    service=RecordingService(); client=client_for(service)
    response=client.put("/projects/7/foundation",json={"expected_version":0,"purpose":"","engineering_basis":"Basis","in_scope":[],"out_of_scope":[],"completion_criteria":[],"rationale":""})
    assert response.status_code == 422 and response.json() == {"outcome":"invalid_request"}
    assert service.calls == []
    app.dependency_overrides.clear()


def test_protected_result_is_discriminator_only():
    class Protected(RecordingService):
        def get(self,**_): return ProjectFoundationProtectedResult()
    client=client_for(Protected()); response=client.get("/projects/999/foundation")
    assert response.json()=={"outcome":"protected_not_found"}
    app.dependency_overrides.clear()


def test_foundation_transport_requires_real_authentication():
    app.dependency_overrides.clear()
    with TestClient(app) as client:
        response = client.get("/projects/7/foundation")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
