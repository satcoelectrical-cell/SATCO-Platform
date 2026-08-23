"""Pure Supporting File contracts and deterministic integrity helpers."""
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
import unicodedata
from uuid import UUID
from io import BytesIO
from zipfile import BadZipFile, ZipFile

from app.enums.supporting_file import SupportingFileLifecycle, SupportingFileMediaType
from app.exceptions.supporting_file import SupportingFileIntegrityError, SupportingFileValidationError

MAX_FILE_BYTES = 26_214_400
_KEY = re.compile(r"^objects/[0-9a-f]{64}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")


def safe_filename(value: str) -> tuple[str, str]:
    if not isinstance(value, str):
        raise SupportingFileValidationError("filename is invalid")
    value = unicodedata.normalize("NFC", value).replace("\\", "/").split("/")[-1].strip()
    if not value or len(value) > 255 or any(ord(char) < 32 for char in value):
        raise SupportingFileValidationError("filename is invalid")
    ascii_name = "".join(char if 32 <= ord(char) < 127 else "_" for char in value).strip(" .")[:120]
    if not ascii_name:
        ascii_name = "attachment"
    return value, ascii_name


def opaque_storage_key(value: str) -> str:
    if not isinstance(value, str) or not _KEY.fullmatch(value):
        raise SupportingFileValidationError("storage key is invalid")
    return value


def content_digest(value: str) -> str:
    if not isinstance(value, str) or not _DIGEST.fullmatch(value):
        raise SupportingFileValidationError("content digest is invalid")
    return value


def verified_media_type(content: bytes, declared: SupportingFileMediaType) -> SupportingFileMediaType:
    """Return a bounded signature-derived type; browser MIME is never authority."""
    if not isinstance(content, bytes) or not content:
        raise SupportingFileValidationError("file type is invalid")
    detected = None
    if content.startswith(b"%PDF-"):
        detected = SupportingFileMediaType.PDF
    elif content.startswith(b"\x89PNG\r\n\x1a\n"):
        detected = SupportingFileMediaType.PNG
    elif content.startswith(b"\xff\xd8\xff"):
        detected = SupportingFileMediaType.JPEG
    elif content.startswith(b"PK\x03\x04"):
        try:
            with ZipFile(BytesIO(content)) as archive:
                names = set(archive.namelist())
            if "word/document.xml" in names:
                detected = SupportingFileMediaType.DOCX
            elif "xl/workbook.xml" in names:
                detected = SupportingFileMediaType.XLSX
        except BadZipFile:
            detected = None
    else:
        try:
            text = content.decode("utf-8")
            if "\x00" not in text:
                detected = (
                    SupportingFileMediaType.CSV
                    if declared is SupportingFileMediaType.CSV and any(mark in text for mark in (",", ";", "\t"))
                    else SupportingFileMediaType.TEXT
                )
        except UnicodeDecodeError:
            detected = None
    if detected is not declared:
        raise SupportingFileValidationError("file type is invalid")
    return detected


def bounded_stream_identity(stream) -> tuple[int, str]:
    """Hash a seekable/spooled stream in bounded chunks and restore position."""
    try:
        stream.seek(0)
        total = 0; digest = sha256()
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            if not isinstance(chunk, bytes):
                raise TypeError
            total += len(chunk)
            if total > MAX_FILE_BYTES:
                raise SupportingFileValidationError("content size is invalid")
            digest.update(chunk)
        if total < 1:
            raise SupportingFileValidationError("content size is invalid")
        return total, digest.hexdigest()
    except SupportingFileValidationError:
        raise
    except Exception:
        raise SupportingFileValidationError("content stream is invalid") from None
    finally:
        try:
            stream.seek(0)
        except Exception:
            pass


def verified_stream_media_type(stream, declared: SupportingFileMediaType) -> SupportingFileMediaType:
    try:
        stream.seek(0)
        prefix = stream.read(8192)
        if prefix.startswith(b"PK\x03\x04"):
            stream.seek(0)
            with ZipFile(stream) as archive:
                names = set(archive.namelist())
            detected = (
                SupportingFileMediaType.DOCX if "word/document.xml" in names
                else SupportingFileMediaType.XLSX if "xl/workbook.xml" in names
                else None
            )
            if detected is not declared:
                raise SupportingFileValidationError("file type is invalid")
            return detected
        return verified_media_type(prefix, declared)
    except SupportingFileValidationError:
        raise
    except Exception:
        raise SupportingFileValidationError("file type is invalid") from None
    finally:
        stream.seek(0)


def canonical_json(value: object) -> str:
    def normalize(item):
        if is_dataclass(item):
            return normalize(asdict(item))
        if isinstance(item, UUID):
            return str(item)
        if isinstance(item, datetime):
            if item.tzinfo is None:
                raise SupportingFileIntegrityError("timestamp must be aware")
            return item.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
        if isinstance(item, tuple):
            return [normalize(x) for x in item]
        if isinstance(item, list):
            return [normalize(x) for x in item]
        if isinstance(item, dict):
            return {str(key): normalize(val) for key, val in item.items()}
        if isinstance(item, SupportingFileLifecycle | SupportingFileMediaType):
            return item.value
        return item
    return json.dumps(normalize(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_digest(value: object) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class SupportingFileActor:
    actor_id: int
    organization_id: UUID


@dataclass(frozen=True, slots=True)
class SupportingFileScope:
    organization_id: UUID
    project_id: int
    workspace_id: int | None = None

    def __post_init__(self):
        if self.project_id <= 0 or (self.workspace_id is not None and self.workspace_id <= 0):
            raise SupportingFileValidationError("scope is invalid")


@dataclass(frozen=True, slots=True)
class SupportingFileMetadata:
    actor: SupportingFileActor
    correlation_id: UUID
    idempotency_id: UUID
    rationale: str

    def __post_init__(self):
        if not self.rationale or not self.rationale.strip() or len(self.rationale) > 2000:
            raise SupportingFileValidationError("rationale is invalid")


@dataclass(frozen=True, slots=True)
class SupportingFileHistoricalBasisV1:
    basis_schema_version: int
    source_category: str
    asset_id: UUID
    asset_version: int
    organization_id: UUID
    project_id: int
    workspace_id: int | None
    safe_filename: str
    media_type: SupportingFileMediaType
    byte_size: int
    digest_algorithm: str
    content_digest: str
    uploader_id: int
    uploaded_at: datetime
    predecessor_asset_id: UUID | None

    def __post_init__(self):
        if self.basis_schema_version != 1 or self.source_category != "supporting_file" or self.asset_version < 1 or self.project_id < 1 or self.uploader_id < 1 or self.byte_size < 1 or self.byte_size > MAX_FILE_BYTES or self.digest_algorithm != "sha256":
            raise SupportingFileValidationError("historical basis is invalid")
        safe_filename(self.safe_filename); content_digest(self.content_digest)
        if self.uploaded_at.tzinfo is None:
            raise SupportingFileValidationError("uploaded timestamp is invalid")
