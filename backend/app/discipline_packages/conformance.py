"""Pure conformance primitives for reviewed source descriptors and adapters."""

from __future__ import annotations

from dataclasses import dataclass

from app.adapters.discipline_package_registry import StaticDisciplinePackageAdapter
from app.discipline_packages.contracts import DisciplinePackageDescriptorV1
from app.discipline_packages.registry import assemble_registry
from app.enums.discipline_package import DisciplinePackageStanding
from app.exceptions.discipline_package import DisciplinePackageError, DisciplinePackageReasonCode


@dataclass(frozen=True, slots=True)
class ConformanceResult:
    passed: bool
    reason_codes: tuple[DisciplinePackageReasonCode, ...]


def validate_descriptor_conformance(
    descriptor: DisciplinePackageDescriptorV1,
    adapter: StaticDisciplinePackageAdapter,
) -> ConformanceResult:
    """Verify one descriptor through the same registry admission boundary."""

    from app.discipline_packages.contracts import DescriptorRegistrationV1, RegistryReleaseManifestV1

    try:
        manifest = RegistryReleaseManifestV1(
            release_id="conformance.fixture",
            core_contract_version=1,
            descriptors=(DescriptorRegistrationV1(
                descriptor=descriptor,
                adapter_id=adapter.adapter_id,
                standing=DisciplinePackageStanding.EXECUTABLE_SUPPORTED,
            ),),
        )
        assemble_registry(manifest, adapters=(adapter,))
    except DisciplinePackageError as error:
        return ConformanceResult(False, (error.reason_code,))
    except (TypeError, ValueError):
        return ConformanceResult(False, (DisciplinePackageReasonCode.INVALID_DESCRIPTOR,))
    return ConformanceResult(True, ())
