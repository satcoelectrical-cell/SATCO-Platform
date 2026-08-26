from datetime import datetime, timezone
from app.schemas.project_context import *
from app.services.project_context_service import ProjectContextService
from app.adapters.project_context import TechnicalReportProjectContextAdapter
from app.ports.technical_report import AcceptedTechnicalReportSummary, AcceptedTechnicalReportSummaryPage
from uuid import UUID
from types import SimpleNamespace
from datetime import timedelta
class User: id=1
class Owners:
 def __getattr__(self,name):
  def f(**kwargs):
   return OwnerPage(items=(),last_evaluated_key=None,observed_at=datetime.now(timezone.utc))
  return f
 def project_control(self,**kwargs): return self.__getattr__(kwargs["control_kind"])(**kwargs)
def test_ten_sections_and_thirteen_calls():
 r=ProjectContextService(Owners()).assemble_project_context(actor=ProjectContextActor(actor_id=1,organization_id="00000000-0000-0000-0000-000000000001"),request=ProjectContextRequest(scope=ProjectContextScope(project_id=1)),current_user=User())
 assert r.status=="success" and len(r.sections)==10

def test_technical_report_section_consumes_only_owner_safe_summary():
 class Reports:
  def list_accepted_summaries(self, actor, criteria):
   return AcceptedTechnicalReportSummaryPage((AcceptedTechnicalReportSummary(UUID("00000000-0000-0000-0000-000000000010"), 2, 1, 3, "a" * 64, datetime.now(timezone.utc), "engineering_analysis"),), 1, 1, False)
 adapter=TechnicalReportProjectContextAdapter(Reports(), None, "technical_report")
 actor=ProjectContextActor(actor_id=1,organization_id="00000000-0000-0000-0000-000000000001")
 result=adapter.list_authorized_accepted(actor=actor,scope=ProjectContextScope(project_id=1,workspace_id=2),page=SectionPageRequest(page_size=1),current_user=User())
 assert isinstance(result, OwnerPage)
 assert isinstance(result.items[0], TechnicalReportItem)
 assert set(result.items[0].model_dump()) == {"selector","version","standing","provenance","item_kind","report_id","project_id","workspace_id","report_type","title_or_purpose","accepted_version_id","accepted_digest","accepted_at"}


def test_canonical_outcome_discriminators_translate_before_projection_or_disclosure():
 class Reports:
  def list_accepted_summaries(self, actor, criteria): return {"outcome": "protected_not_found", "content": "must-not-leak"}
 actor=ProjectContextActor(actor_id=1,organization_id="00000000-0000-0000-0000-000000000001")
 result=TechnicalReportProjectContextAdapter(Reports(),None,"technical_report").list_authorized_accepted(actor=actor,scope=ProjectContextScope(project_id=1,workspace_id=2),page=SectionPageRequest(),current_user=User())
 assert isinstance(result, OwnerProtected) and result.model_dump()=={"status":"protected"}

def test_request_scoped_composition_uses_real_canonical_service_classes(monkeypatch, db_session):
 from app.dependencies.auth import AuthenticatedOrganizationContext
 from app.dependencies.project_context import get_project_context_application
 from app.dependencies.supporting_file import SupportingFileApplication
 from app.services.engineering_object_service import EngineeringObjectService
 from app.services.evidence_service import EvidenceService
 from app.services.technical_report_service import TechnicalReportService
 from tests.test_supporting_file_service import service as in_memory_supporting_service
 import app.dependencies.project_foundation as foundation_dependency
 import app.dependencies.project_control as control_dependency
 import app.dependencies.project_context as context_dependency
 store_service=in_memory_supporting_service()
 file_app=SupportingFileApplication(store_service, 1, UUID("00000000-0000-0000-0000-000000000001"))
 monkeypatch.setattr(foundation_dependency, "supporting_file_service", lambda db: store_service)
 monkeypatch.setattr(control_dependency, "supporting_file_service", lambda db: store_service)
 monkeypatch.setattr(context_dependency, "get_supporting_file_application", lambda db, context: file_app)
 context=AuthenticatedOrganizationContext(SimpleNamespace(id=1), UUID("00000000-0000-0000-0000-000000000001"))
 app=get_project_context_application(db_session, context)
 owners=app.service.owners
 assert isinstance(owners._objects._service, EngineeringObjectService)
 assert isinstance(owners._evidence._service, EvidenceService)
 assert isinstance(owners._reports._service, TechnicalReportService)
 assert owners._files._service is store_service


def test_exact_ten_section_projection_field_allow_lists_exclude_owner_internals():
    """The section contract is closed: a later owner response cannot escape it."""
    matrices = {
      ProjectBasisItem: {"selector","version","standing","provenance","item_kind","project_id","project_code","project_name","project_status","foundation_established","foundation_version","purpose","engineering_basis","current_stage","readiness","ordered_in_scope","ordered_out_scope","completion_basis","required_project_inputs"},
      ExecutionPlanItem: {"selector","version","standing","provenance","item_kind","plan_id","project_id","plan_version","activities","milestones","dependencies","progress"},
      DeliverableItem: {"selector","version","standing","provenance","item_kind","deliverable_id","project_id","workspace_id","code","title","discipline","deliverable_type","purpose","activity_ids","milestone_ids","target_date","external_authority","current_revision"},
      ProjectControlItem: {"selector","version","standing","provenance","item_kind","control_id","project_id","workspace_id","temporal_class","predecessor_present","category","likelihood","impact","severity","impacts"},
      EngineeringObjectItem: {"selector","version","standing","provenance","item_kind","object_id","organization_id","project_id","workspace_id","family","discipline","object_type","object_subtype","lifecycle","authority_standing","created_at","updated_at"},
      EvidenceItem: {"selector","version","standing","provenance","item_kind","evidence_id","project_id","workspace_id","evidence_kind","safe_source_reference","created_at","updated_at"},
      SupportingFileItem: {"selector","version","standing","provenance","item_kind","asset_id","project_id","workspace_id","filename","media_type","byte_size","lifecycle","created_at","updated_at"},
      TechnicalReportItem: {"selector","version","standing","provenance","item_kind","report_id","project_id","workspace_id","report_type","title_or_purpose","accepted_version_id","accepted_digest","accepted_at"},
      OrganizationalMemoryItem: {"selector","version","standing","provenance","item_kind","memory_id","project_id","workspace_id","limitations_present","source_report_id","source_report_version","admitted_at"},
    }
    for projection, allowed in matrices.items():
      assert set(projection.model_fields) == allowed
      assert not ({"human_id","content","body","rationale","private_url","storage_key","object_key","repository_id","total","provenance_entries"} & set(projection.model_fields))
    assert set(EngineeringContextProjection.model_fields) == {"context_id","context_key","project_id","workspace_id","kind","authority","lifecycle","purpose","version","payload","created_at","updated_at","provenance"}


class CountingOwners:
 def __init__(self, result=None): self.calls=[]; self.result=result
 def __getattr__(self,name):
  def f(**kwargs):
   self.calls.append(name)
   return self.result or OwnerPage(items=(), last_evaluated_key=None, observed_at=datetime.now(timezone.utc))
  return f
 def project_control(self, **kwargs):
  self.calls.append("project_control:" + kwargs["control_kind"])
  return self.result or OwnerPage(items=(), last_evaluated_key=None, observed_at=datetime.now(timezone.utc))


def _request(*sections, continuation=None):
 return ProjectContextRequest(scope=ProjectContextScope(project_id=1, workspace_id=2), sections=tuple(ProjectContextSectionRequest(kind=kind, continuation=continuation) for kind in sections))


def _actor(): return ProjectContextActor(actor_id=1,organization_id="00000000-0000-0000-0000-000000000001")


def _basis():
 now=datetime.now(timezone.utc)
 return ProjectBasisItem(selector="1", version=1, standing="established", project_id=1, project_code="P-1", project_name="Project", project_status="active", foundation_established=True, provenance=FactProvenance(owner_kind="project",selector="1",version=1,standing="established",observed_at=now,authority_class=AuthorityClassification.HUMAN_AUTHORITATIVE,temporal_class=TemporalClassification.CURRENT))


def test_actual_composer_fixed_ten_owner_path_has_thirteen_calls_and_no_n_plus_one():
 owners=CountingOwners()
 response=ProjectContextService(owners).assemble_project_context(actor=_actor(), request=_request(*CANONICAL_SECTION_ORDER), current_user=User())
 assert response.status == "success"
 assert len(owners.calls) == 13
 assert owners.calls.count("project_basis") == 1
 assert owners.calls.count("project_control:risk") == 1
 assert owners.calls.count("project_control:change") == 1


def test_actual_composer_translates_all_five_source_states_and_partiality_without_count_leakage():
 available=ProjectContextService(CountingOwners(OwnerResolved(item=_basis()))).assemble_project_context(actor=_actor(), request=_request(ProjectContextSectionKind.PROJECT_BASIS), current_user=User())
 assert available.status == "success" and available.sections[0].state.state is SourceAvailability.AVAILABLE and available.observation_status is ContextObservationStatus.COMPLETE_WITHIN_BOUNDS
 for owner_result, expected in ((OwnerPage(items=(),last_evaluated_key=None,observed_at=datetime.now(timezone.utc)), SourceAvailability.EMPTY), (OwnerProtected(), SourceAvailability.NOT_DISCLOSED)):
  response=ProjectContextService(CountingOwners(owner_result)).assemble_project_context(actor=_actor(), request=_request(ProjectContextSectionKind.DELIVERABLES), current_user=User())
  assert response.status == "success" and response.sections[0].state.state is expected
  if expected is not SourceAvailability.EMPTY:
   assert response.observation_status is ContextObservationStatus.PARTIAL
   assert "visible_count" not in response.sections[0].state.model_dump()
 not_established=ProjectContextService(CountingOwners()).assemble_project_context(actor=_actor(), request=_request(ProjectContextSectionKind.PROJECT_BASIS), current_user=User())
 assert not_established.sections[0].state.state is SourceAvailability.NOT_ESTABLISHED
 unavailable=ProjectContextService(CountingOwners(OwnerUnavailable())).assemble_project_context(actor=_actor(), request=_request(ProjectContextSectionKind.DELIVERABLES), current_user=User())
 assert isinstance(unavailable, ProjectContextUnavailable)


def test_partial_unavailable_and_truncation_are_safe_and_continued_from_last_evaluated_key():
 class MixedOwners(CountingOwners):
  def project_basis(self, **kwargs): self.calls.append("project_basis"); return OwnerResolved(item=_basis())
  def deliverables(self, **kwargs): self.calls.append("deliverables"); return OwnerUnavailable()
 context=ProjectContextService(MixedOwners()).assemble_project_context(actor=_actor(),request=_request(ProjectContextSectionKind.PROJECT_BASIS,ProjectContextSectionKind.DELIVERABLES),current_user=User())
 assert context.status == "success" and context.observation_status is ContextObservationStatus.PARTIAL
 class TruncatedOwners(CountingOwners):
  def project_basis(self, **kwargs): return OwnerPage(items=(_basis(),),has_more=True,last_evaluated_key="project:1",observed_at=datetime.now(timezone.utc))
 truncated=ProjectContextService(TruncatedOwners()).assemble_project_context(actor=_actor(),request=_request(ProjectContextSectionKind.PROJECT_BASIS),current_user=User())
 state=truncated.sections[0].state
 assert state.truncated.truncated and state.truncated.continuation.last_evaluated_key == "project:1" and state.visible_count == 1


def test_continuation_is_canonical_bound_expiring_and_checked_before_owner_probe():
 now=datetime(2030,1,1,tzinfo=timezone.utc)
 owners=CountingOwners()
 service=ProjectContextService(owners, clock=lambda: now)
 request=_request(ProjectContextSectionKind.DELIVERABLES)
 page=request.sections[0]
 token=service.issue_continuation(actor=_actor(),request=request,section=page,last_evaluated_key="deliverable:1")
 assert len(token) <= 4096
 resumed=service.assemble_project_context(actor=_actor(),request=_request(ProjectContextSectionKind.DELIVERABLES, continuation=token),current_user=User())
 assert resumed.status == "success"
 before=len(owners.calls)
 malformed_requests = [_request(ProjectContextSectionKind.DELIVERABLES, continuation=token[:-1] + ("A" if token[-1] != "A" else "B")), _request(ProjectContextSectionKind.DELIVERABLES, continuation="not-a-token")]
 oversized = ProjectContextRequest.model_construct(scope=ProjectContextScope(project_id=1, workspace_id=2), sections=(ProjectContextSectionRequest.model_construct(kind=ProjectContextSectionKind.DELIVERABLES, page_size=100, continuation="a" * 4097),))
 for malformed_request in (*malformed_requests, oversized):
  result=service.assemble_project_context(actor=_actor(),request=malformed_request,current_user=User())
  assert isinstance(result, ProjectContextInvalidRequest)
 assert len(owners.calls) == before
 expired=ProjectContextService(CountingOwners(),clock=lambda: now+timedelta(minutes=16)).assemble_project_context(actor=_actor(),request=_request(ProjectContextSectionKind.DELIVERABLES, continuation=token),current_user=User())
 assert isinstance(expired, ProjectContextInvalidRequest)
