"""Focused PATCH-043 thin transport and protected-disclosure evidence."""

from datetime import datetime, timezone
from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.dependencies.supporting_file import (
    SupportingFileApplication, SupportingFileScannerApplication,
    get_supporting_file_application, get_supporting_file_scanner_application,
)
from app.exceptions.supporting_file import SupportingFileProtectedNotFound
from app.main import app
from app.api.v1.routers.technical_reports import TechnicalReportApplication, get_technical_report_application
from app.enums import EvidenceLifecycle, EvidenceSourceKind, EvidenceSourceStanding
from app.models.supporting_file_command import SupportingFileHistoricalBasisV1
from app.models.technical_report_command import EvidenceHistoricalBasisV2, TechnicalReportActor
from app.ports.supporting_file import SupportingFileScannerPrincipal


NOW = datetime(2026, 8, 23, tzinfo=timezone.utc)
ORG = uuid4()


def _asset(**changes):
    values = dict(
        id=uuid4(), organization_id=ORG, project_id=11, workspace_id=12,
        safe_filename="calculation.pdf", safe_ascii_filename="calculation.pdf",
        media_type="application/pdf", byte_size=16, digest_algorithm="sha256",
        content_digest="a" * 64, lifecycle="available", version=2,
        uploader_id=7, uploaded_at=NOW, scanned_at=NOW,
        predecessor_asset_id=None, storage_key="protected", object_version="v1",
    )
    values.update(changes)
    return SimpleNamespace(**values)


class RecordingService:
    def __init__(self):
        self.asset = _asset(); self.calls = []

    def reserve_upload(self, **values):
        self.calls.append(("reserve", values)); return SimpleNamespace(id=uuid4())

    def finalize_upload(self, **values):
        self.calls.append(("finalize", values)); return self.asset

    def list_metadata(self, **values):
        self.calls.append(("list", values)); return (self.asset,), "opaque-token"

    def get_metadata(self, **values):
        self.calls.append(("get", values)); return self.asset

    def open_active(self, **values):
        self.calls.append(("download", values)); return self.asset, BytesIO(b"%PDF-1.7\nbody!!")

    def open_historical(self, **values):
        self.calls.append(("historical", values)); return self.asset, BytesIO(b"%PDF-1.7\nhist!!")

    def withdraw(self, **values):
        self.calls.append(("withdraw", values)); return _asset(lifecycle="withdrawn", version=3)

    def record_scan_result(self, value):
        self.calls.append(("scan", value)); return self.asset


@pytest.fixture
def supporting_app(client):
    service = RecordingService()
    app.dependency_overrides[get_supporting_file_application] = lambda: SupportingFileApplication(service, 7, ORG)
    app.dependency_overrides[get_supporting_file_scanner_application] = lambda: SupportingFileScannerApplication(service, SupportingFileScannerPrincipal("supporting-file-scanner-v1"))
    try:
        yield client, service
    finally:
        app.dependency_overrides.pop(get_supporting_file_application, None)
        app.dependency_overrides.pop(get_supporting_file_scanner_application, None)


def test_upload_list_status_withdraw_are_one_to_one_and_server_scoped(supporting_app):
    client, service = supporting_app
    uploaded = client.post(
        "/supporting-files/uploads",
        files={"file": ("calculation.pdf", b"%PDF-1.7\nbody", "application/pdf")},
        data={"project_id": "11", "workspace_id": "12", "rationale": "Human evidence"},
        headers={"Idempotency-Key": str(uuid4()), "X-Correlation-ID": str(uuid4())},
    )
    assert uploaded.status_code == 201
    assert uploaded.json()["organization_id"] == str(ORG)
    finalized = next(value for name, value in service.calls if name == "finalize")
    assert finalized["scope"].organization_id == ORG and finalized["actor_id"] == 7

    listed = client.get("/projects/11/supporting-files?workspace_id=12&limit=20")
    assert listed.status_code == 200
    assert listed.json()["visible_count"] == 1
    assert listed.json()["continuation"] == "opaque-token"
    assert "total" not in listed.json()
    assert client.get(f"/supporting-files/{service.asset.id}?project_id=11&workspace_id=12").status_code == 200
    withdrawn = client.post(
        f"/supporting-files/{service.asset.id}/withdrawals?project_id=11&workspace_id=12",
        json={"expected_version": 2, "rationale": "Human withdrawal"},
        headers={"Idempotency-Key": str(uuid4()), "X-Correlation-ID": str(uuid4())},
    )
    assert withdrawn.status_code == 200 and withdrawn.json()["lifecycle"] == "withdrawn"


def test_download_is_attachment_nosniff_private_and_never_exposes_key(supporting_app):
    client, service = supporting_app
    response = client.get(
        f"/supporting-files/{service.asset.id}/download?project_id=11&workspace_id=12"
    )
    assert response.status_code == 200 and response.content.startswith(b"%PDF")
    assert response.headers["content-disposition"].startswith("attachment;")
    assert response.headers["content-length"] == str(service.asset.byte_size)
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "private, no-store"
    assert b"protected" not in response.content


def test_protected_failure_is_discriminator_only(supporting_app):
    client, service = supporting_app
    service.get_metadata = lambda **_: (_ for _ in ()).throw(SupportingFileProtectedNotFound())
    response = client.get(f"/supporting-files/{uuid4()}?project_id=11&workspace_id=12")
    assert response.status_code == 404
    assert response.json() == {"outcome": "protected_not_found"}


def test_internal_scanner_route_is_hidden_and_typed(supporting_app):
    client, service = supporting_app
    response = client.post("/internal/supporting-files/scan-results", json={
        "asset_id": str(service.asset.id), "asset_version": 1,
        "attempt_id": str(uuid4()), "object_fingerprint": "a" * 64,
        "disposition": "clean", "engine_id": "engine",
        "signature_set_id": "signatures", "observed_at": NOW.isoformat(),
        "correlation_id": str(uuid4()),
    })
    assert response.status_code == 200 and response.json()["outcome"] == "accepted"
    assert "/internal/supporting-files/scan-results" not in client.get("/openapi.json").json()["paths"]


def test_historical_download_uses_server_composed_accepted_basis(supporting_app):
    client, service = supporting_app
    basis = SupportingFileHistoricalBasisV1(
        1, "supporting_file", service.asset.id, service.asset.version, ORG,
        11, 12, service.asset.safe_filename, service.asset.media_type,
        service.asset.byte_size, "sha256", service.asset.content_digest, 7, NOW, None,
    )
    evidence_id = uuid4()
    locator = EvidenceHistoricalBasisV2(
        2, "evidence", evidence_id, 3, ORG, 11, 12,
        EvidenceLifecycle.CURRENT, EvidenceSourceKind.ENGINEERING_RECORD,
        "record", "r1", EvidenceSourceStanding.CURRENT, NOW,
        "supported fact", 7, (basis,),
    )
    report = SimpleNamespace(accepted_snapshot=SimpleNamespace(
        project_id=11, workspace_id=12,
        provenance=(SimpleNamespace(locator=locator),),
    ))
    report_service = SimpleNamespace(get_report=lambda *_: report)
    app.dependency_overrides[get_technical_report_application] = lambda: TechnicalReportApplication(
        report_service, TechnicalReportActor(7, ORG)
    )
    try:
        response = client.get(
            f"/technical-reports/{uuid4()}/evidence/{evidence_id}/supporting-files/{service.asset.id}/download"
        )
    finally:
        app.dependency_overrides.pop(get_technical_report_application, None)
    assert response.status_code == 200 and response.content.endswith(b"hist!!")
    call = next(values for name, values in service.calls if name == "historical")
    assert call["basis"] == basis and call["scope"].organization_id == ORG


def test_no_deferred_or_direct_object_routes_exist(supporting_app):
    client, _ = supporting_app
    paths = client.get("/openapi.json").json()["paths"]
    assert "/supporting-files/uploads" in paths
    assert not any("search" in path or "ocr" in path or path.startswith("/objects") for path in paths if "supporting" in path or path.startswith("/objects"))
