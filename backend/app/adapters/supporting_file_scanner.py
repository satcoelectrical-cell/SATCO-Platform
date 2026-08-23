"""Scanner boundary: machine safety authority only, never engineering authority."""
from datetime import datetime
import hmac
from uuid import UUID

from app.enums.supporting_file import SupportingFileScanDisposition
from app.exceptions.supporting_file import SupportingFileScannerUnavailable
from app.ports.supporting_file import SupportingFileScanResult, SupportingFileScanner, SupportingFileScannerPrincipal

SCANNER_PRINCIPAL_ID = "supporting-file-scanner-v1"


class SupportingFileScannerCredentialVerifier:
    """Resolve one rotatable server-side secret into the least-privilege principal."""

    def __init__(self, secret: str):
        if len(secret) < 32:
            raise ValueError("scanner credential is unavailable")
        self._secret = secret

    def authenticate(self, supplied: str | None) -> SupportingFileScannerPrincipal:
        if not supplied or not hmac.compare_digest(
            supplied.encode("utf-8"), self._secret.encode("utf-8")
        ):
            raise SupportingFileScannerUnavailable()
        return SupportingFileScannerPrincipal(SCANNER_PRINCIPAL_ID)


class CallbackSupportingFileScanner(SupportingFileScanner):
    """Production composition supplies a separately authenticated exact-object callback."""
    def __init__(self, callback): self._callback = callback
    def scan_exact(self, *, key: str, version: str, sha256: str) -> SupportingFileScanResult:
        result = self._callback(key=key, version=version, sha256=sha256)
        if not isinstance(result, dict) or result.get("disposition") not in {
            item.value for item in SupportingFileScanDisposition
        }:
            raise SupportingFileScannerUnavailable()
        try:
            observed_at = result["observed_at"]
            engine_id = result["engine_id"]
            signature_set_id = result["signature_set_id"]
            correlation_id = UUID(str(result["correlation_id"]))
            if (
                not isinstance(observed_at, datetime)
                or observed_at.tzinfo is None
                or not isinstance(engine_id, str)
                or not 1 <= len(engine_id) <= 128
                or not isinstance(signature_set_id, str)
                or not 1 <= len(signature_set_id) <= 128
                or correlation_id.int == 0
            ):
                raise ValueError
        except (KeyError, TypeError, ValueError):
            raise SupportingFileScannerUnavailable() from None
        return SupportingFileScanResult(
            result["disposition"], observed_at, engine_id,
            signature_set_id, correlation_id,
        )
