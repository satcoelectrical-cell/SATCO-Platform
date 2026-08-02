"""Pydantic v2 contracts for the EngineeringObject application boundary."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

from app.enums import EngineeringAuthorityStanding
from app.enums import EngineeringDiscipline
from app.enums import EngineeringLifecycle
from app.enums import EngineeringObjectFamily
from app.enums import EngineeringObjectType


PositiveIdentifier = Annotated[int, Field(gt=0)]
PositiveVersion = Annotated[int, Field(gt=0)]
Rationale = Annotated[str, Field(min_length=1, max_length=2000)]


class EngineeringObjectRequest(BaseModel):
    """Strict base for client-supplied EngineeringObject request bodies."""

    model_config = ConfigDict(extra="forbid")


class EngineeringObjectBase(BaseModel):
    """Approved EngineeringObject classification shared by API contracts."""

    family: EngineeringObjectFamily
    discipline: EngineeringDiscipline
    object_type: EngineeringObjectType

    model_config = ConfigDict(extra="forbid")


class EngineeringObjectCreate(EngineeringObjectBase):
    """Client values accepted by ``CreateEngineeringObject``.

    Organization, Customer, Workspace, Creator, initial states, and version are
    derived by trusted application collaborators and cannot be supplied here.
    """

    project_id: PositiveIdentifier
    family: EngineeringObjectFamily
    discipline: EngineeringDiscipline
    object_type: EngineeringObjectType
    steward_id: PositiveIdentifier | None = None
    rationale: Rationale
    evidence_references: list[UUID] = Field(default_factory=list)

    @field_validator("rationale")
    @classmethod
    def normalize_rationale(cls, value: str) -> str:
        """Reject whitespace-only rationale and persist normalized text."""

        normalized = value.strip()
        if not normalized:
            raise ValueError("rationale must not be empty")
        return normalized

    @field_validator("evidence_references")
    @classmethod
    def require_unique_evidence(cls, value: list[UUID]) -> list[UUID]:
        """Prevent ambiguous duplicate Evidence references."""

        if len(value) != len(set(value)):
            raise ValueError("evidence references must be unique")
        return value


class EngineeringObjectMutationRequest(EngineeringObjectRequest):
    """Shared body contract for every post-creation mutation."""

    expected_version: PositiveVersion
    rationale: Rationale

    @field_validator("rationale")
    @classmethod
    def normalize_rationale(cls, value: str) -> str:
        """Reject whitespace-only mutation rationale."""

        normalized = value.strip()
        if not normalized:
            raise ValueError("rationale must not be empty")
        return normalized


class EvidenceBearingMutation(EngineeringObjectMutationRequest):
    """Mutation request that may carry approved Evidence references."""

    evidence_references: list[UUID] = Field(default_factory=list)

    @field_validator("evidence_references")
    @classmethod
    def require_unique_evidence(cls, value: list[UUID]) -> list[UUID]:
        """Prevent duplicate Evidence references in a command."""

        if len(value) != len(set(value)):
            raise ValueError("evidence references must be unique")
        return value


class ReclassifyEngineeringObjectRequest(EvidenceBearingMutation):
    """Complete target classification for ``ReclassifyEngineeringObject``."""

    family: EngineeringObjectFamily
    discipline: EngineeringDiscipline
    object_type: EngineeringObjectType


class TransitionEngineeringObjectLifecycleRequest(EvidenceBearingMutation):
    """Target state for ``TransitionEngineeringObjectLifecycle``."""

    lifecycle: EngineeringLifecycle
    replacement_object_id: UUID | None = None


class TransitionEngineeringObjectAuthorityRequest(EvidenceBearingMutation):
    """Target standing for ``TransitionEngineeringObjectAuthority``."""

    authority_standing: EngineeringAuthorityStanding


class TransferEngineeringObjectStewardRequest(
    EngineeringObjectMutationRequest
):
    """Target Human for ``TransferEngineeringObjectSteward``."""

    steward_id: PositiveIdentifier


class EngineeringObjectFilter(BaseModel):
    """Approved scalar filters for an authorized project-scoped list query."""

    workspace_id: PositiveIdentifier | None = None
    family: EngineeringObjectFamily | None = None
    discipline: EngineeringDiscipline | None = None
    object_type: EngineeringObjectType | None = None
    lifecycle: EngineeringLifecycle | None = None
    authority_standing: EngineeringAuthorityStanding | None = None

    model_config = ConfigDict(extra="forbid")


class EngineeringObjectPagination(BaseModel):
    """Standard SATCO one-based pagination request."""

    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

    model_config = ConfigDict(extra="forbid")


class EngineeringObjectResponse(BaseModel):
    """Authorized scalar representation of current aggregate state."""

    id: UUID
    organization_id: UUID
    customer_id: int | None
    project_id: int
    workspace_id: int
    family: EngineeringObjectFamily
    discipline: EngineeringDiscipline
    object_type: EngineeringObjectType
    subtype: str | None
    lifecycle: EngineeringLifecycle
    authority_standing: EngineeringAuthorityStanding
    version: int
    creator_id: int
    steward_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EngineeringObjectListResponse(BaseModel):
    """Standard SATCO paginated EngineeringObject response."""

    items: list[EngineeringObjectResponse]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    size: int = Field(ge=1)

    model_config = ConfigDict(extra="forbid")
