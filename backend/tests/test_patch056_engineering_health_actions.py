from datetime import datetime,timedelta,timezone
from app.services.engineering_performance import IndicatorObservation
from app.services.engineering_performance_intelligence import HEALTH_FACTORS,action_key,compose_health,next_projection_status,project_actions

def obs(i,state="complete",value=None):
    return IndicatorObservation(i,state,5,None,None,value or {})

def test_p056_hlt_01_exact_five_factors(): assert HEALTH_FACTORS==("readiness","flow","coordination","quality_rework","evidence_acceptance")
def test_p056_hlt_02_no_observations_is_indeterminate(): assert all(x.state=="indeterminate" for x in compose_health({}))
def test_p056_hlt_03_partial_propagates_indeterminate(): assert compose_health({"required_input_readiness":obs("required_input_readiness","partial")})[0].state=="indeterminate"
def test_p056_hlt_04_not_applicable_is_explicit(): assert compose_health({}, rework_facts=(), rework_population_complete=True)[3].state=="not_applicable"
def test_p056_hlt_05_no_overall_numeric_score(): assert all(not hasattr(x,"score") for x in compose_health({}))

def test_flow_is_constrained_only_by_explicit_blocked_work():
    rows={
        "blocked_work_aging":obs("blocked_work_aging",value={"open_blocked":1,"oldest_days":2}),
        "milestone_predictability":obs("milestone_predictability",value={"ratio":1}),
        "deliverable_review_cycle_time":obs("deliverable_review_cycle_time",value={"open_cycles":0}),
    }
    assert compose_health(rows)[1].state=="constrained"
    rows["blocked_work_aging"]=obs("blocked_work_aging",value={"open_blocked":0})
    assert compose_health(rows)[1].state=="healthy"

def test_p056_act_01_action_key_is_stable_and_scope_bound():
    assert action_key("r","1","p:1","x")==action_key("r","1","p:1","x")
    assert action_key("r","1","p:1","x")!=action_key("r","1","p:2","x")
def test_p056_act_02_actions_are_evidence_linked_and_advisory():
    a=project_actions({"required_input_readiness":obs("required_input_readiness",value={"ratio":.8})},scope_key="p:1")[0]
    assert a.status=="active" and a.source_handles==("indicator:required_input_readiness",)
def test_p056_act_03_absence_lifecycle_is_deterministic():
    now=datetime(2026,9,19,tzinfo=timezone.utc)
    assert next_projection_status(active_trigger=False,absent_recalculations=1,last_seen_at=now,now=now)=="stale"
    assert next_projection_status(active_trigger=False,absent_recalculations=2,last_seen_at=now,now=now)=="stale"
    assert next_projection_status(active_trigger=False,absent_recalculations=0,last_seen_at=now-timedelta(hours=25),now=now)=="stale"
    assert next_projection_status(active_trigger=False,absent_recalculations=2,last_seen_at=now-timedelta(hours=25),now=now)=="resolved_by_source_state"
def test_p056_act_04_ai_is_not_part_of_rule_execution():
    import inspect,app.services.engineering_performance_intelligence as m
    source=inspect.getsource(m)
    assert "openai" not in source.lower() and "llm" not in source.lower()
