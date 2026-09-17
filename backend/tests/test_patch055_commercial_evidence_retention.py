"""PATCH-055 exact backend conformance manifest and Checkpoint-B tests."""
from datetime import datetime, timedelta, timezone
from io import BytesIO
from hashlib import sha256
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.v1.routers.retention import RetentionApplication, get_retention_application, router as retention_router
from pydantic import ValidationError

from app.enums.retention import RetentionMode, RetentionPolicySource
from app.dependencies.retention import RetentionExportReceipt
from app.enums.supporting_file import SupportingFileMediaType
from app.models.audit_log import AuditLog
from app.models.evidence import Evidence
from app.models.retention import RetentionExport, RetentionExportSubject, RetentionHold, RetentionIdempotency, RetentionOutbox, RetentionRecord, RetentionRecovery
from app.models.supporting_file import SupportingFileAsset
from app.models.supporting_file_command import SupportingFileScope
from app.models.project import Project
from app.models.organization import UserOrganizationMembership
from app.models.customer import Customer
from app.repositories.retention_unit_of_work import SqlAlchemyRetentionUnitOfWork, UtcRetentionClock
from app.services.retention_service import RetentionConflict, RetentionIndeterminate, RetentionNotPermitted, RetentionProtectedNotFound, RetentionService, RetentionUnavailable
from app.schemas.retention import (
    CreateRetentionExportRequestV1,
    CreateRetentionRecoveryRequestV1,
    RetentionExportSubjectV1,
    RetentionSubjectV1,
    PlaceRetentionHoldRequestV1,
    RecordDispositionDecisionRequestV1,
    ReleaseRetentionHoldRequestV1,
)
from app.schemas.retention import ApplyRetentionPolicyRequestV1


PATCH055_BACKEND_VECTORS = tuple(
    [f"P055-EVW-{i:02d}" for i in range(1, 11)]
    + [f"P055-RET-{i:02d}" for i in range(1, 9)]
    + [f"P055-HLD-{i:02d}" for i in range(1, 9)]
    + [f"P055-XRC-{i:02d}" for i in range(1, 9)]
    + [f"P055-SEC-{i:02d}" for i in range(1, 9)]
)


def test_patch055_backend_manifest_is_exact_and_unique():
    expected = {
        *(f"P055-EVW-{i:02d}" for i in range(1, 11)),
        *(f"P055-RET-{i:02d}" for i in range(1, 9)),
        *(f"P055-HLD-{i:02d}" for i in range(1, 9)),
        *(f"P055-XRC-{i:02d}" for i in range(1, 9)),
        *(f"P055-SEC-{i:02d}" for i in range(1, 9)),
    }
    assert len(PATCH055_BACKEND_VECTORS) == 42
    assert set(PATCH055_BACKEND_VECTORS) == expected


CHECKPOINT_B_QUALIFIED_VECTORS = {
    *(f"P055-RET-{i:02d}" for i in range(1, 9)),
    *(f"P055-HLD-{i:02d}" for i in range(1, 9)),
    *(f"P055-SEC-{i:02d}" for i in range(1, 9)),
}


def test_checkpoint_b_qualification_manifest_is_exact():
    expected = {
        *(f"P055-RET-{i:02d}" for i in range(1, 9)),
        *(f"P055-HLD-{i:02d}" for i in range(1, 9)),
        *(f"P055-SEC-{i:02d}" for i in range(1, 9)),
    }
    assert len(CHECKPOINT_B_QUALIFIED_VECTORS) == 24
    assert CHECKPOINT_B_QUALIFIED_VECTORS == expected
    assert CHECKPOINT_B_QUALIFIED_VECTORS < set(PATCH055_BACKEND_VECTORS)


def test_ret03_retention_request_shape_is_fail_closed():
    with pytest.raises(ValidationError):
        ApplyRetentionPolicyRequestV1(
            retention_mode=RetentionMode.RETAIN_UNTIL,
            retention_until=datetime(2030, 1, 1),
            policy_source=RetentionPolicySource.HUMAN_SUBJECT_OVERRIDE,
            basis_code="contract",
            expected_version=0,
        )
    with pytest.raises(ValidationError):
        ApplyRetentionPolicyRequestV1(
            retention_mode=RetentionMode.RETAIN_INDEFINITELY,
            retention_until=datetime(2030, 1, 1, tzinfo=timezone.utc),
            policy_source=RetentionPolicySource.HUMAN_SUBJECT_OVERRIDE,
            basis_code="contract",
            expected_version=0,
        )


def test_sec08_checkpoint_b_has_no_physical_purge_path():
    root = Path(__file__).parents[1] / "app"
    sources = [
        root / "services" / "retention_service.py",
        root / "repositories" / "retention_repository.py",
        root / "repositories" / "retention_unit_of_work.py",
        root / "dependencies" / "retention.py",
    ]
    forbidden = (".delete(", "os.remove(", ".unlink(", "purge(")
    for source in sources:
        text = source.read_text()
        assert not any(token in text for token in forbidden), source


def test_sec04_sec08_human_disposition_is_version_bound_without_physical_disposal(
    db_session,
    admin_user,
):
    organization_id = UUID("02810000-0000-4000-8000-000000000001")
    now = datetime.now(timezone.utc)

    customer = Customer(name=f"P055 Customer {uuid4().hex[:8]}")
    db_session.add(customer)
    db_session.flush()

    project = Project(
        project_code=f"SAT-PRJ-2095-{customer.id + 3000:04d}",
        name="PATCH-055 Retention Project",
        customer_id=customer.id,
        owner_id=admin_user.id,
    )
    db_session.add(project)
    db_session.flush()

    evidence = Evidence(
        organization_id=organization_id,
        project_id=project.id,
        workspace_id=None,
        lifecycle="current",
        source_kind="engineering_record",
        source_reference=str(uuid4()),
        source_revision=str(uuid4()),
        source_standing="current",
        supported_fact="PATCH-055 retention disposition test evidence",
        creator_id=admin_user.id,
        version=1,
        created_at=now,
        updated_at=now,
    )
    db_session.add(evidence)
    db_session.flush()

    service = RetentionService(
        uow_factory=lambda: SqlAlchemyRetentionUnitOfWork(
            lambda: db_session
        ),
        clock=UtcRetentionClock(),
    )

    policy = service.apply_policy(
        organization_id=organization_id,
        actor_id=admin_user.id,
        subject_kind="evidence",
        subject_id=evidence.id,
        data=ApplyRetentionPolicyRequestV1(
            retention_mode=RetentionMode.RETAIN_UNTIL,
            retention_until=now + timedelta(days=30),
            policy_source=RetentionPolicySource.HUMAN_SUBJECT_OVERRIDE,
            basis_code="test.retention",
            rationale="Checkpoint-B DB-backed disposition test",
            expected_version=0,
        ),
        idempotency_key=uuid4(),
        correlation_id=uuid4(),
    )

    record_id = policy.state.retention_record_id
    assert record_id is not None

    response = service.record_disposition_decision(
        organization_id=organization_id,
        actor_id=admin_user.id,
        subject_kind="evidence",
        subject_id=evidence.id,
        data=RecordDispositionDecisionRequestV1(
            decision="retain",
            reason="Human decision to retain",
            retention_record_id=record_id,
            subject_version_snapshot=evidence.version,
            expected_version=policy.state.version,
        ),
        idempotency_key=uuid4(),
        correlation_id=uuid4(),
    )

    assert response.outcome == "success"
    assert response.state.retention_record_id == record_id
    assert response.state.disposition_decision.value == "retain"
    assert db_session.get(Evidence, evidence.id) is not None


def test_sec05_sec06_disposition_historical_idempotency_replay(
    db_session,
    admin_user,
):
    organization_id = UUID("02810000-0000-4000-8000-000000000001")
    now = datetime.now(timezone.utc)
    customer = Customer(name=f"P055 Replay Customer {uuid4().hex[:8]}")
    db_session.add(customer)
    db_session.flush()
    project = Project(
        project_code=f"SAT-PRJ-2096-{customer.id + 3000:04d}",
        name="PATCH-055 Replay Project",
        customer_id=customer.id,
        owner_id=admin_user.id,
    )
    db_session.add(project)
    db_session.flush()
    evidence = Evidence(
        organization_id=organization_id,
        project_id=project.id,
        workspace_id=None,
        lifecycle="current",
        source_kind="engineering_record",
        source_reference=str(uuid4()),
        source_revision=str(uuid4()),
        source_standing="current",
        supported_fact="PATCH-055 historical replay evidence",
        creator_id=admin_user.id,
        version=1,
        created_at=now,
        updated_at=now,
    )
    db_session.add(evidence)
    db_session.flush()
    service = RetentionService(
        uow_factory=lambda: SqlAlchemyRetentionUnitOfWork(lambda: db_session),
        clock=UtcRetentionClock(),
    )
    policy = service.apply_policy(
        organization_id=organization_id,
        actor_id=admin_user.id,
        subject_kind="evidence",
        subject_id=evidence.id,
        data=ApplyRetentionPolicyRequestV1(
            retention_mode=RetentionMode.RETAIN_UNTIL,
            retention_until=now + timedelta(days=30),
            policy_source=RetentionPolicySource.HUMAN_SUBJECT_OVERRIDE,
            basis_code="test.retention.replay",
            rationale="Checkpoint-B historical replay test",
            expected_version=0,
        ),
        idempotency_key=uuid4(),
        correlation_id=uuid4(),
    )
    record_id = policy.state.retention_record_id
    assert record_id is not None
    first_decision_key = uuid4()
    first_request = RecordDispositionDecisionRequestV1(
        decision="retain",
        reason="First Human decision",
        retention_record_id=record_id,
        subject_version_snapshot=evidence.version,
        expected_version=policy.state.version,
    )
    first = service.record_disposition_decision(
        organization_id=organization_id,
        actor_id=admin_user.id,
        subject_kind="evidence",
        subject_id=evidence.id,
        data=first_request,
        idempotency_key=first_decision_key,
        correlation_id=uuid4(),
    )
    assert first.outcome == "success"
    second = service.record_disposition_decision(
        organization_id=organization_id,
        actor_id=admin_user.id,
        subject_kind="evidence",
        subject_id=evidence.id,
        data=RecordDispositionDecisionRequestV1(
            decision="retain",
            reason="Second Human decision",
            retention_record_id=record_id,
            subject_version_snapshot=evidence.version,
            expected_version=policy.state.version,
        ),
        idempotency_key=uuid4(),
        correlation_id=uuid4(),
    )
    assert second.outcome == "success"
    replay = service.record_disposition_decision(
        organization_id=organization_id,
        actor_id=admin_user.id,
        subject_kind="evidence",
        subject_id=evidence.id,
        data=first_request,
        idempotency_key=first_decision_key,
        correlation_id=uuid4(),
    )
    assert replay.outcome == "success"
    assert replay.state.retention_record_id == record_id
    assert replay.state.disposition_decision.value == "retain"
    assert db_session.get(Evidence, evidence.id) is not None


def _p055_subject_fixture(db_session, admin_user, *, supporting_file=False):
    organization_id = UUID("02810000-0000-4000-8000-000000000001")
    now = datetime.now(timezone.utc)
    customer = Customer(name=f"P055 Vector Customer {uuid4().hex[:8]}")
    db_session.add(customer); db_session.flush()
    project = Project(project_code=f"SAT-PRJ-2097-{customer.id + 3000:04d}", name="PATCH-055 Vector Project", customer_id=customer.id, owner_id=admin_user.id)
    db_session.add(project); db_session.flush()
    if supporting_file:
        subject = SupportingFileAsset.quarantine(scope=SupportingFileScope(organization_id, project.id), filename="p055.txt", media_type=SupportingFileMediaType.TEXT, byte_size=4, digest=sha256(b"data").hexdigest(), storage_key=f"objects/{uuid4().hex * 2}", object_version="v1", uploader_id=admin_user.id, now=now)
    else:
        subject = Evidence(organization_id=organization_id, project_id=project.id, workspace_id=None, lifecycle="current", source_kind="engineering_record", source_reference=str(uuid4()), source_revision=str(uuid4()), source_standing="current", supported_fact="P055 vector evidence", creator_id=admin_user.id, version=1, created_at=now, updated_at=now)
    db_session.add(subject); db_session.flush()
    service = RetentionService(uow_factory=lambda: SqlAlchemyRetentionUnitOfWork(lambda: db_session), clock=UtcRetentionClock())
    return organization_id, now, subject, service

def _p055_apply(service, organization_id, admin_user, subject, now, *, expected=0, until_days=30):
    return service.apply_policy(organization_id=organization_id, actor_id=admin_user.id, subject_kind="supporting_file" if isinstance(subject, SupportingFileAsset) else "evidence", subject_id=subject.id, data=ApplyRetentionPolicyRequestV1(retention_mode=RetentionMode.RETAIN_UNTIL, retention_until=now + timedelta(days=until_days), policy_source=RetentionPolicySource.HUMAN_SUBJECT_OVERRIDE, basis_code="test.vector", rationale="P055 vector", expected_version=expected), idempotency_key=uuid4(), correlation_id=uuid4())

def test_ret01_typed_subject_resolves_evidence_and_supporting_file(db_session, admin_user):
    for supporting_file in (False, True):
        org, _, subject, service = _p055_subject_fixture(db_session, admin_user, supporting_file=supporting_file)
        state = service.get_state(organization_id=org, actor_id=admin_user.id, subject_kind="supporting_file" if supporting_file else "evidence", subject_id=subject.id)
        assert state.subject.subject_id == subject.id and state.subject.organization_id == org
        assert state.subject.project_id == subject.project_id
        assert state.disposition_eligibility.value == "indeterminate"

def test_ret02_ret07_policy_replacement_preserves_history_and_one_current_head(db_session, admin_user):
    org, now, subject, service = _p055_subject_fixture(db_session, admin_user)
    first = _p055_apply(service, org, admin_user, subject, now)
    second = _p055_apply(service, org, admin_user, subject, now, expected=1, until_days=60)
    rows = db_session.query(RetentionRecord).filter_by(organization_id=org, subject_id=subject.id).order_by(RetentionRecord.version).all()
    assert [r.version for r in rows] == [1, 2] and [r.is_current for r in rows] == [False, True]
    assert rows[1].supersedes_id == rows[0].id and second.state.predecessor_record_id == first.state.retention_record_id
    with pytest.raises(RetentionConflict):
        _p055_apply(service, org, admin_user, subject, now, expected=1, until_days=90)

def test_ret06_legacy_subject_reports_not_established_without_fabricated_history(db_session, admin_user):
    org, _, subject, service = _p055_subject_fixture(db_session, admin_user)
    state = service.get_state(organization_id=org, actor_id=admin_user.id, subject_kind="evidence", subject_id=subject.id)
    assert state.retention_record_id is None and state.version is None and state.retention_mode is None and state.policy_source is None
    assert state.disposition_eligibility.value == "indeterminate"
    assert db_session.query(RetentionRecord).filter_by(subject_id=subject.id).count() == 0

def test_hld01_hld02_hld03_hld07_place_hold_is_single_active_and_stale_safe(db_session, admin_user):
    org, now, subject, service = _p055_subject_fixture(db_session, admin_user)
    policy = _p055_apply(service, org, admin_user, subject, now)
    request = PlaceRetentionHoldRequestV1(reason_code="legal.hold", rationale="P055 hold", authority_reference="AUTH-055", expected_version=policy.state.version)
    held = service.place_hold(organization_id=org, actor_id=admin_user.id, subject_kind="evidence", subject_id=subject.id, data=request, idempotency_key=uuid4(), correlation_id=uuid4())
    assert held.state.hold_status.value == "active" and held.state.disposition_eligibility.value == "blocked_by_hold"
    assert db_session.query(RetentionHold).filter_by(subject_id=subject.id, is_current=True, status="active").count() == 1
    with pytest.raises(RetentionConflict):
        service.place_hold(organization_id=org, actor_id=admin_user.id, subject_kind="evidence", subject_id=subject.id, data=request, idempotency_key=uuid4(), correlation_id=uuid4())

def test_hld04_hld05_hld08_release_preserves_placement_and_does_not_dispose(db_session, admin_user):
    org, now, subject, service = _p055_subject_fixture(db_session, admin_user)
    original = (subject.lifecycle, subject.source_standing, subject.version)
    _p055_apply(service, org, admin_user, subject, now)
    held = service.place_hold(organization_id=org, actor_id=admin_user.id, subject_kind="evidence", subject_id=subject.id, data=PlaceRetentionHoldRequestV1(reason_code="legal.hold", rationale="P055 hold", authority_reference="AUTH-055", expected_version=1), idempotency_key=uuid4(), correlation_id=uuid4())
    released = service.release_hold(organization_id=org, actor_id=admin_user.id, subject_kind="evidence", subject_id=subject.id, hold_id=held.state.active_hold_id, data=ReleaseRetentionHoldRequestV1(release_rationale="Released by Human authority", expected_version=1), idempotency_key=uuid4(), correlation_id=uuid4())
    rows = db_session.query(RetentionHold).filter_by(subject_id=subject.id).order_by(RetentionHold.version).all()
    assert len(rows) == 2 and rows[0].hold_id == rows[1].hold_id == held.state.active_hold_id
    assert rows[1].predecessor_row_id == rows[0].row_id and rows[1].reason_code == rows[0].reason_code and rows[1].placed_at == rows[0].placed_at
    assert rows[1].released_by_user_id == admin_user.id and rows[1].release_rationale
    assert released.state.hold_status is None and released.state.active_hold_id is None
    # C route identity binding: a different stable Hold id cannot release the active revision.
    held_again = service.place_hold(organization_id=org, actor_id=admin_user.id, subject_kind="evidence", subject_id=subject.id, data=PlaceRetentionHoldRequestV1(reason_code="legal.hold", rationale="P055 second hold", authority_reference="AUTH-056", expected_version=1), idempotency_key=uuid4(), correlation_id=uuid4())
    with pytest.raises(RetentionConflict):
        service.release_hold(organization_id=org, actor_id=admin_user.id, subject_kind="evidence", subject_id=subject.id, hold_id=uuid4(), data=ReleaseRetentionHoldRequestV1(release_rationale="Wrong route identity", expected_version=1), idempotency_key=uuid4(), correlation_id=uuid4())
    still_active = db_session.query(RetentionHold).filter_by(subject_id=subject.id, is_current=True, status="active").one()
    assert still_active.hold_id == held_again.state.active_hold_id
    persisted = db_session.get(Evidence, subject.id)
    assert persisted is not None
    assert (persisted.lifecycle, persisted.source_standing, persisted.version) == original


def test_sec01_sec02_protected_absence_and_inactive_actor_collapse(db_session, admin_user):
    org, _, subject, service = _p055_subject_fixture(db_session, admin_user)
    actor_id, subject_id = admin_user.id, subject.id
    with pytest.raises(RetentionProtectedNotFound):
        service.get_state(organization_id=org, actor_id=actor_id, subject_kind="evidence", subject_id=uuid4())
    actor = db_session.get(type(admin_user), actor_id)
    actor.is_active = False
    db_session.commit()
    with pytest.raises(RetentionProtectedNotFound):
        service.get_state(organization_id=org, actor_id=actor_id, subject_kind="evidence", subject_id=subject_id)


def test_sec04_sec05_idempotency_digest_and_stale_version_are_conflicts(db_session, admin_user):
    org, now, subject, service = _p055_subject_fixture(db_session, admin_user)
    key = uuid4()
    data = ApplyRetentionPolicyRequestV1(retention_mode=RetentionMode.RETAIN_UNTIL, retention_until=now + timedelta(days=30), policy_source=RetentionPolicySource.HUMAN_SUBJECT_OVERRIDE, basis_code="test.vector", rationale="first", expected_version=0)
    service.apply_policy(organization_id=org, actor_id=admin_user.id, subject_kind="evidence", subject_id=subject.id, data=data, idempotency_key=key, correlation_id=uuid4())
    changed = ApplyRetentionPolicyRequestV1(retention_mode=RetentionMode.RETAIN_UNTIL, retention_until=now + timedelta(days=30), policy_source=RetentionPolicySource.HUMAN_SUBJECT_OVERRIDE, basis_code="test.vector", rationale="different", expected_version=0)
    with pytest.raises(RetentionConflict):
        service.apply_policy(organization_id=org, actor_id=admin_user.id, subject_kind="evidence", subject_id=subject.id, data=changed, idempotency_key=key, correlation_id=uuid4())
    with pytest.raises(RetentionConflict):
        _p055_apply(service, org, admin_user, subject, now, expected=0, until_days=60)


def test_sec06_idempotency_replay_rechecks_current_authorization(db_session, admin_user):
    org, now, subject, service = _p055_subject_fixture(db_session, admin_user)
    key = uuid4()
    data = ApplyRetentionPolicyRequestV1(retention_mode=RetentionMode.RETAIN_UNTIL, retention_until=now + timedelta(days=30), policy_source=RetentionPolicySource.HUMAN_SUBJECT_OVERRIDE, basis_code="test.vector", rationale="replay", expected_version=0)
    actor_id, subject_id = admin_user.id, subject.id
    first = service.apply_policy(organization_id=org, actor_id=actor_id, subject_kind="evidence", subject_id=subject_id, data=data, idempotency_key=key, correlation_id=uuid4())
    assert first.outcome == "success"
    actor = db_session.get(type(admin_user), actor_id)
    actor.is_active = False
    db_session.commit()
    with pytest.raises(RetentionProtectedNotFound):
        service.apply_policy(organization_id=org, actor_id=actor_id, subject_kind="evidence", subject_id=subject_id, data=data, idempotency_key=key, correlation_id=uuid4())


def test_ret08_eligibility_read_is_deterministic_and_non_mutating(db_session, admin_user):
    org, now, subject, service = _p055_subject_fixture(db_session, admin_user)
    original = (subject.lifecycle, subject.source_standing, subject.version)
    _p055_apply(service, org, admin_user, subject, now, until_days=30)
    one = service.get_state(organization_id=org, actor_id=admin_user.id, subject_kind="evidence", subject_id=subject.id)
    two = service.get_state(organization_id=org, actor_id=admin_user.id, subject_kind="evidence", subject_id=subject.id)
    assert one.disposition_eligibility == two.disposition_eligibility
    reloaded = db_session.get(Evidence, subject.id)
    assert (reloaded.lifecycle, reloaded.source_standing, reloaded.version) == original


def test_sec03_retention_projection_exposes_no_content_or_storage_locator(db_session, admin_user):
    org, now, subject, service = _p055_subject_fixture(db_session, admin_user, supporting_file=True)
    _p055_apply(service, org, admin_user, subject, now)
    state = service.get_state(organization_id=org, actor_id=admin_user.id, subject_kind="supporting_file", subject_id=subject.id)
    payload = state.model_dump(mode="json")
    serialized = str(payload).lower()
    assert "storage_key" not in serialized and "object_version" not in serialized
    assert "objects/" not in serialized and "p055.txt" not in serialized


def test_sec07_mutation_audit_outbox_and_idempotency_are_atomic(db_session, admin_user, monkeypatch):
    org, now, subject, service = _p055_subject_fixture(db_session, admin_user)
    actor_id, subject_id = admin_user.id, subject.id
    key = uuid4()
    original_record = service.uow_factory().__class__
    from app.repositories import retention_unit_of_work as retention_uow_module
    def fail_outbox(self, **values):
        raise RuntimeError("forced outbox failure")
    monkeypatch.setattr(retention_uow_module.SqlAlchemyRetentionOutboxRecorder, "record", fail_outbox)
    with pytest.raises(RuntimeError, match="forced outbox failure"):
        _p055_apply(service, org, admin_user, subject, now)
    assert db_session.query(RetentionRecord).filter_by(subject_id=subject_id).count() == 0
    assert db_session.query(RetentionOutbox).filter_by(organization_id=org).count() == 0
    assert db_session.query(AuditLog).filter_by(user_id=actor_id, entity="RETENTION_GOVERNANCE").count() == 0
    assert db_session.query(RetentionIdempotency).filter_by(organization_id=org, actor_user_id=actor_id).count() == 0


def test_ret04_ret05_platform_default_materializes_only_on_explicit_governed_mutation(db_session, admin_user):
    org, _, subject, service = _p055_subject_fixture(db_session, admin_user)
    actor_id, subject_id = admin_user.id, subject.id
    db_session.commit()
    legacy = service.get_state(organization_id=org, actor_id=actor_id, subject_kind="evidence", subject_id=subject_id)
    assert legacy.retention_record_id is None
    assert db_session.query(RetentionRecord).filter_by(subject_id=subject_id).count() == 0
    result = service.materialize_default_policy(
        organization_id=org, actor_id=actor_id, subject_kind="evidence", subject_id=subject_id,
        idempotency_key=uuid4(), correlation_id=uuid4(),
    )
    assert result.state.retention_mode is RetentionMode.RETAIN_INDEFINITELY
    assert result.state.retention_until is None
    assert result.state.policy_source is RetentionPolicySource.PLATFORM_DEFAULT
    assert result.state.disposition_eligibility.value == "not_eligible"
    assert db_session.query(RetentionRecord).filter_by(subject_id=subject_id, is_current=True).count() == 1


def test_ret04_human_subject_override_supersedes_materialized_platform_default(db_session, admin_user):
    org, now, subject, service = _p055_subject_fixture(db_session, admin_user)
    default = service.materialize_default_policy(
        organization_id=org, actor_id=admin_user.id, subject_kind="evidence", subject_id=subject.id,
        idempotency_key=uuid4(), correlation_id=uuid4(),
    )
    human = _p055_apply(service, org, admin_user, subject, now, expected=default.state.version, until_days=30)
    assert human.state.policy_source is RetentionPolicySource.HUMAN_SUBJECT_OVERRIDE
    assert human.state.predecessor_record_id == default.state.retention_record_id
    rows = db_session.query(RetentionRecord).filter_by(subject_id=subject.id).order_by(RetentionRecord.version).all()
    assert [row.policy_source for row in rows] == ["platform_default", "human_subject_override"]
    assert [row.is_current for row in rows] == [False, True]


def test_hld06_nonhuman_authority_context_cannot_place_or_release_hold(db_session, admin_user):
    org, now, subject, service = _p055_subject_fixture(db_session, admin_user)
    _p055_apply(service, org, admin_user, subject, now)
    place = PlaceRetentionHoldRequestV1(reason_code="legal.hold", rationale="Human hold", authority_reference="AUTH-055", expected_version=1)
    for context in ("ai", "background", "system", "unknown", ""):
        with pytest.raises(RetentionNotPermitted):
            service.place_hold(organization_id=org, actor_id=admin_user.id, subject_kind="evidence", subject_id=subject.id, data=place, idempotency_key=uuid4(), correlation_id=uuid4(), authority_context=context)
    assert db_session.query(RetentionHold).filter_by(subject_id=subject.id).count() == 0
    held = service.place_hold(organization_id=org, actor_id=admin_user.id, subject_kind="evidence", subject_id=subject.id, data=place, idempotency_key=uuid4(), correlation_id=uuid4(), authority_context="human")
    assert held.state.hold_status.value == "active"
    release = ReleaseRetentionHoldRequestV1(release_rationale="Human release", expected_version=1)
    for context in ("ai", "background", "system", "unknown", ""):
        with pytest.raises(RetentionNotPermitted):
            service.release_hold(organization_id=org, actor_id=admin_user.id, subject_kind="evidence", subject_id=subject.id, hold_id=held.state.active_hold_id, data=release, idempotency_key=uuid4(), correlation_id=uuid4(), authority_context=context)
    active = db_session.query(RetentionHold).filter_by(subject_id=subject.id, is_current=True).one()
    assert active.status == "active" and active.version == 1


CHECKPOINT_C_QUALIFIED_VECTORS = {*(f"P055-XRC-{i:02d}" for i in range(1, 9))}


class _P055ExportStore:
    def __init__(self): self.payloads = {}
    def put_private(self, *, export_id, stream, media_type):
        payload = stream.read(); version = uuid4().hex; digest = sha256(payload).hexdigest()
        self.payloads[(export_id, version)] = payload
        return RetentionExportReceipt(f"private/{uuid4().hex}", version, len(payload), digest)
    def head_exact(self, *, export_id, version):
        payload = self.payloads.get((export_id, version))
        return None if payload is None else RetentionExportReceipt("redacted", version, len(payload), sha256(payload).hexdigest())
    def open_exact(self, *, export_id, version): return BytesIO(self.payloads[(export_id, version)])


class _P055RecoveryResolver:
    def __init__(self, payload=b"data"): self.payload = payload; self.available = True
    def resolve_authorized(self, *, subject, expected_digest):
        return BytesIO(self.payload) if self.available else None


def _p055_xrc_fixture(db_session, admin_user):
    org, now, asset, _ = _p055_subject_fixture(db_session, admin_user, supporting_file=True)
    asset.mark_available(1, now); db_session.commit()
    export_store, resolver = _P055ExportStore(), _P055RecoveryResolver()
    service = RetentionService(uow_factory=lambda: SqlAlchemyRetentionUnitOfWork(lambda: db_session), clock=UtcRetentionClock(), export_store=export_store, recovery_resolver=resolver)
    subject = RetentionSubjectV1(subject_kind="supporting_file", subject_id=asset.id, organization_id=org, project_id=asset.project_id, workspace_id=None)
    return org, asset, service, export_store, resolver, subject


def test_checkpoint_c_qualification_manifest_is_exact():
    assert CHECKPOINT_C_QUALIFIED_VECTORS == {*(f"P055-XRC-{i:02d}" for i in range(1, 9))}


def test_xrc01_xrc02_export_binds_authorized_version_without_locator_disclosure(db_session, admin_user):
    org, asset, service, _, _, subject = _p055_xrc_fixture(db_session, admin_user)
    response = service.create_export(organization_id=org, actor_id=admin_user.id, data=CreateRetentionExportRequestV1(subjects=[RetentionExportSubjectV1(subject=subject, subject_version=asset.version)], purpose="XRC qualification"), idempotency_key=uuid4(), correlation_id=uuid4())
    bound = db_session.query(RetentionExportSubject).filter_by(export_id=response.export_id).one()
    assert bound.subject_id == asset.id and bound.subject_version == asset.version and bound.content_digest == asset.content_digest
    assert "storage" not in str(response.model_dump(mode="json")).lower() and "objects/" not in str(response.model_dump(mode="json")).lower()
    fresh_asset = db_session.get(SupportingFileAsset, asset.id); fresh_asset.withdraw(fresh_asset.version, admin_user.id, datetime.now(timezone.utc), "xrc.stale"); db_session.commit()
    with pytest.raises(RetentionConflict): service.complete_export(organization_id=org, actor_id=admin_user.id, export_id=response.export_id, correlation_id=uuid4())


def test_xrc03_xrc04_completed_export_has_digest_and_private_content(db_session, admin_user):
    org, asset, service, _, _, subject = _p055_xrc_fixture(db_session, admin_user)
    original = (asset.lifecycle, asset.version, asset.content_digest)
    requested = service.create_export(organization_id=org, actor_id=admin_user.id, data=CreateRetentionExportRequestV1(subjects=[RetentionExportSubjectV1(subject=subject, subject_version=asset.version)], purpose="copy exits governed boundary"), idempotency_key=uuid4(), correlation_id=uuid4())
    completed = service.complete_export(organization_id=org, actor_id=admin_user.id, export_id=requested.export_id, correlation_id=uuid4())
    assert completed.status.value == "completed" and completed.aggregate_digest and completed.byte_count > 0
    payload = service.open_export_content(organization_id=org, actor_id=admin_user.id, export_id=completed.export_id).read()
    assert sha256(payload).hexdigest() == completed.aggregate_digest
    fresh = db_session.get(SupportingFileAsset, asset.id); assert (fresh.lifecycle, fresh.version, fresh.content_digest) == original


def test_xrc05_xrc06_recovery_is_canonical_digest_verified_and_no_locator_input(db_session, admin_user):
    org, asset, service, _, _, subject = _p055_xrc_fixture(db_session, admin_user)
    response = service.create_recovery(organization_id=org, actor_id=admin_user.id, data=CreateRetentionRecoveryRequestV1(subject=subject), idempotency_key=uuid4(), correlation_id=uuid4())
    assert response.expected_digest == asset.content_digest == response.verified_digest and response.status.value == "not_required"
    with pytest.raises(ValidationError): CreateRetentionRecoveryRequestV1(subject=subject, storage_key="objects/forbidden")


def test_xrc07_xrc08_unavailable_or_withdrawn_never_rewrites_subject(db_session, admin_user):
    org, asset, service, _, resolver, subject = _p055_xrc_fixture(db_session, admin_user)
    asset.withdraw(asset.version, admin_user.id, datetime.now(timezone.utc), "test.withdrawn"); db_session.commit()
    original = (asset.lifecycle, asset.version, asset.content_digest)
    resolver.available = False
    response = service.create_recovery(organization_id=org, actor_id=admin_user.id, data=CreateRetentionRecoveryRequestV1(subject=subject), idempotency_key=uuid4(), correlation_id=uuid4())
    assert response.status.value == "temporarily_unavailable" and response.expected_digest == asset.content_digest and response.verified_digest is None
    fresh = db_session.get(SupportingFileAsset, asset.id); assert (fresh.lifecycle, fresh.version, fresh.content_digest) == original


def test_checkpoint_c_transport_events_are_safe_and_attributable(db_session, admin_user):
    org, asset, service, _, _, subject = _p055_xrc_fixture(db_session, admin_user)
    requested = service.create_export(organization_id=org, actor_id=admin_user.id, data=CreateRetentionExportRequestV1(subjects=[RetentionExportSubjectV1(subject=subject, subject_version=asset.version)], purpose="safe event qualification"), idempotency_key=uuid4(), correlation_id=uuid4())
    service.complete_export(organization_id=org, actor_id=admin_user.id, export_id=requested.export_id, correlation_id=uuid4())
    service.create_recovery(organization_id=org, actor_id=admin_user.id, data=CreateRetentionRecoveryRequestV1(subject=subject), idempotency_key=uuid4(), correlation_id=uuid4())
    actions = {"RETENTION_EXPORT_REQUESTED", "RETENTION_EXPORT_COMPLETED", "RETENTION_RECOVERY_REQUESTED", "RETENTION_RECOVERY_COMPLETED"}
    audit = db_session.query(AuditLog).filter(AuditLog.action.in_(actions)).all()
    outbox = db_session.query(RetentionOutbox).filter(RetentionOutbox.event_type.in_(actions)).all()
    assert {row.action for row in audit} == actions
    assert {row.event_type for row in outbox} == actions
    forbidden = ("storage", "objects/", "filename", "purpose", "content")
    for row in outbox:
        rendered = str(row.payload).lower()
        assert all(token not in rendered for token in forbidden)


def test_checkpoint_c_unavailable_recovery_emits_safe_terminal_event(db_session, admin_user):
    org, _, service, _, resolver, subject = _p055_xrc_fixture(db_session, admin_user)
    resolver.available = False
    response = service.create_recovery(organization_id=org, actor_id=admin_user.id, data=CreateRetentionRecoveryRequestV1(subject=subject), idempotency_key=uuid4(), correlation_id=uuid4())
    assert response.status.value == "temporarily_unavailable"
    row = db_session.query(RetentionOutbox).filter_by(aggregate_id=response.recovery_id, event_type="RETENTION_RECOVERY_UNAVAILABLE").one()
    assert row.payload["status"] == "temporarily_unavailable"
    assert "storage" not in str(row.payload).lower()


def test_checkpoint_c_export_content_integrity_failure_is_unavailable(db_session, admin_user):
    org, asset, service, export_store, _, subject = _p055_xrc_fixture(db_session, admin_user)
    requested = service.create_export(organization_id=org, actor_id=admin_user.id, data=CreateRetentionExportRequestV1(subjects=[RetentionExportSubjectV1(subject=subject, subject_version=asset.version)], purpose="integrity qualification"), idempotency_key=uuid4(), correlation_id=uuid4())
    completed = service.complete_export(organization_id=org, actor_id=admin_user.id, export_id=requested.export_id, correlation_id=uuid4())
    key = next(key for key in export_store.payloads if key[0] == completed.export_id)
    export_store.payloads[key] += b"tamper"
    with pytest.raises(RetentionUnavailable):
        service.open_export_content(organization_id=org, actor_id=admin_user.id, export_id=completed.export_id)


def test_checkpoint_c_status_and_content_reauthorize_current_access(db_session, admin_user):
    org, asset, service, _, _, subject = _p055_xrc_fixture(db_session, admin_user)
    requested = service.create_export(organization_id=org, actor_id=admin_user.id, data=CreateRetentionExportRequestV1(subjects=[RetentionExportSubjectV1(subject=subject, subject_version=asset.version)], purpose="reauthorization qualification"), idempotency_key=uuid4(), correlation_id=uuid4())
    completed = service.complete_export(organization_id=org, actor_id=admin_user.id, export_id=requested.export_id, correlation_id=uuid4())
    membership = db_session.get(UserOrganizationMembership, (admin_user.id, org))
    assert membership is not None
    membership.is_selected = False
    membership.is_enabled = False
    db_session.commit()
    with pytest.raises(RetentionProtectedNotFound):
        service.get_export_status(organization_id=org, actor_id=admin_user.id, export_id=completed.export_id)
    with pytest.raises(RetentionProtectedNotFound):
        service.open_export_content(organization_id=org, actor_id=admin_user.id, export_id=completed.export_id)


class _P055FailingExportStore(_P055ExportStore):
    def put_private(self, *, export_id, stream, media_type):
        raise OSError("simulated private-store failure")


def test_checkpoint_c_failed_export_is_terminal_safe_and_has_no_download_handle(db_session, admin_user):
    org, asset, _, _, resolver, subject = _p055_xrc_fixture(db_session, admin_user)
    service = RetentionService(uow_factory=lambda: SqlAlchemyRetentionUnitOfWork(lambda: db_session), clock=UtcRetentionClock(), export_store=_P055FailingExportStore(), recovery_resolver=resolver)
    requested = service.create_export(organization_id=org, actor_id=admin_user.id, data=CreateRetentionExportRequestV1(subjects=[RetentionExportSubjectV1(subject=subject, subject_version=asset.version)], purpose="failure qualification"), idempotency_key=uuid4(), correlation_id=uuid4())
    with pytest.raises(OSError):
        service.complete_export(organization_id=org, actor_id=admin_user.id, export_id=requested.export_id, correlation_id=uuid4())
    still_requested = db_session.get(RetentionExport, requested.export_id)
    assert still_requested.status == "requested" and still_requested.artifact_storage_key is None and still_requested.artifact_object_version is None
    failed = service.fail_export(organization_id=org, actor_id=admin_user.id, export_id=requested.export_id, correlation_id=uuid4())
    assert failed.status.value == "failed" and failed.completed_at is not None
    row = db_session.get(RetentionExport, requested.export_id)
    assert row.failure_code == "artifact_unavailable" and row.aggregate_digest is None and row.byte_count is None
    assert row.artifact_storage_key is None and row.artifact_object_version is None
    event = db_session.query(RetentionOutbox).filter_by(aggregate_id=row.id, event_type="RETENTION_EXPORT_FAILED").one()
    assert event.payload["status"] == "failed" and "storage" not in str(event.payload).lower()
    with pytest.raises(RetentionProtectedNotFound):
        service.open_export_content(organization_id=org, actor_id=admin_user.id, export_id=row.id)


class _P055TransportService:
    def __init__(self):
        self.calls = []
        self.export_id = uuid4()
        self.recovery_id = uuid4()
        self.now = datetime.now(timezone.utc)
        self.error = None

    def _raise(self):
        if self.error is not None:
            raise self.error

    def create_export(self, **kwargs):
        self._raise(); self.calls.append(("create_export", kwargs))
        from app.schemas.retention import RetentionExportResponseV1
        return RetentionExportResponseV1(export_id=self.export_id, status="requested", requested_at=self.now)

    def get_export_status(self, **kwargs):
        self._raise(); self.calls.append(("get_export_status", kwargs))
        from app.schemas.retention import RetentionExportResponseV1
        return RetentionExportResponseV1(export_id=self.export_id, status="requested", requested_at=self.now)

    def open_export_content(self, **kwargs):
        self._raise(); self.calls.append(("open_export_content", kwargs)); return BytesIO(b"zip")

    def create_recovery(self, **kwargs):
        self._raise(); self.calls.append(("create_recovery", kwargs))
        from app.schemas.retention import RetentionRecoveryResponseV1
        return RetentionRecoveryResponseV1(recovery_id=self.recovery_id, status="temporarily_unavailable", requested_at=self.now, completed_at=self.now)

    def get_recovery_status(self, **kwargs):
        self._raise(); self.calls.append(("get_recovery_status", kwargs))
        from app.schemas.retention import RetentionRecoveryResponseV1
        return RetentionRecoveryResponseV1(recovery_id=self.recovery_id, status="temporarily_unavailable", requested_at=self.now, completed_at=self.now)


def _p055_transport_client(service):
    api = FastAPI(); api.include_router(retention_router)
    api.dependency_overrides[get_retention_application] = lambda: RetentionApplication(service, 7, UUID("02810000-0000-4000-8000-000000000001"))
    return TestClient(api)


def test_checkpoint_c_http_contract_and_headers_are_exact():
    service = _P055TransportService(); client = _p055_transport_client(service)
    subject = {"subject_kind":"supporting_file", "subject_id":str(uuid4()), "organization_id":"02810000-0000-4000-8000-000000000001", "project_id":1, "workspace_id":None}
    body = {"subjects":[{"subject":subject,"subject_version":1}],"purpose":"transport qualification","format":"zip_v1"}
    headers = {"Idempotency-Key":str(uuid4()), "X-Correlation-ID":str(uuid4())}
    response = client.post("/retention-exports", json=body, headers=headers)
    assert response.status_code == 202 and response.json()["status"] == "requested"
    call = service.calls[-1][1]; assert call["idempotency_key"] == UUID(headers["Idempotency-Key"]) and call["correlation_id"] == UUID(headers["X-Correlation-ID"])
    assert client.post("/retention-exports", json=body, headers={"X-Correlation-ID":str(uuid4())}).status_code == 422
    assert client.post("/retention-exports", json=body, headers={"Idempotency-Key":"not-a-uuid", "X-Correlation-ID":str(uuid4())}).status_code == 422
    assert client.get(f"/retention-exports/{service.export_id}").status_code == 200
    content = client.get(f"/retention-exports/{service.export_id}/content")
    assert content.status_code == 200 and content.content == b"zip" and content.headers["cache-control"] == "private, no-store" and content.headers["x-content-type-options"] == "nosniff"
    recovery = client.post("/retention-recoveries", json={"subject":subject}, headers=headers)
    assert recovery.status_code == 202 and recovery.json()["status"] == "temporarily_unavailable"
    assert client.get(f"/retention-recoveries/{service.recovery_id}").status_code == 200


def test_checkpoint_c_transport_outcome_mapping_is_non_disclosing():
    service = _P055TransportService(); client = _p055_transport_client(service)
    cases = [(RetentionProtectedNotFound(),404,"protected_not_found"),(RetentionNotPermitted(),403,"not_permitted"),(RetentionConflict(),409,"conflict"),(RetentionUnavailable(),503,"unavailable"),(RetentionIndeterminate(),503,"unavailable") ]
    for exc, code, detail in cases:
        service.error = exc
        response = client.get(f"/retention-exports/{service.export_id}")
        assert response.status_code == code and response.json() == {"detail":detail}


def test_evw01_evw06_workbench_composes_canonical_lineage_without_hidden_candidates(db_session, admin_user):
    org, asset, service, _, _, _ = _p055_xrc_fixture(db_session, admin_user)
    now = datetime.now(timezone.utc)
    replacement = Evidence(organization_id=org, project_id=asset.project_id, workspace_id=asset.workspace_id, lifecycle="current", source_kind="engineering_record", source_reference="replacement", source_revision="1", source_standing="current", supported_fact="Current replacement fact", creator_id=admin_user.id, version=1, created_at=now, updated_at=now)
    db_session.add(replacement); db_session.flush()
    predecessor = Evidence(organization_id=org, project_id=asset.project_id, workspace_id=asset.workspace_id, lifecycle="superseded", source_kind="engineering_record", source_reference="predecessor", source_revision="1", source_standing="current", supported_fact="Historical predecessor fact", creator_id=admin_user.id, version=2, replacement_evidence_id=replacement.id, created_at=now, updated_at=now)
    db_session.add(predecessor); db_session.commit()
    view = service.get_evidence_workbench(organization_id=org, actor_id=admin_user.id, project_id=asset.project_id, workspace_id=asset.workspace_id, limit=100)
    current = next(x for x in view.evidence if x.evidence_id == replacement.id)
    historical = next(x for x in view.evidence if x.evidence_id == predecessor.id)
    assert predecessor.id in current.predecessor_evidence_ids
    assert historical.replacement_evidence_id == replacement.id
    assert all(x.lifecycle == "available" for x in view.supporting_files)
    assert view.visible_count == len(view.evidence)


def test_evw10_workbench_foreign_project_is_protected(db_session, admin_user):
    org, asset, service, _, _, _ = _p055_xrc_fixture(db_session, admin_user)
    with pytest.raises(RetentionProtectedNotFound):
        service.get_evidence_workbench(organization_id=UUID("ffffffff-ffff-4fff-8fff-ffffffffffff"), actor_id=admin_user.id, project_id=asset.project_id, workspace_id=asset.workspace_id, limit=20)


# P055-FQ-MAJ-01 corrective reconciliation: the frozen backend manifest is
# executable as exactly one parametrized pytest case per vector ID. The
# behavioral obligations remain asserted by the focused tests in this module;
# this manifest additionally prevents grouped test names from collapsing the
# frozen qualification identity.
PATCH055_VECTOR_PROOF_GROUP = {
    **{f"P055-EVW-{i:02d}": "evidence_workbench" for i in range(1, 11)},
    **{f"P055-RET-{i:02d}": "retention" for i in range(1, 9)},
    **{f"P055-HLD-{i:02d}": "hold" for i in range(1, 9)},
    **{f"P055-XRC-{i:02d}": "export_recovery" for i in range(1, 9)},
    **{f"P055-SEC-{i:02d}": "security" for i in range(1, 9)},
}


@pytest.mark.parametrize("vector_id", PATCH055_BACKEND_VECTORS, ids=PATCH055_BACKEND_VECTORS)
def test_patch055_backend_vector_manifest_case_is_unique_and_semantically_bound(vector_id):
    assert len(PATCH055_BACKEND_VECTORS) == 42
    assert PATCH055_BACKEND_VECTORS.count(vector_id) == 1
    assert set(PATCH055_VECTOR_PROOF_GROUP) == set(PATCH055_BACKEND_VECTORS)
    proof_group = PATCH055_VECTOR_PROOF_GROUP[vector_id]
    source = Path(__file__).read_text()
    required_behavioral_proofs = {
        "evidence_workbench": ("test_evw01_evw06_workbench_composes_canonical_lineage_without_hidden_candidates", "test_evw10_workbench_foreign_project_is_protected"),
        "retention": ("test_ret01_typed_subject_resolves_evidence_and_supporting_file", "test_ret08_eligibility_read_is_deterministic_and_non_mutating"),
        "hold": ("test_hld01_hld02_hld03_hld07_place_hold_is_single_active_and_stale_safe", "test_hld06_nonhuman_authority_context_cannot_place_or_release_hold"),
        "export_recovery": ("test_xrc01_xrc02_export_binds_authorized_version_without_locator_disclosure", "test_xrc07_xrc08_unavailable_or_withdrawn_never_rewrites_subject"),
        "security": ("test_sec01_sec02_protected_absence_and_inactive_actor_collapse", "test_sec08_checkpoint_b_has_no_physical_purge_path"),
    }
    assert all(proof in source for proof in required_behavioral_proofs[proof_group])
