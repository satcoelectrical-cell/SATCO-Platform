from types import SimpleNamespace

import pytest

from app.adapters.commercial_entitlement import CommercialEntitlementAdapter
from app.adapters.discipline_package_registry import NonCommercialEntitlementAdapter
from app.adapters.runtime_entitlement import runtime_entitlement_adapter
from app.core.operations import ProductionConfigurationError


def _settings(*, environment: str, commercial_enabled: bool):
    return SimpleNamespace(
        SATCO_ENVIRONMENT=environment,
        SATCO_COMMERCIAL_ENTITLEMENT_ENABLED=commercial_enabled,
    )


def test_runtime_factory_uses_commercial_adapter_when_enabled():
    factory = object()

    adapter = runtime_entitlement_adapter(
        configured_settings=_settings(
            environment="production",
            commercial_enabled=True,
        ),
        session_factory=factory,
        user_id=42,
    )

    assert isinstance(adapter, CommercialEntitlementAdapter)
    assert adapter.session_factory is factory
    assert adapter.user_id == 42


def test_runtime_factory_fails_closed_when_production_commercial_is_disabled():
    with pytest.raises(
        ProductionConfigurationError,
        match="commercial_entitlement",
    ):
        runtime_entitlement_adapter(
            configured_settings=_settings(
                environment="production",
                commercial_enabled=False,
            ),
            session_factory=object(),
            user_id=42,
        )


@pytest.mark.parametrize("environment", ["development", "test"])
def test_runtime_factory_allows_explicit_noncommercial_outside_production(
    environment,
):
    adapter = runtime_entitlement_adapter(
        configured_settings=_settings(
            environment=environment,
            commercial_enabled=False,
        ),
        session_factory=object(),
        user_id=42,
    )

    assert isinstance(adapter, NonCommercialEntitlementAdapter)
