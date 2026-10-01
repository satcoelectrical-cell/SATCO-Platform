"""Bounded PATCH-059 commercial entitlement API schemas."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


CommercialPackageKey = Literal[
    "electrical",
    "instrumentation",
    "control_automation",
]

CommercialSeatStateValue = Literal[
    "ASSIGNED",
    "RESERVED",
    "RETAINED",
]

CommercialEntitlementStateValue = Literal[
    "active",
    "grace",
    "expired",
    "invalid_or_unavailable",
    "time_untrusted",
]

CommercialValidationEffect = Literal[
    "initial",
    "successor",
    "idempotent",
    "rejected",
]

CommercialReasonCode = Literal[
    "entitlement_missing",
    "invalid_signature",
    "untrusted_key",
    "revoked_key",
    "organization_mismatch",
    "deployment_mismatch",
    "not_yet_valid",
    "grace",
    "expired",
    "rollback_detected",
    "same_revision_conflict",
    "time_untrusted",
    "package_not_entitled",
    "seat_required",
    "seat_reserved",
    "over_capacity",
    "release_sequence_out_of_range",
]


class StrictCommercialModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must include an explicit timezone")
    return value.astimezone(timezone.utc)


class CommercialEntitlementPayloadRequest(StrictCommercialModel):
    schema_version: Literal[1]
    entitlement_id: UUID
    revision: int = Field(ge=1)
    organization_id: UUID
    deployment_id: str = Field(min_length=1, max_length=200)
    issuer: str = Field(min_length=1, max_length=200)
    issued_at: datetime
    not_before: datetime
    valid_until: datetime
    grace_until: datetime
    package_keys: list[CommercialPackageKey] = Field(min_length=1)
    seat_capacity: int = Field(ge=1)
    support_until: datetime | None = None
    baseline_release_sequence: int = Field(ge=1)
    max_release_sequence: int = Field(ge=1)

    @field_validator(
        "issued_at",
        "not_before",
        "valid_until",
        "grace_until",
        "support_until",
    )
    @classmethod
    def normalize_datetime(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return _utc(value)

    @field_validator("package_keys")
    @classmethod
    def canonical_packages(
        cls,
        value: list[CommercialPackageKey],
    ) -> list[CommercialPackageKey]:
        if len(value) != len(set(value)):
            raise ValueError("package_keys must be unique")
        if value != sorted(value):
            raise ValueError("package_keys must be sorted")
        return value

    @model_validator(mode="after")
    def validate_bounds(self):
        if not (
            self.issued_at
            <= self.not_before
            <= self.valid_until
            <= self.grace_until
        ):
            raise ValueError("entitlement temporal bounds are invalid")

        if (self.grace_until - self.valid_until).total_seconds() > 30 * 86400:
            raise ValueError("grace period exceeds 30 days")

        if self.max_release_sequence < self.baseline_release_sequence:
            raise ValueError("release sequence range is invalid")

        return self


class CommercialEntitlementEnvelopeRequest(StrictCommercialModel):
    schema_: Literal["satco.commercial-entitlement/v1"] = Field(
        alias="schema",
        serialization_alias="schema",
    )
    key_id: str = Field(min_length=1, max_length=120)
    payload: CommercialEntitlementPayloadRequest
    signature: str = Field(min_length=1)


class CommercialEntitlementStatusResponse(StrictCommercialModel):
    available: bool
    effective_state: CommercialEntitlementStateValue
    entitlement_id: UUID | None = None
    revision: int | None = None
    digest_prefix: str | None = None
    package_keys: list[CommercialPackageKey] = Field(default_factory=list)
    seat_capacity: int | None = None
    valid_until: datetime | None = None
    grace_until: datetime | None = None
    support_until: datetime | None = None
    baseline_release_sequence: int | None = None
    max_release_sequence: int | None = None
    reason_code: CommercialReasonCode | None = None


class CommercialEntitlementValidationResponse(StrictCommercialModel):
    valid: bool
    effect: CommercialValidationEffect
    entitlement_id: UUID | None = None
    revision: int | None = None
    digest_prefix: str | None = None
    reason_code: CommercialReasonCode | None = None


class CommercialSeatResponse(StrictCommercialModel):
    user_id: int
    state: CommercialSeatStateValue
    executable: bool
    display_name: str | None = None


class CommercialSeatListResponse(StrictCommercialModel):
    capacity: int
    consuming_count: int
    over_capacity: bool
    seats: list[CommercialSeatResponse]


class CommercialSeatMutationResponse(StrictCommercialModel):
    user_id: int
    state: CommercialSeatStateValue | None
    consuming_count: int = Field(ge=0)
    capacity: int = Field(ge=1)


class CommercialSeatRetentionResponse(StrictCommercialModel):
    capacity: int = Field(ge=1)
    consuming_count: int = Field(ge=0)
    over_capacity: bool
    unresolved: bool


class CommercialSeatRetainedRequest(StrictCommercialModel):
    user_ids: list[int]

    @field_validator("user_ids")
    @classmethod
    def unique_user_ids(cls, value: list[int]) -> list[int]:
        if any(user_id <= 0 for user_id in value):
            raise ValueError("user_ids must contain positive identifiers")
        if len(value) != len(set(value)):
            raise ValueError("user_ids must be unique")
        return value


class CommercialUpdateEligibilityResponse(StrictCommercialModel):
    eligible: bool
    installed_release_sequence: int | None = None
    baseline_release_sequence: int | None = None
    max_release_sequence: int | None = None
    reason_code: CommercialReasonCode | None = None
