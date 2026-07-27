from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.user import User
from app.core.security import hash_password
from app.permissions.roles import Role


def test_workspace_mutations_create_centralized_audit_events(
    client,
    db_session,
    engineer_user,
    engineer_headers,
):
    customer = Customer(name="Workspace Audit Customer")
    db_session.add(customer)
    new_owner = User(
        email="workspace-owner@example.com",
        username="workspace-owner",
        role=Role.ENGINEER.value,
        hashed_password=hash_password("correct-password"),
        is_active=True,
    )
    assignee = User(
        email="workspace-assignee@example.com",
        username="workspace-assignee",
        role=Role.ENGINEER.value,
        hashed_password=hash_password("correct-password"),
        is_active=True,
    )
    collaborator = User(
        email="workspace-reviewer@example.com",
        username="workspace-reviewer",
        role=Role.ENGINEER.value,
        hashed_password=hash_password("correct-password"),
        is_active=True,
    )
    db_session.add_all([new_owner, assignee, collaborator])
    db_session.commit()
    project = client.post(
        "/projects/",
        headers=engineer_headers,
        json={
            "name": "Workspace Audit Project",
            "customer_id": customer.id,
            "owner_id": engineer_user.id,
        },
    ).json()
    created = client.post(
        f"/projects/{project['id']}/workspaces",
        headers=engineer_headers,
        json={"discipline": "process"},
    ).json()
    updated = client.patch(
        f"/workspaces/{created['id']}",
        headers=engineer_headers,
        json={
            "description": "Process discipline scope.",
            "expected_version": 1,
        },
    )
    assert updated.status_code == 200
    owner_changed = client.patch(
        f"/workspaces/{created['id']}",
        headers=engineer_headers,
        json={
            "owner_id": new_owner.id,
            "expected_version": 2,
        },
    )
    assert owner_changed.status_code == 200
    assignee_changed = client.patch(
        f"/workspaces/{created['id']}",
        headers=engineer_headers,
        json={
            "primary_assignee_id": assignee.id,
            "expected_version": 3,
        },
    )
    assert assignee_changed.status_code == 200
    added = client.post(
        f"/workspaces/{created['id']}/collaborators",
        headers=engineer_headers,
        json={
            "user_id": collaborator.id,
            "expected_version": 4,
        },
    )
    assert added.status_code == 200
    removed = client.delete(
        (
            f"/workspaces/{created['id']}/collaborators/"
            f"{collaborator.id}"
        ),
        headers=engineer_headers,
        params={"expected_version": 5},
    )
    assert removed.status_code == 204
    transitioned = client.post(
        f"/workspaces/{created['id']}/transitions",
        headers=engineer_headers,
        json={"status": "active", "expected_version": 6},
    )
    assert transitioned.status_code == 200
    archived = client.post(
        f"/workspaces/{created['id']}/archive",
        headers=engineer_headers,
        json={"reason": "Audit archive", "expected_version": 7},
    )
    assert archived.status_code == 200
    restored = client.post(
        f"/workspaces/{created['id']}/restore",
        headers=engineer_headers,
        json={"reason": "Audit restore", "expected_version": 8},
    )
    assert restored.status_code == 200

    rows = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.entity == "ENGINEERING_WORKSPACE",
            AuditLog.entity_id == created["id"],
        )
        .all()
    )
    assert {row.action for row in rows} == {
        "workspace_created",
        "workspace_updated",
        "workspace_owner_changed",
        "workspace_primary_assignee_changed",
        "workspace_collaborator_added",
        "workspace_collaborator_removed",
        "workspace_status_changed",
        "workspace_archived",
        "workspace_restored",
    }
    assert all(row.user_id == engineer_user.id for row in rows)
    assert all(
        row.details["project_id"] == project["id"]
        for row in rows
    )
    assert all("version" in row.details for row in rows)


def test_failed_mutations_create_no_audit_records(
    client,
    db_session,
    engineer_user,
    engineer_headers,
):
    customer = Customer(name="Failed Workspace Audit Customer")
    db_session.add(customer)
    invalid_user = User(
        email="failed-audit-inactive@example.com",
        username="failed-audit-inactive",
        role=Role.ENGINEER.value,
        hashed_password=hash_password("correct-password"),
        is_active=False,
    )
    db_session.add(invalid_user)
    db_session.commit()
    project = client.post(
        "/projects/",
        headers=engineer_headers,
        json={
            "name": "Failed Workspace Audit Project",
            "customer_id": customer.id,
            "owner_id": engineer_user.id,
        },
    ).json()
    workspace = client.post(
        f"/projects/{project['id']}/workspaces",
        headers=engineer_headers,
        json={"discipline": "process"},
    ).json()

    def audit_count():
        return (
            db_session.query(AuditLog)
            .filter(
                AuditLog.entity == "ENGINEERING_WORKSPACE",
                AuditLog.entity_id == workspace["id"],
            )
            .count()
        )

    baseline = audit_count()
    invalid_assignment = client.patch(
        f"/workspaces/{workspace['id']}",
        headers=engineer_headers,
        json={
            "owner_id": invalid_user.id,
            "expected_version": 1,
        },
    )
    assert invalid_assignment.status_code == 422
    assert audit_count() == baseline

    first_update = client.patch(
        f"/workspaces/{workspace['id']}",
        headers=engineer_headers,
        json={"description": "Committed", "expected_version": 1},
    )
    assert first_update.status_code == 200
    after_success = audit_count()
    assert after_success == baseline + 1

    concurrency_conflict = client.patch(
        f"/workspaces/{workspace['id']}",
        headers=engineer_headers,
        json={"description": "Stale", "expected_version": 1},
    )
    assert concurrency_conflict.status_code == 409
    assert audit_count() == after_success

    rejected_transition = client.post(
        f"/workspaces/{workspace['id']}/transitions",
        headers=engineer_headers,
        json={"status": "completed", "expected_version": 2},
    )
    assert rejected_transition.status_code == 409
    assert audit_count() == after_success
