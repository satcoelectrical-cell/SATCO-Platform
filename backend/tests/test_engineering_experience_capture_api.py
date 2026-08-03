from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from app.exceptions.engineering_experience_capture import EngineeringExperienceCaptureIdempotencyConflict

from app.api.v1.routers.engineering_experience_captures import (
    EngineeringExperienceCaptureApplication,
    get_engineering_experience_capture_application,
)
from app.main import app
from app.models.engineering_experience_capture_command import EngineeringExperienceCaptureActor


CAPTURE_ID = UUID("28000000-0000-4000-8000-000000000001")
ORGANIZATION_ID = UUID("02810000-0000-4000-8000-000000000001")


def _capture(lifecycle="captured", version=1):
    return {
        "id": str(CAPTURE_ID), "organization_id": str(ORGANIZATION_ID),
        "project_id": 1, "workspace_id": 2, "discipline": "electrical",
        "engineering_object_id": None, "source_kind": "observation",
        "original_content": "Authorized engineering experience",
        "source_reference": None, "creator_id": 7, "lifecycle": lifecycle,
        "superseded_by_capture_id": None, "version": version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "allowed_actions": ["withdraw", "supersede"] if lifecycle == "captured" else [],
    }


class FakeCaptureService:
    def create(self, **_values): return _capture()
    def get(self, *_values): return _capture()
    def list_project(self, _project_id, _filters, page, size, _actor):
        return {"items": [_capture()], "total": 1, "page": page, "size": size}
    def list_workspace(self, _workspace_id, _filters, page, size, _actor):
        return {"items": [_capture()], "total": 1, "page": page, "size": size}
    def withdraw(self, *_values): return _capture("withdrawn", 2)
    def supersede(self, *_values):
        value = _capture("superseded", 2)
        value["superseded_by_capture_id"] = str(uuid4())
        return value
    def supersession_chain(self, *_values): return {"items": [_capture()]}


def _client():
    app.dependency_overrides[get_engineering_experience_capture_application] = lambda: (
        EngineeringExperienceCaptureApplication(
            service=FakeCaptureService(),
            actor=EngineeringExperienceCaptureActor(7, ORGANIZATION_ID),
        )
    )
    return TestClient(app)


def test_all_seven_approved_capture_endpoints():
    client = _client()
    headers = {"X-Correlation-ID": str(uuid4()), "Idempotency-Key": str(uuid4())}
    try:
        assert client.post("/engineering-experience-captures", headers=headers, json={
            "project_id": 1, "workspace_id": 2, "source_kind": "observation",
            "original_content": "Authorized engineering experience",
        }).status_code == 201
        assert client.get(f"/engineering-experience-captures/{CAPTURE_ID}").status_code == 200
        assert client.get("/projects/1/engineering-experience-captures").status_code == 200
        assert client.get("/engineering-workspaces/2/engineering-experience-captures").status_code == 200
        assert client.post(f"/engineering-experience-captures/{CAPTURE_ID}/withdraw", headers=headers,
                           json={"expected_version": 1, "rationale": "Withdraw"}).status_code == 200
        assert client.post(f"/engineering-experience-captures/{CAPTURE_ID}/supersede", headers=headers,
                           json={"expected_version": 1, "rationale": "Supersede",
                                 "replacement_capture_id": str(uuid4())}).status_code == 200
        assert client.get(f"/engineering-experience-captures/{CAPTURE_ID}/supersession-chain").status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_capture_transport_rejects_unapproved_methods_and_client_scope():
    client = _client()
    try:
        assert client.put(f"/engineering-experience-captures/{CAPTURE_ID}", json={}).status_code == 405
        assert client.patch(f"/engineering-experience-captures/{CAPTURE_ID}", json={}).status_code == 405
        assert client.delete(f"/engineering-experience-captures/{CAPTURE_ID}").status_code == 405
        response = client.post("/engineering-experience-captures", headers={
            "X-Correlation-ID": str(uuid4()), "Idempotency-Key": str(uuid4()),
        }, json={
            "project_id": 1, "source_kind": "observation", "original_content": "x",
            "organization_id": str(ORGANIZATION_ID),
        })
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_openapi_contains_exact_capture_route_method_set():
    expected = {
        ("/engineering-experience-captures", "post"),
        ("/engineering-experience-captures/{capture_id}", "get"),
        ("/projects/{project_id}/engineering-experience-captures", "get"),
        ("/engineering-workspaces/{workspace_id}/engineering-experience-captures", "get"),
        ("/engineering-experience-captures/{capture_id}/withdraw", "post"),
        ("/engineering-experience-captures/{capture_id}/supersede", "post"),
        ("/engineering-experience-captures/{capture_id}/supersession-chain", "get"),
    }
    actual = {
        (path, method)
        for path, contract in app.openapi()["paths"].items()
        if "engineering-experience-captures" in path
        for method in contract
    }
    assert actual == expected


def test_api_conflict_and_logs_do_not_echo_capture_plaintext(caplog):
    class ConflictService(FakeCaptureService):
        def create(self, **_values):
            raise EngineeringExperienceCaptureIdempotencyConflict()
        def withdraw(self, *_values):
            raise EngineeringExperienceCaptureIdempotencyConflict()

    app.dependency_overrides[get_engineering_experience_capture_application] = lambda: (
        EngineeringExperienceCaptureApplication(
            service=ConflictService(),
            actor=EngineeringExperienceCaptureActor(7, ORGANIZATION_ID),
        )
    )
    content = "API-CONTENT-PLAINTEXT-MARKER"
    reference = "API-REFERENCE-PLAINTEXT-MARKER"
    try:
        response = TestClient(app).post(
            "/engineering-experience-captures",
            headers={"X-Correlation-ID": str(uuid4()), "Idempotency-Key": str(uuid4())},
            json={"project_id": 1, "source_kind": "observation",
                  "original_content": content, "source_reference": reference},
        )
        assert response.status_code == 409
        rendered = response.text + "\n" + caplog.text
        assert content not in rendered
        assert reference not in rendered
        rationale = "API-RATIONALE-PLAINTEXT-MARKER"
        response = TestClient(app).post(
            f"/engineering-experience-captures/{CAPTURE_ID}/withdraw",
            headers={"X-Correlation-ID": str(uuid4()), "Idempotency-Key": str(uuid4())},
            json={"expected_version": 1, "rationale": rationale},
        )
        assert response.status_code == 409
        assert rationale not in response.text + "\n" + caplog.text
    finally:
        app.dependency_overrides.clear()
