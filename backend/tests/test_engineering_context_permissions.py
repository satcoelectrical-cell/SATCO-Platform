import pytest

from app.exceptions.engineering_context import ContextForbidden
from app.exceptions.engineering_context import ContextNotFound
from app.exceptions.engineering_context import InvalidContext
from app.exceptions.engineering_context import InvalidContextResponsibility
from app.models.customer import Customer
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.engineering_workspace import EngineeringWorkspaceMember
from app.models.project import Project
from app.models.user import User
from app.permissions.roles import Role
from app.services.engineering_context_service import EngineeringContextService


def _user(db_session, name, *, active=True, role=Role.ENGINEER):
    user = User(
        email=f"{name}@example.com",
        username=name,
        hashed_password="hashed",
        role=role.value,
        is_active=active,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def context_permissions(db_session):
    users = {
        name: _user(db_session, f"context-{name}")
        for name in (
            "project_owner",
            "project_assignee",
            "workspace_owner",
            "workspace_assignee",
            "collaborator",
            "context_owner",
            "steward",
            "other_workspace",
            "unrelated",
        )
    }
    users["admin"] = _user(
        db_session,
        "context-admin",
        role=Role.ADMIN,
    )
    users["inactive"] = _user(
        db_session,
        "context-inactive",
        active=False,
    )
    customer = Customer(name="Context Permission Customer")
    other_customer = Customer(name="Other Context Customer")
    db_session.add_all([customer, other_customer])
    db_session.flush()
    project = Project(
        project_code="SAT-PRJ-2098-3001",
        name="Context Permission Project",
        customer_id=customer.id,
        owner_id=users["project_owner"].id,
        primary_assignee_id=users["project_assignee"].id,
    )
    other_project = Project(
        project_code="SAT-PRJ-2098-3002",
        name="Other Context Project",
        customer_id=other_customer.id,
        owner_id=users["unrelated"].id,
    )
    db_session.add_all([project, other_project])
    db_session.flush()
    workspace = EngineeringWorkspace(
        project_id=project.id,
        discipline="instrumentation",
        status="active",
        owner_id=users["workspace_owner"].id,
        primary_assignee_id=users["workspace_assignee"].id,
        created_by_id=users["project_owner"].id,
        version=1,
    )
    other_workspace = EngineeringWorkspace(
        project_id=project.id,
        discipline="control",
        status="active",
        owner_id=users["other_workspace"].id,
        created_by_id=users["project_owner"].id,
        version=1,
    )
    db_session.add_all([workspace, other_workspace])
    db_session.flush()
    db_session.add(
        EngineeringWorkspaceMember(
            workspace_id=workspace.id,
            user_id=users["collaborator"].id,
            added_by_id=users["workspace_owner"].id,
        )
    )
    db_session.commit()
    service = EngineeringContextService(db_session)
    context = service.create_context(
        project_id=project.id,
        workspace_id=workspace.id,
        kind="qualified_fact",
        authority="authoritative_fact",
        owner_id=users["context_owner"].id,
        steward_id=users["project_owner"].id,
        current_user=users["project_owner"],
        payload={"statement": "Instrument air is available."},
        subjects=[
            {"subject_kind": "workspace", "workspace_id": workspace.id}
        ],
        sources=[
            {
                "source_kind": "customer_document",
                "source_key": "CUST-INST-001",
                "source_owner_id": users["project_owner"].id,
                "revision": "1",
                "confidentiality": "workspace",
                "applicability": "Instrumentation Workspace",
            }
        ],
    )
    return {
        "users": users,
        "project": project,
        "other_project": other_project,
        "workspace": workspace,
        "other_workspace": other_workspace,
        "context": context,
    }


@pytest.mark.parametrize(
    "persona",
    [
        "admin",
        "project_owner",
        "project_assignee",
        "workspace_owner",
        "workspace_assignee",
        "collaborator",
        "context_owner",
    ],
)
def test_authorized_personas_can_view_scoped_context(
    db_session,
    context_permissions,
    persona,
):
    service = EngineeringContextService(db_session)
    result = service.get(
        context_permissions["context"]["id"],
        context_permissions["users"][persona],
    )
    assert result["project_id"] == context_permissions["project"].id
    assert (
        result["workspace_id"]
        == context_permissions["workspace"].id
    )


def test_steward_has_explicit_access_without_ownership(
    db_session,
    context_permissions,
):
    context = context_permissions["context"]
    project_owner = context_permissions["users"]["project_owner"]
    steward = context_permissions["users"]["steward"]
    service = EngineeringContextService(db_session)
    changed = service.change_responsibility(
        context_id=context["id"],
        expected_version=1,
        owner_id=None,
        steward_id=steward.id,
        reason="Discipline stewardship assigned",
        current_user=project_owner,
    )
    assert changed["steward_id"] == steward.id
    assert service.get(context["id"], steward)["id"] == context["id"]


def test_unrelated_and_other_workspace_identifiers_do_not_disclose(
    db_session,
    context_permissions,
):
    service = EngineeringContextService(db_session)
    context_id = context_permissions["context"]["id"]
    for persona in ("unrelated", "other_workspace"):
        with pytest.raises(ContextNotFound):
            service.get(
                context_id,
                context_permissions["users"][persona],
            )
    unrelated_page = service.list_for_scope(
        project_id=context_permissions["project"].id,
        workspace_id=context_permissions["workspace"].id,
        current_user=context_permissions["users"]["unrelated"],
    )
    assert unrelated_page["items"] == []
    assert unrelated_page["total"] == 0
    owner_page = service.list_for_scope(
        project_id=context_permissions["project"].id,
        workspace_id=context_permissions["workspace"].id,
        current_user=context_permissions["users"]["context_owner"],
    )
    assert owner_page["total"] == 1


def test_cross_project_and_cross_workspace_creation_is_denied(
    db_session,
    context_permissions,
):
    data = context_permissions
    service = EngineeringContextService(db_session)
    unrelated = data["users"]["unrelated"]
    collaborator = data["users"]["collaborator"]

    with pytest.raises(ContextForbidden):
        service.create_context(
            project_id=data["project"].id,
            workspace_id=data["workspace"].id,
            kind="assumption",
            authority="assumption",
            owner_id=unrelated.id,
            steward_id=unrelated.id,
            current_user=unrelated,
            payload={
                "statement": "Unauthorized",
                "reason": "Unauthorized",
                "consequence": "Unauthorized",
                "confirmation_condition": "Unauthorized",
            },
            subjects=[],
        )

    with pytest.raises(InvalidContext):
        service.create_context(
            project_id=data["other_project"].id,
            workspace_id=data["workspace"].id,
            kind="assumption",
            authority="assumption",
            owner_id=collaborator.id,
            steward_id=collaborator.id,
            current_user=collaborator,
            payload={
                "statement": "Cross Project",
                "reason": "Invalid scope",
                "consequence": "Leakage",
                "confirmation_condition": "Never",
            },
        )

    with pytest.raises(ContextForbidden):
        service.create_context(
            project_id=data["project"].id,
            workspace_id=data["other_workspace"].id,
            kind="assumption",
            authority="assumption",
            owner_id=collaborator.id,
            steward_id=collaborator.id,
            current_user=collaborator,
            payload={
                "statement": "Cross Workspace",
                "reason": "Invalid scope",
                "consequence": "Leakage",
                "confirmation_condition": "Never",
            },
        )


def test_restricted_source_requires_exact_source_owner(
    db_session,
    context_permissions,
):
    data = context_permissions
    actor = data["users"]["project_owner"]
    service = EngineeringContextService(db_session)
    context = service.create_context(
        project_id=data["project"].id,
        workspace_id=None,
        kind="qualified_fact",
        authority="authoritative_fact",
        owner_id=actor.id,
        steward_id=actor.id,
        current_user=actor,
        payload={"statement": "Restricted customer instruction."},
        sources=[
            {
                "source_kind": "customer_document",
                "source_key": "CUST-RESTRICTED",
                "source_owner_id": actor.id,
                "confidentiality": "restricted",
                "applicability": "Project only",
            }
        ],
    )
    assert service.get(context["id"], actor)["id"] == context["id"]
    with pytest.raises(ContextNotFound):
        service.get(context["id"], data["users"]["admin"])


def test_inactive_or_missing_responsibility_is_rejected(
    db_session,
    context_permissions,
):
    data = context_permissions
    service = EngineeringContextService(db_session)
    actor = data["users"]["project_owner"]
    for user_id in (
        data["users"]["inactive"].id,
        99999999,
    ):
        with pytest.raises(InvalidContextResponsibility):
            service.create_context(
                project_id=data["project"].id,
                workspace_id=None,
                kind="assumption",
                authority="assumption",
                owner_id=user_id,
                steward_id=actor.id,
                current_user=actor,
                payload={
                    "statement": "Responsibility check",
                    "reason": "Test",
                    "consequence": "Test",
                    "confirmation_condition": "Test",
                },
            )
    with pytest.raises(ContextNotFound):
        service.get(
            data["context"]["id"],
            data["users"]["inactive"],
        )


def test_owner_and_admin_do_not_gain_steward_authority(
    db_session,
    context_permissions,
):
    data = context_permissions
    service = EngineeringContextService(db_session)
    context = data["context"]
    for persona in ("context_owner", "admin"):
        with pytest.raises(ContextForbidden):
            service.change_authority(
                context_id=context["id"],
                expected_version=1,
                authority="authoritative_fact",
                reason="No competence inference",
                current_user=data["users"][persona],
            )
