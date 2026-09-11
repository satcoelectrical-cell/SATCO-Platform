from pathlib import Path

from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text

from conftest import alembic_config, owner_engine


REVISION = "e05300000002"
PARENT = "e05300000001"
TABLES = {
    "cross_discipline_assessments",
    "cross_discipline_assessment_snapshots",
    "cross_discipline_assessment_workspaces",
    "cross_discipline_source_projections",
    "cross_discipline_completeness_attestations",
    "cross_discipline_interface_occurrences",
    "cross_discipline_occurrence_sources",
    "cross_discipline_findings",
    "cross_discipline_finding_sources",
    "cross_discipline_finding_attestations",
    "cross_discipline_finding_dispositions",
    "cross_discipline_finding_current",
    "cross_discipline_assessment_lineage",
    "cross_discipline_idempotency",
    "cross_discipline_outbox",
}


def test_revision_is_sole_head_with_exact_parent():
    script = ScriptDirectory.from_config(alembic_config)
    assert script.get_heads() == [REVISION]
    item = script.get_revision(REVISION)
    assert item.down_revision == PARENT


def test_upgrade_is_additive_and_fabricates_no_assessment():
    assert TABLES <= set(inspect(owner_engine).get_table_names())
    with owner_engine.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == REVISION
        assert connection.execute(text("SELECT count(*) FROM cross_discipline_assessments")).scalar_one() == 0


def test_empty_downgrade_and_reupgrade_restore_linear_head():
    command.downgrade(alembic_config, PARENT)
    try:
        assert TABLES <= set(inspect(owner_engine).get_table_names())
        with owner_engine.connect() as connection:
            assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == PARENT
    finally:
        command.upgrade(alembic_config, REVISION)
    assert TABLES <= set(inspect(owner_engine).get_table_names())


def test_failed_ddl_transaction_rolls_back_without_advancing_head():
    with owner_engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(text("CREATE TABLE xdi_injected_failure_probe(id integer)"))
            raise RuntimeError("injected migration failure")
        except RuntimeError:
            transaction.rollback()
    assert "xdi_injected_failure_probe" not in set(inspect(owner_engine).get_table_names())
    with owner_engine.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == REVISION
