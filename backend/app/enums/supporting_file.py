"""Closed Supporting File Asset vocabulary."""
from enum import StrEnum


class SupportingFileLifecycle(StrEnum):
    QUARANTINED = "quarantined"
    AVAILABLE = "available"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class SupportingFileScanDisposition(StrEnum):
    CLEAN = "clean"
    UNSAFE = "unsafe"
    INDETERMINATE = "indeterminate"


class SupportingFileReservationStatus(StrEnum):
    RESERVED = "reserved"
    STREAMING = "streaming"
    UPLOADED = "uploaded"
    CONSUMED = "consumed"
    FAILED = "failed"
    EXPIRED = "expired"


class SupportingFileMediaType(StrEnum):
    PDF = "application/pdf"
    TEXT = "text/plain"
    CSV = "text/csv"
    PNG = "image/png"
    JPEG = "image/jpeg"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
