from datetime import datetime, timezone
from uuid import uuid4
import json

import pytest

from app.models.audit_log import AuditLog
from app.models.engineering_experience_capture import EngineeringExperienceCapture
from app.models.engineering_experience_capture_command import (
    EngineeringExperienceCaptureActor,
    EngineeringExperienceCaptureEvent,
    EngineeringExperienceCaptureIdempotency,
    EngineeringExperienceCaptureOutbox,
    EngineeringExperienceCaptureResult,
)
from app.repositories.engineering_experience_capture_unit_of_work import (
    SqlAlchemyCaptureAuditRecorder,
    SqlAlchemyCaptureDomainEventRecorder,
    SqlAlchemyCaptureIdempotencyStore,
)


def test_capture_audit_event_and_idempotency_stage_in_one_transaction(db_session, relationship_domain):
    actor_record = relationship_domain["actors"]["project_owner"]
    project = relationship_domain["project"]
    capture = EngineeringExperienceCapture(
        id=uuid4(), organization_id=project.organization_id, project_id=project.id,
        source_kind="observation", original_content="atomic experience",
        creator_id=actor_record.id, lifecycle="captured", version=1,
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )
    db_session.add(capture)
    db_session.flush()
    actor = EngineeringExperienceCaptureActor(actor_record.id, project.organization_id)
    event = EngineeringExperienceCaptureEvent(
        uuid4(), "EngineeringExperienceCaptured", capture.id, 1,
        datetime.now(timezone.utc), actor.actor_id, uuid4(), uuid4(),
        project.organization_id, project.id, None, None, "observation", {"lifecycle": "captured"},
    )
    SqlAlchemyCaptureAuditRecorder(db_session).record(
        actor=actor, capture_id=capture.id, command_type="CreateEngineeringExperienceCapture",
        lifecycle="captured", version=1, project_id=project.id,
    )
    SqlAlchemyCaptureDomainEventRecorder(db_session).record((event,))
    store = SqlAlchemyCaptureIdempotencyStore(db_session)
    store.reserve(id=uuid4(), organization_id=project.organization_id, actor_id=actor.actor_id,
                  command_type="CreateEngineeringExperienceCapture", idempotency_id=uuid4(),
                  request_fingerprint="a" * 64)
    result = EngineeringExperienceCaptureResult(capture.id, None, 1,
                                                 "CreateEngineeringExperienceCapture", event.correlation_id, (event,))
    store.record_result(result, {"capture_id": str(capture.id), "version": 1})
    db_session.flush()
    assert db_session.query(AuditLog).filter_by(entity_uuid=capture.id).count() == 1
    assert db_session.query(EngineeringExperienceCaptureOutbox).filter_by(aggregate_id=capture.id).count() == 1
    assert db_session.query(EngineeringExperienceCaptureIdempotency).filter_by(aggregate_id=capture.id).count() == 1


def test_staged_capture_effects_roll_back_together(db_session, relationship_domain):
    before = db_session.query(EngineeringExperienceCapture).count()
    nested = db_session.begin_nested()
    project = relationship_domain["project"]
    actor = relationship_domain["actors"]["project_owner"]
    db_session.add(EngineeringExperienceCapture(
        id=uuid4(), organization_id=project.organization_id, project_id=project.id,
        source_kind="question", original_content="must roll back", creator_id=actor.id,
        lifecycle="captured", version=1, created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    ))
    db_session.flush()
    nested.rollback()
    assert db_session.query(EngineeringExperienceCapture).count() == before


def test_events_exclude_capture_plaintext(db_session):
    recorder_source = SqlAlchemyCaptureDomainEventRecorder.record.__code__.co_names
    assert "original_content" not in recorder_source
    assert "source_reference" not in recorder_source


def test_persisted_operational_records_exclude_all_capture_plaintext(
    db_session, relationship_domain
):
    content = "CONTENT-PLAINTEXT-MARKER"
    reference = "REFERENCE-PLAINTEXT-MARKER"
    rationale = "RATIONALE-PLAINTEXT-MARKER"
    actor_record = relationship_domain["actors"]["project_owner"]
    project = relationship_domain["project"]
    capture = EngineeringExperienceCapture(
        id=uuid4(), organization_id=project.organization_id, project_id=project.id,
        source_kind="observation", original_content=content, source_reference=reference,
        creator_id=actor_record.id, lifecycle="captured", version=1,
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )
    db_session.add(capture)
    db_session.flush()
    actor = EngineeringExperienceCaptureActor(actor_record.id, project.organization_id)
    event = EngineeringExperienceCaptureEvent(
        uuid4(), "EngineeringExperienceCaptured", capture.id, 1,
        datetime.now(timezone.utc), actor.actor_id, uuid4(), uuid4(),
        project.organization_id, project.id, None, None, "observation", {"lifecycle": "captured"},
    )
    SqlAlchemyCaptureAuditRecorder(db_session).record(
        actor=actor, capture_id=capture.id, command_type="CreateEngineeringExperienceCapture",
        lifecycle="captured", version=1, project_id=project.id,
        correlation_id=event.correlation_id, rationale=rationale,
    )
    SqlAlchemyCaptureDomainEventRecorder(db_session).record((event,))
    store = SqlAlchemyCaptureIdempotencyStore(db_session)
    store.reserve(
        organization_id=project.organization_id, actor_id=actor.actor_id,
        command_type="CreateEngineeringExperienceCapture", idempotency_id=uuid4(),
        request_fingerprint="b" * 64,
    )
    result = EngineeringExperienceCaptureResult(
        capture.id, None, 1, "CreateEngineeringExperienceCapture", event.correlation_id, (event,)
    )
    store.record_result(result, {
        "capture_id": str(capture.id), "content": content,
        "source_reference": reference, "rationale": rationale,
    })
    db_session.flush()
    records = [
        db_session.query(AuditLog).filter_by(entity_uuid=capture.id).one().details,
        db_session.query(EngineeringExperienceCaptureOutbox).filter_by(aggregate_id=capture.id).one().payload,
        db_session.query(EngineeringExperienceCaptureIdempotency).filter_by(aggregate_id=capture.id).one().result,
    ]
    serialized = json.dumps(records, default=str)
    assert content not in serialized
    assert reference not in serialized
    assert rationale not in serialized
