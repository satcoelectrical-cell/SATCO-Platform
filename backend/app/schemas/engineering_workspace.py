from datetime import datetime
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator

from app.enums import Discipline, WorkspaceStatus
from app.schemas.project import UserShortResponse


WorkspaceSortField = Literal[
    "discipline",
    "status",
    "created_at",
    "updated_at",
]
WorkspaceSortOrder = Literal["asc", "desc"]


class EngineeringWorkspaceCreate(BaseModel):
    discipline: Discipline
    description: str | None = Field(default=None, max_length=5000)
    owner_id: int | None = Field(default=None, gt=0)
    primary_assignee_id: int | None = Field(default=None, gt=0)
    collaborator_ids: list[int] = Field(
        default_factory=list,
        max_length=100,
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "discipline": "electrical",
                    "description": "Electrical discipline workspace.",
                    "owner_id": 3,
                    "primary_assignee_id": 8,
                    "collaborator_ids": [11],
                }
            ]
        },
    )

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("collaborator_ids")
    @classmethod
    def validate_collaborator_ids(cls, value: list[int]) -> list[int]:
        if any(user_id <= 0 for user_id in value):
            raise ValueError("Collaborator identifiers must be positive")
        if len(value) != len(set(value)):
            raise ValueError("Collaborator identifiers must be unique")
        return value


class EngineeringWorkspaceUpdate(BaseModel):
    description: str | None = Field(default=None, max_length=5000)
    owner_id: int | None = Field(default=None, gt=0)
    primary_assignee_id: int | None = Field(default=None, gt=0)
    expected_version: int = Field(gt=0)

    model_config = ConfigDict(extra="forbid")

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def require_update_field(self):
        provided = self.model_fields_set - {"expected_version"}
        if not provided:
            raise ValueError("At least one Workspace field is required")
        if {"owner_id", "primary_assignee_id"} <= provided:
            raise ValueError(
                "Owner and primary assignee changes require separate "
                "audited requests"
            )
        return self


class WorkspaceStatusTransitionRequest(BaseModel):
    status: WorkspaceStatus
    reason: str | None = Field(default=None, max_length=2000)
    expected_version: int = Field(gt=0)

    model_config = ConfigDict(extra="forbid")

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class WorkspaceArchiveRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)
    expected_version: int = Field(gt=0)

    model_config = ConfigDict(extra="forbid")

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Archive reason must not be empty")
        return value


class WorkspaceRestoreRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)
    expected_version: int = Field(gt=0)

    model_config = ConfigDict(extra="forbid")

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Restore reason must not be empty")
        return value


class EngineeringWorkspaceCollaboratorAdd(BaseModel):
    user_id: int = Field(gt=0)
    expected_version: int = Field(gt=0)

    model_config = ConfigDict(extra="forbid")


class EngineeringWorkspaceResponse(BaseModel):
    id: int
    project_id: int
    project_code: str
    project_name: str
    discipline: Discipline
    display_name: str
    description: str | None
    status: WorkspaceStatus
    owner: UserShortResponse
    primary_assignee: UserShortResponse | None
    collaborators: list[UserShortResponse]
    collaborator_count: int
    version: int
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime
    allowed_actions: list[str]


class EngineeringWorkspaceGraphSummary(BaseModel):
    """Closed owner-authorized graph projection; excludes people and assignment data."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    workspace_id: int = Field(gt=0)
    project_id: int = Field(gt=0)
    discipline: Discipline
    workspace_status: WorkspaceStatus


class EngineeringWorkspaceListResponse(BaseModel):
    items: list[EngineeringWorkspaceResponse]
    total: int
    page: int
    size: int
