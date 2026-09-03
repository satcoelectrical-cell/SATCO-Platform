import os
from enum import Enum
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL, make_url
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()


def runtime_database_url() -> str:
    """Build the runtime URL only from the restricted runtime inputs."""

    password = os.getenv("DATABASE_PASSWORD")
    password_file = os.getenv("DATABASE_PASSWORD_FILE")
    if password_file:
        password = Path(password_file).read_text(encoding="utf-8").strip()

    required = {
        "host": os.getenv("DATABASE_HOST"),
        "port": int(os.getenv("DATABASE_PORT", "0")),
        "username": os.getenv("DATABASE_USER"),
        "password": password,
        "database": os.getenv("DATABASE_NAME"),
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError("runtime database settings are incomplete: " + ", ".join(missing))
    return URL.create(drivername="postgresql", **required).render_as_string(hide_password=False)


DATABASE_URL = runtime_database_url()


engine = create_engine(
    DATABASE_URL
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()


class DisciplinePackageGuardMode(str, Enum):
    SHARED = "shared"
    EXCLUSIVE = "exclusive"


PACKAGE_REGISTRY_GUARD_NAMESPACE = 1396790339
PACKAGE_REGISTRY_GUARD_CONTRACT = 51


def acquire_discipline_package_registry_guard(session, mode: DisciplinePackageGuardMode) -> None:
    """Acquire the governed transaction-scoped PATCH-051 PostgreSQL guard.

    The caller must own an already-open outer transaction.  This helper neither
    opens a Session nor completes a transaction.
    """

    if not session.in_transaction():
        raise RuntimeError("discipline package guard requires an active transaction")
    session.execute(text("SET LOCAL lock_timeout = '5s'"))
    function = "pg_advisory_xact_lock_shared" if mode is DisciplinePackageGuardMode.SHARED else "pg_advisory_xact_lock"
    session.execute(text(f"SELECT {function}(:namespace, :contract)"), {
        "namespace": PACKAGE_REGISTRY_GUARD_NAMESPACE,
        "contract": PACKAGE_REGISTRY_GUARD_CONTRACT,
    })


def validate_discipline_package_runtime_boundary(
    checked_engine: Engine = engine,
    *,
    migration_role_name: str | None = None,
) -> None:
    """Fail closed if the ordinary runtime can mutate Registry projections."""

    owner_role = migration_role_name or os.getenv("MIGRATION_DATABASE_ROLE")
    runtime_role = make_url(str(checked_engine.url)).username
    if not runtime_role or not owner_role or runtime_role == owner_role:
        raise RuntimeError("discipline package runtime ownership boundary is unsafe")
    tables = (
        "discipline_package_registry_releases", "discipline_package_descriptors",
        "discipline_package_registry_memberships", "discipline_package_compatibility_profiles",
        "discipline_package_registry_profile_memberships", "discipline_package_compatibility_members",
    )
    with checked_engine.connect() as connection:
        flags = connection.execute(text(
            "SELECT rolsuper, rolbypassrls, rolcreatedb, rolcreaterole, rolinherit "
            "FROM pg_roles WHERE rolname=current_user"
        )).mappings().one()
        if any(flags.values()) or connection.execute(text(
            "SELECT has_schema_privilege(current_user, 'public', 'CREATE')"
        )).scalar_one():
            raise RuntimeError("discipline package runtime has forbidden authority")
        grants = connection.execute(text(
            "SELECT table_name, privilege_type FROM information_schema.role_table_grants "
            "WHERE grantee=current_user AND table_name = ANY(CAST(:tables AS text[]))"
        ), {"tables": list(tables)}).all()
        observed = {(name, privilege) for name, privilege in grants}
        expected = {(name, "SELECT") for name in tables}
        if observed != expected:
            raise RuntimeError("discipline package projection grants are not read-only")


def validate_technical_report_runtime_boundary(
    checked_engine: Engine = engine,
    *,
    migration_database_url: str | None = None,
    migration_role_name: str | None = None,
    require_objects: bool = True,
) -> None:
    """Fail closed when the normal runtime can bypass PATCH-032 protections."""

    runtime_role = make_url(str(checked_engine.url)).username
    owner_role = migration_role_name
    if migration_database_url:
        owner_role = make_url(migration_database_url).username
    owner_role = owner_role or os.getenv("MIGRATION_DATABASE_ROLE")
    if not owner_role:
        raise RuntimeError("MIGRATION_DATABASE_ROLE is required for role separation validation")
    if not runtime_role or not owner_role or runtime_role == owner_role:
        raise RuntimeError("runtime and migration PostgreSQL roles must be distinct")

    with checked_engine.connect() as connection:
        role = connection.execute(
            text(
                "SELECT rolname, rolsuper, rolbypassrls, rolcreatedb, rolcreaterole, rolinherit "
                "FROM pg_roles WHERE rolname = current_user"
            )
        ).mappings().one()
        if any(role[key] for key in ("rolsuper", "rolbypassrls", "rolcreatedb", "rolcreaterole", "rolinherit")):
            raise RuntimeError("runtime PostgreSQL role has forbidden privileges")
        membership = connection.execute(
            text("SELECT EXISTS (SELECT 1 FROM pg_auth_members WHERE member=(SELECT oid FROM pg_roles WHERE rolname=current_user))")
        ).scalar_one()
        schema_create = connection.execute(
            text("SELECT has_schema_privilege(current_user, 'public', 'CREATE')")
        ).scalar_one()
        if membership or schema_create:
            raise RuntimeError("runtime PostgreSQL role has forbidden membership or schema authority")
        if require_objects:
            required_tables = (
                "technical_reports", "technical_report_provenance_entries",
                "technical_report_outbox", "technical_report_idempotency",
            )
            missing_tables = connection.execute(
                text("SELECT name FROM unnest(CAST(:names AS text[])) name WHERE to_regclass('public.' || name) IS NULL"),
                {"names": list(required_tables)},
            ).scalars().all()
            owned = connection.execute(
                text(
                    "SELECT EXISTS ("
                    "SELECT 1 FROM pg_class c JOIN pg_roles r ON r.oid=c.relowner "
                    "WHERE c.relname IN ('technical_reports','technical_report_provenance_entries',"
                    "'technical_report_outbox','technical_report_idempotency') AND r.rolname=current_user)"
                )
            ).scalar_one()
            owner_mismatch = connection.execute(
                text(
                    "SELECT EXISTS (SELECT 1 FROM pg_class c JOIN pg_roles r ON r.oid=c.relowner "
                    "WHERE c.relname IN ('technical_reports','technical_report_provenance_entries',"
                    "'technical_report_outbox','technical_report_idempotency') AND r.rolname<>:owner_role)"
                ),
                {"owner_role": owner_role},
            ).scalar_one()
            function_owned = connection.execute(
                text(
                    "SELECT EXISTS (SELECT 1 FROM pg_proc p JOIN pg_roles r ON r.oid=p.proowner "
                    "WHERE p.proname IN ('technical_report_canonical_json','technical_report_historical_basis_valid',"
                    "'technical_report_provenance_json_valid','technical_report_root_accepted_immutable',"
                    "'technical_report_provenance_accepted_immutable') AND r.rolname=current_user)"
                )
            ).scalar_one()
            function_owner_mismatch = connection.execute(
                text(
                    "SELECT EXISTS (SELECT 1 FROM pg_proc p JOIN pg_roles r ON r.oid=p.proowner "
                    "WHERE p.proname IN ('technical_report_canonical_json','technical_report_historical_basis_valid',"
                    "'technical_report_provenance_json_valid','technical_report_root_accepted_immutable',"
                    "'technical_report_provenance_accepted_immutable') AND r.rolname<>:owner_role)"
                ),
                {"owner_role": owner_role},
            ).scalar_one()
            triggers_ok = connection.execute(
                text(
                    "SELECT count(*) = 2 FROM pg_trigger "
                    "WHERE tgname IN ('trg_technical_reports_accepted_immutable',"
                    "'trg_technical_report_provenance_accepted_immutable') AND NOT tgisinternal AND tgenabled='O'"
                )
            ).scalar_one()
            functions_ok = connection.execute(
                text(
                    "SELECT count(*) = 5 FROM pg_proc WHERE proname IN "
                    "('technical_report_canonical_json','technical_report_historical_basis_valid',"
                    "'technical_report_provenance_json_valid','technical_report_root_accepted_immutable',"
                    "'technical_report_provenance_accepted_immutable')"
                )
            ).scalar_one()
            executable = connection.execute(
                text(
                    "SELECT EXISTS (SELECT 1 FROM pg_proc WHERE proname IN "
                    "('technical_report_canonical_json','technical_report_historical_basis_valid',"
                    "'technical_report_provenance_json_valid','technical_report_root_accepted_immutable',"
                    "'technical_report_provenance_accepted_immutable') "
                    "AND has_function_privilege(current_user, oid, 'EXECUTE'))"
                )
            ).scalar_one()
            forbidden_grants = connection.execute(
                text(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.role_table_grants "
                    "WHERE grantee=current_user AND table_name IN "
                    "('technical_reports','technical_report_outbox','technical_report_idempotency','audit_logs') "
                    "AND privilege_type IN ('DELETE','TRUNCATE','REFERENCES','TRIGGER'))"
                )
            ).scalar_one()
            root_update_columns = set(connection.execute(text(
                "SELECT column_name FROM information_schema.role_column_grants WHERE grantee=current_user "
                "AND table_name='technical_reports' AND privilege_type='UPDATE'"
            )).scalars())
            outbox_update_columns = set(connection.execute(text(
                "SELECT column_name FROM information_schema.role_column_grants WHERE grantee=current_user "
                "AND table_name='technical_report_outbox' AND privilege_type='UPDATE'"
            )).scalars())
            idempotency_update_columns = set(connection.execute(text(
                "SELECT column_name FROM information_schema.role_column_grants WHERE grantee=current_user "
                "AND table_name='technical_report_idempotency' AND privilege_type='UPDATE'"
            )).scalars())
            audit_grants = set(connection.execute(text(
                "SELECT privilege_type FROM information_schema.role_table_grants WHERE grantee=current_user "
                "AND table_name='audit_logs'"
            )).scalars())
            expected_root_updates = {
                "engineering_scope", "draft_content", "assumptions", "uncertainty",
                "limitations", "conclusions", "recommendations", "is_preliminary",
                "evidence_deficiencies", "unresolved_issues", "follow_up_requirements",
                "draft_revision_id", "draft_revision_number", "lifecycle", "version",
                "accepted_snapshot", "accepted_snapshot_digest", "accepted_by_id",
                "accepted_at", "accepted_draft_revision_id", "accepted_aggregate_version",
                "updated_at",
            }
            grants_ok = (
                root_update_columns == expected_root_updates
                and outbox_update_columns == {"published_at"}
                and idempotency_update_columns == {"status", "aggregate_id", "result", "updated_at"}
                and audit_grants == {"SELECT", "INSERT"}
            )
            if (missing_tables or owned or owner_mismatch or function_owned
                    or function_owner_mismatch or not triggers_ok or not functions_ok
                    or executable or forbidden_grants or not grants_ok):
                raise RuntimeError("Technical Report ownership or trigger enforcement is unsafe")


def validate_organizational_memory_runtime_boundary(
    checked_engine: Engine = engine,
    *,
    migration_database_url: str | None = None,
    migration_role_name: str | None = None,
    require_objects: bool = True,
) -> None:
    """Fail closed when runtime can bypass PATCH-034 persistence guards."""

    runtime_role = make_url(str(checked_engine.url)).username
    owner_role = migration_role_name
    if migration_database_url:
        owner_role = make_url(migration_database_url).username
    owner_role = owner_role or os.getenv("MIGRATION_DATABASE_ROLE")
    if not runtime_role or not owner_role or runtime_role == owner_role:
        raise RuntimeError("Organizational Memory runtime and migration roles must be distinct")

    with checked_engine.connect() as connection:
        role = connection.execute(text(
            "SELECT rolsuper, rolbypassrls, rolcreatedb, rolcreaterole, rolinherit "
            "FROM pg_roles WHERE rolname=current_user"
        )).mappings().one()
        membership = connection.execute(text(
            "SELECT EXISTS (SELECT 1 FROM pg_auth_members "
            "WHERE member=(SELECT oid FROM pg_roles WHERE rolname=current_user))"
        )).scalar_one()
        schema_create = connection.execute(text(
            "SELECT has_schema_privilege(current_user,'public','CREATE')"
        )).scalar_one()
        if any(role.values()) or membership or schema_create:
            raise RuntimeError("Organizational Memory runtime role has forbidden authority")
        if not require_objects:
            return

        tables = (
            "organizational_memories",
            "organizational_memory_standing_history",
            "organizational_memory_events_outbox",
            "organizational_memory_idempotency",
        )
        functions = (
            "organizational_memory_projection_v1_valid(jsonb)",
            "organizational_memory_manifest_v1_valid(jsonb)",
            "organizational_memory_event_payload_v1_valid(text,jsonb)",
            "organizational_memory_idempotency_result_v1_valid(text,jsonb)",
            "organizational_memory_canonical_json(jsonb)",
            "organizational_memory_lineage_guard()",
            "organizational_memory_root_guard()",
            "organizational_memory_history_guard()",
            "organizational_memory_side_record_guard()",
        )
        triggers = {
            "a_organizational_memory_lineage_guard": (
                "organizational_memories", "organizational_memory_lineage_guard()",
            ),
            "b_organizational_memory_root_guard": (
                "organizational_memories", "organizational_memory_root_guard()",
            ),
            "organizational_memory_history_guard": (
                "organizational_memory_standing_history",
                "organizational_memory_history_guard()",
            ),
            "organizational_memory_outbox_guard": (
                "organizational_memory_events_outbox",
                "organizational_memory_side_record_guard()",
            ),
            "organizational_memory_idempotency_guard": (
                "organizational_memory_idempotency",
                "organizational_memory_side_record_guard()",
            ),
        }
        missing_tables = connection.execute(text(
            "SELECT name FROM unnest(CAST(:names AS text[])) name "
            "WHERE to_regclass('public.'||name) IS NULL"
        ), {"names": list(tables)}).scalars().all()
        owner_mismatch = connection.execute(text(
            "SELECT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "JOIN pg_roles r ON r.oid=c.relowner WHERE n.nspname='public' "
            "AND c.relname=ANY(CAST(:names AS text[])) AND r.rolname<>:owner)"
        ), {"names": list(tables), "owner": owner_role}).scalar_one()
        function_rows = connection.execute(text(
            "SELECT signature, n.nspname, r.rolname, p.prosecdef, "
            "has_function_privilege(current_user,p.oid,'EXECUTE') executable "
            "FROM unnest(CAST(:signatures AS text[])) signature "
            "LEFT JOIN pg_proc p ON p.oid=to_regprocedure('public.'||signature) "
            "LEFT JOIN pg_namespace n ON n.oid=p.pronamespace "
            "LEFT JOIN pg_roles r ON r.oid=p.proowner"
        ), {"signatures": list(functions)}).mappings().all()
        functions_ok = len(function_rows) == len(functions) and all(
            row["nspname"] == "public"
            and row["rolname"] == owner_role
            and row["prosecdef"] is True
            and row["executable"] is False
            for row in function_rows
        )
        trigger_rows = connection.execute(text(
            "SELECT t.tgname,c.relname,p.oid::regprocedure::text signature,t.tgenabled,"
            "nt.nspname table_schema,np.nspname function_schema,r.rolname function_owner "
            "FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
            "JOIN pg_namespace nt ON nt.oid=c.relnamespace JOIN pg_proc p ON p.oid=t.tgfoid "
            "JOIN pg_namespace np ON np.oid=p.pronamespace JOIN pg_roles r ON r.oid=p.proowner "
            "WHERE t.tgname=ANY(CAST(:names AS text[])) AND NOT t.tgisinternal"
        ), {"names": list(triggers)}).mappings().all()
        actual_triggers = {
            row["tgname"]: (row["relname"], row["signature"])
            for row in trigger_rows
            if row["tgenabled"] == "O" and row["table_schema"] == "public"
            and row["function_schema"] == "public" and row["function_owner"] == owner_role
        }
        triggers_ok = actual_triggers == triggers
        forbidden = connection.execute(text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.role_table_grants "
            "WHERE grantee=current_user AND table_name=ANY(CAST(:names AS text[])) "
            "AND privilege_type IN ('DELETE','TRUNCATE','REFERENCES','TRIGGER'))"
        ), {"names": list(tables)}).scalar_one()

        def update_columns(table_name: str) -> set[str]:
            return set(connection.execute(text(
                "SELECT column_name FROM information_schema.role_column_grants "
                "WHERE grantee=current_user AND table_name=:table_name "
                "AND privilege_type='UPDATE'"
            ), {"table_name": table_name}).scalars())

        table_grants = set(connection.execute(text(
            "SELECT table_name,privilege_type FROM information_schema.role_table_grants "
            "WHERE table_schema='public' AND grantee=current_user "
            "AND table_name=ANY(CAST(:names AS text[]))"
        ), {"names": list(tables)}).tuples())
        audit_grants = set(connection.execute(text(
            "SELECT privilege_type FROM information_schema.role_table_grants "
            "WHERE table_schema='public' AND grantee=current_user AND table_name='audit_logs'"
        )).scalars())
        grants_ok = (
            table_grants == {
                (table_name, privilege)
                for table_name in tables for privilege in ("INSERT", "SELECT")
            }
            and update_columns("organizational_memories") == {
                "version", "standing", "withdrawn_by_id", "withdrawn_at",
                "withdrawal_reason", "superseded_by_id", "superseded_at",
                "supersession_reason", "replacement_memory_id", "updated_at",
            }
            and update_columns("organizational_memory_standing_history") == set()
            and update_columns("organizational_memory_events_outbox") == {
                "published_at", "attempt_count", "last_error_category",
            }
            and update_columns("organizational_memory_idempotency") == {
                "status", "result_schema_version", "safe_result", "updated_at",
                "completed_at",
            }
            and audit_grants == {"INSERT", "SELECT"}
        )
        if (missing_tables or owner_mismatch or not functions_ok
                or not triggers_ok or forbidden or not grants_ok):
            raise RuntimeError("Organizational Memory ownership or guard enforcement is unsafe")


if os.getenv("TECHNICAL_REPORT_PERSISTENCE_ENABLED", "false").lower() in {"1", "true", "yes"}:
    validate_technical_report_runtime_boundary(
        migration_role_name=os.getenv("MIGRATION_DATABASE_ROLE"),
    )

if os.getenv("ORGANIZATIONAL_MEMORY_PERSISTENCE_ENABLED", "false").lower() in {"1", "true", "yes"}:
    validate_organizational_memory_runtime_boundary(
        migration_role_name=os.getenv("MIGRATION_DATABASE_ROLE"),
    )

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
