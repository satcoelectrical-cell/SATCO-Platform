from datetime import datetime, timezone
from uuid import uuid4
import pytest
from app.enums.supporting_file import SupportingFileMediaType
from app.exceptions.supporting_file import SupportingFileValidationError
from app.models.supporting_file_command import SupportingFileHistoricalBasisV1, canonical_digest, opaque_storage_key, safe_filename
from app.ports.supporting_file import RecordSupportingFileScan, SupportingFileScannerPrincipal
from dataclasses import fields


def test_opaque_key_and_filename_contracts_are_closed():
    assert opaque_storage_key("objects/" + "a" * 64).startswith("objects/")
    assert safe_filename("../field-note.pdf")[0] == "field-note.pdf"
    with pytest.raises(SupportingFileValidationError): opaque_storage_key("available/customer/1")
    with pytest.raises(SupportingFileValidationError): safe_filename("../../")


def test_historical_basis_digest_is_deterministic_and_closed():
    item = SupportingFileHistoricalBasisV1(1, "supporting_file", uuid4(), 1, uuid4(), 3, None, "basis.pdf", SupportingFileMediaType.PDF, 1, "sha256", "a" * 64, 4, datetime.now(timezone.utc), None)
    assert canonical_digest(item) == canonical_digest(item)


def test_authenticated_scan_result_contract_is_exact_and_scanner_only():
    assert [field.name for field in fields(SupportingFileScannerPrincipal)] == ["principal_id"]
    assert [field.name for field in fields(RecordSupportingFileScan)] == [
        "principal", "asset_id", "asset_version", "attempt_id",
        "object_fingerprint", "disposition", "engine_id",
        "signature_set_id", "observed_at", "correlation_id",
    ]
