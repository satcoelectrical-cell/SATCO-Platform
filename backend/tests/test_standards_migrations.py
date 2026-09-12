import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from uuid import UUID, uuid4

from app.models.customer import Customer
from app.models.project import Project


@pytest.mark.parametrize("vector", ["P054-AUD-01", "P054-AUD-02", "P054-DB-01"])
def test_standards_foundation_tables_exist(db_session, vector):
    for table in ("standard_identities", "standard_editions", "standard_edition_standing_observations", "standard_rights_bindings", "standards_idempotency", "standards_outbox"):
        assert db_session.execute(text("SELECT to_regclass(:name)"), {"name": f"public.{table}"}).scalar_one() is not None


def _foundation_fixture(db_session, admin_user):
    organization_id = UUID("02810000-0000-4000-8000-000000000001")
    customer = Customer(organization_id=organization_id, name=f"Customer {uuid4()}")
    db_session.add(customer); db_session.flush()
    project = Project(organization_id=organization_id, project_code=f"SAT-PRJ-2054-{uuid4().int % 900000 + 100000}", name="Standards correction", customer_id=customer.id, status="new", priority="medium", progress=0, owner_id=admin_user.id)
    db_session.add(project); db_session.flush()
    ids = {name: uuid4() for name in ("identity", "edition", "standing", "rights", "snapshot")}
    digest = "a" * 64
    db_session.execute(text("""
      INSERT INTO standard_identities(id,catalog_scope,issuer_key,issuer_display,designation,designation_key,title,
        jurisdiction,normalization_version,metadata_source_reference,identity_digest,created_by)
      VALUES (:identity,'global_trusted','test-issuer', 'Test Issuer',:designation,:designation,'Test Standard','{}',
        'satco_standard_key_nfkc_casefold_v1','test-catalog',:digest,:actor);
      INSERT INTO standard_editions(id,standard_identity_id,edition_designation,edition_key,edition_disambiguator,
        jurisdiction,metadata_source_reference,edition_digest,created_by)
      VALUES (:edition,:identity,'2026',:designation,'','{}','test-catalog',:digest,:actor);
      INSERT INTO standard_edition_standing_observations(id,standard_edition_id,standing,observed_effective_at,
        source_reference,source_digest,actor_kind,created_by,observation_digest)
      VALUES (:standing,:edition,'current',now(),'test-catalog',:digest,'human',:actor,:digest);
      INSERT INTO standard_rights_bindings(id,organization_id,standard_edition_id,source_provider_id,rights_basis,
        rights_status,allow_metadata_visibility,allow_content_storage,allow_indexing,allow_excerpt_display,
        allow_source_retrieval,allow_derived_retention,allow_derived_current_use,ai_processing_permission,
        approved_processor_policy_ids,effective_from,rights_authority_reference,rights_authority_digest,
        reason_code,rights_digest,created_by)
      VALUES (:rights,:organization,:edition,'test_provider','organization_license','active',true,true,true,true,
        true,true,true,'prohibited','[]',now(),'test-rights',:digest,'created',:digest,:actor);
      INSERT INTO standard_source_snapshots(id,organization_id,project_id,standard_identity_id,standard_edition_id,
        source_provider_id,adapter_policy_id,adapter_policy_version,source_location,availability_status,
        request_purpose,correlation_id,object_key,object_version,content_sha256,byte_count,media_type,
        rights_binding_id,rights_binding_version,rights_digest,evaluated_capabilities,standing_observation_id,
        standing_observation_digest,source_metadata_digest,integrity_verified,integrity_verified_at,snapshot_digest,
        retrieved_at,retrieved_by)
      VALUES (:snapshot,:organization,:project,:identity,:edition,'test_provider','test_policy','1','clause 1',
        'available','verification',:correlation,'standards/test-object','v1',:digest,8,'text/plain',:rights,1,
        :digest,'{}',:standing,:digest,:digest,true,now(),:digest,now(),:actor)
    """), {**ids, "organization": organization_id, "project": project.id, "actor": admin_user.id, "designation": f"std-{uuid4().hex}", "correlation": uuid4(), "digest": digest})
    return {**ids, "organization": organization_id, "project": project.id, "actor": admin_user.id, "digest": digest}


def _insert_assertion(db_session, fixture, ordinal: int):
    assertion_id = uuid4()
    db_session.execute(text("""
      INSERT INTO standard_knowledge_assertions(id,organization_id,project_id,standard_edition_id,source_snapshot_id,
        source_location,source_content_digest,assertion_kind,canonical_representation,assertion_origin,
        extraction_method_id,extraction_method_version,extraction_method_digest,assertion_digest,
        verification_status,rights_binding_id,rights_binding_version,rights_digest,retained_derived_use_eligible,
        evaluated_rights_revision,version,created_by)
      VALUES (:id,:organization,:project,:edition,:snapshot,:location,:digest,'requirement_statement',
        jsonb_build_object('statement',:statement),'human','manual','1',:digest,:assertion_digest,'unverified',
        :rights,1,:digest,false,1,1,:actor)
    """), {**fixture, "id": assertion_id, "location": f"clause {ordinal}", "statement": f"Requirement {ordinal}", "assertion_digest": f"{ordinal:064x}"})
    return assertion_id


def test_corrective_runtime_privileges_are_narrow(db_session):
    observed = db_session.execute(text("""
      SELECT
        has_column_privilege('satco_runtime','standard_source_snapshots','id','INSERT'),
        has_column_privilege('satco_runtime','standard_source_snapshots','provider_handle_ciphertext','SELECT'),
        has_column_privilege('satco_runtime','standard_knowledge_assertions','verification_status','UPDATE'),
        has_column_privilege('satco_runtime','standard_knowledge_assertions','canonical_representation','UPDATE'),
        has_table_privilege('satco_runtime','standard_assertion_verification_events','DELETE')
    """)).one()
    assert tuple(observed) == (True, False, True, False, False)


def test_snapshot_assertion_and_verification_history_are_immutable(db_session, admin_user):
    fixture = _foundation_fixture(db_session, admin_user)
    assertion_id = _insert_assertion(db_session, fixture, 1)
    event_id = uuid4()
    db_session.execute(text("""
      INSERT INTO standard_assertion_verification_events(id,assertion_id,event_kind,status,source_rights_binding_id,
        source_rights_binding_version,source_rights_digest,assertion_digest,actor_kind,verified_by)
      VALUES (:event,:assertion,'verification_decision','human_verified',:rights,1,:digest,:assertion_digest,'human',:actor)
    """), {**fixture, "event": event_id, "assertion": assertion_id, "assertion_digest": f"{1:064x}"})
    attempts = (
        ("UPDATE standard_source_snapshots SET source_location='changed' WHERE id=:id", fixture["snapshot"]),
        ("UPDATE standard_knowledge_assertions SET canonical_representation='{}' WHERE id=:id", assertion_id),
        ("UPDATE standard_assertion_verification_events SET reason='changed' WHERE id=:id", event_id),
    )
    for statement, target in attempts:
        with pytest.raises(DBAPIError), db_session.begin_nested():
            db_session.execute(text(statement), {"id": target})


def test_assertion_limit_accepts_32_and_rejects_33(db_session, admin_user):
    fixture = _foundation_fixture(db_session, admin_user)
    for ordinal in range(1, 33):
        _insert_assertion(db_session, fixture, ordinal)
    assert db_session.execute(text("SELECT count(*) FROM standard_knowledge_assertions WHERE source_snapshot_id=:id"), {"id": fixture["snapshot"]}).scalar_one() == 32
    with pytest.raises(DBAPIError), db_session.begin_nested():
        _insert_assertion(db_session, fixture, 33)


def test_snapshot_project_tenant_scope_is_database_enforced(db_session, admin_user):
    fixture = _foundation_fixture(db_session, admin_user)
    foreign_organization = uuid4()
    db_session.execute(text("INSERT INTO organizations(id,is_active) VALUES (:id,true)"), {"id": foreign_organization})
    with pytest.raises(DBAPIError), db_session.begin_nested():
        db_session.execute(text("""
          INSERT INTO standard_source_snapshots(id,organization_id,project_id,standard_identity_id,standard_edition_id,
            source_provider_id,adapter_policy_id,adapter_policy_version,source_location,availability_status,
            request_purpose,correlation_id,rights_binding_id,rights_binding_version,rights_digest,evaluated_capabilities,
            standing_observation_id,standing_observation_digest,source_metadata_digest,integrity_verified,
            integrity_verified_at,snapshot_digest,retrieved_at,retrieved_by)
          VALUES (:id,:foreign,:project,:identity,:edition,'test_provider','test_policy','1','missing','rights_restricted',
            'verification',:correlation,:rights,1,:digest,'{}',:standing,:digest,:digest,false,now(),:digest,now(),:actor)
        """), {**fixture, "id": uuid4(), "foreign": foreign_organization, "correlation": uuid4()})
