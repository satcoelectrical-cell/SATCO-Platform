from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.routers.engineering_relationships import (
    EngineeringRelationshipApplication,
    get_engineering_relationship_application,
    router,
)
from app.models.engineering_relationship_command import (
    AuthenticatedRelationshipActor,
)


RELATIONSHIP_ID = uuid4()
SOURCE_ID = uuid4()
TARGET_ID = uuid4()
ORGANIZATION_ID = uuid4()


def response():
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": str(RELATIONSHIP_ID), "organization_id": str(ORGANIZATION_ID),
        "project_id": 1, "workspace_id": 1,
        "source_object_id": str(SOURCE_ID), "target_object_id": str(TARGET_ID),
        "relationship_family": "electrical", "relationship_type": "powered_by",
        "lifecycle": "proposed", "authority_standing": "draft",
        "evidence_references": [], "version": 1, "creator_id": 1,
        "steward_id": 1, "reviewer_id": None, "approver_id": None,
        "created_at": now, "updated_at": now, "allowed_actions": ["submit"],
    }


class FakeService:
    def __getattr__(self, name):
        def call(*args, **kwargs):
            if name == "list_for_endpoint":
                return {"items": [response()], "total": 1, "page": 1, "size": 20}
            if name in {"neighborhood", "path"}:
                return {
                    "node_ids": [str(SOURCE_ID), str(TARGET_ID)],
                    "relationships": [response()], "bounded_depth": 1,
                    "truncated": False, "continuation_token": None,
                }
            return response()
        return call


def client():
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_engineering_relationship_application] = lambda: (
        EngineeringRelationshipApplication(
            FakeService(),
            AuthenticatedRelationshipActor(1, ORGANIZATION_ID),
        )
    )
    return TestClient(app)


def headers():
    return {"X-Correlation-ID": str(uuid4()), "Idempotency-Key": str(uuid4())}


def command_payload(**values):
    payload = {
        "relationship_family": "electrical",
        "relationship_type": "powered_by",
        "expected_version": 1, "rationale": "Approved command",
        "evidence_references": [],
    }
    payload.update(values)
    return payload


def test_all_twelve_approved_endpoints_and_no_generic_mutation():
    test_client = client()
    create = test_client.post(
        "/engineering-relationships", headers=headers(), json={
            "source_object_id": str(SOURCE_ID),
            "target_object_id": str(TARGET_ID),
            "relationship_family": "electrical",
            "relationship_type": "powered_by", "rationale": "Create",
        },
    )
    assert create.status_code == 201
    assert test_client.get(
        f"/engineering-relationships/{RELATIONSHIP_ID}"
    ).status_code == 200
    assert test_client.get(
        f"/engineering-objects/{SOURCE_ID}/relationships"
    ).status_code == 200
    assert test_client.get(
        f"/engineering-objects/{SOURCE_ID}/relationship-neighborhood"
    ).status_code == 200
    assert test_client.get(
        f"/engineering-objects/{SOURCE_ID}/relationship-paths",
        params={"target_object_id": str(TARGET_ID)},
    ).status_code == 200

    commands = {
        "submissions": {}, "reviews": {}, "approvals": {}, "disputes": {},
        "rejections": {},
        "lifecycle-transitions": {"lifecycle": "withdrawn"},
        "steward-transfers": {"steward_id": 2},
    }
    for suffix, extra in commands.items():
        result = test_client.post(
            f"/engineering-relationships/{RELATIONSHIP_ID}/{suffix}",
            headers=headers(), json=command_payload(**extra),
        )
        assert result.status_code == 200, (suffix, result.text)

    paths_and_methods = {(route.path, method) for route in router.routes
                         for method in route.methods}
    assert not any(method in {"PUT", "PATCH", "DELETE"}
                   for _, method in paths_and_methods)


def test_request_validation_rejects_missing_family_and_unbounded_traversal():
    test_client = client()
    invalid = command_payload()
    invalid.pop("relationship_family")
    validation = test_client.post(
        f"/engineering-relationships/{RELATIONSHIP_ID}/submissions",
        headers=headers(), json=invalid,
    )
    assert validation.status_code == 422
    assert validation.json()["error"]["code"] == (
        "ENGINEERING_RELATIONSHIP_VALIDATION_ERROR"
    )
    assert test_client.get(
        f"/engineering-objects/{SOURCE_ID}/relationship-neighborhood",
        params={"max_depth": 6},
    ).status_code == 422


def test_response_contract_contains_no_persisted_confidentiality():
    payload = client().get(
        f"/engineering-relationships/{RELATIONSHIP_ID}"
    ).json()
    assert "confidentiality" not in payload
