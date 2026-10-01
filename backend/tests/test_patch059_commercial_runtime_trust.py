import base64
import json

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.commercial_entitlements.runtime import runtime_trust_store
from app.core.config import settings
from app.core.operations import ProductionConfigurationError


def _b64u(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _trust_document() -> dict:
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    return {
        "schema": "satco.commercial-entitlement-trust/v1",
        "keys": [
            {
                "key_id": "commercial-test-a",
                "algorithm": "Ed25519",
                "public_key_base64url": _b64u(public),
                "not_before": "2026-09-01T00:00:00Z",
                "revoked_at": None,
            }
        ],
    }


def test_runtime_trust_store_loads_public_verification_material(tmp_path, monkeypatch):
    path = tmp_path / "commercial-trust.json"
    path.write_text(json.dumps(_trust_document()), encoding="utf-8")
    monkeypatch.setattr(settings, "SATCO_COMMERCIAL_ENTITLEMENT_TRUST_STORE_FILE", str(path))

    store = runtime_trust_store()

    assert store.keys[0].algorithm == "Ed25519"
    assert store.keys[0].key_id == "commercial-test-a"


def test_runtime_trust_store_fails_closed_when_path_missing(monkeypatch):
    monkeypatch.setattr(settings, "SATCO_COMMERCIAL_ENTITLEMENT_TRUST_STORE_FILE", "")

    with pytest.raises(ProductionConfigurationError):
        runtime_trust_store()


def test_runtime_trust_store_fails_closed_when_file_invalid(tmp_path, monkeypatch):
    path = tmp_path / "commercial-trust.json"
    path.write_text('{"schema":"satco.commercial-entitlement-trust/v1","keys":[]}', encoding="utf-8")
    monkeypatch.setattr(settings, "SATCO_COMMERCIAL_ENTITLEMENT_TRUST_STORE_FILE", str(path))

    with pytest.raises(ProductionConfigurationError):
        runtime_trust_store()
