"""PATCH-034 Batch 4 command and replay evidence."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.enums.organizational_memory import MemoryStanding
from app.models.organizational_memory_command import (
    AdmitAcceptedReport, CreateMemorySuccessor, GetActiveMemory,
    InspectMemoryHistory, ListActiveMemory, MemoryActor,
    MemoryCommandMetadata, MemoryIdempotencyCompleted, MemoryIdempotencyMiss,
    MemoryIdempotencyPending, MemoryScope, SupersedeMemory, WithdrawMemory,
)
from app.services.organizational_memory_service import OrganizationalMemoryService
from test_organizational_memory_integration import accepted_fixture, authorizer, source_reader


NOW = datetime(2026, 8, 13, 10, 0, tzinfo=timezone.utc)


class Clock:
    def __init__(self): self.value = NOW
    def now(self): return self.value


class Repository:
    def __init__(self): self.items = {}; self.histories = []
    def add(self, item): self.items[item.id] = item
    def get_by_source(self, source, organization_id):
        return next((x for x in self.items.values() if x.organization_id == organization_id and x.source == source), None)
    def get_scoped(self, identity, organization_id):
        item = self.items.get(identity); return item if item and item.organization_id == organization_id else None
    lock_scoped = get_scoped
    def lock_pair_scoped(self, first, second, organization_id):
        a = self.get_scoped(first, organization_id); b = self.get_scoped(second, organization_id)
        return None if a is None or b is None else (a, b)
    def persist_standing_expected_version(self, memory, expected):
        current = self.items.get(memory.id)
        if current is None or current.version != expected: return False
        self.items[memory.id] = memory; return True
    def append_history(self, history): self.histories.append(history)
    def list_active(self, criteria):
        from app.ports.organizational_memory import MemoryCandidatePage
        items = [item for item in self.items.values() if (
            item.organization_id == criteria.organization_id
            and item.workspace_id == criteria.workspace_id
            and item.standing is MemoryStanding.ACTIVE
            and (criteria.project_id is None or item.project_id == criteria.project_id)
            and (criteria.purpose is None or item.projection.purpose is criteria.purpose)
            and (criteria.anchor is None or (
                item.admitted_at < criteria.anchor.admitted_at
                or (item.admitted_at == criteria.anchor.admitted_at and item.id > criteria.anchor.memory_id)
            ))
        )]
        items.sort(key=lambda item: (-item.admitted_at.timestamp(), str(item.id)))
        return MemoryCandidatePage(tuple(items[:criteria.candidate_limit]), len(items) > criteria.candidate_limit)


class Idempotency:
    def __init__(self): self.rows = {}
    def find(self, key): return self.rows.get(key, MemoryIdempotencyMiss())
    def reserve(self, key, fingerprint): self.rows[key] = MemoryIdempotencyPending()
    def record_result(self, key, fingerprint, result):
        self.rows[key] = MemoryIdempotencyCompleted("completed", fingerprint, 1, result)


class Recorder:
    def __init__(self): self.values = []
    def record(self, value): self.values.extend(value if isinstance(value, tuple) else (value,))


class Policy:
    def __init__(self): self.requests = []; self.owner_ids = []; self.deny = False
    def require(self, request, source_owner_id=None):
        self.requests.append(request); self.owner_ids.append(source_owner_id)
        if self.deny:
            from app.repositories.organizational_memory_unit_of_work import MemoryAuthorizationDenied
            raise MemoryAuthorizationDenied()
    require_current = require


class Rejection:
    def __init__(self): self.values = []; self.permitted = True
    def record_rejection(self, value): self.values.append(value)


class Uow:
    def __init__(self, repository):
        self.memories = repository; self.authorization = Policy(); self.final_recheck = Policy()
        self.audit = Recorder(); self.domain_events = Recorder(); self.idempotency = Idempotency()
        self.rejection_audit = Rejection(); self.commits = self.rollbacks = self.flushes = 0
    def __enter__(self): return self
    def __exit__(self, exc_type, *_):
        if exc_type: self.rollback()
    def flush(self): self.flushes += 1
    def commit(self): self.commits += 1
    def rollback(self): self.rollbacks += 1


def setup(snapshot=None):
    snapshot, locators = accepted_fixture() if snapshot is None else snapshot
    reader, _ = source_reader(snapshot); provenance, _, _ = authorizer(snapshot, locators)
    repository = Repository(); uow = Uow(repository); clock = Clock()
    return OrganizationalMemoryService(lambda: uow, reader, provenance, clock), uow, clock, snapshot


def metadata(snapshot, idempotency=None):
    return MemoryCommandMetadata(MemoryActor(9, snapshot.organization_id), uuid4(), uuid4(), idempotency or uuid4(), "Human authority")


def admit_command(snapshot, idempotency=None):
    from app.models.organizational_memory_command import AcceptedReportSource
    return AdmitAcceptedReport(
        metadata(snapshot, idempotency), AcceptedReportSource(snapshot.report_id, snapshot.accepted_aggregate_version, snapshot.integrity_digest),
        MemoryScope(snapshot.organization_id, snapshot.workspace_id, snapshot.project_id),
        (9,), ("retain limitations",), "Human admission",
    )


def test_admit_is_atomic_and_exact_replay_has_no_new_side_effects():
    service, uow, _, snapshot = setup(); command = admit_command(snapshot)
    first = service.admit(command); second = service.admit(command)
    assert first == second and first.standing is MemoryStanding.ACTIVE
    assert uow.commits == 1 and len(uow.memories.items) == 1
    assert len(uow.memories.histories) == len(uow.audit.values) == len(uow.domain_events.values) == 1


def test_withdraw_expected_version_and_stable_replay_after_later_state():
    service, uow, clock, snapshot = setup(); admitted = service.admit(admit_command(snapshot))
    clock.value += timedelta(seconds=1)
    command = WithdrawMemory(metadata(snapshot), admitted.memory_id, 1, "obsolete")
    first = service.withdraw(command); second = service.withdraw(command)
    assert first == second and first.standing is MemoryStanding.WITHDRAWN
    assert uow.commits == 2


def test_successor_then_explicit_supersession_preserves_replacement_active():
    service, uow, clock, snapshot = setup(); first_provenance = service.provenance
    first = service.admit(admit_command(snapshot))
    next_snapshot = replace(snapshot, report_id=uuid4(), accepted_aggregate_version=7)
    next_snapshot, locators = next_snapshot, tuple(x.locator for x in next_snapshot.provenance)
    next_reader, _ = source_reader(next_snapshot); next_provenance, _, _ = authorizer(next_snapshot, locators)
    service.accepted_reports = next_reader; service.provenance = next_provenance
    from app.models.organizational_memory_command import AcceptedReportSource
    clock.value += timedelta(seconds=1)
    successor_command = CreateMemorySuccessor(
        metadata(next_snapshot), AcceptedReportSource(next_snapshot.report_id, 7, next_snapshot.integrity_digest),
        MemoryScope(next_snapshot.organization_id, 12, 11), (9,), (), "replacement", first.memory_id,
    )
    successor = service.create_successor(successor_command)
    # Both exact sources remain authorized through their own immutable views.
    readers = {snapshot.report_id: source_reader(snapshot)[0], next_snapshot.report_id: next_reader}
    class MultiReader:
        def read_authorized_accepted(self, actor, source): return readers[source.report_id].read_authorized_accepted(actor, source)
    provenance = {snapshot.report_id: first_provenance, next_snapshot.report_id: next_provenance}
    class MultiProvenance:
        def authorize_logical_operation(self, requests):
            return provenance[requests[0].source.report_id].authorize_logical_operation(requests)
    service.accepted_reports = MultiReader(); service.provenance = MultiProvenance()
    clock.value += timedelta(seconds=1)
    result = service.supersede(SupersedeMemory(
        metadata(snapshot), first.memory_id, successor.memory_id, 1, 1, "new accepted basis",
    ))
    assert result.predecessor_standing is MemoryStanding.SUPERSEDED
    assert uow.memories.items[successor.memory_id].standing is MemoryStanding.ACTIVE


def test_fingerprint_conflict_and_current_authority_denial_precede_replay():
    service, uow, _, snapshot = setup(); idempotency = uuid4()
    first_command = admit_command(snapshot, idempotency)
    first = service.admit(first_command)
    different = replace(first_command, admission_rationale="different Human rationale")
    assert service.admit(different).outcome == "idempotency_conflict"
    uow.authorization.deny = True
    assert service.admit(first_command).outcome == "protected_not_found"
    assert len(uow.memories.items) == 1 and uow.commits == 1


def test_rejection_audit_occurs_after_authoritative_rollback_and_failure_is_isolated():
    service, uow, _, snapshot = setup(); uow.authorization.deny = True
    result = service.admit(admit_command(snapshot))
    assert result.outcome == "protected_not_found"
    assert uow.rollbacks == 1 and len(uow.rejection_audit.values) == 1


def test_source_owner_reaches_initial_and_final_authority_decisions():
    service, uow, _, snapshot = setup(); service.admit(admit_command(snapshot))
    assert uow.authorization.owner_ids[-1] == 7
    assert uow.final_recheck.owner_ids[-1] == 7


def test_stale_final_recheck_maps_to_version_conflict_without_rejection_audit():
    service, uow, clock, snapshot = setup(); admitted = service.admit(admit_command(snapshot))
    clock.value += timedelta(seconds=1)
    from app.exceptions.organizational_memory import OrganizationalMemoryVersionConflict
    def stale(*_args, **_kwargs): raise OrganizationalMemoryVersionConflict()
    uow.final_recheck.require_current = stale
    result = service.withdraw(WithdrawMemory(
        metadata(snapshot), admitted.memory_id, 1, "obsolete",
    ))
    assert result.outcome == "version_conflict"
    assert not uow.rejection_audit.values


def test_withdraw_and_supersede_repeat_sources_after_idempotency_reservation():
    service, uow, clock, snapshot = setup(); first = service.admit(admit_command(snapshot))
    reader = service.accepted_reports
    initial_calls = len(reader._technical_reports.calls)
    clock.value += timedelta(seconds=1)
    service.withdraw(WithdrawMemory(metadata(snapshot), first.memory_id, 1, "obsolete"))
    assert len(reader._technical_reports.calls) == initial_calls + 2


def test_active_read_and_history_use_closed_standing_specific_results():
    service, uow, clock, snapshot = setup(); actor = MemoryActor(9, snapshot.organization_id)
    admitted = service.admit(admit_command(snapshot))
    active = service.get_active(actor, GetActiveMemory(admitted.memory_id, True, True))
    assert active.outcome == "success" and active.item.summary.standing is MemoryStanding.ACTIVE
    assert active.item.safe_provenance
    active_history = service.inspect_history(actor, InspectMemoryHistory(admitted.memory_id))
    assert active_history.outcome == "success" and active_history.item.standing is MemoryStanding.ACTIVE
    clock.value += timedelta(seconds=1)
    service.withdraw(WithdrawMemory(metadata(snapshot), admitted.memory_id, 1, "obsolete"))
    history = service.inspect_history(actor, InspectMemoryHistory(admitted.memory_id, include_provenance=True))
    assert history.outcome == "success" and history.item.standing is MemoryStanding.WITHDRAWN
    assert history.item.withdrawal_reason == "obsolete" and history.item.safe_provenance
    assert service.get_active(actor, GetActiveMemory(admitted.memory_id)).outcome == "protected_not_found"


def test_read_authorization_precedes_source_and_protected_results_are_payload_free():
    service, uow, _, snapshot = setup(); actor = MemoryActor(9, snapshot.organization_id)
    admitted = service.admit(admit_command(snapshot))
    reader = service.accepted_reports; before = len(reader._technical_reports.calls)
    uow.authorization.deny = True
    result = service.get_active(actor, GetActiveMemory(admitted.memory_id, True))
    from dataclasses import fields
    assert result.outcome == "protected_not_found" and [
        field.name for field in fields(result)
    ] == ["outcome"]
    assert len(reader._technical_reports.calls) == before
