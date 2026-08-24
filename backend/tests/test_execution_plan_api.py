from uuid import uuid4

from fastapi.testclient import TestClient

from app.dependencies.engineering_execution_plan import EngineeringExecutionPlanApplication, get_engineering_execution_plan_application
from app.api.v1.routers.engineering_execution_plan import router
from app.main import app
from app.schemas.engineering_execution_plan import ExecutionActor, ExecutionPlanNotEstablished, ExecutionPlanProtectedResult


class RecordingService:
    def __init__(self): self.calls=[]
    def _call(self, name, **values): self.calls.append((name, values)); return ExecutionPlanNotEstablished(project_id=values["project_id"])
    def get(self, **values): return self._call("get", **values)
    def establish(self, **values): return self._call("establish", **values)
    def create_activity(self, **values): return self._call("create_activity", **values)
    def update_activity(self, **values): return self._call("update_activity", **values)
    def transition_activity(self, **values): return self._call("transition_activity", **values)
    def replace_dependencies(self, **values): return self._call("replace_dependencies", **values)
    def create_milestone(self, **values): return self._call("create_milestone", **values)
    def update_milestone(self, **values): return self._call("update_milestone", **values)


def client_for(service):
    app.dependency_overrides[get_engineering_execution_plan_application] = lambda: EngineeringExecutionPlanApplication(service=service, actor=ExecutionActor(actor_id=7, organization_id=uuid4()))
    return TestClient(app)


def test_exact_eight_routes_delegate_without_client_authority_fields():
    service=RecordingService(); client=client_for(service); activity_id=uuid4(); milestone_id=uuid4(); key={"Idempotency-Key":str(uuid4())}
    activity={"expected_plan_version":1,"title":"Relay survey","description":None,"ordinal":0,"workspace_id":None,"responsible_user_id":None,"target_date":None,"completion_basis":"Survey accepted","rationale":"Human execution rationale"}
    milestone={"expected_plan_version":1,"title":"Survey complete","completion_basis":"All surveys accepted","target_date":None,"ordinal":0,"activity_ids":[],"rationale":"Human milestone rationale"}
    responses=[client.get("/projects/7/execution-plan"),client.put("/projects/7/execution-plan",json={"expected_plan_version":0,"rationale":"Establish plan"},headers=key),client.post("/projects/7/execution-plan/activities",json=activity,headers=key),client.put(f"/projects/7/execution-plan/activities/{activity_id}",json={**activity,"expected_activity_version":1},headers=key),client.post(f"/projects/7/execution-plan/activities/{activity_id}/transitions",json={"expected_activity_version":1,"target_standing":"ready","rationale":"Ready to execute"},headers=key),client.put("/projects/7/execution-plan/dependencies",json={"expected_plan_version":1,"dependencies":[],"rationale":"No dependencies"},headers=key),client.post("/projects/7/execution-plan/milestones",json=milestone,headers=key),client.put(f"/projects/7/execution-plan/milestones/{milestone_id}",json=milestone,headers=key)]
    assert all(response.status_code == 200 for response in responses)
    assert [name for name,_ in service.calls] == ["get","establish","create_activity","update_activity","transition_activity","replace_dependencies","create_milestone","update_milestone"]
    assert "organization_id" not in str([response.request.content for response in responses])
    app.dependency_overrides.clear()


def test_malformed_transport_and_protected_result_are_payload_free():
    service=RecordingService(); client=client_for(service)
    malformed=client.post("/projects/7/execution-plan/activities",json={"title":""},headers={"Idempotency-Key":str(uuid4())})
    assert malformed.status_code == 422 and malformed.json() == {"outcome":"invalid_request"} and service.calls == []
    class Protected(RecordingService):
        def get(self, **_): return ExecutionPlanProtectedResult()
    protected=client_for(Protected()).get("/projects/999/execution-plan")
    assert protected.status_code == 404 and protected.json() == {"outcome":"protected_not_found"}
    app.dependency_overrides.clear()


def test_execution_plan_transport_requires_real_authentication():
    app.dependency_overrides.clear()
    with TestClient(app) as client:
        response=client.get("/projects/7/execution-plan")
    assert response.status_code == 401 and response.json() == {"detail":"Not authenticated"}


def test_exact_route_surface_is_eight_operations_only():
    assert [(route.path, next(iter(route.methods))) for route in router.routes] == [
        ("/projects/{project_id}/execution-plan", "GET"),
        ("/projects/{project_id}/execution-plan", "PUT"),
        ("/projects/{project_id}/execution-plan/activities", "POST"),
        ("/projects/{project_id}/execution-plan/activities/{activity_id}", "PUT"),
        ("/projects/{project_id}/execution-plan/activities/{activity_id}/transitions", "POST"),
        ("/projects/{project_id}/execution-plan/dependencies", "PUT"),
        ("/projects/{project_id}/execution-plan/milestones", "POST"),
        ("/projects/{project_id}/execution-plan/milestones/{milestone_id}", "PUT"),
    ]
