from uuid import uuid4

from sqlalchemy.orm import sessionmaker

from app.adapters.discipline_package_registry import StaticDisciplinePackageAdapter
from app.discipline_packages.contracts import (
    DescriptorRegistrationV1,
    DisciplinePackageDescriptorV1,
    RegistryReleaseManifestV1,
)
from app.discipline_packages.identity import PackageKey, PackageVersion
from app.discipline_packages.registry import assemble_registry
from app.enums.discipline_package import DisciplinePackageStanding
from app.models.discipline_package import (
    CompatibilityProfile,
    PackageDescriptor,
    RegistryMembership,
    RegistryProfileMembership,
)
from app.repositories.discipline_package_unit_of_work import DisciplinePackageUnitOfWork
from app.services.discipline_package_registry_service import (
    DisciplinePackageRegistryService,
    validate_source_projection_parity,
)


def test_semantic_profile_identity_is_independent_of_registry_membership():
    assert tuple(CompatibilityProfile.__table__.primary_key.columns.keys()) == ("profile_id", "profile_digest")
    assert tuple(RegistryProfileMembership.__table__.primary_key.columns.keys()) == ("registry_digest", "profile_id")
    assert "profile_digest" in RegistryProfileMembership.__table__.c


def test_installer_persists_standing_only_on_release_membership(db_session):
    suffix = uuid4().hex[:12]
    package_key = f"installer_{suffix}"
    descriptor = DisciplinePackageDescriptorV1(
        package_key=package_key,
        package_version="1.0.0",
        primary_discipline_id="electrical",
        core_contract_versions=(1,),
        display_name="Installer standing fixture",
        entitlement_key=f"fixture.{package_key}",
        adapter_id=f"fixture.{package_key}",
    )
    registration = DescriptorRegistrationV1(
        descriptor=descriptor,
        adapter_id=descriptor.adapter_id,
        standing=DisciplinePackageStanding.HISTORICAL_READ_ONLY,
    )
    adapter = StaticDisciplinePackageAdapter(
        descriptor.adapter_id,
        PackageKey(package_key),
        PackageVersion("1.0.0"),
        frozenset(),
    )
    registry = assemble_registry(
        RegistryReleaseManifestV1(
            release_id=f"installer.{suffix}",
            core_contract_version=1,
            descriptors=(registration,),
        ),
        adapters=(adapter,),
    )
    factory = sessionmaker(
        bind=db_session.connection(),
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    with DisciplinePackageUnitOfWork(factory) as uow:
        DisciplinePackageRegistryService().install(registry, uow)
        DisciplinePackageRegistryService().activate(str(registry.digest), uow)
        assert uow.session is not None
        stored_descriptor = uow.session.get(PackageDescriptor, (package_key, "1.0.0"))
        membership = uow.session.get(
            RegistryMembership,
            (str(registry.digest), package_key, "1.0.0"),
        )
        assert stored_descriptor is not None
        assert "standing" not in stored_descriptor.descriptor_json
        assert not hasattr(stored_descriptor, "standing")
        assert membership is not None
        assert membership.standing == "historical_read_only"
        validate_source_projection_parity(uow.session, registry)
