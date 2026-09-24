from uuid import uuid4
import pytest

from app.models.organization import Organization, UserOrganizationMembership
from app.models.user import User
from app.schemas.onboarding import MemberMutationRequest
from app.services.onboarding_service import OnboardingService, ProtectedOnboarding
from app.services.recovery_service import RecoveryRejected, RecoveryService


def _org_for_admin(db_session, admin_user):
    membership = db_session.query(UserOrganizationMembership).filter_by(user_id=admin_user.id, is_enabled=True).one()
    return membership.organization_id


@pytest.mark.parametrize("change", [
    {"role": "engineer"},
    {"membership_enabled": False},
    {"account_active": False},
])
def test_last_administrator_cannot_remove_own_authority(db_session, admin_user, change):
    organization_id = _org_for_admin(db_session, admin_user)
    membership = db_session.query(UserOrganizationMembership).filter_by(user_id=admin_user.id, organization_id=organization_id).one()
    with pytest.raises(ProtectedOnboarding):
        OnboardingService(db_session).mutate_member(
            organization_id,
            admin_user,
            admin_user.id,
            MemberMutationRequest(expected_version=max(admin_user.version, membership.version), **change),
            uuid4(),
        )


def test_non_member_admin_identity_cannot_mutate_organization_authority(db_session, admin_user):
    organization_id = _org_for_admin(db_session, admin_user)
    actor = User(
        email="authority-witness@example.com", username="authority-witness", role="admin",
        hashed_password=admin_user.hashed_password, is_active=True, activation_pending=False,
        auth_version=1, version=1,
    )
    db_session.add(actor)
    db_session.flush()
    auto_membership = db_session.query(UserOrganizationMembership).filter_by(user_id=actor.id, organization_id=organization_id).one_or_none()
    if auto_membership is not None:
        db_session.delete(auto_membership)
        db_session.flush()
    membership = db_session.query(UserOrganizationMembership).filter_by(user_id=admin_user.id, organization_id=organization_id).one()
    with pytest.raises(ProtectedOnboarding):
        OnboardingService(db_session).mutate_member(
            organization_id, actor, admin_user.id,
            MemberMutationRequest(expected_version=max(admin_user.version, membership.version), account_active=False),
            uuid4(),
        )


def test_non_admin_service_actor_cannot_issue_human_recovery(db_session, engineer_user, admin_user):
    organization_id = _org_for_admin(db_session, admin_user)
    with pytest.raises(RecoveryRejected):
        RecoveryService(db_session).issue(
            actor=engineer_user, target=admin_user, organization_id=organization_id,
            purpose="account_recovery",
        )
