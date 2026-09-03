"""Assembly-to-projection service; it has no HTTP or tenant-write responsibility."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import DisciplinePackageGuardMode
from app.discipline_packages.canonical import combination_digest
from app.discipline_packages.registry import TrustedDisciplinePackageRegistryV1
from app.models.discipline_package import (
    CompatibilityMember, CompatibilityProfile, PackageDescriptor, RegistryMembership,
    RegistryProfileMembership, RegistryRelease,
)
from app.repositories.discipline_package_unit_of_work import DisciplinePackageUnitOfWork


class DisciplinePackageRegistryService:
    def install(self, registry: TrustedDisciplinePackageRegistryV1, uow: DisciplinePackageUnitOfWork) -> None:
        """Idempotently stage an immutable source projection under the exclusive guard."""

        assert uow.repository is not None
        uow.acquire_guard(DisciplinePackageGuardMode.EXCLUSIVE)
        digest = str(registry.digest)
        if uow.repository.release(digest) is not None:
            return
        release = RegistryRelease(
            registry_digest=digest,
            release_id=registry.manifest.release_id,
            core_contract_version=registry.manifest.core_contract_version,
            is_current=False,
            manifest_json=registry.manifest.model_dump(mode="json"),
        )
        uow.repository.add(release)
        # These models deliberately expose no ORM relationships: the
        # installer is the sole writer and persistence is governed by the
        # database's immutable projection constraints.  Flush each FK parent
        # layer explicitly so a descriptor/membership release is never
        # emitted ahead of the release it belongs to.
        assert uow.session is not None
        uow.session.flush()
        for identity, descriptor in registry.descriptors.items():
            key, version = identity
            descriptor_digest = str(registry.descriptor_digests[identity])
            if uow.repository.descriptor(key, version) is None:
                uow.repository.add(PackageDescriptor(
                    package_key=key, package_version=version, descriptor_digest=descriptor_digest,
                    primary_discipline_id=descriptor.primary_discipline_id, adapter_id=descriptor.adapter_id,
                    descriptor_json=descriptor.model_dump(mode="json"),
                ))
        uow.session.flush()
        for identity in registry.descriptors:
            key, version = identity
            uow.repository.add(RegistryMembership(
                registry_digest=digest, package_key=key, package_version=version,
                standing=registry.membership_standings[identity].value,
            ))
        new_profile_identities: set[tuple[str, str]] = set()
        for identity, profile in registry.profiles.items():
            profile_id, _profile_version = identity
            profile_digest = str(registry.profile_digests[identity])
            if uow.repository.profile(profile_id, profile_digest) is None:
                new_profile_identities.add(identity)
                uow.repository.add(CompatibilityProfile(
                    profile_id=profile_id, profile_digest=profile_digest,
                    profile_json=profile.model_dump(mode="json"),
                ))
        uow.session.flush()
        for identity, profile in registry.profiles.items():
            profile_id, _profile_version = identity
            profile_digest = str(registry.profile_digests[identity])
            if identity in new_profile_identities:
                for combination in profile.combinations:
                    for member in combination.members:
                        uow.repository.add(CompatibilityMember(
                            profile_id=profile_id, profile_digest=profile_digest,
                            combination_digest=str(combination_digest([
                                {
                                    "package_key": item.package_key,
                                    "package_version": item.package_version,
                                    "descriptor_digest": str(item.descriptor_digest),
                                }
                                for item in combination.members
                            ])),
                            package_key=member.package_key, package_version=member.package_version,
                            descriptor_digest=str(registry.descriptor_digests[(member.package_key, member.package_version)]),
                        ))
            uow.repository.add(RegistryProfileMembership(
                registry_digest=digest, profile_id=profile_id, profile_digest=profile_digest,
            ))
        # Activation may follow installation in the same explicit outer UoW.
        # Flush makes staged rows visible without completing that transaction.
        uow.session.flush()

    def activate(self, registry_digest: str, uow: DisciplinePackageUnitOfWork) -> None:
        assert uow.repository is not None
        uow.acquire_guard(DisciplinePackageGuardMode.EXCLUSIVE)
        if uow.repository.release(registry_digest) is None:
            raise ValueError("unknown Registry projection")
        uow.repository.clear_current_release()
        uow.repository.mark_current(registry_digest)


def validate_source_projection_parity(
    session: Session, registry: TrustedDisciplinePackageRegistryV1
) -> None:
    """Fail closed unless the current immutable projection exactly mirrors source.

    This is intentionally a read-only verifier: registry installation and
    activation remain deployment-only exclusive-guard operations.  Historical
    rows are permitted, but the single *current* release must be a complete
    source-faithful projection including descriptor/profile/combination
    provenance.
    """

    digest = str(registry.digest)
    current = list(session.scalars(select(RegistryRelease).where(RegistryRelease.is_current.is_(True))))
    if len(current) != 1:
        raise RuntimeError("registry projection unavailable")
    release = current[0]
    if (
        release.registry_digest != digest
        or release.release_id != registry.manifest.release_id
        or release.core_contract_version != registry.manifest.core_contract_version
        or release.manifest_json != registry.manifest.model_dump(mode="json")
    ):
        raise RuntimeError("registry projection unavailable")

    expected_descriptors = {
        identity: (descriptor, str(registry.descriptor_digests[identity]))
        for identity, descriptor in registry.descriptors.items()
    }
    memberships = list(session.scalars(select(RegistryMembership).where(RegistryMembership.registry_digest == digest)))
    observed_memberships = {(row.package_key, row.package_version): row.standing for row in memberships}
    if observed_memberships != {
        identity: registry.membership_standings[identity].value
        for identity in expected_descriptors
    }:
        raise RuntimeError("registry projection unavailable")
    for (package_key, package_version), (descriptor, descriptor_digest) in expected_descriptors.items():
        stored = session.get(PackageDescriptor, (package_key, package_version))
        if stored is None or (
            stored.descriptor_digest != descriptor_digest
            or stored.primary_discipline_id != descriptor.primary_discipline_id
            or stored.adapter_id != descriptor.adapter_id
            or stored.descriptor_json != descriptor.model_dump(mode="json")
        ):
            raise RuntimeError("registry projection unavailable")

    expected_profiles = {
        profile.profile_id: (profile, str(registry.profile_digests[(profile.profile_id, profile.profile_version)]))
        for profile in registry.profiles.values()
    }
    profile_memberships = list(session.scalars(select(RegistryProfileMembership).where(RegistryProfileMembership.registry_digest == digest)))
    if {(row.profile_id, row.profile_digest) for row in profile_memberships} != {
        (profile_id, profile_digest) for profile_id, (_profile, profile_digest) in expected_profiles.items()
    }:
        raise RuntimeError("registry projection unavailable")
    for profile_id, (profile, profile_digest) in expected_profiles.items():
        stored_profile = session.get(CompatibilityProfile, (profile_id, profile_digest))
        if stored_profile is None or stored_profile.profile_json != profile.model_dump(mode="json"):
            raise RuntimeError("registry projection unavailable")
        expected_members = set()
        for combination in profile.combinations:
            combination_hash = str(combination_digest([
                {
                    "package_key": member.package_key,
                    "package_version": member.package_version,
                    "descriptor_digest": str(member.descriptor_digest),
                }
                for member in combination.members
            ]))
            expected_members.update(
                (combination_hash, member.package_key, member.package_version, str(member.descriptor_digest))
                for member in combination.members
            )
        observed_members = {
            (row.combination_digest, row.package_key, row.package_version, row.descriptor_digest)
            for row in session.scalars(select(CompatibilityMember).where(
                CompatibilityMember.profile_id == profile_id,
                CompatibilityMember.profile_digest == profile_digest,
            ))
        }
        if observed_members != expected_members:
            raise RuntimeError("registry projection unavailable")
