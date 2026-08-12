"""PATCH-033 Batch 3 authenticated transport evidence."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.dependencies.engineering_knowledge_graph import (
    get_engineering_object_read_service,
)
from app.core.database import get_db
from app.core.security import create_access_token
from app.exceptions.engineering_object import EngineeringObjectProtectedNotFound
from app.main import app
from app.models.organization import UserOrganizationMembership
from app.permissions.roles import Role
from app.schemas.engineering_object import EngineeringObjectResponse
from conftest import create_user


ORGANIZATION_ID = UUID("02810000-0000-4000-8000-000000000001")
NODE_ID = UUID("03300000-0000-4000-8000-000000000001")
NOW = datetime(2026, 8, 12, tzinfo=timezone.utc)


def _response():
    return EngineeringObjectResponse(
        id=NODE_ID,
        organization_id=ORGANIZATION_ID,
        customer_id=None,
        project_id=11,
        workspace_id=12,
        family="electrical",
        discipline="electrical",
        object_type="motor",
        subtype=None,
        lifecycle="active",
        authority_standing="approved",
        version=3,
        creator_id=7,
        steward_id=7,
        created_at=NOW,
        updated_at=NOW,
    )


class _CanonicalRead:
    def __init__(self):
        self.outcome = _response()
        self.calls = []

    def get(self, object_id, actor, context):
        self.calls.append((object_id, actor, context))
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome


@pytest.fixture
def real_context_graph_api(db_session):
    canonical = _CanonicalRead()

    def database_override():
        yield db_session

    app.dependency_overrides[get_db] = database_override
    app.dependency_overrides[get_engineering_object_read_service] = lambda: canonical
    with TestClient(app) as client:
        yield client, canonical
    app.dependency_overrides.clear()


def _headers(user_id):
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def test_real_jwt_and_organization_context_disclose_exact_authorized_projection(
    real_context_graph_api,
    db_session,
):
    client, canonical = real_context_graph_api
    user = create_user(db_session, username="graph-reader", role=Role.ENGINEER)

    response = client.get(
        f"/engineering-knowledge-graph/nodes/{NODE_ID}",
        headers=_headers(user.id),
        params={"project_id": 11, "workspace_id": 12},
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "status": "success",
        "node": {
            "node_type": "engineering_object",
            "node_id": str(NODE_ID),
            **_response().model_dump(mode="json", exclude={"id"}),
        },
    }
    assert len(canonical.calls) == 1
    _, actor, context = canonical.calls[0]
    assert actor.actor_id == user.id
    assert actor.organization_id == ORGANIZATION_ID
    assert context.operation == "ReadEngineeringObject"


def test_missing_invalid_and_inactive_auth_are_rejected_before_canonical_read(
    real_context_graph_api,
    db_session,
):
    client, canonical = real_context_graph_api
    inactive = create_user(
        db_session,
        username="inactive-graph-reader",
        role=Role.ENGINEER,
        is_active=False,
    )

    responses = (
        client.get(f"/engineering-knowledge-graph/nodes/{NODE_ID}"),
        client.get(
            f"/engineering-knowledge-graph/nodes/{NODE_ID}",
            headers={"Authorization": "Bearer invalid"},
        ),
        client.get(
            f"/engineering-knowledge-graph/nodes/{NODE_ID}",
            headers=_headers(inactive.id),
        ),
    )

    assert [item.status_code for item in responses] == [401, 401, 403]
    assert [item.json() for item in responses] == [
        {"detail": "Not authenticated"},
        {"detail": "Invalid authentication credentials"},
        {"detail": "Inactive user"},
    ]
    assert canonical.calls == []


def test_disabled_or_missing_organization_context_denies_before_canonical_read(
    real_context_graph_api,
    db_session,
):
    client, canonical = real_context_graph_api
    user = create_user(
        db_session,
        username="disabled-graph-member",
        role=Role.ENGINEER,
    )
    membership = db_session.query(UserOrganizationMembership).filter_by(
        user_id=user.id,
        organization_id=ORGANIZATION_ID,
    ).one()
    membership.is_enabled = False
    membership.is_selected = False
    db_session.flush()

    response = client.get(
        f"/engineering-knowledge-graph/nodes/{NODE_ID}",
        headers=_headers(user.id),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == (
        "ACTIVE_ORGANIZATION_CONTEXT_REQUIRED"
    )
    assert canonical.calls == []


def test_genuine_nonmember_has_same_stable_organization_denial(
    real_context_graph_api,
    db_session,
):
    client, canonical = real_context_graph_api
    user = create_user(db_session, username="nonmember-graph-user", role=Role.ENGINEER)
    db_session.query(UserOrganizationMembership).filter_by(
        user_id=user.id,
        organization_id=ORGANIZATION_ID,
    ).delete(synchronize_session=False)
    db_session.flush()

    response = client.get(
        f"/engineering-knowledge-graph/nodes/{NODE_ID}",
        headers=_headers(user.id),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == (
        "ACTIVE_ORGANIZATION_CONTEXT_REQUIRED"
    )
    assert canonical.calls == []


def test_closed_application_outcomes_are_payload_free_and_non_disclosing(
    real_context_graph_api,
    db_session,
    caplog,
):
    client, canonical = real_context_graph_api
    user = create_user(
        db_session,
        username="protected-graph-reader",
        role=Role.ENGINEER,
    )
    secret = "protected engineering plaintext"

    canonical.outcome = EngineeringObjectProtectedNotFound(NODE_ID)
    protected = client.get(
        f"/engineering-knowledge-graph/nodes/{NODE_ID}",
        headers=_headers(user.id),
    )
    canonical.outcome = RuntimeError(secret)
    unavailable = client.get(
        f"/engineering-knowledge-graph/nodes/{NODE_ID}",
        headers=_headers(user.id),
    )
    invalid = client.get(
        "/engineering-knowledge-graph/nodes/not-a-uuid",
        headers=_headers(user.id),
    )

    assert protected.json() == {"status": "protected_not_found"}
    assert unavailable.json() == {"status": "unavailable"}
    assert invalid.json() == {"status": "invalid_request"}
    assert secret not in caplog.text
    assert str(NODE_ID) not in caplog.text


def test_optional_scope_mismatch_is_protected_after_one_authorized_read(
    real_context_graph_api,
    db_session,
):
    client, canonical = real_context_graph_api
    user = create_user(
        db_session,
        username="cross-scope-graph-reader",
        role=Role.ENGINEER,
    )

    for params in ({"project_id": 99}, {"workspace_id": 99}):
        before = len(canonical.calls)
        response = client.get(
            f"/engineering-knowledge-graph/nodes/{NODE_ID}",
            headers=_headers(user.id),
            params=params,
        )
        assert response.json() == {"status": "protected_not_found"}
        assert len(canonical.calls) == before + 1


def test_registered_surface_contains_only_the_single_node_read():
    actual = {
        (path, method)
        for path, contract in app.openapi()["paths"].items()
        if path.startswith("/engineering-knowledge-graph")
        for method in contract
    }
    assert actual == {
        ("/engineering-knowledge-graph/nodes/{node_id}", "get")
    }


@pytest.mark.parametrize("suffix", ("edges", "traversal", "search", "nodes"))
def test_deferred_and_collection_routes_are_absent(
    real_context_graph_api,
    db_session,
    suffix,
):
    client, _ = real_context_graph_api
    user = create_user(
        db_session,
        username=f"prohibited-{suffix}",
        role=Role.ENGINEER,
    )
    response = client.get(
        f"/engineering-knowledge-graph/{suffix}",
        headers=_headers(user.id),
    )
    assert response.status_code == 404
