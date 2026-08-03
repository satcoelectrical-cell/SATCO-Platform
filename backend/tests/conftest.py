import os
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID, uuid4

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import event, inspect
from sqlalchemy import text
from sqlalchemy.orm import Session as SqlAlchemySession, sessionmaker
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory


TEST_DATABASE_NAME = "satco_platform_patch02022_test"
test_database_url = os.getenv("TEST_DATABASE_URL", "")
parsed_database_url = urlparse(test_database_url)

if parsed_database_url.path.lstrip("/") != TEST_DATABASE_NAME:
    raise RuntimeError(
        "PATCH-020.2.2 tests require TEST_DATABASE_URL to target "
        f"{TEST_DATABASE_NAME}"
    )

os.environ["DATABASE_HOST"] = parsed_database_url.hostname or "postgres"
os.environ["DATABASE_PORT"] = str(parsed_database_url.port or 5432)
os.environ["DATABASE_USER"] = parsed_database_url.username or "satco"
os.environ["DATABASE_PASSWORD"] = (
    parsed_database_url.password or "satco_password"
)
os.environ["DATABASE_NAME"] = TEST_DATABASE_NAME
os.environ["ALEMBIC_DATABASE_URL"] = test_database_url

backend_root = Path(__file__).resolve().parents[1]
alembic_config = Config(str(backend_root / "alembic.ini"))
alembic_config.set_main_option("script_location", str(backend_root / "migrations"))
TEST_DATABASE_REVISION = ScriptDirectory.from_config(
    alembic_config
).get_current_head()

from app.core.database import engine, get_db  # noqa: E402


with engine.connect() as identity_connection:
    actual_database_name = identity_connection.execute(
        text("SELECT current_database()")
    ).scalar_one()
if actual_database_name != TEST_DATABASE_NAME:
    raise RuntimeError(
        "PATCH-020.2.2 database guard rejected "
        f"{actual_database_name}"
    )

if inspect(engine).has_table("alembic_version"):
    with engine.connect() as schema_connection:
        migrated_revision = schema_connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one_or_none()
else:
    migrated_revision = None

if migrated_revision != TEST_DATABASE_REVISION:
    command.upgrade(alembic_config, "head")
    with engine.connect() as schema_connection:
        migrated_revision = schema_connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()
    if migrated_revision != TEST_DATABASE_REVISION:
        raise RuntimeError(
            "Test database bootstrap did not reach repository head "
            f"{TEST_DATABASE_REVISION}"
        )


from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models.audit_log import AuditLog  # noqa: E402,F401
from app.models.contact import Contact  # noqa: E402,F401
from app.models.customer import Customer  # noqa: E402,F401
from app.models.engineering_workspace import (  # noqa: E402,F401
    EngineeringWorkspace,
    EngineeringWorkspaceMember,
)
from app.models.engineering_context import (  # noqa: E402,F401
    EngineeringContext,
    EngineeringContextAssumption,
    EngineeringContextFact,
    EngineeringContextSourceReference,
    EngineeringContextSubjectReference,
    EngineeringContextValue,
)
from app.models.engineering_context_relationship import (  # noqa: E402,F401
    EngineeringContextRelationship,
    InterfaceCommitment,
)
from app.models.project import (  # noqa: E402,F401
    Project,
    ProjectCodeSequence,
)
from app.models.user import User  # noqa: E402
from app.models.organization import (  # noqa: E402
    Organization,
    UserOrganizationMembership,
)
from app.permissions.roles import Role  # noqa: E402
from app.dependencies.auth import (  # noqa: E402
    AuthenticatedOrganizationContext,
    get_current_user,
    get_current_user_organization_context,
)
from app.services.engineering_context_relationship_service import (  # noqa: E402
    EngineeringContextRelationshipService,
)


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
        test_organization_id = UUID(
            "02810000-0000-4000-8000-000000000001"
        )
        connection.execute(
            text(
                "INSERT INTO organizations (id, is_active) "
                "VALUES (:organization_id, true) "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {"organization_id": test_organization_id},
        )
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

    def override_organization_context(
        current_user: User = Depends(get_current_user),
    ):
        return AuthenticatedOrganizationContext(
            user=current_user,
            organization_id=UUID(
                "02810000-0000-4000-8000-000000000001"
            ),
        )

    app.dependency_overrides[
        get_current_user_organization_context
    ] = override_organization_context

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@event.listens_for(SqlAlchemySession, "before_flush")
def assign_test_project_organization(session, flush_context, instances):
    organization_id = UUID("02810000-0000-4000-8000-000000000001")
    for record in session.new:
        if isinstance(record, Project) and record.organization_id is None:
            record.organization_id = organization_id


@event.listens_for(User, "after_insert")
def assign_test_user_membership(mapper, connection, target):
    connection.execute(
        text(
            """
            INSERT INTO user_organization_memberships (
                user_id, organization_id, is_enabled, is_selected
            ) VALUES (
                :user_id, :organization_id, true, true
            )
            ON CONFLICT (user_id, organization_id) DO NOTHING
            """
        ),
        {
            "user_id": target.id,
            "organization_id": UUID(
                "02810000-0000-4000-8000-000000000001"
            ),
        },
    )


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
    db_session.flush()
    test_organization_id = UUID("02810000-0000-4000-8000-000000000001")
    organization = db_session.get(Organization, test_organization_id)
    if organization is None:
        organization = Organization(
            id=test_organization_id,
            is_active=True,
        )
        db_session.add(organization)
        db_session.flush()
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


@pytest.fixture
def relationship_domain(db_session):
    suffix = uuid4().hex[:8]

    def user(label, role=Role.ENGINEER, active=True):
        record = User(
            email=f"{label}-{suffix}@example.com",
            username=f"{label}-{suffix}",
            hashed_password="not-used",
            role=role.value,
            is_active=active,
        )
        db_session.add(record)
        db_session.flush()
        return record

    actors = {
        "admin": user("admin", Role.ADMIN),
        "project_owner": user("project-owner"),
        "provider": user("provider"),
        "consumer": user("consumer"),
        "steward": user("steward"),
        "unrelated": user("unrelated"),
        "inactive": user("inactive", active=False),
    }
    customer = Customer(name=f"Relationship Customer {suffix}")
    other_customer = Customer(name=f"Other Customer {suffix}")
    db_session.add_all([customer, other_customer])
    db_session.flush()
    project = Project(
        project_code=f"SAT-PRJ-2097-{customer.id + 1000:04d}",
        name="Relationship Project",
        customer_id=customer.id,
        owner_id=actors["project_owner"].id,
    )
    other_project = Project(
        project_code=f"SAT-PRJ-2096-{other_customer.id + 2000:04d}",
        name="Other Project",
        customer_id=other_customer.id,
        owner_id=actors["unrelated"].id,
    )
    db_session.add_all([project, other_project])
    db_session.flush()
    provider_workspace = EngineeringWorkspace(
        project_id=project.id,
        discipline="mechanical",
        status="active",
        owner_id=actors["provider"].id,
        created_by_id=actors["project_owner"].id,
        version=1,
    )
    consumer_workspace = EngineeringWorkspace(
        project_id=project.id,
        discipline="electrical",
        status="active",
        owner_id=actors["consumer"].id,
        created_by_id=actors["project_owner"].id,
        version=1,
    )
    unrelated_workspace = EngineeringWorkspace(
        project_id=project.id,
        discipline="civil",
        status="active",
        owner_id=actors["unrelated"].id,
        created_by_id=actors["project_owner"].id,
        version=1,
    )
    other_workspace = EngineeringWorkspace(
        project_id=other_project.id,
        discipline="instrumentation",
        status="active",
        owner_id=actors["unrelated"].id,
        created_by_id=actors["unrelated"].id,
        version=1,
    )
    db_session.add_all(
        [
            provider_workspace,
            consumer_workspace,
            unrelated_workspace,
            other_workspace,
        ]
    )
    db_session.flush()
    service = EngineeringContextRelationshipService(db_session)
    return {
        "actors": actors,
        "project": project,
        "other_project": other_project,
        "provider_workspace": provider_workspace,
        "consumer_workspace": consumer_workspace,
        "unrelated_workspace": unrelated_workspace,
        "other_workspace": other_workspace,
        "service": service,
    }
