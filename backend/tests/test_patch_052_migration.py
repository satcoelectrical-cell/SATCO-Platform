"""PATCH-052 clean-chain and legacy-preservation migration evidence."""

from uuid import UUID, uuid4

from alembic import command
import pytest
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.organization import Organization
from app.models.project import Project
from app.models.user import User
from app.repositories.organizational_memory_repository import (
    SqlAlchemyOrganizationalMemoryRepository,
)
from conftest import TEST_DATABASE_REVISION, alembic_config, owner_engine
from test_organizational_memory_repository import _memory


PATCH_051_HEAD = "e05100000006"
PATCH_052_M1 = "e05200000001"
PATCH_052_HEAD = "e05200000002"
TEST_ORGANIZATION_ID = UUID("02810000-0000-4000-8000-000000000001")


def _revision() -> str:
    with owner_engine.connect() as connection:
        return connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()


def _truncate_disposable_rows() -> None:
    """Return only the governed disposable database to an empty head state."""

    command.upgrade(alembic_config, PATCH_052_HEAD)
    table_names = sorted(
        table_name
        for table_name in inspect(owner_engine).get_table_names()
        if table_name != "alembic_version"
    )
    with owner_engine.begin() as connection:
        quoted = ", ".join(f'"{name}"' for name in table_names)
        connection.exec_driver_sql(f"TRUNCATE TABLE {quoted} CASCADE")


def _seed_report_memory_scope() -> dict[str, object]:
    suffix = uuid4().hex[:10]
    organization_id = TEST_ORGANIZATION_ID
    with Session(owner_engine, expire_on_commit=False) as session:
        organization = session.get(Organization, organization_id)
        if organization is None:
            session.add(Organization(id=organization_id, is_active=True))
            session.flush()
        owner = User(
            email=f"patch052-{suffix}@example.com",
            username=f"patch052-{suffix}",
            full_name="PATCH-052 migration owner",
            hashed_password="not-used",
            role="engineer",
            is_active=True,
        )
        session.add(owner)
        session.flush()
        customer = Customer(
            organization_id=organization_id,
            name=f"PATCH-052 legacy {suffix}",
        )
        session.add(customer)
        session.flush()
        project = Project(
            organization_id=organization_id,
            project_code=f"SAT-PRJ-2095-{customer.id + 9000:04d}",
            name="PATCH-052 legacy preservation",
            customer_id=customer.id,
            owner_id=owner.id,
        )
        session.add(project)
        session.flush()
        workspace = EngineeringWorkspace(
            project_id=project.id,
            discipline="electrical",
            status="active",
            owner_id=owner.id,
            created_by_id=owner.id,
            version=1,
        )
        session.add(workspace)
        session.flush()
        domain = {
            "actors": {"project_owner": owner},
            "project": project,
            "consumer_workspace": workspace,
        }
        memory = _memory(session, domain)
        repository = SqlAlchemyOrganizationalMemoryRepository(session)
        repository.add(memory)
        repository.append_history(memory.initial_history(event_id=uuid4()))
        session.commit()
        return {
            "organization_id": organization_id,
            "customer_id": customer.id,
            "project_id": project.id,
            "workspace_id": workspace.id,
            "owner_id": owner.id,
            "report_id": memory.source.report_id,
            "memory_id": memory.id,
        }


def _row_json(table: str, identifier: object) -> str:
    with owner_engine.connect() as connection:
        return connection.execute(
            text(f"SELECT to_jsonb(value)::text FROM {table} value WHERE id=:id"),
            {"id": identifier},
        ).scalar_one()


def _assert_patch_052_schema() -> None:
    schema = inspect(owner_engine)
    assert {
        "engineering_identifiers",
        "engineering_identifier_idempotency",
        "engineering_identifier_outbox",
        "engineering_context_package_input_bindings",
        "evidence_package_input_bindings",
    } <= set(schema.get_table_names())
    assert {
        "origin_package_key",
        "origin_project_configuration_revision",
        "origin_declaration_id",
    } <= {column["name"] for column in schema.get_columns("engineering_objects")}
    with owner_engine.connect() as connection:
        assert {
            "satco_patch052_origin_immutable",
            "satco_patch052_identifier_guard",
            "satco_patch052_identifier_cardinality",
            "satco_patch052_context_object_coherence",
            "satco_patch052_binding_coherent",
            "satco_patch052_binding_immutable",
        } <= set(
            connection.execute(text(
                "SELECT proname FROM pg_proc WHERE proname LIKE 'satco_patch052_%'"
            )).scalars()
        )


def test_clean_base_to_patch_052_head_was_recovered() -> None:
    assert TEST_DATABASE_REVISION == PATCH_052_HEAD
    _truncate_disposable_rows()
    command.downgrade(alembic_config, "base")
    with owner_engine.connect() as connection:
        assert connection.execute(text(
            "SELECT count(*) FROM alembic_version"
        )).scalar_one() == 0
    command.upgrade(alembic_config, PATCH_052_HEAD)
    assert _revision() == PATCH_052_HEAD
    _assert_patch_052_schema()


def test_m2_exact_empty_delta_constraints_indexes_triggers_and_grants() -> None:
    assert _revision() == PATCH_052_HEAD
    command.downgrade(alembic_config, PATCH_052_M1)
    before = set(inspect(owner_engine).get_table_names())
    assert {
        "engineering_context_package_input_bindings",
        "evidence_package_input_bindings",
    }.isdisjoint(before)
    with owner_engine.connect() as connection:
        m1_domain = connection.execute(text(
            "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
            "WHERE conname='ck_engineering_context_subject_refs_kind'"
        )).scalar_one()
        assert all(value in m1_domain for value in (
            "project", "workspace", "discipline",
        ))
        assert "engineering_object" not in m1_domain

    command.upgrade(alembic_config, PATCH_052_HEAD)
    after = set(inspect(owner_engine).get_table_names())
    assert after - before == {
        "engineering_context_package_input_bindings",
        "evidence_package_input_bindings",
    }
    schema = inspect(owner_engine)
    assert {row["name"] for row in schema.get_indexes(
        "engineering_context_package_input_bindings"
    )} >= {"ix_context_input_binding_readiness"}
    assert {row["name"] for row in schema.get_indexes(
        "evidence_package_input_bindings"
    )} >= {"ix_evidence_input_binding_readiness"}

    with owner_engine.connect() as connection:
        counts = connection.execute(text(
            "SELECT (SELECT count(*) FROM engineering_context_package_input_bindings), "
            "(SELECT count(*) FROM evidence_package_input_bindings)"
        )).one()
        assert tuple(counts) == (0, 0)
        m2_domain = connection.execute(text(
            "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
            "WHERE conname='ck_engineering_context_subject_refs_kind'"
        )).scalar_one()
        assert all(value in m2_domain for value in (
            "project", "workspace", "discipline", "engineering_object",
        ))
        triggers = set(connection.execute(text(
            "SELECT tgname FROM pg_trigger WHERE NOT tgisinternal AND "
            "tgrelid IN ('engineering_context_package_input_bindings'::regclass, "
            "'evidence_package_input_bindings'::regclass)"
        )).scalars())
        assert triggers == {
            "trg_engineering_context_package_input_bindings_coherent",
            "trg_engineering_context_package_input_bindings_immutable",
            "trg_evidence_package_input_bindings_coherent",
            "trg_evidence_package_input_bindings_immutable",
        }
        if connection.execute(text(
            "SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='satco_runtime')"
        )).scalar_one():
            for table_name in (
                "engineering_context_package_input_bindings",
                "evidence_package_input_bindings",
            ):
                privileges = connection.execute(text(
                    "SELECT has_table_privilege('satco_runtime', :table, 'SELECT'), "
                    "has_table_privilege('satco_runtime', :table, 'INSERT'), "
                    "has_table_privilege('satco_runtime', :table, 'UPDATE'), "
                    "has_table_privilege('satco_runtime', :table, 'DELETE'), "
                    "has_table_privilege('satco_runtime', :table, 'TRUNCATE')"
                ), {"table": table_name}).one()
                assert tuple(privileges) == (True, True, False, False, False)


def test_m2_populated_downgrade_fails_closed() -> None:
    from app.permissions.roles import Role
    from app.services.package_declaration_binding_service import (
        PackageDeclarationBindingService,
    )
    from test_patch_052_batch_3 import _factory, _instrumentation_scope
    from test_patch_052_declaration_bindings import _bind_context, _context, _object

    try:
        with Session(owner_engine, expire_on_commit=False) as session:
            suffix = uuid4().hex[:10]
            session.add(Organization(id=TEST_ORGANIZATION_ID, is_active=True))
            session.flush()
            actor = User(
                email=f"patch052-m2-{suffix}@example.com",
                username=f"patch052-m2-{suffix}", full_name="M2 downgrade guard",
                hashed_password="not-used", role=Role.ENGINEER.value, is_active=True,
            )
            session.add(actor)
            session.flush()
            project, workspace = _instrumentation_scope(session, actor)
            obj = _object(session, actor, project, workspace)
            context, subject = _context(session, actor, project, workspace, obj)
            service = PackageDeclarationBindingService(
                _factory(session), package_key="instrumentation",
            )
            _bind_context(
                service, actor, project, workspace, context, subject,
                "instrumentation.measurement_service.input",
            )
            session.commit()
        with pytest.raises(
            RuntimeError,
            match="engineering_object Context subjects exist",
        ):
            command.downgrade(alembic_config, PATCH_052_M1)
        assert _revision() == PATCH_052_HEAD
    finally:
        _truncate_disposable_rows()


def test_e051_upgrade_preserves_legacy_rows_and_safe_empty_downgrade_reupgrade() -> None:
    assert _revision() == PATCH_052_HEAD
    scope: dict[str, object] | None = None
    legacy_object_id = uuid4()
    try:
        scope = _seed_report_memory_scope()
        command.downgrade(alembic_config, PATCH_051_HEAD)
        assert _revision() == PATCH_051_HEAD

        with owner_engine.begin() as connection:
            connection.execute(text("""
                INSERT INTO engineering_objects (
                    id, organization_id, customer_id, project_id, workspace_id,
                    family, discipline, object_type, lifecycle, authority_standing,
                    version, creator_id, steward_id
                ) VALUES (
                    :id, :organization_id, :customer_id, :project_id, :workspace_id,
                    'electrical', 'electrical', 'motor', 'active', 'draft',
                    1, :owner_id, :owner_id
                )
            """), {**scope, "id": legacy_object_id})

        report_before = _row_json("technical_reports", scope["report_id"])
        memory_before = _row_json("organizational_memories", scope["memory_id"])
        command.upgrade(alembic_config, PATCH_052_HEAD)
        assert _revision() == PATCH_052_HEAD
        _assert_patch_052_schema()

        with owner_engine.connect() as connection:
            legacy = connection.execute(text("""
                SELECT origin_package_key, origin_project_configuration_revision,
                       origin_declaration_id
                FROM engineering_objects WHERE id=:id
            """), {"id": legacy_object_id}).one()
            assert tuple(legacy) == (None, None, None)
            assert connection.execute(text(
                "SELECT count(*) FROM engineering_identifiers "
                "WHERE engineering_object_id=:id"
            ), {"id": legacy_object_id}).scalar_one() == 0
        assert _row_json("technical_reports", scope["report_id"]) == report_before
        assert _row_json("organizational_memories", scope["memory_id"]) == memory_before

        # The accepted contract permits downgrade only when no PATCH-052 rows
        # exist. These rows are all truthful pre-Batch-2 state.
        command.downgrade(alembic_config, PATCH_051_HEAD)
        assert _revision() == PATCH_051_HEAD
        assert _row_json("technical_reports", scope["report_id"]) == report_before
        assert _row_json("organizational_memories", scope["memory_id"]) == memory_before
        command.upgrade(alembic_config, PATCH_052_HEAD)
        assert _revision() == PATCH_052_HEAD
        with owner_engine.connect() as connection:
            assert connection.execute(text(
                "SELECT count(*) FROM engineering_identifiers "
                "WHERE engineering_object_id=:id"
            ), {"id": legacy_object_id}).scalar_one() == 0
    finally:
        _truncate_disposable_rows()
    assert _revision() == PATCH_052_HEAD
