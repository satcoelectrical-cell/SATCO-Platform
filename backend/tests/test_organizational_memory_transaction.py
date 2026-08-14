"""PATCH-034 Batch 4 concrete UoW and transaction-boundary evidence."""

from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.enums.organizational_memory import MemoryEventType, MemoryOperation, MemoryStanding
from app.models.audit_log import AuditLog
from app.models.organizational_memory import OrganizationalMemory
from app.models.organizational_memory_command import (
    AcceptedReportProjection, AcceptedReportProtectedNotFound,
    AcceptedReportSource, AdmitAcceptedReport, CreateMemorySuccessor,
    MemoryActor, MemoryAuditRecord, MemoryCommandMetadata,
    MemoryAuthorizationRequest, MemoryIdempotencyKey, MemoryOutboxRecord, MemoryScope,
    ProvenanceAuthorized, SafeAuthorizedProvenance, SupersedeMemory,
    StoredAdmissionResultV1,
    WithdrawMemory, admission_material_from_snapshot,
)
from app.ports.organizational_memory import OrganizationalMemoryUnitOfWork
from app.repositories.organizational_memory_repository import (
    OrganizationalMemoryIdempotencyRecord, OrganizationalMemoryOutboxRecord,
    OrganizationalMemoryRecord, OrganizationalMemoryStandingHistoryRecord,
    SqlAlchemyOrganizationalMemoryRepository,
)
from app.repositories.organizational_memory_unit_of_work import (
    MemoryAuthorizationDenied,
    SqlAlchemyOrganizationalMemoryUnitOfWork,
)
from app.services.organizational_memory_service import OrganizationalMemoryService
from test_organizational_memory_repository import _accepted_report, _memory
from conftest import owner_engine


NOW = datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc)


class _CanonicalReader:
    def __init__(self, snapshots, owners, *, deny_on_call=None):
        self.snapshots = snapshots; self.owners = owners
        self.deny_on_call = deny_on_call; self.calls = 0
    def read_authorized_accepted(self, _actor, source):
        self.calls += 1
        if self.deny_on_call == self.calls:
            return AcceptedReportProtectedNotFound()
        snapshot = self.snapshots.get(source.report_id)
        if snapshot is None or source.accepted_snapshot_digest != snapshot.integrity_digest:
            return AcceptedReportProtectedNotFound()
        return AcceptedReportProjection(
            source, self.owners[source.report_id],
            MemoryScope(snapshot.organization_id, snapshot.workspace_id, snapshot.project_id),
            snapshot,
        )


class _CanonicalProvenance:
    def __init__(self, snapshots): self.snapshots = snapshots
    def authorize_logical_operation(self, requests):
        snapshot = self.snapshots[requests[0].source.report_id]
        _, manifest = admission_material_from_snapshot(snapshot)
        return ProvenanceAuthorized("success", tuple(
            SafeAuthorizedProvenance(**asdict(entry))
            for entry in manifest.provenance_entries
        ))


class _Clock:
    def __init__(self, value=NOW + timedelta(seconds=100)): self.value = value
    def now(self):
        current = self.value; self.value += timedelta(seconds=1); return current


def _thread_service(snapshots, owners, *, reader=None, rejection_factory=None):
    session_factory = lambda: Session(owner_engine)
    return OrganizationalMemoryService(
        lambda: SqlAlchemyOrganizationalMemoryUnitOfWork(
            session_factory, rejection_factory or session_factory,
        ), reader or _CanonicalReader(snapshots, owners),
        _CanonicalProvenance(snapshots), _Clock(),
    )


def _metadata(actor, organization_id):
    return MemoryCommandMetadata(
        MemoryActor(actor.id, organization_id), uuid4(), uuid4(), uuid4(),
        "Human authority",
    )


def _source(report):
    return AcceptedReportSource(
        report.id, report.version, report.accepted_snapshot.integrity_digest,
    )


def test_concrete_uow_uses_one_session_for_all_atomic_collaborators(db_session):
    factory = lambda: db_session
    uow = SqlAlchemyOrganizationalMemoryUnitOfWork(factory, factory)
    with uow:
        sessions = {
            id(uow.session), id(uow.memories.session), id(uow.authorization.session),
            id(uow.final_recheck.session), id(uow.audit.session),
            id(uow.domain_events.session), id(uow.idempotency.session),
        }
        assert len(sessions) == 1
        assert callable(uow.flush) and callable(uow.commit) and callable(uow.rollback)


def test_repository_and_atomic_recorders_do_not_expose_commit(db_session):
    factory = lambda: db_session
    with SqlAlchemyOrganizationalMemoryUnitOfWork(factory, factory) as uow:
        for collaborator in (uow.memories, uow.audit, uow.domain_events, uow.idempotency, uow.final_recheck):
            assert not hasattr(collaborator, "commit")


def test_real_authority_rejects_engineer_who_does_not_own_source(
    db_session, relationship_domain,
):
    actor = relationship_domain["actors"]["project_owner"]
    scope = MemoryScope(
        relationship_domain["project"].organization_id,
        relationship_domain["consumer_workspace"].id,
        relationship_domain["project"].id,
    )
    request = MemoryAuthorizationRequest(
        MemoryActor(actor.id, scope.organization_id), MemoryOperation.ADMIT,
        scope, None, None, None, None, (actor.id,),
    )
    factory = lambda: db_session
    with SqlAlchemyOrganizationalMemoryUnitOfWork(factory, factory) as uow:
        with pytest.raises(MemoryAuthorizationDenied):
            uow.authorization.require(
                request, relationship_domain["actors"]["consumer"].id,
            )


def test_supersession_authority_uses_predecessor_withdraw_and_replacement_admit_rules(
    db_session, relationship_domain,
):
    actor = relationship_domain["actors"]["project_owner"]
    other_admitter = relationship_domain["actors"]["admin"]
    reports = tuple(_accepted_report(
        db_session, relationship_domain, accepted_at=NOW + timedelta(seconds=index),
    ) for index in range(4))
    materials = tuple(
        admission_material_from_snapshot(report.accepted_snapshot)
        for report in reports
    )
    predecessor = OrganizationalMemory.admit(
        memory_id=uuid4(), projection=materials[0][0], manifest=materials[0][1],
        admitted_by_id=actor.id, admitted_at=NOW + timedelta(seconds=10),
        admission_rationale="predecessor", audience_actor_ids=(actor.id,),
        reuse_restrictions=(),
    )
    replacement = OrganizationalMemory.create_successor(
        predecessor=predecessor, memory_id=uuid4(), projection=materials[1][0],
        manifest=materials[1][1], admitted_by_id=other_admitter.id,
        admitted_at=NOW + timedelta(seconds=11),
        admission_rationale="replacement admitted by another Human",
        audience_actor_ids=(actor.id,), reuse_restrictions=(),
    )
    repository = SqlAlchemyOrganizationalMemoryRepository(db_session)
    for memory in (predecessor, replacement):
        repository.add(memory); repository.append_history(memory.initial_history(event_id=uuid4()))
    db_session.flush()
    request = MemoryAuthorizationRequest(
        MemoryActor(actor.id, predecessor.organization_id), MemoryOperation.SUPERSEDE,
        MemoryScope(predecessor.organization_id, predecessor.workspace_id, predecessor.project_id),
        predecessor.id, replacement.source, predecessor.id, replacement.id,
        predecessor.audience_actor_ids,
    )
    unauthorized_predecessor = OrganizationalMemory.admit(
        memory_id=uuid4(), projection=materials[2][0], manifest=materials[2][1],
        admitted_by_id=other_admitter.id, admitted_at=NOW + timedelta(seconds=12),
        admission_rationale="unauthorized predecessor", audience_actor_ids=(actor.id,),
        reuse_restrictions=(),
    )
    unauthorized_replacement = OrganizationalMemory.create_successor(
        predecessor=unauthorized_predecessor, memory_id=uuid4(),
        projection=materials[3][0], manifest=materials[3][1],
        admitted_by_id=other_admitter.id, admitted_at=NOW + timedelta(seconds=13),
        admission_rationale="unauthorized replacement", audience_actor_ids=(actor.id,),
        reuse_restrictions=(),
    )
    repository.add(unauthorized_predecessor)
    repository.append_history(unauthorized_predecessor.initial_history(event_id=uuid4()))
    repository.add(unauthorized_replacement)
    repository.append_history(unauthorized_replacement.initial_history(event_id=uuid4()))
    db_session.flush()
    denied_request = replace(
        request, memory_id=unauthorized_predecessor.id,
        predecessor_memory_id=unauthorized_predecessor.id,
        replacement_memory_id=unauthorized_replacement.id,
    )
    factory = lambda: db_session
    with SqlAlchemyOrganizationalMemoryUnitOfWork(factory, factory) as uow:
        # Replacement was admitted by another Human, but actor has exact
        # predecessor withdrawal and replacement-source admission authority.
        uow.authorization.require(request, actor.id)
        with pytest.raises(MemoryAuthorizationDenied):
            uow.authorization.require(
                request, relationship_domain["actors"]["consumer"].id,
            )
        # Exact replacement-side admission authority is insufficient when the
        # actor lacks predecessor withdrawal/supersession authority.
        with pytest.raises(MemoryAuthorizationDenied):
            uow.authorization.require(denied_request, actor.id)


def test_rollback_permits_only_the_associated_rejection_boundary(db_session):
    factory = lambda: db_session
    with SqlAlchemyOrganizationalMemoryUnitOfWork(factory, factory) as uow:
        assert not uow.rejection_audit.permitted
        uow.rollback()
        assert uow.rejection_audit.permitted


@pytest.mark.parametrize("failure_stage", ("audit", "outbox", "idempotency"))
def test_real_uow_rolls_back_root_history_audit_outbox_and_idempotency_together(
    db_session, relationship_domain, failure_stage,
):
    memory = _memory(db_session, relationship_domain)
    event_id = uuid4(); command_id = uuid4(); correlation_id = uuid4()
    event = memory.event(
        event_id=event_id, event_type=MemoryEventType.ADMITTED,
        actor_id=memory.admitted_by_id, occurred_at=memory.admitted_at,
        command_id=command_id, correlation_id=correlation_id,
        causation_id=command_id,
    )
    key = MemoryIdempotencyKey(
        memory.organization_id, memory.admitted_by_id, "admit", uuid4(),
    )
    factory = lambda: db_session

    with pytest.raises(RuntimeError):
        with SqlAlchemyOrganizationalMemoryUnitOfWork(factory, factory) as uow:
            uow.memories.add(memory)
            uow.memories.append_history(memory.initial_history(event_id=event_id))
            uow.audit.record(MemoryAuditRecord(
                MemoryOperation.ADMIT, memory.admitted_by_id,
                memory.organization_id, memory.id, None, memory.version,
                memory.standing, memory.source.report_id,
                memory.source.accepted_aggregate_version, correlation_id,
                command_id, key.idempotency_id, memory.admitted_at,
                memory.predecessor_memory_id, memory.replacement_memory_id,
                len(memory.manifest.provenance_entries),
            ))
            if failure_stage == "audit":
                uow.flush()
                raise RuntimeError("fail after Audit stage")
            uow.domain_events.record((MemoryOutboxRecord(
                event.event_id, memory.id, memory.version, event.event_type, 1,
                event.payload, memory.admitted_at, memory.admitted_at,
            ),))
            if failure_stage == "outbox":
                uow.flush()
                raise RuntimeError("fail after outbox stage")
            uow.idempotency.reserve(key, "0" * 64)
            uow.idempotency.record_result(key, "0" * 64, StoredAdmissionResultV1(
                "admit.v1", memory.id, memory.version, "active",
                memory.source.report_id, memory.source.accepted_aggregate_version,
            ))
            uow.flush()
            audit = db_session.execute(select(AuditLog).where(
                AuditLog.entity_uuid == memory.id,
            )).scalar_one()
            assert set(audit.details) == {
                "outcome", "organization_id", "previous_version",
                "result_version", "standing", "source_report_id",
                "source_accepted_version", "command_id", "correlation_id",
                "idempotency_id", "provenance_entry_count",
            }
            serialized_details = repr(audit.details).lower()
            assert all(term not in serialized_details for term in (
                "technical_content", "admission_rationale", "limitations",
                "reuse_restrictions", "password", "exception",
            ))
            raise RuntimeError("fail after idempotency result stage")

    assert db_session.get(OrganizationalMemoryRecord, memory.id) is None
    assert db_session.execute(select(OrganizationalMemoryStandingHistoryRecord).where(
        OrganizationalMemoryStandingHistoryRecord.memory_id == memory.id,
    )).scalar_one_or_none() is None
    assert db_session.execute(select(OrganizationalMemoryOutboxRecord).where(
        OrganizationalMemoryOutboxRecord.memory_id == memory.id,
    )).scalar_one_or_none() is None
    assert db_session.execute(select(OrganizationalMemoryIdempotencyRecord).where(
        OrganizationalMemoryIdempotencyRecord.idempotency_id == key.idempotency_id,
    )).scalar_one_or_none() is None
    assert db_session.execute(select(AuditLog).where(
        AuditLog.entity_uuid == memory.id,
    )).scalar_one_or_none() is None


def test_real_uow_all_four_commands_and_persisted_replay(db_session, relationship_domain):
    actor = relationship_domain["actors"]["project_owner"]
    reports = [
        _accepted_report(
            db_session, relationship_domain,
            accepted_at=NOW + timedelta(seconds=index),
        )
        for index in range(3)
    ]
    snapshots = {report.id: report.accepted_snapshot for report in reports}

    class Reader:
        def read_authorized_accepted(self, memory_actor, source):
            snapshot = snapshots.get(source.report_id)
            if snapshot is None or source.accepted_snapshot_digest != snapshot.integrity_digest:
                return AcceptedReportProtectedNotFound()
            return AcceptedReportProjection(
                source, actor.id,
                MemoryScope(snapshot.organization_id, snapshot.workspace_id, snapshot.project_id),
                snapshot,
            )

    class Provenance:
        def authorize_logical_operation(self, requests):
            snapshot = snapshots[requests[0].source.report_id]
            _, manifest = admission_material_from_snapshot(snapshot)
            return ProvenanceAuthorized("success", tuple(
                SafeAuthorizedProvenance(**asdict(entry))
                for entry in manifest.provenance_entries
            ))

    class Clock:
        def __init__(self, value=NOW + timedelta(seconds=10)):
            self.value = value
        def now(self):
            current = self.value
            self.value += timedelta(seconds=1)
            return current

    factory = lambda: db_session
    service = OrganizationalMemoryService(
        lambda: SqlAlchemyOrganizationalMemoryUnitOfWork(factory, factory),
        Reader(), Provenance(), Clock(),
    )
    scope = MemoryScope(
        reports[0].organization_id, reports[0].workspace_id, reports[0].project_id,
    )
    def metadata():
        return MemoryCommandMetadata(
            MemoryActor(actor.id, reports[0].organization_id), uuid4(), uuid4(),
            uuid4(), "Human authority",
        )
    def source(report):
        return AcceptedReportSource(
            report.id, report.version, report.accepted_snapshot.integrity_digest,
        )

    admit = AdmitAcceptedReport(metadata(), source(reports[0]), scope, (actor.id,), (), "admit")
    first = service.admit(admit)
    successor_command = CreateMemorySuccessor(
        metadata(), source(reports[1]), scope, (actor.id,), (), "successor",
        first.memory_id,
    )
    successor = service.create_successor(successor_command)
    supersede = SupersedeMemory(
        metadata(), first.memory_id, successor.memory_id, 1, 1, "replace",
    )
    superseded = service.supersede(supersede)
    third_command = AdmitAcceptedReport(
        metadata(), source(reports[2]), scope, (actor.id,), (), "admit third",
    )
    third = service.admit(third_command)
    withdraw = WithdrawMemory(metadata(), third.memory_id, 1, "withdraw")
    withdrawn = service.withdraw(withdraw)

    assert service.admit(admit) == first
    assert service.create_successor(successor_command) == successor
    assert service.supersede(supersede) == superseded
    assert service.withdraw(withdraw) == withdrawn
    ids = {first.memory_id, successor.memory_id, third.memory_id}
    assert set(db_session.scalars(select(OrganizationalMemoryRecord.id).where(
        OrganizationalMemoryRecord.id.in_(ids),
    ))) == ids
    assert db_session.scalar(select(func.count()).select_from(
        OrganizationalMemoryIdempotencyRecord,
    ).where(
        OrganizationalMemoryIdempotencyRecord.status == "completed",
        OrganizationalMemoryIdempotencyRecord.idempotency_id.in_({
            admit.metadata.idempotency_id, successor_command.metadata.idempotency_id,
            supersede.metadata.idempotency_id, withdraw.metadata.idempotency_id,
            third_command.metadata.idempotency_id,
        }),
    )) == 5

    db_session.connection().commit()
    barrier = Barrier(2)
    commands = tuple(
        WithdrawMemory(metadata(), successor.memory_id, 1, f"winner-{index}")
        for index in range(2)
    )
    def concurrent_withdraw(command):
        barrier.wait()
        concurrent_service = OrganizationalMemoryService(
                lambda: SqlAlchemyOrganizationalMemoryUnitOfWork(
                    lambda: Session(owner_engine), lambda: Session(owner_engine),
                ), Reader(), Provenance(), Clock(NOW + timedelta(seconds=100)),
        )
        return concurrent_service.withdraw(command).outcome
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(concurrent_withdraw, commands))
    assert sorted(outcomes) == ["success", "version_conflict"]


def test_command_level_concurrent_admission_has_one_atomic_winner(
    db_session, relationship_domain,
):
    actor = relationship_domain["actors"]["project_owner"]
    report = _accepted_report(db_session, relationship_domain, accepted_at=NOW)
    snapshot = report.accepted_snapshot
    scope = MemoryScope(report.organization_id, report.workspace_id, report.project_id)
    commands = tuple(AdmitAcceptedReport(
        _metadata(actor, report.organization_id), _source(report), scope,
        (actor.id,), (), f"concurrent-admit-{index}",
    ) for index in range(2))
    db_session.connection().commit(); barrier = Barrier(2)
    def execute(command):
        barrier.wait()
        return _thread_service(
            {report.id: snapshot}, {report.id: actor.id},
        ).admit(command).outcome
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(execute, commands))
    assert sorted(outcomes) == ["duplicate_source", "success"]
    with Session(owner_engine) as session:
        roots = session.scalars(select(OrganizationalMemoryRecord).where(
            OrganizationalMemoryRecord.source_report_id == report.id,
        )).all()
        assert len(roots) == 1
        assert session.scalar(select(func.count()).select_from(
            OrganizationalMemoryStandingHistoryRecord,
        ).where(OrganizationalMemoryStandingHistoryRecord.memory_id == roots[0].id)) == 1
        assert session.scalar(select(func.count()).select_from(
            OrganizationalMemoryOutboxRecord,
        ).where(OrganizationalMemoryOutboxRecord.memory_id == roots[0].id)) == 1
        assert session.scalar(select(func.count()).select_from(
            OrganizationalMemoryIdempotencyRecord,
        ).where(OrganizationalMemoryIdempotencyRecord.idempotency_id.in_(
            tuple(command.metadata.idempotency_id for command in commands),
        ))) == 1
        assert session.scalar(select(func.count()).select_from(AuditLog).where(
            AuditLog.entity == "ORGANIZATIONAL_MEMORY",
            AuditLog.entity_uuid == roots[0].id,
        )) == 1


def test_command_level_concurrent_successor_has_one_atomic_winner(
    db_session, relationship_domain,
):
    actor = relationship_domain["actors"]["project_owner"]
    predecessor = _memory(db_session, relationship_domain, admitted_at=NOW)
    repository = SqlAlchemyOrganizationalMemoryRepository(db_session)
    repository.add(predecessor)
    repository.append_history(predecessor.initial_history(event_id=uuid4()))
    report = _accepted_report(
        db_session, relationship_domain, accepted_at=NOW + timedelta(seconds=1),
    )
    snapshot = report.accepted_snapshot
    scope = MemoryScope(report.organization_id, report.workspace_id, report.project_id)
    commands = tuple(CreateMemorySuccessor(
        _metadata(actor, report.organization_id), _source(report), scope,
        predecessor.audience_actor_ids, (), f"successor-{index}", predecessor.id,
    ) for index in range(2))
    db_session.connection().commit(); barrier = Barrier(2)
    def execute(command):
        barrier.wait()
        return _thread_service(
            {report.id: snapshot}, {report.id: actor.id},
        ).create_successor(command).outcome
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(execute, commands))
    assert sorted(outcomes) == ["duplicate_source", "success"]
    with Session(owner_engine) as session:
        winners = session.scalars(select(OrganizationalMemoryRecord).where(
            OrganizationalMemoryRecord.source_report_id == report.id,
        )).all()
        assert len(winners) == 1 and winners[0].predecessor_memory_id == predecessor.id
        assert session.scalar(select(func.count()).select_from(
            OrganizationalMemoryStandingHistoryRecord,
        ).where(
            OrganizationalMemoryStandingHistoryRecord.memory_id == winners[0].id,
        )) == 1
        assert session.scalar(select(func.count()).select_from(
            OrganizationalMemoryOutboxRecord,
        ).where(OrganizationalMemoryOutboxRecord.memory_id == winners[0].id)) == 1
        assert session.scalar(select(func.count()).select_from(
            OrganizationalMemoryIdempotencyRecord,
        ).where(OrganizationalMemoryIdempotencyRecord.idempotency_id.in_(
            tuple(command.metadata.idempotency_id for command in commands),
        ))) == 1
        assert session.scalar(select(func.count()).select_from(AuditLog).where(
            AuditLog.entity == "ORGANIZATIONAL_MEMORY",
            AuditLog.entity_uuid == winners[0].id,
        )) == 1


def test_command_level_concurrent_supersession_has_one_atomic_winner(
    db_session, relationship_domain,
):
    actor = relationship_domain["actors"]["project_owner"]
    reports = tuple(_accepted_report(
        db_session, relationship_domain, accepted_at=NOW + timedelta(seconds=index),
    ) for index in range(3))
    material = tuple(admission_material_from_snapshot(report.accepted_snapshot) for report in reports)
    predecessor = OrganizationalMemory.admit(
        memory_id=uuid4(), projection=material[0][0], manifest=material[0][1],
        admitted_by_id=actor.id, admitted_at=NOW + timedelta(seconds=10),
        admission_rationale="predecessor", audience_actor_ids=(actor.id,),
        reuse_restrictions=(),
    )
    replacements = tuple(OrganizationalMemory.create_successor(
        predecessor=predecessor, memory_id=uuid4(), projection=material[index][0],
        manifest=material[index][1], admitted_by_id=actor.id,
        admitted_at=NOW + timedelta(seconds=10 + index),
        admission_rationale=f"replacement-{index}",
        audience_actor_ids=(actor.id,), reuse_restrictions=(),
    ) for index in (1, 2))
    repository = SqlAlchemyOrganizationalMemoryRepository(db_session)
    for memory in (predecessor,) + replacements:
        repository.add(memory); repository.append_history(memory.initial_history(event_id=uuid4()))
    snapshots = {report.id: report.accepted_snapshot for report in reports}
    owners = {report.id: actor.id for report in reports}
    commands = tuple(SupersedeMemory(
        _metadata(actor, predecessor.organization_id), predecessor.id,
        replacement.id, 1, 1, f"supersede-{index}",
    ) for index, replacement in enumerate(replacements))
    db_session.connection().commit(); barrier = Barrier(2)
    def execute(command):
        barrier.wait(); return _thread_service(snapshots, owners).supersede(command).outcome
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(execute, commands))
    assert sorted(outcomes) == ["success", "version_conflict"]
    with Session(owner_engine) as session:
        root = session.get(OrganizationalMemoryRecord, predecessor.id)
        assert root.standing == "superseded"
        assert root.replacement_memory_id in {item.id for item in replacements}
        assert session.scalar(select(func.count()).select_from(
            OrganizationalMemoryStandingHistoryRecord,
        ).where(
            OrganizationalMemoryStandingHistoryRecord.memory_id == predecessor.id,
            OrganizationalMemoryStandingHistoryRecord.to_standing == "superseded",
        )) == 1
        assert session.scalar(select(func.count()).select_from(
            OrganizationalMemoryOutboxRecord,
        ).where(
            OrganizationalMemoryOutboxRecord.memory_id == predecessor.id,
            OrganizationalMemoryOutboxRecord.event_type
            == MemoryEventType.SUPERSEDED.value,
        )) == 1
        assert session.scalar(select(func.count()).select_from(
            OrganizationalMemoryIdempotencyRecord,
        ).where(OrganizationalMemoryIdempotencyRecord.idempotency_id.in_(
            tuple(command.metadata.idempotency_id for command in commands),
        ))) == 1
        assert session.scalar(select(func.count()).select_from(AuditLog).where(
            AuditLog.entity == "ORGANIZATIONAL_MEMORY",
            AuditLog.entity_uuid == predecessor.id,
            AuditLog.action == "supersede",
        )) == 1


def test_real_post_rollback_rejection_audit_and_failure_isolation(
    db_session, relationship_domain,
):
    actor = relationship_domain["actors"]["project_owner"]
    report = _accepted_report(db_session, relationship_domain, accepted_at=NOW)
    snapshot = report.accepted_snapshot
    snapshots = {report.id: snapshot}; owners = {report.id: actor.id}
    scope = MemoryScope(report.organization_id, report.workspace_id, report.project_id)
    command = AdmitAcceptedReport(
        _metadata(actor, report.organization_id), _source(report), scope,
        (actor.id,), (), "denied-final-recheck",
    )
    db_session.connection().commit()
    reader = _CanonicalReader(snapshots, owners, deny_on_call=2)
    result = _thread_service(snapshots, owners, reader=reader).admit(command)
    assert result.outcome == "protected_not_found"
    with Session(owner_engine) as session:
        assert session.scalar(select(func.count()).select_from(
            OrganizationalMemoryRecord,
        ).where(OrganizationalMemoryRecord.source_report_id == report.id)) == 0
        assert session.scalar(select(func.count()).select_from(
            OrganizationalMemoryIdempotencyRecord,
        ).where(
            OrganizationalMemoryIdempotencyRecord.idempotency_id
            == command.metadata.idempotency_id,
        )) == 0
        audit = session.scalar(select(AuditLog).where(
            AuditLog.details["command_id"].as_string()
            == str(command.metadata.command_id),
        ))
        assert audit is not None and audit.entity_uuid is None
        assert set(audit.details) == {
            "outcome", "reason", "organization_id", "command_id",
            "correlation_id",
        }
        assert all(term not in repr(audit.details).lower() for term in (
            "content", "snapshot", "rationale", "provenance", "password",
            "exception",
        ))

    failed_command = replace(command, metadata=_metadata(actor, report.organization_id))
    failing_reader = _CanonicalReader(snapshots, owners, deny_on_call=2)
    def failed_rejection_factory(): raise RuntimeError("Audit unavailable")
    isolated = _thread_service(
        snapshots, owners, reader=failing_reader,
        rejection_factory=failed_rejection_factory,
    ).admit(failed_command)
    assert isolated.outcome == "protected_not_found"
    with Session(owner_engine) as session:
        assert session.scalar(select(func.count()).select_from(
            OrganizationalMemoryRecord,
        ).where(OrganizationalMemoryRecord.source_report_id == report.id)) == 0
        assert session.scalar(select(func.count()).select_from(
            OrganizationalMemoryIdempotencyRecord,
        ).where(
            OrganizationalMemoryIdempotencyRecord.idempotency_id
            == failed_command.metadata.idempotency_id,
        )) == 0
        assert session.scalar(select(func.count()).select_from(AuditLog).where(
            AuditLog.details["command_id"].as_string()
            == str(failed_command.metadata.command_id),
        )) == 0
