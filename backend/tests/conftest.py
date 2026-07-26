import os
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker


TEST_DATABASE_NAME = "satco_platform_patch019_test"
test_database_url = os.getenv("TEST_DATABASE_URL", "")
parsed_database_url = urlparse(test_database_url)

if parsed_database_url.path.lstrip("/") != TEST_DATABASE_NAME:
    raise RuntimeError(
        "PATCH-019 tests require TEST_DATABASE_URL to target "
        f"{TEST_DATABASE_NAME}"
    )

os.environ["DATABASE_HOST"] = parsed_database_url.hostname or "postgres"
os.environ["DATABASE_PORT"] = str(parsed_database_url.port or 5432)
os.environ["DATABASE_USER"] = parsed_database_url.username or "satco"
os.environ["DATABASE_PASSWORD"] = (
    parsed_database_url.password or "satco_password"
)
os.environ["DATABASE_NAME"] = TEST_DATABASE_NAME

from app.core.database import engine, get_db  # noqa: E402


if inspect(engine).has_table("alembic_version"):
    with engine.connect() as schema_connection:
        migrated_revision = schema_connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one_or_none()
else:
    migrated_revision = None

if migrated_revision != "f18a1c0e2026":
    raise RuntimeError(
        "PATCH-019 tests require an Alembic-migrated database at "
        "revision f18a1c0e2026"
    )


from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models.audit_log import AuditLog  # noqa: E402,F401
from app.models.contact import Contact  # noqa: E402,F401
from app.models.customer import Customer  # noqa: E402,F401
from app.models.project import (  # noqa: E402,F401
    Project,
    ProjectCodeSequence,
)
from app.models.user import User  # noqa: E402
from app.permissions.roles import Role  # noqa: E402


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    testing_session = sessionmaker(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    session = testing_session()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def create_user(
    db_session,
    *,
    username: str,
    role: Role,
    is_active: bool = True,
):
    user = User(
        email=f"{username}@example.com",
        username=username,
        full_name=username.title(),
        role=role.value,
        hashed_password=hash_password("correct-password"),
        is_active=is_active,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def engineer_user(db_session):
    return create_user(
        db_session,
        username="engineer",
        role=Role.ENGINEER,
    )


@pytest.fixture
def admin_user(db_session):
    return create_user(
        db_session,
        username="admin",
        role=Role.ADMIN,
    )


def login_headers(client, username: str):
    response = client.post(
        "/auth/login",
        data={
            "username": username,
            "password": "correct-password",
        },
    )
    assert response.status_code == 200
    access_token = response.json()["access_token"]
    return {
        "Authorization": f"Bearer {access_token}",
    }


@pytest.fixture
def engineer_headers(client, engineer_user):
    return login_headers(client, engineer_user.username)


@pytest.fixture
def admin_headers(client, admin_user):
    return login_headers(client, admin_user.username)
