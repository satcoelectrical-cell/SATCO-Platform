import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError


IMMUTABLE_TABLES = {
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
    "cross_discipline_assessment_lineage",
}


def test_named_constraints_and_immutability_triggers_exist(db_session):
    constraints = set(db_session.execute(text(
        "SELECT conname FROM pg_constraint WHERE conname LIKE 'ck_xdi_%' OR conname LIKE 'uq_xdi_%' OR conname LIKE 'fk_xdi_%'"
    )).scalars())
    assert {
        "fk_xdi_root_project_scope", "uq_xdi_finding_fingerprint",
        "fk_xdi_idempotency_project_scope", "uq_xdi_idempotency_scope",
        "ck_xdi_assessment_status_reason",
    } <= constraints
    rows = db_session.execute(text(
        "SELECT c.relname,t.tgname FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
        "WHERE NOT t.tgisinternal AND c.relname LIKE 'cross_discipline_%' "
        "AND t.tgname LIKE 'trg_%_immutable'"
    )).all()
    assert {row[0] for row in rows} == IMMUTABLE_TABLES


def test_functions_are_fixed_search_path_owner_objects_and_public_cannot_execute(db_session):
    rows = db_session.execute(text(
        "SELECT p.proname,pg_get_functiondef(p.oid),has_function_privilege('public',p.oid,'EXECUTE') "
        "FROM pg_proc p WHERE p.proname LIKE 'satco_cross_discipline_%'"
    )).all()
    assert len(rows) == 5
    assert all("SET search_path TO 'pg_catalog', 'public'" in definition for _, definition, _ in rows)
    assert all(not public_execute for _, _, public_execute in rows)


def test_runtime_role_has_no_delete_truncate_or_ddl_authority(db_session):
    forbidden = db_session.execute(text(
        "SELECT privilege_type FROM information_schema.role_table_grants "
        "WHERE grantee='satco_runtime' AND table_name LIKE 'cross_discipline_%' "
        "AND privilege_type IN ('DELETE','TRUNCATE','REFERENCES','TRIGGER')"
    )).scalars().all()
    assert forbidden == []
    assert db_session.execute(text(
        "SELECT NOT has_schema_privilege('satco_runtime','public','CREATE')"
    )).scalar_one()


def _seed_root(db_session, relationship_domain, *, status="completed_no_findings"):
    root_id, execution_id, snapshot_id = uuid4(), uuid4(), uuid4()
    project = relationship_domain["project"]
    workspace = relationship_domain["provider_workspace"]
    actor = relationship_domain["actors"]["project_owner"]
    now = datetime.now(timezone.utc)
    values = {
        "id": root_id, "organization_id": project.organization_id,
        "project_id": project.id, "actor_id": actor.id, "request_id": uuid4(),
        "correlation_id": uuid4(), "idempotency_key": uuid4(),
        "status": status, "now": now,
    }
    db_session.execute(text("""
      INSERT INTO cross_discipline_assessments(
        id,organization_id,project_id,actor_id,request_id,purpose,rationale,
        correlation_id,idempotency_key,combination_id,request_digest,scope_digest,
        status,aggregate_version,created_at,completed_at
      ) VALUES (
        :id,:organization_id,:project_id,:actor_id,:request_id,'interface_assessment',
        'database evidence',:correlation_id,:idempotency_key,'cross.ei.v1',
        repeat('a',64),repeat('b',64),:status,1,:now,:now
      )
    """), values)
    db_session.execute(text("""
      INSERT INTO cross_discipline_assessment_snapshots(
        organization_id,project_id,assessment_id,execution_id,snapshot_id,
        registry_digest,definition_digest,source_manifest_digest,finding_set_digest,
        snapshot_digest,result_digest,observed_through,completed_at,payload
      ) VALUES (
        :organization_id,:project_id,:id,:execution_id,:snapshot_id,
        repeat('c',64),repeat('d',64),repeat('e',64),repeat('f',64),
        repeat('1',64),repeat('2',64),:now,:now,CAST(:payload AS jsonb)
      )
    """), {**values, "execution_id": execution_id, "snapshot_id": snapshot_id, "payload": json.dumps({"workspace_ids": [workspace.id]})})
    db_session.execute(text("""
      INSERT INTO cross_discipline_assessment_workspaces(
        organization_id,project_id,assessment_id,workspace_id,package_key,
        discipline_id,role,binding_revision,binding_digest
      ) VALUES (
        :organization_id,:project_id,:id,:workspace_id,'electrical',
        'electrical','provider',1,repeat('3',64)
      )
    """), {**values, "workspace_id": workspace.id})
    return root_id, values


def test_append_only_and_root_version_guards_execute_on_real_rows(db_session, relationship_domain):
    root_id, values = _seed_root(db_session, relationship_domain)
    db_session.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    savepoint = db_session.begin_nested()
    with pytest.raises(DBAPIError):
        db_session.execute(text(
            "UPDATE cross_discipline_assessment_snapshots SET payload='{}'::jsonb WHERE assessment_id=:id"
        ), {"id": root_id})
    savepoint.rollback()
    db_session.execute(text(
        "UPDATE cross_discipline_assessments SET aggregate_version=2 WHERE id=:id"
    ), {"id": root_id})
    assert db_session.execute(text(
        "SELECT aggregate_version FROM cross_discipline_assessments WHERE id=:id"
    ), {"id": root_id}).scalar_one() == 2
    savepoint = db_session.begin_nested()
    with pytest.raises(DBAPIError):
        db_session.execute(text(
            "UPDATE cross_discipline_assessments SET status='unavailable',reason_code='runtime_unavailable',aggregate_version=3 WHERE id=:id"
        ), {"id": root_id})
    savepoint.rollback()


def test_root_project_tenant_coherence_is_database_enforced(db_session, relationship_domain):
    project = relationship_domain["project"]
    actor = relationship_domain["actors"]["project_owner"]
    foreign_organization = uuid4()
    db_session.execute(text("INSERT INTO organizations(id,is_active) VALUES(:id,true)"), {"id": foreign_organization})
    savepoint = db_session.begin_nested()
    with pytest.raises(IntegrityError):
        db_session.execute(text("""
          INSERT INTO cross_discipline_assessments(
            id,organization_id,project_id,actor_id,request_id,purpose,rationale,
            correlation_id,idempotency_key,combination_id,request_digest,scope_digest,
            status,reason_code,aggregate_version,created_at,completed_at
          ) VALUES (
            :id,:organization_id,:project_id,:actor_id,:request_id,'interface_assessment',
            'tenant coherence',:correlation_id,:idempotency_key,'cross.ei.v1',
            repeat('a',64),repeat('b',64),'unavailable','runtime_unavailable',1,now(),now()
          )
        """), {"id": uuid4(), "organization_id": foreign_organization, "project_id": project.id, "actor_id": actor.id, "request_id": uuid4(), "correlation_id": uuid4(), "idempotency_key": uuid4()})
    savepoint.rollback()


def test_idempotency_project_tenant_coherence_is_database_enforced(db_session, relationship_domain):
    project = relationship_domain["project"]
    actor = relationship_domain["actors"]["project_owner"]
    foreign_organization = uuid4()
    db_session.execute(text("INSERT INTO organizations(id,is_active) VALUES(:id,true)"), {"id": foreign_organization})
    savepoint = db_session.begin_nested()
    with pytest.raises(IntegrityError):
        db_session.execute(text("""
          INSERT INTO cross_discipline_idempotency(
            id,organization_id,project_id,actor_id,operation,idempotency_key,request_digest
          ) VALUES (
            :id,:organization_id,:project_id,:actor_id,'create_assessment',:idempotency_key,repeat('a',64)
          )
        """), {
            "id": uuid4(), "organization_id": foreign_organization,
            "project_id": project.id, "actor_id": actor.id,
            "idempotency_key": uuid4(),
        })
    savepoint.rollback()


def test_duplicate_fingerprint_rejects_second_row_without_partial_commit(db_session, relationship_domain):
    root_id, values = _seed_root(db_session, relationship_domain, status="completed_with_findings")
    occurrence_id, finding_id = uuid4(), uuid4()
    workspace = relationship_domain["provider_workspace"]
    db_session.execute(text("""
      INSERT INTO cross_discipline_interface_occurrences(
        id,organization_id,project_id,assessment_id,occurrence_key,
        interface_definition_id,provider_workspace_id,consumer_workspace_id,
        applicability,payload,occurrence_digest
      ) VALUES (
        :occurrence_id,:organization_id,:project_id,:id,repeat('4',64),
        'test.interface',:workspace_id,:workspace_id,'satisfied','{}'::jsonb,repeat('5',64)
      )
    """), {**values, "occurrence_id": occurrence_id, "workspace_id": workspace.id})
    db_session.execute(text("""
      INSERT INTO cross_discipline_findings(
        id,organization_id,project_id,assessment_id,occurrence_id,ordinal,
        rule_id,rule_version,rule_digest,category,subcode,severity,fingerprint,
        recurrence_key,affected_selector,payload
      ) VALUES (
        :finding_id,:organization_id,:project_id,:id,:occurrence_id,0,
        'test.rule','1.0.0',repeat('6',64),'missing','test.missing','warning',
        repeat('7',64),repeat('8',64),'selector','{}'::jsonb
      )
    """), {**values, "finding_id": finding_id, "occurrence_id": occurrence_id})
    savepoint = db_session.begin_nested()
    with pytest.raises(IntegrityError):
        db_session.execute(text("""
          INSERT INTO cross_discipline_findings(
            id,organization_id,project_id,assessment_id,occurrence_id,ordinal,
            rule_id,rule_version,rule_digest,category,subcode,severity,fingerprint,
            recurrence_key,affected_selector,payload
          ) VALUES (
            :finding_id,:organization_id,:project_id,:id,:occurrence_id,1,
            'test.rule','1.0.0',repeat('6',64),'missing','test.missing','warning',
            repeat('7',64),repeat('8',64),'selector','{}'::jsonb
          )
        """), {**values, "finding_id": uuid4(), "occurrence_id": occurrence_id})
    savepoint.rollback()
    assert db_session.execute(text(
        "SELECT count(*) FROM cross_discipline_findings WHERE assessment_id=:id"
    ), {"id": root_id}).scalar_one() == 1
