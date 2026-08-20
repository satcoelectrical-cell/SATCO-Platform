from uuid import uuid4

import pytest

from app.models.onboarding import AccountActionCredential
from app.models.organization import Organization, UserOrganizationMembership
from app.models.user import User
from app.schemas.onboarding import BootstrapOrganizationRequest, MemberMutationRequest, ProvisionMemberRequest
from app.services.onboarding_service import OnboardingConflict, OnboardingService, ProtectedOnboarding


def bootstrap_request(suffix="one"):
    return BootstrapOrganizationRequest(
        organization_name=f"Customer {suffix}",
        organization_slug=f"customer-{suffix}",
        admin_username=f"admin-{suffix}",
        admin_email=f"admin-{suffix}@example.com",
        admin_full_name="Initial Administrator",
    )


def test_bootstrap_activation_and_safe_replay(db_session):
    service = OnboardingService(db_session)
    key = uuid4()
    organization, member, token, replayed = service.bootstrap(bootstrap_request(), key)
    assert organization.slug == "customer-one"
    assert member.role == "admin" and member.activation_pending
    assert token and not replayed
    _, replay_member, replay_token, replayed = service.bootstrap(bootstrap_request(), key)
    assert replay_member.user_id == member.user_id
    assert replay_token is None and replayed
    assert db_session.query(AccountActionCredential).filter_by(user_id=member.user_id).one().token_digest != token
    service.complete_credential(token=token, new_password="new-secure-password", purpose="activation")
    user = db_session.get(User, member.user_id)
    assert user.is_active and not user.activation_pending and user.auth_version == 2
    with pytest.raises(ProtectedOnboarding):
        service.complete_credential(token=token, new_password="another-password", purpose="activation")


def test_provision_and_last_admin_guard(db_session, admin_user):
    organization_id = uuid4()
    organization = Organization(id=organization_id, name="Admin Org", slug="admin-org", is_active=True)
    db_session.add(organization)
    db_session.add(UserOrganizationMembership(user_id=admin_user.id, organization_id=organization_id, is_enabled=True, is_selected=False, version=1))
    db_session.commit()
    service = OnboardingService(db_session)
    member, token, _ = service.provision(
        organization,
        admin_user,
        ProvisionMemberRequest(username="new-engineer", email="new-engineer@example.com", role="engineer"),
        uuid4(),
    )
    assert token and member.role == "engineer"
    with pytest.raises(ProtectedOnboarding):
        service.mutate_member(
            organization_id,
            admin_user,
            admin_user.id,
            MemberMutationRequest(expected_version=1, role="engineer"),
            uuid4(),
        )


def test_idempotency_fingerprint_conflict(db_session):
    service = OnboardingService(db_session)
    key = uuid4()
    service.bootstrap(bootstrap_request("two"), key)
    with pytest.raises(OnboardingConflict):
        service.bootstrap(bootstrap_request("three"), key)
