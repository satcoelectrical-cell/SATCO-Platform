from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.enums import ProjectPriority, ProjectStatus


ProjectSortField = Literal[
    "name",
    "project_code",
    "created_at",
    "updated_at",
    "status",
    "priority",
    "progress",
    "start_date",
    "target_completion_date",
]
SortOrder = Literal["asc", "desc"]


class CustomerShortResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class UserShortResponse(BaseModel):
    id: int
    username: str
    full_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    customer_id: int
    description: str | None = Field(
        default=None,
        max_length=5000,
    )
    priority: ProjectPriority = ProjectPriority.MEDIUM
    owner_id: int | None = None
    primary_assignee_id: int | None = None
    start_date: date | None = None
    target_completion_date: date | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "name": "PLC Modernization",
                    "description": "Replace the legacy control system.",
                    "customer_id": 12,
                    "priority": "high",
                    "primary_assignee_id": 8,
                    "start_date": "2026-08-01",
                    "target_completion_date": "2026-11-30",
                }
            ]
        },
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Project name must not be empty")
        return value

    @field_validator("description")
    @classmethod
    def normalize_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ProjectUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    customer_id: int | None = None
    description: str | None = Field(
        default=None,
        max_length=5000,
    )
    status: ProjectStatus | None = None
    priority: ProjectPriority | None = None
    owner_id: int | None = None
    primary_assignee_id: int | None = None
    start_date: date | None = None
    target_completion_date: date | None = None
    progress: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "status": "in_progress",
                    "priority": "high",
                    "primary_assignee_id": 8,
                    "start_date": "2026-08-01",
                    "target_completion_date": "2026-11-30",
                    "progress": 35,
                }
            ]
        },
    )

    @field_validator("name")
    @classmethod
    def validate_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Project name must not be empty")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(
        cls,
        value: ProjectStatus | None,
    ) -> ProjectStatus:
        if value is None:
            raise ValueError("Project status must not be null")
        return value

    @field_validator("description")
    @classmethod
    def normalize_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ProjectResponse(BaseModel):
    id: int
    project_code: str
    name: str
    description: str | None
    customer: CustomerShortResponse
    status: ProjectStatus
    priority: ProjectPriority
    owner: UserShortResponse | None
    primary_assignee: UserShortResponse | None
    start_date: date | None
    target_completion_date: date | None
    completed_at: datetime | None
    progress: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 42,
                    "project_code": "SAT-PRJ-2026-0001",
                    "name": "PLC Modernization",
                    "description": "Replace the legacy control system.",
                    "customer": {
                        "id": 12,
                        "name": "Example Customer",
                    },
                    "status": "in_progress",
                    "priority": "high",
                    "owner": {
                        "id": 3,
                        "username": "owner",
                        "full_name": "Project Owner",
                    },
                    "primary_assignee": {
                        "id": 8,
                        "username": "engineer",
                        "full_name": "Primary Engineer",
                    },
                    "start_date": "2026-08-01",
                    "target_completion_date": "2026-11-30",
                    "completed_at": None,
                    "progress": 35,
                    "created_at": "2026-07-26T06:00:00Z",
                    "updated_at": "2026-08-15T10:30:00Z",
                }
            ]
        },
    )


class ProjectSelectionDTO(BaseModel):
    """Immutable base for actor-authorized Project selection contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ProjectSelectionActor(ProjectSelectionDTO):
    """Minimum trusted context used by the canonical Project application read."""

    actor_id: int = Field(gt=0)
    organization_id: UUID


class ProjectAuthorizedSelectionItem(ProjectSelectionDTO):
    """Minimal canonical Project choice visible to the current actor."""

    project_id: int = Field(gt=0)
    display_name: str = Field(min_length=1, max_length=200)


class ProjectAuthorizedSelectionPage(ProjectSelectionDTO):
    """Bounded Project choices without a hidden or global total."""

    items: tuple[ProjectAuthorizedSelectionItem, ...] = Field(max_length=100)
    page: int = Field(ge=1)
    size: int = Field(ge=1, le=100)
    returned_count: int = Field(ge=0, le=100)
    has_more: bool

    @model_validator(mode="after")
    def validate_returned_count(self) -> "ProjectAuthorizedSelectionPage":
        if self.returned_count != len(self.items):
            raise ValueError("returned_count must equal returned Project choices")
        if len(self.items) > self.size:
            raise ValueError("Project choices exceed requested size")
        return self
