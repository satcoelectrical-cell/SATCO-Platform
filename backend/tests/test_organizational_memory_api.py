"""PATCH-034 Batch 6 authenticated transport and composition evidence."""

from dataclasses import fields
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import create_access_token
from app.dependencies.organizational_memory import (
    OrganizationalMemoryApplication,
    get_organizational_memory_application,
    get_organizational_memory_service,
)
from app.enums.organizational_memory import MemoryStanding
from app.main import app
from app.models.organizational_memory_command import (
    AdmissionSuccess,
    CreateSuccessorSuccess,
    MemoryActor,
    MemoryInvalidRequest,
    MemoryProtectedNotFound,
    MemoryUnavailable,
    SupersessionSuccess,
    WithdrawalSuccess,
)
from app.models.organization import UserOrganizationMembership
from app.permissions.roles import Role
from conftest import create_user
from test_organizational_memory_integration import accepted_fixture
from test_organizational_memory_service import admit_command, setup


ORGANIZATION_ID = UUID("02810000-0000-4000-8000-000000000001")
HEADERS = {
    "X-Correlation-ID": "03400000-0000-4000-8000-000000000001",
    "Idempotency-Key": "03400000-0000-4000-8000-000000000002",
}


class RecordingMemoryService:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def __getattr__(self, operation):
        def invoke(*args):
            self.calls.append((operation, args))
            return self.results[operation]
        return invoke


@pytest.fixture
def memory_api(db_session):
    user = create_user(db_session, username="memory-api-user", role=Role.ENGINEER)
    sample_service, uow, _, source = setup()
    admitted = sample_service.admit(admit_command(source))
    memory_id = admitted.memory_id
    active = sample_service.get_active(MemoryActor(9, source.organization_id),
                                       __import__("app.models.organizational_memory_command", fromlist=["GetActiveMemory"]).GetActiveMemory(memory_id))
    listed = sample_service.list_active(MemoryActor(9, source.organization_id),
                                       __import__("app.models.organizational_memory_command", fromlist=["ListActiveMemory"]).ListActiveMemory(admit_command(source).scope, 10))
    history = sample_service.inspect_history(MemoryActor(9, source.organization_id),
                                             __import__("app.models.organizational_memory_command", fromlist=["InspectMemoryHistory"]).InspectMemoryHistory(memory_id))
    replacement_id = uuid4()
    results = {
        "admit": AdmissionSuccess("success", memory_id, 1,
                                   MemoryStanding.ACTIVE, admit_command(source).source),
        "get_active": active,
        "list_active": listed,
        "inspect_history": history,
        "create_successor": CreateSuccessorSuccess(
            "success", replacement_id, 1, MemoryStanding.ACTIVE,
            admit_command(source).source, memory_id,
        ),
        "withdraw": WithdrawalSuccess(
            "success", memory_id, 2, MemoryStanding.WITHDRAWN,
            uow.memories.items[memory_id].admitted_at,
        ),
        "supersede": SupersessionSuccess(
            "success", memory_id, 2, MemoryStanding.SUPERSEDED,
            replacement_id, 1, MemoryStanding.ACTIVE,
            uow.memories.items[memory_id].admitted_at,
        ),
    }
    service = RecordingMemoryService(results)

    def database_override():
        yield db_session

    app.dependency_overrides[get_db] = database_override
    app.dependency_overrides[get_organizational_memory_application] = lambda: (
        OrganizationalMemoryApplication(
            service=service,
            actor=MemoryActor(user.id, ORGANIZATION_ID),
        )
    )
    with TestClient(app) as client:
        yield client, service, user, source, memory_id, replacement_id
    app.dependency_overrides.clear()


def _auth(user):
    return {"Authorization": f"Bearer {create_access_token(user.id)}", **HEADERS}


def _admission(source, predecessor=None):
    value = {
        "report_id": str(source.report_id),
        "accepted_aggregate_version": source.accepted_aggregate_version,
        "accepted_snapshot_digest": source.integrity_digest,
        "workspace_id": source.workspace_id,
        "project_id": source.project_id,
        "audience_actor_ids": [],
        "reuse_restrictions": [],
        "admission_rationale": "Accepted engineering memory",
        "authority_rationale": "Explicit Human authority",
    }
    if predecessor is not None:
        value["predecessor_memory_id"] = str(predecessor)
    return value


def test_all_seven_routes_delegate_once_and_serialize_closed_success(memory_api):
    client, service, user, source, memory_id, replacement_id = memory_api
    headers = _auth(user)
    requests = (
        ("admit", "post", "/organizational-memory/admissions", _admission(source)),
        ("get_active", "get", f"/organizational-memory/{memory_id}", None),
        ("list_active", "get", "/organizational-memory", None),
        ("inspect_history", "get", f"/organizational-memory/{memory_id}/history", None),
        ("create_successor", "post", f"/organizational-memory/{memory_id}/successors", _admission(source, memory_id)),
        ("withdraw", "post", f"/organizational-memory/{memory_id}/withdrawal", {"expected_version": 1, "reason": "Withdraw", "authority_rationale": "Human withdrawal"}),
        ("supersede", "post", f"/organizational-memory/{memory_id}/supersession", {"replacement_memory_id": str(replacement_id), "expected_predecessor_version": 1, "expected_replacement_version": 1, "reason": "Supersede", "authority_rationale": "Human supersession"}),
    )
    for operation, method, path, body in requests:
        params = {"workspace_id": source.workspace_id, "project_id": source.project_id} if operation == "list_active" else None
        response = client.request(
            method.upper(), path, headers=headers, json=body, params=params,
        )
        assert response.status_code == 200, (operation, response.text)
        assert response.json()["outcome"] == "success"
    assert [call[0] for call in service.calls] == [item[0] for item in requests]


def test_protected_results_are_discriminator_only_for_every_route(memory_api):
    client, service, user, source, memory_id, replacement_id = memory_api
    for operation in service.results:
        service.results[operation] = MemoryProtectedNotFound()
    headers = _auth(user)
    calls = (
        client.post("/organizational-memory/admissions", headers=headers, json=_admission(source)),
        client.get(f"/organizational-memory/{memory_id}", headers=headers),
        client.get("/organizational-memory", headers=headers, params={"workspace_id": source.workspace_id}),
        client.get(f"/organizational-memory/{memory_id}/history", headers=headers),
        client.post(f"/organizational-memory/{memory_id}/successors", headers=headers, json=_admission(source, memory_id)),
        client.post(f"/organizational-memory/{memory_id}/withdrawal", headers=headers, json={"expected_version": 1, "reason": "Withdraw", "authority_rationale": "Human withdrawal"}),
        client.post(f"/organizational-memory/{memory_id}/supersession", headers=headers, json={"replacement_memory_id": str(replacement_id), "expected_predecessor_version": 1, "expected_replacement_version": 1, "reason": "Supersede", "authority_rationale": "Human supersession"}),
    )
    assert all(item.json() == {"outcome": "protected_not_found"} for item in calls)


def test_validation_is_payload_free_and_client_cannot_inject_authority(memory_api):
    client, service, user, source, _, _ = memory_api
    body = _admission(source)
    body["organization_id"] = str(uuid4())
    body["actor_id"] = 999
    response = client.post(
        "/organizational-memory/admissions", headers=_auth(user), json=body,
    )
    assert response.status_code == 422
    assert response.json() == {"outcome": "invalid_request"}
    assert service.calls == []


def test_continuation_is_passed_unchanged_to_application(memory_api):
    client, service, user, source, _, _ = memory_api
    token = "opaque-authenticated-continuation"
    response = client.get(
        "/organizational-memory", headers=_auth(user),
        params={"workspace_id": source.workspace_id, "continuation": token},
    )
    assert response.status_code == 200
    request = service.calls[-1][1][1]
    assert request.continuation == token


def test_registered_surface_is_exactly_the_seven_routes():
    actual = {
        (path, method)
        for path, contract in app.openapi()["paths"].items()
        if path.startswith("/organizational-memory")
        for method in contract
    }
    assert actual == {
        ("/organizational-memory/admissions", "post"),
        ("/organizational-memory/{memory_id}", "get"),
        ("/organizational-memory", "get"),
        ("/organizational-memory/{memory_id}/history", "get"),
        ("/organizational-memory/{predecessor_memory_id}/successors", "post"),
        ("/organizational-memory/{memory_id}/withdrawal", "post"),
        ("/organizational-memory/{predecessor_memory_id}/supersession", "post"),
    }


def test_payload_free_result_types_have_no_hidden_fields():
    assert all(
        [field.name for field in fields(value)] == ["outcome"]
        for value in (
            MemoryProtectedNotFound(), MemoryInvalidRequest(), MemoryUnavailable(),
        )
    )


def test_human_rationales_are_required_and_never_synthesized(memory_api):
    client, service, user, source, memory_id, replacement_id = memory_api
    headers = _auth(user)
    admission = _admission(source)
    without_admission = dict(admission); without_admission.pop("admission_rationale")
    without_authority = dict(admission); without_authority.pop("authority_rationale")
    mutation_cases = (
        ("/organizational-memory/admissions", without_admission),
        ("/organizational-memory/admissions", without_authority),
        (f"/organizational-memory/{memory_id}/successors",
         {key: value for key, value in _admission(source, memory_id).items()
          if key != "authority_rationale"}),
        (f"/organizational-memory/{memory_id}/withdrawal",
         {"expected_version": 1, "reason": "Withdraw"}),
        (f"/organizational-memory/{memory_id}/supersession", {
            "replacement_memory_id": str(replacement_id),
            "expected_predecessor_version": 1,
            "expected_replacement_version": 1,
            "reason": "Supersede",
        }),
    )
    responses = [
        client.post(path, headers=headers, json=body)
        for path, body in mutation_cases
    ]
    assert all(response.status_code == 422 for response in responses)
    assert all(response.json() == {"outcome": "invalid_request"}
               for response in responses)
    assert service.calls == []

    schemas = app.openapi()["components"]["schemas"]
    assert "admission_rationale" in schemas["AdmissionBody"]["required"]
    assert "authority_rationale" in schemas["AdmissionBody"]["required"]
    assert "authority_rationale" in schemas["SuccessorBody"]["required"]
    assert "authority_rationale" in schemas["WithdrawalBody"]["required"]
    assert "authority_rationale" in schemas["SupersessionBody"]["required"]
    for name in ("AdmissionBody", "SuccessorBody", "WithdrawalBody",
                 "SupersessionBody"):
        for field_name, contract in schemas[name].get("properties", {}).items():
            if "rationale" in field_name:
                assert "default" not in contract


def test_transport_rejects_audience_and_restriction_contract_violations(
    memory_api,
):
    client, service, user, source, _, _ = memory_api
    invalid_bodies = []
    for audience in ([2, 1], [1, 1]):
        body = _admission(source); body["audience_actor_ids"] = audience
        invalid_bodies.append(body)
    excessive = _admission(source)
    excessive["reuse_restrictions"] = [f"restriction-{i}" for i in range(33)]
    invalid_bodies.append(excessive)
    malformed = _admission(source)
    malformed["audience_actor_ids"] = [True]
    invalid_bodies.append(malformed)

    responses = [client.post(
        "/organizational-memory/admissions", headers=_auth(user), json=body,
    ) for body in invalid_bodies]
    assert all(response.status_code == 422 for response in responses)
    assert all(response.json() == {"outcome": "invalid_request"}
               for response in responses)
    assert service.calls == []


def test_downstream_domain_validation_is_closed_and_non_disclosing(memory_api):
    client, service, user, source, _, _ = memory_api
    body = _admission(source)
    body["admission_rationale"] = "   "
    response = client.post(
        "/organizational-memory/admissions", headers=_auth(user), json=body,
    )
    assert response.status_code == 422
    assert response.json() == {"outcome": "invalid_request"}
    assert "rationale" not in response.text
    assert service.calls == []


def test_real_authentication_and_server_organization_build_trusted_actor(db_session):
    user = create_user(db_session, username="memory-real-context", role=Role.ENGINEER)
    service = RecordingMemoryService({"get_active": MemoryProtectedNotFound()})

    def database_override():
        yield db_session

    app.dependency_overrides[get_db] = database_override
    app.dependency_overrides[get_organizational_memory_service] = lambda: service
    memory_id = uuid4()
    with TestClient(app) as client:
        unauthenticated = client.get(f"/organizational-memory/{memory_id}")
        authenticated = client.get(
            f"/organizational-memory/{memory_id}", headers=_auth(user),
        )
    app.dependency_overrides.clear()

    assert unauthenticated.status_code == 401
    assert authenticated.json() == {"outcome": "protected_not_found"}
    actor = service.calls[0][1][0]
    assert actor.actor_id == user.id
    assert actor.organization_id == ORGANIZATION_ID


def test_disabled_membership_denies_before_application_call(db_session):
    user = create_user(db_session, username="memory-disabled-context", role=Role.ENGINEER)
    membership = db_session.query(UserOrganizationMembership).filter_by(
        user_id=user.id, organization_id=ORGANIZATION_ID,
    ).one()
    membership.is_enabled = False
    membership.is_selected = False
    db_session.flush()
    service = RecordingMemoryService({"get_active": MemoryProtectedNotFound()})

    def database_override():
        yield db_session

    app.dependency_overrides[get_db] = database_override
    app.dependency_overrides[get_organizational_memory_service] = lambda: service
    with TestClient(app) as client:
        response = client.get(
            f"/organizational-memory/{uuid4()}", headers=_auth(user),
        )
    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == (
        "ACTIVE_ORGANIZATION_CONTEXT_REQUIRED"
    )
    assert service.calls == []
