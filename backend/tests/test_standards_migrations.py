import pytest
from sqlalchemy import text


@pytest.mark.parametrize("vector", ["P054-AUD-01", "P054-AUD-02", "P054-DB-01"])
def test_standards_foundation_tables_exist(db_session, vector):
    for table in ("standard_identities", "standard_editions", "standard_edition_standing_observations", "standard_rights_bindings", "standards_idempotency", "standards_outbox"):
        assert db_session.execute(text("SELECT to_regclass(:name)"), {"name": f"public.{table}"}).scalar_one() is not None
