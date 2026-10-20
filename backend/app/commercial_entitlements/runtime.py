"""Runtime verification dependencies for PATCH-059 commercial entitlements."""

from __future__ import annotations

from app.commercial_entitlements.crypto import TrustStore, load_trust_store
from app.core.config import settings
from app.core.operations import ProductionConfigurationError


def runtime_trust_store() -> TrustStore:
    path = settings.SATCO_COMMERCIAL_ENTITLEMENT_TRUST_STORE_FILE.strip()
    if not path:
        raise ProductionConfigurationError("commercial_trust_store")
    try:
        return load_trust_store(path)
    except (OSError, UnicodeError, ValueError) as exc:
        raise ProductionConfigurationError("commercial_trust_store") from exc
