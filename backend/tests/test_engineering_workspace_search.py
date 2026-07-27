from app.core.security import hash_password
from app.models.customer import Customer
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.project import Project
from app.models.user import User
from app.permissions.roles import Role


def test_workspace_search_is_authorization_filtered(
    client,
    db_session,
    engineer_user,
    engineer_headers,
):
    other = User(
        email="workspace-search-other@example.com",
        username="workspace-search-other",
        full_name="Workspace Search Other",
        role=Role.ENGINEER.value,
        hashed_password=hash_password("correct-password"),
        is_active=True,
    )
    db_session.add(other)
    customer = Customer(name="Workspace Search Customer")
    db_session.add(customer)
    db_session.commit()
    login = client.post(
        "/auth/login",
        data={
            "username": other.username,
            "password": "correct-password",
        },
    )
    other_headers = {
        "Authorization": (
            f"Bearer {login.json()['access_token']}"
        )
    }
    project = client.post(
        "/projects/",
        headers=engineer_headers,
        json={
            "name": "Workspace Search Project",
            "customer_id": customer.id,
            "owner_id": engineer_user.id,
        },
    ).json()
    created = client.post(
        f"/projects/{project['id']}/workspaces",
        headers=engineer_headers,
        json={"discipline": "mechanical"},
    )
    assert created.status_code == 201

    found = client.get(
        "/search/",
        headers=engineer_headers,
        params={"q": "mechanical", "type": "workspace"},
    )
    assert found.status_code == 200
    assert found.json()["total"] == 1
    result = found.json()["results"]["workspaces"][0]
    assert result["title"] == "Mechanical Engineering Workspace"
    assert result["project_code"] == project["project_code"]

    partial_code = client.get(
        "/search/",
        headers=engineer_headers,
        params={
            "q": project["project_code"][-5:],
            "type": "workspace",
        },
    )
    assert partial_code.json()["total"] == 1

    hidden = client.get(
        "/search/",
        headers=other_headers,
        params={"q": "mechanical", "type": "workspace"},
    )
    assert hidden.status_code == 200
    assert hidden.json()["total"] == 0


def test_workspace_search_all_fields_archives_and_authorized_pagination(
    client,
    db_session,
    engineer_user,
    engineer_headers,
):
    owner = User(
        email="search-field-owner@example.com",
        username="search-field-owner",
        full_name="Distinctive Workspace Owner",
        role=Role.ENGINEER.value,
        hashed_password=hash_password("correct-password"),
        is_active=True,
    )
    assignee = User(
        email="search-field-assignee@example.com",
        username="search-field-assignee",
        full_name="Distinctive Primary Assignee",
        role=Role.ENGINEER.value,
        hashed_password=hash_password("correct-password"),
        is_active=True,
    )
    hidden_owner = User(
        email="search-hidden-owner@example.com",
        username="search-hidden-owner",
        full_name="Hidden Common Needle",
        role=Role.ENGINEER.value,
        hashed_password=hash_password("correct-password"),
        is_active=True,
    )
    customer = Customer(name="Search Fields Customer")
    db_session.add_all([owner, assignee, hidden_owner, customer])
    db_session.flush()
    projects = [
        Project(
            project_code=f"SAT-PRJ-2098-{8100 + index}",
            name=name,
            customer_id=customer.id,
            owner_id=project_owner.id,
        )
        for index, (name, project_owner) in enumerate(
            (
                ("Distinctive Project Alpha", engineer_user),
                ("Common Needle Visible One", engineer_user),
                ("Common Needle Visible Two", engineer_user),
                ("Common Needle Hidden", hidden_owner),
                ("Archived Discovery Project", engineer_user),
            )
        )
    ]
    db_session.add_all(projects)
    db_session.flush()
    workspaces = [
        EngineeringWorkspace(
            project_id=projects[0].id,
            discipline="electrical",
            status="under_review",
            owner_id=owner.id,
            primary_assignee_id=assignee.id,
            created_by_id=engineer_user.id,
            version=1,
        ),
        EngineeringWorkspace(
            project_id=projects[1].id,
            discipline="civil",
            status="active",
            owner_id=engineer_user.id,
            created_by_id=engineer_user.id,
            version=1,
        ),
        EngineeringWorkspace(
            project_id=projects[2].id,
            discipline="mechanical",
            status="active",
            owner_id=engineer_user.id,
            created_by_id=engineer_user.id,
            version=1,
        ),
        EngineeringWorkspace(
            project_id=projects[3].id,
            discipline="process",
            status="active",
            owner_id=hidden_owner.id,
            created_by_id=hidden_owner.id,
            version=1,
        ),
        EngineeringWorkspace(
            project_id=projects[4].id,
            discipline="instrumentation",
            status="archived",
            owner_id=engineer_user.id,
            created_by_id=engineer_user.id,
            version=2,
            archived_at=datetime(2098, 1, 1, tzinfo=timezone.utc),
        ),
    ]
    db_session.add_all(workspaces)
    db_session.commit()

    for query in (
        "Distinctive Project Alpha",
        "under_review",
        "Distinctive Workspace Owner",
        "Distinctive Primary Assignee",
    ):
        response = client.get(
            "/search/",
            headers=engineer_headers,
            params={"q": query, "type": "workspace"},
        )
        assert response.status_code == 200
        assert response.json()["total"] == 1
        assert response.json()["results"]["workspaces"][0]["id"] == (
            workspaces[0].id
        )

    archived = client.get(
        "/search/",
        headers=engineer_headers,
        params={"q": "Archived Discovery Project", "type": "workspace"},
    )
    assert archived.status_code == 200
    assert archived.json()["total"] == 0
    assert archived.json()["results"]["workspaces"] == []

    first_page = client.get(
        "/search/",
        headers=engineer_headers,
        params={
            "q": "Common Needle",
            "type": "workspace",
            "page": 1,
            "size": 1,
        },
    ).json()
    second_page = client.get(
        "/search/",
        headers=engineer_headers,
        params={
            "q": "Common Needle",
            "type": "workspace",
            "page": 2,
            "size": 1,
        },
    ).json()
    assert first_page["total"] == second_page["total"] == 2
    returned_ids = {
        first_page["results"]["workspaces"][0]["id"],
        second_page["results"]["workspaces"][0]["id"],
    }
    assert returned_ids == {workspaces[1].id, workspaces[2].id}
    assert workspaces[3].id not in returned_ids
from datetime import datetime, timezone
