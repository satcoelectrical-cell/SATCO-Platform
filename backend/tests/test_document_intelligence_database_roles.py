"""Restricted-runtime evidence for Document Intelligence persistence."""
from sqlalchemy import text

from conftest import owner_engine


def test_runtime_document_intelligence_updates_are_column_scoped():
    with owner_engine.connect() as owner:
        privileges = owner.execute(text("""
            SELECT
              has_table_privilege('satco_runtime', 'document_analysis_runs', 'SELECT'),
              has_table_privilege('satco_runtime', 'document_analysis_runs', 'INSERT'),
              has_table_privilege('satco_runtime', 'document_analysis_runs', 'UPDATE'),
              has_column_privilege('satco_runtime', 'document_analysis_runs', 'state', 'UPDATE'),
              has_column_privilege('satco_runtime', 'document_analysis_runs', 'organization_id', 'UPDATE'),
              has_table_privilege('satco_runtime', 'document_engineering_candidates', 'UPDATE'),
              has_column_privilege('satco_runtime', 'document_engineering_candidates', 'review_state', 'UPDATE'),
              has_column_privilege('satco_runtime', 'document_engineering_candidates', 'analysis_run_id', 'UPDATE'),
              has_table_privilege('satco_runtime', 'document_findings', 'UPDATE'),
              has_column_privilege('satco_runtime', 'document_findings', 'state', 'UPDATE'),
              has_column_privilege('satco_runtime', 'document_findings', 'title', 'UPDATE'),
              has_table_privilege('satco_runtime', 'document_findings', 'DELETE')
        """)).one()

    assert privileges == (
        True, True, False, True, False,
        False, True, False,
        False, True, False, False,
    )
