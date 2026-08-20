"""Real PostgreSQL evidence for PATCH-032 restricted-runtime enforcement."""

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from app.core.config import Settings
from app.core.database import runtime_database_url, validate_technical_report_runtime_boundary
from app.enums.technical_report import TechnicalReportIntegrityAlgorithm
from app.models.technical_report_command import (
    CaptureHistoricalBasisV1,
    EngineeringObjectHistoricalBasisV1,
    EngineeringRelationshipHistoricalBasisV1,
    EvidenceHistoricalBasisV1,
    ExternalHumanLocator,
    PreliminaryQualification,
    TechnicalReportAcceptedSnapshot,
    TechnicalReportContent,
    TechnicalReportDraftRevision,
    TechnicalReportProvenanceEntry,
    accepted_snapshot_payload,
    canonical_json,
    historical_basis_from_payload,
    validate_accepted_snapshot_payload,
)
from conftest import owner_engine


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _accepted_state(report_id, revision_id, scope):
    accepted_at = datetime.now(timezone.utc).replace(microsecond=123456)
    locator = ExternalHumanLocator(
        report_local_source_id=uuid4(), external_reference="field-note-1",
        submitted_by_id=scope["owner_id"], observed_at=accepted_at,
        retrieved_at=None, submitted_at=None,
        minimal_representation="verified field observation",
    )
    provenance = TechnicalReportProvenanceEntry(
        entry_id=uuid4(), ordinal=0,
        source_class="external_or_human_material", source_type="external_or_human",
        is_material=True, owning_capability=None, reliance_role="technical basis",
        verification_status="verified", availability_status="available",
        origin_attribution="Human", limitations=(), locator=locator,
        integrity_algorithm=TechnicalReportIntegrityAlgorithm.SHA256,
        integrity_digest=hashlib.sha256(canonical_json(locator)).hexdigest(),
    )
    snapshot = TechnicalReportAcceptedSnapshot(
        report_id=report_id, purpose="engineering_analysis",
        organization_id=scope["organization_id"], workspace_id=scope["workspace_id"],
        project_id=scope["project_id"],
        content=TechnicalReportContent("scope", "draft", (), "known uncertainty", (), "conclusion", ()),
        qualification=PreliminaryQualification(False), provenance=(provenance,),
        accepted_draft_revision=TechnicalReportDraftRevision(revision_id, 1),
        accepted_aggregate_version=2, accepted_by_id=scope["owner_id"],
        accepted_at=accepted_at, predecessor_report_id=None,
    )
    payload = accepted_snapshot_payload(snapshot)
    assert validate_accepted_snapshot_payload(json.loads(json.dumps(payload)), snapshot.integrity_digest) == payload
    return payload, snapshot.integrity_digest, accepted_at, payload["provenance"][0]


def _historical_basis(source_type: str, scope) -> dict[str, object]:
    common = {"basis_schema_version": 1, "organization_id": scope["organization_id"]}
    if source_type == "universal_capture":
        basis = CaptureHistoricalBasisV1(
            **common, source_category="universal_capture", capture_id=uuid4(), source_version=1,
            project_id=scope["project_id"], workspace_id=scope["workspace_id"], discipline="instrumentation",
            engineering_object_id=None, source_kind="field_note", original_content="field observation",
            source_reference="FN-1", creator_id=scope["owner_id"], lifecycle="captured",
            created_at=datetime.now(timezone.utc).replace(microsecond=123456),
        )
    elif source_type == "evidence":
        basis = EvidenceHistoricalBasisV1(
            **common, source_category="evidence", evidence_id=uuid4(), source_version=1,
            project_id=scope["project_id"], workspace_id=scope["workspace_id"], lifecycle="current",
            source_kind="engineering_record", source_reference="EV-1", source_revision="A",
            source_standing="current", effective_at=None, supported_fact="verified fact",
            creator_id=scope["owner_id"],
        )
    elif source_type == "engineering_object":
        basis = EngineeringObjectHistoricalBasisV1(
            **common, source_category="engineering_object", engineering_object_id=uuid4(), source_version=1,
            customer_id=None, project_id=scope["project_id"], workspace_id=scope["workspace_id"],
            family="instrumentation", discipline="instrumentation", object_type="instrument", subtype=None,
            lifecycle="active", authority_standing="approved", creator_id=scope["owner_id"], steward_id=scope["owner_id"],
        )
    else:
        basis = EngineeringRelationshipHistoricalBasisV1(
            **common, source_category="engineering_relationship", engineering_relationship_id=uuid4(), source_version=1,
            project_id=scope["project_id"], workspace_id=scope["workspace_id"], source_object_id=uuid4(),
            target_object_id=uuid4(), relationship_family="dependency", relationship_type="depends_on",
            lifecycle="current", authority_standing="approved", evidence_references=(uuid4(),),
            creator_id=scope["owner_id"], steward_id=scope["owner_id"], reviewer_id=None, approver_id=None,
        )
    return json.loads(canonical_json(basis))


def _fallback_values(source_type: str, report_id, scope, basis: dict[str, object]) -> dict[str, object]:
    values = {
        "id": uuid4(), "report_id": report_id, "source_type": source_type,
        "owning_capability": source_type, "minimal": json.dumps(basis),
        "digest": hashlib.sha256(_canonical(basis)).hexdigest(),
        "capture_id": None, "capture_version": None, "evidence_id": None,
        "evidence_version": None, "engineering_object_id": None,
        "engineering_object_version": None, "engineering_relationship_id": None,
        "engineering_relationship_version": None,
    }
    identity_fields = {
        "universal_capture": ("capture_id", "capture_version", "capture_id"),
        "evidence": ("evidence_id", "evidence_version", "evidence_id"),
        "engineering_object": ("engineering_object_id", "engineering_object_version", "engineering_object_id"),
        "engineering_relationship": ("engineering_relationship_id", "engineering_relationship_version", "engineering_relationship_id"),
    }
    identity_column, version_column, identity_key = identity_fields[source_type]
    values[identity_column] = basis[identity_key]
    values[version_column] = basis["source_version"]
    return values


_INSERT_CANONICAL_FALLBACK = text("""
    INSERT INTO technical_report_provenance_entries (
      id, technical_report_id, ordinal, source_class, source_type, is_material,
      owning_capability, reliance_role, verification_status, availability_status,
      origin_attribution, limitations, integrity_algorithm, integrity_digest,
      minimal_historical_representation, capture_id, capture_version, evidence_id,
      evidence_version, engineering_object_id, engineering_object_version,
      engineering_relationship_id, engineering_relationship_version,
      canonical_snapshot_id
    ) VALUES (
      :id,:report_id,0,'canonical_material',:source_type,true,:owning_capability,
      'basis','verified','available','Human','[]','sha256',:digest,CAST(:minimal AS json),
      :capture_id,:capture_version,:evidence_id,:evidence_version,
      :engineering_object_id,:engineering_object_version,
      :engineering_relationship_id,:engineering_relationship_version,NULL
    )
""")


def _runtime_engine():
    owner_url = owner_engine.url
    return create_engine(owner_url.set(username="satco_runtime", password=os.getenv("TEST_RUNTIME_DATABASE_PASSWORD", "satco_runtime_test_password")))


def _scope(connection):
    select_scope = text("""
        SELECT o.id AS organization_id, w.id AS workspace_id, w.project_id, u.id AS owner_id
        FROM organizations o
        JOIN projects p ON p.organization_id=o.id
        JOIN engineering_workspaces w ON w.project_id=p.id
        CROSS JOIN LATERAL (SELECT id FROM users WHERE is_active IS TRUE ORDER BY id LIMIT 1) u
        WHERE o.is_active IS TRUE ORDER BY w.id LIMIT 1
    """)
    row = connection.execute(select_scope).mappings().one_or_none()
    if row is not None:
        return {**dict(row), "_owned": False}
    token = uuid4().hex
    with owner_engine.begin() as owner:
        user_id = owner.execute(text("""
            INSERT INTO users(email, username, hashed_password, role, is_active, created_at)
            VALUES (:email, :username, 'test', 'engineer', true, now()) RETURNING id
        """), {"email": f"patch032-{token}@example.invalid", "username": f"patch032-{token}"}).scalar_one()
        organization_id = uuid4()
        owner.execute(text("INSERT INTO organizations(id, is_active) VALUES (:id, true)"), {"id": organization_id})
        customer_id = owner.execute(text("""
            INSERT INTO customers(name, organization_id)
            VALUES ('PATCH-032 Test', :organization_id) RETURNING id
        """), {"organization_id": organization_id}).scalar_one()
        project_id = owner.execute(text("""
            INSERT INTO projects(organization_id, project_code, name, customer_id, status, priority, owner_id, progress, created_at)
            VALUES (:organization_id, :code, 'PATCH-032 Test', :customer_id, 'new', 'medium', :owner_id, 0, now()) RETURNING id
        """), {"organization_id": organization_id, "code": f"SAT-PRJ-2099-{int(token[:8], 16)}", "customer_id": customer_id, "owner_id": user_id}).scalar_one()
        workspace_id = owner.execute(text("""
            INSERT INTO engineering_workspaces(project_id, discipline, status, owner_id, created_by_id, version)
            VALUES (:project_id, 'control', 'draft', :owner_id, :owner_id, 1) RETURNING id
        """), {"project_id": project_id, "owner_id": user_id}).scalar_one()
    return {"organization_id": organization_id, "workspace_id": workspace_id, "project_id": project_id, "owner_id": user_id, "customer_id": customer_id, "_owned": True}


def _cleanup_scope(scope) -> None:
    if not scope or not scope.get("_owned"):
        return
    with owner_engine.begin() as owner:
        owner.execute(text("DELETE FROM engineering_workspaces WHERE id=:id"), {"id": scope["workspace_id"]})
        owner.execute(text("DELETE FROM projects WHERE id=:id"), {"id": scope["project_id"]})
        owner.execute(text("DELETE FROM customers WHERE id=:id"), {"id": scope["customer_id"]})
        owner.execute(text("DELETE FROM organizations WHERE id=:id"), {"id": scope["organization_id"]})
        owner.execute(text("DELETE FROM users WHERE id=:id"), {"id": scope["owner_id"]})


def _insert_draft(connection):
    scope = _scope(connection)
    report_id, revision_id = uuid4(), uuid4()
    connection.execute(text("""
        INSERT INTO technical_reports (
          id, organization_id, workspace_id, project_id, owner_id, purpose,
          engineering_scope, draft_content, assumptions, uncertainty, limitations,
          conclusions, recommendations, is_preliminary, evidence_deficiencies,
          unresolved_issues, follow_up_requirements, draft_revision_id,
          draft_revision_number, lifecycle, version
        ) VALUES (
          :id, :organization_id, :workspace_id, :project_id, :owner_id,
          'engineering_analysis', 'scope', 'draft', '[]', 'known uncertainty',
          '[]', 'conclusion', '[]', false, '[]', '[]', '[]', :revision_id, 1,
          'draft', 1
        )
    """), {**scope, "id": report_id, "revision_id": revision_id})
    return report_id, revision_id, scope


def _insert_external_snapshot_provenance(connection, report_id, provenance, accepted_at) -> None:
    connection.execute(text("""
        INSERT INTO technical_report_provenance_entries (
          id, technical_report_id, ordinal, source_class, source_type,
          is_material, reliance_role, verification_status, availability_status,
          origin_attribution, limitations, report_local_source_id,
          external_reference, submitted_by_id, observed_at,
          minimal_historical_representation, integrity_algorithm, integrity_digest
        ) VALUES (
          :id, :report_id, 0, 'external_or_human_material', 'external_or_human', true,
          'technical basis', 'verified', 'available', 'Human', '[]',
          :local_id, :external_reference, :submitted_by_id, :observed_at,
          CAST(:minimal AS json), 'sha256', :integrity_digest
        )
    """), {
        "id": provenance["entry_id"], "report_id": report_id,
        "local_id": provenance["locator"]["report_local_source_id"],
        "external_reference": provenance["locator"]["external_reference"],
        "submitted_by_id": provenance["locator"]["submitted_by_id"],
        "observed_at": accepted_at,
        "minimal": json.dumps(provenance["locator"]["minimal_representation"]),
        "integrity_digest": provenance["integrity_digest"],
    })


def test_runtime_and_schema_owner_are_distinct_and_restricted() -> None:
    runtime = _runtime_engine()
    try:
        with runtime.connect() as connection:
            role = connection.execute(text("SELECT current_user, rolsuper, rolbypassrls, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname=current_user")).one()
            assert role[0] == "satco_runtime"
            assert role[1:] == (False, False, False, False)
            assert connection.execute(text("SELECT current_user <> :owner"), {"owner": owner_engine.url.username}).scalar_one()
        validate_technical_report_runtime_boundary(runtime, migration_database_url=str(owner_engine.url))
    finally:
        runtime.dispose()


def test_exact_runtime_grant_matrix() -> None:
    runtime = _runtime_engine()
    try:
        with runtime.connect() as connection:
            table_grants = {
                (row.table_name, row.privilege_type)
                for row in connection.execute(text("""
                    SELECT table_name, privilege_type
                    FROM information_schema.role_table_grants
                    WHERE grantee=current_user AND table_name IN (
                      'technical_reports','technical_report_provenance_entries',
                      'technical_report_outbox','technical_report_idempotency','audit_logs')
                """)).all()
            }
            assert not ({("technical_reports", "DELETE"), ("technical_report_outbox", "DELETE"),
                         ("technical_report_idempotency", "DELETE"), ("audit_logs", "UPDATE"),
                         ("audit_logs", "DELETE")} & table_grants)
            outbox_updates = set(connection.execute(text("""
                SELECT column_name FROM information_schema.role_column_grants
                WHERE grantee=current_user AND table_name='technical_report_outbox'
                  AND privilege_type='UPDATE'
            """)).scalars())
            idempotency_updates = set(connection.execute(text("""
                SELECT column_name FROM information_schema.role_column_grants
                WHERE grantee=current_user AND table_name='technical_report_idempotency'
                  AND privilege_type='UPDATE'
            """)).scalars())
            assert outbox_updates == {"published_at"}
            assert idempotency_updates == {"status", "aggregate_id", "result", "updated_at"}
            assert {grant for grant in table_grants if grant[0] == "audit_logs"} == {
                ("audit_logs", "SELECT"), ("audit_logs", "INSERT")
            }
    finally:
        runtime.dispose()


def test_allowed_and_prohibited_command_and_audit_operations() -> None:
    runtime = _runtime_engine()
    report_id = outbox_id = idempotency_row_id = audit_id = None
    scope = None
    try:
        with runtime.begin() as connection:
            report_id, _, scope = _insert_draft(connection)
            outbox_id = uuid4()
            connection.execute(text("""
                INSERT INTO technical_report_outbox (
                  id,event_id,aggregate_id,aggregate_version,event_type,
                  schema_version,payload,occurred_at
                ) VALUES (:id,:event_id,:report_id,1,'draft_created',1,
                  CAST('{}' AS json),now())
            """), {"id": outbox_id, "event_id": uuid4(), "report_id": report_id})
            connection.execute(text("UPDATE technical_report_outbox SET published_at=now() WHERE id=:id"), {"id": outbox_id})
            idempotency_row_id = uuid4()
            connection.execute(text("""
                INSERT INTO technical_report_idempotency (
                  id,organization_id,actor_id,command_type,idempotency_id,
                  request_fingerprint,status
                ) VALUES (:id,:organization_id,:actor_id,'create',:key,:fingerprint,'pending')
            """), {"id": idempotency_row_id, "organization_id": scope["organization_id"],
                    "actor_id": scope["owner_id"], "key": uuid4(), "fingerprint": "a" * 64})
            connection.execute(text("""
                UPDATE technical_report_idempotency SET status='completed',
                  aggregate_id=:report_id,result=CAST(:result AS json),updated_at=now()
                WHERE id=:id
            """), {"report_id": report_id, "result": json.dumps({"ok": True}), "id": idempotency_row_id})
            audit_id = connection.execute(text("""
                INSERT INTO audit_logs(user_id,action,entity,entity_uuid,details,created_at)
                VALUES (:actor_id,'PATCH032_TEST','TECHNICAL_REPORT',:report_id,CAST('{}' AS json),now())
                RETURNING id
            """), {"actor_id": scope["owner_id"], "report_id": report_id}).scalar_one()

        with pytest.raises(DBAPIError), runtime.begin() as connection:
            connection.execute(text("UPDATE technical_report_outbox SET payload=CAST(:payload AS json) WHERE id=:id"), {"payload": json.dumps({"changed": True}), "id": outbox_id})
        with pytest.raises(DBAPIError), runtime.begin() as connection:
            connection.execute(text("UPDATE technical_report_idempotency SET request_fingerprint=:value WHERE id=:id"), {"value": "b" * 64, "id": idempotency_row_id})
        with pytest.raises(DBAPIError), runtime.begin() as connection:
            connection.execute(text("UPDATE audit_logs SET action='CHANGED' WHERE id=:id"), {"id": audit_id})
        with pytest.raises(DBAPIError), runtime.begin() as connection:
            connection.execute(text("DELETE FROM audit_logs WHERE id=:id"), {"id": audit_id})
    finally:
        runtime.dispose()
        with owner_engine.begin() as connection:
            if audit_id is not None:
                connection.execute(text("DELETE FROM audit_logs WHERE id=:id"), {"id": audit_id})
            if outbox_id is not None:
                connection.execute(text("DELETE FROM technical_report_outbox WHERE id=:id"), {"id": outbox_id})
            if idempotency_row_id is not None:
                connection.execute(text("DELETE FROM technical_report_idempotency WHERE id=:id"), {"id": idempotency_row_id})
            if report_id is not None:
                connection.execute(text("DELETE FROM technical_reports WHERE id=:id"), {"id": report_id})
        _cleanup_scope(scope)


def test_runtime_configuration_cannot_consume_migration_url(monkeypatch) -> None:
    assert "ALEMBIC_DATABASE_URL" not in Settings.model_fields
    monkeypatch.setenv("DATABASE_URL", str(owner_engine.url))
    monkeypatch.setenv("DATABASE_HOST", owner_engine.url.host or "postgres")
    monkeypatch.setenv("DATABASE_PORT", str(owner_engine.url.port or 5432))
    monkeypatch.setenv("DATABASE_USER", "satco_runtime")
    monkeypatch.setenv("DATABASE_PASSWORD", os.getenv("TEST_RUNTIME_DATABASE_PASSWORD", "satco_runtime_test_password"))
    monkeypatch.setenv("DATABASE_NAME", owner_engine.url.database)
    assert "satco_runtime" in runtime_database_url()
    assert str(owner_engine.url) != runtime_database_url()


@pytest.mark.parametrize("flag", [None, "false", "true"])
def test_alembic_rejects_runtime_identity_unconditionally(flag: str | None) -> None:
    environment = os.environ.copy()
    environment["ALEMBIC_DATABASE_URL"] = str(owner_engine.url.set(username="satco_runtime", password=os.getenv("TEST_RUNTIME_DATABASE_PASSWORD", "satco_runtime_test_password")))
    environment["DATABASE_USER"] = "satco_runtime"
    environment["RUNTIME_DATABASE_ROLE"] = "satco_runtime"
    if flag is None:
        environment.pop("TECHNICAL_REPORT_PERSISTENCE_ENABLED", None)
    else:
        environment["TECHNICAL_REPORT_PERSISTENCE_ENABLED"] = flag
    result = subprocess.run(
        ["alembic", "current"], cwd=Path(__file__).resolve().parents[1],
        env=environment, capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "migration role must differ from the runtime role" in result.stderr


def test_runtime_can_accept_once_but_cannot_mutate_accepted_state_or_provenance() -> None:
    runtime = _runtime_engine()
    report_id = None
    scope = None
    try:
        with runtime.begin() as connection:
            report_id, revision_id, scope = _insert_draft(connection)
            snapshot, snapshot_digest, accepted_at, provenance = _accepted_state(report_id, revision_id, scope)
            provenance_id = provenance["entry_id"]
            connection.execute(text("""
                INSERT INTO technical_report_provenance_entries (
                  id, technical_report_id, ordinal, source_class, source_type,
                  is_material, reliance_role, verification_status, availability_status,
                  origin_attribution, limitations, report_local_source_id,
                  external_reference, submitted_by_id, observed_at,
                  minimal_historical_representation, integrity_algorithm, integrity_digest
                ) VALUES (
                  :id, :report_id, 0, 'external_or_human_material', 'external_or_human', true,
                  'technical basis', 'verified', 'available', 'Human', '[]',
                  :local_id, :external_reference, :submitted_by_id, :observed_at,
                  CAST(:minimal AS json), 'sha256', :integrity_digest
                )
            """), {"id": provenance_id, "report_id": report_id,
                    "local_id": provenance["locator"]["report_local_source_id"],
                    "external_reference": provenance["locator"]["external_reference"],
                    "submitted_by_id": provenance["locator"]["submitted_by_id"],
                    "observed_at": accepted_at,
                    "minimal": json.dumps(provenance["locator"]["minimal_representation"]),
                    "integrity_digest": provenance["integrity_digest"]})
            connection.execute(text("""
                UPDATE technical_reports SET lifecycle='accepted', version=2,
                  accepted_snapshot=CAST(:snapshot AS jsonb), accepted_snapshot_digest=:digest,
                  accepted_by_id=:owner_id, accepted_at=:accepted_at,
                  accepted_draft_revision_id=:revision_id,
                  accepted_aggregate_version=2, updated_at=now()
                WHERE id=:report_id AND lifecycle='draft' AND version=1
            """), {"snapshot": json.dumps(snapshot), "digest": snapshot_digest,
                    "owner_id": scope["owner_id"], "accepted_at": accepted_at,
                    "revision_id": revision_id, "report_id": report_id})

        with runtime.connect() as connection:
            stored = connection.execute(text("SELECT accepted_snapshot, accepted_snapshot_digest, accepted_by_id, accepted_at, version FROM technical_reports WHERE id=:id"), {"id": report_id}).mappings().one()
            assert stored["accepted_snapshot"] == snapshot
            assert hashlib.sha256(_canonical(stored["accepted_snapshot"])).hexdigest() == stored["accepted_snapshot_digest"]
            accepted_state = dict(stored)

        with pytest.raises(DBAPIError), runtime.begin() as connection:
            connection.execute(text("UPDATE technical_reports SET conclusions='changed' WHERE id=:id"), {"id": report_id})
        with pytest.raises(DBAPIError), runtime.begin() as connection:
            connection.execute(text("UPDATE technical_report_provenance_entries SET origin_attribution='changed' WHERE technical_report_id=:id"), {"id": report_id})
        with pytest.raises(DBAPIError), runtime.begin() as connection:
            connection.execute(text("DELETE FROM technical_report_provenance_entries WHERE technical_report_id=:id"), {"id": report_id})
        with pytest.raises(DBAPIError), runtime.begin() as connection:
            connection.execute(text("DELETE FROM technical_reports WHERE id=:id"), {"id": report_id})
        with runtime.connect() as connection:
            assert dict(connection.execute(text("SELECT accepted_snapshot, accepted_snapshot_digest, accepted_by_id, accepted_at, version FROM technical_reports WHERE id=:id"), {"id": report_id}).mappings().one()) == accepted_state
    finally:
        runtime.dispose()
        if report_id is not None:
            with owner_engine.begin() as connection:
                connection.exec_driver_sql("ALTER TABLE technical_report_provenance_entries DISABLE TRIGGER trg_technical_report_provenance_accepted_immutable")
                connection.exec_driver_sql("ALTER TABLE technical_reports DISABLE TRIGGER trg_technical_reports_accepted_immutable")
                connection.execute(text("DELETE FROM technical_report_provenance_entries WHERE technical_report_id=:id"), {"id": report_id})
                connection.execute(text("DELETE FROM technical_reports WHERE id=:id"), {"id": report_id})
                connection.exec_driver_sql("ALTER TABLE technical_reports ENABLE TRIGGER trg_technical_reports_accepted_immutable")
                connection.exec_driver_sql("ALTER TABLE technical_report_provenance_entries ENABLE TRIGGER trg_technical_report_provenance_accepted_immutable")
        _cleanup_scope(scope)


@pytest.mark.parametrize("case", ["incomplete", "bad_digest", "digest_mismatch"])
def test_terminal_acceptance_rejects_invalid_snapshot(case: str) -> None:
    runtime = _runtime_engine()
    report_id = None
    scope = None
    try:
        with runtime.begin() as connection:
            report_id, revision_id, scope = _insert_draft(connection)
        snapshot, snapshot_digest, accepted_at, _ = _accepted_state(report_id, revision_id, scope)
        if case == "incomplete":
            snapshot = {"schema": 1}
            snapshot_digest = hashlib.sha256(_canonical(snapshot)).hexdigest()
        elif case == "bad_digest":
            snapshot_digest = "Z" * 64
        else:
            snapshot_digest = "0" * 64
        with pytest.raises(DBAPIError), runtime.begin() as connection:
            connection.execute(text("""
                UPDATE technical_reports SET lifecycle='accepted', version=2,
                  accepted_snapshot=CAST(:snapshot AS jsonb), accepted_snapshot_digest=:digest,
                  accepted_by_id=:owner_id, accepted_at=:accepted_at,
                  accepted_draft_revision_id=:revision_id,
                  accepted_aggregate_version=2, updated_at=now()
                WHERE id=:id
            """), {"snapshot": json.dumps(snapshot), "digest": snapshot_digest,
                    "owner_id": scope["owner_id"], "accepted_at": accepted_at,
                    "revision_id": revision_id, "id": report_id})
        with runtime.connect() as connection:
            state = connection.execute(text("SELECT lifecycle, accepted_snapshot FROM technical_reports WHERE id=:id"), {"id": report_id}).one()
            assert state == ("draft", None)
    finally:
        runtime.dispose()
        if report_id is not None:
            with owner_engine.begin() as connection:
                connection.execute(text("DELETE FROM technical_reports WHERE id=:id"), {"id": report_id})
        _cleanup_scope(scope)


@pytest.mark.parametrize("defect", [
    "invalid_content", "invalid_qualification", "invalid_revision", "invalid_acceptor",
    "invalid_timestamp", "invalid_provenance", "incomplete_fallback",
    "source_basis_mismatch", "extra_nested_field", "malformed_scope",
    "oversized_content", "empty_normalized_content", "content_control_character",
    "overlong_assumption", "invalid_assumption_member", "invalid_conclusion",
    "invalid_recommendation_member", "qualification_control_character",
    "impossible_acceptance_timestamp", "noncanonical_acceptance_timestamp",
    "invalid_lineage", "invalid_project_representation", "zero_revision",
    "qualification_extra_field", "overlong_locator", "locator_control_character",
    "invalid_locator_optional", "invalid_locator_timestamp", "non_nfc_content",
])
def test_direct_sql_acceptance_rejects_invalid_nested_snapshot_atomically(defect: str) -> None:
    runtime = _runtime_engine()
    report_id = None
    scope = None
    try:
        with runtime.begin() as connection:
            report_id, revision_id, scope = _insert_draft(connection)
        snapshot, _, accepted_at, provenance = _accepted_state(report_id, revision_id, scope)
        with runtime.begin() as connection:
            _insert_external_snapshot_provenance(connection, report_id, provenance, accepted_at)
        if defect == "invalid_content":
            snapshot["content"]["technical_content"] = False
        elif defect == "invalid_qualification":
            snapshot["qualification"]["is_preliminary"] = "false"
        elif defect == "invalid_revision":
            snapshot["accepted_draft_revision"]["revision_number"] = "1"
        elif defect == "invalid_acceptor":
            snapshot["accepted_by_id"] = "1"
        elif defect == "invalid_timestamp":
            snapshot["accepted_at"] = "2026-08-09T00:00:00"
        elif defect == "invalid_provenance":
            snapshot["provenance"] = [{"garbage": True}]
        elif defect == "incomplete_fallback":
            capture_basis = _historical_basis("universal_capture", scope)
            entry = snapshot["provenance"][0]
            entry.update(
                source_class="canonical_material", source_type="universal_capture",
                owning_capability="universal_capture", locator={"basis_schema_version": 1},
            )
            entry["integrity_digest"] = hashlib.sha256(_canonical(entry["locator"])).hexdigest()
        elif defect == "source_basis_mismatch":
            basis = _historical_basis("evidence", scope)
            entry = snapshot["provenance"][0]
            entry.update(
                source_class="canonical_material", source_type="universal_capture",
                owning_capability="universal_capture", locator=basis,
            )
            entry["integrity_digest"] = hashlib.sha256(_canonical(basis)).hexdigest()
        elif defect == "extra_nested_field":
            snapshot["content"]["undeclared"] = "forbidden"
        elif defect == "malformed_scope":
            snapshot["workspace_id"] = {"invalid": True}
        elif defect == "oversized_content":
            snapshot["content"]["technical_content"] = "x" * 10001
        elif defect == "empty_normalized_content":
            snapshot["content"]["technical_content"] = "   "
        elif defect == "content_control_character":
            snapshot["content"]["technical_content"] = "invalid\x01content"
        elif defect == "overlong_assumption":
            snapshot["content"]["assumptions"] = ["x" * 10001]
        elif defect == "invalid_assumption_member":
            snapshot["content"]["assumptions"] = [1]
        elif defect == "invalid_conclusion":
            snapshot["content"]["conclusions"] = " conclusion "
        elif defect == "invalid_recommendation_member":
            snapshot["content"]["recommendations"] = [None]
        elif defect == "qualification_control_character":
            snapshot["qualification"] = {
                "is_preliminary": True, "evidence_deficiencies": ["bad\x01value"],
                "unresolved_issues": [], "follow_up_requirements": [],
            }
        elif defect == "impossible_acceptance_timestamp":
            snapshot["accepted_at"] = "2026-02-30T12:00:00.000000Z"
        elif defect == "noncanonical_acceptance_timestamp":
            snapshot["accepted_at"] = "2026-08-09T12:00:00Z"
        elif defect == "invalid_lineage":
            snapshot["predecessor_report_id"] = "NOT-A-UUID"
        elif defect == "invalid_project_representation":
            snapshot["project_id"] = "1"
        elif defect == "zero_revision":
            snapshot["accepted_draft_revision"]["revision_number"] = 0
        elif defect == "qualification_extra_field":
            snapshot["qualification"]["undeclared"] = True
        elif defect == "overlong_locator":
            snapshot["provenance"][0]["locator"]["external_reference"] = "x" * 513
        elif defect == "locator_control_character":
            snapshot["provenance"][0]["locator"]["external_reference"] = "bad\x01reference"
        elif defect == "invalid_locator_optional":
            snapshot["provenance"][0]["locator"]["submitted_by_id"] = "1"
        elif defect == "invalid_locator_timestamp":
            snapshot["provenance"][0]["locator"]["observed_at"] = "2026-02-30T12:00:00.000000Z"
        else:
            snapshot["content"]["technical_content"] = "e\u0301"
        digest = hashlib.sha256(_canonical(snapshot)).hexdigest()
        with pytest.raises(Exception):
            validate_accepted_snapshot_payload(snapshot, digest)
        with pytest.raises(DBAPIError), runtime.begin() as connection:
            connection.execute(text("""
                UPDATE technical_reports SET lifecycle='accepted', version=2,
                  accepted_snapshot=CAST(:snapshot AS jsonb), accepted_snapshot_digest=:digest,
                  accepted_by_id=:owner_id, accepted_at=:accepted_at,
                  accepted_draft_revision_id=:revision_id,
                  accepted_aggregate_version=2, updated_at=now()
                WHERE id=:id
            """), {"snapshot": json.dumps(snapshot), "digest": digest,
                    "owner_id": scope["owner_id"], "accepted_at": accepted_at,
                    "revision_id": revision_id, "id": report_id})
        with runtime.connect() as connection:
            state = connection.execute(text("""
                SELECT lifecycle, accepted_snapshot, accepted_snapshot_digest,
                       accepted_by_id, accepted_at, accepted_draft_revision_id,
                       accepted_aggregate_version, draft_content, version
                FROM technical_reports WHERE id=:id
            """), {"id": report_id}).one()
            assert state == ("draft", None, None, None, None, None, None, "draft", 1)
    finally:
        runtime.dispose()
        if report_id is not None:
            with owner_engine.begin() as connection:
                connection.execute(text("DELETE FROM technical_report_provenance_entries WHERE technical_report_id=:id"), {"id": report_id})
                connection.execute(text("DELETE FROM technical_reports WHERE id=:id"), {"id": report_id})
        _cleanup_scope(scope)


@pytest.mark.parametrize("defect", [
    "oversized_content", "empty_content", "content_control", "overlong_assumption",
    "invalid_assumption_type", "non_normalized_conclusion", "qualification_control",
])
def test_coherent_invalid_semantic_state_cannot_bypass_acceptance_atomically(defect: str) -> None:
    runtime = _runtime_engine()
    report_id = None
    scope = None
    try:
        with runtime.begin() as connection:
            report_id, revision_id, scope = _insert_draft(connection)
        snapshot, _, accepted_at, provenance = _accepted_state(report_id, revision_id, scope)
        with runtime.begin() as connection:
            _insert_external_snapshot_provenance(connection, report_id, provenance, accepted_at)
        if defect == "oversized_content":
            snapshot["content"]["technical_content"] = "x" * 10001
        elif defect == "empty_content":
            snapshot["content"]["technical_content"] = "   "
        elif defect == "content_control":
            snapshot["content"]["technical_content"] = "bad\x01content"
        elif defect == "overlong_assumption":
            snapshot["content"]["assumptions"] = ["x" * 10001]
        elif defect == "invalid_assumption_type":
            snapshot["content"]["assumptions"] = [1]
        elif defect == "non_normalized_conclusion":
            snapshot["content"]["conclusions"] = " conclusion "
        else:
            snapshot["qualification"] = {
                "is_preliminary": True, "evidence_deficiencies": ["bad\x01value"],
                "unresolved_issues": [], "follow_up_requirements": [],
            }
        digest = hashlib.sha256(_canonical(snapshot)).hexdigest()
        with pytest.raises(Exception):
            validate_accepted_snapshot_payload(snapshot, digest)
        with runtime.connect() as connection:
            before = connection.execute(text("""
                SELECT lifecycle, accepted_snapshot, accepted_snapshot_digest, accepted_by_id,
                       accepted_at, accepted_draft_revision_id, accepted_aggregate_version,
                       draft_content, assumptions, conclusions, version, updated_at
                FROM technical_reports WHERE id=:id
            """), {"id": report_id}).one()
            provenance_before = connection.execute(text(
                "SELECT count(*) FROM technical_report_provenance_entries WHERE technical_report_id=:id"
            ), {"id": report_id}).scalar_one()
        with pytest.raises(DBAPIError), runtime.begin() as connection:
            connection.execute(text("""
                UPDATE technical_reports SET lifecycle='accepted', version=2,
                  draft_content=:technical_content, assumptions=CAST(:assumptions AS json),
                  conclusions=:conclusions, is_preliminary=:is_preliminary,
                  evidence_deficiencies=CAST(:evidence_deficiencies AS json),
                  unresolved_issues=CAST(:unresolved_issues AS json),
                  follow_up_requirements=CAST(:follow_up_requirements AS json),
                  accepted_snapshot=CAST(:snapshot AS jsonb), accepted_snapshot_digest=:digest,
                  accepted_by_id=:owner_id, accepted_at=:accepted_at,
                  accepted_draft_revision_id=:revision_id,
                  accepted_aggregate_version=2, updated_at=now()
                WHERE id=:id
            """), {
                "technical_content": snapshot["content"]["technical_content"],
                "assumptions": json.dumps(snapshot["content"]["assumptions"]),
                "conclusions": snapshot["content"]["conclusions"],
                "is_preliminary": snapshot["qualification"]["is_preliminary"],
                "evidence_deficiencies": json.dumps(snapshot["qualification"]["evidence_deficiencies"]),
                "unresolved_issues": json.dumps(snapshot["qualification"]["unresolved_issues"]),
                "follow_up_requirements": json.dumps(snapshot["qualification"]["follow_up_requirements"]),
                "snapshot": json.dumps(snapshot), "digest": digest,
                "owner_id": scope["owner_id"], "accepted_at": accepted_at,
                "revision_id": revision_id, "id": report_id,
            })
        with runtime.connect() as connection:
            after = connection.execute(text("""
                SELECT lifecycle, accepted_snapshot, accepted_snapshot_digest, accepted_by_id,
                       accepted_at, accepted_draft_revision_id, accepted_aggregate_version,
                       draft_content, assumptions, conclusions, version, updated_at
                FROM technical_reports WHERE id=:id
            """), {"id": report_id}).one()
            provenance_after = connection.execute(text(
                "SELECT count(*) FROM technical_report_provenance_entries WHERE technical_report_id=:id"
            ), {"id": report_id}).scalar_one()
            assert after == before
            assert provenance_after == provenance_before
    finally:
        runtime.dispose()
        if report_id is not None:
            with owner_engine.begin() as connection:
                connection.execute(text("DELETE FROM technical_report_provenance_entries WHERE technical_report_id=:id"), {"id": report_id})
                connection.execute(text("DELETE FROM technical_reports WHERE id=:id"), {"id": report_id})
        _cleanup_scope(scope)


@pytest.mark.parametrize("case", [
    "content_leading_tab", "content_trailing_tab", "content_leading_nbsp",
    "content_trailing_nbsp", "qualification_tab", "qualification_nbsp",
    "provenance_tab", "provenance_nbsp", "locator_tab", "locator_nbsp",
])
def test_coherent_boundary_whitespace_acceptance_is_rejected_atomically(case: str) -> None:
    runtime = _runtime_engine()
    report_id = None
    scope = None
    try:
        with runtime.begin() as connection:
            report_id, revision_id, scope = _insert_draft(connection)
        snapshot, _, accepted_at, provenance = _accepted_state(report_id, revision_id, scope)
        with runtime.begin() as connection:
            _insert_external_snapshot_provenance(connection, report_id, provenance, accepted_at)

        if case == "content_leading_tab":
            snapshot["content"]["technical_content"] = "\tdraft"
        elif case == "content_trailing_tab":
            snapshot["content"]["technical_content"] = "draft\t"
        elif case == "content_leading_nbsp":
            snapshot["content"]["technical_content"] = "\u00a0draft"
        elif case == "content_trailing_nbsp":
            snapshot["content"]["technical_content"] = "draft\u00a0"
        elif case == "qualification_tab":
            snapshot["qualification"] = {
                "is_preliminary": True, "evidence_deficiencies": ["\tdeficiency"],
                "unresolved_issues": [], "follow_up_requirements": [],
            }
        elif case == "qualification_nbsp":
            snapshot["qualification"] = {
                "is_preliminary": True, "evidence_deficiencies": ["deficiency\u00a0"],
                "unresolved_issues": [], "follow_up_requirements": [],
            }
        elif case == "provenance_tab":
            snapshot["provenance"][0]["reliance_role"] = "\ttechnical basis"
        elif case == "provenance_nbsp":
            snapshot["provenance"][0]["origin_attribution"] = "Human\u00a0"
        elif case == "locator_tab":
            snapshot["provenance"][0]["locator"]["external_reference"] = "\tfield-note-1"
        else:
            snapshot["provenance"][0]["locator"]["minimal_representation"] = "verified field observation\u00a0"

        locator = snapshot["provenance"][0]["locator"]
        if case.startswith("locator_"):
            snapshot["provenance"][0]["integrity_digest"] = hashlib.sha256(_canonical(locator)).hexdigest()
        digest = hashlib.sha256(_canonical(snapshot)).hexdigest()
        with pytest.raises(Exception):
            validate_accepted_snapshot_payload(snapshot, digest)

        with runtime.connect() as connection:
            before = connection.execute(text("""
                SELECT lifecycle, accepted_snapshot, accepted_snapshot_digest, accepted_by_id,
                       accepted_at, accepted_draft_revision_id, accepted_aggregate_version,
                       draft_content, evidence_deficiencies, version, updated_at
                FROM technical_reports WHERE id=:id
            """), {"id": report_id}).one()
            provenance_before = connection.execute(text("""
                SELECT reliance_role, origin_attribution, external_reference,
                       minimal_historical_representation, integrity_digest
                FROM technical_report_provenance_entries WHERE technical_report_id=:id
            """), {"id": report_id}).one()

        with pytest.raises(DBAPIError), runtime.begin() as connection:
            if case.startswith("provenance_") or case.startswith("locator_"):
                connection.execute(text("""
                    UPDATE technical_report_provenance_entries SET
                      reliance_role=:reliance_role,
                      origin_attribution=:origin_attribution,
                      external_reference=:external_reference,
                      minimal_historical_representation=CAST(:minimal AS json),
                      integrity_digest=:integrity_digest
                    WHERE technical_report_id=:id
                """), {
                    "reliance_role": snapshot["provenance"][0]["reliance_role"],
                    "origin_attribution": snapshot["provenance"][0]["origin_attribution"],
                    "external_reference": locator["external_reference"],
                    "minimal": json.dumps(locator["minimal_representation"]),
                    "integrity_digest": snapshot["provenance"][0]["integrity_digest"],
                    "id": report_id,
                })
            connection.execute(text("""
                UPDATE technical_reports SET lifecycle='accepted', version=2,
                  draft_content=:technical_content,
                  is_preliminary=:is_preliminary,
                  evidence_deficiencies=CAST(:evidence_deficiencies AS json),
                  accepted_snapshot=CAST(:snapshot AS jsonb),
                  accepted_snapshot_digest=:digest, accepted_by_id=:owner_id,
                  accepted_at=:accepted_at, accepted_draft_revision_id=:revision_id,
                  accepted_aggregate_version=2, updated_at=now()
                WHERE id=:id
            """), {
                "technical_content": snapshot["content"]["technical_content"],
                "is_preliminary": snapshot["qualification"]["is_preliminary"],
                "evidence_deficiencies": json.dumps(snapshot["qualification"]["evidence_deficiencies"]),
                "snapshot": json.dumps(snapshot), "digest": digest,
                "owner_id": scope["owner_id"], "accepted_at": accepted_at,
                "revision_id": revision_id, "id": report_id,
            })

        with runtime.connect() as connection:
            after = connection.execute(text("""
                SELECT lifecycle, accepted_snapshot, accepted_snapshot_digest, accepted_by_id,
                       accepted_at, accepted_draft_revision_id, accepted_aggregate_version,
                       draft_content, evidence_deficiencies, version, updated_at
                FROM technical_reports WHERE id=:id
            """), {"id": report_id}).one()
            provenance_after = connection.execute(text("""
                SELECT reliance_role, origin_attribution, external_reference,
                       minimal_historical_representation, integrity_digest
                FROM technical_report_provenance_entries WHERE technical_report_id=:id
            """), {"id": report_id}).one()
            assert after == before
            assert provenance_after == provenance_before
    finally:
        runtime.dispose()
        if report_id is not None:
            with owner_engine.begin() as connection:
                connection.execute(text("DELETE FROM technical_report_provenance_entries WHERE technical_report_id=:id"), {"id": report_id})
                connection.execute(text("DELETE FROM technical_reports WHERE id=:id"), {"id": report_id})
        _cleanup_scope(scope)


def test_direct_insert_cannot_create_terminal_report() -> None:
    runtime = _runtime_engine()
    with runtime.connect() as connection:
        scope = _scope(connection)
    try:
        report_id, revision_id = uuid4(), uuid4()
        snapshot, digest, accepted_at, _ = _accepted_state(report_id, revision_id, scope)
        with pytest.raises(DBAPIError), runtime.begin() as connection:
            connection.execute(text("""
                INSERT INTO technical_reports (
                  id, organization_id, workspace_id, project_id, owner_id, purpose,
                  engineering_scope, draft_content, assumptions, uncertainty,
                  limitations, conclusions, recommendations, is_preliminary,
                  evidence_deficiencies, unresolved_issues, follow_up_requirements,
                  draft_revision_id, draft_revision_number, lifecycle, version,
                  accepted_snapshot, accepted_snapshot_digest, accepted_by_id,
                  accepted_at, accepted_draft_revision_id, accepted_aggregate_version
                ) VALUES (
                  :id,:organization_id,:workspace_id,:project_id,:owner_id,
                  'engineering_analysis','scope','draft','[]','uncertainty','[]',
                  'conclusion','[]',false,'[]','[]','[]',:revision_id,1,'accepted',2,
                  CAST(:snapshot AS jsonb),:digest,:owner_id,:accepted_at,:revision_id,2
                )
            """), {**scope, "id": report_id, "revision_id": revision_id,
                    "snapshot": json.dumps(snapshot), "digest": digest,
                    "accepted_at": accepted_at})
    finally:
        runtime.dispose()
        _cleanup_scope(scope)


@pytest.mark.parametrize("case", ["canonical_native", "canonical_fallback", "missing_fallback", "bad_digest", "external_missing", "standard_missing", "cross_shape"])
def test_source_aware_provenance_constraints(case: str) -> None:
    runtime = _runtime_engine()
    report_id = None
    scope = None
    try:
        with runtime.begin() as connection:
            report_id, _, scope = _insert_draft(connection)
        values = dict(
            id=uuid4(), report_id=report_id, source_class="canonical_material",
            source_type="universal_capture", is_material=True,
            owning_capability="universal_capture", capture_id=uuid4(), capture_version=1,
            canonical_snapshot_id=uuid4(), minimal=None, algorithm="sha256",
            digest="a" * 64, report_local_source_id=None, external_reference=None,
            standard_identity=None, issuing_authority=None, edition=None,
            clause_or_location=None,
        )
        if case == "canonical_fallback":
            basis = _historical_basis("universal_capture", scope)
            values.update(
                canonical_snapshot_id=None, minimal=json.dumps(basis),
                digest=hashlib.sha256(_canonical(basis)).hexdigest(),
                capture_id=basis["capture_id"], capture_version=basis["source_version"],
            )
        elif case == "missing_fallback":
            values.update(canonical_snapshot_id=None)
        elif case == "bad_digest":
            values.update(digest="A" * 64)
        elif case == "external_missing":
            values.update(source_class="external_or_human_material", source_type="external_or_human",
                          owning_capability=None, capture_id=None, capture_version=None,
                          canonical_snapshot_id=None, report_local_source_id=uuid4(),
                          external_reference="field-note", minimal=None)
        elif case == "standard_missing":
            values.update(source_class="standards_material", source_type="standard",
                          owning_capability=None, capture_id=None, capture_version=None,
                          canonical_snapshot_id=None, standard_identity="STD", issuing_authority="AUTH",
                          edition="1", clause_or_location="1.1", minimal=None)
        elif case == "cross_shape":
            values.update(report_local_source_id=uuid4(), external_reference="forbidden")
        statement = text("""
            INSERT INTO technical_report_provenance_entries (
              id, technical_report_id, ordinal, source_class, source_type,
              is_material, owning_capability, reliance_role, verification_status,
              availability_status, origin_attribution, limitations, integrity_algorithm,
              integrity_digest, minimal_historical_representation, capture_id,
              capture_version, canonical_snapshot_id, report_local_source_id,
              external_reference, standard_identity, issuing_authority, edition,
              clause_or_location
            ) VALUES (
              :id,:report_id,0,:source_class,:source_type,:is_material,
              :owning_capability,'basis','verified','available','Human','[]',
              :algorithm,:digest,CAST(:minimal AS json),:capture_id,:capture_version,
              :canonical_snapshot_id,:report_local_source_id,:external_reference,
              :standard_identity,:issuing_authority,:edition,:clause_or_location
            )
        """)
        if case in {"canonical_native", "canonical_fallback"}:
            with runtime.begin() as connection:
                connection.execute(statement, values)
        else:
            with pytest.raises(DBAPIError), runtime.begin() as connection:
                connection.execute(statement, values)
    finally:
        runtime.dispose()
        if report_id is not None:
            with owner_engine.begin() as connection:
                connection.execute(text("DELETE FROM technical_report_provenance_entries WHERE technical_report_id=:id"), {"id": report_id})
                connection.execute(text("DELETE FROM technical_reports WHERE id=:id"), {"id": report_id})
        _cleanup_scope(scope)


@pytest.mark.parametrize("source_type", [
    "universal_capture", "evidence", "engineering_object", "engineering_relationship",
])
def test_complete_closed_historical_fallback_is_persisted(source_type: str) -> None:
    runtime = _runtime_engine()
    report_id = None
    scope = None
    try:
        with runtime.begin() as connection:
            report_id, _, scope = _insert_draft(connection)
            basis = _historical_basis(source_type, scope)
            connection.execute(_INSERT_CANONICAL_FALLBACK, _fallback_values(source_type, report_id, scope, basis))
            stored = connection.execute(text(
                "SELECT minimal_historical_representation FROM technical_report_provenance_entries "
                "WHERE technical_report_id=:id"
            ), {"id": report_id}).scalar_one()
            assert stored == basis
    finally:
        runtime.dispose()
        if report_id is not None:
            with owner_engine.begin() as connection:
                connection.execute(text("DELETE FROM technical_report_provenance_entries WHERE technical_report_id=:id"), {"id": report_id})
                connection.execute(text("DELETE FROM technical_reports WHERE id=:id"), {"id": report_id})
        _cleanup_scope(scope)


@pytest.mark.parametrize("source_type", [
    "universal_capture", "evidence", "engineering_object", "engineering_relationship",
])
@pytest.mark.parametrize("defect", [
    "missing", "extra", "wrong_type", "invalid_enum", "invalid_version",
    "wrong_source_basis", "incomplete", "malformed_nested",
])
def test_closed_historical_fallback_rejects_every_invalid_shape(source_type: str, defect: str) -> None:
    runtime = _runtime_engine()
    report_id = None
    scope = None
    try:
        with runtime.begin() as connection:
            report_id, _, scope = _insert_draft(connection)
        basis = _historical_basis(source_type, scope)
        if defect == "missing":
            basis.pop("organization_id")
        elif defect == "extra":
            basis["undeclared"] = True
        elif defect == "wrong_type":
            basis["creator_id"] = "1"
        elif defect == "invalid_enum":
            enum_field = {
                "universal_capture": "source_kind", "evidence": "source_standing",
                "engineering_object": "family", "engineering_relationship": "relationship_family",
            }[source_type]
            basis[enum_field] = "invalid"
        elif defect == "invalid_version":
            basis["source_version"] = 0
        elif defect == "wrong_source_basis":
            other = "evidence" if source_type != "evidence" else "universal_capture"
            basis = _historical_basis(other, scope)
        elif defect == "incomplete":
            basis = {"basis_schema_version": 1}
        else:
            nested_field = "evidence_references" if source_type == "engineering_relationship" else "organization_id"
            basis[nested_field] = {} if nested_field == "evidence_references" else {"invalid": True}
        values = _fallback_values(source_type, report_id, scope, _historical_basis(source_type, scope))
        values.update(minimal=json.dumps(basis), digest=hashlib.sha256(_canonical(basis)).hexdigest())
        with pytest.raises(DBAPIError), runtime.begin() as connection:
            connection.execute(_INSERT_CANONICAL_FALLBACK, values)
    finally:
        runtime.dispose()
        if report_id is not None:
            with owner_engine.begin() as connection:
                connection.execute(text("DELETE FROM technical_reports WHERE id=:id"), {"id": report_id})
        _cleanup_scope(scope)


@pytest.mark.parametrize(("source_type", "field", "invalid_value"), [
    ("universal_capture", "created_at", "2026-99-99T12:00:00.000000Z"),
    ("universal_capture", "created_at", "2026-08-09T12:00:00Z"),
    ("universal_capture", "original_content", " x "),
    ("universal_capture", "original_content", "e\u0301"),
    ("universal_capture", "original_content", "x\x01y"),
    ("universal_capture", "original_content", "x" * 10001),
    ("universal_capture", "source_reference", "line\nline"),
    ("evidence", "effective_at", "2026-02-30T12:00:00.000000Z"),
    ("evidence", "effective_at", "2026-08-09T12:00:00.000000+00:00"),
    ("evidence", "source_reference", " EV-1 "),
    ("evidence", "source_revision", "A\x01"),
    ("evidence", "supported_fact", "x" * 2001),
    ("evidence", "source_reference", None),
    ("engineering_object", "customer_id", "1"),
    ("engineering_object", "subtype", "forbidden"),
    ("engineering_relationship", "reviewer_id", "1"),
    ("engineering_relationship", "evidence_references", [None]),
])
def test_historical_basis_python_and_database_parity_rejects_invalid_values(
    source_type: str, field: str, invalid_value: object,
) -> None:
    runtime = _runtime_engine()
    report_id = None
    scope = None
    try:
        with runtime.begin() as connection:
            report_id, _, scope = _insert_draft(connection)
        basis = _historical_basis(source_type, scope)
        basis[field] = invalid_value
        try:
            reconstructed = historical_basis_from_payload(basis, source_type)
        except Exception:
            pass
        else:
            assert json.loads(canonical_json(reconstructed)) != basis
        values = _fallback_values(source_type, report_id, scope, _historical_basis(source_type, scope))
        values.update(minimal=json.dumps(basis), digest=hashlib.sha256(_canonical(basis)).hexdigest())
        with pytest.raises(DBAPIError), runtime.begin() as connection:
            connection.execute(_INSERT_CANONICAL_FALLBACK, values)
    finally:
        runtime.dispose()
        if report_id is not None:
            with owner_engine.begin() as connection:
                connection.execute(text("DELETE FROM technical_reports WHERE id=:id"), {"id": report_id})
        _cleanup_scope(scope)


@pytest.mark.parametrize(("source_type", "field", "valid_value"), [
    ("universal_capture", "original_content", "x" * 10000),
    ("universal_capture", "source_reference", "x" * 512),
    ("evidence", "source_revision", "x" * 128),
    ("evidence", "supported_fact", "x" * 2000),
    ("evidence", "effective_at", None),
    ("engineering_object", "customer_id", None),
    ("engineering_relationship", "reviewer_id", None),
])
def test_historical_basis_python_and_database_parity_accepts_boundaries(
    source_type: str, field: str, valid_value: object,
) -> None:
    runtime = _runtime_engine()
    report_id = None
    scope = None
    try:
        with runtime.begin() as connection:
            report_id, _, scope = _insert_draft(connection)
            basis = _historical_basis(source_type, scope)
            basis[field] = valid_value
            historical_basis_from_payload(basis, source_type)
            connection.execute(_INSERT_CANONICAL_FALLBACK, _fallback_values(source_type, report_id, scope, basis))
    finally:
        runtime.dispose()
        if report_id is not None:
            with owner_engine.begin() as connection:
                connection.execute(text("DELETE FROM technical_report_provenance_entries WHERE technical_report_id=:id"), {"id": report_id})
                connection.execute(text("DELETE FROM technical_reports WHERE id=:id"), {"id": report_id})
        _cleanup_scope(scope)


@pytest.mark.parametrize("source_type", [
    "universal_capture", "evidence", "engineering_object", "engineering_relationship",
])
@pytest.mark.parametrize("boundary", ["\tvalue", "value\t", "\u00a0value", "value\u00a0", "\u2003value"])
def test_historical_boundary_whitespace_matches_python_contract(
    source_type: str, boundary: str,
) -> None:
    runtime = _runtime_engine()
    report_id = None
    scope = None
    try:
        with runtime.begin() as connection:
            report_id, _, scope = _insert_draft(connection)
        basis = _historical_basis(source_type, scope)
        field = {
            "universal_capture": "original_content",
            "evidence": "supported_fact",
            "engineering_object": "family",
            "engineering_relationship": "relationship_family",
        }[source_type]
        basis[field] = boundary
        try:
            reconstructed = historical_basis_from_payload(basis, source_type)
        except Exception:
            pass
        else:
            assert json.loads(canonical_json(reconstructed)) != basis
        values = _fallback_values(source_type, report_id, scope, _historical_basis(source_type, scope))
        values.update(minimal=json.dumps(basis), digest=hashlib.sha256(_canonical(basis)).hexdigest())
        with pytest.raises(DBAPIError), runtime.begin() as connection:
            connection.execute(_INSERT_CANONICAL_FALLBACK, values)
    finally:
        runtime.dispose()
        if report_id is not None:
            with owner_engine.begin() as connection:
                connection.execute(text("DELETE FROM technical_reports WHERE id=:id"), {"id": report_id})
        _cleanup_scope(scope)


@pytest.mark.parametrize(("source_type", "field", "value"), [
    ("universal_capture", "original_content", "value\tinside"),
    ("universal_capture", "source_reference", "value\tinside"),
    ("evidence", "supported_fact", "value\tinside"),
])
def test_historical_interior_tab_remains_valid(
    source_type: str, field: str, value: str,
) -> None:
    runtime = _runtime_engine()
    report_id = None
    scope = None
    try:
        with runtime.begin() as connection:
            report_id, _, scope = _insert_draft(connection)
            basis = _historical_basis(source_type, scope)
            basis[field] = value
            reconstructed = historical_basis_from_payload(basis, source_type)
            assert json.loads(canonical_json(reconstructed)) == basis
            connection.execute(_INSERT_CANONICAL_FALLBACK, _fallback_values(source_type, report_id, scope, basis))
    finally:
        runtime.dispose()
        if report_id is not None:
            with owner_engine.begin() as connection:
                connection.execute(text("DELETE FROM technical_report_provenance_entries WHERE technical_report_id=:id"), {"id": report_id})
                connection.execute(text("DELETE FROM technical_reports WHERE id=:id"), {"id": report_id})
        _cleanup_scope(scope)


def test_database_boundary_whitespace_matches_runtime_python_strip_set() -> None:
    python_strip_whitespace = tuple(
        chr(codepoint) for codepoint in range(0x110000) if chr(codepoint).isspace()
    )
    assert {"\t", "\u00a0", "\u2003"} <= set(python_strip_whitespace)
    with owner_engine.connect() as connection:
        for whitespace in python_strip_whitespace:
            assert connection.execute(
                text("SELECT technical_report_text_valid(:value,10000,false)"),
                {"value": f"{whitespace}value"},
            ).scalar_one() is False
            assert connection.execute(
                text("SELECT technical_report_text_valid(:value,10000,false)"),
                {"value": f"value{whitespace}"},
            ).scalar_one() is False
        assert connection.execute(
            text("SELECT technical_report_text_valid(:value,10000,false)"),
            {"value": "value\tinside"},
        ).scalar_one() is True
        assert connection.execute(
            text("SELECT technical_report_text_valid(:value,10000,false)"),
            {"value": "value\u00a0inside"},
        ).scalar_one() is True


@pytest.mark.parametrize("statement", [
    "ALTER TABLE technical_reports DISABLE TRIGGER trg_technical_reports_accepted_immutable",
    "DROP TRIGGER trg_technical_reports_accepted_immutable ON technical_reports",
    "ALTER TABLE technical_report_provenance_entries DISABLE TRIGGER trg_technical_report_provenance_accepted_immutable",
    "DROP TRIGGER trg_technical_report_provenance_accepted_immutable ON technical_report_provenance_entries",
    "ALTER FUNCTION technical_report_root_accepted_immutable() OWNER TO satco_runtime",
    "DROP FUNCTION technical_report_root_accepted_immutable()",
    "ALTER FUNCTION technical_report_provenance_accepted_immutable() OWNER TO satco_runtime",
    "DROP FUNCTION technical_report_provenance_accepted_immutable()",
    "ALTER TABLE technical_reports OWNER TO satco_runtime",
    "CREATE TABLE patch032_runtime_must_not_create(id integer)",
])
def test_runtime_cannot_administer_protected_schema(statement: str) -> None:
    runtime = _runtime_engine()
    try:
        with pytest.raises(DBAPIError), runtime.begin() as connection:
            connection.exec_driver_sql(statement)
    finally:
        runtime.dispose()


def test_preflight_fails_for_disabled_trigger_and_excessive_grant() -> None:
    runtime = _runtime_engine()
    try:
        with owner_engine.begin() as owner:
            owner.exec_driver_sql("ALTER TABLE technical_reports DISABLE TRIGGER trg_technical_reports_accepted_immutable")
        with pytest.raises(RuntimeError):
            validate_technical_report_runtime_boundary(runtime, migration_role_name=owner_engine.url.username)
    finally:
        with owner_engine.begin() as owner:
            owner.exec_driver_sql("ALTER TABLE technical_reports ENABLE TRIGGER trg_technical_reports_accepted_immutable")
        runtime.dispose()

    runtime = _runtime_engine()
    try:
        with owner_engine.begin() as owner:
            owner.exec_driver_sql("GRANT DELETE ON technical_reports TO satco_runtime")
        with pytest.raises(RuntimeError):
            validate_technical_report_runtime_boundary(runtime, migration_role_name=owner_engine.url.username)
    finally:
        with owner_engine.begin() as owner:
            owner.exec_driver_sql("REVOKE DELETE ON technical_reports FROM satco_runtime")
        runtime.dispose()

    runtime = _runtime_engine()
    try:
        with owner_engine.begin() as owner:
            owner.exec_driver_sql("GRANT UPDATE (payload) ON technical_report_outbox TO satco_runtime")
        with pytest.raises(RuntimeError):
            validate_technical_report_runtime_boundary(runtime, migration_role_name=owner_engine.url.username)
    finally:
        with owner_engine.begin() as owner:
            owner.exec_driver_sql("REVOKE UPDATE (payload) ON technical_report_outbox FROM satco_runtime")
        runtime.dispose()


def test_preflight_rejects_privileged_or_protected_object_owner() -> None:
    with pytest.raises(RuntimeError):
        validate_technical_report_runtime_boundary(owner_engine, migration_role_name="different_owner")

    runtime = _runtime_engine()
    try:
        with owner_engine.begin() as owner:
            owner.exec_driver_sql("ALTER FUNCTION technical_report_canonical_json(jsonb) OWNER TO satco_runtime")
        with pytest.raises(RuntimeError):
            validate_technical_report_runtime_boundary(runtime, migration_role_name=owner_engine.url.username)
    finally:
        with owner_engine.begin() as owner:
            owner.exec_driver_sql(f"ALTER FUNCTION technical_report_canonical_json(jsonb) OWNER TO {owner_engine.url.username}")
        runtime.dispose()


def test_orm_flush_cannot_bypass_accepted_immutability() -> None:
    from sqlalchemy.orm import Session
    from app.models.technical_report import TechnicalReportRecord

    runtime = _runtime_engine()
    report_id = None
    scope = None
    try:
        with runtime.begin() as connection:
            report_id, revision_id, scope = _insert_draft(connection)
            snapshot, snapshot_digest, accepted_at, provenance = _accepted_state(report_id, revision_id, scope)
            _insert_external_snapshot_provenance(connection, report_id, provenance, accepted_at)
            connection.execute(text("""
                UPDATE technical_reports SET lifecycle='accepted', version=2,
                  accepted_snapshot=CAST(:snapshot AS jsonb), accepted_snapshot_digest=:digest,
                  accepted_by_id=:owner_id, accepted_at=:accepted_at,
                  accepted_draft_revision_id=:revision_id,
                  accepted_aggregate_version=2, updated_at=now() WHERE id=:id
            """), {"snapshot": json.dumps(snapshot), "digest": snapshot_digest,
                    "owner_id": scope["owner_id"], "accepted_at": accepted_at,
                    "revision_id": revision_id, "id": report_id})
        with Session(runtime) as session:
            record = session.get(TechnicalReportRecord, report_id)
            record.conclusions = "ORM bypass"
            with pytest.raises(DBAPIError):
                session.flush()
            session.rollback()
    finally:
        runtime.dispose()
        if report_id is not None:
            with owner_engine.begin() as connection:
                connection.exec_driver_sql("ALTER TABLE technical_report_provenance_entries DISABLE TRIGGER trg_technical_report_provenance_accepted_immutable")
                connection.exec_driver_sql("ALTER TABLE technical_reports DISABLE TRIGGER trg_technical_reports_accepted_immutable")
                connection.execute(text("DELETE FROM technical_report_provenance_entries WHERE technical_report_id=:id"), {"id": report_id})
                connection.execute(text("DELETE FROM technical_reports WHERE id=:id"), {"id": report_id})
                connection.exec_driver_sql("ALTER TABLE technical_reports ENABLE TRIGGER trg_technical_reports_accepted_immutable")
                connection.exec_driver_sql("ALTER TABLE technical_report_provenance_entries ENABLE TRIGGER trg_technical_report_provenance_accepted_immutable")
        _cleanup_scope(scope)
