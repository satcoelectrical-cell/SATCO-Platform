"""Strict immutable source-location contracts shared by analysis and Evidence."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.enums.document_intelligence import SourceLocatorKind


NormalizedCoordinate = Annotated[float, Field(ge=0.0, le=1.0)]


class NormalizedBoundingBoxV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    coordinate_space: Literal["normalized_page_v1"] = "normalized_page_v1"
    x0: NormalizedCoordinate
    y0: NormalizedCoordinate
    x1: NormalizedCoordinate
    y1: NormalizedCoordinate

    @model_validator(mode="after")
    def ordered(self):
        if self.x1 <= self.x0 or self.y1 <= self.y0:
            raise ValueError("bounding box must have positive area")
        return self


class SourceLocatorV1(BaseModel):
    """One immutable pointer into one exact Supporting File representation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    locator_id: UUID
    schema_version: Literal[1] = 1
    locator_kind: SourceLocatorKind
    supporting_file_asset_id: UUID
    asset_version_at_analysis: int = Field(gt=0)
    storage_object_version: str = Field(min_length=1, max_length=512)
    digest_algorithm: Literal["sha256"] = "sha256"
    content_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    media_type: str = Field(min_length=1, max_length=255)
    page_index: int | None = Field(default=None, ge=0)
    page_label: str | None = Field(default=None, min_length=1, max_length=64)
    section_path: tuple[str, ...] = Field(default=(), max_length=16)
    section_title: str | None = Field(default=None, min_length=1, max_length=500)
    table_key: str | None = Field(default=None, min_length=1, max_length=128)
    table_title: str | None = Field(default=None, min_length=1, max_length=500)
    row_index: int | None = Field(default=None, ge=0)
    row_label: str | None = Field(default=None, min_length=1, max_length=256)
    column_index: int | None = Field(default=None, ge=0)
    column_label: str | None = Field(default=None, min_length=1, max_length=256)
    text_start: int | None = Field(default=None, ge=0)
    text_end: int | None = Field(default=None, ge=1)
    text_excerpt: str | None = Field(default=None, min_length=1, max_length=500)
    text_excerpt_digest: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    bounding_box: NormalizedBoundingBoxV1 | None = None
    source_revision_label: str | None = Field(default=None, min_length=1, max_length=128)
    extraction_method: Literal["deterministic", "provider", "hybrid"]
    created_at: datetime

    @model_validator(mode="after")
    def coherent_coordinates(self):
        if self.locator_kind is not SourceLocatorKind.DOCUMENT and self.page_index is None:
            raise ValueError("non-document locator requires page_index")
        if self.bounding_box is not None and self.page_index is None:
            raise ValueError("bounding box requires page_index")
        cell_fields = (self.table_key, self.row_index, self.column_index)
        if self.locator_kind is SourceLocatorKind.TABLE_CELL and any(value is None for value in cell_fields):
            raise ValueError("table-cell locator requires table, row, and column")
        span_fields = (self.text_start, self.text_end, self.text_excerpt, self.text_excerpt_digest)
        if self.locator_kind is SourceLocatorKind.TEXT_SPAN and any(value is None for value in span_fields):
            raise ValueError("text-span locator requires offsets, excerpt, and digest")
        if self.text_start is not None and self.text_end is not None and self.text_end <= self.text_start:
            raise ValueError("text span must have positive length")
        if any(not item.strip() for item in self.section_path):
            raise ValueError("section path entries must not be blank")
        return self
