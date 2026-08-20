"""PATCH-038 canonical Customer Organization ownership.

Revision ID: e03800000001
Revises: e03400000001
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e03800000001"
down_revision: str | None = "e03400000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


LEGACY_ORGANIZATION_ID = "7e7c9d7a-7693-4f75-9bc5-3ef7bf528281"


def upgrade() -> None:
    op.add_column(
        "customers",
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_customers_organization_id_organizations",
        "customers",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.execute(
        f"""
        DO $$
        DECLARE
          customer_count integer;
          approved_count integer;
        BEGIN
          SELECT count(*) INTO customer_count FROM customers;
          IF customer_count > 0 THEN
            SELECT count(*) INTO approved_count
            FROM customers
            WHERE (id, name) IN (
              (1, 'SATCO Test Customer'),
              (2, 'SATCO Test Customer'),
              (3, 'Demo Customer'),
              (4, 'SATCO'),
              (6, 'CONTACT AUDIT CUSTOMER')
            );
            IF customer_count <> 5 OR approved_count <> 5 THEN
              RAISE EXCEPTION
                'PATCH-038 legacy Customer inventory differs from Human-approved mapping';
            END IF;
            IF NOT EXISTS (
              SELECT 1 FROM organizations
              WHERE id = '{LEGACY_ORGANIZATION_ID}'::uuid
                AND is_active IS TRUE
            ) THEN
              RAISE EXCEPTION
                'PATCH-038 approved owning Organization is missing or inactive';
            END IF;
            UPDATE customers
            SET organization_id = '{LEGACY_ORGANIZATION_ID}'::uuid;
          END IF;
          IF EXISTS (
            SELECT 1 FROM projects p JOIN customers c ON c.id=p.customer_id
            WHERE p.organization_id IS DISTINCT FROM c.organization_id
          ) THEN
            RAISE EXCEPTION
              'PATCH-038 found Project/Customer Organization conflict';
          END IF;
          IF EXISTS (
            SELECT 1 FROM engineering_objects eo
            JOIN customers c ON c.id=eo.customer_id
            WHERE eo.customer_id IS NOT NULL
              AND eo.organization_id IS DISTINCT FROM c.organization_id
          ) THEN
            RAISE EXCEPTION
              'PATCH-038 found Engineering Object/Customer Organization conflict';
          END IF;
        END $$
        """
    )
    op.alter_column("customers", "organization_id", nullable=False)
    op.create_index(
        "ix_customers_organization_name_id",
        "customers",
        ["organization_id", "name", "id"],
    )
    op.execute(
        """
        CREATE FUNCTION satco_customer_org_immutable() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
          IF NEW.organization_id IS DISTINCT FROM OLD.organization_id THEN
            RAISE EXCEPTION 'Customer Organization ownership is immutable';
          END IF;
          RETURN NEW;
        END $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_customers_org_immutable
        BEFORE UPDATE OF organization_id ON customers
        FOR EACH ROW EXECUTE FUNCTION satco_customer_org_immutable()
        """
    )
    op.execute(
        """
        CREATE FUNCTION satco_project_customer_org_guard() RETURNS trigger
        LANGUAGE plpgsql AS $$
        DECLARE
          customer_organization_id uuid;
        BEGIN
          SELECT organization_id INTO customer_organization_id
          FROM customers WHERE id = NEW.customer_id;
          IF customer_organization_id IS NULL
             OR customer_organization_id IS DISTINCT FROM NEW.organization_id THEN
            RAISE EXCEPTION 'Project and Customer must belong to the same Organization';
          END IF;
          RETURN NEW;
        END $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_projects_customer_org_guard
        BEFORE INSERT OR UPDATE OF customer_id, organization_id ON projects
        FOR EACH ROW EXECUTE FUNCTION satco_project_customer_org_guard()
        """
    )
    for signature in (
        "satco_customer_org_immutable()",
        "satco_project_customer_org_guard()",
    ):
        op.execute(f"REVOKE ALL ON FUNCTION {signature} FROM PUBLIC")
        op.execute(
            "DO $$ BEGIN "
            "IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='satco_runtime') THEN "
            f"EXECUTE 'REVOKE ALL ON FUNCTION {signature} FROM satco_runtime'; "
            "END IF; END $$"
        )
    op.execute(
        """
        DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='satco_runtime') THEN
            REVOKE ALL ON customers FROM satco_runtime;
            GRANT SELECT, INSERT, DELETE ON customers TO satco_runtime;
            GRANT UPDATE (name, company, phone, email) ON customers TO satco_runtime;
            REVOKE TRIGGER, TRUNCATE, REFERENCES ON customers FROM satco_runtime;
          END IF;
        END $$
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS trg_projects_customer_org_guard ON projects"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS trg_customers_org_immutable ON customers"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS satco_project_customer_org_guard()"
    )
    op.execute("DROP FUNCTION IF EXISTS satco_customer_org_immutable()")
    op.drop_index("ix_customers_organization_name_id", table_name="customers")
    op.drop_constraint(
        "fk_customers_organization_id_organizations",
        "customers",
        type_="foreignkey",
    )
    op.drop_column("customers", "organization_id")
