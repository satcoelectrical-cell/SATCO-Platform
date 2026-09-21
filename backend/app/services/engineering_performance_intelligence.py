"""PATCH-056 transparent Health composition and deterministic advisory actions."""

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from app.services.engineering_performance import IndicatorObservation

HEALTH_FACTORS=("readiness","flow","coordination","quality_rework","evidence_acceptance")
HEALTH_STATES={"healthy","attention","constrained","indeterminate","not_applicable"}
ACTION_STATUSES={"active","stale","superseded","resolved_by_source_state"}
HEALTH_RULE_VERSION="health-model.v1"

@dataclass(frozen=True)
class HealthFactor:
    factor: str
    state: str
    indicator_ids: tuple[str,...]
    limitations: tuple[str,...]=()
    rule_id: str=""
    rule_version: str=HEALTH_RULE_VERSION
    rationale_codes: tuple[str,...]=()
    source_handles: tuple[str,...]=()

def _quality_rework_state(facts: tuple[object, ...], *, population_complete: bool) -> tuple[str, tuple[str, ...]]:
    if not population_complete:
        return "indeterminate", ("authorized_rework_population_incomplete",)
    if not facts:
        return "not_applicable", ()
    seen, unresolved, unknown, blocked = set(), 0, 0, 0
    for fact in facts:
        revision_id = getattr(fact, "revision_id", None)
        reason = getattr(getattr(fact, "revision_reason", None), "value", getattr(fact, "revision_reason", None))
        resolution = getattr(fact, "resolution_state", None)
        block_ref = getattr(fact, "blocking_event_id", None)
        if revision_id is None or revision_id in seen:
            return "indeterminate", ("invalid_canonical_rework_fact",)
        seen.add(revision_id)
        if reason is None and resolution == "unknown":
            unknown += 1
        elif reason in {"normal_revision", "change_driven_revision"} and resolution == "not_applicable":
            if block_ref is not None:
                return "indeterminate", ("invalid_canonical_rework_fact",)
        elif reason in {"corrective_rework", "review_return_rework"} and resolution in {"unresolved", "resolved"}:
            if resolution == "unresolved":
                unresolved += 1
                blocked += block_ref is not None
            elif block_ref is not None:
                return "indeterminate", ("invalid_canonical_rework_fact",)
        else:
            return "indeterminate", ("invalid_canonical_rework_fact",)
    if blocked:
        return "constrained", ()
    if unknown:
        return "indeterminate", ("historical_revision_reason_unknown",)
    if unresolved:
        return "attention", ("unresolved_consequential_rework",)
    return "healthy", ()


def compose_health(observations: dict[str,IndicatorObservation], *,
                   rework_facts: tuple[object, ...] | None = None,
                   rework_population_complete: bool = False) -> tuple[HealthFactor,...]:
    mapping={
      "readiness":("required_input_readiness","completeness_trend"),
      "flow":("blocked_work_aging","milestone_predictability","deliverable_review_cycle_time"),
      "coordination":("risk_issue_change_aging","interface_commitment_fulfilment"),
      "quality_rework":("rework_revision_trend",),
      "evidence_acceptance":("technical_report_acceptance_flow","evidence_availability"),
    }
    result=[]
    for factor, ids in mapping.items():
        if factor == "quality_rework":
            if rework_facts is None:
                state, limitations = "indeterminate", ("canonical_rework_state_unavailable",)
            else:
                state, limitations = _quality_rework_state(
                    tuple(rework_facts), population_complete=rework_population_complete,
                )
            handles = tuple(f"deliverable_revision:{fact.revision_id}" for fact in (rework_facts or ())
                            if getattr(fact,"revision_id",None) is not None)
            result.append(HealthFactor(factor, state, ids, limitations,
                                       f"health.{factor}.v1", HEALTH_RULE_VERSION,
                                       ("explicit_rework_state",) if state in {"attention","constrained"} else
                                       ("no_unresolved_consequential_rework",) if state == "healthy" else (),
                                       handles[:100]))
            continue
        rows=[observations[i] for i in ids if i in observations]
        if len(rows) != len(ids):
            state, limitations, rationale = "indeterminate", ("required_indicator_missing",), ()
        elif all(r.state=="not_applicable" for r in rows):
            state, limitations, rationale = "not_applicable", (), ("canonical_scope_not_applicable",)
        elif any(r.state in {"partial","indeterminate"} for r in rows):
            state, limitations, rationale = "indeterminate", tuple(sorted({
                code for row in rows for code in row.limitations
            })) or ("source_insufficient",), ()
        else:
            constrained = (
                factor == "flow" and any(
                    row.indicator_id == "blocked_work_aging"
                    and row.value.get("open_blocked", 0) > 0 for row in rows
                )
            )
            attention = (
                factor == "readiness" and any(
                    row.indicator_id == "required_input_readiness" and
                    row.value.get("ratio",1) < 1 for row in rows
                ) or
                factor == "flow" and any(
                    row.value.get("open_blocked",0) > 0 or
                    row.value.get("open_cycles",0) > 0 or
                    (row.indicator_id == "milestone_predictability" and
                     row.value.get("ratio",1) < 1) for row in rows
                ) or
                factor == "coordination" and any(
                    bool(row.value.get("by_kind")) or
                    row.value.get("open_overdue",0) > 0 or
                    (row.indicator_id == "interface_commitment_fulfilment" and
                     row.value.get("ratio",1) < 1) for row in rows
                ) or
                factor == "evidence_acceptance" and any(
                    row.value.get("pending_cycles",0) > 0 or
                    (row.indicator_id == "evidence_availability" and
                     row.value.get("ratio",1) < 1) for row in rows
                )
            )
            state = "constrained" if constrained else "attention" if attention else "healthy"
            limitations = ()
            rationale = (("explicit_canonical_blocking_condition",) if constrained else
                         ("visible_unresolved_condition",) if attention else
                         ("no_visible_attention_condition",))
        result.append(HealthFactor(factor,state,ids,limitations,
                                   f"health.{factor}.v1",HEALTH_RULE_VERSION,rationale))
    return tuple(result)

@dataclass(frozen=True)
class AdvisoryAction:
    action_key:str; rule_id:str; rule_version:str; title_code:str
    rationale_codes:tuple[str,...]; source_handles:tuple[str,...]
    limitations:tuple[str,...]; status:str="active"

def action_key(rule_id:str, rule_version:str, scope_key:str, subject_key:str)->str:
    return sha256(f"{rule_id}|{rule_version}|{scope_key}|{subject_key}".encode()).hexdigest()

def project_actions(observations:dict[str,IndicatorObservation], *, scope_key:str)->tuple[AdvisoryAction,...]:
    actions=[]
    readiness=observations.get("required_input_readiness")
    if readiness and readiness.state=="complete" and readiness.value.get("ratio",1)<1:
        actions.append(AdvisoryAction(action_key("required-input-gap","1",scope_key,"required-inputs"),"required-input-gap","1","review_required_inputs",("required_inputs_incomplete",),("indicator:required_input_readiness",*readiness.source_handles),()))
    blocked=observations.get("blocked_work_aging")
    if blocked and blocked.state=="complete" and blocked.value.get("open_blocked",0)>0:
        actions.append(AdvisoryAction(action_key("blocked-work","1",scope_key,"execution"),"blocked-work","1","review_blocked_work",("blocked_work_present",),("indicator:blocked_work_aging",*blocked.source_handles),()))
    return tuple(actions)

def next_projection_status(*, active_trigger:bool, absent_recalculations:int, last_seen_at:datetime, now:datetime|None=None)->str:
    if active_trigger:return "active"
    now=now or datetime.now(timezone.utc)
    if absent_recalculations>=2 and (now-last_seen_at).total_seconds()>86400:return "resolved_by_source_state"
    return "stale"
