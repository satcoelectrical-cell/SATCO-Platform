"""Real-PostgreSQL Batch-3 guarded configuration and binding seams."""

from threading import Event, Thread
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, delete, event, func, select, text
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.orm import sessionmaker

from app.models.customer import Customer
from app.models.discipline_package import (CompatibilityMember, CompatibilityProfile, OrganizationPackageConfigurationHead, OrganizationPackageSelection, PackageConfigurationAuditEvent, PackageDescriptor, ProjectPackageConfigurationHead, RegistryMembership, RegistryProfileMembership, RegistryRelease)
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.organization import Organization, UserOrganizationMembership
from app.models.project import Project
from app.models.user import User
from app.adapters.discipline_package_registry import StaticDisciplinePackageAdapter
from app.discipline_packages.canonical import combination_digest
from app.discipline_packages.contracts import (
    AllowedCombinationV1,
    CompatibilityProfileV1,
    DescriptorRegistrationV1,
    DisciplinePackageDescriptorV1,
    ExactPackageSelectionV1,
    RegistryReleaseManifestV1,
)
from app.discipline_packages.identity import DescriptorDigest, PackageKey, PackageVersion
from app.discipline_packages.registry import assemble_registry
from app.enums.discipline_package import DisciplinePackageStanding
from app.services.discipline_package_configuration_service import (DisciplinePackageConfigurationService, ExactPackageSelection, GuardedRequestIdentity, OrganizationConfigurationRequest, ProjectConfigurationRequest)
from app.services.discipline_package_service import (
    PackageWorkspaceForbidden,
    evaluate_persisted_exact_compatibility,
)
from app.services.engineering_workspace_service import EngineeringWorkspaceService
from app.schemas.engineering_workspace import EngineeringWorkspaceCreate


def _factory(db_session):
    return sessionmaker(bind=db_session.connection(), autoflush=False, expire_on_commit=False, join_transaction_mode="create_savepoint")


def _seed_configurable_registry(
    db_session,
    packages: tuple[str, ...] = ("electrical",),
    profile_packages: tuple[str, ...] | None = None,
    *,
    release_id: str = "batch3-test-release",
    profile_id: str = "batch3-profile",
    replace_current: bool = True,
    standing: DisciplinePackageStanding = DisciplinePackageStanding.EXECUTABLE_SUPPORTED,
):
    if replace_current:
        for release in db_session.scalars(select(RegistryRelease).where(RegistryRelease.is_current.is_(True))):
            release.is_current = False
    descriptors = tuple(DisciplinePackageDescriptorV1(
        package_key=key, package_version="1.0.0",
        primary_discipline_id=(
            "control_automation" if key == "control"
            else "electrical" if key.startswith("maj04_")
            else key
        ),
        core_contract_versions=(1,), display_name=f"Test {key.title()}",
        entitlement_key=f"test.{key}", adapter_id=f"test.{key}",
    ) for key in packages)
    adapters = tuple(StaticDisciplinePackageAdapter(
        adapter_id=item.adapter_id, package_key=PackageKey(item.package_key),
        package_version=PackageVersion("1.0.0"), capability_ids=frozenset(),
    ) for item in descriptors)
    bootstrap = assemble_registry(
        RegistryReleaseManifestV1(
            release_id="batch3-test-release-bootstrap", core_contract_version=1,
            descriptors=tuple(DescriptorRegistrationV1(descriptor=item, adapter_id=item.adapter_id, standing=standing) for item in descriptors),
        ), adapters=adapters
    )
    digests = {key: str(bootstrap.descriptor_digests[(key, "1.0.0")]) for key in packages}
    profile_packages = packages if profile_packages is None else profile_packages
    profile = CompatibilityProfileV1(
        profile_id=profile_id, profile_version="1.0.0",
        core_contract_version=1,
        combinations=(AllowedCombinationV1(members=tuple(ExactPackageSelectionV1(
            package_key=key, package_version="1.0.0",
            descriptor_digest=DescriptorDigest(digests[key]),
        ) for key in profile_packages)),),
    )
    manifest = RegistryReleaseManifestV1(
        release_id=release_id, core_contract_version=1,
        descriptors=tuple(DescriptorRegistrationV1(descriptor=item, adapter_id=item.adapter_id, standing=standing) for item in descriptors),
        profiles=(profile,),
    )
    registry = assemble_registry(manifest, adapters=adapters)
    registry_digest = str(registry.digest)
    profile_digest = str(registry.profile_digests[(profile_id, "1.0.0")])
    db_session.add(RegistryRelease(registry_digest=registry_digest, release_id=release_id, core_contract_version=1, is_current=True, manifest_json=manifest.model_dump(mode="json")))
    for item in descriptors:
        if db_session.get(PackageDescriptor, (item.package_key, "1.0.0")) is None:
            db_session.add(PackageDescriptor(package_key=item.package_key, package_version="1.0.0", descriptor_digest=digests[item.package_key], primary_discipline_id=item.primary_discipline_id, adapter_id=item.adapter_id, descriptor_json=item.model_dump(mode="json")))
    profile_is_new = db_session.get(CompatibilityProfile, (profile_id, profile_digest)) is None
    if profile_is_new:
        db_session.add(CompatibilityProfile(profile_id=profile_id, profile_digest=profile_digest, profile_json=profile.model_dump(mode="json")))
    db_session.flush()
    membership_rows = [
        *(RegistryMembership(registry_digest=registry_digest, package_key=item.package_key, package_version="1.0.0", standing=standing.value) for item in descriptors),
        RegistryProfileMembership(registry_digest=registry_digest, profile_id=profile_id, profile_digest=profile_digest),
    ]
    if profile_is_new:
        membership_rows.extend(
            CompatibilityMember(profile_id=profile_id, profile_digest=profile_digest, combination_digest=str(combination_digest([{"package_key": key, "package_version": "1.0.0", "descriptor_digest": digests[key]} for key in packages])), package_key=item.package_key, package_version="1.0.0", descriptor_digest=digests[item.package_key])
            for item in descriptors
        )
    db_session.add_all(membership_rows)
    db_session.flush()
    return digests[packages[0]], profile_digest


_MAJ04_REVOCATION_RELEASE_PREFIX = "maj04-revocation-"
_MAJ04_REVOCATION_PROFILE_PREFIX = "maj04-revocation-"


def _clean_maj04_revocation_business_fixture(session) -> None:
    """Remove only mutable durable authority/business rows owned by this vector.

    Registry releases and profiles are intentionally immutable production data.
    Every run creates a fresh, uniquely identified trusted source instead of
    deleting or rewriting a prior one.
    """
    for user in session.scalars(select(User).where(User.username.like("maj04-revocation-%"))):
        organization_ids = list(session.scalars(select(UserOrganizationMembership.organization_id).where(
            UserOrganizationMembership.user_id == user.id
        )))
        if organization_ids:
            session.execute(delete(PackageConfigurationAuditEvent).where(
                PackageConfigurationAuditEvent.organization_id.in_(organization_ids)
            ))
            session.execute(delete(OrganizationPackageSelection).where(
                OrganizationPackageSelection.organization_id.in_(organization_ids)
            ))
            session.execute(delete(OrganizationPackageConfigurationHead).where(
                OrganizationPackageConfigurationHead.organization_id.in_(organization_ids)
            ))
        session.execute(delete(UserOrganizationMembership).where(
            UserOrganizationMembership.user_id == user.id
        ))
        session.delete(user)
        for organization_id in organization_ids:
            organization = session.get(Organization, organization_id)
            if organization is not None:
                session.delete(organization)
    session.flush()


def _retryable_database_error(sqlstate: str = "40001") -> OperationalError:
    class DatabaseFailure(Exception):
        pass

    failure = DatabaseFailure("controlled PostgreSQL retry vector")
    failure.sqlstate = sqlstate  # type: ignore[attr-defined]
    return OperationalError("controlled PostgreSQL retry vector", {}, failure)


def _seed_durable_maj04_organization(factory, label: str) -> dict[str, object]:
    """Create one committed, isolated Registry/authority fixture namespace."""
    organization_id = uuid4()
    label_slug = label.replace("-", "_")
    release_id = f"maj04-{label_slug}-{organization_id.hex}"
    profile_id = f"maj04-{label_slug}-profile-{organization_id.hex}"
    package_key = f"maj04_{label_slug}_{organization_id.hex}"
    with factory.begin() as setup:
        prior = setup.scalar(
            select(RegistryRelease).where(RegistryRelease.is_current.is_(True)).with_for_update()
        )
        prior_digest = None if prior is None else prior.registry_digest
        if prior is not None:
            prior.is_current = False
            setup.flush()
        organization = Organization(id=organization_id, is_active=True)
        user = User(
            email=f"maj04-{label}-{organization_id}@test",
            username=f"maj04-{label}-{organization_id}",
            hashed_password="x", role="admin", is_active=True, activation_pending=True,
        )
        setup.add_all((organization, user))
        setup.flush()
        setup.add(UserOrganizationMembership(
            user_id=user.id, organization_id=organization_id,
            is_enabled=True, is_selected=True,
        ))
        descriptor_digest, profile_digest = _seed_configurable_registry(
            setup, (package_key,), release_id=release_id,
            profile_id=profile_id, replace_current=False,
        )
        return {
            "organization_id": organization_id, "user_id": user.id,
            "auth_version": user.auth_version, "release_id": release_id,
            "prior_digest": prior_digest, "package_key": package_key,
            "descriptor_digest": descriptor_digest, "profile_id": profile_id,
            "profile_digest": profile_digest,
        }


def _restore_maj04_registry_pointer(factory, fixture: dict[str, object]) -> None:
    with factory.begin() as cleanup:
        scenario = cleanup.scalar(select(RegistryRelease).where(
            RegistryRelease.release_id == fixture["release_id"]
        ).with_for_update())
        assert scenario is not None
        scenario.is_current = False
        cleanup.flush()
        prior_digest = fixture["prior_digest"]
        if prior_digest is not None:
            prior = cleanup.get(RegistryRelease, prior_digest)
            assert prior is not None
            prior.is_current = True


def _clean_maj04_mutable_organization_fixture(session, fixture: dict[str, object]) -> None:
    organization_id = fixture["organization_id"]
    user_id = fixture["user_id"]
    session.execute(delete(OrganizationPackageSelection).where(
        OrganizationPackageSelection.organization_id == organization_id
    ))
    session.execute(delete(OrganizationPackageConfigurationHead).where(
        OrganizationPackageConfigurationHead.organization_id == organization_id
    ))
    # Package Audit is immutable by design.  If this vector reached a success
    # Audit, retain its explicitly namespaced authority fixture rather than
    # weakening history/FK guards to remove it.
    has_immutable_audit = session.scalar(select(func.count()).select_from(
        PackageConfigurationAuditEvent
    ).where(PackageConfigurationAuditEvent.organization_id == organization_id)) > 0
    if not has_immutable_audit:
        session.execute(delete(UserOrganizationMembership).where(
            UserOrganizationMembership.user_id == user_id,
            UserOrganizationMembership.organization_id == organization_id,
        ))
        user = session.get(User, user_id)
        if user is not None:
            session.delete(user)
        organization = session.get(Organization, organization_id)
        if organization is not None:
            session.delete(organization)
    session.flush()


def _project(db_session, owner):
    customer = Customer(name="Batch-3 configuration customer")
    db_session.add(customer); db_session.flush()
    project = Project(project_code=f"SAT-PRJ-2099-{customer.id + 1000:04d}", name="Batch-3 configuration project", customer_id=customer.id, owner_id=owner.id)
    db_session.add(project); db_session.flush()
    return project


def test_persisted_source_reuses_batch1_evaluator(db_session):
    descriptor_digest, profile_digest = _seed_configurable_registry(db_session)
    release = db_session.scalar(select(RegistryRelease).where(RegistryRelease.is_current.is_(True)))
    assert release is not None
    assert evaluate_persisted_exact_compatibility(
        db_session,
        release,
        profile_id="batch3-profile",
        profile_digest=profile_digest,
        selections=(("electrical", "1.0.0", descriptor_digest),),
        enabled_package_keys=frozenset({"electrical"}),
    )


def test_guarded_configuration_workspace_binding_and_atomic_rebind(db_session, engineer_user, admin_user):
    descriptor_digest, profile_digest = _seed_configurable_registry(db_session)
    project = _project(db_session, engineer_user)
    factory = _factory(db_session)
    identity = GuardedRequestIdentity(engineer_user.id, project.organization_id, engineer_user.auth_version, uuid4())
    admin_identity = GuardedRequestIdentity(admin_user.id, project.organization_id, admin_user.auth_version, uuid4())
    selection = ExactPackageSelection("electrical", "1.0.0", descriptor_digest)
    configuration = DisciplinePackageConfigurationService(factory)

    assert configuration.replace_organization_configuration(admin_identity, OrganizationConfigurationRequest(0, (selection,), "initial package configuration")) == 1
    assert configuration.replace_project_configuration(identity, project.id, ProjectConfigurationRequest(0, "batch3-profile", profile_digest, (selection,), "initial Project pin")) == 1

    created = EngineeringWorkspaceService(db_session, project.organization_id, package_uow_factory=factory).create(
        project.id, EngineeringWorkspaceCreate(discipline="electrical"), engineer_user
    )
    workspace = db_session.get(EngineeringWorkspace, created["id"])
    assert workspace.package_binding_state == "OPERATIONAL_PACKAGE_BOUND"
    assert workspace.canonical_discipline_id == "electrical"
    assert workspace.bound_package_key == "electrical"
    assert workspace.bound_project_configuration_revision == 1

    assert configuration.replace_project_configuration(identity, project.id, ProjectConfigurationRequest(1, "batch3-profile", profile_digest, (selection,), "audited forward rebind")) == 2
    db_session.expire_all()
    workspace = db_session.get(EngineeringWorkspace, created["id"])
    assert workspace.bound_project_configuration_revision == 2
    assert db_session.get(ProjectPackageConfigurationHead, project.id).current_revision == 2
    assert db_session.scalar(select(OrganizationPackageConfigurationHead.configuration_version).where(OrganizationPackageConfigurationHead.organization_id == project.organization_id)) == 1
    assert db_session.scalar(select(PackageConfigurationAuditEvent).where(PackageConfigurationAuditEvent.workspace_id == workspace.id, PackageConfigurationAuditEvent.action == "rebind")) is not None


def test_guarded_workspace_future_is_unbound_and_operational_requires_exact_project_pin(db_session, engineer_user, admin_user):
    descriptor_digest, _ = _seed_configurable_registry(db_session)
    project = _project(db_session, engineer_user)
    factory = _factory(db_session)
    configuration = DisciplinePackageConfigurationService(factory)
    configuration.replace_organization_configuration(
        GuardedRequestIdentity(admin_user.id, project.organization_id, admin_user.auth_version),
        OrganizationConfigurationRequest(0, (ExactPackageSelection("electrical", "1.0.0", descriptor_digest),), "future Workspace test"),
    )
    workspace_service = EngineeringWorkspaceService(db_session, project.organization_id, package_uow_factory=factory)
    future = workspace_service.create(project.id, EngineeringWorkspaceCreate(discipline="mechanical"), engineer_user)
    future_row = db_session.get(EngineeringWorkspace, future["id"])
    assert (future_row.canonical_discipline_id, future_row.package_binding_state, future_row.bound_package_key, future_row.bound_project_configuration_revision) == ("mechanical", "FUTURE_UNAVAILABLE_UNBOUND", None, None)

    from app.exceptions.engineering_workspace import WorkspaceProjectStateConflict
    with pytest.raises(WorkspaceProjectStateConflict):
        workspace_service.create(project.id, EngineeringWorkspaceCreate(discipline="electrical"), engineer_user)


def test_historical_current_membership_preserves_pin_but_blocks_new_workspace(db_session, engineer_user, admin_user):
    descriptor_digest, profile_digest = _seed_configurable_registry(
        db_session,
        release_id="standing-r1-executable",
        profile_id="standing-profile",
    )
    executable_release = db_session.scalar(
        select(RegistryRelease).where(RegistryRelease.is_current.is_(True))
    )
    assert executable_release is not None
    project = _project(db_session, engineer_user)
    factory = _factory(db_session)
    configuration = DisciplinePackageConfigurationService(factory)
    selection = ExactPackageSelection("electrical", "1.0.0", descriptor_digest)
    configuration.replace_organization_configuration(
        GuardedRequestIdentity(admin_user.id, project.organization_id, admin_user.auth_version),
        OrganizationConfigurationRequest(0, (selection,), "enable executable release"),
    )
    configuration.replace_project_configuration(
        GuardedRequestIdentity(engineer_user.id, project.organization_id, engineer_user.auth_version),
        project.id,
        ProjectConfigurationRequest(0, "standing-profile", profile_digest, (selection,), "pin immutable descriptor"),
    )
    pinned_revision = db_session.get(ProjectPackageConfigurationHead, project.id).current_revision

    _seed_configurable_registry(
        db_session,
        release_id="standing-r2-historical",
        profile_id="standing-profile",
        standing=DisciplinePackageStanding.HISTORICAL_READ_ONLY,
    )
    historical_release = db_session.scalar(
        select(RegistryRelease).where(RegistryRelease.is_current.is_(True))
    )
    assert historical_release is not None
    assert historical_release.registry_digest != executable_release.registry_digest
    assert db_session.get(
        RegistryMembership,
        (executable_release.registry_digest, "electrical", "1.0.0"),
    ).standing == "executable_supported"
    assert db_session.get(
        RegistryMembership,
        (historical_release.registry_digest, "electrical", "1.0.0"),
    ).standing == "historical_read_only"
    assert db_session.get(PackageDescriptor, ("electrical", "1.0.0")).descriptor_digest == descriptor_digest
    assert db_session.get(ProjectPackageConfigurationHead, project.id).current_revision == pinned_revision

    from app.exceptions.engineering_workspace import WorkspaceProjectStateConflict

    # A pin remains historically readable, but its observed release is not
    # the current historical-only release; it cannot seed a new operational
    # Workspace.
    with pytest.raises(WorkspaceProjectStateConflict, match="current Registry"):
        EngineeringWorkspaceService(
            db_session,
            project.organization_id,
            package_uow_factory=factory,
        ).create(
            project.id,
            EngineeringWorkspaceCreate(discipline="electrical"),
            engineer_user,
        )


def test_project_configuration_removal_locks_real_workspace_rows_and_audits(db_session, engineer_user, admin_user):
    descriptor_digest, profile_digest = _seed_configurable_registry(db_session)
    project = _project(db_session, engineer_user)
    configuration = DisciplinePackageConfigurationService(_factory(db_session))
    selection = ExactPackageSelection("electrical", "1.0.0", descriptor_digest)
    admin = GuardedRequestIdentity(admin_user.id, project.organization_id, admin_user.auth_version)
    owner = GuardedRequestIdentity(engineer_user.id, project.organization_id, engineer_user.auth_version)
    configuration.replace_organization_configuration(admin, OrganizationConfigurationRequest(0, (selection,), "enable"))
    configuration.replace_project_configuration(owner, project.id, ProjectConfigurationRequest(0, "batch3-profile", profile_digest, (selection,), "pin"))
    configuration.remove_project_configuration(owner, project.id, expected_configuration_version=1, rationale="remove unbound")
    assert db_session.get(ProjectPackageConfigurationHead, project.id) is None
    assert db_session.scalar(select(PackageConfigurationAuditEvent).where(PackageConfigurationAuditEvent.project_id == project.id, PackageConfigurationAuditEvent.action == "remove")) is not None
    with pytest.raises(PackageWorkspaceForbidden):
        configuration.remove_project_configuration(
            GuardedRequestIdentity(engineer_user.id, uuid4(), engineer_user.auth_version), project.id,
            expected_configuration_version=1, rationale="cross tenant",
        )


def test_project_and_workspace_paths_reject_subset_wrong_profile_and_provenance(db_session, engineer_user, admin_user):
    electrical_digest, profile_digest = _seed_configurable_registry(
        db_session,
        ("electrical", "control_automation", "instrumentation"),
        ("electrical", "control_automation"),
    )
    control_digest = db_session.get(PackageDescriptor, ("control_automation", "1.0.0")).descriptor_digest
    instrumentation_digest = db_session.get(PackageDescriptor, ("instrumentation", "1.0.0")).descriptor_digest
    project = _project(db_session, engineer_user)
    configuration = DisciplinePackageConfigurationService(_factory(db_session))
    admin = GuardedRequestIdentity(admin_user.id, project.organization_id, admin_user.auth_version)
    owner = GuardedRequestIdentity(engineer_user.id, project.organization_id, engineer_user.auth_version)
    complete = (ExactPackageSelection("electrical", "1.0.0", electrical_digest), ExactPackageSelection("control_automation", "1.0.0", control_digest))
    extra = ExactPackageSelection("instrumentation", "1.0.0", instrumentation_digest)
    configuration.replace_organization_configuration(admin, OrganizationConfigurationRequest(0, (*complete, extra), "enable exact combination"))
    with pytest.raises(ValueError, match="exact Project package combination"):
        configuration.replace_project_configuration(owner, project.id, ProjectConfigurationRequest(0, "batch3-profile", profile_digest, complete[:1], "subset"))
    with pytest.raises(ValueError, match="exact Project package combination"):
        configuration.replace_project_configuration(owner, project.id, ProjectConfigurationRequest(0, "wrong-profile", profile_digest, complete, "wrong profile"))
    with pytest.raises(ValueError, match="exact Project package combination"):
        configuration.replace_project_configuration(owner, project.id, ProjectConfigurationRequest(0, "batch3-profile", profile_digest, (*complete, extra), "incompatible extra"))
    # Version substitution is rejected before any Project revision can be
    # written; it cannot be smuggled through the evaluator-facing path.
    with pytest.raises(ValueError, match="project selection is not organization enabled"):
        configuration.replace_project_configuration(owner, project.id, ProjectConfigurationRequest(0, "batch3-profile", profile_digest, (ExactPackageSelection("electrical", "9.9.9", electrical_digest),), "wrong version"))
    with pytest.raises(ValueError, match="exact executable package descriptor"):
        configuration.replace_project_configuration(owner, project.id, ProjectConfigurationRequest(0, "batch3-profile", profile_digest, (ExactPackageSelection("electrical", "1.0.0", "f" * 64),), "wrong provenance"))
    configuration.replace_project_configuration(owner, project.id, ProjectConfigurationRequest(0, "batch3-profile", profile_digest, complete, "exact"))
    created = EngineeringWorkspaceService(db_session, project.organization_id, package_uow_factory=_factory(db_session)).create(project.id, EngineeringWorkspaceCreate(discipline="control"), engineer_user)
    assert db_session.get(EngineeringWorkspace, created["id"]).bound_package_key == "control_automation"
    with pytest.raises(ValueError, match="exact Project package combination"):
        configuration.replace_project_configuration(owner, project.id, ProjectConfigurationRequest(1, "batch3-profile", profile_digest, complete[:1], "workspace cannot bypass"))
    assert db_session.get(ProjectPackageConfigurationHead, project.id).current_revision == 1


def test_independent_sessions_revocation_wins_before_guarded_authority_read():
    """A real Session B revokes before Session A's production authority lock."""
    engine = create_engine(__import__("os").environ["TEST_DATABASE_URL"], pool_pre_ping=True)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    organization_id = uuid4()
    release_id = f"{_MAJ04_REVOCATION_RELEASE_PREFIX}{organization_id.hex}"
    profile_id = f"{_MAJ04_REVOCATION_PROFILE_PREFIX}{organization_id.hex}"
    package_key = f"maj04_revocation_{organization_id.hex}"
    prior_current_digest: str | None = None
    with factory.begin() as setup:
        # This boundary is deliberately independent of db_session's outer
        # rollback transaction: Session A and Session B must see committed
        # User, membership and Registry state.
        prior_current = setup.scalar(
            select(RegistryRelease).where(RegistryRelease.is_current.is_(True)).with_for_update()
        )
        if prior_current is not None:
            # The disposable database's pre-existing fixture is retained and
            # restored; only this scenario's source becomes current.
            prior_current_digest = prior_current.registry_digest
            prior_current.is_current = False
            # The partial current-release uniqueness constraint requires this
            # pointer transition to be durable before inserting our source.
            setup.flush()
        setup.add(Organization(id=organization_id, is_active=True))
        admin = User(email=f"maj04-revocation-{organization_id}@test", username=f"maj04-revocation-{organization_id}", hashed_password="x", role="admin", is_active=True, activation_pending=True)
        setup.add(admin)
        setup.flush()
        setup.add(UserOrganizationMembership(user_id=admin.id, organization_id=organization_id, is_enabled=True, is_selected=True))
        descriptor_digest, _ = _seed_configurable_registry(
            setup,
                (package_key,),
            release_id=release_id,
            profile_id=profile_id,
            replace_current=False,
        )
        admin_id, auth_version = admin.id, admin.auth_version
    reached_authority_read, revocation_committed = Event(), Event()
    trace: dict[str, int | str] = {"setup_commit_boundary": "committed"}

    def pause_before_authority(_connection, _cursor, statement, _parameters, _context, _executemany):
        normalized = statement.lower()
        if "from users" in normalized and "for update" in normalized and not reached_authority_read.is_set():
            trace["session_a_connection"] = _connection.connection.get_backend_pid()
            trace["authority_validation_point"] = "user_for_update"
            reached_authority_read.set()
            assert revocation_committed.wait(10)

    event.listen(engine, "before_cursor_execute", pause_before_authority)
    identity = GuardedRequestIdentity(admin_id, organization_id, auth_version, uuid4())
    service = DisciplinePackageConfigurationService(factory)
    result: list[BaseException] = []
    worker: Thread | None = None
    try:
        def mutate() -> None:
            try:
                service.replace_organization_configuration(identity, OrganizationConfigurationRequest(0, (ExactPackageSelection(package_key, "1.0.0", descriptor_digest),), "guarded mutation"))
            except BaseException as exc:  # assertion captures production failure from worker
                result.append(exc)

        worker = Thread(target=mutate)
        worker.start()
        assert reached_authority_read.wait(10)
        with factory.begin() as revoker:
            trace["session_b_connection"] = revoker.scalar(text("SELECT pg_backend_pid()"))
            assert revoker.scalar(text("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_locks
                    WHERE pid = :pid AND locktype = 'advisory'
                      AND classid = 1396790339 AND objid = 51
                      AND mode = 'ShareLock' AND granted
                )
            """), {"pid": trace["session_a_connection"]})
            trace["relevant_locks"] = "Session-A ShareLock(1396790339,51); then User/membership/Organization FOR UPDATE"
            membership = revoker.get(UserOrganizationMembership, (admin_id, organization_id))
            assert membership is not None
            membership.is_selected = False
            membership.is_enabled = False
        revocation_committed.set()
        trace["revocation_commit_point"] = "before_session_a_authority_validation"
        worker.join(10)
        assert not worker.is_alive()
        assert len(result) == 1 and isinstance(result[0], PackageWorkspaceForbidden)
        with factory() as observed:
            assert observed.get(OrganizationPackageConfigurationHead, organization_id) is None
            assert observed.scalar(select(func.count()).select_from(PackageConfigurationAuditEvent).where(PackageConfigurationAuditEvent.organization_id == organization_id)) == 0
        assert trace["setup_commit_boundary"] == "committed"
        assert trace["authority_validation_point"] == "user_for_update"
        assert trace["revocation_commit_point"] == "before_session_a_authority_validation"
        assert trace["session_a_connection"] != trace["session_b_connection"]
    finally:
        revocation_committed.set()
        if worker is not None:
            worker.join(10)
        event.remove(engine, "before_cursor_execute", pause_before_authority)
        with factory.begin() as cleanup:
            _clean_maj04_revocation_business_fixture(cleanup)
            scenario_current = cleanup.scalar(
                select(RegistryRelease).where(RegistryRelease.release_id == release_id).with_for_update()
            )
            assert scenario_current is not None
            scenario_current.is_current = False
            # Do not let the ORM batch this with restoration of the prior
            # pointer; PostgreSQL must observe the false transition first.
            cleanup.flush()
            if prior_current_digest is not None:
                prior_current = cleanup.get(RegistryRelease, prior_current_digest)
                assert prior_current is not None
                prior_current.is_current = True
        engine.dispose()


def test_independent_sessions_mutation_wins_before_revocation_commit():
    """Session A linearizes authority first; B's revocation commits after A."""
    engine = create_engine(__import__("os").environ["TEST_DATABASE_URL"], pool_pre_ping=True)
    base_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    fixture = _seed_durable_maj04_organization(base_factory, "mutation")
    identity = GuardedRequestIdentity(
        fixture["user_id"], fixture["organization_id"], fixture["auth_version"], uuid4()
    )
    reached_linearization, permit_mutation, revocation_attempted, revocation_committed = (
        Event(), Event(), Event(), Event()
    )
    trace: dict[str, int | str] = {}

    def pause_after_membership_lock(connection, _cursor, statement, _parameters, _context, _executemany):
        normalized = statement.lower()
        if "from user_organization_memberships" in normalized and "for update" in normalized and not reached_linearization.is_set():
            trace["session_a_connection"] = connection.connection.get_backend_pid()
            trace["authority_validation_point"] = "membership_for_update_acquired"
            reached_linearization.set()
            assert permit_mutation.wait(10)

    event.listen(engine, "after_cursor_execute", pause_after_membership_lock)
    service = DisciplinePackageConfigurationService(base_factory)
    mutation_result: list[int] = []
    revocation_error: list[BaseException] = []
    try:
        def mutate() -> None:
            mutation_result.append(service.replace_organization_configuration(
                identity,
                OrganizationConfigurationRequest(0, (
                    ExactPackageSelection(fixture["package_key"], "1.0.0", fixture["descriptor_digest"]),
                ), "mutation linearizes first"),
            ))

        def revoke() -> None:
            try:
                with base_factory.begin() as session:
                    trace["session_b_connection"] = session.scalar(text("SELECT pg_backend_pid()"))
                    membership = session.get(UserOrganizationMembership, (fixture["user_id"], fixture["organization_id"]))
                    assert membership is not None
                    membership.is_enabled = membership.is_selected = False
                    revocation_attempted.set()
                    session.flush()  # waits for A's held membership lock
                revocation_committed.set()
            except BaseException as exc:
                revocation_error.append(exc)

        mutation = Thread(target=mutate)
        mutation.start()
        assert reached_linearization.wait(10)
        revoker = Thread(target=revoke)
        revoker.start()
        assert revocation_attempted.wait(10)
        permit_mutation.set()
        mutation.join(10); revoker.join(10)
        assert not mutation.is_alive() and not revoker.is_alive()
        assert not revocation_error
        assert mutation_result == [1]
        assert revocation_committed.is_set()
        with base_factory() as observed:
            assert observed.get(OrganizationPackageConfigurationHead, fixture["organization_id"]).configuration_version == 1
            assert observed.scalar(select(func.count()).select_from(PackageConfigurationAuditEvent).where(
                PackageConfigurationAuditEvent.organization_id == fixture["organization_id"]
            )) == 1
            membership = observed.get(UserOrganizationMembership, (fixture["user_id"], fixture["organization_id"]))
            assert membership is not None and not membership.is_enabled and not membership.is_selected
        assert trace["session_a_connection"] != trace["session_b_connection"]
    finally:
        permit_mutation.set()
        event.remove(engine, "after_cursor_execute", pause_after_membership_lock)
        with base_factory.begin() as cleanup:
            _clean_maj04_mutable_organization_fixture(cleanup, fixture)
        _restore_maj04_registry_pointer(base_factory, fixture)
        engine.dispose()


def test_retry_after_revocation_uses_fresh_session_and_fails_closed():
    """A retryable first attempt cannot reuse authority after B revokes it."""
    engine = create_engine(__import__("os").environ["TEST_DATABASE_URL"], pool_pre_ping=True)
    base_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    fixture = _seed_durable_maj04_organization(base_factory, "retry-revocation")
    session_ids: list[int] = []
    session_references: list[object] = []

    def fresh_factory():
        session = base_factory()
        # Retain both closed objects for the duration of this concurrency
        # vector.  Otherwise CPython may recycle the first object's id before
        # the assertion observes the second fresh Session.
        session_references.append(session)
        session_ids.append(id(session))
        return session

    first_failure, revocation_committed = Event(), Event()
    user_reads: list[int] = []
    injected = False

    def schedule_retry(connection, _cursor, statement, _parameters, _context, _executemany):
        nonlocal injected
        normalized = statement.lower()
        if "from users" in normalized and "for update" in normalized:
            user_reads.append(connection.connection.get_backend_pid())
            if len(user_reads) == 2:
                assert revocation_committed.wait(10)
        if not injected and "from discipline_package_registry_releases" in normalized:
            injected = True
            first_failure.set()
            raise _retryable_database_error()

    event.listen(engine, "before_cursor_execute", schedule_retry)
    identity = GuardedRequestIdentity(fixture["user_id"], fixture["organization_id"], fixture["auth_version"], uuid4())
    service = DisciplinePackageConfigurationService(fresh_factory)
    try:
        def revoke() -> None:
            assert first_failure.wait(10)
            with base_factory.begin() as session:
                membership = session.get(UserOrganizationMembership, (fixture["user_id"], fixture["organization_id"]))
                assert membership is not None
                membership.is_enabled = membership.is_selected = False
            revocation_committed.set()

        revoker = Thread(target=revoke)
        revoker.start()
        with pytest.raises(PackageWorkspaceForbidden):
            service.replace_organization_configuration(identity, OrganizationConfigurationRequest(0, (
                ExactPackageSelection(fixture["package_key"], "1.0.0", fixture["descriptor_digest"]),
            ), "retry must reload revoked authority"))
        revoker.join(10)
        assert not revoker.is_alive() and revocation_committed.is_set()
        assert injected and len(session_ids) == 2 and session_ids[0] != session_ids[1]
        assert len(user_reads) == 2
        with base_factory() as observed:
            assert observed.get(OrganizationPackageConfigurationHead, fixture["organization_id"]) is None
            assert observed.scalar(select(func.count()).select_from(PackageConfigurationAuditEvent).where(
                PackageConfigurationAuditEvent.organization_id == fixture["organization_id"]
            )) == 0
    finally:
        event.remove(engine, "before_cursor_execute", schedule_retry)
        with base_factory.begin() as cleanup:
            _clean_maj04_mutable_organization_fixture(cleanup, fixture)
        _restore_maj04_registry_pointer(base_factory, fixture)
        engine.dispose()


@pytest.mark.parametrize(("sqlstate", "expected_attempts"), (("40001", 2), ("23505", 1)))
def test_configuration_retry_is_bounded_and_classifies_database_errors(sqlstate: str, expected_attempts: int):
    """Only PostgreSQL lock/deadlock/serialization states receive one retry."""
    engine = create_engine(__import__("os").environ["TEST_DATABASE_URL"], pool_pre_ping=True)
    base_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    fixture = _seed_durable_maj04_organization(base_factory, f"retry-{sqlstate}")
    attempts = 0

    def inject_on_guard(_connection, _cursor, statement, _parameters, _context, _executemany):
        nonlocal attempts
        if "set local lock_timeout" in statement.lower():
            attempts += 1
            raise _retryable_database_error(sqlstate)

    event.listen(engine, "before_cursor_execute", inject_on_guard)
    try:
        service = DisciplinePackageConfigurationService(base_factory)
        with pytest.raises(ValueError, match="concurrent package configuration update"):
            service.replace_organization_configuration(
                GuardedRequestIdentity(fixture["user_id"], fixture["organization_id"], fixture["auth_version"]),
                OrganizationConfigurationRequest(0, (ExactPackageSelection(
                    fixture["package_key"], "1.0.0", fixture["descriptor_digest"]
                ),), "controlled retry classification"),
            )
        assert attempts == expected_attempts
    finally:
        event.remove(engine, "before_cursor_execute", inject_on_guard)
        with base_factory.begin() as cleanup:
            _clean_maj04_mutable_organization_fixture(cleanup, fixture)
        _restore_maj04_registry_pointer(base_factory, fixture)
        engine.dispose()


def test_atomic_multi_workspace_rebind_failure_rolls_back_in_ascending_lock_order():
    """A forced later rebind failure leaves every bound Workspace and Audit unchanged."""
    engine = create_engine(__import__("os").environ["TEST_DATABASE_URL"], pool_pre_ping=True)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    fixture = _seed_durable_maj04_organization(factory, "rebind")
    identity = GuardedRequestIdentity(fixture["user_id"], fixture["organization_id"], fixture["auth_version"], uuid4())
    configuration = DisciplinePackageConfigurationService(factory)
    try:
        selection = ExactPackageSelection(fixture["package_key"], "1.0.0", fixture["descriptor_digest"])
        assert configuration.replace_organization_configuration(
            identity, OrganizationConfigurationRequest(0, (selection,), "enable for atomic rebind")
        ) == 1
        with factory.begin() as setup:
            customer = Customer(
                name=f"MAJ-04 atomic rebind {fixture['organization_id']}",
                organization_id=fixture["organization_id"],
            )
            setup.add(customer); setup.flush()
            project = Project(
                project_code=f"SAT-PRJ-2099-{customer.id + 1000:04d}",
                name="MAJ-04 atomic rebind project", customer_id=customer.id,
                owner_id=fixture["user_id"], organization_id=fixture["organization_id"],
            )
            setup.add(project); setup.flush()
            project_id = project.id
        assert configuration.replace_project_configuration(
            identity, project_id, ProjectConfigurationRequest(
                0, fixture["profile_id"], fixture["profile_digest"], (selection,), "initial pin"
            )
        ) == 1
        with factory.begin() as setup:
            setup.add_all(tuple(
                EngineeringWorkspace(
                    project_id=project_id, discipline=discipline, status="draft",
                    owner_id=fixture["user_id"], created_by_id=fixture["user_id"], version=1,
                    canonical_discipline_id=canonical,
                    package_binding_state="OPERATIONAL_PACKAGE_BOUND",
                    bound_package_key=fixture["package_key"], bound_project_configuration_revision=1,
                )
                for discipline, canonical in (
                    ("electrical", "electrical"), ("instrumentation", "instrumentation"),
                    ("control", "control_automation"),
                )
            ))
        with factory() as observed:
            workspace_ids = list(observed.scalars(select(EngineeringWorkspace.id).where(
                EngineeringWorkspace.project_id == project_id
            ).order_by(EngineeringWorkspace.id)))
            audit_before = observed.scalar(select(func.count()).select_from(PackageConfigurationAuditEvent).where(
                PackageConfigurationAuditEvent.project_id == project_id
            ))
        statements: list[str] = []
        original_audit = configuration._audit
        rebinds = 0

        def observe_locks(_connection, _cursor, statement, _parameters, _context, _executemany):
            normalized = " ".join(statement.lower().split())
            if "from engineering_workspaces" in normalized and "for update" in normalized:
                statements.append(normalized)

        def fail_second_rebind(session, guarded_identity, category, action, **kwargs):
            nonlocal rebinds
            if category == "WORKSPACE_BINDING" and action == "rebind":
                rebinds += 1
                if rebinds == 2:
                    raise RuntimeError("forced second rebind audit failure")
            return original_audit(session, guarded_identity, category, action, **kwargs)

        event.listen(engine, "before_cursor_execute", observe_locks)
        configuration._audit = fail_second_rebind
        try:
            with pytest.raises(RuntimeError, match="forced second rebind audit failure"):
                configuration.replace_project_configuration(
                    identity, project_id, ProjectConfigurationRequest(
                        1, fixture["profile_id"], fixture["profile_digest"], (selection,), "forced rollback"
                    )
                )
        finally:
            configuration._audit = original_audit
            event.remove(engine, "before_cursor_execute", observe_locks)
        with factory() as observed:
            head = observed.get(ProjectPackageConfigurationHead, project_id)
            assert head is not None and (head.current_revision, head.configuration_version) == (1, 1)
            assert list(observed.scalars(select(EngineeringWorkspace.bound_project_configuration_revision).where(
                EngineeringWorkspace.id.in_(workspace_ids)
            ).order_by(EngineeringWorkspace.id))) == [1, 1, 1]
            assert observed.scalar(select(func.count()).select_from(PackageConfigurationAuditEvent).where(
                PackageConfigurationAuditEvent.project_id == project_id
            )) == audit_before
        assert rebinds == 2
        assert len(statements) == 1 and "order by engineering_workspaces.id" in statements[0]
    finally:
        _restore_maj04_registry_pointer(factory, fixture)
        engine.dispose()


def test_corrected_m3_guard_commits_valid_operational_workspace_and_rejects_invalid_binding():
    """The installed M3 trigger accepts an exact pin and rejects a stale one."""
    engine = create_engine(__import__("os").environ["TEST_DATABASE_URL"], pool_pre_ping=True)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    fixture = _seed_durable_maj04_organization(factory, "m3-operational")
    identity = GuardedRequestIdentity(fixture["user_id"], fixture["organization_id"], fixture["auth_version"])
    configuration = DisciplinePackageConfigurationService(factory)
    try:
        selection = ExactPackageSelection(fixture["package_key"], "1.0.0", fixture["descriptor_digest"])
        assert configuration.replace_organization_configuration(
            identity, OrganizationConfigurationRequest(0, (selection,), "enable M3 direct-insert proof")
        ) == 1
        with factory.begin() as setup:
            customer = Customer(
                name=f"M3 operational guard {fixture['organization_id']}",
                organization_id=fixture["organization_id"],
            )
            setup.add(customer)
            setup.flush()
            project = Project(
                project_code=f"SAT-PRJ-2097-{customer.id + 1000:04d}",
                name="M3 operational guard project", customer_id=customer.id,
                owner_id=fixture["user_id"], organization_id=fixture["organization_id"],
            )
            setup.add(project)
            setup.flush()
            project_id = project.id
        assert configuration.replace_project_configuration(
            identity, project_id, ProjectConfigurationRequest(
                0, fixture["profile_id"], fixture["profile_digest"], (selection,), "M3 direct-insert pin"
            )
        ) == 1
        with factory.begin() as valid:
            valid.add(EngineeringWorkspace(
                project_id=project_id, discipline="electrical", status="draft",
                owner_id=fixture["user_id"], created_by_id=fixture["user_id"], version=1,
                canonical_discipline_id="electrical", package_binding_state="OPERATIONAL_PACKAGE_BOUND",
                bound_package_key=fixture["package_key"], bound_project_configuration_revision=1,
            ))
        with factory() as observed:
            assert observed.scalar(select(func.count()).select_from(EngineeringWorkspace).where(
                EngineeringWorkspace.project_id == project_id,
                EngineeringWorkspace.package_binding_state == "OPERATIONAL_PACKAGE_BOUND",
            )) == 1
        with pytest.raises(DBAPIError, match="future Workspace must be unbound"):
            with factory.begin() as invalid:
                invalid.add(EngineeringWorkspace(
                    project_id=project_id, discipline="instrumentation", status="draft",
                    owner_id=fixture["user_id"], created_by_id=fixture["user_id"], version=1,
                    canonical_discipline_id="instrumentation", package_binding_state="FUTURE_UNAVAILABLE_UNBOUND",
                    bound_package_key=fixture["package_key"], bound_project_configuration_revision=1,
                ))
    finally:
        _restore_maj04_registry_pointer(factory, fixture)
        engine.dispose()


def test_concurrent_cross_tenant_project_configuration_is_non_disclosing():
    """A foreign Project remains not-found even while its own tenant holds it."""
    engine = create_engine(__import__("os").environ["TEST_DATABASE_URL"], pool_pre_ping=True)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    fixture = _seed_durable_maj04_organization(factory, "cross-tenant")
    identity = GuardedRequestIdentity(fixture["user_id"], fixture["organization_id"], fixture["auth_version"], uuid4())
    configuration = DisciplinePackageConfigurationService(factory)
    trace: dict[str, int] = {}
    try:
        selection = ExactPackageSelection(fixture["package_key"], "1.0.0", fixture["descriptor_digest"])
        configuration.replace_organization_configuration(
            identity, OrganizationConfigurationRequest(0, (selection,), "enable source before tenant probe")
        )
        foreign_organization_id = uuid4()
        with factory.begin() as setup:
            foreign_organization = Organization(id=foreign_organization_id, is_active=True)
            foreign_user = User(
                email=f"maj04-foreign-{foreign_organization_id}@test",
                username=f"maj04-foreign-{foreign_organization_id}", hashed_password="x",
                role="admin", is_active=True, activation_pending=True,
            )
            setup.add_all((foreign_organization, foreign_user)); setup.flush()
            setup.add(UserOrganizationMembership(
                user_id=foreign_user.id, organization_id=foreign_organization_id,
                is_enabled=True, is_selected=True,
            ))
            customer = Customer(name=f"MAJ-04 foreign {foreign_organization_id}", organization_id=foreign_organization_id)
            setup.add(customer); setup.flush()
            project = Project(
                project_code=f"SAT-PRJ-2098-{customer.id + 1000:04d}",
                name="MAJ-04 foreign project", customer_id=customer.id,
                owner_id=foreign_user.id, organization_id=foreign_organization_id,
            )
            setup.add(project); setup.flush()
            foreign_project_id = project.id
        locked, release_lock = Event(), Event()

        def hold_foreign_project() -> None:
            with factory.begin() as session:
                trace["session_b_connection"] = session.scalar(text("SELECT pg_backend_pid()"))
                row = session.scalar(select(Project).where(Project.id == foreign_project_id).with_for_update())
                assert row is not None
                locked.set()
                assert release_lock.wait(10)

        def observe_a(connection, _cursor, statement, _parameters, _context, _executemany):
            if "from projects" in statement.lower() and "for update" in statement.lower():
                trace["session_a_connection"] = connection.connection.get_backend_pid()

        event.listen(engine, "before_cursor_execute", observe_a)
        holder = Thread(target=hold_foreign_project)
        holder.start(); assert locked.wait(10)
        result: list[BaseException] = []
        try:
            def foreign_probe() -> None:
                try:
                    configuration.replace_project_configuration(
                        identity, foreign_project_id, ProjectConfigurationRequest(
                            0, fixture["profile_id"], fixture["profile_digest"], (selection,), "foreign probe"
                        )
                    )
                except BaseException as exc:
                    result.append(exc)

            probe = Thread(target=foreign_probe)
            probe.start(); probe.join(10)
            assert not probe.is_alive()
            assert len(result) == 1 and isinstance(result[0], LookupError)
            assert trace["session_a_connection"] != trace["session_b_connection"]
            with factory() as observed:
                assert observed.get(ProjectPackageConfigurationHead, foreign_project_id) is None
                assert observed.scalar(select(func.count()).select_from(PackageConfigurationAuditEvent).where(
                    PackageConfigurationAuditEvent.project_id == foreign_project_id
                )) == 0
        finally:
            release_lock.set()
            holder.join(10)
            event.remove(engine, "before_cursor_execute", observe_a)
    finally:
        _restore_maj04_registry_pointer(factory, fixture)
        engine.dispose()


def test_guarded_configuration_revalidates_authority_and_hides_cross_organization_project(
    db_session, engineer_user, admin_user
):
    """Frozen request identity never substitutes for locked current authority."""
    descriptor_digest, profile_digest = _seed_configurable_registry(db_session)
    project = _project(db_session, engineer_user)
    factory = _factory(db_session)
    configuration = DisciplinePackageConfigurationService(factory)
    selection = ExactPackageSelection("electrical", "1.0.0", descriptor_digest)
    admin = GuardedRequestIdentity(
        admin_user.id, project.organization_id, admin_user.auth_version
    )
    configuration.replace_organization_configuration(
        admin, OrganizationConfigurationRequest(0, (selection,), "initial")
    )

    # A captured identity with an obsolete mutable authority version cannot
    # create a revision or a success Audit record.
    stale = GuardedRequestIdentity(
        engineer_user.id, project.organization_id, engineer_user.auth_version + 1
    )
    audit_count = db_session.scalar(
        select(func.count()).select_from(PackageConfigurationAuditEvent).where(
            PackageConfigurationAuditEvent.project_id == project.id
        )
    )
    with pytest.raises(PackageWorkspaceForbidden):
        configuration.replace_project_configuration(
            stale, project.id,
            ProjectConfigurationRequest(0, "batch3-profile", profile_digest, (selection,), "stale"),
        )
    assert db_session.get(ProjectPackageConfigurationHead, project.id) is None
    assert db_session.scalar(
        select(func.count()).select_from(PackageConfigurationAuditEvent).where(
            PackageConfigurationAuditEvent.project_id == project.id
        )
    ) == audit_count

    foreign_org = Organization(id=uuid4(), is_active=True)
    db_session.add(foreign_org)
    foreign_customer = Customer(
        name="Foreign guarded configuration customer",
        organization_id=foreign_org.id,
    )
    db_session.add(foreign_customer)
    db_session.flush()
    foreign_project = Project(
        project_code=f"SAT-PRJ-2098-{foreign_customer.id + 1000:04d}",
        name="Foreign guarded configuration project",
        customer_id=foreign_customer.id,
        owner_id=engineer_user.id,
        organization_id=foreign_org.id,
    )
    db_session.add(foreign_project)
    db_session.flush()
    actor = GuardedRequestIdentity(
        engineer_user.id, project.organization_id, engineer_user.auth_version
    )
    with pytest.raises(LookupError):
        configuration.replace_project_configuration(
            actor, foreign_project.id,
            ProjectConfigurationRequest(0, "batch3-profile", profile_digest, (selection,), "foreign"),
        )
    assert db_session.get(ProjectPackageConfigurationHead, foreign_project.id) is None
