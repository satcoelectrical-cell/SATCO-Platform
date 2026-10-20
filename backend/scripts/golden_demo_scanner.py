"""Loopback-only structural PDF scanner for the Golden Engineering Demo.

This is deliberately a test boundary, not a production anti-malware engine.  It
retrieves the exact version from the isolated S3-compatible store, verifies the
declared SHA-256 digest, and requires pdfplumber to parse at least one PDF page.
Only then does it return a ``clean`` scanner disposition.
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import hmac
import ipaddress
import os
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import boto3
import pdfplumber
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field


MAX_FILE_BYTES = 25 * 1024 * 1024
ENGINE_ID = "satco-golden-demo-structural-pdf-scanner"
SIGNATURE_SET_ID = "test-boundary-v1-no-malware-signatures"


def _secret(path_name: str) -> str:
    path = os.environ.get(path_name, "")
    if not path:
        raise RuntimeError(f"{path_name} is required")
    value = Path(path).read_text(encoding="utf-8").strip()
    if len(value) < 32:
        raise RuntimeError(f"{path_name} is invalid")
    return value


def _loopback_https_endpoint() -> str:
    endpoint = os.environ.get("GOLDEN_DEMO_OBJECT_ENDPOINT", "")
    parsed = urlparse(endpoint)
    try:
        host = ipaddress.ip_address(parsed.hostname or "")
    except ValueError as exc:
        raise RuntimeError("object endpoint must use a literal loopback address") from exc
    if parsed.scheme != "https" or not host.is_loopback or parsed.port is None:
        raise RuntimeError("object endpoint must be HTTPS on loopback")
    return endpoint


SCANNER_TOKEN = _secret("GOLDEN_DEMO_SCANNER_TOKEN_FILE")
OBJECT_ENDPOINT = _loopback_https_endpoint()
OBJECT_BUCKET = os.environ.get("GOLDEN_DEMO_OBJECT_BUCKET", "")
OBJECT_REGION = os.environ.get("GOLDEN_DEMO_OBJECT_REGION", "")
OBJECT_CA_FILE = os.environ.get("AWS_CA_BUNDLE", "")
if not OBJECT_BUCKET or not OBJECT_REGION or not OBJECT_CA_FILE:
    raise RuntimeError("isolated object-store configuration is incomplete")


class ScanRequest(BaseModel):
    key: str = Field(min_length=1, max_length=1024)
    version: str = Field(min_length=1, max_length=1024)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


app = FastAPI(title="SATCO Golden Demo Test Scanner", docs_url=None, redoc_url=None)


def _authorized(authorization: str | None) -> None:
    prefix = "Bearer "
    supplied = authorization[len(prefix) :] if authorization and authorization.startswith(prefix) else ""
    if not supplied or not hmac.compare_digest(supplied, SCANNER_TOKEN):
        raise HTTPException(status_code=401, detail="unauthorized")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "boundary": "structural-pdf-test-scanner"}


@app.post("/scan")
def scan(
    request: ScanRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict[str, str]:
    _authorized(authorization)
    client = boto3.client(
        "s3",
        endpoint_url=OBJECT_ENDPOINT,
        region_name=OBJECT_REGION,
        aws_access_key_id=_secret("GOLDEN_DEMO_OBJECT_ACCESS_KEY_FILE"),
        aws_secret_access_key=_secret("GOLDEN_DEMO_OBJECT_SECRET_KEY_FILE"),
    )
    try:
        response = client.get_object(
            Bucket=OBJECT_BUCKET,
            Key=request.key,
            VersionId=request.version,
        )
        payload = response["Body"].read(MAX_FILE_BYTES + 1)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="exact object unavailable") from exc

    disposition = "indeterminate"
    if len(payload) <= MAX_FILE_BYTES and sha256(payload).hexdigest() == request.sha256:
        try:
            with pdfplumber.open(BytesIO(payload)) as document:
                structurally_valid = len(document.pages) > 0
                if structurally_valid:
                    document.pages[0].extract_text(x_tolerance=3, y_tolerance=3)
            disposition = "clean" if structurally_valid else "unsafe"
        except Exception:
            disposition = "unsafe"

    return {
        "disposition": disposition,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "engine_id": ENGINE_ID,
        "signature_set_id": SIGNATURE_SET_ID,
        "correlation_id": str(uuid4()),
    }
