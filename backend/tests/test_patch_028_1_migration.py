from pathlib import Path

from alembic import command
from sqlalchemy import inspect, text

from app.core.database import engine
from conftest import alembic_config


MIGRATION = Path(
    "migrations/versions/e02810000001_project_organization_ownership.py"
)
PERSISTENT_TEST_ORGANIZATION_ID = "02810000-0000-4000-8000-000000000001"


def _restore_shared_test_state():
    try:
        command.downgrade(alembic_config, "e02600000001")
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    TRUNCATE TABLE
                        projects,
                        customers,
                        users,
                        organizations,
                        user_organization_memberships
                    RESTART IDENTITY CASCADE
                    """
                )
            )
    finally:
        command.upgrade(alembic_config, "head")
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO organizations (id, is_active)
                    VALUES (:organization_id, true)
                    ON CONFLICT (id) DO UPDATE SET is_active = true
                    """
                ),
                {"organization_id": PERSISTENT_TEST_ORGANIZATION_ID},
            )


def test_patch_028_1_revision_and_non_destructive_contract():
    source = MIGRATION.read_text()

    assert 'revision: str = "e02810000001"' in source
    assert 'down_revision: str | None = "e02600000001"' in source
    assert "op.add_column(" in source
    assert '"organization_id"' in source
    assert "op.drop_column" in source
    assert "DELETE FROM projects" not in source.upper()
    assert "TRUNCATE" not in source.upper()
    assert "DROP TABLE" not in source.upper()


def test_patch_028_1_uses_approved_bootstrap_identities():
    source = MIGRATION.read_text()

    assert "7e7c9d7a-7693-4f75-9bc5-3ef7bf528281" in source
    assert 'BOOTSTRAP_USER_EMAIL = "admin@satco.com"' in source
    assert 'BOOTSTRAP_USER_ROLE = "admin"' in source
    assert "engineer@satco.com" in source
    assert "INSERT INTO users" not in source.upper()
    assert "UPDATE users" not in source.upper()


def test_patch_028_1_contains_preservation_and_abort_guards():
    source = MIGRATION.read_text()

    for required in (
        "LOCK TABLE projects",
        "Project count changed",
        "Project identities changed",
        "Pre-existing Project values changed",
        "Engineer User or membership state changed",
        "Project Organization backfill is incomplete",
        "Project Organization backfill contains dangling IDs",
    ):
        assert required in source


def test_patch_028_1_preserves_seven_projects_and_engineer():
    with engine.connect() as connection:
        assert connection.execute(
            text("SELECT current_database()")
        ).scalar_one() == "satco_platform_patch02022_test"

    try:
        command.downgrade(alembic_config, "e02600000001")
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    TRUNCATE TABLE
                        projects,
                        customers,
                        users,
                        organizations,
                        user_organization_memberships
                    RESTART IDENTITY CASCADE
                    """
                )
            )
            connection.execute(
                text(
                    """
                    INSERT INTO users (
                        id, email, username, hashed_password, full_name,
                        role, is_active, created_at
                    ) VALUES
                        (9001, 'admin@satco.com', 'bootstrap-admin', 'hash',
                         'Bootstrap Admin', 'admin', true, now()),
                        (9002, 'engineer@satco.com', 'protected-engineer', 'hash',
                         'Protected Engineer', 'engineer', true, now())
                    """
                )
            )
            connection.execute(
                text(
                    """
                    INSERT INTO customers (id, name, created_at)
                    VALUES (8001, 'Preserved Customer', now())
                    """
                )
            )
            connection.execute(
                text(
                    """
                    INSERT INTO projects (
                        id, project_code, name, description, customer_id,
                        status, priority, owner_id, primary_assignee_id,
                        start_date, target_completion_date, completed_at,
                        progress, created_at, updated_at
                    )
                    SELECT
                        7000 + sequence_number,
                        'SAT-PRJ-2026-' || lpad(sequence_number::text, 4, '0'),
                        'Preserved Project ' || sequence_number,
                        'Legacy development data ' || sequence_number,
                        8001,
                        'new',
                        'medium',
                        9001,
                        9002,
                        DATE '2026-08-02',
                        DATE '2026-12-31',
                        NULL,
                        sequence_number,
                        TIMESTAMPTZ '2026-08-02 00:00:00+00',
                        TIMESTAMPTZ '2026-08-02 00:00:00+00'
                    FROM generate_series(1, 7) AS sequence_number
                    """
                )
            )
            before_projects = connection.execute(
                text("SELECT to_jsonb(projects) FROM projects ORDER BY id")
            ).scalars().all()
            before_engineer = connection.execute(
                text(
                    "SELECT to_jsonb(users) FROM users "
                    "WHERE email = 'engineer@satco.com'"
                )
            ).scalar_one()

        command.upgrade(alembic_config, "e02810000001")

        with engine.connect() as connection:
            after_projects = connection.execute(
                text(
                    "SELECT to_jsonb(projects) - 'organization_id' "
                    "FROM projects ORDER BY id"
                )
            ).scalars().all()
            assert after_projects == before_projects
            assert connection.execute(
                text("SELECT count(*) FROM projects")
            ).scalar_one() == 7
            assert connection.execute(
                text(
                    "SELECT count(DISTINCT organization_id) FROM projects"
                )
            ).scalar_one() == 1
            assert str(
                connection.execute(
                    text("SELECT organization_id FROM projects LIMIT 1")
                ).scalar_one()
            ) == "7e7c9d7a-7693-4f75-9bc5-3ef7bf528281"
            assert connection.execute(
                text(
                    """
                    SELECT count(*)
                    FROM user_organization_memberships AS membership
                    JOIN users ON users.id = membership.user_id
                    WHERE users.email = 'admin@satco.com'
                      AND membership.is_enabled
                      AND membership.is_selected
                    """
                )
            ).scalar_one() == 1
            assert connection.execute(
                text(
                    "SELECT to_jsonb(users) FROM users "
                    "WHERE email = 'engineer@satco.com'"
                )
            ).scalar_one() == before_engineer
            assert connection.execute(
                text("SELECT count(*) FROM users")
            ).scalar_one() == 2
            columns = {
                item["name"]: item
                for item in inspect(connection).get_columns("projects")
            }
            assert columns["organization_id"]["nullable"] is False
    finally:
        _restore_shared_test_state()
