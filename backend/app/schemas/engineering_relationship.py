"""Pydantic v2 contracts for the PATCH-026 application boundary."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic import model_validator

from app.enums import EngineeringAuthorityStanding
from app.enums import EngineeringRelationshipLifecycle as RelationshipLifecycle
from app.enums import RelationshipFamily, RelationshipType
from app.enums import validate_relationship_pair


PositiveIdentifier = Annotated[int, Field(gt=0)]
PositiveVersion = Annotated[int, Field(gt=0)]
Rationale = Annotated[str, Field(min_length=1, max_length=2000)]


class StrictRelationshipSchema(BaseModel):
    """Reject transport fields outside an approved relationship contract."""

    model_config = ConfigDict(extra="forbid")


class RelationshipPairSchema(StrictRelationshipSchema):
    """Canonical family/type discriminator required by every command."""

    relationship_family: RelationshipFamily
    relationship_type: RelationshipType

    @model_validator(mode="after")
    def validate_pair(self):
        validate_relationship_pair(
            self.relationship_family, self.relationship_type
        )
        return self


class EvidenceSchema(StrictRelationshipSchema):
    """Shared strict Evidence UUID collection."""

    evidence_references: list[UUID] = Field(default_factory=list)

    @field_validator("evidence_references")
    @classmethod
    def require_unique_evidence(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("evidence references must be unique")
        return value


class EngineeringRelationshipCreate(RelationshipPairSchema):
    """Client values for CreateEngineeringRelationship."""

    source_object_id: UUID
    target_object_id: UUID
    steward_id: PositiveIdentifier | None = None
    evidence_references: list[UUID] = Field(default_factory=list)
    rationale: Rationale

    @model_validator(mode="after")
    def validate_create(self):
        if self.source_object_id == self.target_object_id:
            raise ValueError("relationship endpoints must be distinct")
        if len(self.evidence_references) != len(set(self.evidence_references)):
            raise ValueError("evidence references must be unique")
        return self

    @field_validator("rationale")
    @classmethod
    def normalize_rationale(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("rationale must not be empty")
        return value


class EngineeringRelationshipCommandRequest(RelationshipPairSchema):
    """Optimistic command body shared by every post-creation mutation."""

    expected_version: PositiveVersion
    rationale: Rationale
    evidence_references: list[UUID] = Field(default_factory=list)

    @field_validator("rationale")
    @classmethod
    def normalize_rationale(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("rationale must not be empty")
        return value

    @field_validator("evidence_references")
    @classmethod
    def require_unique_evidence(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("evidence references must be unique")
        return value


class SubmitEngineeringRelationshipForReviewRequest(
    EngineeringRelationshipCommandRequest
):
    """Submit one relationship for review."""


class ReviewEngineeringRelationshipRequest(
    EngineeringRelationshipCommandRequest
):
    """Record an accountable review."""


class ApproveEngineeringRelationshipRequest(
    EngineeringRelationshipCommandRequest
):
    """Record an accountable approval."""


class DisputeEngineeringRelationshipRequest(
    EngineeringRelationshipCommandRequest
):
    """Dispute an approved relationship."""


class RejectEngineeringRelationshipRequest(
    EngineeringRelationshipCommandRequest
):
    """Reject a relationship through explicit authority command."""


class TransitionEngineeringRelationshipLifecycleRequest(
    EngineeringRelationshipCommandRequest
):
    """Apply one approved logical lifecycle transition."""

    lifecycle: RelationshipLifecycle
    replacement_relationship_id: UUID | None = None

    @model_validator(mode="after")
    def validate_replacement(self):
        if (
            self.lifecycle is RelationshipLifecycle.SUPERSEDED
            and self.replacement_relationship_id is None
        ):
            raise ValueError(
                "supersession requires replacement_relationship_id"
            )
        if (
            self.lifecycle is not RelationshipLifecycle.SUPERSEDED
            and self.replacement_relationship_id is not None
        ):
            raise ValueError(
                "replacement_relationship_id is valid only for supersession"
            )
        return self


class TransferEngineeringRelationshipStewardRequest(
    EngineeringRelationshipCommandRequest
):
    """Transfer stewardship to one application-validated Human."""

    steward_id: PositiveIdentifier


class EngineeringRelationshipFilter(StrictRelationshipSchema):
    """Approved filters for authorized relationship queries."""

    relationship_family: RelationshipFamily | None = None
    relationship_type: RelationshipType | None = None
    lifecycle: RelationshipLifecycle | None = None
    authority_standing: EngineeringAuthorityStanding | None = None
    direction: Literal["incoming", "outgoing", "both"] = "both"
    workspace_id: PositiveIdentifier | None = None

    @model_validator(mode="after")
    def validate_optional_pair(self):
        if self.relationship_type is not None:
            if self.relationship_family is None:
                raise ValueError("relationship_type filter requires family")
            validate_relationship_pair(
                self.relationship_family, self.relationship_type
            )
        return self


class EngineeringRelationshipPagination(StrictRelationshipSchema):
    """Standard one-based PATCH-026 pagination."""

    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class EngineeringRelationshipTraversal(EngineeringRelationshipFilter):
    """Hard-bounded neighborhood/path query parameters."""

    max_depth: int = Field(default=1, ge=1, le=5)
    max_results: int = Field(default=20, ge=1, le=100)
    continuation_token: str | None = Field(default=None, max_length=2048)


class EngineeringRelationshipResponse(BaseModel):
    """Authorized scalar representation of relationship state."""

    id: UUID
    organization_id: UUID
    project_id: int
    workspace_id: int
    source_object_id: UUID
    target_object_id: UUID
    relationship_family: RelationshipFamily
    relationship_type: RelationshipType
    lifecycle: RelationshipLifecycle
    authority_standing: EngineeringAuthorityStanding
    evidence_references: list[UUID]
    version: int
    creator_id: int
    steward_id: int
    reviewer_id: int | None
    approver_id: int | None
    created_at: datetime
    updated_at: datetime
    allowed_actions: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class EngineeringRelationshipListResponse(StrictRelationshipSchema):
    """Authorized paginated relationship list."""

    items: list[EngineeringRelationshipResponse]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    size: int = Field(ge=1)


class EngineeringRelationshipTraversalResponse(StrictRelationshipSchema):
    """Authorized bounded traversal response without protected counts."""

    node_ids: list[UUID]
    relationships: list[EngineeringRelationshipResponse]
    bounded_depth: int = Field(ge=0, le=5)
    truncated: bool
    continuation_token: str | None = None
