from uuid import uuid4

from fastapi.testclient import TestClient

from app.dependencies.project_control import ProjectControlApplication, get_project_control_application
from app.main import app
from app.schemas.project_control import ControlActor, ControlHistorySuccess, ControlListSuccess, ControlSuccess, Invalid, Protected


class RecordingService:
    def __init__(self): self.calls=[]
    def _call(self, name, **values):
        self.calls.append((name, values))
        if name == "list": return ControlListSuccess(kind=values["kind"], items=(), visible_count=0)
        if name == "history": return ControlHistorySuccess(kind=values["kind"], control_id=values["control_id"], items=(), visible_count=0)
        return ControlSuccess(id=values.get("control_id", values.get("predecessor_id", uuid4())), version=1)
    def list(self, **values): return self._call("list", **values)
    def get(self, **values): return self._call("get", **values)
    def history(self, **values): return self._call("history", **values)
    def create_risk(self, **values): return self._call("create_risk", **values)
    def create_issue(self, **values): return self._call("create_issue", **values)
    def create_decision(self, **values): return self._call("create_decision", **values)
    def create_change(self, **values): return self._call("create_change", **values)
    def create_decision_successor(self, **values): return self._call("create_decision_successor", **values)
    def create_change_successor(self, **values): return self._call("create_change_successor", **values)
    def supersede_change(self, **values): return self._call("supersede_change", **values)
    def create_change_impact(self, **values): return self._call("create_change_impact", **values)
    def confirm_change_impact(self, **values): return self._call("confirm_change_impact", **values)
    def transition_risk(self, **values): return self._call("transition_risk", **values)
    def transition_issue(self, **values): return self._call("transition_issue", **values)
    def transition_decision(self, **values): return self._call("transition_decision", **values)
    def transition_change(self, **values): return self._call("transition_change", **values)


def client_for(service):
    app.dependency_overrides[get_project_control_application] = lambda: ProjectControlApplication(service=service, actor=ControlActor(actor_id=7, organization_id=uuid4()))
    return TestClient(app)


def test_project_control_transport_delegates_with_trusted_context_only():
    service=RecordingService(); client=client_for(service); control_id=uuid4(); key={"Idempotency-Key":str(uuid4())}
    risk={"statement":"Relay availability risk","category":"engineering","likelihood":"medium","impact":"high","rationale":"Human records risk"}
    issue={"statement":"Loose terminal","observed_context":"Inspection observation","severity":"high","rationale":"Human records observed issue"}
    change={"statement":"Cable route changed","rationale":"Human records changed condition"}
    requests=[
        client.get("/projects/7/controls/risk"), client.get(f"/projects/7/controls/risk/{control_id}"), client.get(f"/projects/7/controls/risk/{control_id}/history"),
        client.post("/projects/7/controls/risks",json=risk,headers=key), client.post("/projects/7/controls/issues",json=issue,headers=key), client.post("/projects/7/controls/decisions",json={"statement":"Use guarded design","rationale":"Human choice"},headers=key), client.post("/projects/7/controls/changes",json=change,headers=key),
        client.post(f"/projects/7/controls/changes/{control_id}/transitions",json={"target_standing":"confirmed","expected_version":1,"rationale":"Human confirms Change"},headers=key),
    ]
    assert all(item.status_code == 200 for item in requests)
    assert [name for name,_ in service.calls] == ["list","get","history","create_risk","create_issue","create_decision","create_change","transition_change"]
    assert "organization_id" not in str([item.request.content for item in requests])
    app.dependency_overrides.clear()


def test_transport_protects_malformed_cross_path_and_closed_results():
    service=RecordingService(); client=client_for(service); control_id=uuid4(); key={"Idempotency-Key":str(uuid4())}
    malformed=client.post("/projects/7/controls/risks",json={"statement":""},headers=key)
    mismatch=client.post(f"/projects/7/controls/changes/{control_id}/impacts",json={"change_id":str(uuid4()),"target_kind":"activity","target_id":str(uuid4()),"statement":"Impact","rationale":"Human rationale","expected_version":1},headers=key)
    assert malformed.status_code == 422 and malformed.json()=={"outcome":"invalid_request"}
    assert mismatch.status_code == 422 and mismatch.json()=={"outcome":"invalid_request"}
    class ProtectedService(RecordingService):
        def get(self, **_): return Protected()
    protected=client_for(ProtectedService()).get(f"/projects/999/controls/change/{control_id}")
    assert protected.status_code==404 and protected.json()=={"outcome":"protected_not_found"}
    app.dependency_overrides.clear()


def test_transport_requires_real_authentication_and_has_no_foundation_route():
    app.dependency_overrides.clear()
    with TestClient(app) as client:
        response=client.get("/projects/7/controls/change")
    assert response.status_code==401
    assert all("foundation" not in route.path for route in __import__("app.api.v1.routers.project_controls", fromlist=["router"]).router.routes)
