"""Batch-4 contract guard and real route-path behavior evidence."""

from uuid import uuid4

from sqlalchemy.orm import sessionmaker

from app.api.v1.routers.discipline_packages import (
    router,
)
from app.dependencies.discipline_package import get_discipline_package_configuration_service
from app.dependencies.auth import get_current_user_organization_context
from app.main import app
from app.models.customer import Customer
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.organization import Organization, UserOrganizationMembership
from app.models.project import Project
from app.services.discipline_package_configuration_service import DisciplinePackageConfigurationService



def test_exact_discipline_package_route_manifest_is_registered():
    paths = app.openapi()["paths"]
    expected = {
        "/discipline-packages/supported": {"get"},
        "/organizations/current/discipline-package-configuration": {"get", "put"},
        "/organizations/current/discipline-package-configuration/audit": {"get"},
        "/projects/{project_id}/discipline-package-configuration": {"get", "put", "delete"},
        "/projects/{project_id}/discipline-package-configuration/preflight": {"post"},
        "/projects/{project_id}/effective-discipline-packages": {"get"},
        "/workspaces/{workspace_id}/package-applicability": {"get"},
    }
    assert {path: {method for method in value if method in {"get", "put", "post", "delete"}}
            for path, value in paths.items() if "discipline-package" in path or "discipline-packages" in path or "package-applicability" in path} == expected


def test_public_package_inputs_cannot_supply_identity_or_provenance():
    schemas = app.openapi()["components"]["schemas"]
    assert schemas["PackageSelectionInput"]["additionalProperties"] is False
    assert "descriptor_digest" not in schemas["PackageSelectionInput"]["properties"]
    assert "organization_id" not in schemas["OrganizationConfigurationReplaceInput"]["properties"]


def test_ten_route_surface_uses_real_authorized_paths_and_bound_cursors(
    client, db_session, admin_user, admin_headers,
):
    """One compact matrix vector proves each accepted route's normal behavior.

    The Registry fixture is a real immutable PostgreSQL projection; guarded
    writes receive a savepoint-bound fresh UoW so this request test does not
    bypass the production service/transaction path.
    """
    from test_discipline_package_service import _seed_configurable_registry

    customer = Customer(name=f"Package API customer {uuid4().hex}")
    db_session.add(customer); db_session.flush()
    project = Project(
        project_code=f"SAT-PRJ-2099-{customer.id + 1000:04d}", name="Package API project",
        customer_id=customer.id, owner_id=admin_user.id,
    )
    db_session.add(project); db_session.flush()
    _seed_configurable_registry(db_session, ("electrical", "instrumentation"), profile_packages=("electrical",), release_id=f"api-{uuid4().hex[:20]}", profile_id="api-profile")
    db_session.add(EngineeringWorkspace(
        project_id=project.id, discipline="mechanical", status="draft", owner_id=admin_user.id,
        created_by_id=admin_user.id, version=1, canonical_discipline_id="mechanical",
        package_binding_state="FUTURE_UNAVAILABLE_UNBOUND",
    ))
    db_session.flush()
    app.dependency_overrides[get_discipline_package_configuration_service] = lambda: DisciplinePackageConfigurationService(
        sessionmaker(bind=db_session.connection(), autoflush=False, expire_on_commit=False, join_transaction_mode="create_savepoint")
    )
    try:
        supported = client.get("/discipline-packages/supported?limit=1", headers=admin_headers)
        assert supported.status_code == 200 and len(supported.json()["items"]) == 1
        assert supported.json()["next_cursor"]
        assert client.get(f"/discipline-packages/supported?limit=1&cursor={supported.json()['next_cursor']}", headers=admin_headers).status_code == 200

        org_get = client.get("/organizations/current/discipline-package-configuration", headers=admin_headers)
        assert org_get.status_code == 200 and org_get.json()["configuration_version"] == 0
        org_put = client.put("/organizations/current/discipline-package-configuration", headers=admin_headers, json={
            "expected_configuration_version": 0, "enabled_selections": [{"package_key": "electrical", "package_version": "1.0.0"}], "rationale": "enable exact package",
        })
        assert org_put.status_code == 200
        audit = client.get("/organizations/current/discipline-package-configuration/audit?limit=1", headers=admin_headers)
        assert audit.status_code == 200 and audit.json()["items"]

        assert client.get(f"/projects/{project.id}/discipline-package-configuration", headers=admin_headers).json()["state"] == "NOT_CONFIGURED"
        preflight = client.post(f"/projects/{project.id}/discipline-package-configuration/preflight", headers=admin_headers, json={
            "profile_id": "api-profile", "selections": [{"package_key": "electrical", "package_version": "1.0.0"}],
        })
        assert preflight.status_code == 200 and preflight.json()["decision"] == "COMPATIBLE"
        project_put = client.put(f"/projects/{project.id}/discipline-package-configuration", headers=admin_headers, json={
            "expected_configuration_version": 0, "profile_id": "api-profile", "selections": [{"package_key": "electrical", "package_version": "1.0.0"}], "rationale": "configure exact package",
        })
        assert project_put.status_code == 200 and project_put.json()["state"] == "CONFIGURED"
        pinned_configuration = project_put.json()
        paged_audit = client.get("/organizations/current/discipline-package-configuration/audit?limit=1", headers=admin_headers)
        assert paged_audit.status_code == 200 and paged_audit.json()["next_cursor"]
        assert client.get(f"/organizations/current/discipline-package-configuration/audit?limit=1&cursor={paged_audit.json()['next_cursor']}", headers=admin_headers).status_code == 200
        assert client.get(f"/organizations/current/discipline-package-configuration/audit?limit=2&cursor={paged_audit.json()['next_cursor']}", headers=admin_headers).status_code == 422
        from app.enums.discipline_package import DisciplinePackageStanding

        _seed_configurable_registry(
            db_session,
            ("electrical", "instrumentation"),
            profile_packages=("electrical",),
            release_id=f"api-historical-{uuid4().hex[:16]}",
            profile_id="api-profile",
            standing=DisciplinePackageStanding.HISTORICAL_READ_ONLY,
        )
        effective = client.get(f"/projects/{project.id}/effective-discipline-packages", headers=admin_headers)
        assert effective.status_code == 200 and {item["discipline_id"] for item in effective.json()["items"]} >= {"electrical", "control_automation", "mechanical", "civil", "process", "instrumentation"}
        electrical = next(item for item in effective.json()["items"] if item["discipline_id"] == "electrical")
        assert electrical["availability"] == "HISTORICAL_ONLY"
        assert electrical["allowed_actions"] == []
        preserved = client.get(f"/projects/{project.id}/discipline-package-configuration", headers=admin_headers).json()
        assert preserved["configuration_revision"] == pinned_configuration["configuration_revision"]
        assert preserved["selections"] == pinned_configuration["selections"]
        assert client.get("/discipline-packages/supported", headers=admin_headers).json()["items"] == []
        workspace = db_session.query(EngineeringWorkspace).filter_by(project_id=project.id, discipline="mechanical").one()
        assert client.get(f"/workspaces/{workspace.id}/package-applicability", headers=admin_headers).status_code == 200
        assert client.request("DELETE", f"/projects/{project.id}/discipline-package-configuration", headers=admin_headers, json={"expected_configuration_version": 1, "rationale": "remove unbound configuration"}).json()["state"] == "NOT_CONFIGURED"
    finally:
        app.dependency_overrides.pop(get_discipline_package_configuration_service, None)


def test_package_routes_reject_injected_provenance_and_malformed_cursor(client, admin_headers):
    response = client.get("/discipline-packages/supported?cursor=not-a-cursor", headers=admin_headers)
    assert response.status_code in {422, 503}
    response = client.put("/organizations/current/discipline-package-configuration", headers=admin_headers, json={
        "expected_configuration_version": 0, "enabled_selections": [], "rationale": "x", "organization_id": "injected",
    })
    assert response.status_code == 422


def test_package_route_security_is_protected_before_disclosure(
    client, db_session, admin_user, engineer_user, admin_headers, engineer_headers,
):
    # The shared client fixture pins an Organization for legacy tests.  This
    # vector deliberately restores production context resolution to exercise
    # disabled membership and Organization authority.
    app.dependency_overrides.pop(get_current_user_organization_context, None)
    foreign_organization = Organization(id=uuid4(), is_active=True)
    foreign_customer = Customer(name=f"Foreign package customer {uuid4().hex}", organization_id=foreign_organization.id)
    db_session.add_all((foreign_organization, foreign_customer)); db_session.flush()
    foreign_project = Project(
        organization_id=foreign_organization.id, project_code=f"SAT-PRJ-2098-{foreign_customer.id + 1000:04d}",
        name="Foreign package project", customer_id=foreign_customer.id, owner_id=admin_user.id,
    )
    db_session.add(foreign_project); db_session.flush()
    # A non-owner engineer gets no same-tenant Project disclosure, and a
    # foreign Project remains indistinguishable from absent.
    assert client.get(f"/projects/{foreign_project.id}/discipline-package-configuration", headers=engineer_headers).status_code == 404
    assert client.get(f"/projects/{foreign_project.id}/discipline-package-configuration", headers=admin_headers).status_code == 404
    assert client.get("/organizations/current/discipline-package-configuration", headers=engineer_headers).status_code == 403

    membership = db_session.query(UserOrganizationMembership).filter_by(user_id=engineer_user.id).one()
    assert membership is not None
    membership.is_selected = False; membership.is_enabled = False; db_session.flush()
    assert client.get("/discipline-packages/supported", headers=engineer_headers).status_code == 403
    engineer_user.is_active = False; db_session.flush()
    assert client.get("/discipline-packages/supported", headers=engineer_headers).status_code == 403
    engineer_user.is_active = True; membership.is_selected = membership.is_enabled = True
    organization = db_session.get(Organization, membership.organization_id)
    assert organization is not None
    organization.is_active = False; db_session.flush()
    assert client.get("/discipline-packages/supported", headers=engineer_headers).status_code == 403
