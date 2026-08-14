"""PATCH-034 Batch 2 repository and direct-SQL persistence evidence."""

from datetime import datetime, timedelta, timezone
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
import json
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from app.enums.technical_report import TechnicalReportIntegrityAlgorithm
from app.models.organizational_memory import OrganizationalMemory
from app.models.organizational_memory_command import (
    ActiveMemoryCriteria,
    MemoryOrderingAnchor,
    admission_material_from_snapshot,
)
from app.models.technical_report import TechnicalReport
from app.models.technical_report_command import (
    AcceptExactTechnicalReportDraft,
    AcceptanceConfirmation,
    CaptureHistoricalBasisV1,
    CreateTechnicalReportDraft,
    PreliminaryQualification,
    TechnicalReportActor,
    TechnicalReportCommandMetadata,
    TechnicalReportContent,
    TechnicalReportProvenanceEntry,
    historical_basis_digest,
)
from app.repositories.organizational_memory_repository import (
    SqlAlchemyOrganizationalMemoryRepository,
)
from app.repositories.technical_report_repository import SqlAlchemyTechnicalReportRepository
from conftest import owner_engine


NOW = datetime(2026, 8, 13, 9, 0, tzinfo=timezone.utc)


def _accepted_report(db_session, domain, *, accepted_at=NOW) -> TechnicalReport:
    actor = domain["actors"]["project_owner"]
    workspace = domain["consumer_workspace"]
    organization_id = domain["project"].organization_id
    metadata = TechnicalReportCommandMetadata(
        TechnicalReportActor(actor.id, organization_id),
        "Engineering rationale", uuid4(), uuid4(), uuid4(),
    )
    basis = CaptureHistoricalBasisV1(
        1, "universal_capture", uuid4(), 1, organization_id,
        domain["project"].id, workspace.id, "electrical", uuid4(),
        "observation", "Observed stable process response", "field-note-1",
        actor.id, "captured", accepted_at,
    )
    provenance = TechnicalReportProvenanceEntry(
        uuid4(), 0, "canonical_material", "universal_capture", True,
        "universal_capture", "primary observation", "verified", "available",
        "Authenticated engineer", (), basis, TechnicalReportIntegrityAlgorithm.SHA256,
        historical_basis_digest(basis),
    )
    report = TechnicalReport.create(CreateTechnicalReportDraft(
        metadata, organization_id, workspace.id, domain["project"].id, actor.id,
        "engineering_analysis",
        TechnicalReportContent(
            "Control system", "Stable engineering analysis", (),
            "Known measurement tolerance", (), "Response is repeatable", (),
        ),
        PreliminaryQualification(False),
        (provenance,),
    ), accepted_at)[0]
    report_repository = SqlAlchemyTechnicalReportRepository(db_session)
    report_repository.add(report)
    report.accept_exact_draft(AcceptExactTechnicalReportDraft(
        TechnicalReportCommandMetadata(
            TechnicalReportActor(actor.id, organization_id),
            "Accept exact report", uuid4(), uuid4(), uuid4(),
        ),
        report.id,
        AcceptanceConfirmation(report.version, report.draft_revision_id, True),
    ), accepted_at)
    assert report_repository.persist_acceptance_expected_version(report, 1)
    return report


def _memory(db_session, domain, *, admitted_at=NOW) -> OrganizationalMemory:
    report = _accepted_report(db_session, domain, accepted_at=admitted_at)
    projection, manifest = admission_material_from_snapshot(report.accepted_snapshot)
    return OrganizationalMemory.admit(
        memory_id=uuid4(), projection=projection, manifest=manifest,
        admitted_by_id=report.owner_id, admitted_at=admitted_at,
        admission_rationale="Human memory admission",
        audience_actor_ids=(report.owner_id,),
        reuse_restrictions=("Confirm current applicability",),
    )


def test_repository_round_trip_history_and_no_commit(db_session, relationship_domain):
    memory = _memory(db_session, relationship_domain)
    repository = SqlAlchemyOrganizationalMemoryRepository(db_session)
    repository.add(memory)
    repository.append_history(memory.initial_history(event_id=uuid4()))
    assert db_session.in_transaction()
    loaded = repository.get_scoped(memory.id, memory.organization_id)
    assert loaded == memory
    assert repository.get_by_source(memory.source, memory.organization_id) == memory
    assert repository.get_scoped(memory.id, uuid4()) is None


def test_expected_version_transition_is_one_winner_and_history_is_append_only(db_session, relationship_domain):
    memory = _memory(db_session, relationship_domain)
    repository = SqlAlchemyOrganizationalMemoryRepository(db_session)
    repository.add(memory)
    repository.append_history(memory.initial_history(event_id=uuid4()))
    withdrawn, history = memory.withdraw(
        expected_version=1, actor_id=memory.admitted_by_id,
        occurred_at=NOW + timedelta(seconds=1), reason="Superseded engineering basis",
    )
    assert repository.persist_standing_expected_version(withdrawn, 99) is False
    assert repository.persist_standing_expected_version(withdrawn, 1) is True
    repository.append_history(history)
    assert repository.persist_standing_expected_version(withdrawn, 1) is False
    with pytest.raises(DBAPIError):
        db_session.execute(text(
            "UPDATE organizational_memory_standing_history SET reason='rewrite' "
            "WHERE memory_id=:memory_id"
        ), {"memory_id": memory.id})


def test_candidate_reads_are_bounded_deterministic_and_anchor_safe(db_session, relationship_domain):
    first = _memory(db_session, relationship_domain, admitted_at=NOW)
    second = _memory(db_session, relationship_domain, admitted_at=NOW + timedelta(seconds=1))
    repository = SqlAlchemyOrganizationalMemoryRepository(db_session)
    repository.add(first); repository.add(second)
    criteria = ActiveMemoryCriteria(
        first.organization_id, first.workspace_id, first.project_id, None, None, 1,
    )
    page = repository.list_active(criteria)
    assert page.items == (second,) and page.has_more is True
    next_page = repository.list_active(ActiveMemoryCriteria(
        first.organization_id, first.workspace_id, first.project_id, None,
        MemoryOrderingAnchor(second.admitted_at, second.id), 1,
    ))
    assert next_page.items == (first,) and next_page.has_more is False


def test_database_uniqueness_and_root_immutability_apply_to_direct_sql(db_session, relationship_domain):
    memory = _memory(db_session, relationship_domain)
    repository = SqlAlchemyOrganizationalMemoryRepository(db_session)
    repository.add(memory)
    duplicate = OrganizationalMemory.admit(
        memory_id=uuid4(), projection=memory.projection, manifest=memory.manifest,
        admitted_by_id=memory.admitted_by_id, admitted_at=NOW + timedelta(seconds=1),
        admission_rationale="Duplicate", audience_actor_ids=memory.audience_actor_ids,
        reuse_restrictions=memory.reuse_restrictions,
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            repository.add(duplicate)
    with pytest.raises(DBAPIError):
        db_session.execute(text(
            "UPDATE organizational_memories SET admission_rationale='rewritten' WHERE id=:id"
        ), {"id": memory.id})


def test_direct_sql_cannot_delete_root_or_insert_forged_terminal_history(db_session, relationship_domain):
    memory = _memory(db_session, relationship_domain)
    repository = SqlAlchemyOrganizationalMemoryRepository(db_session)
    repository.add(memory)
    with pytest.raises(DBAPIError):
        with db_session.begin_nested():
            db_session.execute(text("DELETE FROM organizational_memories WHERE id=:id"), {"id": memory.id})
    with pytest.raises(DBAPIError):
        db_session.execute(text("""
            INSERT INTO organizational_memory_standing_history
              (event_id,memory_id,organization_id,aggregate_version,from_standing,
               to_standing,actor_id,occurred_at,reason,replacement_memory_id)
            VALUES (:event_id,:memory_id,:organization_id,1,'active','superseded',
                    :actor_id,:occurred_at,'forged',NULL)
        """), {
            "event_id": uuid4(), "memory_id": memory.id,
            "organization_id": memory.organization_id,
            "actor_id": memory.admitted_by_id, "occurred_at": NOW,
        })


def test_direct_sql_lineage_rejects_audience_broadening_and_wrong_replacement(db_session, relationship_domain):
    predecessor = _memory(db_session, relationship_domain)
    candidate = _memory(db_session, relationship_domain, admitted_at=NOW + timedelta(seconds=1))
    repository = SqlAlchemyOrganizationalMemoryRepository(db_session)
    repository.add(predecessor)
    invalid_successor = replace(
        candidate,
        predecessor_memory_id=predecessor.id,
        audience_actor_ids=(predecessor.admitted_by_id, relationship_domain["actors"]["unrelated"].id),
    )
    with pytest.raises(DBAPIError):
        with db_session.begin_nested():
            repository.add(invalid_successor)
    repository.add(candidate)
    with pytest.raises(DBAPIError):
        db_session.execute(text("""
            UPDATE organizational_memories SET standing='superseded', version=2,
              superseded_by_id=:actor_id, superseded_at=:occurred_at,
              supersession_reason='wrong replacement', replacement_memory_id=:replacement,
              updated_at=:occurred_at
            WHERE id=:predecessor
        """), {
            "actor_id": predecessor.admitted_by_id,
            "occurred_at": NOW + timedelta(seconds=2),
            "replacement": candidate.id,
            "predecessor": predecessor.id,
        })


def test_direct_sql_side_records_are_closed_and_immutable(db_session, relationship_domain):
    memory = _memory(db_session, relationship_domain)
    repository = SqlAlchemyOrganizationalMemoryRepository(db_session)
    repository.add(memory)
    event_id = uuid4(); now = NOW + timedelta(seconds=1)
    payload = memory.event(
        event_id=event_id, event_type="ORGANIZATIONAL_MEMORY_ADMITTED",
        actor_id=memory.admitted_by_id, occurred_at=memory.admitted_at,
        command_id=uuid4(), correlation_id=uuid4(), causation_id=uuid4(),
    ).payload
    from app.models.organizational_memory_command import canonical_json
    db_session.execute(text("""
        INSERT INTO organizational_memory_events_outbox
          (event_id,memory_id,aggregate_version,event_type,payload_schema_version,
           payload,occurred_at,created_at,attempt_count)
        VALUES (:event_id,:memory_id,1,'ORGANIZATIONAL_MEMORY_ADMITTED',1,
                CAST(:payload AS jsonb),:occurred_at,:created_at,0)
    """), {
        "event_id": event_id, "memory_id": memory.id,
        "payload": canonical_json(payload).decode(),
        "occurred_at": memory.admitted_at, "created_at": now,
    })
    with pytest.raises(DBAPIError):
        with db_session.begin_nested():
            db_session.execute(text(
                "UPDATE organizational_memory_events_outbox "
                "SET payload=jsonb_set(payload,'{standing}','\"withdrawn\"') "
                "WHERE event_id=:event_id"
            ), {"event_id": event_id})
    with pytest.raises(DBAPIError):
        with db_session.begin_nested():
            db_session.execute(text("""
                INSERT INTO organizational_memory_events_outbox
                  (event_id,memory_id,aggregate_version,event_type,payload_schema_version,
                   payload,occurred_at,created_at,attempt_count)
                VALUES (:event_id,:memory_id,1,'ORGANIZATIONAL_MEMORY_ADMITTED',1,
                        CAST(:payload AS jsonb),:wrong_time,:created_at,0)
            """), {
                "event_id": uuid4(), "memory_id": memory.id,
                "payload": canonical_json(payload).decode(),
                "wrong_time": memory.admitted_at + timedelta(seconds=1),
                "created_at": now,
            })

    idempotency_id = uuid4()
    result = json.dumps({
        "result_type": "admit.v1", "memory_id": str(memory.id), "version": 1,
        "standing": "active", "source_report_id": str(memory.source.report_id),
        "source_accepted_version": memory.source.accepted_aggregate_version,
    }, sort_keys=True, separators=(",", ":"))
    db_session.execute(text("""
        INSERT INTO organizational_memory_idempotency
          (organization_id,actor_id,operation,idempotency_id,request_fingerprint,
           status,result_schema_version,safe_result,created_at,updated_at,completed_at)
        VALUES (:organization_id,:actor_id,'admit',:idempotency_id,:fingerprint,
                'completed',1,CAST(:result AS jsonb),:now,:now,:now)
    """), {
        "organization_id": memory.organization_id,
        "actor_id": memory.admitted_by_id,
        "idempotency_id": idempotency_id, "fingerprint": "a" * 64,
        "result": result, "now": now,
    })
    with pytest.raises(DBAPIError):
        with db_session.begin_nested():
            db_session.execute(text("""
                INSERT INTO organizational_memory_idempotency
                  (organization_id,actor_id,operation,idempotency_id,request_fingerprint,
                   status,result_schema_version,safe_result,created_at,updated_at,completed_at)
                VALUES (:organization_id,:actor_id,'withdraw',:idempotency_id,:fingerprint,
                        'completed',1,CAST(:result AS jsonb),:now,:now,:now)
            """), {
                "organization_id": memory.organization_id,
                "actor_id": memory.admitted_by_id,
                "idempotency_id": uuid4(), "fingerprint": "c" * 64,
                "result": result, "now": now,
            })
    with pytest.raises(DBAPIError):
        db_session.execute(text("""
            UPDATE organizational_memory_idempotency SET request_fingerprint=:fingerprint
            WHERE organization_id=:organization_id AND actor_id=:actor_id
              AND operation='admit' AND idempotency_id=:idempotency_id
        """), {
            "fingerprint": "b" * 64, "organization_id": memory.organization_id,
            "actor_id": memory.admitted_by_id, "idempotency_id": idempotency_id,
        })


def test_direct_sql_completed_idempotency_rejects_all_required_null_and_invalid_time_bypasses(
    db_session, relationship_domain,
):
    memory = _memory(db_session, relationship_domain)
    SqlAlchemyOrganizationalMemoryRepository(db_session).add(memory)
    other_id = uuid4()
    valid_time = "2026-08-13T09:00:00.000000Z"
    cases = (
        ("admit", {
            "result_type": "admit.v1", "memory_id": None, "version": 1,
            "standing": "active", "source_report_id": str(memory.source.report_id),
            "source_accepted_version": memory.source.accepted_aggregate_version,
        }),
        ("withdraw", {
            "result_type": "withdraw.v1", "memory_id": str(memory.id),
            "result_version": 2, "standing": "withdrawn", "withdrawn_at": None,
        }),
        ("create_successor", {
            "result_type": "create_successor.v1", "memory_id": str(other_id),
            "predecessor_memory_id": None, "version": 1, "standing": "active",
            "source_report_id": str(memory.source.report_id),
            "source_accepted_version": memory.source.accepted_aggregate_version + 1,
        }),
        ("supersede", {
            "result_type": "supersede.v1", "predecessor_memory_id": str(memory.id),
            "predecessor_result_version": 2, "predecessor_standing": "superseded",
            "replacement_memory_id": None, "replacement_version_at_command": 1,
            "replacement_standing": "active", "superseded_at": valid_time,
        }),
        ("withdraw", {
            "result_type": "withdraw.v1", "memory_id": str(memory.id),
            "result_version": 2, "standing": "withdrawn",
            "withdrawn_at": "2026-02-31T09:00:00.000000Z",
        }),
        ("supersede", {
            "result_type": "supersede.v1", "predecessor_memory_id": str(memory.id),
            "predecessor_result_version": 2, "predecessor_standing": "superseded",
            "replacement_memory_id": str(other_id), "replacement_version_at_command": 1,
            "replacement_standing": "active",
            "superseded_at": "2026-08-13T24:00:00.000000Z",
        }),
    )
    for operation, safe_result in cases:
        with pytest.raises(DBAPIError):
            with db_session.begin_nested():
                db_session.execute(text("""
                    INSERT INTO organizational_memory_idempotency
                      (organization_id,actor_id,operation,idempotency_id,
                       request_fingerprint,status,result_schema_version,safe_result,
                       created_at,updated_at,completed_at)
                    VALUES (:organization_id,:actor_id,:operation,:idempotency_id,
                            :fingerprint,'completed',1,CAST(:safe_result AS jsonb),
                            :now,:now,:now)
                """), {
                    "organization_id": memory.organization_id,
                    "actor_id": memory.admitted_by_id,
                    "operation": operation,
                    "idempotency_id": uuid4(),
                    "fingerprint": "d" * 64,
                    "safe_result": json.dumps(safe_result),
                    "now": NOW + timedelta(seconds=1),
                })


def test_direct_sql_projection_and_manifest_validators_are_strict_false(
    db_session, relationship_domain,
):
    memory = _memory(db_session, relationship_domain)
    from app.models.organizational_memory_command import canonical_json

    projection = json.loads(canonical_json(memory.projection))
    manifest = json.loads(canonical_json(memory.manifest))
    invalid_projection_values = (
        {**projection, "report_id": None},
        {**projection, "accepted_at": None},
        {**projection, "accepted_at": "2026-02-31T09:00:00.000000Z"},
        {**projection, "accepted_at": "2026-08-13T24:00:00.000000Z"},
    )
    for payload in invalid_projection_values:
        assert db_session.execute(text(
            "SELECT organizational_memory_projection_v1_valid("
            "CAST(:payload AS jsonb)) IS FALSE"
        ), {"payload": json.dumps(payload)}).scalar_one()

    invalid_source = {
        **manifest, "source": {**manifest["source"], "report_id": None},
    }
    assert db_session.execute(text(
        "SELECT organizational_memory_manifest_v1_valid("
        "CAST(:payload AS jsonb)) IS FALSE"
    ), {"payload": json.dumps(invalid_source)}).scalar_one()

    entry = manifest["provenance_entries"][0]
    invalid_nested_values = {
        "entry_id": "not-a-uuid",
        "ordinal": "0",
        "source_class": "unsupported",
        "source_type": "unsupported",
        "owning_capability": "unsupported",
        "is_material": "true",
        "reliance_role": 7,
        "locator_digest": "not-a-digest",
        "source_integrity_algorithm": "md5",
        "source_integrity_digest": "not-a-digest",
    }
    for field in entry:
        for invalid in (None, invalid_nested_values[field]):
            entries = [
                {**entry, field: invalid},
                *manifest["provenance_entries"][1:],
            ]
            provenance_digest = db_session.execute(text(
                "SELECT encode(sha256(convert_to("
                "organizational_memory_canonical_json(CAST(:entries AS jsonb)),"
                "'UTF8')),'hex')"
            ), {"entries": json.dumps(entries)}).scalar_one()
            payload = {
                **manifest,
                "provenance_entries": entries,
                "provenance_digest": provenance_digest,
            }
            assert payload["provenance_digest"] == provenance_digest
            assert db_session.execute(text(
                "SELECT organizational_memory_manifest_v1_valid("
                "CAST(:payload AS jsonb)) IS FALSE"
            ), {"payload": json.dumps(payload)}).scalar_one(), field

    missing_entry_field = dict(entry)
    missing_entry_field.pop("entry_id")
    entries = [missing_entry_field, *manifest["provenance_entries"][1:]]
    provenance_digest = db_session.execute(text(
        "SELECT encode(sha256(convert_to("
        "organizational_memory_canonical_json(CAST(:entries AS jsonb)),"
        "'UTF8')),'hex')"
    ), {"entries": json.dumps(entries)}).scalar_one()
    payload = {
        **manifest, "provenance_entries": entries,
        "provenance_digest": provenance_digest,
    }
    assert db_session.execute(text(
        "SELECT organizational_memory_manifest_v1_valid("
        "CAST(:payload AS jsonb)) IS FALSE"
    ), {"payload": json.dumps(payload)}).scalar_one()

    # The digest remains an independent guard and is not weakened by the
    # digest-coherent nested-field evidence above.
    stale_digest = {
        **manifest,
        "provenance_entries": [{**entry, "entry_id": None}],
    }
    assert db_session.execute(text(
        "SELECT organizational_memory_manifest_v1_valid("
        "CAST(:payload AS jsonb)) IS FALSE"
    ), {"payload": json.dumps(stale_digest)}).scalar_one()


@pytest.mark.parametrize("field,value", [
    ("actor_id", None),
    ("occurred_at", NOW + timedelta(seconds=1)),
    ("reason", "mismatched reason"),
])
def test_direct_sql_history_must_match_root_actor_time_and_reason(
    db_session, relationship_domain, field, value
):
    memory = _memory(db_session, relationship_domain)
    repository = SqlAlchemyOrganizationalMemoryRepository(db_session)
    repository.add(memory)
    values = {
        "event_id": uuid4(), "memory_id": memory.id,
        "organization_id": memory.organization_id, "actor_id": memory.admitted_by_id,
        "occurred_at": memory.admitted_at, "reason": memory.admission_rationale,
    }
    values[field] = memory.admitted_by_id + 1 if field == "actor_id" else value
    with pytest.raises(DBAPIError):
        db_session.execute(text("""
            INSERT INTO organizational_memory_standing_history
              (event_id,memory_id,organization_id,aggregate_version,from_standing,
               to_standing,actor_id,occurred_at,reason,replacement_memory_id)
            VALUES (:event_id,:memory_id,:organization_id,1,NULL,'active',
                    :actor_id,:occurred_at,:reason,NULL)
        """), values)


def test_direct_sql_terminal_reason_and_timestamp_are_canonical(db_session, relationship_domain):
    memory = _memory(db_session, relationship_domain)
    repository = SqlAlchemyOrganizationalMemoryRepository(db_session)
    repository.add(memory)
    with pytest.raises(DBAPIError):
        db_session.execute(text("""
            UPDATE organizational_memories SET standing='withdrawn',version=2,
              withdrawn_by_id=:actor_id,withdrawn_at=:occurred_at,
              withdrawal_reason=' padded ',updated_at=:occurred_at
            WHERE id=:memory_id
        """), {
            "actor_id": memory.admitted_by_id,
            "occurred_at": NOW + timedelta(seconds=1), "memory_id": memory.id,
        })


def test_replacement_reuse_and_wrong_link_are_rejected(db_session, relationship_domain):
    predecessor = _memory(db_session, relationship_domain)
    replacement_material = _memory(
        db_session, relationship_domain, admitted_at=NOW + timedelta(seconds=1),
    )
    other_predecessor = _memory(
        db_session, relationship_domain, admitted_at=NOW + timedelta(seconds=2),
    )
    replacement = replace(
        replacement_material, predecessor_memory_id=predecessor.id,
        audience_actor_ids=predecessor.audience_actor_ids,
    )
    repository = SqlAlchemyOrganizationalMemoryRepository(db_session)
    for memory in (predecessor, replacement, other_predecessor):
        repository.add(memory)
    occurred_at = NOW + timedelta(seconds=3)
    assert db_session.execute(text("""
        UPDATE organizational_memories SET standing='superseded',version=2,
          superseded_by_id=:actor_id,superseded_at=:occurred_at,
          supersession_reason='valid replacement',replacement_memory_id=:replacement,
          updated_at=:occurred_at WHERE id=:predecessor
    """), {
        "actor_id": predecessor.admitted_by_id, "occurred_at": occurred_at,
        "replacement": replacement.id, "predecessor": predecessor.id,
    }).rowcount == 1
    with pytest.raises(DBAPIError):
        db_session.execute(text("""
            UPDATE organizational_memories SET standing='superseded',version=2,
              superseded_by_id=:actor_id,superseded_at=:occurred_at,
              supersession_reason='reused replacement',replacement_memory_id=:replacement,
              updated_at=:occurred_at WHERE id=:predecessor
        """), {
            "actor_id": other_predecessor.admitted_by_id,
            "occurred_at": occurred_at + timedelta(seconds=1),
            "replacement": replacement.id, "predecessor": other_predecessor.id,
        })


def test_concurrent_duplicate_admission_has_exactly_one_winner(db_session, relationship_domain):
    candidate = _memory(db_session, relationship_domain)
    db_session.connection().commit()
    candidates = (candidate, replace(candidate, id=uuid4()))
    barrier = Barrier(2)

    def insert(memory):
        with Session(owner_engine) as session:
            barrier.wait()
            try:
                SqlAlchemyOrganizationalMemoryRepository(session).add(memory)
                session.commit()
                return "inserted"
            except IntegrityError:
                session.rollback()
                return "duplicate"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(insert, candidates))
    assert sorted(results) == ["duplicate", "inserted"]


def test_concurrent_supersession_has_one_winner_and_uses_ordered_locks(
    db_session, relationship_domain
):
    predecessor = _memory(db_session, relationship_domain)
    material = _memory(
        db_session, relationship_domain, admitted_at=NOW + timedelta(seconds=1),
    )
    replacement = replace(
        material, predecessor_memory_id=predecessor.id,
        audience_actor_ids=predecessor.audience_actor_ids,
    )
    repository = SqlAlchemyOrganizationalMemoryRepository(db_session)
    repository.add(predecessor); repository.add(replacement)
    db_session.connection().commit()
    barrier = Barrier(2)

    def supersede(offset: int):
        barrier.wait()
        try:
            with owner_engine.begin() as connection:
                result = connection.execute(text("""
                    UPDATE organizational_memories SET standing='superseded',version=2,
                      superseded_by_id=:actor_id,superseded_at=:occurred_at,
                      supersession_reason='concurrent replacement',
                      replacement_memory_id=:replacement,updated_at=:occurred_at
                    WHERE id=:predecessor AND version=1
                """), {
                    "actor_id": predecessor.admitted_by_id,
                    "occurred_at": NOW + timedelta(seconds=2 + offset),
                    "replacement": replacement.id, "predecessor": predecessor.id,
                })
                return result.rowcount
        except DBAPIError:
            return 0

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(supersede, (0, 1)))
    assert sorted(results) == [0, 1]
