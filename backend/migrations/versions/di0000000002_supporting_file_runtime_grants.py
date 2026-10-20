"""Correct supporting-file runtime grants required by P0 intake.

Revision ID: di0000000002
Revises: di0000000001
"""
from alembic import op


revision = "di0000000002"
down_revision = "di0000000001"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'satco_runtime'
          ) THEN
            REVOKE ALL ON public.supporting_file_idempotency,
              public.supporting_file_outbox FROM satco_runtime;
            GRANT SELECT, INSERT ON public.supporting_file_idempotency,
              public.supporting_file_outbox TO satco_runtime;
            GRANT UPDATE(status, asset_id, result, updated_at)
              ON public.supporting_file_idempotency TO satco_runtime;
            GRANT UPDATE(published_at)
              ON public.supporting_file_outbox TO satco_runtime;
          END IF;
        END
        $$;
        """
    )


def downgrade():
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'satco_runtime'
          ) THEN
            REVOKE ALL ON public.supporting_file_idempotency,
              public.supporting_file_outbox FROM satco_runtime;
          END IF;
        END
        $$;
        """
    )
