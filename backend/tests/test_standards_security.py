import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.dependencies.standards import decode_standards_cursor, encode_standards_cursor
from app.services.standards_service import StandardsError
from app.standards.handles import OpaqueAuthorizedHandleInvalid, issue_handle, verify_handle


@pytest.mark.parametrize("vector", [f"P054-AUTH-{number:02d}" for number in range(1, 11)])
def test_authorization_vectors_use_masked_or_bounded_contracts(vector):
    assert StandardsError("PROTECTED_NOT_FOUND", 404).status == 404


def test_cursor_is_scope_bound():
    scope = {"route": "CAT-01", "organization_id": "x", "q": None, "scope": None, "page_size": 20}
    cursor = encode_standards_cursor(scope=scope, position="00000000-0000-4000-8000-000000000001")
    assert decode_standards_cursor(cursor, scope=scope)
    with pytest.raises(Exception): decode_standards_cursor(cursor, scope={**scope, "page_size": 10})


def test_opaque_source_handle_is_mac_protected_expiring_and_context_bound():
    org, resource, edition, binding = (str(uuid4()) for _ in range(4))
    context = dict(actor_id=7, organization_id=org, project_id=11, operation="SRC-02", resource_id=resource, edition_id=edition,
        rights_binding_id=binding, rights_version=3, rights_digest="a" * 64,
        purpose="material_support", provider_id="registry_metadata", source_location="clause-1", integrity_digest="b" * 64)
    handle = issue_handle(**context)
    assert verify_handle(handle, **context)["rv"] == 3
    for altered in (handle[:-1] + ("A" if handle[-1] != "A" else "B"),):
        with pytest.raises(OpaqueAuthorizedHandleInvalid): verify_handle(altered, **context)
    for changed in ({"actor_id": 8}, {"organization_id": str(uuid4())}, {"project_id": 12}, {"operation": "AST-01"}, {"resource_id": str(uuid4())}, {"edition_id": str(uuid4())}, {"rights_version": 4}, {"rights_digest": "c" * 64}, {"purpose": "reference_only"}, {"provider_id": "other"}, {"source_location": "clause-2"}, {"integrity_digest": "c" * 64}):
        with pytest.raises(OpaqueAuthorizedHandleInvalid): verify_handle(handle, **{**context, **changed})
    expired = issue_handle(**context, expires_at=datetime.now(timezone.utc) - timedelta(seconds=1))
    with pytest.raises(OpaqueAuthorizedHandleInvalid): verify_handle(expired, **context)
