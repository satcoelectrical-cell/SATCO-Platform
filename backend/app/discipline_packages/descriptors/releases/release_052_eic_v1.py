"""PATCH-052 static source release; assembly/activation remains deployment-owned."""

from app.discipline_packages.canonical import descriptor_digest
from app.discipline_packages.contracts import (
    AllowedCombinationV1, CompatibilityProfileV1, DescriptorRegistrationV1,
    ExactPackageSelectionV1, RegistryReleaseManifestV1,
)
from app.discipline_packages.descriptors.eic_v1 import DESCRIPTORS_V1
from app.enums.discipline_package import DisciplinePackageStanding


def _selection(descriptor):
    return ExactPackageSelectionV1(
        package_key=descriptor.package_key,
        package_version=descriptor.package_version,
        descriptor_digest=descriptor_digest(descriptor),
    )


_BY_KEY = {item.package_key: item for item in DESCRIPTORS_V1}
_E = _selection(_BY_KEY["electrical"])
_I = _selection(_BY_KEY["instrumentation"])
_C = _selection(_BY_KEY["control_automation"])

RELEASE_052_EIC_V1 = RegistryReleaseManifestV1(
    release_id="patch-052.eic-v1",
    core_contract_version=1,
    descriptors=tuple(DescriptorRegistrationV1(
        descriptor=item, adapter_id=item.adapter_id,
        standing=DisciplinePackageStanding.EXECUTABLE_SUPPORTED,
    ) for item in DESCRIPTORS_V1),
    profiles=(CompatibilityProfileV1(
        profile_id="commercial_v1.eic", profile_version="1.0.0", core_contract_version=1,
        combinations=(
            AllowedCombinationV1(members=(_E,)), AllowedCombinationV1(members=(_I,)),
            AllowedCombinationV1(members=(_C,)), AllowedCombinationV1(members=(_E, _I)),
            AllowedCombinationV1(members=(_E, _C)), AllowedCombinationV1(members=(_I, _C)),
            AllowedCombinationV1(members=(_E, _I, _C)),
        ),
        aggregate_resource_ceiling=190,
    ),),
)
