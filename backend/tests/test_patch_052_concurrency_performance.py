"""PATCH-052 real-session concurrency and query-plan evidence."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
import time
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.exceptions.engineering_identifier import EngineeringIdentifierConflict
from app.models.engineering_identifier import EngineeringIdentifier
from app.models.engineering_identifier_command import (
    EngineeringIdentifierIdempotency,
    EngineeringIdentifierOutbox,
)
from app.models.discipline_package import (
    OrganizationPackageSelection,
    ProjectPackageConfigurationHead,
    ProjectPackageConfigurationRevision,
    ProjectPackageConfigurationSelection,
)
from app.models.audit_log import AuditLog
from app.models.engineering_deliverable import (
    EngineeringDeliverable,
    EngineeringDeliverableIdempotency,
    EngineeringDeliverableOutbox,
)
from app.models.engineering_object import EngineeringObject
from app.models.engineering_object_command import (
    EngineeringObjectIdempotency,
    EngineeringObjectOutbox,
)
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.organization import Organization
from app.models.user import User
from app.schemas.discipline_package_operations import PackageObjectCreateRequest
from app.schemas.discipline_package_operations import PackageDeliverableCreateRequest
from app.schemas.engineering_deliverable import (
    DeliverableActor,
    DeliverableMutationSuccess,
    DeliverableUnavailableResult,
)
from app.schemas.engineering_identifier import (
    CreateEngineeringIdentifierRequest,
    ReplaceEngineeringIdentifierRequest,
)
from app.services.electrical_package_service import (
    ElectricalPackageService,
    PackageProtectedNotFound,
    PackageUnavailable,
)
from app.core.database import (
    DisciplinePackageGuardMode,
    acquire_discipline_package_registry_guard,
)
from app.services.engineering_identifier_service import EngineeringIdentifierService
from app.services.engineering_deliverable_service import EngineeringDeliverableService
from app.adapters.engineering_deliverable import SqlAlchemyDeliverableAuthorization
from app.repositories.engineering_deliverable_unit_of_work import (
    SqlAlchemyEngineeringDeliverableUnitOfWork,
)
from app.repositories.patch_052_operation_unit_of_work import Patch052OperationUnitOfWork
from app.repositories.engineering_identifier_unit_of_work import (
    SqlAlchemyEngineeringIdentifierUnitOfWork,
)
from conftest import owner_engine
from test_patch_052_batch_2 import ORG_ID, _electrical_scope
from test_patch_052_migration import _truncate_disposable_rows


def _session_factory():
    return sessionmaker(bind=owner_engine, expire_on_commit=False)


def _seed_package_object():
    _truncate_disposable_rows()
    with Session(owner_engine, expire_on_commit=False) as session:
        session.add(Organization(id=ORG_ID, is_active=True))
        session.flush()
        suffix = uuid4().hex[:10]
        actor = User(
            email=f"patch052-concurrency-{suffix}@example.com",
            username=f"patch052-concurrency-{suffix}",
            full_name="PATCH-052 concurrency actor",
            hashed_password="not-used",
            role="engineer",
            is_active=True,
        )
        session.add(actor)
        session.flush()
        project, workspace = _electrical_scope(session, actor)
        actor_id = actor.id
        project_id = project.id
        workspace_id = workspace.id
    package = ElectricalPackageService(_session_factory())
    obj, primary = package.create_object(
        actor_id=actor_id,
        organization_id=ORG_ID,
        project_id=project_id,
        workspace_id=workspace_id,
        data=PackageObjectCreateRequest(
            declaration_id="electrical.object.motor",
            primary_identifier_display_value="MTR-CONCURRENCY-PRIMARY",
            rationale="Create concurrent Identifier fixture",
        ),
        correlation_id=uuid4(),
        idempotency_key=uuid4(),
    )
    return actor_id, obj, primary


def _seed_package_scope():
    _truncate_disposable_rows()
    with Session(owner_engine, expire_on_commit=False) as session:
        session.add(Organization(id=ORG_ID, is_active=True))
        session.flush()
        suffix = uuid4().hex[:10]
        actor = User(
            email=f"patch052-package-{suffix}@example.com",
            username=f"patch052-package-{suffix}",
            full_name="PATCH-052 package actor",
            hashed_password="not-used",
            role="engineer",
            is_active=True,
        )
        session.add(actor)
        session.flush()
        project, workspace = _electrical_scope(session, actor)
        return actor.id, project.id, workspace.id


def _identifier_service() -> EngineeringIdentifierService:
    return EngineeringIdentifierService(
        lambda: SqlAlchemyEngineeringIdentifierUnitOfWork(_session_factory())
    )


def test_duplicate_create_and_supersession_races_have_one_safe_winner() -> None:
    actor_id, obj, primary = _seed_package_object()
    try:
        create_barrier = Barrier(2)

        def create_candidate():
            create_barrier.wait()
            try:
                result = _identifier_service().create(
                    actor_id=actor_id,
                    organization_id=ORG_ID,
                    object_id=obj.id,
                    data=CreateEngineeringIdentifierRequest(
                        identifier_kind="vendor_reference",
                        display_value="DUPLICATE RACE",
                        expected_object_version=1,
                        rationale="Concurrent duplicate proof",
                    ),
                    correlation_id=uuid4(),
                    idempotency_key=uuid4(),
                )
                return "success", result.identifier_id
            except EngineeringIdentifierConflict:
                return "conflict", None

        with ThreadPoolExecutor(max_workers=2) as executor:
            create_results = tuple(executor.map(lambda _index: create_candidate(), range(2)))
        assert sorted(result[0] for result in create_results) == ["conflict", "success"]

        replace_barrier = Barrier(2)

        def replace_candidate(index: int):
            replace_barrier.wait()
            try:
                result = _identifier_service().replace(
                    actor_id=actor_id,
                    organization_id=ORG_ID,
                    identifier_id=primary.identifier_id,
                    data=ReplaceEngineeringIdentifierRequest(
                        identifier_kind="equipment_number",
                        display_value=f"MTR-CONCURRENCY-{index}",
                        expected_object_version=1,
                        expected_identifier_version=1,
                        rationale="Concurrent supersession proof",
                    ),
                    correlation_id=uuid4(),
                    idempotency_key=uuid4(),
                )
                return "success", result.identifier_id
            except EngineeringIdentifierConflict:
                return "conflict", None

        with ThreadPoolExecutor(max_workers=2) as executor:
            replace_results = tuple(executor.map(replace_candidate, range(2)))
        assert sorted(result[0] for result in replace_results) == ["conflict", "success"]

        with Session(owner_engine) as session:
            identifiers = session.scalars(select(EngineeringIdentifier).where(
                EngineeringIdentifier.engineering_object_id == obj.id,
            )).all()
            current = [item for item in identifiers if item.lifecycle == "current"]
            assert len(current) == 2
            assert sum(item.primary_role == "primary" for item in current) == 1
            assert sum(item.normalized_value == "duplicate race" for item in current) == 1
            assert sum(item.predecessor_identifier_id == primary.identifier_id for item in identifiers) == 1
            assert session.scalar(select(EngineeringIdentifier).where(
                EngineeringIdentifier.identifier_id == primary.identifier_id,
            )).lifecycle == "superseded"
            assert session.query(EngineeringIdentifierIdempotency).filter(
                EngineeringIdentifierIdempotency.operation.in_((
                    "CreateEngineeringIdentifier", "ReplaceEngineeringIdentifier",
                ))
            ).count() == 2
            assert session.query(EngineeringIdentifierOutbox).filter(
                EngineeringIdentifierOutbox.identifier_id.in_(
                    [item.identifier_id for item in identifiers]
                )
            ).count() == 4
    finally:
        _truncate_disposable_rows()


def test_concurrent_duplicate_package_mutation_converges_on_one_snapshot() -> None:
    actor_id, project_id, workspace_id = _seed_package_scope()
    key = uuid4()
    request = PackageObjectCreateRequest(
        declaration_id="electrical.object.motor",
        primary_identifier_display_value="MTR-PACKAGE-DUPLICATE",
        rationale="Concurrent package idempotency proof",
    )
    barrier = Barrier(2)

    def candidate():
        barrier.wait()
        return ElectricalPackageService(_session_factory()).create_object(
            actor_id=actor_id,
            organization_id=ORG_ID,
            auth_version=1,
            project_id=project_id,
            workspace_id=workspace_id,
            data=request,
            correlation_id=uuid4(),
            idempotency_key=key,
        )

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = tuple(executor.map(lambda _index: candidate(), range(2)))
        assert results[0] == results[1]
        with Session(owner_engine) as session:
            object_id = results[0][0].id
            assert session.query(EngineeringObject).filter_by(id=object_id).count() == 1
            assert session.query(EngineeringObjectIdempotency).filter_by(
                actor_id=actor_id,
                command_type="PackageElectricalObjectCreate",
                idempotency_id=key,
            ).count() == 1
            assert session.query(EngineeringObjectOutbox).filter_by(
                aggregate_id=object_id,
            ).count() == 1
    finally:
        _truncate_disposable_rows()


def test_configuration_change_and_workspace_rebind_win_fail_closed() -> None:
    for change in ("configuration", "workspace"):
        actor_id, project_id, workspace_id = _seed_package_scope()
        writer_ready = Event()
        worker_started = Event()

        def writer():
            with Session(owner_engine) as session:
                session.begin()
                acquire_discipline_package_registry_guard(
                    session, DisciplinePackageGuardMode.EXCLUSIVE,
                )
                if change == "configuration":
                    row = session.get(
                        OrganizationPackageSelection,
                        (ORG_ID, "electrical", "1.0.0"),
                        with_for_update=True,
                    )
                    row.state = "disabled"
                else:
                    row = session.get(
                        EngineeringWorkspace, workspace_id, with_for_update=True,
                    )
                    row.package_binding_state = "FUTURE_UNAVAILABLE_UNBOUND"
                    row.bound_package_key = None
                    row.bound_project_configuration_revision = None
                writer_ready.set()
                worker_started.wait(timeout=5)
                time.sleep(0.05)
                session.commit()

        def mutation():
            writer_ready.wait(timeout=5)
            worker_started.set()
            try:
                ElectricalPackageService(_session_factory()).create_object(
                    actor_id=actor_id,
                    organization_id=ORG_ID,
                    auth_version=1,
                    project_id=project_id,
                    workspace_id=workspace_id,
                    data=PackageObjectCreateRequest(
                        declaration_id="electrical.object.motor",
                        primary_identifier_display_value=f"MTR-{change}-WINS",
                        rationale="Authority change wins",
                    ),
                    correlation_id=uuid4(),
                    idempotency_key=uuid4(),
                )
                return "unexpected-success"
            except PackageUnavailable:
                return "unavailable"

        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                write_future = executor.submit(writer)
                mutation_future = executor.submit(mutation)
                write_future.result(timeout=10)
                assert mutation_future.result(timeout=10) == "unavailable"
            with Session(owner_engine) as session:
                assert session.query(EngineeringObject).filter_by(
                    project_id=project_id,
                ).count() == 0
        finally:
            _truncate_disposable_rows()


def test_membership_revocation_wins_and_replay_cannot_disclose() -> None:
    actor_id, project_id, workspace_id = _seed_package_scope()
    service = ElectricalPackageService(_session_factory())
    request = PackageObjectCreateRequest(
        declaration_id="electrical.object.motor",
        primary_identifier_display_value="MTR-REVOKED-REPLAY",
        rationale="Replay authority proof",
    )
    key = uuid4()
    original = service.create_object(
        actor_id=actor_id, organization_id=ORG_ID, auth_version=1,
        project_id=project_id, workspace_id=workspace_id, data=request,
        correlation_id=uuid4(), idempotency_key=key,
    )
    try:
        with Session(owner_engine) as session:
            actor = session.get(User, actor_id, with_for_update=True)
            actor.auth_version += 1
            session.commit()
        with pytest.raises(PackageProtectedNotFound):
            service.create_object(
                actor_id=actor_id, organization_id=ORG_ID, auth_version=1,
                project_id=project_id, workspace_id=workspace_id, data=request,
                correlation_id=uuid4(), idempotency_key=key,
            )
        with Session(owner_engine) as session:
            assert session.get(EngineeringObject, original[0].id) is not None
    finally:
        _truncate_disposable_rows()


def test_mutation_wins_then_configuration_writer_proceeds(monkeypatch) -> None:
    actor_id, project_id, workspace_id = _seed_package_scope()
    service = ElectricalPackageService(_session_factory())
    mutation_staged = Event()
    writer_started = Event()
    release_mutation = Event()
    original_audit = service._audit

    def blocking_audit(session, **kwargs):
        original_audit(session, **kwargs)
        mutation_staged.set()
        release_mutation.wait(timeout=5)

    monkeypatch.setattr(service, "_audit", blocking_audit)

    def mutation():
        return service.create_object(
            actor_id=actor_id, organization_id=ORG_ID, auth_version=1,
            project_id=project_id, workspace_id=workspace_id,
            data=PackageObjectCreateRequest(
                declaration_id="electrical.object.motor",
                primary_identifier_display_value="MTR-MUTATION-WINS",
                rationale="Mutation wins",
            ), correlation_id=uuid4(), idempotency_key=uuid4(),
        )

    def writer():
        mutation_staged.wait(timeout=5)
        writer_started.set()
        with Session(owner_engine) as session:
            session.begin()
            acquire_discipline_package_registry_guard(
                session, DisciplinePackageGuardMode.EXCLUSIVE,
            )
            row = session.get(
                OrganizationPackageSelection,
                (ORG_ID, "electrical", "1.0.0"),
                with_for_update=True,
            )
            row.state = "disabled"
            session.commit()

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            mutation_future = executor.submit(mutation)
            writer_future = executor.submit(writer)
            writer_started.wait(timeout=5)
            time.sleep(0.05)
            release_mutation.set()
            created = mutation_future.result(timeout=10)
            writer_future.result(timeout=10)
        with Session(owner_engine) as session:
            assert session.get(EngineeringObject, created[0].id) is not None
            assert session.get(
                OrganizationPackageSelection,
                (ORG_ID, "electrical", "1.0.0"),
            ).state == "disabled"
    finally:
        _truncate_disposable_rows()


class _TransientFailure(Exception):
    sqlstate = "40001"


def _transient_error():
    return OperationalError("PATCH-052 transient proof", {}, _TransientFailure())


def test_retry_uses_fresh_sessions_and_exhausts_after_two_retries(monkeypatch) -> None:
    actor_id, project_id, workspace_id = _seed_package_scope()
    service = ElectricalPackageService(_session_factory())
    sessions = []

    def always_transient(uow, **_kwargs):
        sessions.append(uow.session)
        raise _transient_error()

    monkeypatch.setattr(service, "_context", always_transient)
    try:
        with pytest.raises(Exception) as caught:
            service.create_object(
                actor_id=actor_id, organization_id=ORG_ID, auth_version=1,
                project_id=project_id, workspace_id=workspace_id,
                data=PackageObjectCreateRequest(
                    declaration_id="electrical.object.motor",
                    primary_identifier_display_value="MTR-RETRY-EXHAUST",
                    rationale="Retry exhaustion",
                ), correlation_id=uuid4(), idempotency_key=uuid4(),
            )
        assert caught.type.__name__ == "PackageConflict"
        assert len(sessions) == 3
        assert len({id(item) for item in sessions}) == 3
    finally:
        _truncate_disposable_rows()


def test_retry_after_revocation_rechecks_authority(monkeypatch) -> None:
    actor_id, project_id, workspace_id = _seed_package_scope()
    service = ElectricalPackageService(_session_factory())
    original_context = service._context
    attempts = []

    def transient_then_authorize(uow, **kwargs):
        attempts.append(uow.session)
        if len(attempts) == 1:
            with Session(owner_engine) as session:
                actor = session.get(User, actor_id, with_for_update=True)
                actor.auth_version += 1
                session.commit()
            raise _transient_error()
        return original_context(uow, **kwargs)

    monkeypatch.setattr(service, "_context", transient_then_authorize)
    try:
        with pytest.raises(PackageProtectedNotFound):
            service.create_object(
                actor_id=actor_id, organization_id=ORG_ID, auth_version=1,
                project_id=project_id, workspace_id=workspace_id,
                data=PackageObjectCreateRequest(
                    declaration_id="electrical.object.motor",
                    primary_identifier_display_value="MTR-RETRY-REVOKED",
                    rationale="Retry after revocation",
                ), correlation_id=uuid4(), idempotency_key=uuid4(),
            )
        assert len(attempts) == 2 and attempts[0] is not attempts[1]
        with Session(owner_engine) as session:
            assert session.query(EngineeringObject).filter_by(
                project_id=project_id,
            ).count() == 0
    finally:
        _truncate_disposable_rows()


def test_concurrent_user_revocation_wins_before_post_lock_authority() -> None:
    actor_id, project_id, workspace_id = _seed_package_scope()
    revocation_locked = Event()
    mutation_started = Event()

    def revoke():
        with Session(owner_engine) as session:
            actor = session.get(User, actor_id, with_for_update=True)
            actor.auth_version += 1
            revocation_locked.set()
            mutation_started.wait(timeout=5)
            time.sleep(0.05)
            session.commit()

    def mutate():
        revocation_locked.wait(timeout=5)
        mutation_started.set()
        try:
            ElectricalPackageService(_session_factory()).create_object(
                actor_id=actor_id, organization_id=ORG_ID, auth_version=1,
                project_id=project_id, workspace_id=workspace_id,
                data=PackageObjectCreateRequest(
                    declaration_id="electrical.object.motor",
                    primary_identifier_display_value="MTR-REVOCATION-WINS",
                    rationale="Concurrent revocation wins",
                ), correlation_id=uuid4(), idempotency_key=uuid4(),
            )
            return "unexpected-success"
        except PackageProtectedNotFound:
            return "protected"

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            revocation = executor.submit(revoke)
            mutation = executor.submit(mutate)
            revocation.result(timeout=10)
            assert mutation.result(timeout=10) == "protected"
        with Session(owner_engine) as session:
            assert session.query(EngineeringObject).filter_by(
                project_id=project_id,
            ).count() == 0
    finally:
        _truncate_disposable_rows()


def test_stale_project_configuration_revision_is_rejected_at_commit() -> None:
    actor_id, project_id, workspace_id = _seed_package_scope()
    try:
        with Session(owner_engine) as session:
            first = session.get(ProjectPackageConfigurationRevision, (project_id, 1))
            selection = session.get(
                ProjectPackageConfigurationSelection,
                (project_id, 1, "electrical"),
            )
            session.add(ProjectPackageConfigurationRevision(
                project_id=project_id,
                configuration_revision=2,
                organization_id=ORG_ID,
                observed_registry_digest=first.observed_registry_digest,
                profile_id=first.profile_id,
                profile_digest=first.profile_digest,
                rationale="Stale Workspace binding proof",
            ))
            session.flush()
            session.add(ProjectPackageConfigurationSelection(
                project_id=project_id,
                configuration_revision=2,
                package_key="electrical",
                package_version=selection.package_version,
                descriptor_digest=selection.descriptor_digest,
            ))
            head = session.get(
                ProjectPackageConfigurationHead, project_id, with_for_update=True,
            )
            head.current_revision = 2
            head.configuration_version += 1
            with pytest.raises(SQLAlchemyError, match="stale Workspace binding"):
                session.commit()
            session.rollback()
        with Session(owner_engine) as session:
            assert session.get(
                ProjectPackageConfigurationHead, project_id,
            ).current_revision == 1
            assert session.get(
                EngineeringWorkspace, workspace_id,
            ).bound_project_configuration_revision == 1
    finally:
        _truncate_disposable_rows()


def _deliverable_request(workspace_id):
    return PackageDeliverableCreateRequest(
        declaration_id="electrical.deliverable.electrical_load_list",
        code="ELL-CONCURRENCY",
        title="Electrical load list",
        discipline="electrical",
        deliverable_type="electrical_load_list",
        external_authority="spreadsheet",
        workspace_id=workspace_id,
        initial_external_label="Rev 0",
        rationale="Package Deliverable transaction proof",
    )


def _deliverable_service(package_factory):
    ordinary_session = Session(owner_engine, expire_on_commit=False)
    return EngineeringDeliverableService(
        uow_factory=lambda: SqlAlchemyEngineeringDeliverableUnitOfWork(
            ordinary_session,
        ),
        authorization=SqlAlchemyDeliverableAuthorization(ordinary_session),
        package_uow_factory=package_factory,
    ), ordinary_session


def test_deliverable_replay_rechecks_configuration_authority() -> None:
    actor_id, project_id, workspace_id = _seed_package_scope()
    service, ordinary_session = _deliverable_service(
        lambda: Patch052OperationUnitOfWork(_session_factory()),
    )
    key = uuid4()
    request = _deliverable_request(workspace_id)
    try:
        created = service.create_package_electrical(
            project_id=project_id, data=request,
            actor=DeliverableActor(
                actor_id=actor_id, organization_id=ORG_ID, auth_version=1,
            ), idempotency_key=key, correlation_id=uuid4(),
        )
        assert isinstance(created, DeliverableMutationSuccess)
        with Session(owner_engine) as session:
            selection = session.get(
                OrganizationPackageSelection,
                (ORG_ID, "electrical", "1.0.0"),
                with_for_update=True,
            )
            selection.state = "disabled"
            session.commit()
        replay = service.create_package_electrical(
            project_id=project_id, data=request,
            actor=DeliverableActor(
                actor_id=actor_id, organization_id=ORG_ID, auth_version=1,
            ), idempotency_key=key, correlation_id=uuid4(),
        )
        assert isinstance(replay, DeliverableUnavailableResult)
    finally:
        ordinary_session.close()
        _truncate_disposable_rows()


def test_deliverable_audit_outbox_and_idempotency_roll_back_together() -> None:
    actor_id, project_id, workspace_id = _seed_package_scope()

    class FailingCommitUow(Patch052OperationUnitOfWork):
        def commit(self):
            self.session.flush()
            raise RuntimeError("forced commit-boundary failure")

    service, ordinary_session = _deliverable_service(
        lambda: FailingCommitUow(_session_factory()),
    )
    try:
        with pytest.raises(RuntimeError, match="commit-boundary"):
            service.create_package_electrical(
                project_id=project_id,
                data=_deliverable_request(workspace_id),
                actor=DeliverableActor(
                    actor_id=actor_id, organization_id=ORG_ID, auth_version=1,
                ), idempotency_key=uuid4(), correlation_id=uuid4(),
            )
        with Session(owner_engine) as session:
            assert session.query(EngineeringDeliverable).filter_by(
                project_id=project_id,
            ).count() == 0
            assert session.query(EngineeringDeliverableIdempotency).filter_by(
                organization_id=ORG_ID, actor_id=actor_id,
            ).count() == 0
            assert session.query(EngineeringDeliverableOutbox).count() == 0
            assert session.query(AuditLog).filter_by(user_id=actor_id).count() == 0
    finally:
        ordinary_session.close()
        _truncate_disposable_rows()


def _plan(connection, sql: str, parameters: dict[str, object]) -> str:
    rows = connection.execute(text(f"EXPLAIN (COSTS OFF) {sql}"), parameters).all()
    return "\n".join(row[0] for row in rows)


def test_production_shaped_queries_are_index_compatible_on_bounded_data() -> None:
    _actor_id, obj, primary = _seed_package_object()
    try:
        with owner_engine.begin() as connection:
            connection.execute(text(
                "ANALYZE engineering_identifiers, engineering_objects, "
                "engineering_context_subject_references, engineering_deliverables"
            ))
            connection.execute(text("SET LOCAL enable_seqscan=off"))
            plans = {
                "current_lookup": _plan(connection, """
                    SELECT identifier_id FROM engineering_identifiers
                    WHERE organization_id=:organization_id AND project_id=:project_id
                      AND issuing_scope_kind='project' AND issuing_scope_value=:scope
                      AND identifier_kind=:kind AND normalized_value=:value
                      AND lifecycle='current'
                """, {
                    "organization_id": ORG_ID,
                    "project_id": obj.project_id,
                    "scope": str(obj.project_id),
                    "kind": primary.identifier_kind.value,
                    "value": primary.normalized_value,
                }),
                "report_identifier_snapshot": _plan(connection, """
                    SELECT * FROM engineering_identifiers
                    WHERE engineering_object_id=:object_id
                      AND organization_id=:organization_id AND lifecycle='current'
                    ORDER BY primary_role DESC, identifier_kind,
                             normalized_value, identifier_id
                """, {"object_id": obj.id, "organization_id": ORG_ID}),
                "object_provenance": _plan(connection, """
                    SELECT id FROM engineering_objects
                    WHERE project_id=:project_id
                      AND origin_project_configuration_revision=1
                      AND origin_package_key='electrical'
                """, {"project_id": obj.project_id}),
                "object_context": _plan(connection, """
                    SELECT context_id FROM engineering_context_subject_references
                    WHERE subject_engineering_object_id=:object_id
                """, {"object_id": obj.id}),
                "deliverable_readiness": _plan(connection, """
                    SELECT id FROM engineering_deliverables
                    WHERE project_id=:project_id
                      AND origin_project_configuration_revision=1
                      AND origin_package_key='electrical'
                """, {"project_id": obj.project_id}),
            }
        assert "uq_engineering_identifier_current_value" in plans["current_lookup"]
        assert "ix_engineering_identifier_current_set" in plans["report_identifier_snapshot"]
        assert "ix_engineering_objects_origin" in plans["object_provenance"]
        assert "ix_engineering_context_subject_refs_object_id" in plans["object_context"]
        assert "ix_engineering_deliverables_origin" in plans["deliverable_readiness"]
    finally:
        _truncate_disposable_rows()
