"""Real PostgreSQL vectors for source-to-current-projection readiness parity."""

import pytest
from sqlalchemy import func, select

from app.adapters.discipline_package_registry import StaticDisciplinePackageAdapter
from app.discipline_packages.contracts import (
    DescriptorRegistrationV1,
    DisciplinePackageDescriptorV1,
    RegistryReleaseManifestV1,
)
from app.discipline_packages.descriptors.releases.release_051_core_v1 import RELEASE_051_CORE_V1
from app.discipline_packages.identity import PackageKey, PackageVersion
from app.discipline_packages.registry import assemble_registry
from app.enums.discipline_package import DisciplinePackageStanding
from app.models.discipline_package import (
    CompatibilityMember,
    CompatibilityProfile,
    PackageDescriptor,
    RegistryMembership,
    RegistryProfileMembership,
    RegistryRelease,
)
from app.services.discipline_package_registry_service import validate_source_projection_parity


def _install_current_core_projection(db_session, *, manifest_json=None) -> RegistryRelease:
    for release in db_session.scalars(select(RegistryRelease).where(RegistryRelease.is_current.is_(True))):
        release.is_current = False
    registry = assemble_registry(RELEASE_051_CORE_V1)
    row = RegistryRelease(
        registry_digest=str(registry.digest),
        release_id=registry.manifest.release_id,
        core_contract_version=registry.manifest.core_contract_version,
        is_current=True,
        manifest_json=registry.manifest.model_dump(mode="json") if manifest_json is None else manifest_json,
    )
    db_session.add(row)
    db_session.flush()
    return row


def _projection_counts(db_session) -> tuple[int, int, int, int, int, int]:
    return tuple(
        db_session.scalar(select(func.count()).select_from(model))
        for model in (
            RegistryRelease,
            PackageDescriptor,
            RegistryMembership,
            CompatibilityProfile,
            RegistryProfileMembership,
            CompatibilityMember,
        )
    )


def test_current_source_projection_parity_passes_and_readiness_does_not_repair(db_session):
    _install_current_core_projection(db_session)
    registry = assemble_registry(RELEASE_051_CORE_V1)
    before = _projection_counts(db_session)
    validate_source_projection_parity(db_session, registry)
    assert _projection_counts(db_session) == before


def test_source_projection_drift_fails_closed_without_mutation(db_session):
    registry = assemble_registry(RELEASE_051_CORE_V1)
    release = _install_current_core_projection(db_session, manifest_json={
        **registry.manifest.model_dump(mode="json"), "release_id": "drifted",
    })
    before = _projection_counts(db_session)
    with pytest.raises(RuntimeError, match="registry projection unavailable"):
        validate_source_projection_parity(db_session, assemble_registry(RELEASE_051_CORE_V1))

    assert _projection_counts(db_session) == before


def test_missing_or_wrong_current_release_fails_closed(db_session):
    release = _install_current_core_projection(db_session)
    release.is_current = False
    db_session.flush()
    with pytest.raises(RuntimeError, match="registry projection unavailable"):
        validate_source_projection_parity(db_session, assemble_registry(RELEASE_051_CORE_V1))


def test_membership_standing_drift_fails_closed_independently_of_descriptor(db_session):
    descriptor = DisciplinePackageDescriptorV1(
        package_key="readiness_standing",
        package_version="1.0.0",
        primary_discipline_id="electrical",
        core_contract_versions=(1,),
        display_name="Readiness standing fixture",
        entitlement_key="fixture.readiness_standing",
        adapter_id="fixture.readiness_standing",
    )
    manifest = RegistryReleaseManifestV1(
        release_id="readiness.standing",
        core_contract_version=1,
        descriptors=(DescriptorRegistrationV1(
            descriptor=descriptor,
            adapter_id=descriptor.adapter_id,
            standing=DisciplinePackageStanding.HISTORICAL_READ_ONLY,
        ),),
    )
    adapter = StaticDisciplinePackageAdapter(
        descriptor.adapter_id,
        PackageKey(descriptor.package_key),
        PackageVersion(descriptor.package_version),
        frozenset(),
    )
    registry = assemble_registry(manifest, adapters=(adapter,))
    for release in db_session.scalars(select(RegistryRelease).where(RegistryRelease.is_current.is_(True))):
        release.is_current = False
    db_session.add_all((
        RegistryRelease(
            registry_digest=str(registry.digest),
            release_id=manifest.release_id,
            core_contract_version=manifest.core_contract_version,
            is_current=True,
            manifest_json=manifest.model_dump(mode="json"),
        ),
        PackageDescriptor(
            package_key=descriptor.package_key,
            package_version=descriptor.package_version,
            descriptor_digest=str(registry.descriptor_digests[(descriptor.package_key, descriptor.package_version)]),
            primary_discipline_id=descriptor.primary_discipline_id,
            adapter_id=descriptor.adapter_id,
            descriptor_json=descriptor.model_dump(mode="json"),
        ),
    ))
    db_session.flush()
    db_session.add(RegistryMembership(
        registry_digest=str(registry.digest),
        package_key=descriptor.package_key,
        package_version=descriptor.package_version,
        standing="executable_supported",
    ))
    db_session.flush()
    before = _projection_counts(db_session)
    with pytest.raises(RuntimeError, match="registry projection unavailable"):
        validate_source_projection_parity(db_session, registry)
    assert _projection_counts(db_session) == before
