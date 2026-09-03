#!/usr/bin/env python3
"""Deployment-only Registry projection installer; not imported by FastAPI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import sessionmaker

from app.core.database import DisciplinePackageGuardMode
from app.discipline_packages.contracts import RegistryReleaseManifestV1
from app.discipline_packages.registry import assemble_registry
from app.repositories.discipline_package_unit_of_work import DisciplinePackageUnitOfWork
from app.services.discipline_package_registry_service import DisciplinePackageRegistryService


def _installer_url(args: argparse.Namespace) -> str:
    password = Path(args.password_file).read_text(encoding="utf-8").strip()
    return URL.create("postgresql", username=args.user, password=password, host=args.host, port=args.port, database=args.database).render_as_string(hide_password=False)


def _validate_installer(engine, migration_role: str) -> None:
    with engine.connect() as connection:
        identity = connection.execute(text("SELECT current_user")).scalar_one()
        if identity != "satco_registry_installer" or identity == migration_role:
            raise RuntimeError("Registry installer identity is not authorized")
        flags = connection.execute(text("SELECT rolsuper OR rolbypassrls OR rolcreatedb OR rolcreaterole OR rolinherit FROM pg_roles WHERE rolname=current_user")).scalar_one()
        if flags or connection.execute(text("SELECT has_schema_privilege(current_user, 'public', 'CREATE')")).scalar_one():
            raise RuntimeError("Registry installer privilege boundary is unsafe")
        projection_tables = [
            "discipline_package_registry_releases", "discipline_package_descriptors",
            "discipline_package_registry_memberships", "discipline_package_compatibility_profiles",
            "discipline_package_registry_profile_memberships", "discipline_package_compatibility_members",
        ]
        grants = set(connection.execute(text(
            "SELECT table_name, privilege_type FROM information_schema.role_table_grants "
            "WHERE grantee=current_user AND table_name = ANY(CAST(:tables AS text[]))"
        ), {"tables": projection_tables}).all())
        expected = {(table, privilege) for table in projection_tables for privilege in ("SELECT", "INSERT")}
        update_columns = set(connection.execute(text(
            "SELECT column_name FROM information_schema.role_column_grants "
            "WHERE grantee=current_user AND table_name='discipline_package_registry_releases' "
            "AND privilege_type='UPDATE'"
        )).scalars())
        tenant_grants = connection.execute(text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.role_table_grants "
            "WHERE grantee=current_user AND table_name IN "
            "('organization_package_configuration_heads','organization_package_selections',"
            "'project_package_configuration_revisions','project_package_configuration_selections',"
            "'project_package_configuration_heads','package_configuration_audit_events'))"
        )).scalar_one()
        if grants != expected or update_columns != {"is_current"} or tenant_grants:
            raise RuntimeError("Registry installer grants are not exact")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, default=5432)
    parser.add_argument("--database", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--password-file", required=True)
    parser.add_argument("--migration-role", required=True)
    parser.add_argument("--activate", action="store_true")
    args = parser.parse_args()
    engine = create_engine(_installer_url(args))
    _validate_installer(engine, args.migration_role)
    manifest = RegistryReleaseManifestV1.model_validate_json(Path(args.manifest).read_text(encoding="utf-8"))
    registry = assemble_registry(manifest)
    service = DisciplinePackageRegistryService()
    with DisciplinePackageUnitOfWork(sessionmaker(bind=engine, autocommit=False, autoflush=False)) as uow:
        service.install(registry, uow)
        if args.activate:
            service.activate(str(registry.digest), uow)
        uow.commit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
