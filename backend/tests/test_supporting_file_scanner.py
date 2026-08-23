from app.adapters.supporting_file_scanner import CallbackSupportingFileScanner
from app.exceptions.supporting_file import SupportingFileScannerUnavailable
from app.adapters.supporting_file_scanner import SupportingFileScannerCredentialVerifier
from datetime import datetime, timezone
from uuid import uuid4
import pytest

def test_scanner_accepts_only_closed_safety_dispositions():
    valid = lambda **_: {"disposition": "clean", "engine_id": "engine-a", "signature_set_id": "sig-1", "observed_at": datetime.now(timezone.utc), "correlation_id": uuid4()}
    assert CallbackSupportingFileScanner(valid).scan_exact(key="objects/" + "a" * 64, version="v", sha256="a" * 64).disposition == "clean"
    with pytest.raises(SupportingFileScannerUnavailable):
        CallbackSupportingFileScanner(lambda **_: {**valid(), "disposition": "approved"}).scan_exact(key="objects/" + "a" * 64, version="v", sha256="a" * 64)


def test_scanner_provider_identity_is_required_and_credential_is_constant_time_verified():
    with pytest.raises(SupportingFileScannerUnavailable):
        CallbackSupportingFileScanner(lambda **_: {"disposition": "clean"}).scan_exact(key="objects/" + "a" * 64, version="v", sha256="a" * 64)
    verifier = SupportingFileScannerCredentialVerifier("s" * 32)
    assert verifier.authenticate("s" * 32).principal_id == "supporting-file-scanner-v1"
    for supplied in (None, "", "wrong"):
        with pytest.raises(SupportingFileScannerUnavailable):
            verifier.authenticate(supplied)
    with pytest.raises(ValueError):
        SupportingFileScannerCredentialVerifier("weak")
    rotated = SupportingFileScannerCredentialVerifier("r" * 32)
    with pytest.raises(SupportingFileScannerUnavailable):
        rotated.authenticate("s" * 32)
