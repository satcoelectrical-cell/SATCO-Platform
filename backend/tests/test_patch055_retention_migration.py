"""PATCH-055 retention-governance migration qualification."""

from uuid import uuid4

from alembic import command
import pytest
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.organization import Organization
from app.models.project import Project
from app.models.user import User

from conftest import TEST_DATABASE_REVISION, alembic_config, owner_engine


PATCH_054_HEAD = "e05400000006"
PATCH_055_HEAD = "e05500000002"

RETENTION_TABLES = {
    "retention_records",
    "retention_holds",
    "retention_disposition_decisions",
    "retention_exports",
    "retention_export_subjects",
    "retention_recoveries",
    "retention_idempotency",
    "retention_outbox",
}


def _revision() -> str:
    with owner_engine.connect() as connection:
        return connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()


def _truncate_patch055_rows() -> None:
    with owner_engine.begin() as connection:
        connection.exec_driver_sql(
            """
            TRUNCATE TABLE
                retention_outbox,
                retention_idempotency,
                retention_recoveries,
                retention_export_subjects,
                retention_exports,
                retention_disposition_decisions,
                retention_holds,
                retention_records
            CASCADE
            """
        )


@pytest.fixture(scope="module", autouse=True)
def _patch055_boundary():
    command.upgrade(alembic_config, PATCH_055_HEAD)
    _truncate_patch055_rows()
    try:
        yield
    finally:
        command.upgrade(alembic_config, PATCH_055_HEAD)
        _truncate_patch055_rows()
        command.upgrade(alembic_config, TEST_DATABASE_REVISION)


def test_patch055_revision_is_repository_head() -> None:
    assert TEST_DATABASE_REVISION == PATCH_055_HEAD
    assert _revision() == PATCH_055_HEAD


def test_patch055_creates_exact_retention_tables() -> None:
    schema = inspect(owner_engine)
    tables = set(schema.get_table_names())
    assert RETENTION_TABLES <= tables


def test_retention_idempotency_has_exact_physical_columns() -> None:
    columns = {
        column["name"]
        for column in inspect(owner_engine).get_columns("retention_idempotency")
    }
    assert columns == {
        "organization_id",
        "actor_user_id",
        "operation",
        "idempotency_key",
        "request_digest",
        "status",
        "safe_result",
        "created_at",
        "updated_at",
        "completed_at",
    }
    assert "id" not in columns


def test_patch055_partial_unique_indexes_exist() -> None:
    schema = inspect(owner_engine)

    record_indexes = {
        row["name"]: row
        for row in schema.get_indexes("retention_records")
    }
    assert "uq_retention_record_current_subject" in record_indexes
    assert record_indexes["uq_retention_record_current_subject"]["unique"] is True

    hold_indexes = {
        row["name"]: row
        for row in schema.get_indexes("retention_holds")
    }
    assert "uq_retention_hold_current_active_subject" in hold_indexes
    assert hold_indexes["uq_retention_hold_current_active_subject"]["unique"] is True


def test_patch055_key_types_match_normative_contract() -> None:
    schema = inspect(owner_engine)

    records = {
        column["name"]: str(column["type"]).upper()
        for column in schema.get_columns("retention_records")
    }
    assert "UUID" in records["organization_id"]
    assert "INTEGER" in records["project_id"]
    assert "INTEGER" in records["workspace_id"]
    assert "UUID" in records["subject_id"]

    idempotency = {
        column["name"]: str(column["type"]).upper()
        for column in schema.get_columns("retention_idempotency")
    }
    assert "UUID" in idempotency["organization_id"]
    assert "INTEGER" in idempotency["actor_user_id"]
    assert "UUID" in idempotency["idempotency_key"]
    assert "CHAR(64)" in idempotency["request_digest"]
    assert "JSONB" in idempotency["safe_result"]

    outbox = {
        column["name"]: str(column["type"]).upper()
        for column in schema.get_columns("retention_outbox")
    }
    assert "JSONB" in outbox["payload"]


def test_patch055_empty_downgrade_and_reupgrade_are_safe() -> None:
    assert _revision() == PATCH_055_HEAD
    _truncate_patch055_rows()

    command.downgrade(alembic_config, PATCH_054_HEAD)
    assert _revision() == PATCH_054_HEAD

    tables = set(inspect(owner_engine).get_table_names())
    assert RETENTION_TABLES.isdisjoint(tables)

    command.upgrade(alembic_config, PATCH_055_HEAD)
    assert _revision() == PATCH_055_HEAD
    assert RETENTION_TABLES <= set(inspect(owner_engine).get_table_names())


def test_patch055_populated_downgrade_fails_closed() -> None:
    organization_id = uuid4()
    suffix = uuid4().hex[:10]
    user_id = None
    customer_id = None
    project_id = None

    try:
        with Session(owner_engine, expire_on_commit=False) as session:
            organization = Organization(
                id=organization_id,
                name=f"PATCH-055 migration {suffix}",
                slug=f"patch055-{suffix}",
                is_active=True,
            )
            session.add(organization)
            session.flush()

            user = User(
                email=f"patch055-{suffix}@example.com",
                username=f"patch055-{suffix}",
                hashed_password="not-used",
                full_name="PATCH-055 migration actor",
                role="engineer",
                is_active=True,
                activation_pending=True,
            )
            session.add(user)
            session.flush()
            user_id = user.id

            customer = Customer(
                organization_id=organization_id,
                name=f"PATCH-055 customer {suffix}",
            )
            session.add(customer)
            session.flush()
            customer_id = customer.id

            project = Project(
                organization_id=organization_id,
                project_code=f"SAT-PRJ-2099-{10000 + uuid4().int % 900000:06d}",
                name="PATCH-055 populated downgrade guard",
                customer_id=customer.id,
                owner_id=user.id,
            )
            session.add(project)
            session.flush()
            project_id = project.id

            session.execute(
                text(
                    """
                    INSERT INTO retention_records (
                        id,
                        organization_id,
                        project_id,
                        workspace_id,
                        subject_kind,
                        subject_id,
                        version,
                        is_current,
                        mode,
                        retain_until,
                        policy_source,
                        basis_code,
                        rationale,
                        created_by_user_id,
                        request_digest,
                        record_digest
                    ) VALUES (
                        :id,
                        :organization_id,
                        :project_id,
                        NULL,
                        'evidence',
                        :subject_id,
                        1,
                        true,
                        'retain_indefinitely',
                        NULL,
                        'platform_default',
                        'platform.default',
                        NULL,
                        :user_id,
                        :request_digest,
                        :record_digest
                    )
                    """
                ),
                {
                    "id": uuid4(),
                    "organization_id": organization_id,
                    "project_id": project.id,
                    "subject_id": uuid4(),
                    "user_id": user.id,
                    "request_digest": "a" * 64,
                    "record_digest": "b" * 64,
                },
            )
            session.commit()

        with pytest.raises(
            RuntimeError,
            match="PATCH-055 downgrade refused",
        ):
            command.downgrade(alembic_config, PATCH_054_HEAD)

        assert _revision() == PATCH_055_HEAD
    finally:
        command.upgrade(alembic_config, PATCH_055_HEAD)
        _truncate_patch055_rows()

        with owner_engine.begin() as connection:
            if project_id is not None:
                connection.execute(
                    text("DELETE FROM projects WHERE id=:id"),
                    {"id": project_id},
                )
            if customer_id is not None:
                connection.execute(
                    text("DELETE FROM customers WHERE id=:id"),
                    {"id": customer_id},
                )
            if user_id is not None:
                connection.execute(
                    text("DELETE FROM users WHERE id=:id"),
                    {"id": user_id},
                )
            connection.execute(
                text("DELETE FROM organizations WHERE id=:id"),
                {"id": organization_id},
            )


def _truncate_all_disposable_rows() -> None:
    """Empty only the disposable qualification database."""
    table_names = sorted(
        table_name
        for table_name in inspect(owner_engine).get_table_names()
        if table_name != "alembic_version"
    )
    if not table_names:
        return

    quoted = ", ".join(f'"{name}"' for name in table_names)
    with owner_engine.begin() as connection:
        connection.exec_driver_sql(f"TRUNCATE TABLE {quoted} CASCADE")


def _row_json(table_name: str, row_id: object) -> str:
    with owner_engine.connect() as connection:
        return connection.execute(
            text(
                f'SELECT to_jsonb(value)::text '
                f'FROM "{table_name}" value WHERE id=:id'
            ),
            {"id": row_id},
        ).scalar_one()


def test_patch055_exact_empty_schema_delta_and_no_backfill() -> None:
    assert _revision() == PATCH_055_HEAD
    _truncate_patch055_rows()

    command.downgrade(alembic_config, PATCH_054_HEAD)
    assert _revision() == PATCH_054_HEAD

    before = set(inspect(owner_engine).get_table_names())
    assert RETENTION_TABLES.isdisjoint(before)

    command.upgrade(alembic_config, PATCH_055_HEAD)
    assert _revision() == PATCH_055_HEAD

    after = set(inspect(owner_engine).get_table_names())
    assert after - before == RETENTION_TABLES

    with owner_engine.connect() as connection:
        for table_name in RETENTION_TABLES:
            assert connection.execute(
                text(f'SELECT COUNT(*) FROM "{table_name}"')
            ).scalar_one() == 0


def test_patch055_exact_constraints_foreign_keys_and_partial_predicates() -> None:
    schema = inspect(owner_engine)

    expected_checks = {
        "retention_records": {
            "ck_retention_record_version",
            "ck_retention_record_subject_kind",
            "ck_retention_record_mode",
            "ck_retention_record_policy_source",
            "ck_retention_record_basis_code",
            "ck_retention_record_until_shape",
            "ck_retention_record_digest",
        },
        "retention_holds": {
            "ck_retention_hold_subject_kind",
            "ck_retention_hold_status",
            "ck_retention_hold_reason_code",
            "ck_retention_hold_version",
            "ck_retention_hold_digest",
            "ck_retention_hold_release_shape",
        },
        "retention_disposition_decisions": {
            "ck_retention_disposition_subject_kind",
            "ck_retention_disposition_eligibility",
            "ck_retention_disposition_decision",
            "ck_retention_disposition_subject_version",
            "ck_retention_disposition_request_digest",
        },
        "retention_exports": {
            "ck_retention_export_status",
            "ck_retention_export_format",
            "ck_retention_export_request_digest",
            "ck_retention_export_aggregate_digest",
            "ck_retention_export_completed_shape",
        },
        "retention_export_subjects": {
            "ck_retention_export_subject_kind",
            "ck_retention_export_subject_ordinal",
            "ck_retention_export_subject_version",
            "ck_retention_export_subject_digest",
        },
        "retention_recoveries": {
            "ck_retention_recovery_subject_kind",
            "ck_retention_recovery_status",
            "ck_retention_recovery_expected_digest",
            "ck_retention_recovery_verified_digest",
            "ck_retention_recovery_request_digest",
        },
        "retention_idempotency": {
            "ck_retention_idempotency_status",
            "ck_retention_idempotency_request_digest",
            "ck_retention_idempotency_completion_shape",
        },
        "retention_outbox": {
            "ck_retention_outbox_aggregate_version",
            "ck_retention_outbox_payload_schema",
            "ck_retention_outbox_attempt_count",
        },
    }

    for table_name, expected in expected_checks.items():
        actual = {
            row["name"]
            for row in schema.get_check_constraints(table_name)
        }
        assert actual == expected

    for table_name in RETENTION_TABLES:
        for foreign_key in schema.get_foreign_keys(table_name):
            assert foreign_key["options"].get("ondelete") == "RESTRICT"

    record_fks = schema.get_foreign_keys("retention_records")
    supersedes = next(
        fk for fk in record_fks
        if fk["constrained_columns"] == ["supersedes_id"]
    )
    assert supersedes["referred_table"] == "retention_records"
    assert supersedes["referred_columns"] == ["id"]

    hold_fks = schema.get_foreign_keys("retention_holds")
    predecessor = next(
        fk for fk in hold_fks
        if fk["constrained_columns"] == ["predecessor_row_id"]
    )
    assert predecessor["referred_table"] == "retention_holds"
    assert predecessor["referred_columns"] == ["row_id"]

    record_index = next(
        row for row in schema.get_indexes("retention_records")
        if row["name"] == "uq_retention_record_current_subject"
    )
    record_predicate = str(
        record_index.get("dialect_options", {}).get("postgresql_where", "")
    ).lower()
    assert record_index["unique"] is True
    assert "is_current" in record_predicate

    hold_index = next(
        row for row in schema.get_indexes("retention_holds")
        if row["name"] == "uq_retention_hold_current_active_subject"
    )
    hold_predicate = str(
        hold_index.get("dialect_options", {}).get("postgresql_where", "")
    ).lower()
    assert hold_index["unique"] is True
    assert "is_current" in hold_predicate
    assert "status" in hold_predicate
    assert "active" in hold_predicate


def test_patch055_populated_e054_upgrade_preserves_legacy_row() -> None:
    assert _revision() == PATCH_055_HEAD
    _truncate_patch055_rows()

    organization_id = uuid4()
    suffix = uuid4().hex[:10]

    command.downgrade(alembic_config, PATCH_054_HEAD)
    assert _revision() == PATCH_054_HEAD

    try:
        with Session(owner_engine, expire_on_commit=False) as session:
            organization = Organization(
                id=organization_id,
                name=f"PATCH-055 historical {suffix}",
                slug=f"patch055-historical-{suffix}",
                is_active=True,
            )
            session.add(organization)
            session.commit()

        organization_before = _row_json(
            "organizations",
            organization_id,
        )

        before_tables = set(inspect(owner_engine).get_table_names())
        assert RETENTION_TABLES.isdisjoint(before_tables)

        command.upgrade(alembic_config, PATCH_055_HEAD)
        assert _revision() == PATCH_055_HEAD

        organization_after = _row_json(
            "organizations",
            organization_id,
        )
        assert organization_after == organization_before

        after_tables = set(inspect(owner_engine).get_table_names())
        assert after_tables - before_tables == RETENTION_TABLES

        with owner_engine.connect() as connection:
            for table_name in RETENTION_TABLES:
                assert connection.execute(
                    text(f'SELECT COUNT(*) FROM "{table_name}"')
                ).scalar_one() == 0
    finally:
        command.upgrade(alembic_config, PATCH_055_HEAD)
        _truncate_patch055_rows()
        with owner_engine.begin() as connection:
            connection.execute(
                text("DELETE FROM organizations WHERE id=:id"),
                {"id": organization_id},
            )


def test_patch055_clean_base_to_head_install() -> None:
    assert _revision() == PATCH_055_HEAD

    _truncate_all_disposable_rows()
    command.downgrade(alembic_config, "base")

    with owner_engine.connect() as connection:
        assert connection.execute(
            text("SELECT COUNT(*) FROM alembic_version")
        ).scalar_one() == 0

    command.upgrade(alembic_config, PATCH_055_HEAD)

    assert _revision() == PATCH_055_HEAD
    tables = set(inspect(owner_engine).get_table_names())
    assert RETENTION_TABLES <= tables

    with owner_engine.connect() as connection:
        for table_name in RETENTION_TABLES:
            assert connection.execute(
                text(f'SELECT COUNT(*) FROM "{table_name}"')
            ).scalar_one() == 0
