import base64, json
from datetime import datetime, timedelta, timezone
from uuid import UUID
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from pydantic import ValidationError
from app.commercial_entitlements.canonical import EntitlementPayload, canonical_payload_bytes, parse_envelope
from app.commercial_entitlements.crypto import TrustKey, TrustStore, verify_envelope

NOW=datetime(2026,9,30,6,0,tzinfo=timezone.utc)
ORG="11111111-1111-4111-8111-111111111111"
ENT="22222222-2222-4222-8222-222222222222"

def b64u(value:bytes)->str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")

def payload(**overrides):
    data=dict(schema_version=1,entitlement_id=UUID(ENT),revision=1,organization_id=UUID(ORG),
        deployment_id="satco-prod-1",issuer="SATCO",issued_at=NOW,not_before=NOW,
        valid_until=NOW+timedelta(days=30),grace_until=NOW+timedelta(days=60),
        package_keys=("electrical","instrumentation"),seat_capacity=5,support_until=None,
        baseline_release_sequence=1,max_release_sequence=3)
    data.update(overrides); return EntitlementPayload(**data)

def signed():
    private=Ed25519PrivateKey.generate()
    public=private.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    p=payload(); sig=private.sign(canonical_payload_bytes(p))
    raw=json.dumps({"schema":"satco.commercial-entitlement/v1","key_id":"commercial-2026-a",
        "payload":json.loads(canonical_payload_bytes(p)),"signature":b64u(sig)},separators=(",",":")).encode()
    store=TrustStore(schema="satco.commercial-entitlement-trust/v1",keys=(TrustKey(
        key_id="commercial-2026-a",algorithm="Ed25519",public_key_base64url=b64u(public),
        not_before=NOW-timedelta(days=1),revoked_at=None),))
    return raw,store

def test_canonical_payload_is_stable_and_sorted():
    a=canonical_payload_bytes(payload())
    b=canonical_payload_bytes(payload())
    assert a==b
    assert a.startswith(b'{"baseline_release_sequence":1,"deployment_id":"satco-prod-1"')
    assert b'"package_keys":["electrical","instrumentation"]' in a

def test_valid_signature_verifies():
    raw,store=signed(); env=parse_envelope(raw)
    verify_envelope(env,store,now=NOW+timedelta(days=2))

def test_signature_mutation_is_rejected():
    raw,store=signed(); obj=json.loads(raw); obj["payload"]["seat_capacity"]=6
    env=parse_envelope(json.dumps(obj,separators=(",",":")).encode())
    with pytest.raises(ValueError,match="invalid signature"): verify_envelope(env,store,now=NOW+timedelta(days=2))

def test_duplicate_envelope_member_is_rejected():
    raw=b'{"schema":"satco.commercial-entitlement/v1","schema":"satco.commercial-entitlement/v1","key_id":"x","payload":{},"signature":"x"}'
    with pytest.raises(ValueError,match="duplicate JSON member"): parse_envelope(raw)

def test_unknown_payload_field_is_rejected():
    raw,_=signed(); obj=json.loads(raw); obj["payload"]["unknown"]=1
    with pytest.raises(ValidationError): parse_envelope(json.dumps(obj).encode())

def test_grace_over_30_days_is_rejected():
    with pytest.raises(ValidationError): payload(grace_until=NOW+timedelta(days=61))

def test_revoked_key_is_rejected():
    raw,store=signed(); key=store.keys[0]
    revoked=TrustStore(schema=store.schema_id,keys=(key.model_copy(update={"revoked_at":NOW+timedelta(hours=1)}),))
    with pytest.raises(ValueError,match="key revoked"): verify_envelope(parse_envelope(raw),revoked,now=NOW+timedelta(days=2))

def test_unknown_key_is_rejected():
    raw,store=signed(); obj=json.loads(raw); obj["key_id"]="missing"
    with pytest.raises(ValueError,match="untrusted key"): verify_envelope(parse_envelope(json.dumps(obj).encode()),store,now=NOW)

def test_unsorted_package_array_is_rejected():
    with pytest.raises(ValidationError,match="canonical sorted order"):
        payload(package_keys=("instrumentation","electrical"))

def test_noncanonical_wire_timestamp_is_rejected_before_signature_check():
    raw,_=signed(); obj=json.loads(raw); obj["payload"]["issued_at"]="2026-09-30T06:00:00+00:00"
    with pytest.raises(ValueError,match="canonical UTC-second format"):
        parse_envelope(json.dumps(obj).encode())

def test_integer_above_i_json_safe_range_is_rejected():
    with pytest.raises(ValidationError):
        payload(revision=9007199254740992)
