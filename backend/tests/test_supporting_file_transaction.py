"""Real PostgreSQL/UoW atomicity evidence for PATCH-043 Batch 2."""
from datetime import datetime, timezone
from dataclasses import replace
from hashlib import sha256
from uuid import UUID, uuid4
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from sqlalchemy.orm import sessionmaker

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.adapters.supporting_file_object_store import InMemoryPrivateSupportingFileObjectStore
from app.enums.supporting_file import SupportingFileMediaType
from app.exceptions.supporting_file import SupportingFileIntegrityError, SupportingFileProtectedNotFound, SupportingFileScannerUnavailable
from app.models.supporting_file import SupportingFileAsset, SupportingFileIdempotencyRecord, SupportingFileOutboxRecord, SupportingFileScanAttempt
from app.models.supporting_file_command import SupportingFileScope
from app.ports.supporting_file import RecordSupportingFileScan, SupportingFileScanResult, SupportingFileScannerPrincipal
from app.repositories.supporting_file_repository import SqlAlchemySupportingFileRepository
from app.repositories.supporting_file_unit_of_work import SqlAlchemySupportingFileUnitOfWork
from app.services.supporting_file_service import SupportingFileService
from conftest import owner_engine

PDF_BYTES=b"%PDF-1.7\ntransaction-basis"


class AllowTrustedScope:
    def require_mutation(self, **request):
        assert request["actor_id"] > 0 and request["project_id"] > 0
    def require_read(self, **request):
        assert request["actor_id"] > 0 and request["project_id"] > 0
    def require_withdraw(self, **request):
        assert request["actor_id"] > 0 and request["project_id"] > 0


class CleanScanner:
    def scan_exact(self, **_): return SupportingFileScanResult("clean", datetime.now(timezone.utc), "test-engine", "test-signatures", uuid4())


class UnavailableScanner:
    def scan_exact(self, **_): raise SupportingFileScannerUnavailable()


def _scope(db_session):
    token = uuid4().hex
    organization_id = UUID("02810000-0000-4000-8000-000000000001")
    actor_id = db_session.execute(text("""
        INSERT INTO users(email,username,hashed_password,role,is_active,created_at)
        VALUES (:email,:username,'test','engineer',true,now()) RETURNING id
    """), {"email": f"sf-tx-{token}@example.invalid", "username": f"sf-tx-{token}"}).scalar_one()
    customer_id = db_session.execute(text("INSERT INTO customers(name,organization_id) VALUES (:name,:organization_id) RETURNING id"), {"name": f"Supporting transaction {token}", "organization_id": organization_id}).scalar_one()
    project_id = db_session.execute(text("""
        INSERT INTO projects(organization_id,project_code,name,customer_id,status,priority,owner_id,progress,created_at)
        VALUES (:organization_id,:code,'Supporting transaction',:customer_id,'new','medium',:owner_id,0,now()) RETURNING id
    """), {"organization_id": organization_id, "code": f"SAT-PRJ-2098-{int(token[:6],16)%10000:04d}", "customer_id": customer_id, "owner_id": actor_id}).scalar_one()
    return actor_id, SupportingFileScope(organization_id, project_id, None)


def _service(db_session):
    actor, scope = _scope(db_session)
    return actor, scope, SupportingFileService(uow=SqlAlchemySupportingFileUnitOfWork(db_session), objects=InMemoryPrivateSupportingFileObjectStore(), scanner=CleanScanner(), authorization=AllowTrustedScope())


def _finalize(service, actor, scope, reservation, idem, fingerprint):
    return service.finalize_upload(actor_id=actor, reservation_id=reservation.id, scope=scope, filename="basis.pdf", media_type=SupportingFileMediaType.PDF, content=PDF_BYTES, expected_digest=sha256(PDF_BYTES).hexdigest(), rationale="Human supporting evidence", correlation_id=uuid4(), idempotency_id=idem, request_fingerprint=fingerprint)


def test_real_uow_first_execution_replay_and_conflict_are_atomic(db_session):
    actor, scope, service = _service(db_session); key, fingerprint = uuid4(), "a" * 64
    reservation = service.reserve_upload(actor_id=actor, scope=scope)
    asset = _finalize(service, actor, scope, reservation, key, fingerprint)
    assert db_session.query(SupportingFileAsset).filter_by(id=asset.id).count() == 1
    assert db_session.query(SupportingFileIdempotencyRecord).filter_by(actor_id=actor, idempotency_id=key, status="completed").count() == 1
    record = db_session.query(SupportingFileIdempotencyRecord).filter_by(actor_id=actor, idempotency_id=key).one()
    assert record.organization_id == scope.organization_id
    attempt = db_session.query(SupportingFileScanAttempt).filter_by(asset_id=asset.id).one()
    assert attempt.organization_id == scope.organization_id and attempt.attempt_number == 1
    assert attempt.expected_asset_version == 1 and attempt.state == "completed" and attempt.disposition == "clean"
    assert db_session.query(SupportingFileOutboxRecord).filter_by(asset_id=asset.id).count() == 2
    assert db_session.execute(text("SELECT count(*) FROM audit_logs WHERE entity='SUPPORTING_FILE' AND entity_uuid=:id"), {"id": asset.id}).scalar_one() == 2
    replay = _finalize(service, actor, scope, reservation, key, fingerprint)
    assert replay.id == asset.id
    assert db_session.query(SupportingFileAsset).filter_by(project_id=scope.project_id).count() == 1
    assert db_session.query(SupportingFileOutboxRecord).filter_by(asset_id=asset.id).count() == 2
    with pytest.raises(SupportingFileIntegrityError): _finalize(service, actor, scope, reservation, key, "b" * 64)
    assert db_session.query(SupportingFileOutboxRecord).filter_by(asset_id=asset.id).count() == 2


def test_real_uow_scope_mismatch_cannot_replay_idempotency_result(db_session):
    actor, scope, service = _service(db_session); key = uuid4(); reservation = service.reserve_upload(actor_id=actor, scope=scope)
    _finalize(service, actor, scope, reservation, key, "c" * 64)
    other = SupportingFileScope(uuid4(), scope.project_id, None)
    with pytest.raises(SupportingFileProtectedNotFound):
        _finalize(service, actor, other, reservation, key, "c" * 64)


def test_real_uow_audit_staging_failure_rolls_back_business_success(db_session):
    actor, scope, service = _service(db_session); reservation = service.reserve_upload(actor_id=actor, scope=scope)
    original = service.uow.repository.stage_audit
    def fail(**_): raise RuntimeError("injected audit staging failure")
    service.uow.repository.stage_audit = fail
    with pytest.raises(RuntimeError): _finalize(service, actor, scope, reservation, uuid4(), "d" * 64)
    service.uow.repository.stage_audit = original
    assert db_session.query(SupportingFileAsset).filter_by(project_id=scope.project_id).count() == 0
    assert db_session.execute(text("""
        SELECT count(*) FROM supporting_file_outbox
        WHERE asset_id IN (SELECT id FROM supporting_file_assets WHERE project_id=:project_id)
    """), {"project_id": scope.project_id}).scalar_one() == 0


def test_real_uow_outbox_staging_failure_rolls_back_business_success(db_session):
    actor, scope, service = _service(db_session); reservation = service.reserve_upload(actor_id=actor, scope=scope)
    original = service.uow.repository.stage_outbox
    def fail(_): raise RuntimeError("injected outbox staging failure")
    service.uow.repository.stage_outbox = fail
    with pytest.raises(RuntimeError): _finalize(service, actor, scope, reservation, uuid4(), "e" * 64)
    service.uow.repository.stage_outbox = original
    assert db_session.query(SupportingFileAsset).filter_by(project_id=scope.project_id).count() == 0
    assert db_session.query(SupportingFileIdempotencyRecord).filter_by(actor_id=actor).count() == 0
    assert db_session.execute(text("""
        SELECT count(*) FROM supporting_file_outbox
        WHERE asset_id IN (SELECT id FROM supporting_file_assets WHERE project_id=:project_id)
    """), {"project_id": scope.project_id}).scalar_one() == 0


def test_real_uow_scanner_unavailable_persists_failed_attempt_without_promotion(db_session):
    actor, scope, service = _service(db_session)
    service.scanner = UnavailableScanner()
    reservation = service.reserve_upload(actor_id=actor, scope=scope)
    asset = _finalize(service, actor, scope, reservation, uuid4(), "u" * 64)
    attempt = db_session.query(SupportingFileScanAttempt).filter_by(asset_id=asset.id).one()
    assert asset.lifecycle == "quarantined" and reservation.status == "uploaded"
    assert attempt.organization_id == scope.organization_id
    assert attempt.state == "failed" and attempt.disposition is None and attempt.completed_at is not None


def test_authenticated_result_is_bound_idempotent_and_provider_attributed(db_session):
    actor, scope, service = _service(db_session)
    service.scanner = UnavailableScanner()
    reservation = service.reserve_upload(actor_id=actor, scope=scope)
    asset = _finalize(service, actor, scope, reservation, uuid4(), "1" * 64)
    failed = db_session.query(SupportingFileScanAttempt).filter_by(asset_id=asset.id).one()
    now, correlation = datetime.now(timezone.utc), uuid4()
    request = RecordSupportingFileScan(
        principal=SupportingFileScannerPrincipal("supporting-file-scanner-v1"),
        asset_id=asset.id, asset_version=asset.version, attempt_id=failed.id,
        object_fingerprint=asset.content_digest, disposition="clean",
        engine_id="engine-a", signature_set_id="signatures-2026-08",
        observed_at=now, correlation_id=correlation,
    )
    # A completed failed attempt cannot be rewritten by a late result.
    with pytest.raises(SupportingFileIntegrityError):
        service.record_scan_result(request)
    service.scanner = CleanScanner()
    asset = service.retry_scan(
        principal=request.principal, asset_id=asset.id,
        expected_asset_version=asset.version, expected_attempt_number=1, now=now,
    )
    attempt = db_session.query(SupportingFileScanAttempt).filter_by(asset_id=asset.id, attempt_number=2).one()
    assert asset.lifecycle == "available"
    assert attempt.engine_id == "test-engine" and attempt.signature_set_id == "test-signatures"
    duplicate = RecordSupportingFileScan(
        principal=request.principal, asset_id=asset.id,
        asset_version=attempt.expected_asset_version, attempt_id=attempt.id,
        object_fingerprint=attempt.object_digest, disposition=attempt.disposition,
        engine_id=attempt.engine_id, signature_set_id=attempt.signature_set_id,
        observed_at=attempt.completed_at, correlation_id=attempt.correlation_id,
    )
    assert service.record_scan_result(duplicate).id == asset.id
    with pytest.raises(SupportingFileIntegrityError):
        service.record_scan_result(replace(duplicate, correlation_id=uuid4()))
    for bad in (
        replace(duplicate, asset_version=99),
        replace(duplicate, object_fingerprint="0" * 64),
        replace(duplicate, attempt_id=uuid4()),
        replace(duplicate, principal=SupportingFileScannerPrincipal("customer")),
    ):
        with pytest.raises(SupportingFileProtectedNotFound):
            service.record_scan_result(bad)


def test_retry_is_durable_bounded_and_never_creates_attempt_four(db_session):
    actor, scope, service = _service(db_session)
    service.scanner = UnavailableScanner()
    reservation = service.reserve_upload(actor_id=actor, scope=scope)
    asset = _finalize(service, actor, scope, reservation, uuid4(), "2" * 64)
    principal = SupportingFileScannerPrincipal("supporting-file-scanner-v1")
    service.retry_scan(principal=principal, asset_id=asset.id, expected_asset_version=1, expected_attempt_number=1)
    service.retry_scan(principal=principal, asset_id=asset.id, expected_asset_version=1, expected_attempt_number=2)
    attempts = db_session.query(SupportingFileScanAttempt).filter_by(asset_id=asset.id).order_by(SupportingFileScanAttempt.attempt_number).all()
    assert [item.attempt_number for item in attempts] == [1, 2, 3]
    assert all(item.state == "failed" for item in attempts)
    with pytest.raises(SupportingFileProtectedNotFound):
        service.retry_scan(principal=principal, asset_id=asset.id, expected_asset_version=1, expected_attempt_number=3)
    assert db_session.query(SupportingFileScanAttempt).filter_by(asset_id=asset.id).count() == 3


def test_direct_sql_cannot_rebind_or_rewrite_scan_history(db_session):
    actor, scope, service = _service(db_session)
    service.scanner = UnavailableScanner()
    reservation = service.reserve_upload(actor_id=actor, scope=scope)
    asset = _finalize(service, actor, scope, reservation, uuid4(), "4" * 64)
    attempt = db_session.query(SupportingFileScanAttempt).filter_by(asset_id=asset.id).one()

    nested = db_session.begin_nested()
    with pytest.raises(DBAPIError):
        db_session.execute(text("UPDATE supporting_file_scan_attempts SET object_digest=:digest WHERE id=:id"), {"digest": "0" * 64, "id": attempt.id})
    nested.rollback()

    nested = db_session.begin_nested()
    with pytest.raises(DBAPIError):
        db_session.execute(text("INSERT INTO supporting_file_scan_attempts(id,asset_id,organization_id,expected_asset_version,object_digest,attempt_number,state,requested_at) VALUES (:id,:asset,:organization_id,1,:digest,2,'requested',now())"), {"id": uuid4(), "asset": asset.id, "organization_id": scope.organization_id, "digest": "0" * 64})
    nested.rollback()
    db_session.expire_all()
    preserved = db_session.query(SupportingFileScanAttempt).filter_by(id=attempt.id).one()
    assert preserved.state == "failed" and preserved.object_digest == asset.content_digest


def test_retry_request_audit_outbox_failure_rolls_back_next_attempt(db_session):
    actor, scope, service = _service(db_session)
    service.scanner = UnavailableScanner()
    reservation = service.reserve_upload(actor_id=actor, scope=scope)
    asset = _finalize(service, actor, scope, reservation, uuid4(), "5" * 64)
    original = service.uow.repository.stage_outbox
    service.uow.repository.stage_outbox = lambda _record: (_ for _ in ()).throw(RuntimeError("injected retry outbox failure"))
    with pytest.raises(RuntimeError):
        service.retry_scan(
            principal=SupportingFileScannerPrincipal("supporting-file-scanner-v1"),
            asset_id=asset.id, expected_asset_version=1,
            expected_attempt_number=1,
        )
    service.uow.repository.stage_outbox = original
    assert db_session.query(SupportingFileScanAttempt).filter_by(asset_id=asset.id).count() == 1


def test_real_postgresql_same_key_concurrency_has_one_winner():
    """Two independent PostgreSQL transactions race one durable idempotency key.

    Setup is committed before the race: the two worker Sessions must observe
    the same real reservation, not fixture-transaction state.  The shared
    object-store double is only an external-object-store substitute; the
    winner/replay guarantee is exercised solely through PostgreSQL uniqueness
    and the real SQLAlchemy UoW/repository implementation.
    """
    token = uuid4().hex
    organization_id = uuid4()
    factory = sessionmaker(bind=owner_engine, expire_on_commit=False)
    with owner_engine.begin() as connection:
        connection.execute(text("""
            INSERT INTO organizations(id,name,slug,is_active,created_at,updated_at)
            VALUES (:id,:name,:slug,true,now(),now())
        """), {"id": organization_id, "name": f"Supporting race {token}", "slug": f"sf-race-{token[:16]}"})
        actor = connection.execute(text("""
            INSERT INTO users(email,username,hashed_password,role,is_active,created_at)
            VALUES (:email,:username,'test','engineer',true,now()) RETURNING id
        """), {"email": f"sf-race-{token}@example.invalid", "username": f"sf-race-{token}"}).scalar_one()
        customer_id = connection.execute(text("""
            INSERT INTO customers(name,organization_id)
            VALUES (:name,:organization_id) RETURNING id
        """), {"name": f"Supporting race {token}", "organization_id": organization_id}).scalar_one()
        project_id = connection.execute(text("""
            INSERT INTO projects(organization_id,project_code,name,customer_id,status,priority,owner_id,progress,created_at)
            VALUES (:organization_id,:code,'Supporting race',:customer_id,'new','medium',:owner_id,0,now())
            RETURNING id
        """), {"organization_id": organization_id, "code": f"SAT-PRJ-2097-{int(token[:6], 16) % 10000:04d}", "customer_id": customer_id, "owner_id": actor}).scalar_one()
    scope = SupportingFileScope(organization_id, project_id, None)
    store = InMemoryPrivateSupportingFileObjectStore()
    setup_session = factory()
    try:
        setup_service = SupportingFileService(
            uow=SqlAlchemySupportingFileUnitOfWork(setup_session), objects=store,
            scanner=CleanScanner(), authorization=AllowTrustedScope(),
        )
        reservation = setup_service.reserve_upload(actor_id=actor, scope=scope)
    finally:
        setup_session.close()

    key, fingerprint, barrier = uuid4(), "f" * 64, Barrier(2)

    def attempt():
        session = factory()
        try:
            service = SupportingFileService(
                uow=SqlAlchemySupportingFileUnitOfWork(session), objects=store,
                scanner=CleanScanner(), authorization=AllowTrustedScope(),
            )
            barrier.wait(timeout=10)
            return _finalize(service, actor, scope, reservation, key, fingerprint).id
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        values = list(pool.map(lambda _: attempt(), range(2)))
    assert values[0] == values[1]
    asset_id = values[0]
    with owner_engine.connect() as connection:
        assert connection.execute(text("""
            SELECT count(*) FROM supporting_file_assets
            WHERE id=:asset AND organization_id=:organization_id
        """), {"asset": asset_id, "organization_id": organization_id}).scalar_one() == 1
        assert connection.execute(text("""
            SELECT count(*) FROM supporting_file_idempotency
            WHERE actor_id=:actor AND idempotency_id=:key AND status='completed'
        """), {"actor": actor, "key": key}).scalar_one() == 1
        assert connection.execute(text("SELECT count(*) FROM supporting_file_outbox WHERE asset_id=:asset"), {"asset": asset_id}).scalar_one() == 2
        assert connection.execute(text("SELECT count(*) FROM audit_logs WHERE entity='SUPPORTING_FILE' AND entity_uuid=:asset"), {"asset": asset_id}).scalar_one() == 2

    replay_session = factory()
    try:
        protected_service = SupportingFileService(
            uow=SqlAlchemySupportingFileUnitOfWork(replay_session), objects=store,
            scanner=CleanScanner(), authorization=AllowTrustedScope(),
        )
        with pytest.raises(SupportingFileProtectedNotFound):
            _finalize(
                protected_service, actor,
                SupportingFileScope(uuid4(), project_id, None), reservation, key, fingerprint,
            )
    finally:
        replay_session.close()


def test_real_postgresql_concurrent_retry_creates_one_next_attempt():
    token, organization_id = uuid4().hex, uuid4()
    factory = sessionmaker(bind=owner_engine, expire_on_commit=False)
    with owner_engine.begin() as connection:
        connection.execute(text("INSERT INTO organizations(id,name,slug,is_active,created_at,updated_at) VALUES (:id,:name,:slug,true,now(),now())"), {"id": organization_id, "name": f"Scan retry {token}", "slug": f"scan-retry-{token[:14]}"})
        actor = connection.execute(text("INSERT INTO users(email,username,hashed_password,role,is_active,created_at) VALUES (:email,:username,'test','engineer',true,now()) RETURNING id"), {"email": f"scan-retry-{token}@example.invalid", "username": f"scan-retry-{token}"}).scalar_one()
        customer = connection.execute(text("INSERT INTO customers(name,organization_id) VALUES (:name,:organization_id) RETURNING id"), {"name": f"Scan retry {token}", "organization_id": organization_id}).scalar_one()
        project = connection.execute(text("INSERT INTO projects(organization_id,project_code,name,customer_id,status,priority,owner_id,progress,created_at) VALUES (:organization_id,:code,'Scan retry',:customer,'new','medium',:actor,0,now()) RETURNING id"), {"organization_id": organization_id, "code": f"SAT-PRJ-2096-{int(token[:6],16)%10000:04d}", "customer": customer, "actor": actor}).scalar_one()
    scope, store = SupportingFileScope(organization_id, project, None), InMemoryPrivateSupportingFileObjectStore()
    setup = factory()
    try:
        service = SupportingFileService(uow=SqlAlchemySupportingFileUnitOfWork(setup), objects=store, scanner=UnavailableScanner(), authorization=AllowTrustedScope())
        reservation = service.reserve_upload(actor_id=actor, scope=scope)
        asset = _finalize(service, actor, scope, reservation, uuid4(), "3" * 64)
        asset_id = asset.id
    finally:
        setup.close()
    barrier = Barrier(2)
    principal = SupportingFileScannerPrincipal("supporting-file-scanner-v1")

    def retry():
        session = factory()
        try:
            service = SupportingFileService(uow=SqlAlchemySupportingFileUnitOfWork(session), objects=store, scanner=UnavailableScanner(), authorization=AllowTrustedScope())
            barrier.wait(timeout=10)
            try:
                service.retry_scan(principal=principal, asset_id=asset_id, expected_asset_version=1, expected_attempt_number=1)
                return "winner"
            except (SupportingFileIntegrityError, SupportingFileProtectedNotFound):
                return "conflict"
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: retry(), range(2)))
    assert sorted(outcomes) == ["conflict", "winner"]
    with owner_engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM supporting_file_scan_attempts WHERE asset_id=:asset"), {"asset": asset_id}).scalar_one() == 2
        assert connection.execute(text("SELECT max(attempt_number) FROM supporting_file_scan_attempts WHERE asset_id=:asset"), {"asset": asset_id}).scalar_one() == 2
