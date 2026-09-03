"""PATCH-051 Core release: explicit empty operational-package Registry."""

from app.discipline_packages.contracts import RegistryReleaseManifestV1
from app.discipline_packages.identity import RegistryDigest


RELEASE_051_CORE_V1 = RegistryReleaseManifestV1(
    release_id="patch-051.core-v1",
    core_contract_version=1,
    descriptors=(),
    profiles=(),
    expected_registry_digest=RegistryDigest("9f785b463f1ad0374de2eefc93af5591db596d92972628a24d9b7f0e028baece"),
)
