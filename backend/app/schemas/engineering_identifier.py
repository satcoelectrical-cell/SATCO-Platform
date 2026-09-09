"""Strict ADR-025 API contracts."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums import EngineeringAuthorityStanding, EngineeringIdentifierKind
from app.enums.engineering_identifier import (
    EngineeringIdentifierIssuingScope,
    EngineeringIdentifierLifecycle,
    EngineeringIdentifierPrimaryRole,
)
from app.models.engineering_identifier import normalize_engineering_identifier


Rationale = Annotated[str, Field(min_length=1, max_length=2000)]


class IdentifierSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateEngineeringIdentifierRequest(IdentifierSchema):
    identifier_kind: EngineeringIdentifierKind
    display_value: str = Field(min_length=1, max_length=128)
    evidence_references: tuple[UUID, ...] = Field(default=(), max_length=8)
    expected_object_version: int = Field(ge=1)
    rationale: Rationale

    @field_validator("display_value")
    @classmethod
    def valid_value(cls, value: str) -> str:
        normalize_engineering_identifier(value)
        return value

    @field_validator("evidence_references")
    @classmethod
    def lexical_evidence(cls, value: tuple[UUID, ...]) -> tuple[UUID, ...]:
        if value != tuple(sorted(set(value), key=str)):
            raise ValueError("evidence_references must be unique and UUID-lexical")
        return value


class ReplaceEngineeringIdentifierRequest(CreateEngineeringIdentifierRequest):
    expected_identifier_version: int = Field(ge=1)


class WithdrawEngineeringIdentifierRequest(IdentifierSchema):
    expected_identifier_version: int = Field(ge=1)
    rationale: Rationale


class ReassignPrimaryIdentifierRequest(IdentifierSchema):
    target_identifier_id: UUID
    expected_object_version: int = Field(ge=1)
    expected_identifier_versions: dict[UUID, int] = Field(min_length=1, max_length=16)
    rationale: Rationale


class EngineeringIdentifierResponse(IdentifierSchema):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    identifier_id: UUID
    engineering_object_id: UUID
    organization_id: UUID
    project_id: int
    workspace_id: int
    identifier_kind: EngineeringIdentifierKind
    display_value: str
    normalized_value: str
    normalization_algorithm_version: str
    issuing_scope_kind: EngineeringIdentifierIssuingScope
    issuing_scope_value: str
    lifecycle: EngineeringIdentifierLifecycle
    authority_standing: EngineeringAuthorityStanding
    primary_role: EngineeringIdentifierPrimaryRole
    evidence_references: tuple[UUID, ...]
    version: int
    predecessor_identifier_id: UUID | None
    successor_identifier_id: UUID | None
    creator_id: int
    steward_id: int
    reviewer_id: int | None
    approver_id: int | None
    created_at: datetime
    updated_at: datetime
    origin_package_key: str | None
    origin_project_configuration_revision: int | None
    origin_declaration_id: str | None


class EngineeringIdentifierSetResponse(IdentifierSchema):
    items: tuple[EngineeringIdentifierResponse, ...] = Field(max_length=16)


class EngineeringIdentifierHistoryResponse(IdentifierSchema):
    items: tuple[EngineeringIdentifierResponse, ...] = Field(max_length=100)
    next_cursor: str | None = None
