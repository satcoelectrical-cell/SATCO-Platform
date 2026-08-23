"""PostgreSQL-only integrity and restricted-runtime evidence for PATCH-043."""
from datetime import datetime, timezone
import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from conftest import owner_engine


def _runtime_engine():
    return create_engine(owner_engine.url.set(
        username="satco_runtime",
        password=os.getenv("TEST_RUNTIME_DATABASE_PASSWORD", "satco_runtime_test_password"),
    ))


def test_migration_owns_all_guard_functions_and_runtime_cannot_change_them():
    with owner_engine.connect() as owner:
        rows = owner.execute(text("""
            SELECT p.proname FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
            WHERE n.nspname='public' AND p.proname IN (
                'satco_guard_supporting_file_asset', 'satco_seal_evidence_file_links',
                'satco_guard_evidence_supporting_file_link',
                'satco_guard_supporting_file_scan_attempt') ORDER BY p.proname
        """)).scalars().all()
    assert rows == [
        "satco_guard_evidence_supporting_file_link",
        "satco_guard_supporting_file_asset",
        "satco_guard_supporting_file_scan_attempt",
        "satco_seal_evidence_file_links",
    ]
    runtime = _runtime_engine()
    try:
        with pytest.raises(DBAPIError):
            with runtime.begin() as connection:
                connection.execute(text("DROP FUNCTION satco_guard_supporting_file_asset()"))
    finally:
        runtime.dispose()


def test_database_rejects_invalid_opaque_key_before_application_can_use_it():
    # The non-null foreign keys are intentionally supplied by existing canonical
    # rows; invalid storage-key data is therefore attributable to this guard.
    token = uuid4().hex
    organization_id = uuid4()
    with owner_engine.begin() as owner:
        uploader_id = owner.execute(text("""
            INSERT INTO users(email, username, hashed_password, role, is_active, created_at)
            VALUES (:email, :username, 'test', 'engineer', true, now()) RETURNING id
        """), {"email": f"sf-{token}@example.invalid", "username": f"sf-{token}"}).scalar_one()
        owner.execute(text("INSERT INTO organizations(id, is_active) VALUES (:id, true)"), {"id": organization_id})
        customer_id = owner.execute(text("""
            INSERT INTO customers(name, organization_id) VALUES (:name, :organization_id) RETURNING id
        """), {"name": f"Supporting file {token}", "organization_id": organization_id}).scalar_one()
        project_id = owner.execute(text("""
            INSERT INTO projects(organization_id,project_code,name,customer_id,status,priority,owner_id,progress,created_at)
            VALUES (:organization_id,:code,:name,:customer_id,'new','medium',:owner_id,0,now()) RETURNING id
        """), {"organization_id": organization_id, "code": f"SAT-PRJ-2099-{int(token[:6], 16) % 10000:04d}", "name": "Supporting file", "customer_id": customer_id, "owner_id": uploader_id}).scalar_one()
    try:
        with owner_engine.begin() as owner:
            with pytest.raises(DBAPIError):
                owner.execute(text("""
                INSERT INTO supporting_file_assets(
                  id,organization_id,project_id,safe_filename,safe_ascii_filename,media_type,
                  byte_size,digest_algorithm,content_digest,storage_key,object_version,uploader_id,
                  lifecycle,version,uploaded_at,scan_requested_at
                ) VALUES (
                  :id,:organization_id,:project_id,'x.pdf','x.pdf','application/pdf',1,'sha256',
                  :digest,'customer/visible', 'object-v1', :uploader_id,'quarantined',1,:now,:now
                )
                """), {"organization_id": organization_id, "project_id": project_id, "uploader_id": uploader_id, "id": uuid4(), "digest": "a" * 64, "now": datetime.now(timezone.utc)})
    finally:
        with owner_engine.begin() as owner:
            owner.execute(text("DELETE FROM projects WHERE id=:id"), {"id": project_id})
            owner.execute(text("DELETE FROM customers WHERE id=:id"), {"id": customer_id})
            owner.execute(text("DELETE FROM organizations WHERE id=:id"), {"id": organization_id})
            owner.execute(text("DELETE FROM users WHERE id=:id"), {"id": uploader_id})


def test_direct_sql_cannot_modify_or_remove_a_sealed_evidence_file_link():
    """The permanent seal survives Evidence's historic withdrawn→proposed path."""
    connection = owner_engine.connect()
    transaction = connection.begin()
    token = uuid4().hex
    organization_id = uuid4()
    try:
        uploader_id = connection.execute(text("""
            INSERT INTO users(email,username,hashed_password,role,is_active,created_at)
            VALUES (:email,:username,'test','engineer',true,now()) RETURNING id
        """), {"email": f"seal-{token}@example.invalid", "username": f"seal-{token}"}).scalar_one()
        connection.execute(text("INSERT INTO organizations(id,is_active) VALUES (:id,true)"), {"id": organization_id})
        customer_id = connection.execute(text("INSERT INTO customers(name,organization_id) VALUES (:name,:organization_id) RETURNING id"), {"name": f"Seal {token}", "organization_id": organization_id}).scalar_one()
        project_id = connection.execute(text("""
            INSERT INTO projects(organization_id,project_code,name,customer_id,status,priority,owner_id,progress,created_at)
            VALUES (:organization_id,:code,'Seal evidence',:customer_id,'new','medium',:owner_id,0,now()) RETURNING id
        """), {"organization_id": organization_id, "code": f"SAT-PRJ-2099-{int(token[:6], 16) % 10000:04d}", "customer_id": customer_id, "owner_id": uploader_id}).scalar_one()
        asset_id, evidence_id = uuid4(), uuid4()
        connection.execute(text("""
            INSERT INTO supporting_file_assets(id,organization_id,project_id,safe_filename,safe_ascii_filename,media_type,byte_size,digest_algorithm,content_digest,storage_key,object_version,uploader_id,lifecycle,version,uploaded_at,scan_requested_at,scanned_at)
            VALUES (:asset_id,:organization_id,:project_id,'basis.pdf','basis.pdf','application/pdf',1,'sha256',:digest,:storage_key,'v1',:uploader_id,'available',1,now(),now(),now())
        """), {"asset_id": asset_id, "organization_id": organization_id, "project_id": project_id, "uploader_id": uploader_id, "digest": "a" * 64, "storage_key": "objects/" + uuid4().hex + uuid4().hex})
        connection.execute(text("""
            INSERT INTO evidence(id,organization_id,project_id,lifecycle,source_kind,source_reference,source_revision,source_standing,supported_fact,creator_id,version)
            VALUES (:evidence_id,:organization_id,:project_id,'proposed','engineering_record','SF','1','current','fact',:uploader_id,1)
        """), {"evidence_id": evidence_id, "organization_id": organization_id, "project_id": project_id, "uploader_id": uploader_id})
        connection.execute(text("""
            INSERT INTO evidence_supporting_file_links(evidence_id,asset_id,organization_id,project_id,evidence_version,ordinal,linked_by_id,linked_at)
            VALUES (:evidence_id,:asset_id,:organization_id,:project_id,1,0,:uploader_id,now())
        """), {"evidence_id": evidence_id, "asset_id": asset_id, "organization_id": organization_id, "project_id": project_id, "uploader_id": uploader_id})
        connection.execute(text("UPDATE evidence SET lifecycle='current', version=2, updated_at=now() WHERE id=:id"), {"id": evidence_id})
        connection.execute(text("UPDATE evidence SET lifecycle='withdrawn', version=3, updated_at=now() WHERE id=:id"), {"id": evidence_id})
        connection.execute(text("UPDATE evidence SET lifecycle='proposed', version=4, updated_at=now() WHERE id=:id"), {"id": evidence_id})
        with pytest.raises(DBAPIError):
            connection.execute(text("DELETE FROM evidence_supporting_file_links WHERE evidence_id=:id"), {"id": evidence_id})
    finally:
        transaction.rollback()
        connection.close()
