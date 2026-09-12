"""Strict HTTP contracts for the PATCH-054 Batch-1 catalog and rights routes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

from app.enums.standards import AIProcessingPermission, CatalogScope, RightsBasis, RightsStatus, StandardStanding


class StandardsSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StandardIdentityCreate(StandardsSchema):
    catalog_scope: CatalogScope
    issuer_display: Annotated[str, Field(min_length=1, max_length=240)]
    designation: Annotated[str, Field(min_length=1, max_length=240)]
    title: Annotated[str, Field(min_length=1, max_length=500)]
    language: Annotated[str | None, Field(max_length=24)] = None
    jurisdiction: dict[str, str] = Field(default_factory=dict, max_length=16)
    metadata_source_reference: Annotated[str, Field(min_length=1, max_length=500)]

    @field_validator("issuer_display", "designation", "title", "metadata_source_reference")
    @classmethod
    def safe_text(cls, value: str) -> str:
        value = value.strip()
        if not value or "\x00" in value:
            raise ValueError("invalid text")
        return value


class StandardEditionCreate(StandardsSchema):
    edition_designation: Annotated[str, Field(min_length=1, max_length=240)]
    edition_disambiguator: Annotated[str, Field(max_length=120)] = ""
    official_publication_identifier: Annotated[str | None, Field(max_length=240)] = None
    publication_date: AwareDatetime | None = None
    effective_date: AwareDatetime | None = None
    language: Annotated[str | None, Field(max_length=24)] = None
    jurisdiction: dict[str, str] = Field(default_factory=dict, max_length=16)
    metadata_source_reference: Annotated[str, Field(min_length=1, max_length=500)]
    initial_standing: StandardStanding
    observed_effective_at: AwareDatetime
    standing_source_reference: Annotated[str, Field(min_length=1, max_length=500)]
    superseded_by_edition_id: UUID | None = None

    @model_validator(mode="after")
    def standing_shape(self):
        if self.initial_standing == StandardStanding.SUPERSEDED and self.superseded_by_edition_id is None:
            raise ValueError("superseded standing requires replacement edition")
        if self.initial_standing != StandardStanding.SUPERSEDED and self.superseded_by_edition_id is not None:
            raise ValueError("replacement edition only applies to superseded standing")
        return self


class StandingObservationCreate(StandardsSchema):
    standing: StandardStanding
    observed_effective_at: AwareDatetime
    source_reference: Annotated[str, Field(min_length=1, max_length=500)]
    superseded_by_edition_id: UUID | None = None
    expected_version: Annotated[int, Field(ge=1)]

    @model_validator(mode="after")
    def standing_shape(self):
        if self.standing == StandardStanding.SUPERSEDED and self.superseded_by_edition_id is None:
            raise ValueError("superseded standing requires replacement edition")
        if self.standing != StandardStanding.SUPERSEDED and self.superseded_by_edition_id is not None:
            raise ValueError("replacement edition only applies to superseded standing")
        return self


class RightsBindingReplace(StandardsSchema):
    rights_basis: RightsBasis
    rights_status: RightsStatus
    allow_metadata_visibility: bool = False
    allow_content_storage: bool = False
    allow_indexing: bool = False
    allow_excerpt_display: bool = False
    allow_source_retrieval: bool = False
    allow_derived_retention: bool = False
    allow_derived_current_use: bool = False
    ai_processing_permission: AIProcessingPermission = AIProcessingPermission.PROHIBITED
    approved_processor_policy_ids: list[Annotated[str, Field(min_length=1, max_length=80)]] = Field(default_factory=list, max_length=32)
    effective_from: AwareDatetime
    effective_until: AwareDatetime | None = None
    rights_authority_reference: Annotated[str, Field(min_length=1, max_length=500)]
    rights_authority_digest: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    expected_version: Annotated[int, Field(ge=0)]
    reason_code: Annotated[str, Field(min_length=1, max_length=80)] = "replacement"
    reason: Annotated[str | None, Field(max_length=500)] = None

    @model_validator(mode="after")
    def closed_rights_shape(self):
        if self.effective_until is not None and self.effective_from >= self.effective_until:
            raise ValueError("effective_from must precede effective_until")
        if self.approved_processor_policy_ids != sorted(set(self.approved_processor_policy_ids)):
            raise ValueError("processor policies must be sorted and unique")
        if self.ai_processing_permission == AIProcessingPermission.APPROVED_PROCESSOR and not self.approved_processor_policy_ids:
            raise ValueError("approved processor permission requires policies")
        if self.ai_processing_permission != AIProcessingPermission.APPROVED_PROCESSOR and self.approved_processor_policy_ids:
            raise ValueError("processor policies are only valid for approved processor")
        protected = (self.allow_content_storage, self.allow_indexing, self.allow_excerpt_display, self.allow_source_retrieval, self.allow_derived_retention, self.allow_derived_current_use)
        if self.rights_basis in {RightsBasis.METADATA_ONLY, RightsBasis.UNKNOWN} and any(protected):
            raise ValueError("metadata-only and unknown bases deny protected capability")
        if self.rights_status in {RightsStatus.EXPIRED, RightsStatus.REVOKED, RightsStatus.UNKNOWN} and any(protected):
            raise ValueError("inactive status denies protected capability")
        return self


class RightsRevocation(StandardsSchema):
    expected_version: Annotated[int, Field(ge=1)]
    reason: Annotated[str, Field(min_length=1, max_length=500)]


class StandardsPage(StandardsSchema):
    items: list[dict]
    next_cursor: str | None = None


def require_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("timestamps must be UTC")
    return value
