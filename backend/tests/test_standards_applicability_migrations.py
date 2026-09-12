"""Real-PostgreSQL evidence for the PATCH-054 applicability foundation correction."""

from importlib import import_module
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

def _fixture(db_session, admin_user):
    from tests.test_standards_migrations import _foundation_fixture
    return _foundation_fixture(db_session, admin_user)


def _row(values, *, edition=True, status="declared_applicable", role="design_basis", predecessor=None, expected=None, revision=1):
    return values | {
        "id": uuid4(), "edition_value": values["edition"] if edition else None, "status": status, "role": role,
        "candidate": None if edition else f"candidate-{uuid4().hex}", "rationale_code": "human_review",
        "rationale": "Human applicability decision", "origin": "project_engineer",
        "candidate_ref": None if edition else f"package-candidate:{uuid4().hex}",
        "mandatory_kind": None, "mandatory_ref": None, "mandatory_digest": None, "predecessor": predecessor,
        "expected": expected, "successor": None, "revision": revision, "digest": f"{uuid4().int:064x}"[-64:],
    }


def _insert(db_session, values):
    db_session.execute(text("""
      INSERT INTO project_standard_applicability(id,organization_id,project_id,standard_edition_id,candidate_designation_key,
        status,applicability_role,rationale_code,rationale,origin_reference,source_candidate_reference,
        mandatory_source_kind,mandatory_source_reference,mandatory_source_digest,expected_predecessor_revision,
        predecessor_id,successor_id,is_current,revision,applicability_digest,declared_by)
      VALUES (:id,:organization,:project,:edition_value,:candidate,:status,:role,:rationale_code,:rationale,:origin,:candidate_ref,
        :mandatory_kind,:mandatory_ref,:mandatory_digest,:expected,:predecessor,:successor,true,:revision,:digest,:actor)
    """), values)


def test_applicability_corrective_schema_and_narrow_privileges(db_session):
    columns = {row[0] for row in db_session.execute(text("""
      SELECT column_name FROM information_schema.columns
      WHERE table_schema='public' AND table_name='project_standard_applicability'
    """))}
    assert {"candidate_designation_key", "rationale_code", "rationale", "origin_reference", "source_candidate_reference", "mandatory_source_kind", "mandatory_source_reference", "mandatory_source_digest", "expected_predecessor_revision", "successor_id", "is_current", "applicability_digest", "declared_by"} <= columns
    assert db_session.execute(text("SELECT has_table_privilege('satco_runtime','project_standard_applicability','DELETE')")).scalar_one() is False
    assert db_session.execute(text("SELECT has_column_privilege('satco_runtime','project_standard_applicability','is_current','UPDATE')")).scalar_one() is True
    guard_security = db_session.execute(text("""
      SELECT count(*)=3
        AND bool_and(prosecdef AND proconfig @> ARRAY['search_path=pg_catalog, public'])
        AND NOT EXISTS (
          SELECT 1 FROM pg_proc AS public_grant
          CROSS JOIN LATERAL aclexplode(coalesce(public_grant.proacl,acldefault('f',public_grant.proowner))) AS privilege
          WHERE public_grant.proname IN ('standards_applicability_history_guard','standards_applicability_limit_guard','standards_applicability_lineage_guard')
            AND privilege.grantee=0 AND privilege.privilege_type='EXECUTE'
        )
      FROM pg_proc
      WHERE proname IN ('standards_applicability_history_guard','standards_applicability_limit_guard','standards_applicability_lineage_guard')
    """)).scalar_one()
    assert guard_security is True


def test_mandatory_and_candidate_shapes_are_database_enforced(db_session, admin_user):
    values = _fixture(db_session, admin_user)
    candidate = _row(values, edition=False, status="candidate_advisory", role="informative")
    _insert(db_session, candidate)
    mandatory = _row(values, role="mandatory") | {"mandatory_kind": "contract", "mandatory_ref": "contract-1", "mandatory_digest": "b" * 64}
    _insert(db_session, mandatory)
    invalid = _row(values, role="mandatory")
    with pytest.raises(DBAPIError), db_session.begin_nested():
        _insert(db_session, invalid)
    with pytest.raises(DBAPIError), db_session.begin_nested():
        _insert(db_session, candidate | {"id": uuid4(), "candidate_ref": None})
    with pytest.raises(DBAPIError), db_session.begin_nested():
        _insert(db_session, _row(values, edition=False, status="declared_applicable"))
    other_organization = uuid4()
    db_session.execute(text("INSERT INTO organizations(id,is_active) VALUES (:id,true)"), {"id": other_organization})
    with pytest.raises(DBAPIError), db_session.begin_nested():
        _insert(db_session, _row(values | {"organization": other_organization}))


def test_current_head_limit_lineage_and_immutability(db_session, admin_user):
    values = _fixture(db_session, admin_user)
    _insert(db_session, _row(values))
    for item in range(63):
        edition = uuid4()
        db_session.execute(text("""
          INSERT INTO standard_editions(id,standard_identity_id,edition_designation,edition_key,edition_disambiguator,jurisdiction,metadata_source_reference,edition_digest,created_by)
          SELECT :edition,standard_identity_id,:key,:key,'',jurisdiction,'catalog',:digest,:actor FROM standard_editions WHERE id=:base
        """), {"edition": edition, "key": f"e-{item}-{uuid4().hex[:8]}", "digest": "c" * 64, "actor": admin_user.id, "base": values["edition"]})
        _insert(db_session, _row(values | {"edition": edition}))
    assert db_session.execute(text("SELECT count(*) FROM project_standard_applicability WHERE project_id=:project AND is_current"), values).scalar_one() == 64
    overflow_identity = uuid4()
    overflow_edition = uuid4()
    db_session.execute(text("""
      INSERT INTO standard_identities(id,catalog_scope,organization_id,issuer_key,issuer_display,designation,designation_key,
        title,language,jurisdiction,normalization_version,metadata_source_reference,identity_digest,created_by)
      SELECT :identity,catalog_scope,organization_id,issuer_key,:designation,:designation,:designation,
        title,language,jurisdiction,normalization_version,metadata_source_reference,:identity_digest,created_by
      FROM standard_identities WHERE id=:base_identity;
      INSERT INTO standard_editions(id,standard_identity_id,edition_designation,edition_key,edition_disambiguator,jurisdiction,metadata_source_reference,edition_digest,created_by)
      SELECT :edition,:identity,'overflow','overflow','','{}','catalog',:digest,:actor FROM standard_editions WHERE id=:base
    """), {"identity": overflow_identity, "edition": overflow_edition, "designation": f"overflow-{uuid4().hex}", "identity_digest": "e" * 64, "digest": "d" * 64, "actor": admin_user.id, "base": values["edition"], "base_identity": values["identity"]})
    with pytest.raises(DBAPIError), db_session.begin_nested():
        _insert(db_session, _row(values | {"edition": overflow_edition}))
    first = db_session.execute(text("SELECT id,revision FROM project_standard_applicability WHERE project_id=:project ORDER BY created_at LIMIT 1"), values).one()
    successor = _row(values | {"edition": db_session.execute(text("SELECT standard_edition_id FROM project_standard_applicability WHERE id=:id"), {"id": first.id}).scalar_one()}, predecessor=first.id, expected=first.revision, revision=first.revision + 1)
    db_session.execute(text("UPDATE project_standard_applicability SET is_current=false,successor_id=:successor,revision=revision+1 WHERE id=:id"), {"id": first.id, "successor": successor["id"]})
    _insert(db_session, successor)
    db_session.execute(text("SET CONSTRAINTS tr_standard_applicability_lineage IMMEDIATE"))
    db_session.flush()
    with pytest.raises(DBAPIError), db_session.begin_nested():
        db_session.execute(text("UPDATE project_standard_applicability SET rationale='rewritten' WHERE id=:id"), {"id": successor["id"]})


def test_downgrade_refuses_retained_applicability_history(db_session, admin_user, monkeypatch):
    _insert(db_session, _row(_fixture(db_session, admin_user)))
    migration = import_module("migrations.versions.e05400000004_patch_054_applicability_foundation_corrective")
    monkeypatch.setattr(migration.op, "get_bind", db_session.connection)

    with pytest.raises(RuntimeError, match="retained applicability history"):
        migration.downgrade()
