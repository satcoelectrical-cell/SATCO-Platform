import os
from pathlib import Path


def test_bootstrap_and_migration_name_both_fixed_roles():
    # The backend test image mounts only ``backend/`` at /app.  A caller that
    # needs to inspect the governed compose/bootstrap source supplies the
    # read-only repository root explicitly; local source runs retain the
    # normal repository-relative path.
    repository_root = Path(os.environ.get("SATCO_REPOSITORY_ROOT", Path(__file__).resolve().parents[2]))
    bootstrap = (repository_root / "postgres/init/001_satco_database_roles.sh").read_text()
    # Migration source is in the always-mounted backend image even when the
    # compose-root bootstrap source is supplied through the test seam above.
    migration = (Path(__file__).resolve().parents[1] / "migrations/versions/e05100000001_registry_configuration_audit.py").read_text()
    assert "satco_registry_installer" in bootstrap
    assert "satco_registry_installer" in migration
    assert "GRANT UPDATE (is_current)" in migration
