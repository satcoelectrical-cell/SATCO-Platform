"""PATCH-056 authenticated, read-only Engineering Performance transport."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.auth import AuthenticatedOrganizationContext, get_current_user_organization_context
from app.adapters.engineering_performance import EngineeringPerformanceProtectedNotFound, EngineeringPerformanceScope, EngineeringPerformanceSourceAdapter
from app.adapters.engineering_deliverable import SupportingFileApplicationAdapter
from app.services.engineering_performance import INDICATOR_IDS, IndicatorObservation, required_input_readiness, blocked_work_aging, milestone_predictability, deliverable_review_cycle_from_events, rework_revision_trend, risk_issue_change_aging_from_evidence, interface_commitment_fulfilment, completeness_trend, technical_report_acceptance_flow, evidence_availability
from app.services.engineering_performance_intelligence import compose_health, project_actions
from app.dependencies.project_foundation import get_project_foundation_application
from app.dependencies.supporting_file import get_supporting_file_application
from app.dependencies.project_context import get_project_context_application
from app.dependencies.project_completeness import get_project_completeness_application
from app.services.technical_report_service import TechnicalReportService
from app.repositories.technical_report_unit_of_work import SqlAlchemyTechnicalReportUnitOfWork
from app.repositories.engineering_object_unit_of_work import UtcClock
from app.core.database import SessionLocal
from app.repositories.evidence_unit_of_work import SqlAlchemyEvidenceAuthorizationPolicy, SqlAlchemyEvidenceUnitOfWork, UtcEvidenceClock
from app.services.evidence_availability_service import EvidenceAvailabilityService
from app.repositories.engineering_performance_repository import EngineeringPerformanceRepository
from app.services.engineering_performance_projection_service import EngineeringPerformanceProjectionService
from datetime import datetime, timezone
from datetime import timedelta
from dataclasses import replace
from fastapi.encoders import jsonable_encoder
from hashlib import sha256
import json
from uuid import UUID

router=APIRouter(prefix="/api/v1/projects/{project_id}/engineering-performance",tags=["Engineering Performance"])

def _scope(project_id:int, workspace_id:int|None, org:AuthenticatedOrganizationContext):
    return EngineeringPerformanceScope(org.organization_id,project_id,workspace_id,org.user.id)

def _adapter(db:Session, org:AuthenticatedOrganizationContext):
    foundation = get_project_foundation_application(db, org)
    file_app = get_supporting_file_application(db, org)
    supporting_files = SupportingFileApplicationAdapter(file_app)
    completeness = get_project_completeness_application(get_project_context_application(db, org), db)
    reports = TechnicalReportService(lambda: SqlAlchemyTechnicalReportUnitOfWork(SessionLocal), UtcClock())
    evidence = EvidenceAvailabilityService(
        uow_factory=lambda: SqlAlchemyEvidenceUnitOfWork(SessionLocal),
        authorization=SqlAlchemyEvidenceAuthorizationPolicy(db),
        availability_reader=file_app.service, clock=UtcEvidenceClock(),
    )
    return EngineeringPerformanceSourceAdapter(db, foundation_service=foundation.service, supporting_files=supporting_files, completeness_service=completeness.service, technical_report_service=reports, evidence_availability_service=evidence, current_user=org.user)

def _projection(db:Session):
    return EngineeringPerformanceProjectionService(EngineeringPerformanceRepository(db))

def _observations(adapter,scope,window_days=30):
    cutoff=datetime.now(timezone.utc)
    inputs=adapter.required_input_standings(scope)
    activities=adapter.execution_activity_rows(scope)
    milestones=adapter.milestone_rows(scope)
    transitions=adapter.deliverable_transition_rows(scope)
    controls=adapter.control_aging_rows(scope)
    commitments=adapter.interface_commitment_rows(scope)
    completeness=adapter.completeness_history(scope, window_days=window_days)
    reports=adapter.technical_report_rows(scope)
    rework_facts=(adapter.deliverable_rework_rows(scope,source_cutoff=cutoff)
                  if hasattr(adapter,"deliverable_rework_rows") else None)
    evidence_snapshot=(adapter.issue_evidence_availability_snapshot(scope)
                       if hasattr(adapter,"issue_evidence_availability_snapshot") else None)
    if transitions is None:
        review=IndicatorObservation("deliverable_review_cycle_time","indeterminate",None,None,None,{},("canonical_deliverable_transition_evidence_unavailable",))
    else:
        review=deliverable_review_cycle_from_events(transitions)
    rework=(rework_revision_trend(rework_facts,source_cutoff=cutoff,population_complete=True)
            if rework_facts is not None else
            IndicatorObservation("rework_revision_trend","indeterminate",None,None,None,{},("canonical_deliverable_rework_evidence_unavailable",)))
    calculated = {
      "required_input_readiness":required_input_readiness(inputs),
      "blocked_work_aging":blocked_work_aging([r.blocked_since for r in activities if r.standing=="blocked"]),
      "milestone_predictability":milestone_predictability(milestones),
      "deliverable_review_cycle_time":review,
      "rework_revision_trend":rework,
      "risk_issue_change_aging":(
          risk_issue_change_aging_from_evidence(controls.items,source_cutoff=controls.source_cutoff)
          if controls is not None else
          IndicatorObservation("risk_issue_change_aging","indeterminate",None,None,None,{},("canonical_project_control_traversal_incomplete",))
      ),
      "interface_commitment_fulfilment":(
          interface_commitment_fulfilment(commitments["items"], source_cutoff=commitments["source_cutoff"])
          if commitments is not None else
          IndicatorObservation("interface_commitment_fulfilment", "indeterminate", None, None, None, {},
                               ("canonical_interface_due_evidence_unavailable",))
      ),
      "completeness_trend":(
          completeness_trend(completeness["observations"], source_cutoff=completeness["source_cutoff"])
          if completeness is not None else
          IndicatorObservation("completeness_trend", "indeterminate", None, None, None, {},
                               ("canonical_completeness_history_unavailable",))
      ),
      "technical_report_acceptance_flow":(
          technical_report_acceptance_flow(reports.items, source_cutoff=reports.source_cutoff, window_days=window_days)
          if reports is not None else
          IndicatorObservation("technical_report_acceptance_flow", "indeterminate", None, None, None, {},
                               ("canonical_technical_report_lifecycle_unavailable",))
      ),
      "evidence_availability":(
          evidence_availability(
              evidence_snapshot.items, source_cutoff=evidence_snapshot.source_cutoff,
              population_complete=evidence_snapshot.status == "complete",
          ) if evidence_snapshot is not None else
          IndicatorObservation("evidence_availability","indeterminate",None,None,None,{},
                               ("canonical_evidence_availability_traversal_incomplete",))
      ),
    }
    sources = {
        "required_input_readiness": (inputs, (f"project_foundation:{scope.project_id}",)),
        "blocked_work_aging": (activities, tuple(f"execution_activity:{r.id}" for r in activities)),
        "milestone_predictability": (milestones, tuple(r.source_handle for r in milestones)),
        "deliverable_review_cycle_time": (transitions, tuple(f"deliverable_revision:{r.revision_id}" for r in transitions or ())),
        "rework_revision_trend": (rework_facts, tuple(f"deliverable_revision:{r.revision_id}" for r in rework_facts or ())),
        "risk_issue_change_aging": (controls, tuple(f"project_control:{r.kind}:{r.id}" for r in controls.items) if controls else ()),
        "interface_commitment_fulfilment": (commitments, tuple(f"interface_commitment:{r['id']}" for r in commitments["items"]) if commitments else ()),
        "completeness_trend": (completeness, tuple(f"project_completeness:{scope.project_id}" for _ in completeness["observations"]) if completeness else ()),
        "technical_report_acceptance_flow": (reports, tuple(f"technical_report:{r.report_id}" for r in reports.items) if reports else ()),
        "evidence_availability": (
            evidence_snapshot,
            ((f"evidence_availability_snapshot:{evidence_snapshot.snapshot_id}",)
             + tuple(f"evidence:{r.evidence_id}" for r in evidence_snapshot.items))
            if evidence_snapshot is not None and evidence_snapshot.status == "complete" else (),
        ),
    }
    observed_at = datetime.now(timezone.utc)
    window_start = observed_at - timedelta(days=window_days)
    units = {
        "required_input_readiness": "ratio", "blocked_work_aging": "days",
        "milestone_predictability": "ratio", "deliverable_review_cycle_time": "hours",
        "rework_revision_trend": "ratio", "risk_issue_change_aging": "days",
        "interface_commitment_fulfilment": "ratio",
        "completeness_trend": "classification_transition",
        "technical_report_acceptance_flow": "hours", "evidence_availability": "ratio",
    }
    decorated = {}
    for indicator_id, observation in calculated.items():
        source, handles = sources[indicator_id]
        canonical_payload = json.dumps(jsonable_encoder(source), sort_keys=True, separators=(",", ":"), default=str)
        digest = sha256(canonical_payload.encode()).hexdigest()
        owner_cutoff = (source.get("source_cutoff") if isinstance(source, dict)
                        else getattr(source, "source_cutoff", None))
        decorated[indicator_id] = replace(
            observation, organization_id=str(scope.organization_id), project_id=scope.project_id,
            workspace_id=scope.workspace_id, observed_at=observed_at,
            window_start=window_start, window_end=observed_at,
            source_cutoff=owner_cutoff or (cutoff if indicator_id == "rework_revision_trend" else observed_at),
            source_digest=digest,
            source_handles=tuple(sorted(set(handles))) if observation.state in {"complete", "partial"} else (),
            unit=units[indicator_id],
        )
    return decorated

def _authorized_observations(adapter,scope,window_days=30):
    try:
        return _observations(adapter,scope,window_days)
    except EngineeringPerformanceProtectedNotFound:
        raise HTTPException(404,"not_found") from None

def _authorize_scope(adapter,scope):
    try:
        adapter.authorize_scope(scope)
    except EngineeringPerformanceProtectedNotFound:
        raise HTTPException(404,"not_found") from None

@router.get("/catalog")
def catalog(project_id:int, workspace_id:int|None=None, org:AuthenticatedOrganizationContext=Depends(get_current_user_organization_context), db:Session=Depends(get_db)):
    _authorize_scope(_adapter(db,org),_scope(project_id,workspace_id,org))
    return {"derived":True,"advisory":True,"authoritative":False,"indicator_ids":INDICATOR_IDS}

@router.get("/indicators")
def indicators(project_id:int, workspace_id:int|None=None, window_days:int=Query(30), org:AuthenticatedOrganizationContext=Depends(get_current_user_organization_context), db:Session=Depends(get_db)):
    if window_days not in {7,30,90,180}: raise HTTPException(422,"unsupported_window")
    scope=_scope(project_id,workspace_id,org)
    rows=_authorized_observations(_adapter(db,org),scope,window_days)
    try: _projection(db).persist_observations(scope=scope,observations=rows)
    except Exception: raise HTTPException(503,"derived_persistence_unavailable") from None
    return {"derived":True,"advisory":True,"authoritative":False,"window_days":window_days,"observations":[vars(v) for v in rows.values()]}

@router.get("/health")
def health(project_id:int, workspace_id:int|None=None, org:AuthenticatedOrganizationContext=Depends(get_current_user_organization_context), db:Session=Depends(get_db)):
    adapter=_adapter(db,org); scope=_scope(project_id,workspace_id,org)
    rows=_authorized_observations(adapter,scope)
    try: _projection(db).persist_observations(scope=scope,observations=rows)
    except Exception: raise HTTPException(503,"derived_persistence_unavailable") from None
    try: rework_facts=adapter.deliverable_rework_rows(scope,source_cutoff=datetime.now(timezone.utc))
    except EngineeringPerformanceProtectedNotFound: raise HTTPException(404,"not_found") from None
    return {"derived":True,"advisory":True,"authoritative":False,"factors":[vars(v) for v in compose_health(rows,rework_facts=rework_facts,rework_population_complete=rework_facts is not None)]}

@router.get("/next-actions")
def next_actions(project_id:int, workspace_id:int|None=None, org:AuthenticatedOrganizationContext=Depends(get_current_user_organization_context), db:Session=Depends(get_db)):
    scope=_scope(project_id,workspace_id,org)
    rows=_authorized_observations(_adapter(db,org),scope)
    actions=project_actions(rows,scope_key=f"project:{project_id}:workspace:{workspace_id or 'all'}")
    projection=_projection(db)
    try:
        projection.persist_observations(scope=scope,observations=rows)
        persisted=projection.reconcile_actions(scope=scope,projected=actions,observations=rows)
    except Exception: raise HTTPException(503,"derived_persistence_unavailable") from None
    return {"derived":True,"advisory":True,"authoritative":False,"actions":[projection.action_view(v) for v in persisted]}

@router.get("/trends")
def trends(project_id:int, workspace_id:int|None=None, window_days:int=Query(30),
           indicator_id:str|None=None, cadence:str=Query("daily",pattern="^(daily|weekly)$"),
           org:AuthenticatedOrganizationContext=Depends(get_current_user_organization_context), db:Session=Depends(get_db)):
    if window_days not in {7,30,90,180}: raise HTTPException(422,"unsupported_window")
    adapter=_adapter(db,org);scope=_scope(project_id,workspace_id,org);_authorize_scope(adapter,scope)
    if indicator_id is not None and indicator_id not in INDICATOR_IDS: raise HTTPException(422,"unsupported_indicator")
    try: points,limitations=_projection(db).trends(scope=scope,window_days=window_days,indicator_id=indicator_id,cadence=cadence)
    except Exception: raise HTTPException(503,"derived_persistence_unavailable") from None
    return {"derived":True,"advisory":True,"authoritative":False,"window_days":window_days,"cadence":cadence,"points":points,"limitations":limitations}

@router.get("/drill-down")
def drill_down(project_id:int, indicator_id:str, workspace_id:int|None=None,
               limit:int=Query(20,ge=1,le=100), offset:int=Query(0,ge=0),
               snapshot_id:UUID|None=None,
               org:AuthenticatedOrganizationContext=Depends(get_current_user_organization_context),
               db:Session=Depends(get_db)):
    adapter=_adapter(db,org); scope=_scope(project_id,workspace_id,org)
    _authorize_scope(adapter,scope)
    if indicator_id not in INDICATOR_IDS: raise HTTPException(422,"unsupported_indicator")
    observation=_authorized_observations(adapter,scope)[indicator_id]
    handles=observation.source_handles
    if snapshot_id is not None:
        try: handles=_projection(db).historical_handles(scope=scope,snapshot_id=snapshot_id,indicator_id=indicator_id,currently_authorized=handles)
        except Exception: raise HTTPException(503,"derived_persistence_unavailable") from None
        if handles is None: raise HTTPException(404,"not_found")
    selected=handles[offset:offset+limit]
    return {"derived":True,"advisory":True,"authoritative":False,
            "indicator_id":indicator_id,"state":observation.state,
            "source_cutoff":observation.source_cutoff,"source_digest":observation.source_digest,
            "limit":limit,"offset":offset,
            "items":[{"source_handle":handle} for handle in selected],
            "next_offset":offset+len(selected) if offset+len(selected)<len(handles) else None,
            "limitations":list(observation.limitations)}
