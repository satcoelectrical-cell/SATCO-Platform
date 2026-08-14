"""PATCH-034 Batch 1 pure Aggregate and digest evidence."""

from dataclasses import asdict
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from uuid import uuid4

import pytest

from app.enums.engineering_experience_capture import EngineeringExperienceCaptureLifecycle, EngineeringExperienceSourceKind
from app.enums.organizational_memory import MemoryStanding
from app.enums.technical_report import (
    TechnicalReportAvailabilityStatus, TechnicalReportIntegrityAlgorithm,
    TechnicalReportOwningCapability, TechnicalReportPurpose,
    TechnicalReportSourceClass, TechnicalReportSourceType,
    TechnicalReportVerificationStatus,
)
from app.exceptions.organizational_memory import (
    OrganizationalMemoryIntegrityError, OrganizationalMemoryInvalidLineage,
    OrganizationalMemoryInvalidStanding,
)
from app.models.organizational_memory import OrganizationalMemory
from app.models.organizational_memory_command import (
    AcceptedReportSource, AdmittedReportProjectionV1, admission_material_from_snapshot,
    canonical_digest, canonical_json,
)
from app.models.technical_report_command import (
    CaptureHistoricalBasisV1, PreliminaryQualification, TechnicalReportAcceptedSnapshot,
    TechnicalReportContent, TechnicalReportDraftRevision, TechnicalReportProvenanceEntry,
    canonical_json as technical_report_canonical_json,
)


NOW = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)


def _snapshot(version: int = 2, report_id=None, organization=None, workspace_id=2, project_id=3):
    organization = organization or uuid4(); report_id = report_id or uuid4()
    locator = CaptureHistoricalBasisV1(1, "universal_capture", uuid4(), 1, organization, 3, 2, None, None, EngineeringExperienceSourceKind.OBSERVATION, "Exact source", None, 1, EngineeringExperienceCaptureLifecycle.CAPTURED, NOW)
    integrity = __import__("hashlib").sha256(technical_report_canonical_json(locator)).hexdigest()
    provenance = TechnicalReportProvenanceEntry(uuid4(), 0, TechnicalReportSourceClass.CANONICAL_MATERIAL, TechnicalReportSourceType.UNIVERSAL_CAPTURE, True, TechnicalReportOwningCapability.UNIVERSAL_CAPTURE, "basis", TechnicalReportVerificationStatus.VERIFIED, TechnicalReportAvailabilityStatus.AVAILABLE, "Human", (), locator, TechnicalReportIntegrityAlgorithm.SHA256, integrity)
    return TechnicalReportAcceptedSnapshot(report_id, TechnicalReportPurpose.ENGINEERING_ANALYSIS, organization, workspace_id, project_id, TechnicalReportContent("Scope", "Technical content", ("A",), "Known uncertainty", ("L",), "Conclusion", ("Recommendation",)), PreliminaryQualification(False), (provenance,), TechnicalReportDraftRevision(uuid4(), 1), version, 1, NOW, None)


def _memory(snapshot=None, memory_id=None, audience=(1, 2)):
    snapshot = snapshot or _snapshot(); projection, manifest = admission_material_from_snapshot(snapshot)
    return OrganizationalMemory.admit(memory_id=memory_id or uuid4(), projection=projection, manifest=manifest, admitted_by_id=1, admitted_at=NOW, admission_rationale="Human approved", audience_actor_ids=audience, reuse_restrictions=("Check scope",))


def test_projection_is_exact_non_transformative_and_digests_are_deterministic():
    snapshot = _snapshot(); projection, manifest = admission_material_from_snapshot(snapshot)
    assert projection.content.engineering_scope == snapshot.content.engineering_scope
    assert projection.content.technical_content == snapshot.content.technical_content
    assert projection.content.assumptions == snapshot.content.assumptions
    assert projection.qualification.evidence_deficiencies == snapshot.qualification.evidence_deficiencies
    assert manifest.source_snapshot_digest == snapshot.integrity_digest
    assert manifest.admitted_projection_digest == canonical_digest(projection)
    assert canonical_json(projection) == canonical_json(projection)


def test_semantic_transformation_or_omission_breaks_digest_coherence():
    projection, manifest = admission_material_from_snapshot(_snapshot())
    changed_content = replace(projection.content, conclusions="A newly authored conclusion")
    changed = replace(projection, content=changed_content)
    with pytest.raises(OrganizationalMemoryIntegrityError):
        OrganizationalMemory.admit(memory_id=uuid4(), projection=changed, manifest=manifest, admitted_by_id=1, admitted_at=NOW, admission_rationale="Human approved")


def test_admission_is_active_version_one_and_admitted_state_is_frozen():
    memory = _memory()
    assert memory.standing is MemoryStanding.ACTIVE and memory.version == 1
    with pytest.raises((AttributeError, TypeError)): memory.admission_rationale = "rewrite"


def test_direct_admission_cannot_accept_arbitrary_predecessor_and_initial_evidence_is_coherent():
    import inspect
    assert "predecessor_memory_id" not in inspect.signature(OrganizationalMemory.admit).parameters
    memory = _memory(); history = memory.initial_history(event_id=uuid4())
    assert (history.from_standing, history.to_standing, history.aggregate_version) == (None, MemoryStanding.ACTIVE, 1)
    assert history.memory_id == memory.id and history.actor_id == memory.admitted_by_id


def test_withdrawal_is_single_active_to_terminal_transition():
    memory = _memory(); withdrawn, history = memory.withdraw(expected_version=1, actor_id=1, occurred_at=NOW + timedelta(seconds=1), reason="obsolete")
    assert withdrawn.standing is MemoryStanding.WITHDRAWN and withdrawn.version == 2
    assert memory.standing is MemoryStanding.ACTIVE
    assert history.from_standing is MemoryStanding.ACTIVE and history.to_standing is MemoryStanding.WITHDRAWN
    with pytest.raises(OrganizationalMemoryInvalidStanding): withdrawn.withdraw(expected_version=2, actor_id=1, occurred_at=NOW + timedelta(seconds=2), reason="again")


def test_successor_does_not_supersede_predecessor_and_has_one_predecessor():
    predecessor = _memory(); next_snapshot = _snapshot(version=3, organization=predecessor.organization_id, workspace_id=predecessor.workspace_id, project_id=predecessor.project_id)
    projection, manifest = admission_material_from_snapshot(next_snapshot)
    successor = OrganizationalMemory.create_successor(predecessor=predecessor, memory_id=uuid4(), projection=projection, manifest=manifest, admitted_by_id=1, admitted_at=NOW + timedelta(seconds=1), admission_rationale="replacement", audience_actor_ids=predecessor.audience_actor_ids, reuse_restrictions=predecessor.reuse_restrictions)
    assert predecessor.standing is MemoryStanding.ACTIVE
    assert successor.standing is MemoryStanding.ACTIVE and successor.predecessor_memory_id == predecessor.id


def test_explicit_supersession_changes_only_predecessor_and_is_terminal():
    predecessor = _memory(); projection, manifest = admission_material_from_snapshot(_snapshot(version=3, organization=predecessor.organization_id, workspace_id=predecessor.workspace_id, project_id=predecessor.project_id))
    successor = OrganizationalMemory.create_successor(predecessor=predecessor, memory_id=uuid4(), projection=projection, manifest=manifest, admitted_by_id=1, admitted_at=NOW + timedelta(seconds=1), admission_rationale="replacement", audience_actor_ids=predecessor.audience_actor_ids, reuse_restrictions=predecessor.reuse_restrictions)
    superseded, history = predecessor.supersede_with(successor, expected_version=1, expected_replacement_version=1, actor_id=1, occurred_at=NOW + timedelta(seconds=2), reason="new accepted basis")
    assert superseded.standing is MemoryStanding.SUPERSEDED and superseded.replacement_memory_id == successor.id
    assert successor.standing is MemoryStanding.ACTIVE and successor.version == 1
    assert history.replacement_memory_id == successor.id
    with pytest.raises(OrganizationalMemoryInvalidStanding): superseded.withdraw(expected_version=2, actor_id=1, occurred_at=NOW + timedelta(seconds=3), reason="illegal")


def test_successor_audience_may_narrow_but_never_broaden_and_supersession_accepts_narrowing():
    predecessor = _memory(audience=(1, 2, 3)); projection, manifest = admission_material_from_snapshot(_snapshot(version=3, organization=predecessor.organization_id, workspace_id=predecessor.workspace_id, project_id=predecessor.project_id))
    successor = OrganizationalMemory.create_successor(predecessor=predecessor, memory_id=uuid4(), projection=projection, manifest=manifest, admitted_by_id=1, admitted_at=NOW + timedelta(seconds=1), admission_rationale="narrower", audience_actor_ids=(1, 3), reuse_restrictions=predecessor.reuse_restrictions)
    superseded, _ = predecessor.supersede_with(successor, expected_version=1, expected_replacement_version=1, actor_id=1, occurred_at=NOW + timedelta(seconds=2), reason="replace")
    assert successor.audience_actor_ids == (1, 3) and superseded.standing is MemoryStanding.SUPERSEDED
    with pytest.raises(OrganizationalMemoryInvalidLineage):
        OrganizationalMemory.create_successor(predecessor=predecessor, memory_id=uuid4(), projection=projection, manifest=manifest, admitted_by_id=1, admitted_at=NOW + timedelta(seconds=1), admission_rationale="broader", audience_actor_ids=(1, 2, 3, 4), reuse_restrictions=predecessor.reuse_restrictions)


def test_domain_event_type_must_match_current_standing():
    from app.enums.organizational_memory import MemoryEventType
    from app.exceptions.organizational_memory import OrganizationalMemoryValidationError
    memory = _memory()
    event = memory.event(event_id=uuid4(), event_type=MemoryEventType.ADMITTED, actor_id=1, occurred_at=NOW, command_id=uuid4(), correlation_id=uuid4(), causation_id=uuid4())
    assert event.payload.memory_id == memory.id and event.payload.standing is MemoryStanding.ACTIVE
    with pytest.raises(OrganizationalMemoryValidationError):
        memory.event(event_id=uuid4(), event_type=MemoryEventType.WITHDRAWN, actor_id=1, occurred_at=NOW, command_id=uuid4(), correlation_id=uuid4(), causation_id=uuid4())


def test_initial_admission_event_and_history_are_coherent_and_event_is_non_plaintext():
    from app.enums.organizational_memory import MemoryEventType

    memory = _memory()
    event_id = uuid4()
    command_id = uuid4()
    correlation_id = uuid4()
    causation_id = uuid4()
    event = memory.event(
        event_id=event_id,
        event_type=MemoryEventType.ADMITTED,
        actor_id=memory.admitted_by_id,
        occurred_at=memory.admitted_at,
        command_id=command_id,
        correlation_id=correlation_id,
        causation_id=causation_id,
    )
    history = memory.initial_history(event_id=event_id)

    assert event.event_id == history.event_id == event_id
    assert event.memory_id == history.memory_id == memory.id
    assert event.aggregate_version == history.aggregate_version == memory.version == 1
    assert event.organization_id == history.organization_id == memory.organization_id
    assert event.actor_id == history.actor_id == memory.admitted_by_id
    assert event.occurred_at == history.occurred_at == memory.admitted_at
    assert event.standing == history.to_standing == MemoryStanding.ACTIVE
    assert history.from_standing is None
    assert event.event_type is MemoryEventType.ADMITTED
    assert event.payload_schema_version == 1
    assert event.command_id == command_id
    assert event.correlation_id == correlation_id
    assert event.causation_id == causation_id

    payload = asdict(event.payload)
    assert tuple(payload) == (
        "memory_id", "aggregate_version", "organization_id", "workspace_id",
        "project_id", "standing", "actor_id", "occurred_at", "command_id",
        "correlation_id", "causation_id", "source_report_id",
        "source_accepted_version", "predecessor_memory_id",
        "replacement_memory_id", "provenance_entry_count",
    )
    assert payload["predecessor_memory_id"] is None
    assert payload["replacement_memory_id"] is None
    assert payload["provenance_entry_count"] == len(memory.manifest.provenance_entries)
    serialized = canonical_json(event.payload).decode("utf-8")
    serialized_values = {
        str(value).lower()
        for value in json.loads(serialized).values()
        if isinstance(value, str)
    }
    prohibited_plaintext = (
        memory.projection.content.engineering_scope,
        memory.projection.content.technical_content,
        memory.admission_rationale,
        *memory.projection.content.limitations,
        *memory.projection.content.recommendations,
        *memory.reuse_restrictions,
        *(entry.reliance_role for entry in memory.manifest.provenance_entries),
    )
    assert all(value.lower() not in serialized_values for value in prohibited_plaintext)
    assert not {
        "content", "projection", "snapshot", "admission_rationale", "limitations",
        "recommendations", "reuse_restrictions", "provenance", "reliance_role",
    }.intersection(json.loads(serialized))


def test_invalid_successor_source_or_scope_is_rejected():
    predecessor = _memory(); same_projection, same_manifest = predecessor.projection, predecessor.manifest
    with pytest.raises(OrganizationalMemoryInvalidLineage): OrganizationalMemory.create_successor(predecessor=predecessor, memory_id=uuid4(), projection=same_projection, manifest=same_manifest, admitted_by_id=1, admitted_at=NOW + timedelta(seconds=1), admission_rationale="same")
    projection, manifest = admission_material_from_snapshot(_snapshot(version=3)); wrong_scope = replace(projection, workspace_id=99); wrong_manifest = replace(manifest, admitted_projection_digest=canonical_digest(wrong_scope))
    with pytest.raises(OrganizationalMemoryInvalidLineage): OrganizationalMemory.create_successor(predecessor=predecessor, memory_id=uuid4(), projection=wrong_scope, manifest=wrong_manifest, admitted_by_id=1, admitted_at=NOW + timedelta(seconds=1), admission_rationale="wrong scope")
