from datetime import datetime, timezone
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.enums.engineering_relationship import RelationshipFamily, RelationshipType
from app.schemas.project_context import (
    AuthorityClassification,
    CANONICAL_SECTION_ORDER,
    ContextNodeKind,
    ContextNodeSelector,
    ContextObservationStatus,
    ContextRelationshipKind,
    EngineeringRelationshipDiscriminator,
    FactProvenance,
    ProjectContextInvalidRequest,
    ProjectContextRequest,
    ProjectContextScope,
    ProjectContextSectionKind,
    SectionAvailable,
    SectionEmpty,
    SectionNotDisclosed,
    SectionPageRequest,
    TemporalClassification,
    TruncationMetadata,
)


def test_exact_context_section_allow_list_is_closed_and_canonical():
    assert tuple(ProjectContextSectionKind) == CANONICAL_SECTION_ORDER
    request = ProjectContextRequest(scope=ProjectContextScope(project_id=7))
    assert tuple(item.kind for item in request.sections) == CANONICAL_SECTION_ORDER
    assert "capture" not in {item.value for item in ProjectContextSectionKind}
    assert "journal" not in {item.value for item in ProjectContextSectionKind}
    assert "interface_commitment" not in {item.value for item in ProjectContextSectionKind}
    with pytest.raises(ValidationError):
        ProjectContextRequest(
            scope=ProjectContextScope(project_id=7),
            sections=(
                {"kind": "execution"},
                {"kind": "project_basis"},
            ),
        )


def test_exact_node_allow_list_has_no_foundation_or_untyped_selector():
    assert len(ContextNodeKind) == 18
    assert "foundation" not in {kind.value for kind in ContextNodeKind}
    assert ContextNodeSelector(
        kind=ContextNodeKind.ENGINEERING_CONTEXT, value=12
    ).value == 12
    assert ContextNodeSelector(
        kind=ContextNodeKind.EVIDENCE,
        value=UUID("00000000-0000-0000-0000-000000000001"),
    ).kind is ContextNodeKind.EVIDENCE
    with pytest.raises(ValidationError):
        ContextNodeSelector(kind=ContextNodeKind.PROJECT, value="7")
    with pytest.raises(ValidationError):
        ContextNodeSelector(kind=ContextNodeKind.EVIDENCE, value=7)


def test_relationship_vocabulary_is_closed_without_wildcard_pairs():
    valid = EngineeringRelationshipDiscriminator(
        family=RelationshipFamily.STRUCTURAL,
        relationship_type=RelationshipType.PART_OF,
    )
    assert valid.relationship_type is RelationshipType.PART_OF
    with pytest.raises(ValidationError):
        EngineeringRelationshipDiscriminator(
            family=RelationshipFamily.STRUCTURAL,
            relationship_type=RelationshipType.POWERED_BY,
        )
    assert {item.value for item in ContextRelationshipKind} == {
        "context_requires", "context_provided_by", "context_consumed_by",
        "context_potentially_affects", "plan_activity", "plan_milestone",
        "activity_dependency", "milestone_activity", "deliverable_activity",
        "deliverable_milestone", "deliverable_revision",
        "revision_representation", "decision_successor", "change_successor",
        "change_impact", "impact_target", "evidence_supporting_file",
        "report_evidence_provenance", "report_object_provenance",
        "memory_source_report",
    }


def test_envelopes_provenance_and_protected_results_are_closed():
    now = datetime.now(timezone.utc)
    metadata = TruncationMetadata(
        truncated=True,
        continuation={"continuation": "opaque", "last_evaluated_key": "context:7"},
    )
    assert SectionAvailable(
        visible_count=1, truncated=metadata, observed_at=now
    ).state.value == "available"
    assert SectionEmpty().state.value == "empty"
    assert SectionNotDisclosed().model_dump() == {"state": "not_disclosed"}
    assert ProjectContextInvalidRequest().model_dump() == {"status": "invalid_request"}
    provenance = FactProvenance(
        owner_kind="engineering_context", selector="7", version=1,
        standing="current", observed_at=now,
        authority_class=AuthorityClassification.HUMAN_AUTHORITATIVE,
        temporal_class=TemporalClassification.CURRENT,
    )
    assert "actor_id" not in provenance.model_dump()
    assert ContextObservationStatus.PARTIAL.value == "partial"
    with pytest.raises(ValidationError):
        SectionPageRequest(page_size=101)
def test_batch3_graph_contract_is_closed_to_eighteen_nodes_and_twenty_context_relations():
    from app.schemas.project_context import ContextNodeKind, ContextRelationshipKind, ExpandOneHopRequest
    assert len(ContextNodeKind)==18
    assert len(ContextRelationshipKind)==20
    assert set(ExpandOneHopRequest.model_fields)=={"scope","start","relationship_kinds","direction","page_size","continuation"}
    assert "depth" not in ExpandOneHopRequest.model_fields
