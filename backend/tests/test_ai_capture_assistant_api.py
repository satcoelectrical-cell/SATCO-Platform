from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.dependencies.ai_capture_assistant import AICaptureAssistantApplication, get_ai_capture_assistant_application
from app.main import app
from app.ports.ai_capture_assistant import CaptureAdviceDisabled, CaptureAdviceProtectedNotFound, CopilotActor


class Service:
    def __init__(self, result): self.result, self.calls = result, []
    def advise_capture(self, *args): self.calls.append(args); return self.result


def _client(result):
    service, organization_id = Service(result), uuid4()
    app.dependency_overrides[get_ai_capture_assistant_application] = lambda: AICaptureAssistantApplication(
        service, CopilotActor(8, organization_id)
    )
    return TestClient(app), service


def test_route_is_single_thin_operation_and_protected_outcome_is_payload_free():
    client, service = _client(CaptureAdviceProtectedNotFound())
    response = client.post("/engineering-copilot/capture-advice", json={
        "capture_id": str(uuid4()), "project_id": 2, "workspace_id": 3,
        "human_instruction": "Clarify",
    })
    assert response.status_code == 200
    assert response.json() == {"outcome": "protected_not_found"}
    assert len(service.calls) == 1
    app.dependency_overrides.clear()


def test_malformed_request_has_no_domain_or_exception_detail():
    client, _service = _client(CaptureAdviceDisabled())
    response = client.post("/engineering-copilot/capture-advice", json={
        "capture_id": "bad", "project_id": 0, "human_instruction": "",
    })
    assert response.status_code == 422
    assert response.json() == {"outcome": "invalid_request"}
    app.dependency_overrides.clear()


def test_authentication_is_required_and_no_deferred_routes_exist():
    app.dependency_overrides.clear()
    client = TestClient(app)
    response = client.post("/engineering-copilot/capture-advice", json={
        "capture_id": str(uuid4()), "project_id": 2,
        "human_instruction": "Clarify",
    })
    assert response.status_code in (401, 403)
    for path in (
        "/engineering-copilot/conversations",
        "/engineering-copilot/approve",
        "/engineering-copilot/memory-admission",
    ):
        assert client.post(path).status_code == 404
