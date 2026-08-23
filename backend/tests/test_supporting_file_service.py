from datetime import datetime, timedelta, timezone
from hashlib import sha256
from io import BytesIO
from uuid import uuid4

import pytest

from app.adapters.supporting_file_object_store import InMemoryPrivateSupportingFileObjectStore
from app.enums.supporting_file import SupportingFileMediaType
from app.exceptions.supporting_file import SupportingFileIntegrityError, SupportingFileProtectedNotFound, SupportingFileScannerUnavailable
from app.models.supporting_file_command import SupportingFileScope
from app.ports.supporting_file import SupportingFileScanResult
from app.services.supporting_file_service import SupportingFileService

PDF_BYTES=b"%PDF-1.7\ncanonical-test"


class Repo:
    def __init__(self): self.assets={}; self.reservations={}; self.scan_attempts=[]; self.idempotency={}
    def add_reservation(self, value): self.reservations[value.id]=value
    def get_reservation(self, key, organization_id):
        value=self.reservations.get(key); return value if value and value.organization_id == organization_id else None
    def add(self, value): self.assets[value.id]=value
    def bind_reservation_asset(self, reservation, asset, status): reservation.asset_id=asset.id; reservation.status=status
    def get_scoped(self, key, organization_id):
        value=self.assets.get(key); return value if value and value.organization_id == organization_id else None
    def get_idempotency(self, *, organization_id, actor_id, operation, idempotency_id):
        return self.idempotency.get((organization_id, actor_id, operation, idempotency_id))
    def stage_idempotency(self, value):
        self.idempotency[(value.organization_id, value.actor_id, value.operation, value.idempotency_id)] = value
    def persist_expected_version(self, asset, expected): return expected + 1 == asset.version
    def next_scan_attempt_number(self, *, asset_id):
        return 1 + sum(item.asset_id == asset_id for item in self.scan_attempts)
    def stage_scan_attempt(self, record): self.scan_attempts.append(record)
    def get_scan_attempt(self, *, attempt_id, for_update=False): return next((item for item in self.scan_attempts if item.id == attempt_id), None)
    def get_latest_scan_attempt(self, *, asset_id, for_update=False):
        values=[item for item in self.scan_attempts if item.asset_id == asset_id]; return max(values, key=lambda item: item.attempt_number) if values else None
    def complete_scan_attempt(self, record, *, disposition, completed_at, failed=False, engine_id=None, signature_set_id=None, correlation_id=None):
        record.state = "failed" if failed else "completed"; record.disposition = disposition; record.completed_at = completed_at; record.engine_id=engine_id; record.signature_set_id=signature_set_id; record.correlation_id=correlation_id
    def stage_outbox(self, record): return None
    def stage_audit(self, **kwargs): return None
    def list_candidates(self, *, organization_id, project_id, workspace_id, lifecycle, anchor, limit):
        values=[item for item in self.assets.values() if item.organization_id == organization_id and item.project_id == project_id and (workspace_id is None or item.workspace_id in {None, workspace_id}) and (lifecycle is None or item.lifecycle == lifecycle)]
        values.sort(key=lambda item: (-item.uploaded_at.timestamp(), str(item.id)))
        if anchor is not None:
            values=[item for item in values if item.uploaded_at < anchor[0] or (item.uploaded_at == anchor[0] and item.id > anchor[1])]
        return values[:limit]

class Uow:
    def __init__(self): self.repository=Repo(); self.commits=0; self.rollbacks=0
    def commit(self): self.commits+=1
    def rollback(self): self.rollbacks+=1
class Auth:
    def require_mutation(self, **kwargs): return None
    def require_read(self, **kwargs): return None
    def require_withdraw(self, **kwargs): return None
class Scanner:
    def __init__(self, value): self.value=value
    def scan_exact(self, **kwargs): return SupportingFileScanResult(self.value, datetime.now(timezone.utc), "test-engine", "test-signatures", uuid4())

def service(scan="clean"):
    return SupportingFileService(uow=Uow(), objects=InMemoryPrivateSupportingFileObjectStore(), scanner=Scanner(scan), authorization=Auth())
def scope(): return SupportingFileScope(uuid4(), 1, None)
def mutation_metadata():
    return {
        "rationale": "Human supporting evidence",
        "correlation_id": uuid4(),
        "idempotency_id": uuid4(),
        "request_fingerprint": "f" * 64,
    }

def test_private_upload_clean_scan_makes_available_without_business_key():
    item=service(); s=scope(); reservation=item.reserve_upload(actor_id=1, scope=s)
    asset=item.finalize_upload(actor_id=1,reservation_id=reservation.id,scope=s,filename="basis.pdf",media_type=SupportingFileMediaType.PDF,content=PDF_BYTES,expected_digest=sha256(PDF_BYTES).hexdigest(),**mutation_metadata())
    assert asset.lifecycle == "available" and asset.storage_key == reservation.storage_key and len(asset.storage_key) == len("objects/") + 64

def test_scanner_indeterminate_stays_quarantined_and_is_not_disclosed_as_available():
    item=service("indeterminate"); s=scope(); reservation=item.reserve_upload(actor_id=1, scope=s)
    asset=item.finalize_upload(actor_id=1,reservation_id=reservation.id,scope=s,filename="basis.pdf",media_type=SupportingFileMediaType.PDF,content=PDF_BYTES,expected_digest=sha256(PDF_BYTES).hexdigest(),**mutation_metadata())
    assert asset.lifecycle == "quarantined"

def test_digest_mismatch_removes_private_object_and_never_creates_asset():
    item=service(); s=scope(); reservation=item.reserve_upload(actor_id=1, scope=s)
    with pytest.raises(SupportingFileIntegrityError):
        item.finalize_upload(actor_id=1,reservation_id=reservation.id,scope=s,filename="basis.pdf",media_type=SupportingFileMediaType.PDF,content=PDF_BYTES,expected_digest="a" * 64,**mutation_metadata())
    assert not item.uow.repository.assets

def test_scanner_unavailable_leaves_reconcilable_quarantined_asset():
    class Down:
        def scan_exact(self, **kwargs): raise SupportingFileScannerUnavailable()
    item=service(); item.scanner=Down(); s=scope(); reservation=item.reserve_upload(actor_id=1, scope=s)
    asset=item.finalize_upload(actor_id=1,reservation_id=reservation.id,scope=s,filename="basis.pdf",media_type=SupportingFileMediaType.PDF,content=PDF_BYTES,expected_digest=sha256(PDF_BYTES).hexdigest(),**mutation_metadata())
    assert asset.lifecycle == "quarantined" and reservation.status == "uploaded" and item.objects.head_exact(asset.storage_key, asset.object_version) is not None
