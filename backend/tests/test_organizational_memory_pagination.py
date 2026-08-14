"""PATCH-034 Batch 5 bounded pagination and continuation evidence."""

from dataclasses import replace
from datetime import timedelta
import base64
import json
from uuid import UUID

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.enums.organizational_memory import MemoryStanding
from app.models.organizational_memory_command import (
    GetActiveMemory, ListActiveMemory, MemoryActor, MemoryScope,
)
from test_organizational_memory_service import admit_command, setup


def _populate(count):
    service, uow, clock, snapshot = setup()
    items = []; readers = {}; authorizers = {}
    for index in range(count):
        current = replace(snapshot, report_id=UUID(int=index + 1))
        integration = __import__(
            "test_organizational_memory_integration", fromlist=["source_reader"]
        )
        reader, _ = integration.source_reader(current)
        provenance, _, _ = integration.authorizer(
            current, tuple(entry.locator for entry in current.provenance),
        )
        service.accepted_reports = reader
        service.provenance = provenance
        readers[current.report_id] = reader
        authorizers[current.report_id] = provenance
        command = admit_command(current)
        admitted = service.admit(command)
        items.append(uow.memories.items[admitted.memory_id])
        clock.value += timedelta(seconds=1)
    class MultiReader:
        def read_authorized_accepted(self, actor, source):
            return readers[source.report_id].read_authorized_accepted(actor, source)
    class MultiProvenance:
        def authorize_logical_operation(self, requests):
            return authorizers[requests[0].source.report_id].authorize_logical_operation(requests)
    service.accepted_reports = MultiReader(); service.provenance = MultiProvenance()
    return service, uow, clock, snapshot, items


def test_canonical_order_and_authenticated_continuation_have_no_skip_or_duplicate():
    service, _, _, snapshot, items = _populate(5)
    actor = MemoryActor(9, snapshot.organization_id)
    scope = MemoryScope(snapshot.organization_id, snapshot.workspace_id, snapshot.project_id)
    request = ListActiveMemory(scope, 2)
    first = service.list_active(actor, request)
    assert first.outcome == "success" and first.page.visible_total == 2
    assert [item.admitted_at for item in first.page.items] == sorted(
        (item.admitted_at for item in first.page.items), reverse=True,
    )
    assert first.page.next_continuation and not any(
        str(item.id) in first.page.next_continuation for item in items
    )
    second = service.list_active(actor, replace(
        request, continuation=first.page.next_continuation,
    ))
    assert second.outcome == "success"
    assert not ({item.memory_id for item in first.page.items} & {
        item.memory_id for item in second.page.items
    })


def test_denied_candidate_advances_last_evaluated_anchor():
    service, uow, _, snapshot, items = _populate(4)
    actor = MemoryActor(9, snapshot.organization_id)
    ordered = sorted(items, key=lambda item: (-item.admitted_at.timestamp(), str(item.id)))
    denied = ordered[1]
    original = uow.authorization.require
    def selective(request, source_owner_id=None):
        if request.memory_id == denied.id:
            from app.repositories.organizational_memory_unit_of_work import MemoryAuthorizationDenied
            raise MemoryAuthorizationDenied()
        return original(request, source_owner_id)
    uow.authorization.require = selective
    request = ListActiveMemory(
        MemoryScope(snapshot.organization_id, snapshot.workspace_id, snapshot.project_id), 2,
    )
    first = service.list_active(actor, request)
    second = service.list_active(actor, replace(
        request, continuation=first.page.next_continuation,
    ))
    returned = [item.memory_id for item in first.page.items + second.page.items]
    assert denied.id not in returned and len(returned) == len(set(returned))


def test_token_tamper_binding_and_expiry_are_payload_free_invalid_request():
    service, _, clock, snapshot, _ = _populate(3)
    actor = MemoryActor(9, snapshot.organization_id)
    scope = MemoryScope(snapshot.organization_id, snapshot.workspace_id, snapshot.project_id)
    request = ListActiveMemory(scope, 1)
    token = service.list_active(actor, request).page.next_continuation
    variants = (
        token[:-1] + ("A" if token[-1] != "A" else "B"),
        token,
    )
    tampered = service.list_active(actor, replace(request, continuation=variants[0]))
    from dataclasses import fields
    assert tampered.outcome == "invalid_request" and [
        field.name for field in fields(tampered)
    ] == ["outcome"]
    mismatch = service.list_active(actor, ListActiveMemory(scope, 2, token))
    assert mismatch.outcome == "invalid_request"
    clock.value += timedelta(minutes=16)
    expired = service.list_active(actor, replace(request, continuation=variants[1]))
    assert expired.outcome == "invalid_request"


def test_candidate_and_canonical_call_bounds_and_visible_count_only():
    service, uow, _, snapshot, _ = _populate(105)
    actor = MemoryActor(9, snapshot.organization_id)
    calls = 0; original = service.accepted_reports.read_authorized_accepted
    def counted(actor_value, source):
        nonlocal calls; calls += 1; return original(actor_value, source)
    service.accepted_reports.read_authorized_accepted = counted
    page = service.list_active(actor, ListActiveMemory(
        MemoryScope(snapshot.organization_id, snapshot.workspace_id, snapshot.project_id), 100,
    )).page
    assert len(page.items) == page.visible_total == 100
    assert calls == 100 and page.next_continuation is not None
    assert not hasattr(page, "hidden_total") and not hasattr(page, "authorized_total")


def test_page_size_contract_remains_one_through_one_hundred():
    _, _, _, snapshot, _ = _populate(1)
    scope = MemoryScope(snapshot.organization_id, snapshot.workspace_id, snapshot.project_id)
    assert ListActiveMemory(scope, 1).page_size == 1
    assert ListActiveMemory(scope, 100).page_size == 100


def test_equal_timestamp_order_is_memory_uuid_ascending():
    service, uow, _, snapshot, items = _populate(4)
    common_time = items[0].admitted_at
    replacements = []
    for index, item in enumerate(items):
        updated = replace(
            item, id=UUID(int=100 - index), admitted_at=common_time,
            created_at=common_time, updated_at=common_time,
        )
        replacements.append(updated)
    uow.memories.items = {item.id: item for item in replacements}
    result = service.list_active(
        MemoryActor(9, snapshot.organization_id),
        ListActiveMemory(MemoryScope(
            snapshot.organization_id, snapshot.workspace_id, snapshot.project_id,
        ), 4),
    )
    assert [item.memory_id for item in result.page.items] == sorted(
        (item.id for item in replacements), key=str,
    )


def test_token_rejects_actor_organization_workspace_project_and_version_mismatch():
    service, _, _, snapshot, _ = _populate(3)
    actor = MemoryActor(9, snapshot.organization_id)
    scope = MemoryScope(snapshot.organization_id, snapshot.workspace_id, snapshot.project_id)
    request = ListActiveMemory(scope, 1)
    token = service.list_active(actor, request).page.next_continuation
    mismatches = (
        (MemoryActor(10, snapshot.organization_id), request),
        (MemoryActor(9, UUID(int=999)), request),
        (actor, ListActiveMemory(MemoryScope(snapshot.organization_id, 999, snapshot.project_id), 1, token)),
        (actor, ListActiveMemory(MemoryScope(snapshot.organization_id, snapshot.workspace_id, 999), 1, token)),
    )
    for token_actor, token_request in mismatches:
        current = token_request if token_request.continuation else replace(
            token_request, continuation=token,
        )
        assert service.list_active(token_actor, current).outcome == "invalid_request"

    padded = token + "=" * (-len(token) % 4)
    raw = base64.urlsafe_b64decode(padded)
    aad = b"organizational-memory-continuation.v1"
    payload = json.loads(AESGCM(service._token_key()).decrypt(raw[:12], raw[12:], aad))
    payload["v"] = 2
    changed = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    versioned = base64.urlsafe_b64encode(
        raw[:12] + AESGCM(service._token_key()).encrypt(raw[:12], changed, aad)
    ).decode().rstrip("=")
    assert service.list_active(actor, replace(
        request, continuation=versioned,
    )).outcome == "invalid_request"


def test_ten_denied_rounds_terminate_deterministically_at_last_evaluated():
    service, uow, _, snapshot, items = _populate(12)
    actor = MemoryActor(9, snapshot.organization_id)
    rounds = 0; original_list = uow.memories.list_active
    def counted(criteria):
        nonlocal rounds; rounds += 1
        return original_list(replace(criteria, candidate_limit=1))
    uow.memories.list_active = counted
    original_authorize = uow.authorization.require
    def deny_candidates(request, source_owner_id=None):
        if request.memory_id is not None:
            from app.repositories.organizational_memory_unit_of_work import MemoryAuthorizationDenied
            raise MemoryAuthorizationDenied()
        return original_authorize(request, source_owner_id)
    uow.authorization.require = deny_candidates
    page = service.list_active(actor, ListActiveMemory(
        MemoryScope(snapshot.organization_id, snapshot.workspace_id, snapshot.project_id),
        1,
    )).page
    assert rounds == 10 and page.items == () and page.visible_total == 0
    assert page.next_continuation is not None
    decoded = service._decode_continuation(actor, ListActiveMemory(
        MemoryScope(snapshot.organization_id, snapshot.workspace_id, snapshot.project_id),
        1, page.next_continuation,
    ))
    ordered = sorted(items, key=lambda item: (-item.admitted_at.timestamp(), str(item.id)))
    assert decoded.memory_id == ordered[9].id
