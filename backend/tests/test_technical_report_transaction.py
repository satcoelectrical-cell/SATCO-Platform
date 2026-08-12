"""Focused PATCH-032 Batch 4 transaction and Audit evidence."""

from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
import json
from threading import Event
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.models.audit_log import AuditLog
from app.models.technical_report import (
    TechnicalReport,
    TechnicalReportProvenanceRecord,
    TechnicalReportRecord,
)
from app.models.organization import UserOrganizationMembership
from app.models.engineering_object import EngineeringObject
from app.models.engineering_relationship import EngineeringRelationship
from app.models.engineering_experience_capture import EngineeringExperienceCapture
from app.models.evidence import Evidence
from app.models.technical_report_command import (
    AcceptExactTechnicalReportDraft,
    AcceptanceConfirmation,
    CaptureHistoricalBasisV1,
    CreateTechnicalReportDraft,
    PreliminaryQualification,
    TechnicalReportActor,
    TechnicalReportCommandResult,
    TechnicalReportDomainEvent,
    TechnicalReportDraftRevision,
    TechnicalReportIdempotencyRecord,
    TechnicalReportOutboxRecord,
    TechnicalReportCommandMetadata,
    TechnicalReportContent,
    TechnicalReportProvenanceEntry,
    historical_basis_digest,
)
from app.enums.technical_report import TechnicalReportIntegrityAlgorithm
from app.exceptions.technical_report import (
    TechnicalReportAuthorizationDenied,
    TechnicalReportHistoricalBasisIncomplete,
    TechnicalReportIdempotencyConflict,
    TechnicalReportVersionConflict,
)
from app.ports.technical_report import (
    TechnicalReportAuditRecord,
    TechnicalReportAuthorizationRequest,
    AcceptExactDraftHistoricalAuthority,
    TechnicalReportFinalRecheckRequest,
    TechnicalReportScope,
    TechnicalReportHistoricalRequest,
    TechnicalReportIdempotencyKey,
    TechnicalReportRejectionAuditRecord,
    TechnicalReportRejectionReason,
)
from app.repositories.technical_report_unit_of_work import (
    SqlAlchemyTechnicalReportAuditRecorder,
    SqlAlchemyTechnicalReportDomainEventRecorder,
    SqlAlchemyTechnicalReportIdempotencyStore,
    SqlAlchemyTechnicalReportRejectionAuditRecorder,
    SqlAlchemyTechnicalReportUnitOfWork,
)
from app.repositories.technical_report_repository import (
    SqlAlchemyTechnicalReportRepository,
)


def _report(db_session, relationship_domain):
    actor = relationship_domain["actors"]["project_owner"]
    project = relationship_domain["project"]
    workspace = relationship_domain["consumer_workspace"]
    now = datetime.now(timezone.utc)
    report = TechnicalReportRecord(
        id=uuid4(),
        organization_id=project.organization_id,
        workspace_id=workspace.id,
        project_id=project.id,
        owner_id=actor.id,
        purpose="engineering_analysis",
        engineering_scope="Authorized equipment scope",
        draft_content="Protected technical content",
        assumptions=[],
        uncertainty="Known limitations are recorded",
        limitations=[],
        conclusions="Draft conclusion",
        recommendations=[],
        is_preliminary=False,
        evidence_deficiencies=[],
        unresolved_issues=[],
        follow_up_requirements=[],
        draft_revision_id=uuid4(),
        draft_revision_number=1,
        lifecycle="draft",
        version=1,
        created_at=now,
        updated_at=now,
    )
    db_session.add(report)
    db_session.flush()
    return report, actor, now


def _operation(report, actor, now):
    command_id = uuid4()
    correlation_id = uuid4()
    event = TechnicalReportDomainEvent(
        event_id=uuid4(),
        report_id=report.id,
        aggregate_version=report.version,
        event_type="TechnicalReportDraftCreated",
        command_id=command_id,
        correlation_id=correlation_id,
        occurred_at=now,
        organization_id=report.organization_id,
        workspace_id=report.workspace_id,
        project_id=report.project_id,
        purpose=report.purpose,
        lifecycle=report.lifecycle,
        draft_revision_id=report.draft_revision_id,
        actor_id=actor.id,
        causation_id=command_id,
        predecessor_report_id=report.predecessor_report_id,
        source_entry_count=0,
    )
    result = TechnicalReportCommandResult(
        report_id=report.id,
        previous_version=None,
        version=report.version,
        draft_revision=TechnicalReportDraftRevision(
            report.draft_revision_id, report.draft_revision_number
        ),
        command_type="CreateTechnicalReportDraft",
        correlation_id=correlation_id,
        events=(event,),
    )
    audit = TechnicalReportAuditRecord(
        actor_id=actor.id,
        organization_id=report.organization_id,
        report_id=report.id,
        operation=result.command_type,
        command_id=command_id,
        correlation_id=correlation_id,
        occurred_at=now,
    )
    key = TechnicalReportIdempotencyKey(
        organization_id=report.organization_id,
        actor_id=actor.id,
        command_type=result.command_type,
        idempotency_id=uuid4(),
    )
    return event, result, audit, key


def _factory(db_session):
    return sessionmaker(
        bind=db_session.get_bind(), expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )


def _contextual_provenance(report_id):
    return TechnicalReportProvenanceRecord(
        id=uuid4(), technical_report_id=report_id, ordinal=0,
        source_class="contextual_non_material", source_type="contextual",
        is_material=False, owning_capability=None, reliance_role="context",
        verification_status="unverified", availability_status="available",
        origin_attribution="authorized context", limitations=[],
        context_id=uuid4(), owning_context="engineering_context",
    )


def _domain_report(relationship_domain, now):
    actor = relationship_domain["actors"]["project_owner"]
    project = relationship_domain["project"]
    workspace = relationship_domain["consumer_workspace"]
    metadata = TechnicalReportCommandMetadata(
        TechnicalReportActor(actor.id, project.organization_id),
        "Human engineering rationale", uuid4(), uuid4(), uuid4(),
    )
    basis = CaptureHistoricalBasisV1(
        1, "universal_capture", uuid4(), 1, project.organization_id,
        project.id, workspace.id, "electrical", uuid4(), "observation",
        "Authorized historical content", "field-note", actor.id, "captured", now,
    )
    provenance = TechnicalReportProvenanceEntry(
        uuid4(), 0, "canonical_material", "universal_capture", True,
        "universal_capture", "primary observation", "verified", "available",
        "Authenticated engineer", (), basis,
        TechnicalReportIntegrityAlgorithm.SHA256, historical_basis_digest(basis),
    )
    report, _result = TechnicalReport.create(
        CreateTechnicalReportDraft(
            metadata, project.organization_id, workspace.id, project.id, actor.id,
            "engineering_analysis",
            TechnicalReportContent(
                "Authorized scope", "Accepted technical conclusion", (),
                "Known uncertainty", (), "Human conclusion", (),
            ),
            PreliminaryQualification(False), (provenance,),
        ),
        now,
    )
    return report, actor, metadata


def _accountability(report, actor, result, now):
    event = result.events[0]
    audit = TechnicalReportAuditRecord(
        actor.id, report.organization_id, report.id, result.command_type,
        event.command_id, result.correlation_id, now,
    )
    key = TechnicalReportIdempotencyKey(
        report.organization_id, actor.id, result.command_type, uuid4(),
    )
    return event, audit, key


def test_unit_of_work_owns_one_shared_session_and_commit():
    session = MagicMock()
    with SqlAlchemyTechnicalReportUnitOfWork(lambda: session) as uow:
        assert uow.technical_reports.session is session
        assert uow.historical.session is session
        assert uow.audit.session is session
        assert uow.domain_events.session is session
        assert uow.idempotency.session is session
        uow.commit()

    session.commit.assert_called_once_with()
    session.rollback.assert_not_called()
    session.close.assert_called_once_with()


def test_unit_of_work_rolls_back_once_on_failure_without_commit():
    session = MagicMock()
    with pytest.raises(RuntimeError, match="injected failure"):
        with SqlAlchemyTechnicalReportUnitOfWork(lambda: session):
            raise RuntimeError("injected failure")

    session.rollback.assert_called_once_with()
    session.commit.assert_not_called()
    session.close.assert_called_once_with()


def test_success_side_records_stage_in_one_session(
    db_session, relationship_domain
):
    report, actor, now = _report(db_session, relationship_domain)
    event, result, audit, key = _operation(report, actor, now)

    SqlAlchemyTechnicalReportAuditRecorder(db_session).record(audit)
    SqlAlchemyTechnicalReportDomainEventRecorder(db_session).record((event,))
    store = SqlAlchemyTechnicalReportIdempotencyStore(db_session)
    store.reserve(key, "a" * 64)
    store.record_result(key, result)
    db_session.flush()

    assert db_session.query(AuditLog).filter_by(
        entity="TECHNICAL_REPORT", entity_uuid=report.id
    ).count() == 1
    assert db_session.query(TechnicalReportOutboxRecord).filter_by(
        aggregate_id=report.id
    ).count() == 1
    assert db_session.query(TechnicalReportIdempotencyRecord).filter_by(
        aggregate_id=report.id, status="completed"
    ).count() == 1
    stored = db_session.query(TechnicalReportIdempotencyRecord).filter_by(
        aggregate_id=report.id, status="completed"
    ).one().result
    assert stored["safe_result_schema_version"] == 1
    assert "Protected technical content" not in json.dumps(stored)
    assert store.find(key, "a" * 64) == result


def test_injected_failure_rolls_back_all_staged_success_records(
    db_session, relationship_domain
):
    report, actor, now = _report(db_session, relationship_domain)
    event, result, audit, key = _operation(report, actor, now)
    savepoint = db_session.begin_nested()

    SqlAlchemyTechnicalReportAuditRecorder(db_session).record(audit)
    SqlAlchemyTechnicalReportDomainEventRecorder(db_session).record((event,))
    store = SqlAlchemyTechnicalReportIdempotencyStore(db_session)
    store.reserve(key, "b" * 64)
    store.record_result(key, result)
    db_session.flush()
    savepoint.rollback()

    assert db_session.query(AuditLog).filter_by(entity_uuid=report.id).count() == 0
    assert db_session.query(TechnicalReportOutboxRecord).filter_by(
        aggregate_id=report.id
    ).count() == 0
    assert db_session.query(TechnicalReportIdempotencyRecord).filter_by(
        aggregate_id=report.id
    ).count() == 0


def test_actual_uow_commits_report_provenance_and_side_records_atomically(
    db_session, relationship_domain
):
    report, actor, now = _report(db_session, relationship_domain)
    event, result, audit, key = _operation(report, actor, now)
    with SqlAlchemyTechnicalReportUnitOfWork(_factory(db_session)) as uow:
        persisted = uow.session.get(TechnicalReportRecord, report.id)
        persisted.draft_content = "Atomic revised content"
        uow.session.add(_contextual_provenance(report.id))
        uow.audit.record(audit)
        uow.domain_events.record((event,))
        uow.idempotency.reserve(key, "d" * 64)
        uow.idempotency.record_result(key, result)
        uow.commit()

    db_session.expire_all()
    assert db_session.get(TechnicalReportRecord, report.id).draft_content == "Atomic revised content"
    assert db_session.query(TechnicalReportProvenanceRecord).filter_by(
        technical_report_id=report.id
    ).count() == 1
    assert db_session.query(AuditLog).filter_by(entity_uuid=report.id).count() == 1
    assert db_session.query(TechnicalReportOutboxRecord).filter_by(aggregate_id=report.id).count() == 1
    assert db_session.query(TechnicalReportIdempotencyRecord).filter_by(aggregate_id=report.id).count() == 1


@pytest.mark.parametrize("failure_after", ["report", "provenance", "audit", "outbox", "idempotency"])
def test_actual_uow_rolls_back_every_staged_failure(
    db_session, relationship_domain, failure_after
):
    report, actor, now = _report(db_session, relationship_domain)
    event, result, audit, key = _operation(report, actor, now)
    with pytest.raises(RuntimeError, match="stage failure"):
        with SqlAlchemyTechnicalReportUnitOfWork(_factory(db_session)) as uow:
            persisted = uow.session.get(TechnicalReportRecord, report.id)
            persisted.draft_content = "must roll back"
            if failure_after == "report": raise RuntimeError("stage failure")
            uow.session.add(_contextual_provenance(report.id)); uow.session.flush()
            if failure_after == "provenance": raise RuntimeError("stage failure")
            uow.audit.record(audit); uow.session.flush()
            if failure_after == "audit": raise RuntimeError("stage failure")
            uow.domain_events.record((event,)); uow.session.flush()
            if failure_after == "outbox": raise RuntimeError("stage failure")
            uow.idempotency.reserve(key, "e" * 64)
            uow.idempotency.record_result(key, result); uow.session.flush()
            raise RuntimeError("stage failure")

    db_session.expire_all()
    assert db_session.get(TechnicalReportRecord, report.id).draft_content == "Protected technical content"
    assert db_session.query(TechnicalReportProvenanceRecord).filter_by(technical_report_id=report.id).count() == 0
    assert db_session.query(AuditLog).filter_by(entity_uuid=report.id).count() == 0
    assert db_session.query(TechnicalReportOutboxRecord).filter_by(aggregate_id=report.id).count() == 0
    assert db_session.query(TechnicalReportIdempotencyRecord).filter_by(aggregate_id=report.id).count() == 0


def test_actual_uow_commits_acceptance_snapshot_provenance_and_side_records(
    db_session, relationship_domain
):
    now = datetime.now(timezone.utc)
    report, actor, metadata = _domain_report(relationship_domain, now)
    SqlAlchemyTechnicalReportRepository(db_session).add(report)
    db_session.flush()

    with SqlAlchemyTechnicalReportUnitOfWork(_factory(db_session)) as uow:
        loaded = uow.technical_reports.get_scoped(report.id, report.organization_id)
        result = loaded.accept_exact_draft(
            AcceptExactTechnicalReportDraft(
                metadata, loaded.id,
                AcceptanceConfirmation(
                    loaded.version, loaded.draft_revision_id, True,
                ),
            ),
            now + timedelta(seconds=1),
        )
        assert uow.technical_reports.persist_acceptance_expected_version(loaded, 1)
        event, audit, key = _accountability(loaded, actor, result, now)
        uow.audit.record(audit)
        uow.domain_events.record((event,))
        uow.idempotency.reserve(key, "1" * 64)
        uow.idempotency.record_result(key, result)
        uow.commit()

    db_session.expire_all()
    persisted = db_session.get(TechnicalReportRecord, report.id)
    assert persisted.lifecycle == "accepted"
    assert persisted.version == 2
    assert persisted.accepted_snapshot is not None
    assert persisted.accepted_snapshot_digest is not None
    assert db_session.query(TechnicalReportProvenanceRecord).filter_by(
        technical_report_id=report.id,
    ).count() == 1
    assert db_session.query(AuditLog).filter_by(entity_uuid=report.id).count() == 1
    assert db_session.query(TechnicalReportOutboxRecord).filter_by(
        aggregate_id=report.id,
    ).count() == 1
    assert db_session.query(TechnicalReportIdempotencyRecord).filter_by(
        aggregate_id=report.id,
    ).count() == 1


@pytest.mark.parametrize(
    "failure_after",
    ["acceptance", "audit", "outbox", "idempotency"],
)
def test_actual_uow_acceptance_failure_rolls_back_all_authoritative_state(
    db_session, relationship_domain, failure_after
):
    now = datetime.now(timezone.utc)
    report, actor, metadata = _domain_report(relationship_domain, now)
    SqlAlchemyTechnicalReportRepository(db_session).add(report)
    db_session.flush()
    initial_provenance = db_session.query(TechnicalReportProvenanceRecord).filter_by(
        technical_report_id=report.id,
    ).count()

    with pytest.raises(RuntimeError, match="acceptance failure"):
        with SqlAlchemyTechnicalReportUnitOfWork(_factory(db_session)) as uow:
            loaded = uow.technical_reports.get_scoped(report.id, report.organization_id)
            result = loaded.accept_exact_draft(
                AcceptExactTechnicalReportDraft(
                    metadata, loaded.id,
                    AcceptanceConfirmation(
                        loaded.version, loaded.draft_revision_id, True,
                    ),
                ),
                now + timedelta(seconds=1),
            )
            assert uow.technical_reports.persist_acceptance_expected_version(loaded, 1)
            if failure_after == "acceptance":
                raise RuntimeError("acceptance failure")
            event, audit, key = _accountability(loaded, actor, result, now)
            uow.audit.record(audit); uow.session.flush()
            if failure_after == "audit":
                raise RuntimeError("acceptance failure")
            uow.domain_events.record((event,)); uow.session.flush()
            if failure_after == "outbox":
                raise RuntimeError("acceptance failure")
            uow.idempotency.reserve(key, "2" * 64)
            uow.idempotency.record_result(key, result); uow.session.flush()
            raise RuntimeError("acceptance failure")

    db_session.expire_all()
    persisted = db_session.get(TechnicalReportRecord, report.id)
    assert persisted.lifecycle == "draft"
    assert persisted.version == 1
    assert persisted.accepted_snapshot is None
    assert db_session.query(TechnicalReportProvenanceRecord).filter_by(
        technical_report_id=report.id,
    ).count() == initial_provenance
    assert db_session.query(AuditLog).filter_by(entity_uuid=report.id).count() == 0
    assert db_session.query(TechnicalReportOutboxRecord).filter_by(
        aggregate_id=report.id,
    ).count() == 0
    assert db_session.query(TechnicalReportIdempotencyRecord).filter_by(
        aggregate_id=report.id,
    ).count() == 0


def test_operational_records_exclude_protected_plaintext(
    db_session, relationship_domain
):
    report, actor, now = _report(db_session, relationship_domain)
    event, result, audit, key = _operation(report, actor, now)
    SqlAlchemyTechnicalReportAuditRecorder(db_session).record(audit)
    SqlAlchemyTechnicalReportDomainEventRecorder(db_session).record((event,))
    store = SqlAlchemyTechnicalReportIdempotencyStore(db_session)
    store.reserve(key, "c" * 64)
    store.record_result(key, result)
    db_session.flush()

    outbox_payload = db_session.query(TechnicalReportOutboxRecord).filter_by(
        aggregate_id=report.id
    ).one().payload
    assert set(outbox_payload) == {
        "report_id", "aggregate_version", "command_id", "correlation_id",
        "occurred_at", "organization_id", "workspace_id", "project_id",
        "purpose", "lifecycle", "draft_revision_id", "actor_id",
        "causation_id", "predecessor_report_id", "source_entry_count",
    }
    records = [
        db_session.query(AuditLog).filter_by(entity_uuid=report.id).one().details,
        outbox_payload,
        db_session.query(TechnicalReportIdempotencyRecord).filter_by(
            aggregate_id=report.id
        ).one().result,
    ]
    serialized = json.dumps(records, default=str)
    assert "Protected technical content" not in serialized
    assert "Authorized equipment scope" not in serialized
    assert "Draft conclusion" not in serialized


def test_idempotency_requires_valid_fingerprint_and_reservation(db_session):
    store = SqlAlchemyTechnicalReportIdempotencyStore(db_session)
    key = TechnicalReportIdempotencyKey(
        organization_id=uuid4(), actor_id=1,
        command_type="CreateTechnicalReportDraft", idempotency_id=uuid4()
    )
    with pytest.raises(ValueError, match="fingerprint"):
        store.reserve(key, "not-a-digest")

    event = TechnicalReportDomainEvent(
        uuid4(), uuid4(), 1, "TechnicalReportDraftCreated",
        uuid4(), uuid4(), datetime.now(timezone.utc), uuid4(), 1, None,
        "engineering_analysis", "draft", uuid4(), 1, uuid4(), None, 0,
    )
    result = TechnicalReportCommandResult(
        event.report_id, None, 1, TechnicalReportDraftRevision(uuid4(), 1),
        key.command_type, event.correlation_id, (event,)
    )
    with pytest.raises(ValueError, match="reservation"):
        store.record_result(key, result)


def test_idempotency_exact_replay_and_fingerprint_conflicts(
    db_session, relationship_domain
):
    report, actor, now = _report(db_session, relationship_domain)
    _event, result, _audit, key = _operation(report, actor, now)
    store = SqlAlchemyTechnicalReportIdempotencyStore(db_session)
    store.reserve(key, "f" * 64)
    with pytest.raises(TechnicalReportIdempotencyConflict):
        store.find(key, "f" * 64)
    store.record_result(key, result); db_session.flush()
    assert store.find(key, "f" * 64) == result
    with pytest.raises(TechnicalReportIdempotencyConflict):
        store.find(key, "0" * 64)
    with pytest.raises(TechnicalReportIdempotencyConflict):
        store.reserve(key, "f" * 64)


def test_idempotency_concurrent_reservation_maps_unique_race_to_stable_conflict(
    db_session,
):
    engine = db_session.get_bind().engine
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    organization_id = uuid4()
    unique = uuid4().hex
    with engine.begin() as connection:
        connection.execute(
            text("INSERT INTO organizations (id, is_active) VALUES (:id, true)"),
            {"id": organization_id},
        )
        actor_id = connection.execute(
            text(
                "INSERT INTO users (email, username, hashed_password, role, is_active) "
                "VALUES (:email, :username, 'test-only', 'engineer', true) "
                "RETURNING id"
            ),
            {"email": f"b4-{unique}@example.test", "username": f"b4-{unique}"},
        ).scalar_one()
    key = TechnicalReportIdempotencyKey(
        organization_id=organization_id, actor_id=actor_id,
        command_type="AcceptExactTechnicalReportDraft",
        idempotency_id=uuid4(),
    )
    reserved = Event()
    release = Event()

    def first_reservation():
        session = factory()
        try:
            SqlAlchemyTechnicalReportIdempotencyStore(session).reserve(
                key, "3" * 64,
            )
            reserved.set()
            assert release.wait(timeout=10)
            session.commit()
        finally:
            session.close()

    def competing_reservation():
        assert reserved.wait(timeout=10)
        session = factory()
        try:
            with pytest.raises(TechnicalReportIdempotencyConflict):
                SqlAlchemyTechnicalReportIdempotencyStore(session).reserve(
                    key, "3" * 64,
                )
        finally:
            session.rollback()
            session.close()

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(first_reservation)
            second = pool.submit(competing_reservation)
            assert reserved.wait(timeout=10)
            release.set()
            first.result(timeout=15)
            second.result(timeout=15)
    finally:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "DELETE FROM technical_report_idempotency "
                    "WHERE organization_id=:organization_id AND actor_id=:actor_id"
                ),
                {"organization_id": organization_id, "actor_id": actor_id},
            )
            connection.execute(text("DELETE FROM users WHERE id=:id"), {"id": actor_id})
            connection.execute(
                text("DELETE FROM organizations WHERE id=:id"),
                {"id": organization_id},
            )


def test_concrete_uow_conforms_and_final_recheck_detects_revocation(
    db_session, relationship_domain
):
    report, actor, _now = _report(db_session, relationship_domain)
    scope = TechnicalReportScope(
        report.organization_id, report.workspace_id, report.project_id
    )
    request = TechnicalReportFinalRecheckRequest(
        actor=TechnicalReportActor(actor.id, report.organization_id),
        scope=scope, report_id=report.id, owner_id=actor.id,
        expected_version=report.version,
        expected_draft_revision_id=report.draft_revision_id, sources=(),
    )
    with SqlAlchemyTechnicalReportUnitOfWork(_factory(db_session)) as uow:
        for name in (
            "technical_reports", "authorization", "references", "historical",
            "audit", "domain_events", "idempotency", "final_recheck",
        ):
            assert hasattr(uow, name)
        uow.final_recheck.require_current(request)

    membership = db_session.get(
        UserOrganizationMembership, (actor.id, report.organization_id)
    )
    membership.is_selected = False
    membership.is_enabled = False
    db_session.flush()
    with pytest.raises(TechnicalReportAuthorizationDenied):
        with SqlAlchemyTechnicalReportUnitOfWork(_factory(db_session)) as uow:
            uow.final_recheck.require_current(request)


def test_final_recheck_detects_owner_version_and_revision_races(
    db_session, relationship_domain
):
    report, actor, _now = _report(db_session, relationship_domain)
    base = dict(
        actor=TechnicalReportActor(actor.id, report.organization_id),
        scope=TechnicalReportScope(report.organization_id, report.workspace_id, report.project_id),
        report_id=report.id, sources=(),
    )
    for request in (
        TechnicalReportFinalRecheckRequest(**base, owner_id=actor.id + 1, expected_version=1, expected_draft_revision_id=report.draft_revision_id),
        TechnicalReportFinalRecheckRequest(**base, owner_id=actor.id, expected_version=2, expected_draft_revision_id=report.draft_revision_id),
        TechnicalReportFinalRecheckRequest(**base, owner_id=actor.id, expected_version=1, expected_draft_revision_id=uuid4()),
    ):
        with pytest.raises(TechnicalReportVersionConflict):
            with SqlAlchemyTechnicalReportUnitOfWork(_factory(db_session)) as uow:
                uow.final_recheck.require_current(request)


def test_final_recheck_detects_canonical_source_version_race(
    db_session, relationship_domain
):
    report, actor, now = _report(db_session, relationship_domain)
    project = relationship_domain["project"]
    source = EngineeringObject(
        id=uuid4(), organization_id=report.organization_id,
        customer_id=project.customer_id, project_id=report.project_id,
        workspace_id=report.workspace_id, family="electrical",
        discipline="electrical", object_type="motor", subtype=None,
        lifecycle="active", authority_standing="approved", version=1,
        creator_id=actor.id, steward_id=actor.id, created_at=now, updated_at=now,
    )
    db_session.add(source); db_session.flush()
    scope = TechnicalReportScope(report.organization_id, report.workspace_id, report.project_id)
    historical = TechnicalReportHistoricalRequest(
        actor=TechnicalReportActor(actor.id, report.organization_id), scope=scope,
        authority=AcceptExactDraftHistoricalAuthority(report.id, actor.id),
        source_type="engineering_object", source_id=source.id, source_version=1,
    )
    request = TechnicalReportFinalRecheckRequest(
        actor=historical.actor, scope=scope, report_id=report.id, owner_id=actor.id,
        expected_version=1, expected_draft_revision_id=report.draft_revision_id,
        sources=(historical,),
    )
    with SqlAlchemyTechnicalReportUnitOfWork(_factory(db_session)) as uow:
        uow.final_recheck.require_current(request)
    source.version = 2
    source.updated_at = now + timedelta(seconds=1)
    db_session.flush()
    with pytest.raises(ValueError, match="historical basis"):
        with SqlAlchemyTechnicalReportUnitOfWork(_factory(db_session)) as uow:
            uow.final_recheck.require_current(request)


def test_final_recheck_rejects_workspace_authority_revocation(
    db_session, relationship_domain
):
    report, actor, _now = _report(db_session, relationship_domain)
    workspace = relationship_domain["consumer_workspace"]
    request = TechnicalReportFinalRecheckRequest(
        actor=TechnicalReportActor(actor.id, report.organization_id),
        scope=TechnicalReportScope(
            report.organization_id, report.workspace_id, report.project_id,
        ),
        report_id=report.id, owner_id=actor.id, expected_version=1,
        expected_draft_revision_id=report.draft_revision_id, sources=(),
    )
    workspace.status = "archived"
    workspace.archived_at = datetime.now(timezone.utc)
    db_session.flush()
    with pytest.raises(TechnicalReportAuthorizationDenied):
        with SqlAlchemyTechnicalReportUnitOfWork(_factory(db_session)) as uow:
            uow.final_recheck.require_current(request)


def test_final_recheck_rejects_relationship_dependency_state_change(
    db_session, relationship_domain
):
    report, actor, now = _report(db_session, relationship_domain)
    project = relationship_domain["project"]
    workspace = relationship_domain["consumer_workspace"]
    source = EngineeringObject(
        id=uuid4(), organization_id=report.organization_id,
        customer_id=project.customer_id, project_id=project.id,
        workspace_id=workspace.id, family="electrical", discipline="electrical",
        object_type="motor", subtype=None, lifecycle="active",
        authority_standing="approved", version=1, creator_id=actor.id,
        steward_id=actor.id, created_at=now, updated_at=now,
    )
    target = EngineeringObject(
        id=uuid4(), organization_id=report.organization_id,
        customer_id=project.customer_id, project_id=project.id,
        workspace_id=workspace.id, family="electrical", discipline="electrical",
        object_type="motor", subtype=None, lifecycle="active",
        authority_standing="approved", version=1, creator_id=actor.id,
        steward_id=actor.id, created_at=now, updated_at=now,
    )
    evidence = Evidence(
        id=uuid4(), organization_id=report.organization_id,
        project_id=project.id, workspace_id=workspace.id, lifecycle="current",
        source_kind="engineering_record", source_reference="EV-B4",
        source_revision="A", source_standing="current", effective_at=now,
        supported_fact="Approved relationship basis", creator_id=actor.id,
        version=1,
    )
    db_session.add_all([source, target, evidence]); db_session.flush()
    relationship = EngineeringRelationship(
        id=uuid4(), organization_id=report.organization_id,
        project_id=project.id, workspace_id=workspace.id,
        source_object_id=source.id, target_object_id=target.id,
        relationship_family="dependency", relationship_type="depends_on",
        lifecycle="current", authority_standing="approved",
        evidence_references=[str(evidence.id)], version=1,
        creator_id=actor.id, steward_id=actor.id,
    )
    db_session.add(relationship); db_session.flush()
    scope = TechnicalReportScope(report.organization_id, workspace.id, project.id)
    historical = TechnicalReportHistoricalRequest(
        actor=TechnicalReportActor(actor.id, report.organization_id), scope=scope,
        authority=AcceptExactDraftHistoricalAuthority(report.id, actor.id),
        source_type="engineering_relationship", source_id=relationship.id,
        source_version=1,
    )
    request = TechnicalReportFinalRecheckRequest(
        actor=historical.actor, scope=scope, report_id=report.id,
        owner_id=actor.id, expected_version=1,
        expected_draft_revision_id=report.draft_revision_id,
        sources=(historical,),
    )
    with SqlAlchemyTechnicalReportUnitOfWork(_factory(db_session)) as uow:
        uow.final_recheck.require_current(request)
    evidence.lifecycle = "withdrawn"; db_session.flush()
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete):
        with SqlAlchemyTechnicalReportUnitOfWork(_factory(db_session)) as uow:
            uow.final_recheck.require_current(request)


def test_rejection_audit_uses_isolated_commit_and_closes():
    authoritative = MagicMock()
    session = MagicMock()
    record = TechnicalReportRejectionAuditRecord(
        actor_id=7,
        organization_id=uuid4(),
        report_id=uuid4(), operation="AcceptExactTechnicalReportDraft",
        reason=TechnicalReportRejectionReason.NON_OWNER_ACCEPTANCE,
        command_id=uuid4(),
        correlation_id=uuid4(),
        occurred_at=datetime.now(timezone.utc),
    )
    uow = SqlAlchemyTechnicalReportUnitOfWork(
        lambda: authoritative, lambda: session,
    )
    with pytest.raises(TechnicalReportAuthorizationDenied):
        with uow:
            raise TechnicalReportAuthorizationDenied()
    uow.rejection_audit.record_rejection(record)

    authoritative.rollback.assert_called_once_with()
    session.add.assert_called_once()
    staged = session.add.call_args.args[0]
    assert staged.details["outcome"] == "rejected"
    assert staged.details["reason"] == "non_owner_acceptance"
    session.commit.assert_called_once_with()
    session.rollback.assert_not_called()
    session.close.assert_called_once_with()


def test_rejection_audit_failure_is_isolated_and_suppressed():
    authoritative = MagicMock()
    session = MagicMock()
    session.commit.side_effect = RuntimeError("audit unavailable")
    record = TechnicalReportRejectionAuditRecord(
        actor_id=7,
        organization_id=uuid4(),
        report_id=None, operation="AcceptExactTechnicalReportDraft",
        reason=TechnicalReportRejectionReason.CROSS_ORGANIZATION,
        command_id=uuid4(),
        correlation_id=uuid4(),
        occurred_at=datetime.now(timezone.utc),
    )

    uow = SqlAlchemyTechnicalReportUnitOfWork(
        lambda: authoritative, lambda: session,
    )
    original = TechnicalReportAuthorizationDenied()
    with pytest.raises(TechnicalReportAuthorizationDenied) as raised:
        try:
            with uow:
                raise original
        except TechnicalReportAuthorizationDenied:
            uow.rejection_audit.record_rejection(record)
            raise

    assert raised.value is original
    session.rollback.assert_called_once_with()
    session.close.assert_called_once_with()


def test_rejection_audit_is_forbidden_before_rollback_and_is_single_use():
    authoritative = MagicMock()
    rejection = MagicMock()
    uow = SqlAlchemyTechnicalReportUnitOfWork(
        lambda: authoritative, lambda: rejection,
    )
    record = TechnicalReportRejectionAuditRecord(
        actor_id=7, organization_id=uuid4(), report_id=None,
        operation="AcceptExactTechnicalReportDraft",
        reason=TechnicalReportRejectionReason.ACCEPTED_STATE_MUTATION,
        command_id=None, correlation_id=uuid4(),
        occurred_at=datetime.now(timezone.utc),
    )
    with pytest.raises(ValueError, match="requires authoritative rollback"):
        uow.rejection_audit.record_rejection(record)
    with uow:
        uow.rollback()
    uow.rejection_audit.record_rejection(record)
    with pytest.raises(ValueError, match="requires authoritative rollback"):
        uow.rejection_audit.record_rejection(record)
    assert rejection.add.call_count == 1


def test_ordinary_failure_rollback_does_not_create_rejection_audit():
    authoritative = MagicMock()
    rejection = MagicMock()
    uow = SqlAlchemyTechnicalReportUnitOfWork(
        lambda: authoritative, lambda: rejection,
    )
    with pytest.raises(TechnicalReportVersionConflict):
        with uow:
            raise TechnicalReportVersionConflict()
    rejection.add.assert_not_called()
    rejection.commit.assert_not_called()


@pytest.mark.parametrize(
    "field,value",
    [
        ("reason", "ordinary_validation"),
        ("operation", "GenericUpdateTechnicalReport"),
    ],
)
def test_rejection_audit_contract_rejects_open_categories(field, value):
    values = {
        "actor_id": 7,
        "organization_id": uuid4(),
        "report_id": None,
        "operation": "AcceptExactTechnicalReportDraft",
        "reason": TechnicalReportRejectionReason.NON_OWNER_ACCEPTANCE,
        "command_id": None,
        "correlation_id": uuid4(),
        "occurred_at": datetime.now(timezone.utc),
    }
    values[field] = value
    with pytest.raises(ValueError, match="rejection Audit"):
        TechnicalReportRejectionAuditRecord(**values)


def test_batch_4_uow_does_not_implement_batch_5_surfaces():
    names = set(SqlAlchemyTechnicalReportUnitOfWork.__dict__)
    assert not names.intersection(
        {"create_draft", "revise_draft", "accept_exact_draft", "create_successor",
         "request_ai_proposal", "route", "dispatch"}
    )
