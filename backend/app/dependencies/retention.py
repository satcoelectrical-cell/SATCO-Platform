"""PATCH-055 retention-governance dependency composition."""

from hashlib import sha256
from dataclasses import dataclass

from app.adapters.supporting_file_object_store import S3PrivateSupportingFileObjectStore
from app.core.config import settings
from app.core.database import SessionLocal
from app.enums.retention import RetentionSubjectKind
from app.ports.supporting_file import SupportingFileObjectReceipt
from app.repositories.retention_unit_of_work import (
    SqlAlchemyRetentionUnitOfWork,
    UtcRetentionClock,
)
from app.services.retention_service import RetentionService


@dataclass(frozen=True, slots=True)
class RetentionExportReceipt:
    key: str
    version: str
    byte_count: int
    sha256: str


class PrivateRetentionExportStore:
    MAX_EXPORT_BYTES = 838_860_800

    def __init__(self, objects):
        self.objects = objects

    @staticmethod
    def _key(export_id):
        digest = sha256(b"retention-export-v1:" + export_id.bytes).hexdigest()
        return f"objects/{digest}"

    def put_private(self, *, export_id, stream, media_type):
        key = self._key(export_id)
        stream.seek(0)
        total = 0
        digest = sha256()
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > self.MAX_EXPORT_BYTES:
                raise ValueError("retention export exceeds aggregate bound")
            digest.update(chunk)
        if total < 1:
            raise ValueError("retention export is empty")
        stream.seek(0)
        response = self.objects.client.put_object(
            Bucket=self.objects.bucket, Key=key, Body=stream, ContentType=media_type,
            Metadata={"sha256": digest.hexdigest()}, ChecksumAlgorithm="SHA256",
            IfNoneMatch="*",
        )
        version = str(response.get("VersionId") or response.get("ETag", "")).strip('"')
        return RetentionExportReceipt(key, version, total, digest.hexdigest())

    def head_exact(self, *, export_id, version):
        receipt = self.objects.head_exact(self._key(export_id), version)
        if receipt is None:
            return None
        return RetentionExportReceipt(receipt.key, receipt.version, receipt.byte_size, receipt.sha256)

    def open_exact(self, *, export_id, version):
        return self.objects.open_exact(self._key(export_id), version)


class ExactSupportingFileRecoveryResolver:
    def __init__(self, *, uow_factory, objects):
        self.uow_factory = uow_factory
        self.objects = objects

    def resolve_authorized(self, *, subject, expected_digest):
        if subject.subject_kind is not RetentionSubjectKind.SUPPORTING_FILE:
            return None
        with self.uow_factory() as uow:
            asset = uow.retention.get_supporting_file_asset(subject=subject)
            if asset is None or asset.lifecycle not in {"available", "withdrawn"}:
                return None
            if expected_digest is not None and asset.content_digest != expected_digest:
                return None
            receipt = self.objects.head_exact(asset.storage_key, asset.object_version)
            if receipt is None or receipt.sha256 != asset.content_digest or receipt.byte_size != asset.byte_size:
                return None
            return self.objects.open_exact(asset.storage_key, asset.object_version)


def _objects():
    return S3PrivateSupportingFileObjectStore(
        endpoint_url=settings.SUPPORTING_FILE_OBJECT_ENDPOINT,
        bucket=settings.SUPPORTING_FILE_OBJECT_BUCKET,
        region=settings.SUPPORTING_FILE_OBJECT_REGION,
        access_key=settings.resolved_supporting_file_object_access_key(),
        secret_key=settings.resolved_supporting_file_object_secret_key(),
    )


def get_retention_service() -> RetentionService:
    uow_factory = lambda: SqlAlchemyRetentionUnitOfWork(SessionLocal)
    objects = _objects()
    return RetentionService(
        uow_factory=uow_factory,
        clock=UtcRetentionClock(),
        export_store=PrivateRetentionExportStore(objects),
        recovery_resolver=ExactSupportingFileRecoveryResolver(
            uow_factory=uow_factory, objects=objects
        ),
    )
