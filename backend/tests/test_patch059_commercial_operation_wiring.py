from uuid import UUID

import pytest

import app.api.v1.routers.discipline_package_operations as router_module
from app.core.config import settings
from app.enums.discipline_package import EntitlementDecision, EntitlementOperation
from app.services.electrical_package_service import (
    ElectricalPackageService,
    PackageProtectedNotFound,
    PackageUnavailable,
)
from app.services.instrumentation_package_service import InstrumentationPackageService
from app.services.control_automation_package_service import ControlAutomationPackageService


ORG = UUID("00000000-0000-4000-8000-000000000001")


@pytest.mark.parametrize(
    ("declaration_id", "expected"),
    [
        ("electrical.object.motor", "electrical"),
        ("instrumentation.object.transmitter", "instrumentation"),
        ("control_automation.object.plc", "control_automation"),
    ],
)
def test_package_key_is_derived_from_closed_declaration_prefix(
    declaration_id,
    expected,
):
    assert router_module._package_key_from_declaration(declaration_id) == expected


class RecordingEntitlementPort:
    def __init__(self, decision):
        self.decision = decision
        self.requests = []

    def evaluate(self, request):
        self.requests.append(request)
        return self.decision


@pytest.mark.parametrize(
    ("service_type", "expected_package"),
    [
        (ElectricalPackageService, "electrical"),
        (InstrumentationPackageService, "instrumentation"),
        (ControlAutomationPackageService, "control_automation"),
    ],
)
def test_execute_gate_builds_trusted_service_request(
    service_type,
    expected_package,
):
    port = RecordingEntitlementPort(EntitlementDecision.PERMITTED)
    service = service_type(object(), entitlement_port=port)

    service._require_execute_entitlement(organization_id=ORG)

    assert len(port.requests) == 1
    request = port.requests[0]
    assert request.trusted_organization_id == ORG
    assert request.trusted_deployment_id == settings.SATCO_DEPLOYMENT_ID
    assert request.package_key == expected_package
    assert request.entitlement_key == expected_package
    assert request.operation is EntitlementOperation.EXECUTE


def test_execute_gate_denial_is_protected_not_found():
    port = RecordingEntitlementPort(EntitlementDecision.DENIED)
    service = ElectricalPackageService(object(), entitlement_port=port)

    with pytest.raises(PackageProtectedNotFound):
        service._require_execute_entitlement(organization_id=ORG)


def test_execute_gate_unavailable_is_unavailable():
    port = RecordingEntitlementPort(EntitlementDecision.UNAVAILABLE)
    service = ElectricalPackageService(object(), entitlement_port=port)

    with pytest.raises(PackageUnavailable):
        service._require_execute_entitlement(organization_id=ORG)


def test_execute_gate_permitted_allows():
    port = RecordingEntitlementPort(EntitlementDecision.PERMITTED)
    service = ElectricalPackageService(object(), entitlement_port=port)

    service._require_execute_entitlement(organization_id=ORG)

    assert len(port.requests) == 1


def test_explicit_noncommercial_not_required_remains_compatible():
    port = RecordingEntitlementPort(EntitlementDecision.NOT_REQUIRED)
    service = ElectricalPackageService(object(), entitlement_port=port)

    service._require_execute_entitlement(organization_id=ORG)

    assert len(port.requests) == 1


def test_configure_gate_builds_trusted_service_request():
    from app.services.discipline_package_configuration_service import (
        DisciplinePackageConfigurationService,
    )

    port = RecordingEntitlementPort(EntitlementDecision.PERMITTED)
    service = DisciplinePackageConfigurationService(
        object(),
        entitlement_port=port,
    )

    service._require_configure_entitlement(
        organization_id=ORG,
        package_keys={"electrical"},
        expanding=True,
    )

    assert len(port.requests) == 1
    request = port.requests[0]
    assert request.trusted_organization_id == ORG
    assert request.trusted_deployment_id == settings.SATCO_DEPLOYMENT_ID
    assert request.package_key == "electrical"
    assert request.entitlement_key == "electrical"
    assert request.operation is EntitlementOperation.CONFIGURE


def test_configure_gate_denial_is_protected_not_found():
    from app.services.discipline_package_configuration_service import (
        DisciplinePackageConfigurationService,
    )

    port = RecordingEntitlementPort(EntitlementDecision.DENIED)
    service = DisciplinePackageConfigurationService(
        object(),
        entitlement_port=port,
    )

    with pytest.raises(PackageProtectedNotFound):
        service._require_configure_entitlement(
            organization_id=ORG,
                package_keys={"electrical"},
            expanding=True,
        )


def test_configure_gate_unavailable_is_package_unavailable():
    from app.services.discipline_package_configuration_service import (
        DisciplinePackageConfigurationService,
    )

    port = RecordingEntitlementPort(EntitlementDecision.UNAVAILABLE)
    service = DisciplinePackageConfigurationService(
        object(),
        entitlement_port=port,
    )

    with pytest.raises(PackageUnavailable):
        service._require_configure_entitlement(
            organization_id=ORG,
                package_keys={"electrical"},
            expanding=True,
        )


def test_configure_gate_explicit_noncommercial_not_required_remains_compatible():
    from app.services.discipline_package_configuration_service import (
        DisciplinePackageConfigurationService,
    )

    port = RecordingEntitlementPort(EntitlementDecision.NOT_REQUIRED)
    service = DisciplinePackageConfigurationService(
        object(),
        entitlement_port=port,
    )

    service._require_configure_entitlement(
        organization_id=ORG,
        package_keys={"electrical"},
        expanding=True,
    )

    assert len(port.requests) == 1


def test_organization_configure_denied_maps_to_protected_not_found(
    client, db_session, admin_headers,
):
    from uuid import uuid4

    from sqlalchemy.orm import sessionmaker

    from app.main import app
    from app.dependencies.discipline_package import (
        get_discipline_package_configuration_service,
    )
    from app.enums.discipline_package import EntitlementDecision
    from app.services.discipline_package_configuration_service import (
        DisciplinePackageConfigurationService,
    )
    from test_discipline_package_service import _seed_configurable_registry

    class DeniedPort:
        def evaluate(self, request):
            return EntitlementDecision.DENIED

    _seed_configurable_registry(
        db_session,
        ("electrical",),
        profile_packages=("electrical",),
        release_id=f"p059-denied-{uuid4().hex[:16]}",
        profile_id="p059-denied-profile",
    )

    factory = sessionmaker(
        bind=db_session.connection(),
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    app.dependency_overrides[
        get_discipline_package_configuration_service
    ] = lambda: DisciplinePackageConfigurationService(
        factory,
        entitlement_port=DeniedPort(),
    )

    try:
        response = client.put(
            "/organizations/current/discipline-package-configuration",
            headers=admin_headers,
            json={
                "expected_configuration_version": 0,
                "enabled_selections": [
                    {
                        "package_key": "electrical",
                        "package_version": "1.0.0",
                    }
                ],
                "rationale": "PATCH-059 denied mapping proof",
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "PROTECTED_NOT_FOUND"
    finally:
        app.dependency_overrides.pop(
            get_discipline_package_configuration_service,
            None,
        )


def test_organization_configure_unavailable_maps_to_package_unavailable(
    client, db_session, admin_headers,
):
    from uuid import uuid4

    from sqlalchemy.orm import sessionmaker

    from app.main import app
    from app.dependencies.discipline_package import (
        get_discipline_package_configuration_service,
    )
    from app.enums.discipline_package import EntitlementDecision
    from app.services.discipline_package_configuration_service import (
        DisciplinePackageConfigurationService,
    )
    from test_discipline_package_service import _seed_configurable_registry

    class UnavailablePort:
        def evaluate(self, request):
            return EntitlementDecision.UNAVAILABLE

    _seed_configurable_registry(
        db_session,
        ("electrical",),
        profile_packages=("electrical",),
        release_id=f"p059-unavailable-{uuid4().hex[:16]}",
        profile_id="p059-unavailable-profile",
    )

    factory = sessionmaker(
        bind=db_session.connection(),
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    app.dependency_overrides[
        get_discipline_package_configuration_service
    ] = lambda: DisciplinePackageConfigurationService(
        factory,
        entitlement_port=UnavailablePort(),
    )

    try:
        response = client.put(
            "/organizations/current/discipline-package-configuration",
            headers=admin_headers,
            json={
                "expected_configuration_version": 0,
                "enabled_selections": [
                    {
                        "package_key": "electrical",
                        "package_version": "1.0.0",
                    }
                ],
                "rationale": "PATCH-059 unavailable mapping proof",
            },
        )

        assert response.status_code == 503
        assert response.json()["detail"] == "PACKAGE_UNAVAILABLE"
    finally:
        app.dependency_overrides.pop(
            get_discipline_package_configuration_service,
            None,
        )


def test_organization_configure_canonical_admin_authority_precedes_entitlement(
    client, db_session, engineer_headers,
):
    from uuid import uuid4

    from sqlalchemy.orm import sessionmaker

    from app.main import app
    from app.dependencies.discipline_package import (
        get_discipline_package_configuration_service,
    )
    from app.enums.discipline_package import EntitlementDecision
    from app.services.discipline_package_configuration_service import (
        DisciplinePackageConfigurationService,
    )
    from test_discipline_package_service import _seed_configurable_registry

    class RecordingPort:
        def __init__(self):
            self.calls = 0

        def evaluate(self, request):
            self.calls += 1
            return EntitlementDecision.PERMITTED

    port = RecordingPort()

    _seed_configurable_registry(
        db_session,
        ("electrical",),
        profile_packages=("electrical",),
        release_id=f"p059-auth-first-{uuid4().hex[:16]}",
        profile_id="p059-auth-first-profile",
    )

    factory = sessionmaker(
        bind=db_session.connection(),
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    app.dependency_overrides[
        get_discipline_package_configuration_service
    ] = lambda: DisciplinePackageConfigurationService(
        factory,
        entitlement_port=port,
    )

    try:
        response = client.put(
            "/organizations/current/discipline-package-configuration",
            headers=engineer_headers,
            json={
                "expected_configuration_version": 0,
                "enabled_selections": [
                    {
                        "package_key": "electrical",
                        "package_version": "1.0.0",
                    }
                ],
                "rationale": "PATCH-059 authority ordering proof",
            },
        )

        assert response.status_code == 403
        assert port.calls == 0
    finally:
        app.dependency_overrides.pop(
            get_discipline_package_configuration_service,
            None,
        )
