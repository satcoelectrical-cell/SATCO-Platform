"""Closed Supporting File HTTP-neutral schemas."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.enums.supporting_file import SupportingFileLifecycle, SupportingFileMediaType
from app.models.supporting_file_command import MAX_FILE_BYTES, content_digest, safe_filename


class SupportingFileSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SupportingFileUploadRequest(SupportingFileSchema):
    project_id: int = Field(gt=0)
    workspace_id: int | None = Field(None, gt=0)
    predecessor_asset_id: UUID | None = None
    rationale: str = Field(min_length=1, max_length=2000)


class SupportingFileWithdrawalRequest(SupportingFileSchema):
    expected_version: int = Field(gt=0)
    rationale: str = Field(min_length=1, max_length=2000)


class SupportingFileResponse(SupportingFileSchema):
    id: UUID
    organization_id: UUID
    project_id: int
    workspace_id: int | None
    safe_filename: str = Field(min_length=1, max_length=255)
    media_type: SupportingFileMediaType
    byte_size: int = Field(ge=1, le=MAX_FILE_BYTES)
    digest_algorithm: str = "sha256"
    content_digest: str
    lifecycle: SupportingFileLifecycle
    version: int = Field(ge=1)
    uploader_id: int = Field(gt=0)
    uploaded_at: datetime
    scanned_at: datetime | None
    predecessor_asset_id: UUID | None
    allowed_actions: tuple[str, ...] = ()

    @field_validator("safe_filename")
    @classmethod
    def valid_filename(cls, value):
        return safe_filename(value)[0]

    @field_validator("content_digest")
    @classmethod
    def valid_digest(cls, value):
        return content_digest(value)


class SupportingFileListResponse(SupportingFileSchema):
    items: list[SupportingFileResponse] = Field(max_length=50)
    visible_count: int = Field(ge=0, le=50)
    continuation: str | None = None

    @model_validator(mode="after")
    def count_matches(self):
        if self.visible_count != len(self.items):
            raise ValueError("visible count must match items")
        return self


class SupportingFileScanResultRequest(SupportingFileSchema):
    asset_id: UUID
    asset_version: int = Field(gt=0)
    attempt_id: UUID
    object_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    disposition: str = Field(pattern=r"^(clean|unsafe|indeterminate)$")
    engine_id: str = Field(min_length=1, max_length=128)
    signature_set_id: str = Field(min_length=1, max_length=128)
    observed_at: datetime
    correlation_id: UUID
