"""Real-PostgreSQL qualification for PATCH-054 Batch-5 migration M3."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.models.customer import Customer
from app.models.project import Project
from conftest import TEST_DATABASE_REVISION, alembic_config, owner_engine


def _run_values(db_session, admin_user):
    organization_id = db_session.execute(
        text(
            "SELECT organization_id FROM user_organization_memberships "
            "WHERE user_id=:actor AND is_enabled=true AND is_selected=true"
        ),
        {"actor": admin_user.id},
    ).scalar_one()
    customer = Customer(organization_id=organization_id, name=f"Intelligence {uuid4()}")
    db_session.add(customer); db_session.flush()
    project = Project(organization_id=organization_id, project_code=f"SAT-PRJ-2054-{uuid4().int % 900000 + 100000}", name="Intelligence migration", customer_id=customer.id, status="new", priority="medium", progress=0, owner_id=admin_user.id)
    db_session.add(project); db_session.flush()
    return {"id": uuid4(), "organization": organization_id, "project": project.id, "actor": admin_user.id,
            "correlation": uuid4(), "digest": uuid4().hex + uuid4().hex,
            "deadline": datetime.now(timezone.utc) + timedelta(seconds=30)}


INSERT_RUN = text("""
INSERT INTO standard_intelligence_runs(
 id,organization_id,project_id,request_kind,purpose,correlation_id,request_digest,
 deterministic_result,deterministic_result_digest,template_id,template_version,template_digest,
 processor_policy_id,provider_id,provider_model,rights_manifest,authorized_handle_digest,
 input_digest,input_byte_count,created_by,deadline_at)
VALUES (:id,:organization,:project,'human_requested_advisory','review',:correlation,:digest,
 '{"bounds":"pass"}'::jsonb,:digest,'standards_advisory','1',:digest,
 'local','local','local-safe-v1','[]'::jsonb,:digest,:digest,128,:actor,:deadline)
""")


def test_intelligence_migration_is_sole_additive_successor():
    script = ScriptDirectory.from_config(alembic_config)
    assert script.get_heads() == [TEST_DATABASE_REVISION]
    assert script.get_revision("e05400000006").down_revision == "e05400000005"


def test_runtime_privileges_are_exact_and_function_is_not_callable(db_session):
    observed = db_session.execute(text("""
    SELECT has_table_privilege('satco_runtime','standard_intelligence_runs','SELECT'),
      has_column_privilege('satco_runtime','standard_intelligence_runs','id','INSERT'),
      has_column_privilege('satco_runtime','standard_intelligence_runs','phase_status','INSERT'),
      has_column_privilege('satco_runtime','standard_intelligence_runs','phase_status','UPDATE'),
      has_column_privilege('satco_runtime','standard_intelligence_runs','processor_policy_id','UPDATE'),
      has_table_privilege('satco_runtime','standard_intelligence_runs','DELETE'),
      has_function_privilege('satco_runtime','standards_intelligence_lifecycle_guard()','EXECUTE'),
      has_table_privilege('satco_registry_installer','standard_intelligence_runs','SELECT'),
      has_function_privilege('satco_registry_installer','standards_intelligence_lifecycle_guard()','EXECUTE'),
      EXISTS (
        SELECT 1 FROM pg_class relation
        CROSS JOIN LATERAL aclexplode(coalesce(relation.relacl,acldefault('r',relation.relowner))) privilege
        WHERE relation.oid='standard_intelligence_runs'::regclass
          AND privilege.grantee=0 AND privilege.privilege_type='SELECT'
      ),
      EXISTS (
        SELECT 1 FROM pg_proc procedure
        CROSS JOIN LATERAL aclexplode(coalesce(procedure.proacl,acldefault('f',procedure.proowner))) privilege
        WHERE procedure.oid='standards_intelligence_lifecycle_guard()'::regprocedure
          AND privilege.grantee=0 AND privilege.privilege_type='EXECUTE'
      )
    """)).one()
    assert tuple(observed) == (True, True, False, True, False, False, False, False, False, False, False)


def test_runtime_trigger_function_direct_execution_is_denied(db_session):
    with pytest.raises(DBAPIError), db_session.begin_nested():
        db_session.execute(text("SET LOCAL ROLE satco_runtime"))
        db_session.execute(text("SELECT standards_intelligence_lifecycle_guard()"))


def test_runtime_can_insert_and_perform_only_bounded_cas(db_session, admin_user):
    values = _run_values(db_session, admin_user)
    db_session.execute(text("SET LOCAL ROLE satco_runtime"))
    db_session.execute(INSERT_RUN, values)
    assert db_session.execute(text("SELECT phase_status,call_count,version FROM standard_intelligence_runs WHERE id=:id"), values).one() == ("requested", 0, 1)
    assert db_session.execute(text("""UPDATE standard_intelligence_runs SET phase_status='dispatched',call_count=1,dispatched_at=now(),version=2 WHERE id=:id AND phase_status='requested' AND call_count=0 AND version=1 RETURNING version"""), values).scalar_one() == 2


def test_runtime_select_is_explicitly_tenant_scoped(db_session, admin_user):
    values = _run_values(db_session, admin_user)
    db_session.execute(INSERT_RUN, values)
    db_session.execute(text("SET LOCAL ROLE satco_runtime"))
    assert db_session.execute(
        text("SELECT id FROM standard_intelligence_runs WHERE id=:id AND organization_id=:organization"),
        values,
    ).scalar_one() == values["id"]
    assert db_session.execute(
        text("SELECT id FROM standard_intelligence_runs WHERE id=:id AND organization_id=:other"),
        {**values, "other": uuid4()},
    ).scalar_one_or_none() is None


@pytest.mark.parametrize("statement", [
    "UPDATE standard_intelligence_runs SET organization_id=organization_id WHERE id=:id",
    "UPDATE standard_intelligence_runs SET project_id=project_id WHERE id=:id",
    "UPDATE standard_intelligence_runs SET report_id=report_id WHERE id=:id",
    "UPDATE standard_intelligence_runs SET processor_policy_id='other' WHERE id=:id",
    "UPDATE standard_intelligence_runs SET provider_id='other' WHERE id=:id",
    "UPDATE standard_intelligence_runs SET provider_model='other' WHERE id=:id",
    "UPDATE standard_intelligence_runs SET provider_version='other' WHERE id=:id",
    "DELETE FROM standard_intelligence_runs WHERE id=:id",
])
def test_runtime_cannot_mutate_provenance_provider_decision_or_delete(db_session, admin_user, statement):
    values = _run_values(db_session, admin_user); db_session.execute(INSERT_RUN, values); db_session.flush()
    with pytest.raises(DBAPIError), db_session.begin_nested():
        db_session.execute(text("SET LOCAL ROLE satco_runtime")); db_session.execute(text(statement), values)


@pytest.mark.parametrize("update", [
    "phase_status='terminal',result_status='completed_no_suggestions',completed_at=now(),version=2",
    "phase_status='dispatched',call_count=2,dispatched_at=now(),version=2",
    "phase_status='dispatched',call_count=1,dispatched_at=now(),version=3",
])
def test_database_rejects_invalid_lifecycle_call_count_and_version(db_session, admin_user, update):
    values = _run_values(db_session, admin_user); db_session.execute(INSERT_RUN, values); db_session.flush()
    with pytest.raises(DBAPIError), db_session.begin_nested():
        db_session.execute(text(f"UPDATE standard_intelligence_runs SET {update} WHERE id=:id"), values)


def test_terminal_run_cannot_be_mutated(db_session, admin_user):
    values = _run_values(db_session, admin_user); db_session.execute(INSERT_RUN, values)
    db_session.execute(text("UPDATE standard_intelligence_runs SET phase_status='terminal',result_status='unavailable',failure_code='AI_UNAVAILABLE',completed_at=now(),version=2 WHERE id=:id"), values)
    with pytest.raises(DBAPIError), db_session.begin_nested():
        db_session.execute(text("UPDATE standard_intelligence_runs SET failure_code='OTHER',version=3 WHERE id=:id"), values)


def test_intelligence_migration_downgrade_reupgrade():
    try:
        command.downgrade(alembic_config, "e05400000005")
        with owner_engine.connect() as connection:
            assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "e05400000005"
            assert not connection.execute(text("SELECT EXISTS(SELECT 1 FROM pg_trigger WHERE tgname='tr_standard_intelligence_lifecycle')")).scalar_one()
    finally:
        command.upgrade(alembic_config, TEST_DATABASE_REVISION)
    with owner_engine.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == TEST_DATABASE_REVISION
