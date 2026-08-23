from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import sessionmaker

from app.core.database import engine
from app.enums import ContextAuthority
from app.enums import ContextKind
from app.exceptions.engineering_context import ContextLifecycleConflict
from app.exceptions.engineering_context import ContextVersionConflict
from app.exceptions.engineering_context import InvalidContext
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.engineering_context import EngineeringContext
from app.models.engineering_context import EngineeringContextFact
from app.models.engineering_context import EngineeringContextSourceReference
from app.models.engineering_context import EngineeringContextSubjectReference
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.organization import Organization
from app.models.project import Project
from app.models.organization import UserOrganizationMembership
from app.models.user import User
from app.permissions.roles import Role
from app.services.engineering_context_service import EngineeringContextService


def _user(db_session, name):
    user = User(
        email=f"{name}@example.com",
        username=name,
        hashed_password="hashed",
        role=Role.ENGINEER.value,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _scope(db_session, name="core"):
    owner = _user(db_session, f"{name}-owner")
    customer = Customer(name=f"{name.title()} Customer")
    db_session.add(customer)
    db_session.flush()
    project = Project(
        project_code=f"SAT-PRJ-2098-{1000 + customer.id:04d}",
        name=f"{name.title()} Project",
        customer_id=customer.id,
        owner_id=owner.id,
    )
    db_session.add(project)
    db_session.flush()
    workspace = EngineeringWorkspace(
        project_id=project.id,
        discipline="electrical",
        status="active",
        owner_id=owner.id,
        created_by_id=owner.id,
        version=1,
    )
    db_session.add(workspace)
    db_session.commit()
    return owner, project, workspace


def _source(owner):
    return {
        "source_kind": "customer_document",
        "source_key": "CUST-SPEC-001",
        "source_owner_id": owner.id,
        "revision": "A",
        "confidentiality": "project",
        "applicability": "Project electrical design basis",
    }


def _fact(service, owner, project, workspace=None):
    return service.create_context(
        project_id=project.id,
        workspace_id=workspace.id if workspace else None,
        kind=ContextKind.QUALIFIED_FACT,
        authority=ContextAuthority.AUTHORITATIVE_FACT,
        owner_id=owner.id,
        steward_id=owner.id,
        current_user=owner,
        payload={
            "statement": "Customer supply is 400 V.",
            "uncertainty": "None recorded.",
        },
        subjects=[
            {
                "subject_kind": (
                    "workspace" if workspace else "project"
                ),
                (
                    "workspace_id"
                    if workspace
                    else "project_id"
                ): workspace.id if workspace else project.id,
            }
        ],
        sources=[_source(owner)],
        purpose="Electrical design basis",
    )


def test_project_and_workspace_context_are_distinct_and_traceable(
    db_session,
):
    owner, project, workspace = _scope(db_session)
    service = EngineeringContextService(db_session)

    project_context = _fact(service, owner, project)
    workspace_context = _fact(service, owner, project, workspace)

    assert project_context["id"] != workspace_context["id"]
    assert project_context["context_key"] != workspace_context["context_key"]
    assert project_context["scope"] == "project"
    assert project_context["workspace_id"] is None
    assert workspace_context["scope"] == "workspace"
    assert workspace_context["workspace_id"] == workspace.id
    assert workspace_context["project_id"] == project.id
    assert "project_name" not in workspace_context
    assert "workspace_status" not in workspace_context


def test_all_allowed_context_kinds_preserve_typed_meaning(db_session):
    owner, project, workspace = _scope(db_session, "kinds")
    service = EngineeringContextService(db_session)

    value = service.create_context(
        project_id=project.id,
        workspace_id=workspace.id,
        kind="qualified_engineering_value",
        authority="authoritative_fact",
        owner_id=owner.id,
        steward_id=owner.id,
        current_user=owner,
        payload={
            "numeric_value": "55.0",
            "unit": "kW",
            "quantity_type": "motor_rated_power",
            "tolerance_min": "54.5",
            "tolerance_max": "55.5",
            "range_min": "0",
            "range_max": "55",
            "basis": "Vendor rated output",
            "condition_type": "design",
            "condition": "Continuous duty",
            "uncertainty": "Vendor confirmation required",
        },
        subjects=[
            {
                "subject_kind": "discipline",
                "discipline": "electrical",
            }
        ],
        sources=[_source(owner)],
    )
    assumption = service.create_context(
        project_id=project.id,
        workspace_id=None,
        kind="assumption",
        authority="assumption",
        owner_id=owner.id,
        steward_id=owner.id,
        current_user=owner,
        payload={
            "statement": "Existing transformer has spare capacity.",
            "reason": "Final load list is unavailable.",
            "consequence": "Transformer sizing may require revision.",
            "confirmation_condition": "Approved load list received.",
        },
        subjects=[
            {"subject_kind": "project", "project_id": project.id}
        ],
    )
    subject = service.create_context(
        project_id=project.id,
        workspace_id=workspace.id,
        kind="subject_reference",
        authority="authoritative_fact",
        owner_id=owner.id,
        steward_id=owner.id,
        current_user=owner,
        subjects=[
            {"subject_kind": "workspace", "workspace_id": workspace.id}
        ],
    )
    source = service.create_context(
        project_id=project.id,
        workspace_id=None,
        kind="source_evidence_reference",
        authority="authoritative_fact",
        owner_id=owner.id,
        steward_id=owner.id,
        current_user=owner,
        sources=[_source(owner)],
    )

    assert value["payload"]["unit"] == "kW"
    assert str(value["payload"]["numeric_value"]) == "55.0000000000"
    assert assumption["authority"] == "assumption"
    assert subject["subjects"][0]["workspace_id"] == workspace.id
    assert source["sources"][0]["source_key"] == "CUST-SPEC-001"


@pytest.mark.parametrize(
    ("kind", "authority", "payload", "sources"),
    [
        ("derived_finding", "authoritative_fact", None, []),
        (
            "qualified_fact",
            "engineer_verified_fact",
            {"statement": "Unsupported verified claim"},
            [{"source_kind": "engineer_input"}],
        ),
        (
            "assumption",
            "authoritative_fact",
            {
                "statement": "Invalid",
                "reason": "Invalid",
                "consequence": "Invalid",
                "confirmation_condition": "Invalid",
            },
            [],
        ),
        (
            "qualified_engineering_value",
            "authoritative_fact",
            {
                "numeric_value": "10",
                "unit": "A",
                "quantity_type": "current",
            },
            [],
        ),
    ],
)
def test_unsupported_kind_authority_and_unqualified_values_are_rejected(
    db_session,
    kind,
    authority,
    payload,
    sources,
):
    owner, project, _ = _scope(db_session, f"reject-{kind[:6]}")
    service = EngineeringContextService(db_session)

    if sources:
        sources[0].update(
            {
                "source_key": "ENG-001",
                "source_owner_id": owner.id,
                "applicability": "Test",
            }
        )
    with pytest.raises(InvalidContext):
        service.create_context(
            project_id=project.id,
            workspace_id=None,
            kind=kind,
            authority=authority,
            owner_id=owner.id,
            steward_id=owner.id,
            current_user=owner,
            payload=payload,
            subjects=[
                {"subject_kind": "project", "project_id": project.id}
            ],
            sources=sources,
        )


def test_update_withdraw_restore_and_no_physical_delete(db_session):
    owner, project, _ = _scope(db_session, "lifecycle")
    service = EngineeringContextService(db_session)
    created = _fact(service, owner, project)

    updated = service.update_payload(
        context_id=created["id"],
        expected_version=1,
        values={"statement": "Customer supply is 415 V."},
        reason="Customer clarification",
        current_user=owner,
    )
    assert updated["version"] == 2
    assert updated["payload"]["statement"] == "Customer supply is 415 V."

    with pytest.raises(ContextVersionConflict):
        service.update_payload(
            context_id=created["id"],
            expected_version=1,
            values={"statement": "Stale value"},
            reason="Stale attempt",
            current_user=owner,
        )

    withdrawn = service.withdraw(
        context_id=created["id"],
        expected_version=2,
        reason="Source withdrawn",
        current_user=owner,
    )
    assert withdrawn["lifecycle"] == "withdrawn"
    with pytest.raises(ContextLifecycleConflict):
        service.update_payload(
            context_id=created["id"],
            expected_version=3,
            values={"statement": "Prohibited"},
            reason="Prohibited",
            current_user=owner,
        )
    restored = service.restore(
        context_id=created["id"],
        expected_version=3,
        reason="Source reissued",
        current_user=owner,
    )
    assert restored["lifecycle"] == "current"
    assert restored["id"] == created["id"]
    assert not hasattr(service, "delete")


def test_concurrent_updates_have_one_winner_and_one_audit():
    token = uuid4().hex[:12]
    code_suffix = str(uuid4().int % 100000000).zfill(8)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    setup = session_factory()
    test_organization_id = UUID(
        "02810000-0000-4000-8000-000000000001"
    )
    if setup.get(Organization, test_organization_id) is None:
        setup.add(
            Organization(id=test_organization_id, is_active=True)
        )
        setup.flush()
    owner = User(
        email=f"context-concurrency-owner-{token}@example.com",
        username=f"context-concurrency-owner-{token}",
        hashed_password="hashed",
        role=Role.ENGINEER.value,
        is_active=True,
    )
    customer = Customer(name=f"Context Concurrency Customer {token}")
    setup.add_all([owner, customer])
    setup.flush()
    project = Project(
        project_code=f"SAT-PRJ-2098-{code_suffix}",
        name="Context Concurrency Project",
        customer_id=customer.id,
        owner_id=owner.id,
    )
    setup.add(project)
    setup.commit()
    created = _fact(
        EngineeringContextService(setup),
        owner,
        project,
    )
    owner_id = owner.id
    customer_id = customer.id
    project_id = project.id
    setup.close()
    barrier = Barrier(2)

    def update(statement):
        session = session_factory()
        try:
            actor = session.get(User, owner_id)
            service = EngineeringContextService(session)
            barrier.wait()
            try:
                service.update_payload(
                    context_id=created["id"],
                    expected_version=1,
                    values={"statement": statement},
                    reason="Concurrent update",
                    current_user=actor,
                )
                return "updated"
            except ContextVersionConflict:
                return "conflict"
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(update, ["Concurrent A", "Concurrent B"])
        )

    verify = session_factory()
    try:
        assert sorted(results) == ["conflict", "updated"]
        assert (
            verify.query(AuditLog)
            .filter(
                AuditLog.entity == "ENGINEERING_CONTEXT",
                AuditLog.entity_id == created["id"],
                AuditLog.action == "engineering_context_updated",
            )
            .count()
            == 1
        )
    finally:
        verify.query(AuditLog).filter(
            AuditLog.entity == "ENGINEERING_CONTEXT",
            AuditLog.entity_id == created["id"],
        ).delete(synchronize_session=False)
        verify.query(EngineeringContextSourceReference).filter(
            EngineeringContextSourceReference.context_id == created["id"]
        ).delete(synchronize_session=False)
        verify.query(EngineeringContextSubjectReference).filter(
            EngineeringContextSubjectReference.context_id
            == created["id"]
        ).delete(synchronize_session=False)
        verify.query(EngineeringContextFact).filter(
            EngineeringContextFact.context_id == created["id"]
        ).delete(synchronize_session=False)
        verify.query(EngineeringContext).filter(
            EngineeringContext.id == created["id"]
        ).delete(synchronize_session=False)
        verify.query(Project).filter(Project.id == project_id).delete(
            synchronize_session=False
        )
        verify.query(Customer).filter(
            Customer.id == customer_id
        ).delete(synchronize_session=False)
        verify.query(UserOrganizationMembership).filter(
            UserOrganizationMembership.user_id == owner_id
        ).delete(synchronize_session=False)
        verify.query(User).filter(User.id == owner_id).delete(
            synchronize_session=False
        )
        verify.commit()
        verify.close()
