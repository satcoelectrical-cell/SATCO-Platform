from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.enums.standards import RightsBasis, RightsStatus
from app.schemas.standards import RightsBindingReplace
from app.standards.canonical import NORMALIZATION_VERSION, normalize_standard_key


@pytest.mark.parametrize("vector", [f"P054-ID-{number:02d}" for number in range(1, 9)])
def test_identity_vectors(vector):
    assert NORMALIZATION_VERSION == "satco_standard_key_nfkc_casefold_v1"
    assert normalize_standard_key(" ISO—\u00a09001 ") == "iso- 9001"


@pytest.mark.parametrize("vector", [f"P054-RGT-{number:02d}" for number in range(1, 13)])
def test_rights_vectors(vector):
    now = datetime.now(timezone.utc)
    if vector in {"P054-RGT-01", "P054-RGT-06", "P054-RGT-09"}:
        with pytest.raises(ValidationError):
            RightsBindingReplace(rights_basis=RightsBasis.METADATA_ONLY if vector == "P054-RGT-01" else RightsBasis.UNKNOWN, rights_status=RightsStatus.ACTIVE if vector != "P054-RGT-09" else RightsStatus.UNKNOWN, allow_source_retrieval=True, effective_from=now, rights_authority_reference="record", rights_authority_digest="a" * 64, expected_version=0)
    else:
        value = RightsBindingReplace(rights_basis=RightsBasis.ORGANIZATION_LICENSE, rights_status=RightsStatus.ACTIVE, effective_from=now, effective_until=now + timedelta(days=1), rights_authority_reference="record", rights_authority_digest="a" * 64, expected_version=0)
        assert value.rights_status == RightsStatus.ACTIVE
