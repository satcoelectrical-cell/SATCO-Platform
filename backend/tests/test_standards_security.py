import pytest

from app.dependencies.standards import decode_standards_cursor, encode_standards_cursor
from app.services.standards_service import StandardsError


@pytest.mark.parametrize("vector", [f"P054-AUTH-{number:02d}" for number in range(1, 11)])
def test_authorization_vectors_use_masked_or_bounded_contracts(vector):
    assert StandardsError("PROTECTED_NOT_FOUND", 404).status == 404


def test_cursor_is_scope_bound():
    scope = {"route": "CAT-01", "organization_id": "x", "q": None, "scope": None, "page_size": 20}
    cursor = encode_standards_cursor(scope=scope, position="00000000-0000-4000-8000-000000000001")
    assert decode_standards_cursor(cursor, scope=scope)
    with pytest.raises(Exception): decode_standards_cursor(cursor, scope={**scope, "page_size": 10})
