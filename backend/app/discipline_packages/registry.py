"""Deterministic trusted source Registry assembly with no I/O or plugin loading."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from app.adapters.discipline_package_registry import StaticDisciplinePackageAdapter, static_adapter_table
from app.discipline_packages.canonical import canonical_json_bytes, descriptor_digest, profile_digest, registry_digest
from app.discipline_packages.contributions import (
    MAX_DEPENDENCY_DEPTH,
    MAX_DEPENDENCY_VISITS,
    MAX_DESCRIPTOR_CANONICAL_BYTES,
    MAX_EXECUTABLE_DESCRIPTOR_VERSIONS,
    MAX_REGISTRY_CANONICAL_BYTES,
)
from app.discipline_packages.contracts import (
    CompatibilityProfileV1,
    DescriptorRegistrationV1,
    DisciplinePackageDescriptorV1,
    RegistryReleaseManifestV1,
)
from app.discipline_packages.identity import DescriptorDigest, ProfileDigest, RegistryDigest
from app.enums.discipline_package import DisciplinePackageStanding
from app.exceptions.discipline_package import (
    DisciplinePackageError,
    DisciplinePackageReasonCode,
    RegistryAssemblyError,
)


@dataclass(frozen=True, slots=True)
class TrustedDisciplinePackageRegistryV1:
    manifest: RegistryReleaseManifestV1
    digest: RegistryDigest
    descriptors: Mapping[tuple[str, str], DisciplinePackageDescriptorV1]
    descriptor_digests: Mapping[tuple[str, str], DescriptorDigest]
    membership_standings: Mapping[tuple[str, str], DisciplinePackageStanding]
    profiles: Mapping[tuple[str, str], CompatibilityProfileV1]
    profile_digests: Mapping[tuple[str, str], ProfileDigest]
    adapters: Mapping[tuple[str, str], StaticDisciplinePackageAdapter]

    def descriptor(self, package_key: str, package_version: str) -> DisciplinePackageDescriptorV1 | None:
        return self.descriptors.get((package_key, package_version))

    def membership_standing(
        self, package_key: str, package_version: str
    ) -> DisciplinePackageStanding | None:
        return self.membership_standings.get((package_key, package_version))


def assemble_registry(
    manifest: RegistryReleaseManifestV1,
    *,
    adapters: tuple[StaticDisciplinePackageAdapter, ...] | None = None,
) -> TrustedDisciplinePackageRegistryV1:
    """Validate source descriptors in the accepted fixed order and freeze output."""

    try:
        adapter_table = static_adapter_table() if adapters is None else adapters
        adapter_by_identity = _validate_adapters(adapter_table)
        registrations = _ordered_registrations(manifest)
        descriptors = tuple(item.descriptor for item in registrations)
        descriptor_by_identity = {(item.package_key, item.package_version): item for item in descriptors}
        standing_by_identity = {
            (item.descriptor.package_key, item.descriptor.package_version): item.standing
            for item in registrations
        }
        _validate_core_and_adapters(
            descriptors,
            standing_by_identity,
            manifest.core_contract_version,
            adapter_by_identity,
        )
        _validate_dependencies(descriptors, descriptor_by_identity)
        _validate_profiles(manifest.profiles, descriptor_by_identity)
        _validate_resource_bounds(manifest, descriptors)

        descriptor_digests = {
            identity: descriptor_digest(descriptor)
            for identity, descriptor in descriptor_by_identity.items()
        }
        profile_digests = {
            (profile.profile_id, profile.profile_version): profile_digest(profile)
            for profile in manifest.profiles
        }
        release_payload = {
            "schema_version": manifest.schema_version,
            "release_id": manifest.release_id,
            "core_contract_version": manifest.core_contract_version,
            "descriptors": [
                {
                    "package_key": registration.descriptor.package_key,
                    "package_version": registration.descriptor.package_version,
                    "descriptor_digest": str(descriptor_digests[(registration.descriptor.package_key, registration.descriptor.package_version)]),
                    "adapter_id": registration.adapter_id,
                    "standing": registration.standing.value,
                }
                for registration in registrations
            ],
            "profiles": [
                {
                    "profile_id": profile.profile_id,
                    "profile_version": profile.profile_version,
                    "profile_digest": str(profile_digests[(profile.profile_id, profile.profile_version)]),
                }
                for profile in sorted(manifest.profiles, key=lambda item: (item.profile_id, item.profile_version))
            ],
        }
        digest = registry_digest(release_payload)
        if manifest.expected_registry_digest is not None and manifest.expected_registry_digest != digest:
            raise RegistryAssemblyError(DisciplinePackageReasonCode.REGISTRY_DIGEST_MISMATCH)
        return TrustedDisciplinePackageRegistryV1(
            manifest=manifest,
            digest=digest,
            descriptors=MappingProxyType(descriptor_by_identity),
            descriptor_digests=MappingProxyType(descriptor_digests),
            membership_standings=MappingProxyType(standing_by_identity),
            profiles=MappingProxyType({(profile.profile_id, profile.profile_version): profile for profile in manifest.profiles}),
            profile_digests=MappingProxyType(profile_digests),
            adapters=MappingProxyType(adapter_by_identity),
        )
    except DisciplinePackageError:
        raise
    except (TypeError, ValueError) as error:
        raise RegistryAssemblyError(DisciplinePackageReasonCode.INVALID_DESCRIPTOR) from error


def _validate_adapters(adapters: tuple[StaticDisciplinePackageAdapter, ...]) -> dict[tuple[str, str], StaticDisciplinePackageAdapter]:
    table: dict[tuple[str, str], StaticDisciplinePackageAdapter] = {}
    for adapter in adapters:
        identity = (str(adapter.package_key), str(adapter.package_version))
        if identity in table:
            raise RegistryAssemblyError(DisciplinePackageReasonCode.DUPLICATE_ADAPTER)
        table[identity] = adapter
    return table


def _ordered_registrations(
    manifest: RegistryReleaseManifestV1,
) -> tuple[DescriptorRegistrationV1, ...]:
    registrations = tuple(manifest.descriptors)
    identities = tuple(
        (item.descriptor.package_key, item.descriptor.package_version)
        for item in registrations
    )
    if len(identities) != len(set(identities)):
        raise RegistryAssemblyError(DisciplinePackageReasonCode.DUPLICATE_DESCRIPTOR)
    return tuple(
        sorted(
            registrations,
            key=lambda item: (
                item.descriptor.package_key,
                item.descriptor.package_version,
            ),
        )
    )


def _validate_core_and_adapters(
    descriptors: tuple[DisciplinePackageDescriptorV1, ...],
    membership_standings: Mapping[tuple[str, str], DisciplinePackageStanding],
    core_contract_version: int,
    adapters: Mapping[tuple[str, str], StaticDisciplinePackageAdapter],
) -> None:
    executable = 0
    for descriptor in descriptors:
        if core_contract_version not in descriptor.core_contract_versions:
            raise RegistryAssemblyError(DisciplinePackageReasonCode.CORE_CONTRACT_MISMATCH)
        if len(canonical_json_bytes(descriptor)) > MAX_DESCRIPTOR_CANONICAL_BYTES:
            raise RegistryAssemblyError(DisciplinePackageReasonCode.RESOURCE_LIMIT_EXCEEDED)
        identity = (descriptor.package_key, descriptor.package_version)
        adapter = adapters.get(identity)
        if adapter is None or adapter.adapter_id != descriptor.adapter_id:
            raise RegistryAssemblyError(DisciplinePackageReasonCode.STATIC_ADAPTER_REQUIRED)
        declared_capabilities = frozenset(
            item.id for item in descriptor.contributions.deterministic_rule_hooks
        ) | frozenset(
            item.hook_id for item in descriptor.contributions.standards_hooks
        ) | frozenset(
            item.interface_type_id for item in descriptor.contributions.cross_discipline_interfaces
        )
        if adapter.capability_ids != declared_capabilities:
            raise RegistryAssemblyError(DisciplinePackageReasonCode.STATIC_ADAPTER_REQUIRED)
        if membership_standings[identity] is DisciplinePackageStanding.EXECUTABLE_SUPPORTED:
            executable += 1
    if executable > MAX_EXECUTABLE_DESCRIPTOR_VERSIONS:
        raise RegistryAssemblyError(DisciplinePackageReasonCode.RESOURCE_LIMIT_EXCEEDED)


def _validate_dependencies(
    descriptors: tuple[DisciplinePackageDescriptorV1, ...],
    by_identity: Mapping[tuple[str, str], DisciplinePackageDescriptorV1],
) -> None:
    graph: dict[tuple[str, str], tuple[tuple[str, str], ...]] = {}
    for descriptor in descriptors:
        identity = (descriptor.package_key, descriptor.package_version)
        dependencies = tuple(sorted((item.package_key, item.package_version) for item in descriptor.dependencies))
        for dependency in dependencies:
            if dependency not in by_identity:
                raise RegistryAssemblyError(DisciplinePackageReasonCode.MISSING_DEPENDENCY)
        graph[identity] = dependencies
        for conflict in descriptor.conflicts:
            if (conflict.package_key, conflict.package_version) not in by_identity:
                raise RegistryAssemblyError(DisciplinePackageReasonCode.UNSUPPORTED_VERSION)
    for root in sorted(graph):
        _walk_dependency_graph(root, graph, (), 0, set())


def _walk_dependency_graph(
    current: tuple[str, str],
    graph: Mapping[tuple[str, str], tuple[tuple[str, str], ...]],
    lineage: tuple[tuple[str, str], ...],
    depth: int,
    visited: set[tuple[str, str]],
) -> None:
    if current in lineage:
        raise RegistryAssemblyError(DisciplinePackageReasonCode.INVALID_DESCRIPTOR)
    if depth > MAX_DEPENDENCY_DEPTH or len(visited) >= MAX_DEPENDENCY_VISITS:
        raise RegistryAssemblyError(DisciplinePackageReasonCode.RESOURCE_LIMIT_EXCEEDED)
    visited.add(current)
    for child in sorted(graph[current]):
        _walk_dependency_graph(child, graph, lineage + (current,), depth + 1, visited)


def _validate_profiles(
    profiles: tuple[CompatibilityProfileV1, ...],
    descriptors: Mapping[tuple[str, str], DisciplinePackageDescriptorV1],
) -> None:
    for profile in profiles:
        combination_identities: set[tuple[tuple[str, str], ...]] = set()
        for combination in profile.combinations:
            members = tuple(sorted((member.package_key, member.package_version) for member in combination.members))
            if members in combination_identities:
                raise RegistryAssemblyError(DisciplinePackageReasonCode.INVALID_DESCRIPTOR)
            combination_identities.add(members)
            for member in combination.members:
                descriptor = descriptors.get((member.package_key, member.package_version))
                if descriptor is None:
                    raise RegistryAssemblyError(DisciplinePackageReasonCode.UNSUPPORTED_VERSION)
                if descriptor_digest(descriptor) != member.descriptor_digest:
                    raise RegistryAssemblyError(DisciplinePackageReasonCode.REGISTRY_DIGEST_MISMATCH)


def _validate_resource_bounds(manifest: RegistryReleaseManifestV1, descriptors: tuple[DisciplinePackageDescriptorV1, ...]) -> None:
    taxonomy_ids: set[str] = set()
    contribution_ids: set[tuple[str, str]] = set()
    for descriptor in descriptors:
        for taxonomy in descriptor.contributions.taxonomy_families:
            if taxonomy.id in taxonomy_ids:
                raise RegistryAssemblyError(DisciplinePackageReasonCode.TAXONOMY_COLLISION)
            taxonomy_ids.add(taxonomy.id)
        for namespace, values, identity in _contribution_collision_sets(descriptor):
            for item in values:
                key = (namespace, identity(item))
                if key in contribution_ids:
                    raise RegistryAssemblyError(DisciplinePackageReasonCode.CONTRIBUTION_COLLISION)
                contribution_ids.add(key)
    payload = {
        "manifest": manifest.model_dump(
            mode="python", exclude={"expected_registry_digest"}, exclude_none=True
        ),
        "descriptors": descriptors,
    }
    if len(canonical_json_bytes(payload)) > MAX_REGISTRY_CANONICAL_BYTES:
        raise RegistryAssemblyError(DisciplinePackageReasonCode.RESOURCE_LIMIT_EXCEEDED)


def _contribution_collision_sets(descriptor: DisciplinePackageDescriptorV1):
    """Return the closed EDS-051 collision namespaces for a descriptor."""

    contributions = descriptor.contributions
    return (
        ("object_type", contributions.object_types, lambda item: item.id),
        ("relationship_type", contributions.relationship_types, lambda item: item.id),
        ("context_kind", contributions.context_contributions, lambda item: item.context_kind_id),
        ("rule_hook", contributions.deterministic_rule_hooks, lambda item: item.hook_id),
        ("interface_type", contributions.cross_discipline_interfaces, lambda item: item.interface_type_id),
        ("frontend_key", contributions.frontend_metadata.route_keys, lambda item: item),
        ("frontend_key", contributions.frontend_metadata.navigation_keys, lambda item: item),
        ("frontend_key", contributions.frontend_metadata.component_keys, lambda item: item),
    )
