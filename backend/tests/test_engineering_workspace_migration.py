from datetime import datetime, timezone

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.core.database import engine
from app.models.customer import Customer
from app.models.engineering_workspace import (
    EngineeringWorkspace,
    EngineeringWorkspaceMember,
)
from app.models.project import Project


def test_engineering_workspace_database_contract():
    inspector = inspect(engine)
    assert {
        "engineering_workspaces",
        "engineering_workspace_members",
    } <= set(inspector.get_table_names())

    columns = {
        column["name"]: column
        for column in inspector.get_columns(
            "engineering_workspaces"
        )
    }
    assert {
        "id",
        "project_id",
        "discipline",
        "description",
        "status",
        "owner_id",
        "primary_assignee_id",
        "created_by_id",
        "version",
        "archived_at",
        "created_at",
        "updated_at",
    } == set(columns)
    for required in (
        "project_id",
        "discipline",
        "status",
        "owner_id",
        "created_by_id",
        "version",
        "created_at",
        "updated_at",
    ):
        assert columns[required]["nullable"] is False

    unique_names = {
        item["name"]
        for item in inspector.get_unique_constraints(
            "engineering_workspaces"
        )
    }
    assert (
        "uq_engineering_workspaces_project_discipline"
        in unique_names
    )
    check_names = {
        item["name"]
        for item in inspector.get_check_constraints(
            "engineering_workspaces"
        )
    }
    assert {
        "ck_engineering_workspaces_discipline",
        "ck_engineering_workspaces_status",
        "ck_engineering_workspaces_version",
        "ck_engineering_workspaces_archive_state",
    } <= check_names

    foreign_key_names = {
        item["name"]
        for item in inspector.get_foreign_keys(
            "engineering_workspaces"
        )
    }
    assert {
        "fk_engineering_workspaces_project_id_projects",
        "fk_engineering_workspaces_owner_id_users",
        "fk_engineering_workspaces_primary_assignee_id_users",
        "fk_engineering_workspaces_created_by_id_users",
    } <= foreign_key_names

    index_names = {
        item["name"]
        for item in inspector.get_indexes(
            "engineering_workspaces"
        )
    }
    assert {
        "ix_engineering_workspaces_project_status",
        "ix_engineering_workspaces_owner_id",
        "ix_engineering_workspaces_primary_assignee_id",
        "ix_engineering_workspaces_status",
        "ix_engineering_workspaces_updated_at",
    } <= index_names

    member_pk = inspector.get_pk_constraint(
        "engineering_workspace_members"
    )
    assert member_pk["constrained_columns"] == [
        "workspace_id",
        "user_id",
    ]
    member_foreign_keys = {
        item["name"]
        for item in inspector.get_foreign_keys(
            "engineering_workspace_members"
        )
    }
    assert {
        "fk_ew_members_workspace_id_workspaces",
        "fk_engineering_workspace_members_user_id_users",
        "fk_engineering_workspace_members_added_by_id_users",
    } <= member_foreign_keys

    with engine.connect() as connection:
        revision = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()
    assert revision != "f18a1c0e2026"


@pytest.mark.parametrize(
    "invalid_values",
    [
        {"discipline": "software"},
        {"status": "ready"},
        {"version": 0},
        {
            "status": "archived",
            "archived_at": None,
        },
        {
            "status": "active",
            "archived_at": datetime.now(timezone.utc),
        },
    ],
    ids=[
        "invalid-discipline",
        "invalid-status",
        "non-positive-version",
        "archived-without-timestamp",
        "timestamp-without-archived-status",
    ],
)
def test_postgresql_rejects_invalid_workspace_constraints(
    db_session,
    engineer_user,
    invalid_values,
):
    customer = Customer(name="Direct Constraint Customer")
    db_session.add(customer)
    db_session.flush()
    project = Project(
        project_code="SAT-PRJ-2097-9001",
        name="Direct Constraint Project",
        customer_id=customer.id,
        owner_id=engineer_user.id,
    )
    db_session.add(project)
    db_session.flush()
    values = {
        "project_id": project.id,
        "discipline": "electrical",
        "status": "draft",
        "owner_id": engineer_user.id,
        "created_by_id": engineer_user.id,
        "version": 1,
        **invalid_values,
    }

    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(EngineeringWorkspace(**values))
            db_session.flush()


def test_postgresql_rejects_duplicate_workspace_and_membership(
    db_session,
    engineer_user,
):
    customer = Customer(name="Direct Uniqueness Customer")
    db_session.add(customer)
    db_session.flush()
    project = Project(
        project_code="SAT-PRJ-2097-9002",
        name="Direct Uniqueness Project",
        customer_id=customer.id,
        owner_id=engineer_user.id,
    )
    db_session.add(project)
    db_session.flush()
    workspace = EngineeringWorkspace(
        project_id=project.id,
        discipline="civil",
        status="draft",
        owner_id=engineer_user.id,
        created_by_id=engineer_user.id,
        version=1,
    )
    db_session.add(workspace)
    db_session.flush()
    member = EngineeringWorkspaceMember(
        workspace_id=workspace.id,
        user_id=engineer_user.id,
        added_by_id=engineer_user.id,
    )
    db_session.add(member)
    db_session.flush()

    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(
                EngineeringWorkspace(
                    project_id=project.id,
                    discipline="civil",
                    status="draft",
                    owner_id=engineer_user.id,
                    created_by_id=engineer_user.id,
                    version=1,
                )
            )
            db_session.flush()

    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.execute(
                text(
                    "INSERT INTO engineering_workspace_members "
                    "(workspace_id, user_id, added_by_id) "
                    "VALUES (:workspace_id, :user_id, :added_by_id)"
                ),
                {
                    "workspace_id": workspace.id,
                    "user_id": engineer_user.id,
                    "added_by_id": engineer_user.id,
                },
            )
            db_session.flush()
