"""Endpoint contract tests for PATCH-023 EngineeringObject transport."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from app.api.v1.routers.engineering_objects import (
    EngineeringObjectApplication,
    get_engineering_object_application,
)
from app.exceptions.engineering_object import (
    EngineeringObjectProtectedNotFound,
    EngineeringObjectVersionConflict,
)
from app.main import app
from app.models.engineering_object_command import AuthenticatedActor
from app.schemas.engineering_object import (
    EngineeringObjectListResponse,
    EngineeringObjectResponse,
)


OBJECT_ID = UUID("11111111-1111-4111-8111-111111111111")
ORGANIZATION_ID = UUID("22222222-2222-4222-8222-222222222222")
CORRELATION_ID = "33333333-3333-4333-8333-333333333333"
IDEMPOTENCY_ID = "44444444-4444-4444-8444-444444444444"
COMMAND_HEADERS = {
    "X-Correlation-ID": CORRELATION_ID,
    "Idempotency-Key": IDEMPOTENCY_ID,
}


def _response() -> EngineeringObjectResponse:
    now = datetime(2026, 8, 1, tzinfo=timezone.utc)
    return EngineeringObjectResponse(
        id=OBJECT_ID,
        organization_id=ORGANIZATION_ID,
        customer_id=7,
        project_id=11,
        workspace_id=13,
        family="instrumentation",
        discipline="instrumentation",
        object_type="instrument",
        subtype=None,
        lifecycle="proposed",
        authority_standing="draft",
        version=1,
        creator_id=17,
        steward_id=17,
        created_at=now,
        updated_at=now,
    )


class ServiceStub:
    """Small application-boundary fake; transport tests never bypass the port."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []
        self.failure: Exception | None = None

    def _result(self, operation: str, context):
        self.calls.append((operation, context))
        if self.failure is not None:
            raise self.failure
        return _response()

    def create(self, **values):
        return self._result("create", values["context"])

    def get(self, object_id, actor, context):
        return self._result("get", context)

    def list(self, **values):
        result = self._result("list", values["context"])
        return EngineeringObjectListResponse(
            items=[result], total=1, page=values["page"], size=values["size"]
        )

    def reclassify(self, object_id, data, actor, context, *metadata):
        return self._result("reclassify", context)

    def transition_lifecycle(self, object_id, data, actor, context, *metadata):
        return self._result("transition_lifecycle", context)

    def transition_authority(self, object_id, data, actor, context, *metadata):
        return self._result("transition_authority", context)

    def transfer_steward(self, object_id, data, actor, context, *metadata):
        return self._result("transfer_steward", context)


@pytest.fixture
def engineering_object_api(client):
    service = ServiceStub()
    actor = AuthenticatedActor(actor_id=17, organization_id=ORGANIZATION_ID)
    app.dependency_overrides[get_engineering_object_application] = lambda: (
        EngineeringObjectApplication(service=service, actor=actor)
    )
    yield client, service
    app.dependency_overrides.pop(get_engineering_object_application, None)


def test_create_uses_trusted_context(engineering_object_api):
    client, service = engineering_object_api
    response = client.post(
        "/engineering-objects",
        headers=COMMAND_HEADERS,
        json={
            "project_id": 11,
            "family": "instrumentation",
            "discipline": "instrumentation",
            "object_type": "instrument",
            "rationale": "Initial creation",
        },
    )
    assert response.status_code == 201
    assert response.json()["organization_id"] == str(ORGANIZATION_ID)
    assert service.calls[0][1].operation == "CreateEngineeringObject"


@pytest.mark.parametrize(
    ("path", "body", "operation"),
    [
        (
            "reclassifications",
            {
                "expected_version": 1,
                "rationale": "Correct classification",
                "family": "electrical",
                "discipline": "electrical",
                "object_type": "motor",
            },
            "ReclassifyEngineeringObject",
        ),
        (
            "lifecycle-transitions",
            {
                "expected_version": 1,
                "rationale": "Begin use",
                "lifecycle": "active",
            },
            "TransitionEngineeringObjectLifecycle",
        ),
        (
            "authority-transitions",
            {
                "expected_version": 1,
                "rationale": "Ready for review",
                "authority_standing": "proposed",
            },
            "TransitionEngineeringObjectAuthority",
        ),
        (
            "steward-transfers",
            {
                "expected_version": 1,
                "rationale": "Transfer responsibility",
                "steward_id": 19,
            },
            "TransferEngineeringObjectSteward",
        ),
    ],
)
def test_mutation_endpoints_use_canonical_commands(
    engineering_object_api, path, body, operation
):
    client, service = engineering_object_api
    response = client.post(
        f"/engineering-objects/{OBJECT_ID}/{path}",
        headers=COMMAND_HEADERS,
        json=body,
    )
    assert response.status_code == 200
    assert service.calls[0][1].operation == operation


def test_read_and_list_are_authorized_operations(engineering_object_api):
    client, service = engineering_object_api
    read = client.get(f"/engineering-objects/{OBJECT_ID}")
    listed = client.get(
        "/projects/11/engineering-objects",
        params={"page": 2, "size": 5, "discipline": "instrumentation"},
    )
    assert read.status_code == 200
    assert listed.status_code == 200
    assert listed.json()["page"] == 2
    assert [call[1].operation for call in service.calls] == [
        "ReadEngineeringObject",
        "ListEngineeringObjects",
    ]


def test_client_cannot_supply_organization_scope(engineering_object_api):
    client, service = engineering_object_api
    response = client.post(
        "/engineering-objects",
        headers=COMMAND_HEADERS,
        json={
            "project_id": 11,
            "organization_id": str(uuid4()),
            "family": "instrumentation",
            "discipline": "instrumentation",
            "object_type": "instrument",
            "rationale": "Invalid scope injection",
        },
    )
    assert response.status_code == 422
    assert service.calls == []


def test_post_creation_mutation_requires_positive_expected_version(
    engineering_object_api,
):
    client, service = engineering_object_api
    response = client.post(
        f"/engineering-objects/{OBJECT_ID}/steward-transfers",
        headers=COMMAND_HEADERS,
        json={
            "expected_version": 0,
            "rationale": "Invalid version",
            "steward_id": 19,
        },
    )
    assert response.status_code == 422
    assert service.calls == []


def test_protected_not_found_uses_stable_error_mapping(engineering_object_api):
    client, service = engineering_object_api
    service.failure = EngineeringObjectProtectedNotFound(OBJECT_ID)
    response = client.get(f"/engineering-objects/{OBJECT_ID}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ENGINEERING_OBJECT_NOT_FOUND"


def test_version_conflict_uses_stable_error_mapping(engineering_object_api):
    client, service = engineering_object_api
    service.failure = EngineeringObjectVersionConflict()
    response = client.post(
        f"/engineering-objects/{OBJECT_ID}/steward-transfers",
        headers=COMMAND_HEADERS,
        json={
            "expected_version": 1,
            "rationale": "Concurrent transfer",
            "steward_id": 19,
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == (
        "ENGINEERING_OBJECT_VERSION_CONFLICT"
    )


@pytest.mark.parametrize("method", ["put", "patch", "delete"])
def test_generic_mutation_and_physical_delete_are_not_exposed(
    engineering_object_api, method
):
    client, _ = engineering_object_api
    response = client.request(
        method.upper(), f"/engineering-objects/{OBJECT_ID}", json={}
    )
    assert response.status_code == 405
