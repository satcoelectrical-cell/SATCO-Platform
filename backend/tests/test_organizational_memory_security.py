"""PATCH-034 Batch 3 authorization and non-disclosure evidence."""

from dataclasses import fields, replace
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.adapters.organizational_memory import TechnicalReportAcceptedSourceAdapter
from app.exceptions.evidence import EvidenceProtectedNotFound
from app.exceptions.technical_report import TechnicalReportAuthorizationDenied
from app.enums import TechnicalReportLifecycle
from app.models.organizational_memory_command import (
    AcceptedReportProtectedNotFound,
    AcceptedReportSource,
    AcceptedReportUnavailable,
    MemoryActor,
    MemoryScope,
    ProvenanceProtectedNotFound,
    ProvenanceUnavailable,
)
from test_organizational_memory_service import GetActiveMemory, admit_command, setup
from test_organizational_memory_integration import (
    RecordingService,
    accepted_fixture,
    actual_canonical_services,
    authorizer,
    canonical_services,
    provenance_request,
    source_reader,
)


def test_source_authorization_precedes_every_provenance_disclosure():
    snapshot, locators = accepted_fixture(); request = provenance_request(snapshot, locators)
    denied_reader = TechnicalReportAcceptedSourceAdapter(
        RecordingService(failure=RuntimeError("database credential and report body")),
    )
    services = canonical_services(locators)
    from app.adapters.organizational_memory import CanonicalMemoryProvenanceAuthorizer
    adapter = CanonicalMemoryProvenanceAuthorizer(
        accepted_reports=denied_reader, captures=services[0], evidence=services[1],
        engineering_objects=services[2], engineering_relationships=services[3],
    )
    result = adapter.authorize_and_resolve(request)
    assert isinstance(result, ProvenanceUnavailable)
    assert all(not service.calls for service in services)
    assert [field.name for field in fields(result)] == ["outcome"]


def test_scope_or_canonical_identity_mismatch_is_payload_free_and_all_or_nothing():
    snapshot, locators = accepted_fixture(); request = provenance_request(snapshot, locators)
    services = canonical_services(locators)
    services[1].response = SimpleNamespace(
        id=uuid4(), organization_id=snapshot.organization_id,
        project_id=11, workspace_id=12,
    )
    adapter, _, _ = authorizer(snapshot, locators, services)
    result = adapter.authorize_and_resolve(request)
    assert isinstance(result, ProvenanceProtectedNotFound)
    assert [field.name for field in fields(result)] == ["outcome"]
    assert "source body" not in repr(result) and "supported fact" not in repr(result)
    assert not services[2].calls and not services[3].calls


def test_protected_canonical_exception_does_not_leak_identity_count_or_exception():
    snapshot, locators = accepted_fixture(); request = provenance_request(snapshot, locators)
    services = canonical_services(locators)
    services[1].failure = EvidenceProtectedNotFound()
    adapter, _, _ = authorizer(snapshot, locators, services)
    result = adapter.authorize_and_resolve(request)
    assert isinstance(result, ProvenanceProtectedNotFound)
    assert repr(result) == "ProvenanceProtectedNotFound(outcome='protected_not_found')"
    assert not hasattr(result, "items") and not hasattr(result, "count")


def test_source_version_digest_or_scope_mismatch_is_protected_and_payload_free():
    snapshot, _ = accepted_fixture(); reader, _ = source_reader(snapshot)
    actor = MemoryActor(9, snapshot.organization_id)
    bad = AcceptedReportSource(
        snapshot.report_id, snapshot.accepted_aggregate_version + 1,
        snapshot.integrity_digest,
    )
    result = reader.read_authorized_accepted(actor, bad)
    assert isinstance(result, AcceptedReportProtectedNotFound)
    assert [field.name for field in fields(result)] == ["outcome"]


def test_draft_missing_revoked_digest_and_scope_failures_are_equivalent():
    snapshot, _ = accepted_fixture()
    actor = MemoryActor(9, snapshot.organization_id)
    exact = AcceptedReportSource(
        snapshot.report_id, snapshot.accepted_aggregate_version,
        snapshot.integrity_digest,
    )
    base = dict(
        id=snapshot.report_id, organization_id=snapshot.organization_id,
        workspace_id=snapshot.workspace_id, project_id=snapshot.project_id,
        owner_id=7, lifecycle=TechnicalReportLifecycle.ACCEPTED,
        version=snapshot.accepted_aggregate_version,
        accepted_snapshot=snapshot,
    )
    variants = (
        ({**base, "lifecycle": TechnicalReportLifecycle.DRAFT}, exact),
        ({**base, "accepted_snapshot": None}, exact),
        ({**base, "workspace_id": 99}, exact),
        (base, AcceptedReportSource(
            snapshot.report_id, snapshot.accepted_aggregate_version, "f" * 64,
        )),
    )
    for view, source in variants:
        result = TechnicalReportAcceptedSourceAdapter(
            RecordingService(SimpleNamespace(**view)),
        ).read_authorized_accepted(actor, source)
        assert isinstance(result, AcceptedReportProtectedNotFound)
        assert [field.name for field in fields(result)] == ["outcome"]
    for failure in (TechnicalReportAuthorizationDenied(),):
        result = TechnicalReportAcceptedSourceAdapter(
            RecordingService(failure=failure),
        ).read_authorized_accepted(actor, exact)
        assert isinstance(result, AcceptedReportProtectedNotFound)


def test_dependency_failure_is_unavailable_without_internal_details():
    snapshot, locators = accepted_fixture(); request = provenance_request(snapshot, locators)
    services = canonical_services(locators)
    services[0].failure = RuntimeError("postgres password=secret source body")
    adapter, _, _ = authorizer(snapshot, locators, services)
    result = adapter.authorize_and_resolve(request)
    assert isinstance(result, ProvenanceUnavailable)
    assert repr(result) == "ProvenanceUnavailable(outcome='unavailable')"


def test_request_basis_mismatch_never_calls_foreign_capabilities():
    snapshot, locators = accepted_fixture(); request = provenance_request(snapshot, locators)
    first = request.items[0]
    request = replace(request, items=(replace(first, source_version=99),) + request.items[1:])
    services = canonical_services(locators)
    adapter, _, _ = authorizer(snapshot, locators, services)
    result = adapter.authorize_and_resolve(request)
    assert isinstance(result, ProvenanceProtectedNotFound)
    assert all(not service.calls for service in services)


def test_actual_canonical_service_denial_is_all_or_nothing_and_payload_free():
    snapshot, locators = accepted_fixture()
    services, policies, _ = actual_canonical_services(locators, denied="evidence")
    adapter, _, _ = authorizer(snapshot, locators, services)
    result = adapter.authorize_and_resolve(provenance_request(snapshot, locators))
    assert isinstance(result, ProvenanceProtectedNotFound)
    assert [field.name for field in fields(result)] == ["outcome"]
    assert policies["evidence"].calls[0]["operation"] == "ReadEvidence"
    assert not policies["object"].calls
    assert not policies["relationship"].calls


def test_current_source_revocation_never_falls_back_to_retained_projection():
    service, uow, _, snapshot = setup(); actor = MemoryActor(9, snapshot.organization_id)
    admitted = service.admit(admit_command(snapshot))
    service.accepted_reports._technical_reports.failure = TechnicalReportAuthorizationDenied()
    result = service.get_active(actor, GetActiveMemory(admitted.memory_id, True))
    assert result.outcome == "protected_not_found"
    assert [field.name for field in fields(result)] == ["outcome"]
    assert "technical_content" not in repr(result) and "provenance" not in repr(result)


def test_provenance_denial_is_all_or_nothing_at_memory_read_boundary():
    service, _, _, snapshot = setup(); actor = MemoryActor(9, snapshot.organization_id)
    admitted = service.admit(admit_command(snapshot))
    original = service.provenance.authorize_logical_operation
    service.provenance.authorize_logical_operation = lambda _requests: ProvenanceProtectedNotFound()
    result = service.get_active(actor, GetActiveMemory(admitted.memory_id, True))
    assert result.outcome == "protected_not_found"
    assert not hasattr(result, "items") and not hasattr(result, "count")
    service.provenance.authorize_logical_operation = original


def test_concrete_policy_enforces_exact_read_operations_without_mutation_drift(
    db_session, relationship_domain,
):
    from app.enums.organizational_memory import MemoryOperation
    from app.models.organizational_memory_command import MemoryAuthorizationRequest
    from app.repositories.organizational_memory_repository import SqlAlchemyOrganizationalMemoryRepository
    from app.repositories.organizational_memory_unit_of_work import (
        MemoryAuthorizationDenied, SqlAlchemyOrganizationalMemoryUnitOfWork,
    )
    from test_organizational_memory_repository import _memory
    memory = _memory(db_session, relationship_domain)
    repository = SqlAlchemyOrganizationalMemoryRepository(db_session)
    repository.add(memory); repository.append_history(memory.initial_history(event_id=uuid4()))
    actor = MemoryActor(memory.admitted_by_id, memory.organization_id)
    scope = MemoryScope(memory.organization_id, memory.workspace_id, memory.project_id)
    factory = lambda: db_session
    with SqlAlchemyOrganizationalMemoryUnitOfWork(factory, factory) as uow:
        for operation, identity in (
            (MemoryOperation.GET_ACTIVE, memory.id),
            (MemoryOperation.LIST_ACTIVE, None),
            (MemoryOperation.INSPECT_HISTORY, memory.id),
        ):
            uow.authorization.require(MemoryAuthorizationRequest(
                actor, operation, scope, identity,
                None if identity is None else memory.source,
                None, None, () if identity is None else memory.audience_actor_ids,
            ))
        outsider = MemoryActor(
            relationship_domain["actors"]["consumer"].id,
            memory.organization_id,
        )
        with pytest.raises(MemoryAuthorizationDenied):
            uow.authorization.require(MemoryAuthorizationRequest(
                outsider, MemoryOperation.INSPECT_HISTORY, scope, memory.id,
                memory.source, None, None, memory.audience_actor_ids,
            ))


def test_unrelated_inactive_audience_member_does_not_block_authorized_reader(
    db_session, relationship_domain,
):
    from dataclasses import replace as dc_replace
    from app.enums.organizational_memory import MemoryOperation
    from app.models.organizational_memory_command import MemoryAuthorizationRequest
    from app.repositories.organizational_memory_repository import SqlAlchemyOrganizationalMemoryRepository
    from app.repositories.organizational_memory_unit_of_work import SqlAlchemyOrganizationalMemoryUnitOfWork
    from test_organizational_memory_repository import _memory
    actor = relationship_domain["actors"]["project_owner"]
    unrelated = relationship_domain["actors"]["consumer"]
    memory = dc_replace(
        _memory(db_session, relationship_domain),
        audience_actor_ids=tuple(sorted((actor.id, unrelated.id))),
    )
    repository = SqlAlchemyOrganizationalMemoryRepository(db_session)
    repository.add(memory); repository.append_history(memory.initial_history(event_id=uuid4()))
    unrelated.is_active = False; db_session.flush()
    request = MemoryAuthorizationRequest(
        MemoryActor(actor.id, memory.organization_id), MemoryOperation.GET_ACTIVE,
        MemoryScope(memory.organization_id, memory.workspace_id, memory.project_id),
        memory.id, memory.source, None, None, memory.audience_actor_ids,
    )
    factory = lambda: db_session
    with SqlAlchemyOrganizationalMemoryUnitOfWork(factory, factory) as uow:
        uow.authorization.require(request)


def test_history_fails_closed_when_transition_human_is_not_currently_visible(
    db_session, relationship_domain,
):
    from app.enums.organizational_memory import MemoryOperation
    from app.models.organizational_memory_command import MemoryAuthorizationRequest
    from app.repositories.organizational_memory_repository import SqlAlchemyOrganizationalMemoryRepository
    from app.repositories.organizational_memory_unit_of_work import (
        MemoryAuthorizationDenied, SqlAlchemyOrganizationalMemoryUnitOfWork,
    )
    from test_organizational_memory_repository import _memory
    actor = relationship_domain["actors"]["project_owner"]
    transition_human = relationship_domain["actors"]["consumer"]
    memory = _memory(db_session, relationship_domain)
    repository = SqlAlchemyOrganizationalMemoryRepository(db_session)
    repository.add(memory); repository.append_history(memory.initial_history(event_id=uuid4()))
    withdrawn, history = memory.withdraw(
        expected_version=1, actor_id=transition_human.id,
        occurred_at=memory.admitted_at.replace(microsecond=1), reason="withdrawn",
    )
    assert repository.persist_standing_expected_version(withdrawn, 1)
    repository.append_history(history)
    transition_human.is_active = False; db_session.flush()
    request = MemoryAuthorizationRequest(
        MemoryActor(actor.id, memory.organization_id), MemoryOperation.INSPECT_HISTORY,
        MemoryScope(memory.organization_id, memory.workspace_id, memory.project_id),
        memory.id, memory.source, None, None, memory.audience_actor_ids,
    )
    factory = lambda: db_session
    with SqlAlchemyOrganizationalMemoryUnitOfWork(factory, factory) as uow:
        with pytest.raises(MemoryAuthorizationDenied):
            uow.authorization.require(request)


def test_batch6_router_has_no_infrastructure_or_policy_ownership():
    from pathlib import Path

    source = Path("app/api/v1/routers/organizational_memory.py").read_text()
    prohibited = (
        "sqlalchemy", "SessionLocal", "get_db", "Repository",
        "UnitOfWork", "AuthorizationPolicy", "ReferenceValidator",
    )
    assert all(term not in source for term in prohibited)
    assert "get_organizational_memory_application" in source
