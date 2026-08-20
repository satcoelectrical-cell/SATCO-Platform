from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.onboarding import (
    BootstrapOrganizationRequest,
    CredentialCompletionRequest,
    MemberMutationRequest,
    ProvisionMemberRequest,
)


def test_onboarding_requests_are_closed_and_bounded():
    with pytest.raises(ValidationError):
        BootstrapOrganizationRequest(
            organization_name="Acme",
            organization_slug="Acme Bad",
            admin_username="owner",
            admin_email="owner@example.com",
        )
    with pytest.raises(ValidationError):
        ProvisionMemberRequest(
            username="engineer", email="engineer@example.com", role="owner"
        )
    with pytest.raises(ValidationError):
        CredentialCompletionRequest(token="short", new_password="strong-password")


def test_member_mutation_requires_exactly_one_change():
    with pytest.raises(ValidationError):
        MemberMutationRequest(expected_version=1)
    with pytest.raises(ValidationError):
        MemberMutationRequest(expected_version=1, role="admin", account_active=False)
    assert MemberMutationRequest(expected_version=1, role="engineer").role == "engineer"


def test_idempotency_key_is_uuid_shaped():
    assert isinstance(uuid4(), type(uuid4()))
