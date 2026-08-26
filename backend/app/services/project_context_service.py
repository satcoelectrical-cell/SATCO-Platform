"""Fixed, read-only ten-section Project Context composition."""
from __future__ import annotations
import base64
import json
import os
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.core.config import settings
from app.schemas.project_context import *
from app.schemas.project_context import _NodeProjection

class ProjectContextService:
    def __init__(self, owners, clock=None): self.owners=owners; self.clock=clock or (lambda: datetime.now(timezone.utc))
    def assemble_project_context(self, *, actor, request, current_user):
        if current_user.id != actor.actor_id: return ProjectContextProtectedNotFound()
        try:
            self._validate_continuations(actor, request)
        except Exception:
            return ProjectContextInvalidRequest()
        start=self.clock(); sections=[]; calls=0
        for section in request.sections:
            results=[]
            if section.kind is ProjectContextSectionKind.PROJECT_BASIS: results=[self.owners.project_basis(actor=actor,scope=request.scope,page=section,current_user=current_user)]
            elif section.kind is ProjectContextSectionKind.EXECUTION: results=[self.owners.execution(actor=actor,scope=request.scope,page=section,current_user=current_user)]
            elif section.kind is ProjectContextSectionKind.DELIVERABLES: results=[self.owners.deliverables(actor=actor,scope=request.scope,page=section,current_user=current_user)]
            elif section.kind is ProjectContextSectionKind.PROJECT_CONTROLS: results=[self.owners.project_control(control_kind=k,actor=actor,scope=request.scope,page=section,current_user=current_user) for k in ("risk","issue","human_decision","change")]
            elif section.kind is ProjectContextSectionKind.ENGINEERING_CONTEXT: results=[self.owners.engineering_context(actor=actor,scope=request.scope,page=section,current_user=current_user)]
            elif section.kind is ProjectContextSectionKind.ENGINEERING_OBJECTS: results=[self.owners.engineering_objects(actor=actor,scope=request.scope,page=section,current_user=current_user)]
            elif section.kind is ProjectContextSectionKind.EVIDENCE: results=[self.owners.evidence(actor=actor,scope=request.scope,page=section,current_user=current_user)]
            elif section.kind is ProjectContextSectionKind.SUPPORTING_FILES: results=[self.owners.supporting_files(actor=actor,scope=request.scope,page=section,current_user=current_user)]
            elif section.kind is ProjectContextSectionKind.TECHNICAL_REPORTS: results=[self.owners.technical_reports(actor=actor,scope=request.scope,page=section,current_user=current_user)]
            else: results=[self.owners.organizational_memory(actor=actor,scope=request.scope,page=section,current_user=current_user)]
            calls += len(results)
            if calls>13: return ProjectContextInvalidRequest()
            if any(isinstance(result, OwnerInvalid) for result in results): return ProjectContextInvalidRequest()
            sections.append(self._section(section.kind, results, self.clock(), actor, request, section))
        if all(s.state.state is SourceAvailability.UNAVAILABLE for s in sections): return ProjectContextUnavailable()
        partial=any(s.state.state in {SourceAvailability.UNAVAILABLE,SourceAvailability.NOT_DISCLOSED} or (isinstance(s.state,SectionAvailable) and s.state.truncated.truncated) for s in sections)
        result=ProjectContextSuccess(observation_started_at=start,observation_completed_at=self.clock(),observation_status=ContextObservationStatus.PARTIAL if partial else ContextObservationStatus.COMPLETE_WITHIN_BOUNDS,sections=tuple(sections))
        return ProjectContextUnavailable() if len(json.dumps(result.model_dump(mode="json")).encode())>524288 else result

    def get_context_node(self, *, actor, request, current_user):
        if current_user.id != actor.actor_id:
            return ProjectContextProtectedNotFound()
        result = self._read_node(actor=actor, scope=request.scope, selector=request.selector, current_user=current_user)
        if isinstance(result, GraphNodeResolved) and isinstance(result.item, _NodeProjection):
            if result.item.node_kind is not request.selector.kind or result.item.selector != request.selector.value:
                return ProjectContextProtectedNotFound()
            if not self._node_in_scope(result.item, request.scope, actor):
                return ProjectContextProtectedNotFound()
            return ContextNodeSuccess(node=result.item)
        if isinstance(result, OwnerInvalid): return ProjectContextInvalidRequest()
        if isinstance(result, OwnerUnavailable): return ProjectContextUnavailable()
        return ProjectContextProtectedNotFound()

    def expand_one_hop(self, *, actor, request, current_user):
        if current_user.id != actor.actor_id:
            return ProjectContextProtectedNotFound()
        try:
            anchor = self._validate_graph_continuation(actor, request)
        except Exception:
            return ProjectContextInvalidRequest()
        start_result = self._read_node(actor=actor, scope=request.scope, selector=request.start, current_user=current_user)
        if isinstance(start_result, OwnerInvalid): return ProjectContextInvalidRequest()
        if isinstance(start_result, OwnerUnavailable): return ProjectContextUnavailable()
        if not isinstance(start_result, GraphNodeResolved) or not isinstance(start_result.item, _NodeProjection) or start_result.item.node_kind is not request.start.kind or start_result.item.selector != request.start.value or not self._node_in_scope(start_result.item, request.scope, actor):
            return ProjectContextProtectedNotFound()
        start = start_result.item
        calls = 1
        candidates=[]
        reader_more=False
        for reader_name in self._applicable_readers(request.start.kind, request.relationship_kinds):
            if len(candidates) >= 91: reader_more=True; break
            reader=getattr(self.owners, reader_name)
            response=reader(actor=actor,scope=request.scope,selector=request.start,direction=request.direction,page=SectionPageRequest(page_size=91-len(candidates),continuation=anchor),current_user=current_user)
            calls += 1
            if isinstance(response, OwnerUnavailable): continue
            if isinstance(response, OwnerInvalid): return ProjectContextInvalidRequest()
            if isinstance(response, OwnerProtected): continue
            if not isinstance(response, GraphCandidatePage): return ProjectContextUnavailable()
            candidates.extend(
                item for item in response.items
                if self._relationship_requested(item.relationship_kind, request.relationship_kinds)
            )
            reader_more = reader_more or response.has_more
        dedup={self._candidate_identity(item):item for item in candidates}
        ordered=sorted(dedup.values(),key=lambda item:item.candidate_key)
        if anchor is not None: ordered=[item for item in ordered if item.candidate_key>anchor]
        edges=[]; nodes=[]; node_keys=set(); last_evaluated=None; truncated=reader_more
        for candidate in ordered:
            if calls >= 100 or len(edges) >= request.page_size or len(nodes) >= 91:
                truncated=True; break
            target_selector=self._other_endpoint(candidate, request.start, request.direction)
            if target_selector is None:
                last_evaluated=candidate.candidate_key
                continue
            target_result=self._read_node(actor=actor,scope=request.scope,selector=target_selector,current_user=current_user)
            calls += 1
            if not isinstance(target_result,GraphNodeResolved) or not isinstance(target_result.item,_NodeProjection):
                last_evaluated=candidate.candidate_key
                continue
            if target_result.item.node_kind is not target_selector.kind or target_result.item.selector != target_selector.value or not self._node_in_scope(target_result.item,request.scope,actor):
                last_evaluated=candidate.candidate_key
                continue
            edge=ContextEdgeProjection(relationship_selector=candidate.relationship_selector,relationship_kind=candidate.relationship_kind,source=candidate.source,target=candidate.target,provenance=candidate.provenance)
            target_key=(target_selector.kind.value,str(target_selector.value))
            proposed_nodes=nodes if target_key in node_keys else nodes+[target_result.item]
            proposed=OneHopSuccess(start=start,edges=tuple(edges+[edge]),nodes=tuple(proposed_nodes),truncated=TruncationMetadata(truncated=False))
            if len(json.dumps(proposed.model_dump(mode="json"),sort_keys=True,separators=(",",":")).encode())>524288:
                truncated=True; break
            edges.append(edge)
            if target_key not in node_keys:
                nodes.append(target_result.item); node_keys.add(target_key)
            last_evaluated=candidate.candidate_key
        if len(ordered)>len(edges): truncated=truncated or last_evaluated is not None and any(item.candidate_key>last_evaluated for item in ordered)
        continuation=None
        if truncated and last_evaluated:
            token=self.issue_graph_continuation(actor=actor,request=request,last_evaluated_key=last_evaluated)
            continuation=ContinuationMetadata(continuation=token,last_evaluated_key=last_evaluated)
        result=OneHopSuccess(start=start,edges=tuple(edges),nodes=tuple(nodes),truncated=TruncationMetadata(truncated=bool(continuation),continuation=continuation))
        return ProjectContextUnavailable() if len(json.dumps(result.model_dump(mode="json")).encode())>524288 else result

    def _read_node(self, *, actor, scope, selector, current_user):
        kw=dict(actor=actor,scope=scope,selector=selector,current_user=current_user)
        if selector.kind is ContextNodeKind.PROJECT: return self.owners.project_node(**kw)
        if selector.kind is ContextNodeKind.WORKSPACE: return self.owners.workspace_node(**kw)
        if selector.kind is ContextNodeKind.EXECUTION_PLAN: return self.owners.execution_plan_node(**kw)
        if selector.kind is ContextNodeKind.ACTIVITY: return self.owners.activity_node(**kw)
        if selector.kind is ContextNodeKind.MILESTONE: return self.owners.milestone_node(**kw)
        if selector.kind is ContextNodeKind.DELIVERABLE: return self.owners.deliverable_node(**kw)
        if selector.kind is ContextNodeKind.DELIVERABLE_REVISION: return self.owners.deliverable_revision_node(**kw)
        if selector.kind is ContextNodeKind.RISK: return self.owners.risk_node(**kw)
        if selector.kind is ContextNodeKind.ISSUE: return self.owners.issue_node(**kw)
        if selector.kind is ContextNodeKind.HUMAN_DECISION: return self.owners.decision_node(**kw)
        if selector.kind is ContextNodeKind.CHANGE: return self.owners.change_node(**kw)
        if selector.kind is ContextNodeKind.CHANGE_IMPACT: return self.owners.change_impact_node(**kw)
        if selector.kind is ContextNodeKind.ENGINEERING_OBJECT: return self.owners.engineering_object_node(**kw)
        if selector.kind is ContextNodeKind.ENGINEERING_CONTEXT: return self.owners.engineering_context_node(**kw)
        if selector.kind is ContextNodeKind.EVIDENCE: return self.owners.evidence_node(**kw)
        if selector.kind is ContextNodeKind.SUPPORTING_FILE: return self.owners.supporting_file_node(**kw)
        if selector.kind is ContextNodeKind.TECHNICAL_REPORT: return self.owners.technical_report_node(**kw)
        if selector.kind is ContextNodeKind.ORGANIZATIONAL_MEMORY: return self.owners.organizational_memory_node(**kw)
        return OwnerInvalid()

    @staticmethod
    def _node_in_scope(node, scope, actor):
        if node.navigation.project_id != scope.project_id: return False
        if scope.workspace_id is not None and node.navigation.workspace_id not in {None,scope.workspace_id}: return False
        return getattr(node,"organization_id",actor.organization_id)==actor.organization_id

    @staticmethod
    def _other_endpoint(candidate, start, direction):
        if candidate.source==start and direction in {GraphDirection.OUTGOING,GraphDirection.BOTH}: return candidate.target
        if candidate.target==start and direction in {GraphDirection.INCOMING,GraphDirection.BOTH}: return candidate.source
        return None

    @staticmethod
    def _candidate_identity(candidate):
        relationship = candidate.relationship_kind.model_dump_json() if hasattr(candidate.relationship_kind,"model_dump_json") else str(candidate.relationship_kind.value)
        return (candidate.source.kind.value,str(candidate.source.value),relationship,candidate.relationship_selector,candidate.target.kind.value,str(candidate.target.value))

    @staticmethod
    def _relationship_key(relationship):
        if isinstance(relationship, ContextRelationshipKind):
            return f"context:{relationship.value}"
        return f"engineering:{relationship.family.value}:{relationship.relationship_type.value}"

    @classmethod
    def _relationship_requested(cls, relationship, requested):
        return not requested or cls._relationship_key(relationship) in {
            cls._relationship_key(item) for item in requested
        }

    @classmethod
    def _applicable_readers(cls, kind, requested):
        mapping = {
            ContextNodeKind.PROJECT: ("context_relationship_edges",),
            ContextNodeKind.WORKSPACE: ("context_relationship_edges",),
            ContextNodeKind.EXECUTION_PLAN: ("execution_edges",),
            ContextNodeKind.ACTIVITY: ("execution_edges", "deliverable_edges", "project_control_edges"),
            ContextNodeKind.MILESTONE: ("execution_edges", "deliverable_edges", "project_control_edges"),
            ContextNodeKind.DELIVERABLE: ("deliverable_edges", "project_control_edges"),
            ContextNodeKind.DELIVERABLE_REVISION: ("deliverable_edges", "project_control_edges"),
            ContextNodeKind.RISK: (),
            ContextNodeKind.ISSUE: (),
            ContextNodeKind.HUMAN_DECISION: ("project_control_edges",),
            ContextNodeKind.CHANGE: ("project_control_edges",),
            ContextNodeKind.CHANGE_IMPACT: ("project_control_edges",),
            ContextNodeKind.ENGINEERING_OBJECT: ("engineering_relationship_edges", "technical_report_edges"),
            ContextNodeKind.ENGINEERING_CONTEXT: ("context_relationship_edges",),
            ContextNodeKind.EVIDENCE: ("project_control_edges", "evidence_file_edges", "technical_report_edges"),
            ContextNodeKind.SUPPORTING_FILE: ("deliverable_edges", "project_control_edges", "evidence_file_edges"),
            ContextNodeKind.TECHNICAL_REPORT: ("technical_report_edges", "organizational_memory_edges"),
            ContextNodeKind.ORGANIZATIONAL_MEMORY: ("organizational_memory_edges",),
        }
        readers = mapping[kind]
        if not requested:
            return readers
        reader_kinds = {
            "engineering_relationship_edges": None,
            "context_relationship_edges": {
                ContextRelationshipKind.CONTEXT_REQUIRES,
                ContextRelationshipKind.CONTEXT_PROVIDED_BY,
                ContextRelationshipKind.CONTEXT_CONSUMED_BY,
                ContextRelationshipKind.CONTEXT_POTENTIALLY_AFFECTS,
            },
            "execution_edges": {
                ContextRelationshipKind.PLAN_ACTIVITY,
                ContextRelationshipKind.PLAN_MILESTONE,
                ContextRelationshipKind.ACTIVITY_DEPENDENCY,
                ContextRelationshipKind.MILESTONE_ACTIVITY,
            },
            "deliverable_edges": {
                ContextRelationshipKind.DELIVERABLE_ACTIVITY,
                ContextRelationshipKind.DELIVERABLE_MILESTONE,
                ContextRelationshipKind.DELIVERABLE_REVISION,
                ContextRelationshipKind.REVISION_REPRESENTATION,
            },
            "project_control_edges": {
                ContextRelationshipKind.DECISION_SUCCESSOR,
                ContextRelationshipKind.CHANGE_SUCCESSOR,
                ContextRelationshipKind.CHANGE_IMPACT,
                ContextRelationshipKind.IMPACT_TARGET,
            },
            "evidence_file_edges": {ContextRelationshipKind.EVIDENCE_SUPPORTING_FILE},
            "technical_report_edges": {
                ContextRelationshipKind.REPORT_EVIDENCE_PROVENANCE,
                ContextRelationshipKind.REPORT_OBJECT_PROVENANCE,
            },
            "organizational_memory_edges": {ContextRelationshipKind.MEMORY_SOURCE_REPORT},
        }
        requested_context = {item for item in requested if isinstance(item, ContextRelationshipKind)}
        has_engineering = any(isinstance(item, EngineeringRelationshipDiscriminator) for item in requested)
        return tuple(
            reader for reader in readers
            if (reader_kinds[reader] is None and has_engineering)
            or (reader_kinds[reader] is not None and bool(reader_kinds[reader] & requested_context))
        )

    def _validate_graph_continuation(self, actor, request):
        if request.continuation is None: return None
        token=request.continuation
        if len(token)>4096: raise ValueError("cursor exceeds bound")
        raw=base64.b64decode(token+"="*(-len(token)%4),altchars=b"-_",validate=True)
        if len(raw)<29 or base64.urlsafe_b64encode(raw).decode().rstrip("=")!=token: raise ValueError("noncanonical token")
        payload=json.loads(AESGCM(self._token_key()).decrypt(raw[:12],raw[12:],b"project-context-one-hop:v1"))
        expected={"v":1,"operation":"expand_one_hop","actor":actor.actor_id,"organization":str(actor.organization_id),"project":request.scope.project_id,"workspace":request.scope.workspace_id,"start_kind":request.start.kind.value,"start":str(request.start.value),"relationship_kinds":[self._relationship_key(item) for item in request.relationship_kinds],"direction":request.direction.value,"page_size":request.page_size}
        if set(payload)!=set(expected)|{"iat","exp","last_evaluated_key"} or any(payload.get(k)!=v for k,v in expected.items()) or type(payload["iat"]) is not int or type(payload["exp"]) is not int or payload["exp"]<=int(self.clock().timestamp()) or payload["exp"]-payload["iat"]!=900 or not isinstance(payload["last_evaluated_key"],str) or not payload["last_evaluated_key"]: raise ValueError("token binding")
        return payload["last_evaluated_key"]

    def issue_graph_continuation(self, *, actor, request, last_evaluated_key):
        issued_at=int(self.clock().timestamp())
        payload={"v":1,"operation":"expand_one_hop","actor":actor.actor_id,"organization":str(actor.organization_id),"project":request.scope.project_id,"workspace":request.scope.workspace_id,"start_kind":request.start.kind.value,"start":str(request.start.value),"relationship_kinds":[self._relationship_key(item) for item in request.relationship_kinds],"direction":request.direction.value,"page_size":request.page_size,"iat":issued_at,"exp":issued_at+900,"last_evaluated_key":last_evaluated_key}
        nonce=os.urandom(12); encrypted=AESGCM(self._token_key()).encrypt(nonce,json.dumps(payload,sort_keys=True,separators=(",",":")).encode(),b"project-context-one-hop:v1")
        return base64.urlsafe_b64encode(nonce+encrypted).decode().rstrip("=")

    @staticmethod
    def _token_key():
        return sha256((settings.SECRET_KEY + ":project-context-continuation:v1").encode()).digest()

    def _validate_continuations(self, actor, request):
        """Verify caller supplied canonical AES-GCM cursors before owner reads."""
        for section in request.sections:
            token = section.continuation
            if token is None:
                continue
            if len(token) > 4096:
                raise ValueError("cursor exceeds bound")
            raw = base64.b64decode(token + "=" * (-len(token) % 4), altchars=b"-_", validate=True)
            if len(raw) < 29 or base64.urlsafe_b64encode(raw).decode().rstrip("=") != token:
                raise ValueError("noncanonical token")
            payload = json.loads(AESGCM(self._token_key()).decrypt(raw[:12], raw[12:], b"project-context-continuation:v1"))
            expected = {"v": 1, "operation": "assemble_project_context", "actor": actor.actor_id, "organization": str(actor.organization_id), "project": request.scope.project_id, "workspace": request.scope.workspace_id, "section": section.kind.value, "page_size": section.page_size}
            if set(payload) != set(expected) | {"iat", "exp", "last_evaluated_key"} or any(payload.get(k) != v for k, v in expected.items()) or type(payload["iat"]) is not int or type(payload["exp"]) is not int or payload["exp"] <= int(self.clock().timestamp()) or payload["exp"] - payload["iat"] != 900 or not isinstance(payload["last_evaluated_key"], str) or not payload["last_evaluated_key"]:
                raise ValueError("token binding")

    def issue_continuation(self, *, actor, request, section, last_evaluated_key):
        """Canonical authenticated continuation used only for a bounded owner page."""
        issued_at = int(self.clock().timestamp())
        payload = {"v": 1, "operation": "assemble_project_context", "actor": actor.actor_id, "organization": str(actor.organization_id), "project": request.scope.project_id, "workspace": request.scope.workspace_id, "section": section.kind.value, "page_size": section.page_size, "iat": issued_at, "exp": issued_at + 900, "last_evaluated_key": str(last_evaluated_key)}
        nonce = os.urandom(12)
        encrypted = AESGCM(self._token_key()).encrypt(nonce, json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(), b"project-context-continuation:v1")
        return base64.urlsafe_b64encode(nonce + encrypted).decode().rstrip("=")
    def _section(self, kind, results, observed, actor, request, page):
        if any(r is None or isinstance(r,OwnerUnavailable) for r in results): return ProjectContextSection(kind=kind,state=SectionUnavailable())
        if any(isinstance(r,OwnerProtected) for r in results): return ProjectContextSection(kind=kind,state=SectionNotDisclosed())
        items=[]
        for r in results:
            if isinstance(r,OwnerPage): items.extend(r.items)
            elif isinstance(r,OwnerResolved): items.append(r.item)
        allowed = {
            ProjectContextSectionKind.PROJECT_BASIS: ProjectBasisItem,
            ProjectContextSectionKind.EXECUTION: ExecutionPlanItem,
            ProjectContextSectionKind.DELIVERABLES: DeliverableItem,
            ProjectContextSectionKind.PROJECT_CONTROLS: ProjectControlItem,
            ProjectContextSectionKind.ENGINEERING_CONTEXT: EngineeringContextProjection,
            ProjectContextSectionKind.ENGINEERING_OBJECTS: EngineeringObjectItem,
            ProjectContextSectionKind.EVIDENCE: EvidenceItem,
            ProjectContextSectionKind.SUPPORTING_FILES: SupportingFileItem,
            ProjectContextSectionKind.TECHNICAL_REPORTS: TechnicalReportItem,
            ProjectContextSectionKind.ORGANIZATIONAL_MEMORY: OrganizationalMemoryItem,
        }[kind]
        if any(not isinstance(item, allowed) for item in items):
            return ProjectContextSection(kind=kind, state=SectionUnavailable())
        safe=tuple(items)
        if not safe and kind in {ProjectContextSectionKind.PROJECT_BASIS,ProjectContextSectionKind.EXECUTION}: return ProjectContextSection(kind=kind,state=SectionNotEstablished())
        if not safe: return ProjectContextSection(kind=kind,state=SectionEmpty())
        truncated = any(isinstance(result, OwnerPage) and result.has_more for result in results)
        last_key = next((result.last_evaluated_key for result in reversed(results) if isinstance(result, OwnerPage) and result.last_evaluated_key), None)
        continuation = None
        if truncated:
            if last_key is None:
                return ProjectContextSection(kind=kind, state=SectionUnavailable())
            continuation = ContinuationMetadata(continuation=self.issue_continuation(actor=actor, request=request, section=page, last_evaluated_key=last_key), last_evaluated_key=last_key)
        return ProjectContextSection(kind=kind,items=safe,state=SectionAvailable(visible_count=len(safe),observed_at=observed,truncated=TruncationMetadata(truncated=truncated, continuation=continuation)))
