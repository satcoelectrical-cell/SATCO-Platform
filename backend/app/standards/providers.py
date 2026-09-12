"""Static policy seams. Batch 1 deliberately has no network provider adapter."""

from __future__ import annotations

from app.core.config import settings


def platform_catalog_admin_ids() -> frozenset[int]:
    values: set[int] = set()
    for raw in settings.STANDARDS_PLATFORM_CATALOG_ADMIN_USER_IDS.split(","):
        raw = raw.strip()
        if raw:
            values.add(int(raw))
    return frozenset(values)


def is_configured_provider(provider_id: str) -> bool:
    """Batch 1 permits the metadata-only reserved provider only.

    Retrieval provider registration belongs to Batch 2.
    """
    return provider_id == "registry_metadata"
