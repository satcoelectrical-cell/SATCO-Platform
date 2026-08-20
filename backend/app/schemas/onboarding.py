"""Closed PATCH-041 transport contracts."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

RoleValue = Literal["admin", "engineer"]


class OrganizationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    name: str
    slug: str
    is_active: bool


class MemberSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: int
    username: str
    email: str
    full_name: str | None
    role: RoleValue
    account_active: bool
    activation_pending: bool
    membership_enabled: bool
    membership_selected: bool
    version: int


class BootstrapOrganizationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    organization_name: str = Field(min_length=2, max_length=200)
    organization_slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", min_length=2, max_length=80)
    admin_username: str = Field(pattern=r"^[A-Za-z0-9_.-]+$", min_length=3, max_length=64)
    admin_email: str = Field(min_length=3, max_length=320)
    admin_full_name: str | None = Field(None, max_length=200)


class ProvisionMemberRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(pattern=r"^[A-Za-z0-9_.-]+$", min_length=3, max_length=64)
    email: str = Field(min_length=3, max_length=320)
    full_name: str | None = Field(None, max_length=200)
    role: RoleValue = "engineer"


class CredentialCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=40, max_length=256)
    new_password: str = Field(min_length=12, max_length=256)


class PasswordChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=12, max_length=256)


class MemberMutationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: int = Field(gt=0)
    role: RoleValue | None = None
    membership_enabled: bool | None = None
    account_active: bool | None = None

    @model_validator(mode="after")
    def one_change(self):
        if sum(value is not None for value in (self.role, self.membership_enabled, self.account_active)) != 1:
            raise ValueError("exactly one member change is required")
        return self


class PlatformResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    organization_slug: str = Field(min_length=2, max_length=80)
    username: str = Field(min_length=3, max_length=64)


class ClosedOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")
    outcome: Literal["success", "invalid_request", "protected_not_found", "version_conflict", "unavailable"]


class IssuedCredentialResult(ClosedOutcome):
    organization: OrganizationSummary | None = None
    member: MemberSummary | None = None
    one_time_token: str | None = None
    replayed: bool = False


class MemberListResult(ClosedOutcome):
    items: list[MemberSummary] = Field(default_factory=list, max_length=100)
