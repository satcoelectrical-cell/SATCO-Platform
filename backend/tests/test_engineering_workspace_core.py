from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.core.database import engine
from app.enums import Discipline, WorkspaceStatus
from app.models.customer import Customer
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.project import Project
from app.repositories.engineering_workspace_repository import (
    EngineeringWorkspaceRepository,
)


def _create_project(client, db_session, headers, owner):
    customer = Customer(name="Workspace Core Customer")
    db_session.add(customer)
    db_session.commit()
    response = client.post(
        "/projects/",
        headers=headers,
        json={
            "name": "Workspace Core Project",
            "customer_id": customer.id,
            "owner_id": owner.id,
        },
    )
    assert response.status_code == 200
    return response.json()


def test_workspace_create_lifecycle_archive_restore_and_version(
    client,
    db_session,
    engineer_user,
    engineer_headers,
):
    project = _create_project(
        client,
        db_session,
        engineer_headers,
        engineer_user,
    )
    created = client.post(
        f"/projects/{project['id']}/workspaces",
        headers=engineer_headers,
        json={
            "discipline": "electrical",
            "description": "Electrical engineering scope.",
        },
    )
    assert created.status_code == 201
    workspace = created.json()
    assert workspace["display_name"] == (
        "Electrical Engineering Workspace"
    )
    assert workspace["status"] == "draft"
    assert workspace["version"] == 1
    assert workspace["owner"]["id"] == engineer_user.id

    duplicate = client.post(
        f"/projects/{project['id']}/workspaces",
        headers=engineer_headers,
        json={"discipline": "electrical"},
    )
    assert duplicate.status_code == 409

    activated = client.post(
        f"/workspaces/{workspace['id']}/transitions",
        headers=engineer_headers,
        json={"status": "active", "expected_version": 1},
    )
    assert activated.status_code == 200
    assert activated.json()["version"] == 2

    stale = client.patch(
        f"/workspaces/{workspace['id']}",
        headers=engineer_headers,
        json={
            "description": "Stale update",
            "expected_version": 1,
        },
    )
    assert stale.status_code == 409

    archived = client.post(
        f"/workspaces/{workspace['id']}/archive",
        headers=engineer_headers,
        json={
            "reason": "Discipline scope paused.",
            "expected_version": 2,
        },
    )
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"
    assert archived.json()["archived_at"] is not None

    restored = client.post(
        f"/workspaces/{workspace['id']}/restore",
        headers=engineer_headers,
        json={
            "reason": "Discipline scope resumed.",
            "expected_version": 3,
        },
    )
    assert restored.status_code == 200
    assert restored.json()["id"] == workspace["id"]
    assert restored.json()["status"] == "active"
    assert restored.json()["archived_at"] is None


def test_workspace_validation_listing_and_openapi_examples(
    client,
    db_session,
    engineer_user,
    engineer_headers,
):
    project = _create_project(
        client,
        db_session,
        engineer_headers,
        engineer_user,
    )
    invalid = client.post(
        f"/projects/{project['id']}/workspaces",
        headers=engineer_headers,
        json={"discipline": "software"},
    )
    assert invalid.status_code == 422

    created = client.post(
        f"/projects/{project['id']}/workspaces",
        headers=engineer_headers,
        json={"discipline": "instrumentation"},
    )
    assert created.status_code == 201

    listed = client.get(
        f"/projects/{project['id']}/workspaces",
        headers=engineer_headers,
        params={"discipline": "instrumentation"},
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    schema = client.get("/openapi.json").json()
    expected_paths = {
        "/projects/{project_id}/workspaces",
        "/workspaces/{workspace_id}",
        "/workspaces/{workspace_id}/transitions",
        "/workspaces/{workspace_id}/archive",
        "/workspaces/{workspace_id}/restore",
        "/workspaces/{workspace_id}/collaborators",
        "/workspaces/{workspace_id}/collaborators/{user_id}",
    }
    assert expected_paths <= set(schema["paths"])
    for path in expected_paths:
        for operation in schema["paths"][path].values():
            responses = operation["responses"]
            assert {
                "401",
                "403",
                "404",
                "409",
                "422",
            } <= set(responses)


def test_project_deletion_is_blocked_after_workspace_history(
    client,
    db_session,
    engineer_user,
    engineer_headers,
    admin_headers,
):
    project = _create_project(
        client,
        db_session,
        engineer_headers,
        engineer_user,
    )
    created = client.post(
        f"/projects/{project['id']}/workspaces",
        headers=engineer_headers,
        json={"discipline": "civil"},
    )
    assert created.status_code == 201

    blocked = client.delete(
        f"/projects/{project['id']}",
        headers=admin_headers,
    )
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == (
        "PROJECT_HAS_WORKSPACE_HISTORY"
    )
    assert (
        db_session.query(EngineeringWorkspace)
        .filter(
            EngineeringWorkspace.project_id == project["id"]
        )
        .count()
        == 1
    )


@pytest.mark.parametrize(
    ("source", "target"),
    [
        ("draft", "active"),
        ("active", "on_hold"),
        ("active", "under_review"),
        ("on_hold", "active"),
        ("under_review", "active"),
        ("under_review", "completed"),
        ("completed", "active"),
    ],
)
def test_complete_permitted_workspace_transition_matrix(
    client,
    db_session,
    engineer_user,
    engineer_headers,
    source,
    target,
):
    project = _create_project(
        client, db_session, engineer_headers, engineer_user
    )
    workspace = EngineeringWorkspace(
        project_id=project["id"],
        discipline="electrical",
        status=source,
        owner_id=engineer_user.id,
        created_by_id=engineer_user.id,
        version=1,
    )
    db_session.add(workspace)
    db_session.commit()

    response = client.post(
        f"/workspaces/{workspace.id}/transitions",
        headers=engineer_headers,
        json={
            "status": target,
            "expected_version": 1,
            "reason": "Required when reopening",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == target
    assert response.json()["version"] == 2


@pytest.mark.parametrize(
    ("source", "target"),
    [
        (source, target)
        for source in (
            "draft",
            "active",
            "on_hold",
            "under_review",
            "completed",
        )
        for target in (
            "draft",
            "active",
            "on_hold",
            "under_review",
            "completed",
        )
        if source != target
        and (source, target)
        not in {
            ("draft", "active"),
            ("active", "on_hold"),
            ("active", "under_review"),
            ("on_hold", "active"),
            ("under_review", "active"),
            ("under_review", "completed"),
            ("completed", "active"),
        }
    ],
)
def test_complete_prohibited_workspace_transition_matrix(
    client,
    db_session,
    engineer_user,
    engineer_headers,
    source,
    target,
):
    project = _create_project(
        client, db_session, engineer_headers, engineer_user
    )
    workspace = EngineeringWorkspace(
        project_id=project["id"],
        discipline="electrical",
        status=source,
        owner_id=engineer_user.id,
        created_by_id=engineer_user.id,
        version=1,
    )
    db_session.add(workspace)
    db_session.commit()

    response = client.post(
        f"/workspaces/{workspace.id}/transitions",
        headers=engineer_headers,
        json={"status": target, "expected_version": 1},
    )

    assert response.status_code == 409
    db_session.refresh(workspace)
    assert workspace.status == source
    assert workspace.version == 1


def test_archive_restore_and_self_transition_complete_the_matrix(
    client,
    db_session,
    engineer_user,
    engineer_headers,
):
    for index, source in enumerate(
        ("draft", "active", "on_hold", "under_review", "completed")
    ):
        project = _create_project(
            client, db_session, engineer_headers, engineer_user
        )
        workspace = EngineeringWorkspace(
            project_id=project["id"],
            discipline=list(Discipline)[index].value,
            status=source,
            owner_id=engineer_user.id,
            created_by_id=engineer_user.id,
            version=1,
        )
        db_session.add(workspace)
        db_session.commit()
        same = client.post(
            f"/workspaces/{workspace.id}/transitions",
            headers=engineer_headers,
            json={"status": source, "expected_version": 1},
        )
        assert same.status_code == 200
        assert same.json()["version"] == 1
        archived = client.post(
            f"/workspaces/{workspace.id}/archive",
            headers=engineer_headers,
            json={"reason": "Matrix archive", "expected_version": 1},
        )
        assert archived.status_code == 200
        rejected = client.post(
            f"/workspaces/{workspace.id}/transitions",
            headers=engineer_headers,
            json={"status": "on_hold", "expected_version": 2},
        )
        assert rejected.status_code == 409
        restored = client.post(
            f"/workspaces/{workspace.id}/restore",
            headers=engineer_headers,
            json={"reason": "Matrix restore", "expected_version": 2},
        )
        assert restored.status_code == 200
        assert restored.json()["status"] == "active"


def test_repository_filters_sorting_pagination_archives_and_project_scope(
    db_session,
    engineer_user,
):
    customer = Customer(name="Workspace Repository Customer")
    db_session.add(customer)
    db_session.flush()
    projects = [
        Project(
            project_code=f"SAT-PRJ-2099-{9000 + index}",
            name=f"Repository Project {index}",
            customer_id=customer.id,
            owner_id=engineer_user.id,
        )
        for index in (1, 2)
    ]
    db_session.add_all(projects)
    db_session.flush()
    rows = [
        EngineeringWorkspace(
            project_id=projects[0].id,
            discipline="civil",
            status="active",
            owner_id=engineer_user.id,
            primary_assignee_id=engineer_user.id,
            created_by_id=engineer_user.id,
            version=1,
        ),
        EngineeringWorkspace(
            project_id=projects[0].id,
            discipline="electrical",
            status="draft",
            owner_id=engineer_user.id,
            created_by_id=engineer_user.id,
            version=1,
        ),
        EngineeringWorkspace(
            project_id=projects[0].id,
            discipline="mechanical",
            status="archived",
            archived_at=datetime.now(timezone.utc),
            owner_id=engineer_user.id,
            created_by_id=engineer_user.id,
            version=2,
        ),
        EngineeringWorkspace(
            project_id=projects[1].id,
            discipline="process",
            status="active",
            owner_id=engineer_user.id,
            created_by_id=engineer_user.id,
            version=1,
        ),
    ]
    db_session.add_all(rows)
    db_session.commit()
    repository = EngineeringWorkspaceRepository(db_session)

    common = {
        "project_id": projects[0].id,
        "current_user": engineer_user,
        "page": 1,
        "size": 20,
        "discipline": None,
        "status": None,
        "owner_id": None,
        "primary_assignee_id": None,
        "include_archived": False,
        "sort_by": "discipline",
        "order": "asc",
    }
    items, total = repository.list_for_project(**common)
    assert total == 2
    assert [item.discipline for item in items] == ["civil", "electrical"]
    page, page_total = repository.list_for_project(
        **{**common, "page": 2, "size": 1}
    )
    assert page_total == 2
    assert [item.discipline for item in page] == ["electrical"]
    archived, archived_total = repository.list_for_project(
        **{**common, "include_archived": True, "order": "desc"}
    )
    assert archived_total == 3
    assert [item.discipline for item in archived] == [
        "mechanical",
        "electrical",
        "civil",
    ]
    filtered, filtered_total = repository.list_for_project(
        **{
            **common,
            "status": WorkspaceStatus.ACTIVE,
            "discipline": Discipline.CIVIL,
            "owner_id": engineer_user.id,
            "primary_assignee_id": engineer_user.id,
        }
    )
    assert filtered_total == 1
    assert [item.id for item in filtered] == [rows[0].id]
    assert all(item.project_id == projects[0].id for item in archived)


def test_concurrent_workspace_uniqueness_for_project_and_discipline():
    token = uuid4().hex[:12]
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    setup = Session()
    barrier = Barrier(2)
    try:
        from app.core.security import hash_password
        from app.models.user import User

        user = User(
            email=f"concurrent-{token}@example.com",
            username=f"concurrent-{token}",
            role="engineer",
            hashed_password=hash_password("correct-password"),
            is_active=True,
        )
        customer = Customer(name=f"Concurrent Customer {token}")
        setup.add_all([user, customer])
        setup.flush()
        code_suffix = str(uuid4().int % 100000000).zfill(8)
        project = Project(
            project_code=f"SAT-PRJ-2099-{code_suffix}",
            name=f"Concurrent Project {token}",
            customer_id=customer.id,
            owner_id=user.id,
        )
        setup.add(project)
        setup.commit()

        def create_workspace():
            session = Session()
            try:
                workspace = EngineeringWorkspace(
                    project_id=project.id,
                    discipline="control",
                    status="draft",
                    owner_id=user.id,
                    created_by_id=user.id,
                    version=1,
                )
                session.add(workspace)
                barrier.wait()
                session.commit()
                return "created"
            except IntegrityError:
                session.rollback()
                return "conflict"
            finally:
                session.close()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(
                executor.map(lambda _: create_workspace(), range(2))
            )
        assert sorted(results) == ["conflict", "created"]
        assert (
            setup.query(EngineeringWorkspace)
            .filter_by(project_id=project.id, discipline="control")
            .count()
            == 1
        )
    finally:
        setup.rollback()
        if "project" in locals():
            setup.query(EngineeringWorkspace).filter_by(
                project_id=project.id
            ).delete()
            setup.delete(project)
            setup.delete(customer)
            setup.delete(user)
            setup.commit()
        setup.close()
