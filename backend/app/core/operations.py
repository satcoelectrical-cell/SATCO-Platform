"""PATCH-042 operational guards with deliberately non-disclosing outputs."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import ssl
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings


class ProductionConfigurationError(RuntimeError):
    pass


class GovernedWriteBlocked(RuntimeError):
    pass


REQUIRED_RELEASE_KEYS = frozenset(
    {
        "release_id",
        "git_commit",
        "backend_image_digest",
        "frontend_asset_digest",
        "expected_alembic_head",
        "configuration_schema_version",
        "migration_artifact_digest",
        "dependency_lock_digest",
        "package_lock_digest",
        "sbom_reference",
        "scan_evidence_reference",
        "signing_approver_evidence_reference",
        "created_at",
    }
)
MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
READ_ONLY_MODES = frozenset({"read_only", "RECOVERY_PROTECTION_DEGRADED"})


@dataclass(frozen=True)
class OperationalSnapshot:
    ready: bool
    mode: str


def validate_release_manifest(settings: Settings) -> dict[str, object]:
    """Validate the local immutable manifest without revealing it to callers."""

    path = Path(settings.SATCO_RELEASE_MANIFEST_PATH)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProductionConfigurationError("release_manifest") from exc
    if not isinstance(payload, dict) or not REQUIRED_RELEASE_KEYS.issubset(payload):
        raise ProductionConfigurationError("release_manifest")
    expected = payload.get("expected_alembic_head")
    if expected != settings.SATCO_EXPECTED_ALEMBIC_HEAD:
        raise ProductionConfigurationError("release_manifest")
    for key in REQUIRED_RELEASE_KEYS:
        if not isinstance(payload.get(key), str) or not payload[key]:
            raise ProductionConfigurationError("release_manifest")
    for key in (
        "backend_image_digest",
        "frontend_asset_digest",
        "migration_artifact_digest",
        "dependency_lock_digest",
        "package_lock_digest",
    ):
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(payload[key])):
            raise ProductionConfigurationError("release_manifest")
    if not re.fullmatch(r"[0-9a-f]{7,40}", str(payload["git_commit"])):
        raise ProductionConfigurationError("release_manifest")
    try:
        created_at = datetime.fromisoformat(
            str(payload["created_at"]).replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ProductionConfigurationError("release_manifest") from exc
    if created_at.tzinfo is None:
        raise ProductionConfigurationError("release_manifest")
    return payload


def validate_production_settings(settings: Settings) -> None:
    errors = settings.production_validation_errors()
    if errors:
        raise ProductionConfigurationError(errors[0])
    if settings.SATCO_ENVIRONMENT == "production":
        validate_release_manifest(settings)
        parsed = urlparse(settings.SATCO_OBJECT_HEALTH_URL)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ProductionConfigurationError("object_health")


def _database_ready(settings: Settings) -> bool:
    """Check connectivity and the expected Alembic head without business data."""

    from app.core.database import engine

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            observed_head = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
            if observed_head != settings.SATCO_EXPECTED_ALEMBIC_HEAD:
                return False
        if settings.DISCIPLINE_PACKAGE_PERSISTENCE_ENABLED:
            from app.core.database import validate_discipline_package_runtime_boundary
            from app.discipline_packages.descriptors.releases.release_051_core_v1 import RELEASE_051_CORE_V1
            from app.discipline_packages.registry import assemble_registry
            from app.services.discipline_package_registry_service import validate_source_projection_parity
            validate_discipline_package_runtime_boundary(engine, migration_role_name=settings.MIGRATION_DATABASE_ROLE)
            # The runtime role can only read projections.  Readiness verifies
            # that the one current projection is precisely the source release;
            # it never installs, activates, or repairs data.
            with Session(engine, autoflush=False) as session:
                validate_source_projection_parity(session, assemble_registry(RELEASE_051_CORE_V1))
        return True
    except Exception:
        return False


def _object_health_ready(settings: Settings) -> bool:
    """Call the monitor assertion, never the object store or an object key."""

    try:
        context = ssl.create_default_context(
            cafile=settings.SATCO_OBJECT_HEALTH_CA_FILE
        )
        request = Request(
            settings.SATCO_OBJECT_HEALTH_URL,
            method="HEAD",
            headers={"Accept": "application/json"},
        )
        with urlopen(  # nosec B310: validated HTTPS URL and governed CA
            request,
            timeout=2,
            context=context,
        ) as response:
            return 200 <= response.status < 300
    except Exception:
        return False


def _mode_payload(settings: Settings) -> dict[str, object]:
    if not settings.SATCO_OPS_MODE_FILE:
        return {"mode": "normal"}
    try:
        payload = json.loads(Path(settings.SATCO_OPS_MODE_FILE).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProductionConfigurationError("ops_mode") from exc
    if not isinstance(payload, dict) or payload.get("mode") not in {
        "normal", "read_only", "RECOVERY_PROTECTION_DEGRADED"
    }:
        raise ProductionConfigurationError("ops_mode")
    signature = payload.get("signature")
    if settings.SATCO_OPS_MODE_HMAC_KEY_FILE:
        key = Path(settings.SATCO_OPS_MODE_HMAC_KEY_FILE).read_bytes().strip()
        unsigned = {key: value for key, value in payload.items() if key != "signature"}
        encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
        expected = hmac.new(key, encoded, hashlib.sha256).hexdigest()
        if not isinstance(signature, str) or not hmac.compare_digest(signature, expected):
            raise ProductionConfigurationError("ops_mode")
    return payload


def operational_mode(settings: Settings) -> str:
    return str(_mode_payload(settings)["mode"])


def ensure_governed_write_allowed(settings: Settings, method: str) -> None:
    if method.upper() in MUTATING_METHODS and operational_mode(settings) in READ_ONLY_MODES:
        raise GovernedWriteBlocked("governed writes are temporarily unavailable")


def readiness_snapshot(settings: Settings) -> OperationalSnapshot:
    try:
        validate_production_settings(settings)
        mode = operational_mode(settings)
        if settings.SATCO_ENVIRONMENT == "production" and (
            not _database_ready(settings)
            or not _object_health_ready(settings)
        ):
            return OperationalSnapshot(ready=False, mode="unavailable")
        return OperationalSnapshot(ready=mode == "normal", mode=mode)
    except ProductionConfigurationError:
        return OperationalSnapshot(ready=False, mode="unavailable")


def safe_diagnostic_snapshot(settings: Settings) -> dict[str, str]:
    """Return only fixed-key categories; never pass through configuration values."""

    snapshot = readiness_snapshot(settings)
    return {
        "environment": settings.SATCO_ENVIRONMENT,
        "readiness": "ready" if snapshot.ready else "not_ready",
        "operational_mode": snapshot.mode,
        "expected_alembic_head": settings.SATCO_EXPECTED_ALEMBIC_HEAD or "not_configured",
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }
