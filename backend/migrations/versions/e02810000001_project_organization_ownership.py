"""add non-destructive Project Organization ownership

Revision ID: e02810000001
Revises: e02600000001
"""

from collections.abc import Sequence
from uuid import UUID

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e02810000001"
down_revision: str | None = "e02600000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEFAULT_ORGANIZATION_ID = UUID("7e7c9d7a-7693-4f75-9bc5-3ef7bf528281")
BOOTSTRAP_USER_EMAIL = "admin@satco.com"
BOOTSTRAP_USER_ROLE = "admin"
DEVELOPMENT_DATABASE_NAME = "satco_platform"
DEVELOPMENT_PROJECT_COUNT = 7


def _scalar(connection, statement: str, **parameters):
    return connection.execute(sa.text(statement), parameters).scalar_one()


def _project_digest(connection, *, exclude_organization: bool) -> str:
    expression = "to_jsonb(projects)"
    if exclude_organization:
        expression += " - 'organization_id'"
    return _scalar(
        connection,
        f"""
        SELECT md5(
            COALESCE(
                jsonb_agg({expression} ORDER BY projects.id)::text,
                '[]'
            )
        )
        FROM projects
        """,
    )


def _engineer_snapshot(connection) -> str:
    return _scalar(
        connection,
        """
        SELECT md5(
            COALESCE(
                jsonb_agg(snapshot.item ORDER BY snapshot.sort_key)::text,
                '[]'
            )
        )
        FROM (
            SELECT
                'user:' || users.id::text AS sort_key,
                jsonb_build_object(
                    'kind', 'user',
                    'value', to_jsonb(users)
                ) AS item
            FROM users
            WHERE lower(users.email) = 'engineer@satco.com'

            UNION ALL

            SELECT
                'membership:' || memberships.organization_id::text,
                jsonb_build_object(
                    'kind', 'membership',
                    'value', to_jsonb(memberships)
                )
            FROM user_organization_memberships AS memberships
            JOIN users ON users.id = memberships.user_id
            WHERE lower(users.email) = 'engineer@satco.com'
        ) AS snapshot
        """,
    )


def _assert_reference_integrity(connection) -> None:
    invalid = connection.execute(
        sa.text(
            """
            SELECT child.relname, constraint_record.conname
            FROM pg_constraint AS constraint_record
            JOIN pg_class AS child
              ON child.oid = constraint_record.conrelid
            WHERE constraint_record.contype = 'f'
              AND constraint_record.confrelid = 'projects'::regclass
              AND NOT constraint_record.convalidated
            """
        )
    ).all()
    if invalid:
        raise RuntimeError(
            "Project reference constraints are not validated: "
            f"{invalid!r}"
        )


def upgrade() -> None:
    connection = op.get_bind()
    connection.execute(sa.text("LOCK TABLE projects IN SHARE ROW EXCLUSIVE MODE"))

    inspector = sa.inspect(connection)
    required_tables = {
        "projects",
        "organizations",
        "user_organization_memberships",
        "users",
    }
    missing_tables = required_tables - set(inspector.get_table_names())
    if missing_tables:
        raise RuntimeError(
            "PATCH-028.1 required tables are missing: "
            f"{sorted(missing_tables)!r}"
        )
    if "organization_id" in {
        item["name"] for item in inspector.get_columns("projects")
    }:
        raise RuntimeError(
            "projects.organization_id already exists; refusing ambiguous upgrade"
        )

    project_count = _scalar(connection, "SELECT count(*) FROM projects")
    database_name = _scalar(connection, "SELECT current_database()")
    if (
        database_name == DEVELOPMENT_DATABASE_NAME
        and project_count != DEVELOPMENT_PROJECT_COUNT
    ):
        raise RuntimeError(
            "Development Project inventory changed: expected "
            f"{DEVELOPMENT_PROJECT_COUNT}, found {project_count}"
        )

    project_ids = tuple(
        connection.execute(sa.text("SELECT id FROM projects ORDER BY id")).scalars()
    )
    project_digest = _project_digest(
        connection, exclude_organization=False
    )
    engineer_snapshot = _engineer_snapshot(connection)
    _assert_reference_integrity(connection)

    op.add_column(
        "projects",
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_projects_organization_id_organizations",
        "projects",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    requires_backfill = project_count > 0
    if requires_backfill:
        organization = connection.execute(
            sa.text(
                "SELECT is_active FROM organizations WHERE id = :organization_id"
            ),
            {"organization_id": DEFAULT_ORGANIZATION_ID},
        ).one_or_none()
        if organization is not None and not organization.is_active:
            raise RuntimeError("Default Organization exists but is inactive")
        if organization is None:
            connection.execute(
                sa.text(
                    """
                    INSERT INTO organizations (id, is_active)
                    VALUES (:organization_id, true)
                    """
                ),
                {"organization_id": DEFAULT_ORGANIZATION_ID},
            )

        bootstrap_users = connection.execute(
            sa.text(
                """
                SELECT id, role, is_active
                FROM users
                WHERE lower(email) = lower(:email)
                ORDER BY id
                """
            ),
            {"email": BOOTSTRAP_USER_EMAIL},
        ).all()
        if len(bootstrap_users) != 1:
            raise RuntimeError(
                "Approved bootstrap email must resolve to exactly one User"
            )
        bootstrap_user = bootstrap_users[0]
        if (
            not bootstrap_user.is_active
            or bootstrap_user.role != BOOTSTRAP_USER_ROLE
        ):
            raise RuntimeError(
                "Approved bootstrap User must be active with role admin"
            )

        connection.execute(
            sa.text(
                """
                UPDATE projects
                SET organization_id = :organization_id
                WHERE organization_id IS NULL
                """
            ),
            {"organization_id": DEFAULT_ORGANIZATION_ID},
        )
        connection.execute(
            sa.text(
                """
                UPDATE user_organization_memberships
                SET is_selected = false, updated_at = now()
                WHERE user_id = :user_id
                  AND organization_id <> :organization_id
                  AND is_selected
                """
            ),
            {
                "user_id": bootstrap_user.id,
                "organization_id": DEFAULT_ORGANIZATION_ID,
            },
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO user_organization_memberships (
                    user_id, organization_id, is_enabled, is_selected
                )
                VALUES (:user_id, :organization_id, true, true)
                ON CONFLICT (user_id, organization_id) DO UPDATE
                SET is_enabled = true,
                    is_selected = true,
                    updated_at = now()
                """
            ),
            {
                "user_id": bootstrap_user.id,
                "organization_id": DEFAULT_ORGANIZATION_ID,
            },
        )

    if _scalar(connection, "SELECT count(*) FROM projects") != project_count:
        raise RuntimeError("Project count changed during PATCH-028.1")
    current_ids = tuple(
        connection.execute(sa.text("SELECT id FROM projects ORDER BY id")).scalars()
    )
    if current_ids != project_ids:
        raise RuntimeError("Project identities changed during PATCH-028.1")
    if _project_digest(connection, exclude_organization=True) != project_digest:
        raise RuntimeError("Pre-existing Project values changed during PATCH-028.1")
    if _scalar(
        connection,
        "SELECT count(*) FROM projects WHERE organization_id IS NULL",
    ):
        raise RuntimeError("Project Organization backfill is incomplete")
    if _scalar(
        connection,
        """
        SELECT count(*)
        FROM projects
        LEFT JOIN organizations
          ON organizations.id = projects.organization_id
        WHERE organizations.id IS NULL
        """,
    ):
        raise RuntimeError("Project Organization backfill contains dangling IDs")
    if requires_backfill:
        selected_count = _scalar(
            connection,
            """
            SELECT count(*)
            FROM user_organization_memberships AS memberships
            JOIN users ON users.id = memberships.user_id
            JOIN organizations ON organizations.id = memberships.organization_id
            WHERE lower(users.email) = lower(:email)
              AND memberships.organization_id = :organization_id
              AND memberships.is_enabled
              AND memberships.is_selected
              AND organizations.is_active
            """,
            email=BOOTSTRAP_USER_EMAIL,
            organization_id=DEFAULT_ORGANIZATION_ID,
        )
        if selected_count != 1:
            raise RuntimeError("Bootstrap Organization membership is not selected")
    if _engineer_snapshot(connection) != engineer_snapshot:
        raise RuntimeError("Engineer User or membership state changed")
    _assert_reference_integrity(connection)

    op.create_index(
        "ix_projects_organization_id",
        "projects",
        ["organization_id"],
        unique=False,
    )
    op.alter_column(
        "projects",
        "organization_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_index("ix_projects_organization_id", table_name="projects")
    op.drop_constraint(
        "fk_projects_organization_id_organizations",
        "projects",
        type_="foreignkey",
    )
    op.drop_column("projects", "organization_id")
