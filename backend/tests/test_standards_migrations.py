import pytest
from datetime import datetime, timedelta, timezone
from importlib import import_module
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from uuid import UUID, uuid4

from app.models.customer import Customer
from app.models.project import Project


@pytest.mark.parametrize("vector", ["P054-AUD-01", "P054-AUD-02", "P054-DB-01"])
def test_standards_foundation_tables_exist(db_session, vector):
    for table in ("standard_identities", "standard_editions", "standard_edition_standing_observations", "standard_rights_bindings", "standards_idempotency", "standards_outbox"):
        assert db_session.execute(text("SELECT to_regclass(:name)"), {"name": f"public.{table}"}).scalar_one() is not None


def _foundation_fixture(
    db_session,
    admin_user,
    *,
    effective_from=None,
    effective_until=None,
    allow_excerpt_display=True,
    allow_source_retrieval=True,
    source_location="clause 1",
):
    organization_id = UUID("02810000-0000-4000-8000-000000000001")
    customer = Customer(organization_id=organization_id, name=f"Customer {uuid4()}")
    db_session.add(customer); db_session.flush()
    project = Project(organization_id=organization_id, project_code=f"SAT-PRJ-2054-{uuid4().int % 900000 + 100000}", name="Standards correction", customer_id=customer.id, status="new", priority="medium", progress=0, owner_id=admin_user.id)
    db_session.add(project); db_session.flush()
    ids = {name: uuid4() for name in ("identity", "edition", "standing", "rights", "snapshot")}
    digest = "a" * 64
    effective_from = effective_from or datetime.now(timezone.utc) - timedelta(minutes=1)
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
        approved_processor_policy_ids,effective_from,effective_until,rights_authority_reference,rights_authority_digest,
        reason_code,rights_digest,created_by)
      VALUES (:rights,:organization,:edition,'test_provider','organization_license','active',true,true,true,
        :allow_excerpt_display,
        :allow_source_retrieval,true,true,'prohibited','[]',:effective_from,:effective_until,
        'test-rights',:digest,'created',:digest,:actor);
      INSERT INTO standard_source_snapshots(id,organization_id,project_id,standard_identity_id,standard_edition_id,
        source_provider_id,adapter_policy_id,adapter_policy_version,source_location,availability_status,
        request_purpose,correlation_id,object_key,object_version,content_sha256,byte_count,media_type,
        rights_binding_id,rights_binding_version,rights_digest,evaluated_capabilities,standing_observation_id,
        standing_observation_digest,source_metadata_digest,integrity_verified,integrity_verified_at,snapshot_digest,
        retrieved_at,retrieved_by)
      VALUES (:snapshot,:organization,:project,:identity,:edition,'test_provider','test_policy','1',:source_location,
        'available','verification',:correlation,'standards/test-object','v1',:digest,8,'text/plain',:rights,1,
        :digest,'{}',:standing,:digest,:digest,true,now(),:digest,now(),:actor)
    """), {
        **ids,
        "organization": organization_id,
        "project": project.id,
        "actor": admin_user.id,
        "designation": f"std-{uuid4().hex}",
        "correlation": uuid4(),
        "digest": digest,
        "allow_excerpt_display": allow_excerpt_display,
        "allow_source_retrieval": allow_source_retrieval,
        "source_location": source_location,
        "effective_from": effective_from,
        "effective_until": effective_until,
    })
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
        has_table_privilege('satco_runtime','standard_assertion_verification_events','DELETE'),
        has_function_privilege('satco_runtime','resolve_standard_provider_handle(uuid,uuid,integer,text)','EXECUTE'),
        has_function_privilege('satco_registry_installer','resolve_standard_provider_handle(uuid,uuid,integer,text)','EXECUTE'),
        (
          SELECT pg_get_userbyid(proowner)='satco'
            AND prosecdef
            AND proconfig @> ARRAY['search_path=pg_catalog, public']
          FROM pg_proc
          WHERE oid='resolve_standard_provider_handle(uuid,uuid,integer,text)'::regprocedure
        ),
        EXISTS (
          SELECT 1
          FROM pg_proc AS procedure
          CROSS JOIN LATERAL aclexplode(
            coalesce(procedure.proacl,acldefault('f',procedure.proowner))
          ) AS privilege
          WHERE procedure.oid='resolve_standard_provider_handle(uuid,uuid,integer,text)'::regprocedure
            AND privilege.grantee=0
            AND privilege.privilege_type='EXECUTE'
        )
    """)).one()
    assert tuple(observed) == (True, False, True, False, False, True, False, True, False)


def _provider_handle_fixture(
    db_session,
    admin_user,
    *,
    evaluated_excerpt_display=True,
    evaluated_source_retrieval=True,
    snapshot_rights_version=1,
    snapshot_rights_digest=None,
    snapshot_provider_id="test_provider",
    **foundation_kwargs,
):
    fixture = _foundation_fixture(db_session, admin_user, **foundation_kwargs)
    handle_snapshot = uuid4()
    sealed_handle = b"sealed-provider-handle"
    snapshot_rights_digest = snapshot_rights_digest or fixture["digest"]
    db_session.execute(text("""
      INSERT INTO standard_source_snapshots(id,organization_id,project_id,standard_identity_id,standard_edition_id,
        source_provider_id,adapter_policy_id,adapter_policy_version,source_location,availability_status,
        request_purpose,correlation_id,provider_handle_ciphertext,provider_handle_key_version,
        provider_version_digest,byte_count,media_type,rights_binding_id,rights_binding_version,rights_digest,
        evaluated_capabilities,standing_observation_id,standing_observation_digest,source_metadata_digest,
        integrity_verified,integrity_verified_at,snapshot_digest,retrieved_at,retrieved_by)
      VALUES (:snapshot,:organization,:project,:identity,:edition,:snapshot_provider_id,'test_policy','1','clause 2',
        'available','verification',:correlation,:sealed_handle,'test-key-v1',:digest,8,'text/plain',:rights,
        :snapshot_rights_version,
        :snapshot_rights_digest,
        jsonb_build_object('excerpt_display',:evaluated_excerpt_display,'source_retrieval',:evaluated_source_retrieval),
        :standing,:digest,:digest,
        true,now(),:snapshot_digest,now(),:actor)
    """), {
        **fixture,
        "snapshot": handle_snapshot,
        "correlation": uuid4(),
        "sealed_handle": sealed_handle,
        "snapshot_digest": "b" * 64,
        "snapshot_provider_id": snapshot_provider_id,
        "snapshot_rights_version": snapshot_rights_version,
        "snapshot_rights_digest": snapshot_rights_digest,
        "evaluated_excerpt_display": evaluated_excerpt_display,
        "evaluated_source_retrieval": evaluated_source_retrieval,
    })
    return fixture, handle_snapshot, sealed_handle


def _resolve_provider_handle(db_session, *, snapshot_id, organization_id, actor_id, purpose):
    return db_session.execute(text("""
      SELECT resolve_standard_provider_handle(:snapshot_id,:organization_id,:actor_id,:purpose)
    """), {
        "snapshot_id": snapshot_id,
        "organization_id": organization_id,
        "actor_id": actor_id,
        "purpose": purpose,
    }).scalar_one()


def test_provider_handle_resolver_returns_only_sealed_handle_after_fresh_checks(db_session, admin_user):
    fixture, snapshot_id, sealed_handle = _provider_handle_fixture(db_session, admin_user)

    db_session.execute(text("SET LOCAL ROLE satco_runtime"))
    try:
        assert bytes(_resolve_provider_handle(
            db_session,
            snapshot_id=snapshot_id,
            organization_id=fixture["organization"],
            actor_id=admin_user.id,
            purpose="display",
        )) == sealed_handle
        assert bytes(_resolve_provider_handle(
            db_session,
            snapshot_id=snapshot_id,
            organization_id=fixture["organization"],
            actor_id=admin_user.id,
            purpose="retrieval",
        )) == sealed_handle
    finally:
        db_session.execute(text("RESET ROLE"))


def test_runtime_cannot_select_provider_handle_ciphertext_directly(db_session, admin_user):
    _, snapshot_id, _ = _provider_handle_fixture(db_session, admin_user)

    with pytest.raises(DBAPIError), db_session.begin_nested():
        db_session.execute(text("SET LOCAL ROLE satco_runtime"))
        db_session.execute(text("""
          SELECT provider_handle_ciphertext FROM standard_source_snapshots WHERE id=:snapshot_id
        """), {"snapshot_id": snapshot_id}).scalar_one()


def test_provider_handle_resolver_masks_scope_actor_purpose_and_stale_rights(db_session, admin_user):
    fixture, snapshot_id, _ = _provider_handle_fixture(db_session, admin_user)

    assert _resolve_provider_handle(
        db_session,
        snapshot_id=snapshot_id,
        organization_id=uuid4(),
        actor_id=admin_user.id,
        purpose="display",
    ) is None
    assert _resolve_provider_handle(
        db_session,
        snapshot_id=snapshot_id,
        organization_id=fixture["organization"],
        actor_id=-1,
        purpose="display",
    ) is None
    assert _resolve_provider_handle(
        db_session,
        snapshot_id=snapshot_id,
        organization_id=fixture["organization"],
        actor_id=admin_user.id,
        purpose="unsupported",
    ) is None

    db_session.execute(text("""
      UPDATE user_organization_memberships SET is_enabled=false,is_selected=false
      WHERE user_id=:actor AND organization_id=:organization
    """), fixture)
    assert _resolve_provider_handle(
        db_session,
        snapshot_id=snapshot_id,
        organization_id=fixture["organization"],
        actor_id=admin_user.id,
        purpose="display",
    ) is None
    db_session.execute(text("""
      UPDATE user_organization_memberships SET is_enabled=true,is_selected=true
      WHERE user_id=:actor AND organization_id=:organization
    """), fixture)

    db_session.execute(text("UPDATE users SET is_active=false WHERE id=:actor"), fixture)
    assert _resolve_provider_handle(
        db_session,
        snapshot_id=snapshot_id,
        organization_id=fixture["organization"],
        actor_id=admin_user.id,
        purpose="display",
    ) is None
    db_session.execute(text("UPDATE users SET is_active=true WHERE id=:actor"), fixture)

    db_session.execute(text("UPDATE organizations SET is_active=false WHERE id=:organization"), fixture)
    assert _resolve_provider_handle(
        db_session,
        snapshot_id=snapshot_id,
        organization_id=fixture["organization"],
        actor_id=admin_user.id,
        purpose="display",
    ) is None
    db_session.execute(text("UPDATE organizations SET is_active=true WHERE id=:organization"), fixture)

    db_session.execute(text("""
      UPDATE standard_rights_bindings SET is_current=false,version=version+1 WHERE id=:rights;
      INSERT INTO standard_rights_bindings(id,organization_id,standard_edition_id,source_provider_id,rights_basis,
        rights_status,allow_metadata_visibility,allow_content_storage,allow_indexing,allow_excerpt_display,
        allow_source_retrieval,allow_derived_retention,allow_derived_current_use,ai_processing_permission,
        approved_processor_policy_ids,effective_from,rights_authority_reference,rights_authority_digest,
        predecessor_id,reason_code,rights_digest,created_by,version)
      VALUES (:replacement,:organization,:edition,'test_provider','organization_license','revoked',false,false,
        false,false,false,false,false,'prohibited','[]',now(),'test-rights',:digest,:rights,'revoked',:replacement_digest,
        :actor,2)
    """), {
        **fixture,
        "replacement": uuid4(),
        "replacement_digest": "c" * 64,
    })
    assert _resolve_provider_handle(
        db_session,
        snapshot_id=snapshot_id,
        organization_id=fixture["organization"],
        actor_id=admin_user.id,
        purpose="display",
    ) is None


def test_provider_handle_resolver_enforces_time_capability_and_snapshot_rights_binding(db_session, admin_user):
    future_fixture, future_snapshot, _ = _provider_handle_fixture(
        db_session,
        admin_user,
        effective_from=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    assert _resolve_provider_handle(
        db_session,
        snapshot_id=future_snapshot,
        organization_id=future_fixture["organization"],
        actor_id=admin_user.id,
        purpose="display",
    ) is None

    expired_fixture, expired_snapshot, _ = _provider_handle_fixture(
        db_session,
        admin_user,
        effective_from=datetime.now(timezone.utc) - timedelta(hours=2),
        effective_until=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    assert _resolve_provider_handle(
        db_session,
        snapshot_id=expired_snapshot,
        organization_id=expired_fixture["organization"],
        actor_id=admin_user.id,
        purpose="display",
    ) is None

    recorded_fixture, recorded_snapshot, _ = _provider_handle_fixture(
        db_session,
        admin_user,
        evaluated_excerpt_display=False,
    )
    assert _resolve_provider_handle(
        db_session,
        snapshot_id=recorded_snapshot,
        organization_id=recorded_fixture["organization"],
        actor_id=admin_user.id,
        purpose="display",
    ) is None

    current_fixture, current_snapshot, _ = _provider_handle_fixture(
        db_session,
        admin_user,
        allow_excerpt_display=False,
    )
    assert _resolve_provider_handle(
        db_session,
        snapshot_id=current_snapshot,
        organization_id=current_fixture["organization"],
        actor_id=admin_user.id,
        purpose="display",
    ) is None

    recorded_retrieval_fixture, recorded_retrieval_snapshot, _ = _provider_handle_fixture(
        db_session,
        admin_user,
        evaluated_source_retrieval=False,
    )
    assert _resolve_provider_handle(
        db_session,
        snapshot_id=recorded_retrieval_snapshot,
        organization_id=recorded_retrieval_fixture["organization"],
        actor_id=admin_user.id,
        purpose="retrieval",
    ) is None

    current_retrieval_fixture, current_retrieval_snapshot, _ = _provider_handle_fixture(
        db_session,
        admin_user,
        allow_source_retrieval=False,
    )
    assert _resolve_provider_handle(
        db_session,
        snapshot_id=current_retrieval_snapshot,
        organization_id=current_retrieval_fixture["organization"],
        actor_id=admin_user.id,
        purpose="retrieval",
    ) is None

    for overrides in (
        {"snapshot_rights_version": 2},
        {"snapshot_rights_digest": "d" * 64},
        {"snapshot_provider_id": "other_provider"},
    ):
        fixture, mismatched_snapshot, _ = _provider_handle_fixture(
            db_session,
            admin_user,
            **overrides,
        )
        assert _resolve_provider_handle(
            db_session,
            snapshot_id=mismatched_snapshot,
            organization_id=fixture["organization"],
            actor_id=admin_user.id,
            purpose="display",
        ) is None


def test_provider_handle_resolver_downgrade_refuses_retained_handles(db_session, admin_user, monkeypatch):
    _provider_handle_fixture(db_session, admin_user)
    migration = import_module(
        "migrations.versions.e05400000003_patch_054_protected_provider_handle_resolver"
    )
    monkeypatch.setattr(migration.op, "get_bind", db_session.connection)

    with pytest.raises(RuntimeError, match="retained provider handles"):
        migration.downgrade()


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
