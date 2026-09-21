"""PATCH-056 deterministic, non-authoritative Engineering Performance calculations."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Iterable

MIN_SAFE_POPULATION = 5
INDICATOR_IDS = (
    "required_input_readiness", "blocked_work_aging", "milestone_predictability",
    "deliverable_review_cycle_time", "rework_revision_trend",
    "risk_issue_change_aging", "interface_commitment_fulfilment",
    "completeness_trend", "technical_report_acceptance_flow",
    "evidence_availability",
)


@dataclass(frozen=True)
class IndicatorObservation:
    indicator_id: str
    state: str
    eligible_count: int | None
    numerator: int | None
    denominator: int | None
    value: dict
    limitations: tuple[str, ...] = ()
    indicator_version: str = "1"
    calculation_method_version: str = "calculator.v1"
    unit: str | None = None
    source_cutoff: datetime | None = None
    source_digest: str | None = None
    source_handles: tuple[str, ...] = ()
    organization_id: str | None = None
    project_id: int | None = None
    workspace_id: int | None = None
    observed_at: datetime | None = None
    window_start: datetime | None = None
    window_end: datetime | None = None
    calculation_method: str = "canonical_owner_facts"


@dataclass(frozen=True)
class MilestoneEvidence:
    target_date: date | None
    standing: str
    actual_completed_at: datetime | None
    forecast_completion_at: datetime | None
    source_handle: str
    limitations: tuple[str, ...] = ()


def safe_ratio(indicator_id: str, numerator: int, denominator: int) -> IndicatorObservation:
    if denominator == 0:
        return IndicatorObservation(indicator_id, "not_applicable", 0, None, None, {}, ("no_eligible_population",))
    if denominator < MIN_SAFE_POPULATION:
        return IndicatorObservation(indicator_id, "indeterminate", None, None, None, {}, ("insufficient_safe_population",))
    return IndicatorObservation(indicator_id, "complete", denominator, numerator, denominator, {"ratio": numerator / denominator})


def _standing_ratio(indicator_id: str, standings: Iterable[str], *, successes: frozenset[str],
                    failures: frozenset[str], exclusions: frozenset[str]) -> IndicatorObservation:
    rows = tuple(standings)
    known = successes | failures | exclusions
    if any(value not in known for value in rows):
        # Unknown/protected input might alter the conclusion; do not reveal its count.
        return IndicatorObservation(indicator_id, "indeterminate", None, None, None, {}, ("source_visibility_or_validity_unknown",))
    eligible = tuple(value for value in rows if value not in exclusions)
    return safe_ratio(indicator_id, sum(value in successes for value in eligible), len(eligible))


def required_input_readiness(standings: Iterable[str]) -> IndicatorObservation:
    return _standing_ratio(
        "required_input_readiness", standings,
        successes=frozenset({"received"}),
        failures=frozenset({"missing", "clarification_required"}),
        exclusions=frozenset({"not_applicable"}),
    )


def blocked_work_aging(blocked_since: Iterable[datetime | None], *, now: datetime | None = None) -> IndicatorObservation:
    now = now or datetime.now(timezone.utc)
    rows = list(blocked_since)
    if not rows:
        return IndicatorObservation("blocked_work_aging", "not_applicable", 0, None, None, {}, ("no_blocked_work",))
    if any(value is None or value.tzinfo is None or value > now for value in rows):
        return IndicatorObservation("blocked_work_aging", "indeterminate", None, None, None, {}, ("blocked_transition_time_unavailable",))
    ages = [max(0.0, (now - value).total_seconds() / 86400) for value in rows]
    return IndicatorObservation("blocked_work_aging", "complete", len(rows), None, None, {"open_blocked": len(rows), "oldest_days": max(ages)})


def milestone_predictability(evidence: Iterable[MilestoneEvidence], *, today: date | None = None) -> IndicatorObservation:
    """Only owner-attested completion/forecast evidence can establish timing."""
    today = today or date.today()
    rows = list(evidence)
    if not rows:
        return IndicatorObservation("milestone_predictability", "not_applicable", 0, None, None, {}, ("no_milestones",))
    eligible = []
    unknown = 0
    for row in rows:
        if row.target_date is None:
            unknown += 1
            continue
        if row.standing == "achieved":
            if row.actual_completed_at is None:
                unknown += 1
                continue
            eligible.append(row.actual_completed_at.date() <= row.target_date)
        elif row.forecast_completion_at is not None:
            eligible.append(row.forecast_completion_at.date() <= row.target_date)
        elif row.target_date < today:
            # A past target with current owner-attested non-achievement is known overdue.
            eligible.append(False)
        else:
            unknown += 1
    if not eligible:
        return IndicatorObservation("milestone_predictability", "indeterminate", None, None, None, {}, ("canonical_timing_evidence_unavailable",))
    result = safe_ratio("milestone_predictability", sum(eligible), len(eligible))
    if unknown and result.state == "complete":
        return IndicatorObservation("milestone_predictability", "partial", result.eligible_count, result.numerator, result.denominator, result.value, ("excluded_unknown_timing",))
    return result


def deliverable_review_cycle_time(hours: Iterable[float]) -> IndicatorObservation:
    try:
        values = [float(v) for v in hours]
    except (TypeError, ValueError, OverflowError):
        return IndicatorObservation("deliverable_review_cycle_time", "indeterminate", None, None, None, {}, ("invalid_cycle_time",))
    if any(not 0 <= value < float("inf") for value in values):
        return IndicatorObservation("deliverable_review_cycle_time", "indeterminate", None, None, None, {}, ("invalid_cycle_time",))
    if not values:
        return IndicatorObservation("deliverable_review_cycle_time", "not_applicable", 0, None, None, {}, ("no_closed_review_cycles",))
    return IndicatorObservation("deliverable_review_cycle_time", "complete", len(values), None, None, {"average_hours": sum(values) / len(values)})


def deliverable_review_cycle_from_events(events: Iterable[object]) -> IndicatorObservation:
    """Pair only owner-attested ready-for-review and reviewed transitions."""
    rows = tuple(events)
    if not rows:
        return IndicatorObservation("deliverable_review_cycle_time", "not_applicable", 0, None, None, {}, ("no_deliverable_transition_evidence",))
    review_events = {"revision_transitioned", "package_revision_transitioned"}
    by_revision: dict[object, list[object]] = {}
    unknown = 0
    for row in rows:
        if row.source_event_type not in review_events:
            continue
        target = row.target_standing
        if hasattr(target, "value"):
            target = target.value
        if target is None:
            unknown += 1
            continue
        if target in {"ready_for_review", "reviewed"}:
            by_revision.setdefault(row.revision_id, []).append(row)
    hours = []
    open_cycles = 0
    for revision_rows in by_revision.values():
        openings = [row for row in revision_rows if (row.target_standing.value if hasattr(row.target_standing, "value") else row.target_standing) == "ready_for_review"]
        closings = [row for row in revision_rows if (row.target_standing.value if hasattr(row.target_standing, "value") else row.target_standing) == "reviewed"]
        if len(openings) == 1 and not closings:
            instant = openings[0].occurred_at
            if instant is None or instant.tzinfo is None:
                unknown += 1
            else:
                open_cycles += 1
            continue
        if len(openings) != 1 or len(closings) != 1:
            unknown += 1
            continue
        opening, closing = openings[0].occurred_at, closings[0].occurred_at
        if (opening is None or closing is None or opening.tzinfo is None
                or closing.tzinfo is None or closing < opening):
            unknown += 1
            continue
        hours.append((closing - opening).total_seconds() / 3600)
    limitations = tuple(code for code, present in (
        ("historical_or_ambiguous_review_boundary", unknown > 0),
        ("review_open_without_close", open_cycles > 0),
    ) if present)
    if not hours:
        state = "indeterminate" if limitations else "not_applicable"
        return IndicatorObservation("deliverable_review_cycle_time", state, None if limitations else 0,
                                    None, None, {}, limitations or ("no_closed_review_cycles",))
    return IndicatorObservation(
        "deliverable_review_cycle_time", "partial" if limitations else "complete",
        len(hours), None, None,
        {"average_hours": sum(hours) / len(hours), "open_cycles": open_cycles,
         "excluded_unknown_events": unknown}, limitations,
    )


def rework_revision_trend(evidence: Iterable[object], *, source_cutoff: datetime,
                          population_complete: bool) -> IndicatorObservation:
    """Only Human-typed Deliverable creation events can classify revisions."""
    indicator = "rework_revision_trend"
    if not population_complete:
        return IndicatorObservation(indicator, "indeterminate", None, None, None, {},
                                    ("authorized_rework_population_incomplete",))
    if (not isinstance(source_cutoff, datetime) or source_cutoff.tzinfo is None
            or source_cutoff.utcoffset() is None):
        return IndicatorObservation(indicator, "indeterminate", None, None, None, {},
                                    ("invalid_source_cutoff",))
    rows = tuple(evidence)
    if not rows:
        return IndicatorObservation(indicator, "not_applicable", 0, None, None, {},
                                    ("no_authorized_deliverable_revisions",))
    seen, neutral, rework, unknown = set(), 0, 0, 0
    for row in rows:
        revision_id = getattr(row, "revision_id", None)
        reason = getattr(row, "revision_reason", None)
        reason = getattr(reason, "value", reason)
        created = getattr(row, "created_at", None)
        if (revision_id is None or revision_id in seen or not isinstance(created, datetime)
                or created.tzinfo is None or created.utcoffset() is None
                or created > source_cutoff or getattr(row, "creation_event_id", None) is None):
            return IndicatorObservation(indicator, "indeterminate", None, None, None, {},
                                        ("invalid_canonical_revision_event",))
        seen.add(revision_id)
        if reason in {"normal_revision", "change_driven_revision"}:
            neutral += 1
        elif reason in {"corrective_rework", "review_return_rework"}:
            rework += 1
        elif reason is None:
            unknown += 1
        else:
            return IndicatorObservation(indicator, "indeterminate", None, None, None, {},
                                        ("invalid_canonical_revision_reason",))
    classified = neutral + rework
    if classified < MIN_SAFE_POPULATION:
        return IndicatorObservation(indicator, "indeterminate", None, None, None, {},
                                    ("insufficient_safe_classified_population",))
    return IndicatorObservation(indicator, "partial" if unknown else "complete",
                                classified, rework, classified,
                                {"neutral_revisions": neutral,
                                 "consequential_rework_revisions": rework,
                                 "rework_ratio": rework / classified},
                                ("historical_revision_reason_unknown",) if unknown else ())


def risk_issue_change_aging(opened_at: Iterable[datetime], *, now: datetime | None = None) -> IndicatorObservation:
    now = now or datetime.now(timezone.utc); values = list(opened_at)
    if not values:
        return IndicatorObservation("risk_issue_change_aging", "not_applicable", 0, None, None, {}, ("no_open_control_items",))
    ages = [max(0.0, (now-v).total_seconds()/86400) for v in values]
    return IndicatorObservation("risk_issue_change_aging", "complete", len(values), None, None, {"oldest_days": max(ages), "average_days": sum(ages)/len(ages)})


def risk_issue_change_aging_from_evidence(evidence: Iterable[object], *, source_cutoff: datetime) -> IndicatorObservation:
    """Current unresolved record age; never a fabricated closed-cycle duration."""
    if source_cutoff.tzinfo is None:
        return IndicatorObservation("risk_issue_change_aging", "indeterminate", None, None, None, {}, ("invalid_source_cutoff",))
    rows = tuple(evidence)
    if not rows:
        return IndicatorObservation("risk_issue_change_aging", "not_applicable", 0, None, None, {}, ("no_control_records",))
    unresolved = {
        "risk": frozenset({"open", "treated", "accepted"}),
        "issue": frozenset({"open"}),
        "change": frozenset({"recorded"}),
    }
    resolved = {
        "risk": frozenset({"closed"}),
        "issue": frozenset({"resolved", "closed"}),
        "change": frozenset({"confirmed", "withdrawn"}),
    }
    ages: dict[str, list[float]] = {kind: [] for kind in unresolved}
    excluded_closed = 0
    for row in rows:
        if (row.kind not in unresolved or row.created_at is None
                or row.created_at.tzinfo is None or row.created_at > source_cutoff):
            return IndicatorObservation("risk_issue_change_aging", "indeterminate", None, None, None, {}, ("invalid_canonical_control_evidence",))
        if row.standing in unresolved[row.kind]:
            ages[row.kind].append((source_cutoff - row.created_at).total_seconds() / 86400)
        elif row.standing in resolved[row.kind]:
            excluded_closed += 1
        else:
            return IndicatorObservation("risk_issue_change_aging", "indeterminate", None, None, None, {}, ("unknown_control_standing",))
    if any(0 < len(values) < MIN_SAFE_POPULATION for values in ages.values()):
        return IndicatorObservation("risk_issue_change_aging", "indeterminate", None, None, None, {}, ("insufficient_safe_population",))
    by_kind = {
        kind: {"open_count": len(values), "oldest_days": max(values),
               "average_days": sum(values) / len(values)}
        for kind, values in ages.items() if values
    }
    if not by_kind:
        return IndicatorObservation("risk_issue_change_aging", "indeterminate" if excluded_closed else "not_applicable", None if excluded_closed else 0, None, None, {}, ("closed_cycle_time_unavailable",) if excluded_closed else ("no_open_control_items",))
    value = {"by_kind": by_kind}
    if excluded_closed:
        value["excluded_closed_count"] = excluded_closed
    return IndicatorObservation(
        "risk_issue_change_aging", "partial" if excluded_closed else "complete",
        sum(len(values) for values in ages.values()), None, None, value,
        ("closed_cycle_time_unavailable",) if excluded_closed else (),
    )


def interface_commitment_fulfilment(evidence: Iterable[dict], *, source_cutoff: datetime) -> IndicatorObservation:
    """Classify only canonical, actor-visible facts at one source cutoff."""
    indicator = "interface_commitment_fulfilment"
    if source_cutoff.tzinfo is None or source_cutoff.utcoffset() is None:
        return IndicatorObservation(indicator, "indeterminate", None, None, None, {}, ("invalid_source_cutoff",))
    eligible = []
    unknown_due = False
    unknown_state = False
    for row in evidence:
        if not isinstance(row, dict) or not isinstance(row.get("current_use"), bool):
            unknown_state = True
            continue
        if not row["current_use"] or row.get("state") == "superseded":
            continue
        state = row.get("state")
        if state == "fulfilled_for_stated_use":
            eligible.append("fulfilled")
        elif state in {"identified", "acknowledged_by_provider", "information_provided", "consumer_review_required"}:
            due_at = row.get("due_at")
            if due_at is None:
                unknown_due = True
            elif not isinstance(due_at, datetime) or due_at.tzinfo is None or due_at.utcoffset() is None:
                unknown_due = True
            else:
                eligible.append("overdue" if due_at < source_cutoff else "open_on_time")
        else:
            unknown_state = True
    if unknown_due or unknown_state:
        limitations = ["actor_visible_population_only", "fulfilment_time_unavailable"]
        if unknown_due:
            limitations.append("typed_due_evidence_unavailable")
        if unknown_state:
            limitations.append("unknown_commitment_standing")
        return IndicatorObservation(indicator, "indeterminate", None, None, None, {}, tuple(limitations))
    if len(eligible) < MIN_SAFE_POPULATION:
        return IndicatorObservation(indicator, "indeterminate", None, None, None, {},
                                    ("actor_visible_population_only", "insufficient_safe_population"))
    fulfilled = eligible.count("fulfilled")
    return IndicatorObservation(
        indicator, "partial", len(eligible), fulfilled, len(eligible),
        {"ratio": fulfilled / len(eligible),
         "open_on_time": eligible.count("open_on_time"),
         "open_overdue": eligible.count("overdue")},
        ("actor_visible_population_only", "fulfilment_time_unavailable"),
    )


def completeness_trend(observations: Iterable[dict], *, source_cutoff: datetime) -> IndicatorObservation:
    """Compare owner-classified rules; no percentage, weights or invented past."""
    indicator = "completeness_trend"
    rows = tuple(observations)
    if source_cutoff.tzinfo is None or source_cutoff.utcoffset() is None:
        return IndicatorObservation(indicator, "indeterminate", None, None, None, {}, ("invalid_source_cutoff",))
    if not rows:
        return IndicatorObservation(indicator, "indeterminate", None, None, None, {}, ("no_completeness_history",))
    if len(rows) == 1:
        return IndicatorObservation(indicator, "indeterminate", None, None, None, {}, ("insufficient_trend_history",))
    if any(not isinstance(row, dict) for row in rows):
        return IndicatorObservation(indicator, "indeterminate", None, None, None, {}, ("invalid_completeness_observation",))
    methods = {(row.get("method_version"), row.get("catalog_digest"), row.get("observation_version")) for row in rows}
    if len(methods) != 1:
        return IndicatorObservation(indicator, "indeterminate", None, None, None, {}, ("method_changed",))
    method, catalog_digest, version = next(iter(methods))
    if method != "project_completeness.v1" or version != 1 or not isinstance(catalog_digest, str) or len(catalog_digest) != 64:
        return IndicatorObservation(indicator, "indeterminate", None, None, None, {}, ("invalid_completeness_method",))
    if any(row.get("assessment_status") != "complete_within_bounds" for row in rows):
        return IndicatorObservation(indicator, "indeterminate", None, None, None, {}, ("partial_completeness_source",))
    if any(not isinstance(row.get("source_cutoff"), datetime)
           or row["source_cutoff"].tzinfo is None
           or row["source_cutoff"].utcoffset() is None
           or row["source_cutoff"] > source_cutoff
           or not isinstance(row.get("source_digest"), str)
           for row in rows):
        return IndicatorObservation(indicator, "indeterminate", None, None, None, {}, ("invalid_completeness_observation",))
    ordered = sorted(rows, key=lambda row: (row["source_cutoff"], str(row.get("id"))))
    if len({row["source_digest"] for row in ordered}) != len(ordered):
        return IndicatorObservation(indicator, "indeterminate", None, None, None, {}, ("duplicate_completeness_source",))

    def classified(row):
        result = {}
        for item in row.get("classifications", ()):
            if (not isinstance(item, dict) or not isinstance(item.get("rule_id"), str)
                    or not isinstance(item.get("category"), str)
                    or item.get("classification") not in {"present", "missing", "not_applicable"}
                    or item["rule_id"] in result):
                return None
            result[item["rule_id"]] = (item["category"], item["classification"])
        return result if len(result) == 14 else None

    classified_rows = [classified(row) for row in ordered]
    first, last = classified_rows[0], classified_rows[-1]
    if (any(item is None for item in classified_rows) or first.keys() != last.keys()
            or any(item.keys() != first.keys() for item in classified_rows)):
        return IndicatorObservation(indicator, "indeterminate", None, None, None, {}, ("incomparable_completeness_rules",))
    if any(item[key][0] != first[key][0] for item in classified_rows for key in first):
        return IndicatorObservation(indicator, "indeterminate", None, None, None, {}, ("method_changed",))
    changed = any(first[key][1] != last[key][1] for key in first)
    limitations = tuple(dict.fromkeys(
        ("non_atomic_source_observation",)
        + tuple(str(code) for row in (ordered[0], ordered[-1])
                for code in row.get("limitations", ()))
    ))
    return IndicatorObservation(
        indicator, "partial", 14, None, None,
        {"method_version": ordered[-1]["method_version"],
         "catalog_digest": ordered[-1]["catalog_digest"],
         "assessment_state_from": ordered[0]["assessment_status"],
         "assessment_state_to": ordered[-1]["assessment_status"],
         "classification_transition": "changed" if changed else "unchanged"}, limitations,
    )


def technical_report_acceptance_flow(evidence: Iterable[object], *, source_cutoff: datetime,
                                     window_days: int = 30) -> IndicatorObservation:
    """Only each report's canonical creation-to-Human-Acceptance cycle."""
    indicator = "technical_report_acceptance_flow"
    if source_cutoff.tzinfo is None or source_cutoff.utcoffset() is None:
        return IndicatorObservation(indicator, "indeterminate", None, None, None, {}, ("invalid_source_cutoff",))
    if window_days not in {7, 30, 90, 180}:
        return IndicatorObservation(indicator, "indeterminate", None, None, None, {}, ("invalid_window",))
    window_start = source_cutoff - timedelta(days=window_days)
    rows = tuple(evidence)
    if not rows:
        return IndicatorObservation(indicator, "not_applicable", 0, None, None, {}, ("no_visible_reports",))
    completed_hours = []
    pending_days = []
    seen = set()
    for row in rows:
        report_id = getattr(row, "report_id", None)
        created_at = getattr(row, "created_at", None)
        lifecycle = getattr(row, "lifecycle", None)
        if (report_id is None or report_id in seen or not isinstance(created_at, datetime)
                or created_at.tzinfo is None or created_at.utcoffset() is None
                or created_at > source_cutoff):
            return IndicatorObservation(indicator, "indeterminate", None, None, None, {},
                                        ("canonical_report_creation_time_unavailable",))
        seen.add(report_id)
        if lifecycle == "draft":
            if (getattr(row, "accepted_at", None) is not None
                    or getattr(row, "accepted_snapshot_digest", None) is not None):
                return IndicatorObservation(indicator, "indeterminate", None, None, None, {},
                                            ("incoherent_report_lifecycle_evidence",))
            pending_days.append((source_cutoff - created_at).total_seconds() / 86400)
        elif lifecycle == "accepted":
            accepted_at = getattr(row, "accepted_at", None)
            digest = getattr(row, "accepted_snapshot_digest", None)
            if (not isinstance(accepted_at, datetime) or accepted_at.tzinfo is None
                    or accepted_at.utcoffset() is None or accepted_at < created_at
                    or accepted_at > source_cutoff or not isinstance(digest, str)
                    or len(digest) != 64
                    or getattr(row, "accepted_aggregate_version", None) != getattr(row, "version", None)):
                return IndicatorObservation(indicator, "indeterminate", None, None, None, {},
                                            ("canonical_human_acceptance_evidence_unavailable",))
            if accepted_at >= window_start:
                completed_hours.append((accepted_at - created_at).total_seconds() / 3600)
        else:
            return IndicatorObservation(indicator, "indeterminate", None, None, None, {},
                                        ("unknown_report_lifecycle",))
    if not completed_hours and not pending_days:
        return IndicatorObservation(indicator, "not_applicable", 0, None, None, {},
                                    ("no_acceptance_cycles_in_window",))
    if not completed_hours and len(pending_days) >= MIN_SAFE_POPULATION:
        return IndicatorObservation(indicator, "partial", 0, None, None,
                                    {"pending_cycles": len(pending_days),
                                     "oldest_pending_days": max(pending_days)},
                                    ("no_completed_acceptance_cycles", "open_draft_cycles"))
    if len(completed_hours) < MIN_SAFE_POPULATION:
        return IndicatorObservation(indicator, "indeterminate", None, None, None, {},
                                    ("insufficient_safe_completed_cycles",))
    value = {"average_acceptance_hours": sum(completed_hours) / len(completed_hours),
             "completed_cycles": len(completed_hours)}
    limitations = []
    if len(pending_days) >= MIN_SAFE_POPULATION:
        value["pending_cycles"] = len(pending_days)
        value["oldest_pending_days"] = max(pending_days)
        limitations.append("open_draft_cycles")
    elif pending_days:
        limitations.append("pending_cohort_suppressed")
    return IndicatorObservation(indicator, "partial" if pending_days else "complete",
                                len(completed_hours), None, None, value, tuple(limitations))


def evidence_availability(evidence: Iterable[object], *, source_cutoff: datetime,
                          population_complete: bool) -> IndicatorObservation:
    """Count only actor-visible Evidence classified by canonical exact-artifact facts."""
    indicator = "evidence_availability"
    if not population_complete:
        return IndicatorObservation(indicator, "indeterminate", None, None, None, {},
                                    ("authorized_population_incomplete",))
    if (not isinstance(source_cutoff, datetime) or source_cutoff.tzinfo is None
            or source_cutoff.utcoffset() is None):
        return IndicatorObservation(indicator, "indeterminate", None, None, None, {},
                                    ("invalid_source_cutoff",))
    rows = tuple(evidence)
    if not rows:
        return IndicatorObservation(indicator, "not_applicable", 0, None, None, {},
                                    ("no_authorized_evidence",))
    seen, available, unavailable, unknown = set(), 0, 0, 0
    for row in rows:
        identifier = getattr(row, "evidence_id", None)
        state = getattr(row, "state", None)
        if (identifier is None or identifier in seen
                or getattr(row, "source_cutoff", None) != source_cutoff
                or state not in {"available", "unavailable", "indeterminate"}):
            return IndicatorObservation(indicator, "indeterminate", None, None, None, {},
                                        ("invalid_canonical_availability_evidence",))
        seen.add(identifier)
        available += state == "available"
        unavailable += state == "unavailable"
        unknown += state == "indeterminate"
    classified = available + unavailable
    if classified < MIN_SAFE_POPULATION:
        return IndicatorObservation(indicator, "indeterminate", None, None, None, {},
                                    ("insufficient_safe_population",))
    return IndicatorObservation(indicator, "partial" if unknown else "complete",
                                classified, available, classified,
                                {"ratio": available / classified},
                                ("excluded_indeterminate_availability",) if unknown else ())
