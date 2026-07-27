from datetime import datetime
from datetime import timezone
from math import ceil
from time import perf_counter
from uuid import uuid4

from sqlalchemy import event

from app.core.database import engine
from app.exceptions.engineering_context import ContextVersionConflict
from app.models.customer import Customer
from app.models.engineering_context import EngineeringContext
from app.models.engineering_context import EngineeringContextAssumption
from app.models.engineering_context import EngineeringContextFact
from app.models.engineering_context import EngineeringContextSourceReference
from app.models.engineering_context import EngineeringContextSubjectReference
from app.models.engineering_context import EngineeringContextValue
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.project import Project
from app.models.user import User
from app.permissions.roles import Role
from app.repositories.engineering_context_repository import (
    EngineeringContextRepository,
)
from app.services.engineering_context_service import EngineeringContextService


CONTEXT_COUNT = 10_000
ITERATIONS = 30


def _p95(samples):
    ordered = sorted(samples)
    return ordered[ceil(len(ordered) * 0.95) - 1]


def _measure(operation):
    query_count = 0

    def count_query(*args, **kwargs):
        nonlocal query_count
        query_count += 1

    operation()
    event.listen(engine, "before_cursor_execute", count_query)
    try:
        samples = []
        for _ in range(ITERATIONS):
            started = perf_counter()
            operation()
            samples.append(perf_counter() - started)
    finally:
        event.remove(engine, "before_cursor_execute", count_query)
    return {
        "p50": sorted(samples)[len(samples) // 2],
        "p95": _p95(samples),
        "maximum": max(samples),
        "query_count": query_count,
    }


def _performance_dataset(db_session):
    owner = User(
        email="context-performance-owner@example.com",
        username="context-performance-owner",
        hashed_password="hashed",
        role=Role.ENGINEER.value,
        is_active=True,
    )
    users = [owner]
    for index in range(24):
        users.append(
            User(
                email=f"context-performance-{index}@example.com",
                username=f"context-performance-{index}",
                hashed_password="hashed",
                role=Role.ENGINEER.value,
                is_active=True,
            )
        )
    db_session.add_all(users)
    db_session.flush()

    customers = [
        Customer(name=f"Context Performance Customer {index}")
        for index in range(3)
    ]
    db_session.add_all(customers)
    db_session.flush()
    projects = [
        Project(
            project_code=f"SAT-PRJ-2098-{7001 + index}",
            name=f"Context Performance Project {index}",
            customer_id=customers[index].id,
            owner_id=owner.id,
        )
        for index in range(3)
    ]
    db_session.add_all(projects)
    db_session.flush()
    disciplines = (
        "electrical",
        "instrumentation",
        "control",
        "mechanical",
        "civil",
        "process",
    )
    workspaces = [
        EngineeringWorkspace(
            project_id=projects[index // 2].id,
            discipline=disciplines[index],
            status="active",
            owner_id=owner.id,
            created_by_id=owner.id,
            version=1,
        )
        for index in range(6)
    ]
    db_session.add_all(workspaces)
    db_session.flush()

    kinds = (
        "subject_reference",
        "qualified_fact",
        "qualified_engineering_value",
        "assumption",
        "source_evidence_reference",
    )
    now = datetime.now(timezone.utc)
    context_rows = []
    for index in range(CONTEXT_COUNT):
        workspace_scoped = index % 10 >= 6
        project = projects[index % 3]
        workspace = (
            workspaces[(index % 3) * 2 + (index % 2)]
            if workspace_scoped
            else None
        )
        kind = kinds[index % len(kinds)]
        withdrawn = index % 10 == 0
        context_rows.append(
            {
                "context_key": str(uuid4()),
                "kind": kind,
                "scope": "workspace" if workspace else "project",
                "project_id": project.id,
                "workspace_id": workspace.id if workspace else None,
                "owner_id": owner.id,
                "steward_id": owner.id,
                "created_by_id": owner.id,
                "authority": (
                    "assumption"
                    if kind == "assumption"
                    else "authoritative_fact"
                ),
                "lifecycle": "withdrawn" if withdrawn else "current",
                "purpose": "Deterministic performance validation",
                "version": 1,
                "withdrawal_reason": (
                    "Performance lifecycle distribution"
                    if withdrawn
                    else None
                ),
                "withdrawn_at": now if withdrawn else None,
            }
        )
    db_session.bulk_insert_mappings(EngineeringContext, context_rows)
    db_session.flush()
    contexts = (
        db_session.query(EngineeringContext)
        .order_by(EngineeringContext.id)
        .all()
    )

    facts = []
    values = []
    assumptions = []
    subjects = []
    sources = []
    for index, context in enumerate(contexts):
        if context.kind == "qualified_fact":
            facts.append(
                {
                    "context_id": context.id,
                    "statement": f"Qualified fact {index}",
                    "uncertainty": "Synthetic",
                }
            )
        elif context.kind == "qualified_engineering_value":
            values.append(
                {
                    "context_id": context.id,
                    "numeric_value": index,
                    "unit": "unit",
                    "quantity_type": "synthetic_quantity",
                    "basis": "Deterministic performance data",
                    "condition_type": "design",
                    "condition": "Synthetic condition",
                    "uncertainty": "Synthetic",
                }
            )
        elif context.kind == "assumption":
            assumptions.append(
                {
                    "context_id": context.id,
                    "statement": f"Assumption {index}",
                    "reason": "Synthetic",
                    "consequence": "Synthetic",
                    "confirmation_condition": "Synthetic",
                }
            )

        project = projects[index % 3]
        workspace_scoped = context.workspace_id is not None
        subjects.append(
            {
                "context_id": context.id,
                "subject_kind": (
                    "workspace" if workspace_scoped else "project"
                ),
                "subject_project_id": (
                    None if workspace_scoped else project.id
                ),
                "subject_workspace_id": context.workspace_id,
                "discipline": None,
            }
        )
        subjects.append(
            {
                "context_id": context.id,
                "subject_kind": "discipline",
                "subject_project_id": None,
                "subject_workspace_id": None,
                "discipline": disciplines[index % len(disciplines)],
            }
        )

        source_total = 2 if index % 2 else 1
        for source_index in range(source_total):
            restricted = (index + source_index) % 10 == 0
            sources.append(
                {
                    "context_id": context.id,
                    "source_kind": "engineer_input",
                    "source_key": f"PERF-{index}-{source_index}",
                    "source_owner_id": (
                        owner.id if restricted else None
                    ),
                    "revision": "1",
                    "confidentiality": (
                        "restricted"
                        if restricted
                        else (
                            "workspace"
                            if workspace_scoped
                            else "project"
                        )
                    ),
                    "applicability": "Synthetic performance scope",
                }
            )

    db_session.bulk_insert_mappings(EngineeringContextFact, facts)
    db_session.bulk_insert_mappings(EngineeringContextValue, values)
    db_session.bulk_insert_mappings(
        EngineeringContextAssumption,
        assumptions,
    )
    db_session.bulk_insert_mappings(
        EngineeringContextSubjectReference,
        subjects,
    )
    db_session.bulk_insert_mappings(
        EngineeringContextSourceReference,
        sources,
    )
    db_session.commit()
    return owner, projects, workspaces, contexts


def test_approved_context_performance_baseline(db_session):
    owner, projects, workspaces, contexts = _performance_dataset(
        db_session
    )
    current_fact = next(
        context
        for context in contexts
        if context.kind == "qualified_fact"
        and context.lifecycle == "current"
    )
    owner_id = owner.id
    project_ids = [project.id for project in projects]
    workspace_ids = [workspace.id for workspace in workspaces]
    current_fact_id = current_fact.id

    # Measure normal request behavior, not fixture construction overhead
    # from retaining all 10,000 inserted ORM instances in the identity map.
    db_session.expunge_all()
    owner = db_session.get(User, owner_id)
    projects = [
        db_session.get(Project, project_id)
        for project_id in project_ids
    ]
    workspaces = [
        db_session.get(EngineeringWorkspace, workspace_id)
        for workspace_id in workspace_ids
    ]
    current_fact = db_session.get(EngineeringContext, current_fact_id)
    repository = EngineeringContextRepository(db_session)
    service = EngineeringContextService(db_session)

    detail = _measure(
        lambda: repository.get_visible_by_id(current_fact.id, owner)
    )
    project_page = _measure(
        lambda: repository.list_for_scope(
            project_id=projects[0].id,
            workspace_id=None,
            current_user=owner,
            page=1,
            size=100,
            include_withdrawn=False,
        )
    )
    workspace_page = _measure(
        lambda: repository.list_for_scope(
            project_id=workspaces[0].project_id,
            workspace_id=workspaces[0].id,
            current_user=owner,
            page=1,
            size=100,
            include_withdrawn=False,
        )
    )

    version = current_fact.version

    def successful_update():
        nonlocal version
        service.update_payload(
            context_id=current_fact.id,
            expected_version=version,
            values={"statement": f"Measured version {version + 1}"},
            reason="Performance measurement",
            current_user=owner,
        )
        version += 1

    update = _measure(successful_update)

    def stale_update():
        try:
            service.update_payload(
                context_id=current_fact.id,
                expected_version=1,
                values={"statement": "Stale performance attempt"},
                reason="Performance measurement",
                current_user=owner,
            )
        except ContextVersionConflict:
            pass
        else:
            raise AssertionError("Stale update unexpectedly succeeded")

    conflict = _measure(stale_update)
    report = {
        "environment": "backend container / PostgreSQL 17",
        "dataset_seed": "deterministic-index-sequence",
        "context_count": CONTEXT_COUNT,
        "iterations": ITERATIONS,
        "detail": detail,
        "project_page": project_page,
        "workspace_page": workspace_page,
        "successful_update": update,
        "stale_conflict": conflict,
        "claim_boundary": "tested environment and dataset only",
    }
    print(report)

    assert detail["p95"] <= 0.150
    assert project_page["p95"] <= 0.300
    assert workspace_page["p95"] <= 0.300
    assert update["p95"] <= 0.250
    assert conflict["p95"] <= 0.250
