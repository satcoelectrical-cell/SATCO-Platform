"""Central runtime construction policy for the PATCH-051 entitlement seam."""

from __future__ import annotations

from sqlalchemy.orm import sessionmaker

from app.adapters.commercial_entitlement import CommercialEntitlementAdapter
from app.adapters.discipline_package_registry import NonCommercialEntitlementAdapter
from app.core.config import Settings
from app.core.operations import ProductionConfigurationError


def runtime_entitlement_adapter(
    *,
    configured_settings: Settings,
    session_factory: sessionmaker,
    user_id: int | None,
):
    """Build the runtime entitlement adapter without a production downgrade path."""

    if configured_settings.SATCO_COMMERCIAL_ENTITLEMENT_ENABLED:
        return CommercialEntitlementAdapter(
            session_factory,
            user_id=user_id,
        )

    if configured_settings.SATCO_ENVIRONMENT == "production":
        raise ProductionConfigurationError("commercial_entitlement")

    return NonCommercialEntitlementAdapter()
