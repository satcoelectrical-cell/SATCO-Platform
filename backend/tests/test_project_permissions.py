from conftest import create_user
from uuid import UUID

from app.models.project import Project
from app.permissions.roles import Role


def create_customer(client, headers):
    response = client.post(
        "/customers/",
        json={"name": "Permission Customer"},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_project_permission_matrix(
    client,
    db_session,
    engineer_user,
    engineer_headers,
    admin_user,
    admin_headers,
):
    other = create_user(
        db_session,
        username="other_engineer",
        role=Role.ENGINEER,
    )
    customer_id = create_customer(
        client,
        engineer_headers,
    )

    forbidden_owner = client.post(
        "/projects/",
        json={
            "name": "Forbidden Owner",
            "customer_id": customer_id,
            "owner_id": other.id,
        },
        headers=engineer_headers,
    )
    assert forbidden_owner.status_code == 403

    created = client.post(
        "/projects/",
        json={
            "name": "Permission Project",
            "customer_id": customer_id,
            "owner_id": engineer_user.id,
            "primary_assignee_id": other.id,
        },
        headers=admin_headers,
    )
    assert created.status_code == 200
    project_id = created.json()["id"]

    unrelated = create_user(
        db_session,
        username="unrelated_engineer",
        role=Role.ENGINEER,
    )
    from conftest import login_headers

    unrelated_headers = login_headers(
        client,
        unrelated.username,
    )
    denied = client.put(
        f"/projects/{project_id}",
        json={"progress": 20},
        headers=unrelated_headers,
    )
    assert denied.status_code == 403

    assignee_headers = login_headers(
        client,
        other.username,
    )
    allowed = client.put(
        f"/projects/{project_id}",
        json={
            "status": "in_progress",
            "progress": 20,
        },
        headers=assignee_headers,
    )
    assert allowed.status_code == 200

    assignee_cannot_reassign = client.put(
        f"/projects/{project_id}",
        json={"primary_assignee_id": None},
        headers=assignee_headers,
    )
    assert assignee_cannot_reassign.status_code == 403

    owner_reassigns = client.put(
        f"/projects/{project_id}",
        json={"primary_assignee_id": engineer_user.id},
        headers=engineer_headers,
    )
    assert owner_reassigns.status_code == 200

    owner_cannot_transfer = client.put(
        f"/projects/{project_id}",
        json={"owner_id": other.id},
        headers=engineer_headers,
    )
    assert owner_cannot_transfer.status_code == 403

    admin_transfers = client.put(
        f"/projects/{project_id}",
        json={"owner_id": admin_user.id},
        headers=admin_headers,
    )
    assert admin_transfers.status_code == 200


def test_legacy_unowned_project_is_updateable(
    client,
    db_session,
    engineer_headers,
):
    customer_id = create_customer(
        client,
        engineer_headers,
    )
    project = Project(
        organization_id=UUID("02810000-0000-4000-8000-000000000001"),
        project_code="SAT-PRJ-2025-9001",
        name="Legacy Unowned",
        customer_id=customer_id,
        status="new",
        priority="medium",
        owner_id=None,
        progress=0,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    response = client.put(
        f"/projects/{project.id}",
        json={"name": "Legacy Updated"},
        headers=engineer_headers,
    )
    assert response.status_code == 200
