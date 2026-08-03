from uuid import uuid4

import pytest

from app.exceptions.engineering_experience_capture import EngineeringExperienceCaptureInvalidContext
from app.models.engineering_object import EngineeringObject
from app.models.engineering_experience_capture_command import EngineeringExperienceCaptureActor
from app.models.organization import UserOrganizationMembership
from app.repositories.engineering_experience_capture_unit_of_work import (
    SqlAlchemyCaptureAuthorizationPolicy,
    SqlAlchemyCaptureContextValidator,
)


def test_authorization_is_organization_scoped(db_session, relationship_domain):
    project = relationship_domain["project"]
    owner = relationship_domain["actors"]["project_owner"]
    policy = SqlAlchemyCaptureAuthorizationPolicy(db_session)
    assert policy.authorize(
        actor=EngineeringExperienceCaptureActor(owner.id, project.organization_id),
        operation="create", project_id=project.id,
    )


def test_cross_organization_scope_is_denied(db_session, relationship_domain):
    project = relationship_domain["project"]
    owner = relationship_domain["actors"]["project_owner"]
    assert not SqlAlchemyCaptureAuthorizationPolicy(db_session).authorize(
        actor=EngineeringExperienceCaptureActor(owner.id, __import__("uuid").uuid4()),
        operation="read", project_id=project.id,
    )


def test_context_derives_control_mapping_without_client_discipline(db_session, relationship_domain):
    project = relationship_domain["project"]
    owner = relationship_domain["actors"]["project_owner"]
    workspace = relationship_domain["consumer_workspace"]
    context = SqlAlchemyCaptureContextValidator(db_session).validate(
        actor=EngineeringExperienceCaptureActor(owner.id, project.organization_id),
        project_id=project.id, workspace_id=workspace.id,
    )
    assert context["discipline"] == "electrical"


def test_inactive_user_is_denied(db_session, relationship_domain):
    domain = relationship_domain
    actor = EngineeringExperienceCaptureActor(
        domain["actors"]["inactive"].id, domain["project"].organization_id
    )
    assert not SqlAlchemyCaptureAuthorizationPolicy(db_session).authorize(
        actor=actor, operation="create", project_id=domain["project"].id
    )


def test_disabled_organization_membership_is_denied(db_session, relationship_domain):
    domain = relationship_domain
    user = domain["actors"]["project_owner"]
    membership = db_session.get(
        UserOrganizationMembership, (user.id, domain["project"].organization_id)
    )
    membership.is_selected = False
    membership.is_enabled = False
    db_session.flush()
    assert not SqlAlchemyCaptureAuthorizationPolicy(db_session).authorize(
        actor=EngineeringExperienceCaptureActor(user.id, domain["project"].organization_id),
        operation="create", project_id=domain["project"].id,
    )


def test_nonmember_organization_is_denied(db_session, relationship_domain):
    domain = relationship_domain
    user = domain["actors"]["project_owner"]
    db_session.delete(db_session.get(
        UserOrganizationMembership, (user.id, domain["project"].organization_id)
    ))
    db_session.flush()
    assert not SqlAlchemyCaptureAuthorizationPolicy(db_session).authorize(
        actor=EngineeringExperienceCaptureActor(user.id, domain["project"].organization_id),
        operation="read", project_id=domain["project"].id,
    )


def test_cross_project_and_workspace_access_is_denied(db_session, relationship_domain):
    domain = relationship_domain
    actor = EngineeringExperienceCaptureActor(
        domain["actors"]["consumer"].id, domain["project"].organization_id
    )
    policy = SqlAlchemyCaptureAuthorizationPolicy(db_session)
    assert not policy.authorize(
        actor=actor, operation="read", project_id=domain["other_project"].id,
        workspace_id=domain["other_workspace"].id,
    )
    assert not policy.authorize(
        actor=actor, operation="read", project_id=domain["project"].id,
        workspace_id=domain["unrelated_workspace"].id,
    )


def test_cross_engineering_object_context_is_denied(db_session, relationship_domain):
    domain = relationship_domain
    user = domain["actors"]["project_owner"]
    object_record = EngineeringObject(
        id=uuid4(), organization_id=domain["project"].organization_id,
        project_id=domain["project"].id,
        workspace_id=domain["consumer_workspace"].id,
        family="electrical", discipline="electrical", object_type="motor",
        lifecycle="proposed", authority_standing="draft", version=1,
        creator_id=user.id, steward_id=user.id,
    )
    db_session.add(object_record)
    db_session.flush()
    with pytest.raises(EngineeringExperienceCaptureInvalidContext):
        SqlAlchemyCaptureContextValidator(db_session).validate(
            actor=EngineeringExperienceCaptureActor(user.id, domain["project"].organization_id),
            project_id=domain["project"].id,
            workspace_id=domain["provider_workspace"].id,
            engineering_object_id=object_record.id,
        )
