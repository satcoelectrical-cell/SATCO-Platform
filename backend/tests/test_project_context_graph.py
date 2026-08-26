from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from app.schemas.project_context import (
    AuthorityClassification, ContextNodeKind, ContextNodeSelector,
    ContextRelationshipKind, ExpandOneHopRequest, FactProvenance,
    GetContextNodeRequest, GraphCandidatePage, GraphDirection, GraphNodeResolved,
    GraphEdgeCandidate, NodeNavigation, OwnerPage, OwnerProtected,
    OwnerResolved, ProjectContextActor, ProjectContextInvalidRequest,
    ProjectContextProtectedNotFound, ProjectContextScope, ProjectNode,
    TemporalClassification, EngineeringRelationshipDiscriminator,
)
from app.services.project_context_service import ProjectContextService


NOW=datetime(2030,1,1,tzinfo=timezone.utc)
ORG=UUID("00000000-0000-0000-0000-000000000001")


class User: id=1


def actor(): return ProjectContextActor(actor_id=1,organization_id=ORG)
def scope(): return ProjectContextScope(project_id=1)
def selector(value=1): return ContextNodeSelector(kind=ContextNodeKind.PROJECT,value=value)
def provenance(owner="project", value="1"):
    return FactProvenance(owner_kind=owner,selector=value,observed_at=NOW,authority_class=AuthorityClassification.HUMAN_AUTHORITATIVE,temporal_class=TemporalClassification.CURRENT)
def project(value=1):
    return ProjectNode(selector=value,project_code=f"P-{value}",project_name=f"Project {value}",lifecycle_status="active",navigation=NodeNavigation(project_id=1),provenance=provenance(value=str(value)),authority_class=AuthorityClassification.HUMAN_AUTHORITATIVE,temporal_class=TemporalClassification.CURRENT)


class Owners:
    def __init__(self): self.calls=[]; self.edge_page=GraphCandidatePage(items=(),observed_at=NOW)
    def project_node(self,**kw): self.calls.append("project_node"); return GraphNodeResolved(item=project(int(kw["selector"].value)))
    def __getattr__(self,name):
        if name.endswith("_node"):
            def node(**kw): self.calls.append(name); return OwnerProtected()
            return node
        if name.endswith("_edges"):
            def edges(**kw): self.calls.append(name); return self.edge_page
            return edges
        raise AttributeError(name)


def test_get_node_exact_dispatch_identity_and_payload_free_protection():
    owners=Owners(); service=ProjectContextService(owners,clock=lambda:NOW)
    result=service.get_context_node(actor=actor(),request=GetContextNodeRequest(scope=scope(),selector=selector()),current_user=User())
    assert result.status=="success" and result.node.selector==1 and owners.calls==["project_node"]
    class Wrong(Owners):
        def project_node(self,**kw): return GraphNodeResolved(item=project(2))
    denied=ProjectContextService(Wrong()).get_context_node(actor=actor(),request=GetContextNodeRequest(scope=scope(),selector=selector()),current_user=User())
    assert isinstance(denied,ProjectContextProtectedNotFound) and denied.model_dump()=={"status":"protected_not_found"}


def test_all_eighteen_kinds_have_fixed_dispatch_and_no_generic_fallback():
    expected={
        ContextNodeKind.PROJECT:"project_node",ContextNodeKind.WORKSPACE:"workspace_node",
        ContextNodeKind.EXECUTION_PLAN:"execution_plan_node",ContextNodeKind.ACTIVITY:"activity_node",
        ContextNodeKind.MILESTONE:"milestone_node",ContextNodeKind.DELIVERABLE:"deliverable_node",
        ContextNodeKind.DELIVERABLE_REVISION:"deliverable_revision_node",ContextNodeKind.RISK:"risk_node",
        ContextNodeKind.ISSUE:"issue_node",ContextNodeKind.HUMAN_DECISION:"decision_node",
        ContextNodeKind.CHANGE:"change_node",ContextNodeKind.CHANGE_IMPACT:"change_impact_node",
        ContextNodeKind.ENGINEERING_OBJECT:"engineering_object_node",ContextNodeKind.ENGINEERING_CONTEXT:"engineering_context_node",
        ContextNodeKind.EVIDENCE:"evidence_node",ContextNodeKind.SUPPORTING_FILE:"supporting_file_node",
        ContextNodeKind.TECHNICAL_REPORT:"technical_report_node",ContextNodeKind.ORGANIZATIONAL_MEMORY:"organizational_memory_node",
    }
    assert len(expected)==18
    service=ProjectContextService(Owners())
    for kind,method in expected.items():
        value=1 if kind in {ContextNodeKind.PROJECT,ContextNodeKind.WORKSPACE,ContextNodeKind.ENGINEERING_CONTEXT} else uuid4()
        owners=Owners(); service=ProjectContextService(owners)
        service.get_context_node(actor=actor(),request=GetContextNodeRequest(scope=scope(),selector=ContextNodeSelector(kind=kind,value=value)),current_user=User())
        assert owners.calls==[method]
    assert not hasattr(service,"resolve_node")


def test_one_hop_reauthorizes_target_never_expands_target_and_is_directional():
    owners=Owners(); start=selector(); target=ContextNodeSelector(kind=ContextNodeKind.PROJECT,value=2)
    edge=GraphEdgeCandidate(candidate_key="01",relationship_selector="r1",relationship_kind=ContextRelationshipKind.CONTEXT_REQUIRES,source=start,target=target,provenance=provenance("relationship","r1"))
    owners.edge_page=GraphCandidatePage(items=(edge,),observed_at=NOW)
    result=ProjectContextService(owners,clock=lambda:NOW).expand_one_hop(actor=actor(),request=ExpandOneHopRequest(scope=scope(),start=start,direction=GraphDirection.OUTGOING),current_user=User())
    assert result.status=="success" and len(result.edges)==1 and [node.selector for node in result.nodes]==[2]
    assert owners.calls.count("project_node")==2
    assert [name for name in owners.calls if name.endswith("_edges")]==["context_relationship_edges"]


def test_denied_target_is_silent_and_page_anchor_is_last_evaluated():
    class Denied(Owners):
        def project_node(self,**kw):
            self.calls.append("project_node")
            return GraphNodeResolved(item=project(1)) if kw["selector"].value==1 else OwnerProtected()
    owners=Denied(); start=selector(); target=ContextNodeSelector(kind=ContextNodeKind.PROJECT,value=2)
    owners.edge_page=GraphCandidatePage(items=(GraphEdgeCandidate(candidate_key="01",relationship_selector="secret",relationship_kind=ContextRelationshipKind.CONTEXT_REQUIRES,source=start,target=target,provenance=provenance("relationship","secret")),),observed_at=NOW)
    result=ProjectContextService(owners,clock=lambda:NOW).expand_one_hop(actor=actor(),request=ExpandOneHopRequest(scope=scope(),start=start),current_user=User())
    assert result.status=="success" and result.edges==() and result.nodes==()
    dumped=result.model_dump(mode="json")
    assert "secret" not in str(dumped) and "total" not in str(dumped)


def test_graph_continuation_is_canonical_bound_tamper_safe_and_checked_first():
    owners=Owners(); service=ProjectContextService(owners,clock=lambda:NOW)
    request=ExpandOneHopRequest(scope=scope(),start=selector(),page_size=10)
    token=service.issue_graph_continuation(actor=actor(),request=request,last_evaluated_key="edge:01")
    assert len(token)<=4096
    valid=ExpandOneHopRequest(scope=scope(),start=selector(),page_size=10,continuation=token)
    assert service.expand_one_hop(actor=actor(),request=valid,current_user=User()).status=="success"
    prior=len(owners.calls)
    tampered=token[:-1]+("A" if token[-1]!="A" else "B")
    result=service.expand_one_hop(actor=actor(),request=ExpandOneHopRequest(scope=scope(),start=selector(),page_size=10,continuation=tampered),current_user=User())
    assert isinstance(result,ProjectContextInvalidRequest) and result.model_dump()=={"status":"invalid_request"} and len(owners.calls)==prior
    expired=ProjectContextService(Owners(),clock=lambda:NOW+timedelta(minutes=16)).expand_one_hop(actor=actor(),request=valid,current_user=User())
    assert isinstance(expired,ProjectContextInvalidRequest)


def test_graph_contract_has_no_depth_or_recursive_enrichment():
    assert "depth" not in ExpandOneHopRequest.model_fields
    assert "relationship_kinds" in ExpandOneHopRequest.model_fields
    assert set(ProjectContextProtectedNotFound.model_fields)=={"status"}

def test_exact_ninety_one_candidate_and_owner_call_budget():
    class LastReaderOwners(Owners):
        def __getattr__(self,name):
            if name.endswith("_node"):
                return super().__getattr__(name)
            if name.endswith("_edges"):
                def edges(**kw):
                    self.calls.append(name)
                    return self.edge_page if name=="context_relationship_edges" else GraphCandidatePage(items=(),observed_at=NOW)
                return edges
            raise AttributeError(name)
    owners=LastReaderOwners();start=selector()
    edges=tuple(GraphEdgeCandidate(candidate_key=f"{index:03d}",relationship_selector=f"r{index}",relationship_kind=ContextRelationshipKind.CONTEXT_REQUIRES,source=start,target=ContextNodeSelector(kind=ContextNodeKind.PROJECT,value=index+2),provenance=provenance("relationship",f"r{index}")) for index in range(91))
    owners.edge_page=GraphCandidatePage(items=edges,observed_at=NOW)
    result=ProjectContextService(owners,clock=lambda:NOW).expand_one_hop(actor=actor(),request=ExpandOneHopRequest(scope=scope(),start=start),current_user=User())
    assert result.status=="success" and len(result.edges)==91 and len(result.nodes)==91
    assert len(owners.calls)==93


def test_relationship_filter_is_closed_distinct_canonical_and_limits_owner_calls():
    from pydantic import ValidationError
    requested=(ContextRelationshipKind.CONTEXT_REQUIRES, ContextRelationshipKind.CONTEXT_PROVIDED_BY)
    with __import__("pytest").raises(ValidationError):
        ExpandOneHopRequest(scope=scope(),start=selector(),relationship_kinds=requested)
    with __import__("pytest").raises(ValidationError):
        ExpandOneHopRequest(scope=scope(),start=selector(),relationship_kinds=(ContextRelationshipKind.CONTEXT_REQUIRES,ContextRelationshipKind.CONTEXT_REQUIRES))
    owners=Owners()
    request=ExpandOneHopRequest(scope=scope(),start=selector(),relationship_kinds=(ContextRelationshipKind.CONTEXT_REQUIRES,))
    ProjectContextService(owners,clock=lambda:NOW).expand_one_hop(actor=actor(),request=request,current_user=User())
    assert [name for name in owners.calls if name.endswith("_edges")]==["context_relationship_edges"]

def test_page_truncation_continuation_anchors_after_last_evaluated_without_skip():
    owners=Owners();start=selector()
    edges=tuple(GraphEdgeCandidate(candidate_key=f"{index:03d}",relationship_selector=f"r{index}",relationship_kind=ContextRelationshipKind.CONTEXT_REQUIRES,source=start,target=ContextNodeSelector(kind=ContextNodeKind.PROJECT,value=index+2),provenance=provenance("relationship",f"r{index}")) for index in range(12))
    owners.edge_page=GraphCandidatePage(items=edges,has_more=True,last_evaluated_key="011",observed_at=NOW)
    service=ProjectContextService(owners,clock=lambda:NOW)
    first=service.expand_one_hop(actor=actor(),request=ExpandOneHopRequest(scope=scope(),start=start,page_size=5),current_user=User())
    assert [edge.relationship_selector for edge in first.edges]==[f"r{i}" for i in range(5)]
    token=first.truncated.continuation.continuation
    second=service.expand_one_hop(actor=actor(),request=ExpandOneHopRequest(scope=scope(),start=start,page_size=5,continuation=token),current_user=User())
    assert [edge.relationship_selector for edge in second.edges]==[f"r{i}" for i in range(5,10)]


def test_canonical_graph_adapter_uses_only_exact_incident_owner_reads():
    from types import SimpleNamespace
    from app.adapters.project_context import ProjectContextGraphAdapter
    from app.schemas.engineering_execution_plan import ExecutionGraphIncidentLink,ExecutionGraphIncidentPage
    from app.schemas.engineering_deliverable import DeliverableGraphIncidentLink,DeliverableGraphIncidentPage
    from app.schemas.project_control import ProjectControlGraphIncidentLink,ProjectControlGraphIncidentPage
    from app.schemas.organizational_memory import OrganizationalMemoryGraphSourceLink,OrganizationalMemoryGraphSourcePage
    ids=[uuid4() for _ in range(8)]
    class Exact:
        def __init__(self):self.calls=[]
        def list(self,**_):raise AssertionError("broad list forbidden")
        def list_active(self,*_,**__):raise AssertionError("broad list_active forbidden")
        def list_authorized_incident_graph_links(self,**kw):
            self.calls.append(kw);kind=kw["selector_kind"]
            if kind=="activity":return ExecutionGraphIncidentPage(items=(ExecutionGraphIncidentLink(relationship="plan_activity",relationship_selector="execution",source_kind="execution_plan",source_id=ids[0],target_kind="activity",target_id=ids[1],owner_version=1),))
            if kind=="deliverable":return DeliverableGraphIncidentPage(items=(DeliverableGraphIncidentLink(relationship="deliverable_activity",relationship_selector="deliverable",source_kind="deliverable",source_id=ids[2],target_kind="activity",target_id=ids[1],owner_version=1),))
            return ProjectControlGraphIncidentPage(items=(ProjectControlGraphIncidentLink(relationship="impact_target",relationship_selector="impact",source_kind="change_impact",source_id=ids[3],target_kind="activity",target_id=ids[1],owner_version=1),))
        def get_authorized_source_report_graph_links(self,*_,**kw):
            self.calls.append(kw);return OrganizationalMemoryGraphSourcePage(items=(OrganizationalMemoryGraphSourceLink(memory_id=ids[4],report_id=ids[5],accepted_report_version=1,memory_version=1,project_id=1,workspace_id=2,observed_at=NOW),))
    exact=Exact(); adapter=ProjectContextGraphAdapter(project=None,workspace=None,execution=exact,execution_actor=object(),deliverables=exact,deliverable_actor=object(),controls=exact,control_actor=object(),objects=None,object_actor=None,context=None,evidence=None,evidence_actor=None,files=None,file_actor_id=1,reports=None,report_actor=None,memory=exact,memory_actor=object(),relationships=None,relationship_actor=None,context_relationships=None)
    shared=dict(actor=actor(),scope=ProjectContextScope(project_id=1,workspace_id=2),direction=GraphDirection.BOTH,page=__import__("app.schemas.project_context",fromlist=["SectionPageRequest"]).SectionPageRequest(page_size=10),current_user=User())
    assert len(adapter.execution_edges(selector=ContextNodeSelector(kind=ContextNodeKind.ACTIVITY,value=ids[1]),**shared).items)==1
    assert len(adapter.deliverable_edges(selector=ContextNodeSelector(kind=ContextNodeKind.DELIVERABLE,value=ids[2]),**shared).items)==1
    assert len(adapter.project_control_edges(selector=ContextNodeSelector(kind=ContextNodeKind.ACTIVITY,value=ids[1]),**shared).items)==1
    assert len(adapter.organizational_memory_edges(selector=ContextNodeSelector(kind=ContextNodeKind.TECHNICAL_REPORT,value=ids[5]),**shared).items)==1
    assert len(exact.calls)==4
