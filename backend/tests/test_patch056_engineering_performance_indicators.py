from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4
import pytest
from app.services.engineering_performance import (
    INDICATOR_IDS, blocked_work_aging, completeness_trend,
    deliverable_review_cycle_time, evidence_availability,
    interface_commitment_fulfilment, milestone_predictability, MilestoneEvidence,
    required_input_readiness, rework_revision_trend,
    risk_issue_change_aging, technical_report_acceptance_flow,
)

def test_p056_ind_manifest_has_exact_ten_families():
    assert len(INDICATOR_IDS) == 10

def test_p056_ind_01_required_input_readiness_and_safe_suppression():
    assert required_input_readiness(["received"]*4).limitations == ("insufficient_safe_population",)
    r=required_input_readiness(["received"]*4+["missing"]); assert r.value["ratio"]==0.8
    hidden=required_input_readiness(["received"]*5+["protected"])
    assert hidden.state == "indeterminate" and hidden.denominator is None and hidden.value == {}

def test_p056_ind_02_blocked_work_aging():
    now=datetime(2026,9,19,tzinfo=timezone.utc); r=blocked_work_aging([now-timedelta(days=3)],now=now); assert r.value["oldest_days"]==3

def test_p056_ind_03_milestone_predictability():
    known = [MilestoneEvidence(date(2026, 9, 20), "achieved", datetime(2026, 9, 19, tzinfo=timezone.utc), None, f"milestone:{index}") for index in range(5)]
    r=milestone_predictability(known,today=date(2026,9,19))
    assert r.state == "complete" and r.value["ratio"] == 1
    historical = MilestoneEvidence(date(2026, 9, 20), "achieved", None, None, "milestone:historical")
    assert milestone_predictability([historical],today=date(2026,9,19)).state == "indeterminate"
    forecastless = MilestoneEvidence(date(2026, 9, 21), "not_ready", None, None, "milestone:future")
    assert milestone_predictability([forecastless],today=date(2026,9,19)).state == "indeterminate"
    assert milestone_predictability(known + [historical],today=date(2026,9,19)).state == "partial"

def test_p056_ind_04_deliverable_review_cycle_time():
    assert deliverable_review_cycle_time([2,4]).value["average_hours"]==3

def test_p056_ind_05_rework_revision_trend():
    cutoff = datetime(2026, 9, 19, tzinfo=timezone.utc)
    reasons = ["normal_revision", "change_driven_revision", "corrective_rework",
               "review_return_rework", "normal_revision"]
    rows = [SimpleNamespace(revision_id=uuid4(), creation_event_id=uuid4(),
                            created_at=cutoff - timedelta(days=1), revision_reason=reason)
            for reason in reasons]
    result = rework_revision_trend(rows, source_cutoff=cutoff,
                                   population_complete=True)
    assert result.state == "complete" and result.numerator == 2
    assert result.value["neutral_revisions"] == 3
    assert rework_revision_trend(rows, source_cutoff=cutoff,
                                 population_complete=False).denominator is None
    historical = SimpleNamespace(revision_id=uuid4(), creation_event_id=uuid4(),
                                 created_at=cutoff - timedelta(days=2), revision_reason=None)
    partial = rework_revision_trend([*rows, historical], source_cutoff=cutoff,
                                    population_complete=True)
    assert partial.state == "partial" and partial.denominator == 5
    assert rework_revision_trend([1, 2, 3], source_cutoff=cutoff,
                                 population_complete=True).state == "indeterminate"

def test_p056_ind_06_risk_issue_change_aging():
    now=datetime(2026,9,19,tzinfo=timezone.utc); assert risk_issue_change_aging([now-timedelta(days=2)],now=now).value["oldest_days"]==2

def test_p056_ind_07_interface_commitment_fulfilment():
    cutoff = datetime(2026, 9, 19, tzinfo=timezone.utc)
    fulfilled = {"state": "fulfilled_for_stated_use", "current_use": True, "due_at": None}
    assert interface_commitment_fulfilment([fulfilled]*5, source_cutoff=cutoff).value["ratio"] == 1
    assert interface_commitment_fulfilment([fulfilled]*5+[{"state": "protected", "current_use": True}], source_cutoff=cutoff).state == "indeterminate"

def test_p056_ind_08_completeness_trend():
    first = [{"rule_id": f"rule-{index}", "category": "project_basis", "classification": "missing"}
             for index in range(14)]
    second = [dict(item) for item in first]
    second[0]["classification"] = "present"
    cutoff = datetime(2026, 9, 19, tzinfo=timezone.utc)
    base = {"method_version": "project_completeness.v1", "catalog_digest": "a" * 64,
            "observation_version": 1, "assessment_status": "complete_within_bounds", "limitations": ()}
    rows = [dict(base, id=1, source_cutoff=cutoff - timedelta(days=1), source_digest="b" * 64,
                 classifications=first),
            dict(base, id=2, source_cutoff=cutoff, source_digest="c" * 64,
                 classifications=second)]
    result = completeness_trend(rows, source_cutoff=cutoff)
    assert result.state == "partial" and result.value["classification_transition"] == "changed"
    assert "ratio" not in result.value and "score" not in result.value
    assert completeness_trend([], source_cutoff=cutoff).limitations == ("no_completeness_history",)
    assert completeness_trend(rows[:1], source_cutoff=cutoff).limitations == ("insufficient_trend_history",)
    assert completeness_trend(rows + [dict(rows[1], source_digest="d" * 64,
                                         assessment_status="partial")], source_cutoff=cutoff).state == "indeterminate"
    assert completeness_trend([rows[0], dict(rows[1], method_version="project_completeness.v2")],
                              source_cutoff=cutoff).limitations == ("method_changed",)

def test_p056_ind_09_technical_report_acceptance_flow():
    cutoff = datetime(2026, 9, 19, tzinfo=timezone.utc)
    created = cutoff - timedelta(days=2)
    accepted = cutoff - timedelta(days=1)
    rows = [SimpleNamespace(report_id=uuid4(), lifecycle="accepted", created_at=created,
                            accepted_at=accepted, accepted_snapshot_digest="a" * 64,
                            accepted_aggregate_version=2, version=2)
            for _ in range(5)]
    result = technical_report_acceptance_flow(rows, source_cutoff=cutoff)
    assert result.state == "complete" and result.value["average_acceptance_hours"] == 24
    assert result.eligible_count == 5
    draft = SimpleNamespace(report_id=uuid4(), lifecycle="draft", created_at=created,
                            accepted_at=None, accepted_snapshot_digest=None,
                            accepted_aggregate_version=None, version=1)
    pending = technical_report_acceptance_flow(rows + [draft], source_cutoff=cutoff)
    assert pending.state == "partial" and "pending_cohort_suppressed" in pending.limitations
    assert pending.value["average_acceptance_hours"] == 24
    missing = technical_report_acceptance_flow(rows + [SimpleNamespace(**{
        **vars(rows[0]), "report_id": uuid4(), "accepted_at": None,
    })], source_cutoff=cutoff)
    assert missing.state == "indeterminate" and missing.eligible_count is None

def test_p056_ind_10_evidence_availability():
    cutoff = datetime.now(timezone.utc)
    known = [SimpleNamespace(evidence_id=uuid4(), state="available", source_cutoff=cutoff)
             for _ in range(5)]
    assert evidence_availability(known, source_cutoff=cutoff,
                                 population_complete=True).value["ratio"] == 1
    assert evidence_availability(known, source_cutoff=cutoff,
                                 population_complete=False).denominator is None
    unknown = SimpleNamespace(evidence_id=uuid4(), state="indeterminate", source_cutoff=cutoff)
    partial = evidence_availability([*known, unknown], source_cutoff=cutoff,
                                    population_complete=True)
    assert partial.state == "partial" and partial.denominator == 5
    # Engineering standing is not a canonical artifact-availability state.
    assert evidence_availability(["current"] * 5, source_cutoff=cutoff,
                                 population_complete=True).state == "indeterminate"
