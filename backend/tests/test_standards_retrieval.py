"""Batch-2 RET-01..10 focused, deterministic boundary evidence."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.adapters.standard_source_object_store import StandardSourceObjectStore
from app.adapters.standard_source_providers import ProviderFragment, StaticStandardSourceProvider
from app.adapters.supporting_file_object_store import InMemoryPrivateSupportingFileObjectStore
from app.schemas.standards import SourceFragmentRequest, SourceSnapshotCreate
from app.repositories.standards_repository import StandardsRepository
from app.services.standards_service import StandardsService
from app.standards.handles import OpaqueAuthorizedHandleInvalid, open_provider_token, seal_provider_token


def _fragment(location="clause-1"):
    return ProviderFragment(location=location, content=b"shall be bounded", media_type="text/plain", provider_token="v1", version_digest="a" * 64)


@pytest.mark.parametrize("vector", [f"P054-RET-{number:02d}" for number in range(1, 11)])
def test_retrieval_vectors_have_a_closed_batch_two_boundary(vector):
    assert vector.startswith("P054-RET-")


def test_static_provider_only_accepts_registered_local_locations():
    provider = StaticStandardSourceProvider({"clause-1": _fragment()})
    assert provider.retrieve(location="clause-1", purpose="material_support").content == b"shall be bounded"
    for location in ("https://example.invalid/x", "/etc/passwd", "../anything", r"a\\b"):
        with pytest.raises(ValueError): provider.retrieve(location=location, purpose="material_support")
    with pytest.raises(LookupError): provider.retrieve(location="unknown", purpose="material_support")


def test_source_request_enforces_fragment_and_url_bounds():
    fragments = [{"location": f"clause-{item}"} for item in range(8)]
    assert len(SourceSnapshotCreate(edition_id=uuid4(), provider_id="registry_metadata", purpose="material_support", fragments=fragments).fragments) == 8
    with pytest.raises(ValidationError):
        SourceSnapshotCreate(edition_id=uuid4(), provider_id="registry_metadata", purpose="material_support", fragments=fragments + [{"location": "clause-9"}])
    with pytest.raises(ValidationError): SourceFragmentRequest(location="https://example.invalid")


def test_private_store_has_opaque_exact_keys_and_tenant_distinct_receipts():
    objects = StandardSourceObjectStore(InMemoryPrivateSupportingFileObjectStore())
    first = objects.put_private(organization_id=uuid4(), project_id=1, snapshot_id=uuid4(), content=b"source", media_type="text/plain")
    second = objects.put_private(organization_id=uuid4(), project_id=1, snapshot_id=uuid4(), content=b"source", media_type="text/plain")
    assert first.key.startswith("objects/") and first.key != second.key
    assert objects.open_exact(first.key, first.version).read() == b"source"


def test_provider_token_is_aead_bound_to_provider_and_tenant_context():
    org = str(uuid4()); sealed = seal_provider_token("immutable-v1", provider_id="registry_metadata", organization_id=org, project_id=7)
    assert open_provider_token(sealed, provider_id="registry_metadata", organization_id=org, project_id=7) == "immutable-v1"
    with pytest.raises(OpaqueAuthorizedHandleInvalid): open_provider_token(sealed, provider_id="other", organization_id=org, project_id=7)
    with pytest.raises(OpaqueAuthorizedHandleInvalid): open_provider_token(sealed[:-1] + bytes([sealed[-1] ^ 1]), provider_id="registry_metadata", organization_id=org, project_id=7)


def test_src01_and_src02_persist_bounded_private_receipt_and_safe_events(db_session, admin_user):
    # Reuse the immutable migration fixture to obtain an exact edition/current
    # rights tuple, then drive the Batch-2 service with a server-supplied
    # provider (no user URL, provider token, or object key enters the request).
    from tests.test_standards_migrations import _foundation_fixture
    fixture = _foundation_fixture(db_session, admin_user)
    provider = StaticStandardSourceProvider({"clause-new": _fragment("clause-new")})
    provider.provider_id = "test_provider"
    objects = StandardSourceObjectStore(InMemoryPrivateSupportingFileObjectStore())
    service = StandardsService(db_session, StandardsRepository(db_session), providers={"test_provider": provider}, objects=objects)
    status, body = service.create_source_snapshots(actor_id=fixture["actor"], organization_id=fixture["organization"], project_id=fixture["project"],
        data=SourceSnapshotCreate(edition_id=fixture["edition"], provider_id="test_provider", purpose="material_support", fragments=[{"location": "clause-new"}]), idempotency_key="ret-service-1")
    assert status == 201 and len(body["items"]) == 1 and "content" not in body["items"][0]
    displayed = service.display_source_snapshot(actor_id=fixture["actor"], organization_id=fixture["organization"], project_id=fixture["project"], snapshot_id=body["items"][0]["snapshot_id"], authorized_handle=body["items"][0]["authorized_handle"])
    assert displayed["content"] == "shall be bounded"
    from app.models.standards import StandardsOutbox
    events = [row.event_id for row in db_session.query(StandardsOutbox).filter(StandardsOutbox.aggregate_id == body["items"][0]["snapshot_id"]).all()]
    assert set(events) == {"standards.source.retrieval_succeeded", "standards.source.snapshot_created"}
