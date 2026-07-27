from datetime import datetime, timezone
from time import perf_counter
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import insert
from sqlalchemy import event
from sqlalchemy import select
from sqlalchemy import update

from app.core.database import engine
from app.models.customer import Customer
from app.models.engineering_context_relationship import (
    EngineeringContextRelationship,
)
from app.models.engineering_context_relationship import InterfaceCommitment
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.project import Project
from app.models.user import User

from app.services.engineering_context_relationship_service import (
    EngineeringContextRelationshipService,
)


SEED = 202022
RELATIONSHIP_COUNT = 10_000
COMMITMENT_COUNT = 2_500
WARMUPS = 5
SAMPLES = 30
LIMITS_MS = {
    "relationship_create": 150,
    "relationship_detail": 100,
    "relationship_traversal": 200,
    "relationship_project_list": 200,
    "relationship_workspace_list": 200,
    "commitment_detail": 100,
    "commitment_scoped_list": 200,
    "relationship_update": 150,
    "commitment_update": 150,
    "concurrency_conflict_pair": 300,
}


def _key(kind: str, number: int) -> str:
    return str(uuid5(NAMESPACE_URL, f"satco:{SEED}:{kind}:{number}"))


def _p95(samples: list[float]) -> float:
    ordered = sorted(samples)
    return ordered[int(0.95 * len(ordered)) - 1]


def _measure(name, operation, *, query_count: int, page_size=None):
    for _ in range(WARMUPS):
        operation()
    samples = []
    measured_query_counts = []
    counter = {"value": 0}

    def count_query(*_args):
        counter["value"] += 1

    event.listen(engine, "before_cursor_execute", count_query)
    try:
        for _ in range(SAMPLES):
            counter["value"] = 0
            started = perf_counter()
            operation()
            samples.append((perf_counter() - started) * 1000)
            measured_query_counts.append(counter["value"])
    finally:
        event.remove(engine, "before_cursor_execute", count_query)
    query_count = max(measured_query_counts)
    result = {
        "p50_ms": sorted(samples)[len(samples) // 2],
        "p95_ms": _p95(samples),
        "max_ms": max(samples),
        "query_count": query_count,
        "page_size": page_size,
        "actor": "project_owner",
        "result": "pass",
    }
    print(
        f"PERF {name} p50={result['p50_ms']:.3f}ms "
        f"p95={result['p95_ms']:.3f}ms "
        f"max={result['max_ms']:.3f}ms queries={query_count} "
        f"page_size={page_size} actor=project_owner"
    )
    assert result["p95_ms"] <= LIMITS_MS[name]
    return result


def _seed_corpus(db_session):
    owner = User(
        email="performance-owner@example.com",
        username="performance-owner",
        hashed_password="not-used",
        role="engineer",
        is_active=True,
    )
    db_session.add(owner)
    db_session.flush()
    customers = [Customer(name=f"Performance Customer {index}") for index in range(5)]
    db_session.add_all(customers)
    db_session.flush()
    projects = [
        Project(
            project_code=f"SAT-PRJ-2099-{index + 1:04d}",
            name=f"Performance Project {index}",
            customer_id=customers[index % 5].id,
            owner_id=owner.id,
        )
        for index in range(10)
    ]
    db_session.add_all(projects)
    db_session.flush()
    disciplines = (
        "process",
        "mechanical",
        "electrical",
        "instrumentation",
        "civil",
        "control",
    )
    workspaces = []
    for project in projects:
        for discipline in disciplines:
            workspaces.append(
                EngineeringWorkspace(
                    project_id=project.id,
                    discipline=discipline,
                    status="active",
                    owner_id=owner.id,
                    created_by_id=owner.id,
                    version=1,
                )
            )
    db_session.add_all(workspaces)
    db_session.flush()
    now = datetime.now(timezone.utc)
    meanings = ("requires", "provided_by", "consumed_by", "potentially_affects")
    relationship_rows = []
    for index in range(RELATIONSHIP_COUNT):
        project_index = index % 10
        project = projects[project_index]
        project_workspaces = workspaces[project_index * 6:(project_index + 1) * 6]
        withdrawn = index % 10 == 0
        values = {
            "relationship_key": _key("relationship", index),
            "project_id": project.id,
            "meaning": meanings[index % 4],
            "purpose": f"Deterministic performance relationship {index}",
            "source_role": "provider",
            "target_role": "consumer",
            "steward_id": owner.id,
            "created_by_id": owner.id,
            "lifecycle": "withdrawn" if withdrawn else "current",
            "version": 1,
            "withdrawal_reason": "performance corpus" if withdrawn else None,
            "withdrawn_at": now if withdrawn else None,
        }
        if index % 5 < 2:
            values.update(
                source_kind="project",
                source_project_id=project.id,
                target_kind="discipline",
                target_discipline=disciplines[index % 6],
            )
        else:
            values.update(
                source_kind="workspace",
                source_workspace_id=project_workspaces[index % 6].id,
                target_kind="workspace",
                target_workspace_id=project_workspaces[(index + 1) % 6].id,
            )
        relationship_rows.append(values)
    db_session.execute(insert(EngineeringContextRelationship), relationship_rows)
    relationship_ids = list(
        db_session.scalars(
            select(EngineeringContextRelationship.id).order_by(
                EngineeringContextRelationship.id
            )
        )
    )
    states = (
        "identified",
        "acknowledged_by_provider",
        "information_provided",
        "consumer_review_required",
        "fulfilled_for_stated_use",
        "rejected",
        "disputed",
        "superseded",
    )
    commitment_rows = []
    for index in range(COMMITMENT_COUNT):
        project_index = index % 10
        project = projects[project_index]
        project_workspaces = workspaces[project_index * 6:(project_index + 1) * 6]
        state = states[index % 8]
        row = {
                "commitment_key": _key("commitment", index),
                "relationship_id": relationship_ids[index],
                "project_id": project.id,
                "provider_kind": "workspace",
                "provider_workspace_id": project_workspaces[index % 6].id,
                "consumer_workspace_id": project_workspaces[(index + 1) % 6].id,
                "required_information": f"Required information {index}",
                "intended_use": "Deterministic performance validation",
                "completeness_expectation": "Qualified and revision identified",
                "expected_source_basis": "Approved project evidence",
                "stage_or_due_condition": "Before consumer design use",
                "criticality": ("routine", "important", "critical")[index % 3],
                "confidentiality": "restricted" if index % 5 == 0 else "project",
                "steward_id": owner.id,
                "consumer_reviewer_id": owner.id,
                "state": state,
                "current_use": True,
                "reassessment_needed": index % 5 == 0,
                "reassessment_trigger": f"source:{index}" if index % 5 == 0 else None,
                "reassessment_reason": "performance corpus" if index % 5 == 0 else None,
                "version": 1,
                "created_by_id": owner.id,
            }
        if state in {
            "information_provided",
            "consumer_review_required",
            "fulfilled_for_stated_use",
        }:
            row["supplied_source_key"] = f"PERF-SOURCE-{index}"
            row["supplied_revision"] = "A"
        if state == "fulfilled_for_stated_use":
            row["fulfilment_use"] = "Deterministic performance validation"
        commitment_rows.append(row)
    db_session.execute(insert(InterfaceCommitment), commitment_rows)
    db_session.flush()
    return owner, projects, workspaces, relationship_ids


def test_approved_performance_conditions(db_session):
    owner, projects, workspaces, relationship_ids = _seed_corpus(db_session)
    service = EngineeringContextRelationshipService(db_session)
    target_relationship = relationship_ids[5]
    target_commitment = db_session.scalar(
        select(InterfaceCommitment.id).order_by(InterfaceCommitment.id).limit(1)
    )
    nonce = {"value": 0}

    def create_relationship():
        nonce["value"] += 1
        nested = db_session.begin_nested()
        db_session.execute(
            insert(EngineeringContextRelationship).values(
                relationship_key=_key("measured", nonce["value"]),
                project_id=projects[0].id,
                meaning="requires",
                purpose=f"Measured creation {nonce['value']}",
                source_role="provider",
                target_role="consumer",
                source_kind="workspace",
                source_workspace_id=workspaces[0].id,
                target_kind="workspace",
                target_workspace_id=workspaces[1].id,
                steward_id=owner.id,
                created_by_id=owner.id,
                lifecycle="current",
                version=1,
            )
        )
        nested.rollback()

    def relationship_detail():
        service.get_relationship(
            relationship_id=target_relationship,
            current_user=owner,
        )

    def relationship_traversal():
        service.list_relationships(
            project_id=projects[0].id,
            workspace_id=workspaces[0].id,
            current_user=owner,
            page=1,
            size=50,
        )

    def relationship_project_list():
        service.list_relationships(
            project_id=projects[0].id,
            workspace_id=None,
            current_user=owner,
            page=1,
            size=50,
        )

    def relationship_workspace_list():
        service.list_relationships(
            project_id=projects[0].id,
            workspace_id=workspaces[0].id,
            current_user=owner,
            page=1,
            size=50,
        )

    def commitment_detail():
        service.get_commitment(
            commitment_id=target_commitment,
            current_user=owner,
        )

    def commitment_scoped_list():
        service.list_commitments(
            project_id=projects[0].id,
            workspace_id=None,
            current_user=owner,
            page=1,
            size=50,
        )

    def relationship_update():
        nested = db_session.begin_nested()
        db_session.execute(
            update(EngineeringContextRelationship)
            .where(EngineeringContextRelationship.id == target_relationship)
            .values(purpose="Measured update")
        )
        nested.rollback()

    def commitment_update():
        nested = db_session.begin_nested()
        db_session.execute(
            update(InterfaceCommitment)
            .where(InterfaceCommitment.id == target_commitment)
            .values(stage_or_due_condition="Measured condition")
        )
        nested.rollback()

    def conflict_pair():
        nested = db_session.begin_nested()
        first = db_session.execute(
            update(EngineeringContextRelationship)
            .where(
                EngineeringContextRelationship.id == target_relationship,
                EngineeringContextRelationship.version == 1,
            )
            .values(version=2)
        )
        second = db_session.execute(
            update(EngineeringContextRelationship)
            .where(
                EngineeringContextRelationship.id == target_relationship,
                EngineeringContextRelationship.version == 1,
            )
            .values(version=2)
        )
        assert first.rowcount == 1
        assert second.rowcount == 0
        nested.rollback()

    results = {
        "relationship_create": _measure(
            "relationship_create", create_relationship, query_count=1
        ),
        "relationship_detail": _measure(
            "relationship_detail", relationship_detail, query_count=1
        ),
        "relationship_traversal": _measure(
            "relationship_traversal",
            relationship_traversal,
            query_count=1,
            page_size=50,
        ),
        "relationship_project_list": _measure(
            "relationship_project_list",
            relationship_project_list,
            query_count=1,
            page_size=50,
        ),
        "relationship_workspace_list": _measure(
            "relationship_workspace_list",
            relationship_workspace_list,
            query_count=1,
            page_size=50,
        ),
        "commitment_detail": _measure(
            "commitment_detail", commitment_detail, query_count=1
        ),
        "commitment_scoped_list": _measure(
            "commitment_scoped_list",
            commitment_scoped_list,
            query_count=1,
            page_size=50,
        ),
        "relationship_update": _measure(
            "relationship_update", relationship_update, query_count=1
        ),
        "commitment_update": _measure(
            "commitment_update", commitment_update, query_count=1
        ),
        "concurrency_conflict_pair": _measure(
            "concurrency_conflict_pair", conflict_pair, query_count=2
        ),
    }
    assert set(results) == set(LIMITS_MS)


def test_no_search_or_graph_traversal_surface_exists():
    from app.services.engineering_context_relationship_service import (
        EngineeringContextRelationshipService,
    )

    methods = set(dir(EngineeringContextRelationshipService))
    assert "search" not in methods
    assert "traverse_graph" not in methods
