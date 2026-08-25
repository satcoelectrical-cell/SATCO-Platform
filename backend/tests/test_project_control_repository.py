from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.models.project_control import ProjectControlIdempotency, ProjectControlOutbox, ProjectRiskHistory
from app.repositories.project_control_repository import ProjectControlRepository
from tests.conftest import owner_engine


def test_repository_is_no_commit_boundary():
    assert not hasattr(ProjectControlRepository, "commit")


def test_history_idempotency_and_outbox_contracts_are_persistence_facts():
    assert ProjectRiskHistory.__tablename__ == "project_risk_history"
    assert ProjectControlIdempotency.__tablename__ == "project_control_idempotency"
    assert ProjectControlOutbox.__tablename__ == "project_control_outbox"


def _must_reject(connection, statement, params):
    savepoint = connection.begin_nested()
    try:
        with pytest.raises(DBAPIError):
            connection.execute(text(statement), params)
    finally:
        savepoint.rollback()


def _scope(connection):
    org_a, org_b = uuid4(), uuid4()
    actor = connection.execute(text("SELECT id FROM users ORDER BY id LIMIT 1")).scalar_one_or_none()
    if actor is None:
        actor = connection.execute(text(
            "INSERT INTO users(email,username,hashed_password,role,is_active) "
            "VALUES (:email,:username,'test','engineer',true) RETURNING id"
        ), {"email": f"patch047-{uuid4()}@test.invalid", "username": f"patch047-{uuid4()}"}).scalar_one()
    connection.execute(text("INSERT INTO organizations(id,is_active) VALUES (:a,true),(:b,true)"), {"a": org_a, "b": org_b})
    customer_a = connection.execute(text("SELECT coalesce(max(id), 0) + 1 FROM customers")).scalar_one()
    customer_b = customer_a + 1
    for customer_id, organization_id, name in ((customer_a, org_a, "PATCH-047 direct SQL A"), (customer_b, org_b, "PATCH-047 direct SQL B")):
        connection.execute(text("INSERT INTO customers(id,organization_id,name) VALUES (:id,:org,:name)"), {"id": customer_id, "org": organization_id, "name": name})
    project_a = connection.execute(text("SELECT coalesce(max(id), 0) + 1 FROM projects")).scalar_one()
    project_b = project_a + 1
    for project_id, organization_id, customer_id, suffix in ((project_a, org_a, customer_a, "9001"), (project_b, org_b, customer_b, "9002")):
        connection.execute(text("INSERT INTO projects(id,organization_id,project_code,name,customer_id,status,priority,progress,created_at,updated_at) VALUES (:id,:org,:code,'PATCH-047 direct SQL',:customer,'new','medium',0,now(),now())"), {"id": project_id, "org": organization_id, "code": f"SAT-PRJ-2099-{suffix}", "customer": customer_id})
    return org_a, org_b, project_a, project_b, actor


_ROOT_FIELDS = {
    "project_risks": ("statement,category,likelihood,impact,standing", "'risk','category','low','low','open'"),
    "project_issues": ("statement,observed_context,severity,standing", "'issue','observed','low','open'"),
    "project_decisions": ("statement,rationale,standing", "'decision','rationale','draft'"),
    "project_changes": ("statement,rationale,standing", "'change','rationale','recorded'"),
}


def _insert_root(connection, table, organization_id, project_id, actor):
    root_id = uuid4()
    fields, values = _ROOT_FIELDS[table]
    connection.execute(text(f"INSERT INTO {table}(id,organization_id,project_id,version,created_by_id,created_at,updated_by_id,updated_at,{fields}) VALUES (:id,:organization_id,:project_id,1,:actor,now(),:actor,now(),{values})"), {"id": root_id, "organization_id": organization_id, "project_id": project_id, "actor": actor})
    return root_id


def test_postgresql_direct_sql_enforces_root_and_change_impact_scope():
    with owner_engine.connect() as connection:
        transaction = connection.begin()
        try:
            org_a, org_b, project_a, _, actor = _scope(connection)
            roots = {table: _insert_root(connection, table, org_a, project_a, actor) for table in _ROOT_FIELDS}
            for table, (fields, values) in _ROOT_FIELDS.items():
                _must_reject(connection, f"INSERT INTO {table}(id,organization_id,project_id,version,created_by_id,created_at,updated_by_id,updated_at,{fields}) VALUES (:id,:organization_id,:project_id,1,:actor,now(),:actor,now(),{values})", {"id": uuid4(), "organization_id": org_b, "project_id": project_a, "actor": actor})
            _must_reject(connection, "INSERT INTO project_change_impacts(id,change_id,organization_id,project_id,target_kind,target_id,statement,standing) VALUES (:id,:change_id,:organization_id,:project_id,'deliverable',:target_id,'impact','potential')", {"id": uuid4(), "change_id": roots["project_changes"], "organization_id": org_b, "project_id": project_a, "target_id": uuid4()})
        finally:
            transaction.rollback()


def test_postgresql_direct_sql_enforces_append_only_history():
    histories = (("project_risk_history", "risk_id", "project_risks"), ("project_issue_history", "issue_id", "project_issues"), ("project_decision_history", "decision_id", "project_decisions"), ("project_change_history", "change_id", "project_changes"))
    with owner_engine.connect() as connection:
        transaction = connection.begin()
        try:
            org_a, _, project_a, _, actor = _scope(connection)
            for history_table, parent_column, root_table in histories:
                root_id = _insert_root(connection, root_table, org_a, project_a, actor)
                history_id = uuid4()
                connection.execute(text(f"INSERT INTO {history_table}(id,{parent_column},organization_id,project_id,aggregate_version,event_type,actor_id,occurred_at) VALUES (:id,:root_id,:organization_id,:project_id,1,'created',:actor,now())"), {"id": history_id, "root_id": root_id, "organization_id": org_a, "project_id": project_a, "actor": actor})
                _must_reject(connection, f"UPDATE {history_table} SET event_type='changed' WHERE id=:id", {"id": history_id})
                _must_reject(connection, f"DELETE FROM {history_table} WHERE id=:id", {"id": history_id})
        finally:
            transaction.rollback()


def test_postgresql_direct_sql_enforces_project_scoped_idempotency_and_outbox_scope():
    with owner_engine.connect() as connection:
        transaction = connection.begin()
        try:
            org_a, org_b, project_a, project_b, actor = _scope(connection)
            risk_id = _insert_root(connection, "project_risks", org_a, project_a, actor)
            key = uuid4()
            record = {"id": uuid4(), "organization_id": org_a, "project_id": project_a, "actor": actor, "key": key, "fingerprint": "a" * 64, "payload": '{"outcome":"success"}'}
            idempotency_sql = "INSERT INTO project_control_idempotency(id,organization_id,project_id,actor_id,operation,idempotency_key,fingerprint,replay_json,created_at) VALUES (:id,:organization_id,:project_id,:actor,'create_risk',:key,:fingerprint,CAST(:payload AS jsonb),now())"
            connection.execute(text(idempotency_sql), record)
            _must_reject(connection, idempotency_sql, dict(record, id=uuid4(), fingerprint="b" * 64))
            connection.execute(text(idempotency_sql), dict(record, id=uuid4(), organization_id=org_b, project_id=project_b, fingerprint="c" * 64))
            outbox = {"id": uuid4(), "event_id": uuid4(), "organization_id": org_a, "project_id": project_a, "aggregate_id": risk_id, "payload": '{"event":"RiskCreated"}'}
            outbox_sql = "INSERT INTO project_control_outbox(id,event_id,organization_id,project_id,aggregate_kind,aggregate_id,aggregate_version,event_type,payload,occurred_at) VALUES (:id,:event_id,:organization_id,:project_id,'risk',:aggregate_id,1,'RiskCreated',CAST(:payload AS jsonb),now())"
            connection.execute(text(outbox_sql), outbox)
            persisted = connection.execute(text("SELECT organization_id,project_id,aggregate_kind,aggregate_id,aggregate_version FROM project_control_outbox WHERE id=:id"), {"id": outbox["id"]}).mappings().one()
            assert dict(persisted) == {"organization_id": org_a, "project_id": project_a, "aggregate_kind": "risk", "aggregate_id": risk_id, "aggregate_version": 1}
            _must_reject(connection, outbox_sql, dict(outbox, id=uuid4(), event_id=uuid4(), organization_id=None))
            _must_reject(connection, outbox_sql, dict(outbox, id=uuid4(), event_id=uuid4(), project_id=None))
            _must_reject(connection, outbox_sql, dict(outbox, id=uuid4(), event_id=uuid4(), organization_id=org_b))
        finally:
            transaction.rollback()
