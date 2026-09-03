"""Non-completing persistence primitives for immutable Registry projections."""

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.discipline_package import (
    CompatibilityProfile,
    PackageDescriptor,
    RegistryRelease,
)


class DisciplinePackageRepository:
    """All methods use the caller's Session and never complete a transaction."""

    def __init__(self, session: Session):
        self.session = session

    def release(self, registry_digest: str) -> RegistryRelease | None:
        return self.session.get(RegistryRelease, registry_digest)

    def current_release(self) -> RegistryRelease | None:
        return self.session.scalar(select(RegistryRelease).where(RegistryRelease.is_current.is_(True)))

    def descriptor(self, package_key: str, package_version: str) -> PackageDescriptor | None:
        return self.session.get(PackageDescriptor, (package_key, package_version))

    def profile(self, profile_id: str, profile_digest: str) -> CompatibilityProfile | None:
        return self.session.get(CompatibilityProfile, (profile_id, profile_digest))

    def add(self, value: object) -> None:
        self.session.add(value)

    def clear_current_release(self) -> None:
        self.session.execute(update(RegistryRelease).where(RegistryRelease.is_current.is_(True)).values(is_current=False))

    def mark_current(self, registry_digest: str) -> None:
        self.session.execute(
            update(RegistryRelease)
            .where(RegistryRelease.registry_digest == registry_digest)
            .values(is_current=True)
        )
