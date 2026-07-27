import pytest

from app.exceptions.engineering_context import ContextNotFound
from app.exceptions.engineering_context import ContextVersionConflict
from app.exceptions.engineering_context import InvalidContext
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.engineering_context import EngineeringContext
from app.models.project import Project
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


def _project(db_session, owner):
    customer = Customer(name="Context Audit Customer")
    db_session.add(customer)
    db_session.flush()
    project = Project(
        project_code="SAT-PRJ-2098-4001",
        name="Context Audit Project",
        customer_id=customer.id,
        owner_id=owner.id,
    )
    db_session.add(project)
    db_session.commit()
    return project


def _create(service, owner, project):
    return service.create_context(
        project_id=project.id,
        workspace_id=None,
        kind="qualified_fact",
        authority="authoritative_fact",
        owner_id=owner.id,
        steward_id=owner.id,
        current_user=owner,
        payload={"statement": "Ambient temperature is 40 degC."},
        subjects=[
            {"subject_kind": "project", "project_id": project.id}
        ],
        sources=[
            {
                "source_kind": "customer_document",
                "source_key": "ENV-001",
                "source_owner_id": owner.id,
                "revision": "A",
                "applicability": "Project environment",
            }
        ],
    )


def _audit_actions(db_session, context_id):
    return [
        row.action
        for row in (
            db_session.query(AuditLog)
            .filter(
                AuditLog.entity == "ENGINEERING_CONTEXT",
                AuditLog.entity_id == context_id,
            )
            .order_by(AuditLog.id)
            .all()
        )
    ]


def test_successful_material_actions_create_complete_audit_evidence(
    db_session,
):
    owner = _user(db_session, "context-audit-owner")
    replacement = _user(db_session, "context-audit-replacement")
    project = _project(db_session, owner)
    service = EngineeringContextService(db_session)
    context = _create(service, owner, project)

    updated = service.update_payload(
        context_id=context["id"],
        expected_version=1,
        values={"statement": "Ambient temperature is 45 degC."},
        reason="Customer revision",
        current_user=owner,
    )
    linked = service.add_source(
        context_id=context["id"],
        expected_version=updated["version"],
        source={
            "source_kind": "site_survey",
            "source_key": "SITE-001",
            "source_owner_id": owner.id,
            "revision": "1",
            "applicability": "Outdoor installation area",
        },
        reason="Site evidence added",
        current_user=owner,
    )
    changed = service.change_responsibility(
        context_id=context["id"],
        expected_version=linked["version"],
        owner_id=replacement.id,
        steward_id=None,
        reason="Maintenance responsibility changed",
        current_user=owner,
    )
    withdrawn = service.withdraw(
        context_id=context["id"],
        expected_version=changed["version"],
        reason="Customer instruction withdrawn",
        current_user=owner,
    )
    service.restore(
        context_id=context["id"],
        expected_version=withdrawn["version"],
        reason="Customer instruction reissued",
        current_user=owner,
    )

    assert _audit_actions(db_session, context["id"]) == [
        "engineering_context_created",
        "engineering_context_updated",
        "engineering_context_source_linked",
        "engineering_context_owner_changed",
        "engineering_context_withdrawn",
        "engineering_context_restored",
    ]
    rows = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.entity == "ENGINEERING_CONTEXT",
            AuditLog.entity_id == context["id"],
        )
        .all()
    )
    assert all(row.user_id == owner.id for row in rows)
    assert all(row.details["project_id"] == project.id for row in rows)
    assert all("version" in row.details for row in rows)


def test_failed_validation_authorization_and_concurrency_create_no_audit(
    db_session,
):
    owner = _user(db_session, "context-failed-owner")
    unrelated = _user(db_session, "context-failed-unrelated")
    project = _project(db_session, owner)
    service = EngineeringContextService(db_session)
    context = _create(service, owner, project)
    baseline = len(_audit_actions(db_session, context["id"]))

    with pytest.raises(InvalidContext):
        service.update_payload(
            context_id=context["id"],
            expected_version=1,
            values={"unsupported": "value"},
            reason="Invalid",
            current_user=owner,
        )
    assert len(_audit_actions(db_session, context["id"])) == baseline

    with pytest.raises(ContextNotFound):
        service.update_payload(
            context_id=context["id"],
            expected_version=1,
            values={"statement": "Unauthorized"},
            reason="Unauthorized",
            current_user=unrelated,
        )
    assert len(_audit_actions(db_session, context["id"])) == baseline

    service.update_payload(
        context_id=context["id"],
        expected_version=1,
        values={"statement": "Committed"},
        reason="Valid",
        current_user=owner,
    )
    after_success = len(_audit_actions(db_session, context["id"]))
    assert after_success == baseline + 1

    with pytest.raises(ContextVersionConflict):
        service.update_payload(
            context_id=context["id"],
            expected_version=1,
            values={"statement": "Stale"},
            reason="Stale",
            current_user=owner,
        )
    assert len(_audit_actions(db_session, context["id"])) == after_success


def test_audit_failure_rolls_back_context_creation(
    db_session,
    monkeypatch,
):
    owner = _user(db_session, "context-audit-rollback")
    project = _project(db_session, owner)
    service = EngineeringContextService(db_session)
    context_count = db_session.query(EngineeringContext).count()
    audit_count = db_session.query(AuditLog).count()

    def fail_audit(**kwargs):
        raise RuntimeError("forced audit failure")

    monkeypatch.setattr(
        "app.services.engineering_context_service.create_audit_log",
        fail_audit,
    )
    with pytest.raises(RuntimeError, match="forced audit failure"):
        _create(service, owner, project)

    assert db_session.query(EngineeringContext).count() == context_count
    assert db_session.query(AuditLog).count() == audit_count
