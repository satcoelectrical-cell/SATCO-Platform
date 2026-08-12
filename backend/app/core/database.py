import os

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL, make_url
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()


def runtime_database_url() -> str:
    """Build the runtime URL only from the restricted runtime inputs."""

    required = {
        "host": os.getenv("DATABASE_HOST"),
        "port": int(os.getenv("DATABASE_PORT", "0")),
        "username": os.getenv("DATABASE_USER"),
        "password": os.getenv("DATABASE_PASSWORD"),
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


if os.getenv("TECHNICAL_REPORT_PERSISTENCE_ENABLED", "false").lower() in {"1", "true", "yes"}:
    validate_technical_report_runtime_boundary(
        migration_role_name=os.getenv("MIGRATION_DATABASE_ROLE"),
    )

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
