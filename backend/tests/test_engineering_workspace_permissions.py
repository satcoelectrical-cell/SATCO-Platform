import pytest

from app.core.security import hash_password
from app.models.customer import Customer
from app.models.user import User
from app.permissions.roles import Role


def _user(db_session, username):
    user = User(
        email=f"{username}@example.com",
        username=username,
        full_name=username.title(),
        role=Role.ENGINEER.value,
        hashed_password=hash_password("correct-password"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _headers(client, username):
    response = client.post(
        "/auth/login",
        data={
            "username": username,
            "password": "correct-password",
        },
    )
    return {
        "Authorization": (
            f"Bearer {response.json()['access_token']}"
        )
    }


def test_workspace_permission_and_collaborator_boundaries(
    client,
    db_session,
    engineer_user,
    engineer_headers,
    admin_headers,
):
    other = _user(db_session, "workspace-other")
    collaborator = _user(
        db_session,
        "workspace-collaborator",
    )
    other_headers = _headers(client, other.username)
    collaborator_headers = _headers(
        client,
        collaborator.username,
    )
    customer = Customer(name="Workspace Permission Customer")
    db_session.add(customer)
    db_session.commit()
    project = client.post(
        "/projects/",
        headers=engineer_headers,
        json={
            "name": "Workspace Permission Project",
            "customer_id": customer.id,
            "owner_id": engineer_user.id,
        },
    ).json()

    denied_create = client.post(
        f"/projects/{project['id']}/workspaces",
        headers=other_headers,
        json={"discipline": "control"},
    )
    assert denied_create.status_code == 403

    created = client.post(
        f"/projects/{project['id']}/workspaces",
        headers=engineer_headers,
        json={"discipline": "control"},
    ).json()

    hidden = client.get(
        f"/workspaces/{created['id']}",
        headers=other_headers,
    )
    assert hidden.status_code == 404

    added = client.post(
        f"/workspaces/{created['id']}/collaborators",
        headers=engineer_headers,
        json={
            "user_id": collaborator.id,
            "expected_version": 1,
        },
    )
    assert added.status_code == 200

    visible = client.get(
        f"/workspaces/{created['id']}",
        headers=collaborator_headers,
    )
    assert visible.status_code == 200

    denied_governance = client.post(
        f"/workspaces/{created['id']}/archive",
        headers=collaborator_headers,
        json={"reason": "No authority", "expected_version": 2},
    )
    assert denied_governance.status_code == 403

    admin_visible = client.get(
        f"/workspaces/{created['id']}",
        headers=admin_headers,
    )
    assert admin_visible.status_code == 200


@pytest.mark.parametrize(
    ("field", "user_kind", "expected_code"),
    [
        ("owner_id", "missing", "INVALID_WORKSPACE_OWNER"),
        ("owner_id", "inactive", "INVALID_WORKSPACE_OWNER"),
        ("owner_id", "unsupported", "INVALID_WORKSPACE_OWNER"),
        (
            "primary_assignee_id",
            "missing",
            "INVALID_WORKSPACE_ASSIGNEE",
        ),
        (
            "primary_assignee_id",
            "inactive",
            "INVALID_WORKSPACE_ASSIGNEE",
        ),
        (
            "primary_assignee_id",
            "unsupported",
            "INVALID_WORKSPACE_ASSIGNEE",
        ),
    ],
)
def test_workspace_assignment_validation(
    client,
    db_session,
    engineer_user,
    engineer_headers,
    field,
    user_kind,
    expected_code,
):
    customer = Customer(name=f"Assignment Validation {field} {user_kind}")
    db_session.add(customer)
    db_session.commit()
    invalid_id = 2_000_000_000
    if user_kind != "missing":
        invalid = _user(db_session, f"{field}-{user_kind}")
        if user_kind == "inactive":
            invalid.is_active = False
        else:
            invalid.role = "viewer"
        db_session.commit()
        invalid_id = invalid.id
    project = client.post(
        "/projects/",
        headers=engineer_headers,
        json={
            "name": "Assignment Validation Project",
            "customer_id": customer.id,
            "owner_id": engineer_user.id,
        },
    ).json()

    response = client.post(
        f"/projects/{project['id']}/workspaces",
        headers=engineer_headers,
        json={"discipline": "electrical", field: invalid_id},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == expected_code


@pytest.mark.parametrize("user_kind", ["missing", "inactive", "unsupported"])
def test_invalid_collaborator_is_rejected(
    client,
    db_session,
    engineer_user,
    engineer_headers,
    user_kind,
):
    customer = Customer(name=f"Collaborator Validation {user_kind}")
    db_session.add(customer)
    db_session.commit()
    invalid_id = 2_000_000_000
    if user_kind != "missing":
        invalid = _user(db_session, f"collaborator-{user_kind}")
        if user_kind == "inactive":
            invalid.is_active = False
        else:
            invalid.role = "viewer"
        db_session.commit()
        invalid_id = invalid.id
    project = client.post(
        "/projects/",
        headers=engineer_headers,
        json={
            "name": "Collaborator Validation Project",
            "customer_id": customer.id,
            "owner_id": engineer_user.id,
        },
    ).json()
    workspace = client.post(
        f"/projects/{project['id']}/workspaces",
        headers=engineer_headers,
        json={"discipline": "instrumentation"},
    ).json()

    response = client.post(
        f"/workspaces/{workspace['id']}/collaborators",
        headers=engineer_headers,
        json={"user_id": invalid_id, "expected_version": 1},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == (
        "INVALID_WORKSPACE_COLLABORATOR"
    )


@pytest.fixture
def permission_workspace(client, db_session):
    users = {
        name: _user(db_session, f"boundary-{name.replace('_', '-')}")
        for name in (
            "project_owner",
            "workspace_owner",
            "assignee",
            "collaborator",
            "unrelated",
        )
    }
    customer = Customer(name="Complete Permission Boundary Customer")
    db_session.add(customer)
    db_session.commit()
    project_headers = _headers(client, users["project_owner"].username)
    project = client.post(
        "/projects/",
        headers=project_headers,
        json={
            "name": "Complete Permission Boundary Project",
            "customer_id": customer.id,
            "owner_id": users["project_owner"].id,
        },
    ).json()
    workspace = client.post(
        f"/projects/{project['id']}/workspaces",
        headers=project_headers,
        json={
            "discipline": "control",
            "owner_id": users["workspace_owner"].id,
            "primary_assignee_id": users["assignee"].id,
            "collaborator_ids": [users["collaborator"].id],
        },
    ).json()
    return {
        "users": users,
        "headers": {
            name: _headers(client, user.username)
            for name, user in users.items()
        },
        "project": project,
        "workspace": workspace,
    }


@pytest.mark.parametrize(
    ("persona", "visible", "description", "assign_owner", "governance"),
    [
        ("workspace_owner", True, True, False, True),
        ("project_owner", True, True, True, True),
        ("assignee", True, True, False, False),
        ("collaborator", True, False, False, False),
        ("unrelated", False, False, False, False),
        ("admin", True, True, True, True),
    ],
)
def test_complete_workspace_permission_boundaries(
    client,
    admin_headers,
    permission_workspace,
    persona,
    visible,
    description,
    assign_owner,
    governance,
):
    workspace = permission_workspace["workspace"]
    users = permission_workspace["users"]
    headers = (
        admin_headers
        if persona == "admin"
        else permission_workspace["headers"][persona]
    )

    retrieved = client.get(
        f"/workspaces/{workspace['id']}", headers=headers
    )
    assert retrieved.status_code == (200 if visible else 404)

    update_description = client.patch(
        f"/workspaces/{workspace['id']}",
        headers=headers,
        json={"description": "Boundary update", "expected_version": 1},
    )
    assert update_description.status_code == (
        200 if description else (404 if not visible else 403)
    )

    assign = client.patch(
        f"/workspaces/{workspace['id']}",
        headers=headers,
        json={
            "owner_id": users["unrelated"].id,
            "expected_version": 2 if description else 1,
        },
    )
    assert assign.status_code == (
        200 if assign_owner else (404 if not visible else 403)
    )

    expected_version = 3 if assign_owner and description else (
        2 if description else 1
    )
    transition = client.post(
        f"/workspaces/{workspace['id']}/transitions",
        headers=headers,
        json={"status": "active", "expected_version": expected_version},
    )
    assert transition.status_code == (
        200 if governance else (404 if not visible else 403)
    )


def test_assignment_and_collaborator_semantics_reject_overlap(
    client,
    permission_workspace,
):
    workspace = permission_workspace["workspace"]
    users = permission_workspace["users"]
    headers = permission_workspace["headers"]["project_owner"]

    owner_as_collaborator = client.post(
        f"/workspaces/{workspace['id']}/collaborators",
        headers=headers,
        json={
            "user_id": users["workspace_owner"].id,
            "expected_version": 1,
        },
    )
    assert owner_as_collaborator.status_code == 422
    collaborator_as_assignee = client.patch(
        f"/workspaces/{workspace['id']}",
        headers=headers,
        json={
            "primary_assignee_id": users["collaborator"].id,
            "expected_version": 1,
        },
    )
    assert collaborator_as_assignee.status_code == 422
