from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker

from app.core.database import engine
from app.exceptions.engineering_context_relationship import (
    CommitmentVersionConflict,
    RelationshipVersionConflict,
)
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.engineering_context_relationship import (
    EngineeringContextRelationship,
    InterfaceCommitment,
)
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.project import Project
from app.models.organization import UserOrganizationMembership
from app.models.user import User
from app.services.engineering_context_relationship_service import (
    EngineeringContextRelationshipService,
)


SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)


@dataclass(frozen=True)
class RaceDomain:
    relationship_id: int
    commitment_id: int
    project_id: int
    customer_id: int
    owner_id: int
    provider_user_id: int
    consumer_user_id: int
    steward_a_id: int
    steward_b_id: int
    workspace_ids: tuple[int, ...]
    provider_workspace_id: int
    consumer_workspace_id: int
    alt_provider_workspace_ids: tuple[int, int]
    alt_consumer_workspace_ids: tuple[int, int]


def _new_user(session, suffix: str, label: str) -> User:
    user = User(
        email=f"{label}-{suffix}@example.com",
        username=f"{label}-{suffix}",
        hashed_password="unused",
        role="engineer",
        is_active=True,
    )
    session.add(user)
    session.flush()
    return user


def _build_domain() -> RaceDomain:
    suffix = uuid4().hex[:8]
    session = SessionFactory()

    owner = _new_user(session, suffix, "owner")
    provider = _new_user(session, suffix, "provider")
    consumer = _new_user(session, suffix, "consumer")
    steward_a = _new_user(session, suffix, "steward-a")
    steward_b = _new_user(session, suffix, "steward-b")
    alt_provider_a = _new_user(session, suffix, "alt-provider-a")
    alt_provider_b = _new_user(session, suffix, "alt-provider-b")
    alt_consumer_a = _new_user(session, suffix, "alt-consumer-a")
    alt_consumer_b = _new_user(session, suffix, "alt-consumer-b")

    users = (
        owner,
        provider,
        consumer,
        steward_a,
        steward_b,
        alt_provider_a,
        alt_provider_b,
        alt_consumer_a,
        alt_consumer_b,
    )

    customer = Customer(name=f"Concurrency Customer {suffix}")
    session.add(customer)
    session.flush()

    project = Project(
        project_code=f"SAT-PRJ-2094-{customer.id + 4000:04d}",
        name=f"Concurrency Project {suffix}",
        customer_id=customer.id,
        owner_id=owner.id,
    )
    session.add(project)
    session.flush()

    workspace_specs = (
        ("mechanical", provider),
        ("electrical", consumer),
        ("civil", alt_provider_a),
        ("process", alt_provider_b),
        ("control", alt_consumer_a),
        ("instrumentation", alt_consumer_b),
    )

    workspaces = []
    for discipline, workspace_owner in workspace_specs:
        workspace = EngineeringWorkspace(
            project_id=project.id,
            discipline=discipline,
            status="active",
            owner_id=workspace_owner.id,
            created_by_id=owner.id,
            version=1,
        )
        session.add(workspace)
        session.flush()
        workspaces.append(workspace)

    session.commit()

    service = EngineeringContextRelationshipService(session)

    relationship = service.create_relationship(
        data={
            "project_id": project.id,
            "meaning": "requires",
            "purpose": "Synchronized concurrency relationship",
            "source_role": "provider",
            "target_role": "consumer",
            "source": {
                "kind": "workspace",
                "workspace_id": workspaces[0].id,
            },
            "target": {
                "kind": "workspace",
                "workspace_id": workspaces[1].id,
            },
            "steward_id": owner.id,
        },
        current_user=owner,
    )
    session.commit()

    commitment = service.create_commitment(
        data={
            "relationship_id": relationship["id"],
            "provider_kind": "workspace",
            "provider_workspace_id": workspaces[0].id,
            "consumer_workspace_id": workspaces[1].id,
            "required_information": "Governed engineering information",
            "intended_use": "Consumer engineering design",
            "completeness_expectation": "Complete and revision identified",
            "expected_source_basis": "Governed project evidence",
            "stage_or_due_condition": "Before consumer design use",
            "criticality": "important",
            "confidentiality": "project",
            "steward_id": owner.id,
            "consumer_reviewer_id": consumer.id,
            "external_review_required": False,
        },
        current_user=owner,
    )
    session.commit()

    domain = RaceDomain(
        relationship_id=relationship["id"],
        commitment_id=commitment["id"],
        project_id=project.id,
        customer_id=customer.id,
        owner_id=owner.id,
        provider_user_id=provider.id,
        consumer_user_id=consumer.id,
        steward_a_id=steward_a.id,
        steward_b_id=steward_b.id,
        workspace_ids=tuple(workspace.id for workspace in workspaces),
        provider_workspace_id=workspaces[0].id,
        consumer_workspace_id=workspaces[1].id,
        alt_provider_workspace_ids=(workspaces[2].id, workspaces[3].id),
        alt_consumer_workspace_ids=(workspaces[4].id, workspaces[5].id),
    )

    # Keep scalar identifiers only; independent race sessions load their own rows.
    _ = tuple(user.id for user in users)
    session.close()
    return domain


def _load_user(session, user_id: int) -> User:
    user = session.get(User, user_id)
    assert user is not None
    return user


def _audit_count(session, entity: str, entity_id: int) -> int:
    return (
        session.query(AuditLog)
        .filter(
            AuditLog.entity == entity,
            AuditLog.entity_id == entity_id,
        )
        .count()
    )


def _prepare_commitment(domain: RaceDomain, case_name: str) -> int:
    session = SessionFactory()
    try:
        service = EngineeringContextRelationshipService(session)
        provider = _load_user(session, domain.provider_user_id)

        commitment = service.get_commitment(
            commitment_id=domain.commitment_id,
            current_user=_load_user(session, domain.owner_id),
        )

        if case_name in {
            "information_provided",
            "fulfilment",
            "source_revision",
        }:
            commitment = service.transition_commitment(
                commitment_id=domain.commitment_id,
                target="acknowledged_by_provider",
                expected_version=commitment["version"],
                reason="Prepare synchronized concurrency test",
                current_user=provider,
            )
            session.commit()

        if case_name in {"fulfilment", "source_revision"}:
            commitment = service.transition_commitment(
                commitment_id=domain.commitment_id,
                target="information_provided",
                expected_version=commitment["version"],
                reason="Prepare supplied information",
                supplied_source_key="SRC-BASE",
                supplied_revision="A",
                current_user=provider,
            )
            session.commit()

        return commitment["version"]
    finally:
        session.close()


def _run_two_writers(
    *,
    actor_id: int,
    expected_version: int,
    mutation,
    conflict_type,
):
    barrier = Barrier(2)

    def writer(candidate):
        session = SessionFactory()
        try:
            service = EngineeringContextRelationshipService(session)
            actor = _load_user(session, actor_id)
            barrier.wait()
            try:
                result = mutation(
                    service,
                    actor,
                    expected_version,
                    candidate,
                )
                session.commit()
                return ("success", result)
            except conflict_type:
                session.rollback()
                return ("conflict", None)
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(writer, ("A", "B")))

    assert sorted(result[0] for result in results) == [
        "conflict",
        "success",
    ]
    success = next(result[1] for result in results if result[0] == "success")
    return success


def _cleanup_domain(domain: RaceDomain) -> None:
    session = SessionFactory()
    try:
        session.query(AuditLog).filter(
            (
                (AuditLog.entity == "CONTEXT_RELATIONSHIP")
                & (AuditLog.entity_id == domain.relationship_id)
            )
            | (
                (AuditLog.entity == "INTERFACE_COMMITMENT")
                & (AuditLog.entity_id == domain.commitment_id)
            )
        ).delete(synchronize_session=False)

        session.query(InterfaceCommitment).filter(
            InterfaceCommitment.id == domain.commitment_id
        ).delete(synchronize_session=False)

        session.query(EngineeringContextRelationship).filter(
            EngineeringContextRelationship.id == domain.relationship_id
        ).delete(synchronize_session=False)

        session.query(EngineeringWorkspace).filter(
            EngineeringWorkspace.id.in_(domain.workspace_ids)
        ).delete(synchronize_session=False)

        session.query(Project).filter(
            Project.id == domain.project_id
        ).delete(synchronize_session=False)

        session.query(Customer).filter(
            Customer.id == domain.customer_id
        ).delete(synchronize_session=False)

        user_ids = {
            domain.owner_id,
            domain.provider_user_id,
            domain.consumer_user_id,
            domain.steward_a_id,
            domain.steward_b_id,
        }
        workspace_owner_ids = (
            session.query(EngineeringWorkspace.owner_id)
            .filter(EngineeringWorkspace.id.in_(domain.workspace_ids))
            .all()
        )
        user_ids.update(owner_id for (owner_id,) in workspace_owner_ids)

        session.query(UserOrganizationMembership).filter(
            UserOrganizationMembership.user_id.in_(user_ids)
        ).delete(synchronize_session=False)

        # Workspaces have already been deleted, so recover remaining test users
        # by their deterministic email suffix through the Project creator group.
        session.query(User).filter(
            User.id.in_(user_ids)
        ).delete(synchronize_session=False)

        # Remove any remaining concurrency users associated with this project
        # through the test-specific username prefixes.
        session.query(User).filter(
            User.username.like("%owner%")
        ).filter(User.id >= min(user_ids)).delete(synchronize_session=False)

        session.commit()
    finally:
        session.close()


@pytest.mark.parametrize(
    ("case_name", "actor_field", "expected_action"),
    [
        (
            "metadata",
            "owner_id",
            "CONTEXT_RELATIONSHIP_METADATA_CHANGED",
        ),
        (
            "lifecycle",
            "owner_id",
            "CONTEXT_RELATIONSHIP_WITHDRAWN",
        ),
    ],
)
def test_synchronized_relationship_mutations_have_one_winner(
    case_name,
    actor_field,
    expected_action,
):
    domain = _build_domain()
    verification = SessionFactory()

    try:
        relationship_before = verification.get(
            EngineeringContextRelationship,
            domain.relationship_id,
        )
        assert relationship_before is not None

        baseline_version = relationship_before.version
        baseline_audits = _audit_count(
            verification,
            "CONTEXT_RELATIONSHIP",
            domain.relationship_id,
        )
        source_workspace_id = relationship_before.source_workspace_id
        target_workspace_id = relationship_before.target_workspace_id
        project_id = relationship_before.project_id
        verification.close()

        if case_name == "metadata":
            def mutation(service, actor, expected_version, candidate):
                return service.update_relationship_metadata(
                    relationship_id=domain.relationship_id,
                    expected_version=expected_version,
                    purpose=f"Concurrent purpose {candidate}",
                    applicability=f"Concurrent applicability {candidate}",
                    reason=f"Writer {candidate}",
                    current_user=actor,
                )
        else:
            def mutation(service, actor, expected_version, candidate):
                return service.set_relationship_lifecycle(
                    relationship_id=domain.relationship_id,
                    target="withdrawn",
                    expected_version=expected_version,
                    reason=f"Writer {candidate}",
                    current_user=actor,
                )

        success = _run_two_writers(
            actor_id=getattr(domain, actor_field),
            expected_version=baseline_version,
            mutation=mutation,
            conflict_type=RelationshipVersionConflict,
        )

        verification = SessionFactory()
        relationship_after = verification.get(
            EngineeringContextRelationship,
            domain.relationship_id,
        )
        assert relationship_after is not None
        assert relationship_after.version == baseline_version + 1
        assert success["version"] == baseline_version + 1
        assert relationship_after.project_id == project_id
        assert relationship_after.source_workspace_id == source_workspace_id
        assert relationship_after.target_workspace_id == target_workspace_id
        assert (
            _audit_count(
                verification,
                "CONTEXT_RELATIONSHIP",
                domain.relationship_id,
            )
            == baseline_audits + 1
        )
        assert (
            verification.query(AuditLog)
            .filter(
                AuditLog.entity == "CONTEXT_RELATIONSHIP",
                AuditLog.entity_id == domain.relationship_id,
                AuditLog.action == expected_action,
            )
            .count()
            == 1
        )

        if case_name == "metadata":
            assert relationship_after.purpose in {
                "Concurrent purpose A",
                "Concurrent purpose B",
            }
        else:
            assert relationship_after.lifecycle == "withdrawn"
    finally:
        verification.close()
        _cleanup_domain(domain)


COMMITMENT_RACE_CASES = [
    "provider_change",
    "consumer_change",
    "information_provided",
    "fulfilment",
    "withdrawal",
    "responsibility",
    "source_revision",
    "reassessment",
]


@pytest.mark.parametrize("case_name", COMMITMENT_RACE_CASES)
def test_synchronized_commitment_mutations_have_one_winner(case_name):
    domain = _build_domain()
    verification = SessionFactory()

    try:
        baseline_version = _prepare_commitment(domain, case_name)

        commitment_before = verification.get(
            InterfaceCommitment,
            domain.commitment_id,
        )
        assert commitment_before is not None
        verification.refresh(commitment_before)

        baseline_audits = _audit_count(
            verification,
            "INTERFACE_COMMITMENT",
            domain.commitment_id,
        )
        relationship_id = commitment_before.relationship_id
        project_id = commitment_before.project_id
        original_provider = commitment_before.provider_workspace_id
        original_consumer = commitment_before.consumer_workspace_id
        verification.close()

        if case_name == "provider_change":
            candidates = {
                "A": domain.alt_provider_workspace_ids[0],
                "B": domain.alt_provider_workspace_ids[1],
            }

            def mutation(service, actor, expected_version, candidate):
                return service.change_commitment_responsibility(
                    commitment_id=domain.commitment_id,
                    expected_version=expected_version,
                    field="provider_workspace_id",
                    value=candidates[candidate],
                    reason=f"Writer {candidate}",
                    current_user=actor,
                )

            actor_id = domain.owner_id

        elif case_name == "consumer_change":
            candidates = {
                "A": domain.alt_consumer_workspace_ids[0],
                "B": domain.alt_consumer_workspace_ids[1],
            }

            def mutation(service, actor, expected_version, candidate):
                return service.change_commitment_responsibility(
                    commitment_id=domain.commitment_id,
                    expected_version=expected_version,
                    field="consumer_workspace_id",
                    value=candidates[candidate],
                    reason=f"Writer {candidate}",
                    current_user=actor,
                )

            actor_id = domain.owner_id

        elif case_name == "information_provided":
            def mutation(service, actor, expected_version, candidate):
                return service.transition_commitment(
                    commitment_id=domain.commitment_id,
                    target="information_provided",
                    expected_version=expected_version,
                    reason=f"Writer {candidate}",
                    supplied_source_key=f"SRC-{candidate}",
                    supplied_revision=candidate,
                    current_user=actor,
                )

            actor_id = domain.provider_user_id

        elif case_name == "fulfilment":
            def mutation(service, actor, expected_version, candidate):
                return service.transition_commitment(
                    commitment_id=domain.commitment_id,
                    target="fulfilled_for_stated_use",
                    expected_version=expected_version,
                    reason=f"Writer {candidate}",
                    fulfilment_use=f"Approved stated use {candidate}",
                    current_user=actor,
                )

            actor_id = domain.consumer_user_id

        elif case_name == "withdrawal":
            def mutation(service, actor, expected_version, candidate):
                return service.set_commitment_current_use(
                    commitment_id=domain.commitment_id,
                    current_use=False,
                    expected_version=expected_version,
                    reason=f"Writer {candidate}",
                    current_user=actor,
                )

            actor_id = domain.owner_id

        elif case_name == "responsibility":
            candidates = {
                "A": domain.steward_a_id,
                "B": domain.steward_b_id,
            }

            def mutation(service, actor, expected_version, candidate):
                return service.change_commitment_responsibility(
                    commitment_id=domain.commitment_id,
                    expected_version=expected_version,
                    field="steward_id",
                    value=candidates[candidate],
                    reason=f"Writer {candidate}",
                    current_user=actor,
                )

            actor_id = domain.owner_id

        elif case_name == "source_revision":
            def mutation(service, actor, expected_version, candidate):
                return service.change_supplied_source(
                    commitment_id=domain.commitment_id,
                    expected_version=expected_version,
                    source_key=f"SRC-RACE-{candidate}",
                    revision=candidate,
                    reason=f"Writer {candidate}",
                    current_user=actor,
                )

            actor_id = domain.provider_user_id

        elif case_name == "reassessment":
            def mutation(service, actor, expected_version, candidate):
                return service.set_reassessment(
                    commitment_id=domain.commitment_id,
                    needed=True,
                    expected_version=expected_version,
                    trigger=f"trigger-{candidate}",
                    reason=f"Writer {candidate}",
                    current_user=actor,
                )

            actor_id = domain.owner_id

        else:
            raise AssertionError(f"Unsupported race case: {case_name}")

        success = _run_two_writers(
            actor_id=actor_id,
            expected_version=baseline_version,
            mutation=mutation,
            conflict_type=CommitmentVersionConflict,
        )

        verification = SessionFactory()
        commitment_after = verification.get(
            InterfaceCommitment,
            domain.commitment_id,
        )
        assert commitment_after is not None
        assert commitment_after.version == baseline_version + 1
        assert success["version"] == baseline_version + 1
        assert commitment_after.relationship_id == relationship_id
        assert commitment_after.project_id == project_id
        assert (
            _audit_count(
                verification,
                "INTERFACE_COMMITMENT",
                domain.commitment_id,
            )
            == baseline_audits + 1
        )

        if case_name == "provider_change":
            assert commitment_after.provider_workspace_id in set(
                domain.alt_provider_workspace_ids
            )
            assert commitment_after.consumer_workspace_id == original_consumer

        elif case_name == "consumer_change":
            assert commitment_after.consumer_workspace_id in set(
                domain.alt_consumer_workspace_ids
            )
            assert commitment_after.provider_workspace_id == original_provider

        elif case_name == "information_provided":
            assert commitment_after.state == "information_provided"
            assert commitment_after.supplied_source_key in {
                "SRC-A",
                "SRC-B",
            }

        elif case_name == "fulfilment":
            assert commitment_after.state == "fulfilled_for_stated_use"
            assert commitment_after.fulfilment_use in {
                "Approved stated use A",
                "Approved stated use B",
            }

        elif case_name == "withdrawal":
            assert commitment_after.current_use is False
            assert commitment_after.withdrawn_at is not None

        elif case_name == "responsibility":
            assert commitment_after.steward_id in {
                domain.steward_a_id,
                domain.steward_b_id,
            }

        elif case_name == "source_revision":
            assert commitment_after.supplied_source_key in {
                "SRC-RACE-A",
                "SRC-RACE-B",
            }
            assert commitment_after.reassessment_needed is True

        elif case_name == "reassessment":
            assert commitment_after.reassessment_needed is True
            assert commitment_after.reassessment_trigger in {
                "trigger-A",
                "trigger-B",
            }
    finally:
        verification.close()
        _cleanup_domain(domain)
