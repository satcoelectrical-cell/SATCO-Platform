import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.core.database import engine
from app.models.audit_log import AuditLog
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate


PROJECT_CODE_PATTERN = re.compile(
    r"^SAT-PRJ-\d{4}-\d{4,}$"
)


def create_customer(client, headers, name="Core Customer"):
    response = client.post(
        "/customers/",
        json={"name": name},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_project_core_lifecycle_filters_and_audit(
    client,
    db_session,
    engineer_user,
    engineer_headers,
    admin_headers,
):
    customer_id = create_customer(
        client,
        engineer_headers,
    )
    created = client.post(
        "/projects/",
        json={
            "name": "  Core Project  ",
            "description": "Project core validation",
            "customer_id": customer_id,
            "priority": "high",
            "primary_assignee_id": engineer_user.id,
            "start_date": "2026-08-01",
            "target_completion_date": "2026-08-31",
        },
        headers=engineer_headers,
    )
    assert created.status_code == 200
    project = created.json()
    assert PROJECT_CODE_PATTERN.fullmatch(
        project["project_code"]
    )
    assert project["name"] == "Core Project"
    assert project["status"] == "new"
    assert project["priority"] == "high"
    assert project["progress"] == 0
    assert project["owner"]["id"] == engineer_user.id
    assert project["primary_assignee"]["id"] == engineer_user.id

    detail = client.get(
        f"/projects/{project['id']}",
        headers=engineer_headers,
    )
    assert detail.status_code == 200
    assert detail.json()["project_code"] == project["project_code"]

    listed = client.get(
        "/projects/",
        params={
            "project_code": project["project_code"][4:12],
            "priority": "high",
            "owner_id": engineer_user.id,
            "primary_assignee_id": engineer_user.id,
            "start_date_from": "2026-08-01",
            "target_date_to": "2026-08-31",
            "sort_by": "project_code",
            "order": "asc",
        },
        headers=engineer_headers,
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    in_progress = client.put(
        f"/projects/{project['id']}",
        json={
            "status": "in_progress",
            "progress": 40,
        },
        headers=engineer_headers,
    )
    assert in_progress.status_code == 200
    assert in_progress.json()["progress"] == 40

    completed = client.put(
        f"/projects/{project['id']}",
        json={"status": "completed"},
        headers=engineer_headers,
    )
    assert completed.status_code == 200
    assert completed.json()["progress"] == 100
    assert completed.json()["completed_at"] is not None

    invalid_terminal_transition = client.put(
        f"/projects/{project['id']}",
        json={"status": "in_progress"},
        headers=engineer_headers,
    )
    assert invalid_terminal_transition.status_code == 400

    immutable_code = client.put(
        f"/projects/{project['id']}",
        json={"project_code": "SAT-PRJ-2026-9999"},
        headers=engineer_headers,
    )
    assert immutable_code.status_code == 422

    audits = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.entity == "PROJECT",
            AuditLog.entity_id == project["id"],
        )
        .all()
    )
    assert {audit.action for audit in audits} == {
        "CREATE",
        "UPDATE",
    }
    assert all(
        project["project_code"]
        in str(audit.details)
        for audit in audits
    )
    assert "hashed_password" not in str(
        [audit.details for audit in audits]
    )

    deleted = client.delete(
        f"/projects/{project['id']}",
        headers=admin_headers,
    )
    assert deleted.status_code == 200
    assert deleted.json()["project_code"] == project["project_code"]


def test_project_validation_and_openapi_examples(
    client,
    engineer_headers,
):
    customer_id = create_customer(
        client,
        engineer_headers,
        "Validation Customer",
    )
    invalid_dates = client.post(
        "/projects/",
        json={
            "name": "Invalid Dates",
            "customer_id": customer_id,
            "start_date": "2026-09-02",
            "target_completion_date": "2026-09-01",
        },
        headers=engineer_headers,
    )
    assert invalid_dates.status_code == 400

    null_status = client.put(
        "/projects/999999",
        json={"status": None},
        headers=engineer_headers,
    )
    assert null_status.status_code == 422

    invalid_enum = client.get(
        "/projects/",
        params={"priority": "urgent"},
        headers=engineer_headers,
    )
    assert invalid_enum.status_code == 422

    schema = client.get("/openapi.json").json()
    paths = schema["paths"]
    for path, method in (
        ("/projects/", "post"),
        ("/projects/", "get"),
        ("/projects/{project_id}", "get"),
        ("/projects/{project_id}", "put"),
        ("/projects/{project_id}", "delete"),
    ):
        responses = paths[path][method]["responses"]
        assert "200" in responses
        assert "401" in responses


def test_yearly_sequence_and_concurrent_project_creation():
    with engine.begin() as connection:
        customer_id = connection.execute(
            text(
                "INSERT INTO customers (name) "
                "VALUES ('Concurrency Customer') RETURNING id"
            )
        ).scalar_one()
        starting_2027 = connection.execute(
            text(
                "SELECT COALESCE(last_value, 0) "
                "FROM project_code_sequences WHERE year = 2027"
            )
        ).scalar_one_or_none() or 0
        starting_2028 = connection.execute(
            text(
                "SELECT COALESCE(last_value, 0) "
                "FROM project_code_sequences WHERE year = 2028"
            )
        ).scalar_one_or_none() or 0

    session_factory = sessionmaker(bind=engine)

    def create_one(index):
        with session_factory() as session:
            return ProjectRepository(session).create(
                ProjectCreate(
                    name=f"Concurrent Project {index}",
                    customer_id=customer_id,
                ),
                owner_id=None,
                creation_time=datetime(
                    2027,
                    1,
                    2,
                    tzinfo=timezone.utc,
                ),
            ).project_code

    with ThreadPoolExecutor(max_workers=4) as executor:
        codes = list(executor.map(create_one, range(8)))

    assert len(codes) == len(set(codes))
    assert sorted(
        int(code.rsplit("-", 1)[1])
        for code in codes
    ) == list(range(starting_2027 + 1, starting_2027 + 9))

    with session_factory() as session:
        next_year = ProjectRepository(session).create(
            ProjectCreate(
                name="New Year Project",
                customer_id=customer_id,
            ),
            owner_id=None,
            creation_time=datetime(
                2028,
                1,
                1,
                tzinfo=timezone.utc,
            ),
        )
        assert next_year.project_code == (
            f"SAT-PRJ-2028-{starting_2028 + 1:04d}"
        )

    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM projects WHERE customer_id = :customer_id"),
            {"customer_id": customer_id},
        )
        connection.execute(
            text("DELETE FROM customers WHERE id = :customer_id"),
            {"customer_id": customer_id},
        )
