"""enhance Project core

Revision ID: f18a1c0e2026
Revises: d8271b8f1a29
Create Date: 2026-07-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f18a1c0e2026"
down_revision: Union[str, Sequence[str], None] = "d8271b8f1a29"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _prepare_project_code_sequences() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "project_code_sequences" not in inspector.get_table_names():
        op.create_table(
            "project_code_sequences",
            sa.Column(
                "year",
                sa.Integer(),
                autoincrement=False,
                nullable=False,
            ),
            sa.Column("last_value", sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint(
                "year",
                name="pk_project_code_sequences",
            ),
            sa.CheckConstraint(
                "last_value >= 1",
                name="ck_project_code_sequences_last_value",
            ),
        )
        return

    columns = {
        column["name"]: column
        for column in inspector.get_columns("project_code_sequences")
    }
    if set(columns) != {"year", "last_value"}:
        raise RuntimeError(
            "PATCH-019: incompatible project_code_sequences columns"
        )
    for column_name in ("year", "last_value"):
        column = columns[column_name]
        if not isinstance(column["type"], sa.Integer):
            raise RuntimeError(
                "PATCH-019: project_code_sequences columns must be integers"
            )
        if column["nullable"]:
            raise RuntimeError(
                "PATCH-019: project_code_sequences columns must be non-null"
            )

    primary_key = inspector.get_pk_constraint(
        "project_code_sequences"
    )
    if primary_key.get("constrained_columns") != ["year"]:
        raise RuntimeError(
            "PATCH-019: project_code_sequences requires year primary key"
        )

    invalid_counter = bind.execute(
        sa.text(
            "SELECT 1 FROM project_code_sequences "
            "WHERE last_value < 1 LIMIT 1"
        )
    ).first()
    if invalid_counter:
        raise RuntimeError(
            "PATCH-019: project_code_sequences has invalid counters"
        )

    op.alter_column(
        "project_code_sequences",
        "year",
        existing_type=sa.Integer(),
        existing_nullable=False,
        server_default=None,
    )

    primary_key_name = primary_key.get("name")
    if not primary_key_name:
        raise RuntimeError(
            "PATCH-019: project_code_sequences primary key must be named"
        )
    if primary_key_name != "pk_project_code_sequences":
        op.execute(
            sa.text(
                "ALTER TABLE project_code_sequences "
                f"RENAME CONSTRAINT "
                f'"{primary_key_name}" TO "pk_project_code_sequences"'
            )
        )

    check_constraints = {
        constraint["name"]: constraint
        for constraint in inspector.get_check_constraints(
            "project_code_sequences"
        )
    }
    counter_check = check_constraints.get(
        "ck_project_code_sequences_last_value"
    )
    if counter_check is None:
        op.create_check_constraint(
            "ck_project_code_sequences_last_value",
            "project_code_sequences",
            "last_value >= 1",
        )
    elif "last_value >= 1" not in (
        counter_check.get("sqltext", "")
        .replace("(", "")
        .replace(")", "")
        .strip()
    ):
        raise RuntimeError(
            "PATCH-019: incompatible Project Code counter constraint"
        )


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM projects
                WHERE status IS NULL
                   OR status NOT IN (
                       'new',
                       'in_progress',
                       'on_hold',
                       'completed',
                       'cancelled'
                    )
            ) OR EXISTS (
                SELECT 1
                FROM projects
                WHERE name IS NULL
                   OR LENGTH(BTRIM(name)) NOT BETWEEN 1 AND 200
            ) THEN
                RAISE EXCEPTION
                    'PATCH-018.1: projects contain invalid status or name values';
            END IF;
        END
        $$;
        """
    )

    _prepare_project_code_sequences()

    op.add_column(
        "projects",
        sa.Column(
            "project_code",
            sa.String(length=32),
            nullable=True,
        ),
    )

    op.execute(
        """
        WITH ranked_projects AS (
            SELECT
                id,
                EXTRACT(
                    YEAR FROM COALESCE(
                        created_at,
                        CURRENT_TIMESTAMP AT TIME ZONE 'UTC'
                    )
                )::integer AS creation_year,
                ROW_NUMBER() OVER (
                    PARTITION BY EXTRACT(
                        YEAR FROM COALESCE(
                            created_at,
                            CURRENT_TIMESTAMP AT TIME ZONE 'UTC'
                        )
                    )::integer
                    ORDER BY
                        COALESCE(
                            created_at,
                            CURRENT_TIMESTAMP AT TIME ZONE 'UTC'
                        ),
                        id
                ) AS yearly_sequence
            FROM projects
        )
        UPDATE projects AS project
        SET project_code = (
            'SAT-PRJ-'
            || ranked.creation_year::text
            || '-'
            || LPAD(
                ranked.yearly_sequence::text,
                GREATEST(
                    4,
                    LENGTH(ranked.yearly_sequence::text)
                ),
                '0'
            )
        )
        FROM ranked_projects AS ranked
        WHERE project.id = ranked.id;
        """
    )

    op.execute(
        """
        INSERT INTO project_code_sequences AS existing (year, last_value)
        SELECT
            SUBSTRING(project_code FROM 9 FOR 4)::integer,
            MAX(SUBSTRING(project_code FROM 14)::integer)
        FROM projects
        GROUP BY SUBSTRING(project_code FROM 9 FOR 4)::integer
        ON CONFLICT (year) DO UPDATE
        SET last_value = GREATEST(
            existing.last_value,
            EXCLUDED.last_value
        );
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM projects
                WHERE project_code IS NULL
            ) OR EXISTS (
                SELECT project_code
                FROM projects
                GROUP BY project_code
                HAVING COUNT(*) > 1
            ) THEN
                RAISE EXCEPTION
                    'PATCH-018.1: Project Code backfill validation failed';
            END IF;
        END
        $$;
        """
    )

    op.alter_column(
        "projects",
        "project_code",
        existing_type=sa.String(length=32),
        nullable=False,
    )
    op.create_unique_constraint(
        "uq_projects_project_code",
        "projects",
        ["project_code"],
    )
    op.alter_column(
        "projects",
        "name",
        existing_type=sa.String(),
        type_=sa.String(length=200),
        existing_nullable=False,
    )
    op.execute(
        """
        UPDATE projects
        SET created_at = CURRENT_TIMESTAMP AT TIME ZONE 'UTC'
        WHERE created_at IS NULL;
        """
    )
    op.alter_column(
        "projects",
        "created_at",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
        nullable=False,
        postgresql_using="created_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "projects",
        "status",
        existing_type=sa.String(),
        existing_nullable=True,
        nullable=False,
    )

    op.add_column(
        "projects",
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column(
            "priority",
            sa.String(length=16),
            server_default=sa.text("'medium'"),
            nullable=False,
        ),
    )
    op.add_column(
        "projects",
        sa.Column("owner_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column(
            "primary_assignee_id",
            sa.Integer(),
            nullable=True,
        ),
    )
    op.add_column(
        "projects",
        sa.Column("start_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column(
            "target_completion_date",
            sa.Date(),
            nullable=True,
        ),
    )
    op.add_column(
        "projects",
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "projects",
        sa.Column(
            "progress",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )
    op.add_column(
        "projects",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE projects
        SET updated_at = COALESCE(
            created_at AT TIME ZONE 'UTC',
            CURRENT_TIMESTAMP
        );
        """
    )
    op.alter_column(
        "projects",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )

    op.create_foreign_key(
        "fk_projects_owner_id_users",
        "projects",
        "users",
        ["owner_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_projects_primary_assignee_id_users",
        "projects",
        "users",
        ["primary_assignee_id"],
        ["id"],
    )

    op.create_check_constraint(
        "ck_projects_project_code_format",
        "projects",
        "project_code ~ '^SAT-PRJ-[0-9]{4}-[0-9]{4,}$'",
    )
    op.create_check_constraint(
        "ck_projects_status",
        "projects",
        (
            "status IS NOT NULL AND status IN "
            "('new', 'in_progress', 'on_hold', 'completed', 'cancelled')"
        ),
    )
    op.create_check_constraint(
        "ck_projects_priority",
        "projects",
        "priority IN ('low', 'medium', 'high', 'critical')",
    )
    op.create_check_constraint(
        "ck_projects_progress",
        "projects",
        "progress BETWEEN 0 AND 100",
    )
    op.create_check_constraint(
        "ck_projects_completion_progress",
        "projects",
        (
            "(status = 'completed' AND progress = 100) "
            "OR (status <> 'completed' AND progress < 100)"
        ),
    )
    op.create_check_constraint(
        "ck_projects_date_order",
        "projects",
        (
            "start_date IS NULL "
            "OR target_completion_date IS NULL "
            "OR target_completion_date >= start_date"
        ),
    )

    op.create_index(
        "ix_projects_customer_id",
        "projects",
        ["customer_id"],
    )
    op.create_index(
        "ix_projects_status",
        "projects",
        ["status"],
    )
    op.create_index(
        "ix_projects_priority",
        "projects",
        ["priority"],
    )
    op.create_index(
        "ix_projects_owner_id",
        "projects",
        ["owner_id"],
    )
    op.create_index(
        "ix_projects_primary_assignee_id",
        "projects",
        ["primary_assignee_id"],
    )
    op.create_index(
        "ix_projects_start_date",
        "projects",
        ["start_date"],
    )
    op.create_index(
        "ix_projects_target_completion_date",
        "projects",
        ["target_completion_date"],
    )

    op.alter_column(
        "projects",
        "priority",
        existing_type=sa.String(length=16),
        server_default=None,
    )
    op.alter_column(
        "projects",
        "progress",
        existing_type=sa.Integer(),
        server_default=None,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_projects_target_completion_date",
        table_name="projects",
    )
    op.drop_index(
        "ix_projects_start_date",
        table_name="projects",
    )
    op.drop_index(
        "ix_projects_primary_assignee_id",
        table_name="projects",
    )
    op.drop_index(
        "ix_projects_owner_id",
        table_name="projects",
    )
    op.drop_index(
        "ix_projects_priority",
        table_name="projects",
    )
    op.drop_index(
        "ix_projects_status",
        table_name="projects",
    )
    op.drop_index(
        "ix_projects_customer_id",
        table_name="projects",
    )

    op.drop_constraint(
        "ck_projects_date_order",
        "projects",
        type_="check",
    )
    op.drop_constraint(
        "ck_projects_completion_progress",
        "projects",
        type_="check",
    )
    op.drop_constraint(
        "ck_projects_progress",
        "projects",
        type_="check",
    )
    op.drop_constraint(
        "ck_projects_priority",
        "projects",
        type_="check",
    )
    op.drop_constraint(
        "ck_projects_status",
        "projects",
        type_="check",
    )
    op.drop_constraint(
        "ck_projects_project_code_format",
        "projects",
        type_="check",
    )
    op.drop_constraint(
        "fk_projects_primary_assignee_id_users",
        "projects",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_projects_owner_id_users",
        "projects",
        type_="foreignkey",
    )
    op.drop_constraint(
        "uq_projects_project_code",
        "projects",
        type_="unique",
    )

    op.alter_column(
        "projects",
        "status",
        existing_type=sa.String(),
        existing_nullable=False,
        nullable=True,
    )
    op.alter_column(
        "projects",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=False,
        nullable=True,
        postgresql_using="created_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "projects",
        "name",
        existing_type=sa.String(length=200),
        type_=sa.String(),
        existing_nullable=False,
    )
    op.drop_column("projects", "updated_at")
    op.drop_column("projects", "progress")
    op.drop_column("projects", "completed_at")
    op.drop_column("projects", "target_completion_date")
    op.drop_column("projects", "start_date")
    op.drop_column("projects", "primary_assignee_id")
    op.drop_column("projects", "owner_id")
    op.drop_column("projects", "priority")
    op.drop_column("projects", "description")
    op.drop_column("projects", "project_code")
    op.drop_table("project_code_sequences")
