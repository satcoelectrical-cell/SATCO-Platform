"""Narrow Document Intelligence runtime mutation privileges.

Revision ID: di0000000003
Revises: di0000000002
"""
from alembic import op


revision = "di0000000003"
down_revision = "di0000000002"
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
            REVOKE ALL ON public.document_analysis_runs,
              public.document_engineering_candidates,
              public.document_findings FROM satco_runtime;

            GRANT SELECT, INSERT ON public.document_analysis_runs,
              public.document_engineering_candidates,
              public.document_findings TO satco_runtime;

            GRANT UPDATE(
              document_family, state, progress_completed, progress_total,
              customer_message, page_count, candidate_count, unreviewed_count,
              limitations, provider_status, parser_id, parser_version,
              output_digest, version, superseded_by_run_id, updated_at
            ) ON public.document_analysis_runs TO satco_runtime;

            GRANT UPDATE(
              review_state, subject_key, subject_label, raw_value,
              normalized_value, numeric_value, unit, quantity_type, condition,
              uncertainty, reviewed_by_id, reviewed_at, version, updated_at
            ) ON public.document_engineering_candidates TO satco_runtime;

            GRANT UPDATE(state) ON public.document_findings TO satco_runtime;
          END IF;
        END
        $$;
        """
    )


def downgrade():
    """Restore the exact parent-revision ACL instead of a blanket revoke."""
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'satco_runtime'
          ) THEN
            REVOKE ALL ON public.document_analysis_runs,
              public.document_engineering_candidates,
              public.document_findings FROM satco_runtime;
            GRANT SELECT, INSERT, UPDATE ON public.document_analysis_runs,
              public.document_engineering_candidates,
              public.document_findings TO satco_runtime;
          END IF;
        END
        $$;
        """
    )
