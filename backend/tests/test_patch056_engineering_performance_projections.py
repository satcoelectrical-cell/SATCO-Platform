from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.services.engineering_performance import IndicatorObservation
from app.services.engineering_performance_intelligence import AdvisoryAction, action_key
from app.services.engineering_performance_projection_service import EngineeringPerformanceProjectionService


NOW = datetime(2026, 9, 21, tzinfo=timezone.utc)


class Repo:
    def __init__(self):
        self.snapshots = []
        self.actions = []
        self.commits = 0

    def find_snapshot(self, **values):
        return next((row for row in self.snapshots if all(
            getattr(row, key) == value for key, value in values.items()
        )), None)

    def add_snapshot(self, row): self.snapshots.append(row)
    def list_snapshots(self, **values):
        rows = [row for row in self.snapshots
                if row.organization_id == values["organization_id"]
                and row.project_id == values["project_id"]
                and row.workspace_id == values["workspace_id"]
                and row.actor_id == values["actor_id"]
                and row.observed_at >= values["after"]]
        if values["indicator_id"] is not None:
            rows = [row for row in rows if row.indicator_id == values["indicator_id"]]
        return rows[:values["limit"]]
    def get_snapshot(self, **values):
        values["id"] = values.pop("snapshot_id")
        return next((row for row in self.snapshots if all(
            getattr(row, key) == value for key, value in values.items()
        )), None)
    def list_actions(self, **values): return list(self.actions)
    def add_action(self, row): self.actions.append(row)
    def commit(self): self.commits += 1
    def rollback(self): raise AssertionError("unexpected rollback")


def scope(actor=3):
    return SimpleNamespace(organization_id=uuid4(), project_id=7,
                           workspace_id=None, actor_id=actor)


def observation(*, observed_at=NOW, calculation="calculator.v1", handles=("source:1",)):
    return IndicatorObservation(
        "required_input_readiness", "complete", 5, 4, 5, {"ratio": .8}, (),
        source_cutoff=observed_at, source_digest="a" * 64,
        source_handles=handles, organization_id="ignored", project_id=7,
        observed_at=observed_at, window_start=observed_at - timedelta(days=30),
        window_end=observed_at, calculation_method_version=calculation,
    )


def action(rule="required-input-gap", version="1", subject="required-inputs"):
    return AdvisoryAction(
        action_key(rule, version, "project:7", subject), rule, version,
        "review_required_inputs", ("required_inputs_incomplete",),
        ("source:1",), (),
    )


def test_persisted_snapshot_is_reproducible_and_actor_bound():
    repository = Repo(); current_scope = scope()
    service = EngineeringPerformanceProjectionService(repository, clock=lambda: NOW)
    rows = {"required_input_readiness": observation()}
    first = service.persist_observations(scope=current_scope, observations=rows)
    second = service.persist_observations(scope=current_scope, observations=rows)
    assert len(repository.snapshots) == 1 and first[0] is second[0]
    stored = first[0]
    assert stored.actor_id == current_scope.actor_id
    assert stored.source_digest == "a" * 64
    assert stored.source_handles_json == ["source:1"]
    assert stored.recomputation_reason == "request_calculation"


def test_action_projection_deduplicates_and_resolves_only_after_both_boundaries():
    repository = Repo(); current_scope = scope(); now = [NOW]
    service = EngineeringPerformanceProjectionService(repository, clock=lambda: now[0])
    observations = {"required_input_readiness": observation()}
    projected = (action(),)
    service.reconcile_actions(scope=current_scope, projected=projected,
                              observations=observations)
    service.reconcile_actions(scope=current_scope, projected=projected,
                              observations=observations)
    assert len(repository.actions) == 1
    row = repository.actions[0]
    assert row.status == "active" and row.absent_recalculation_count == 0
    now[0] = NOW + timedelta(hours=25)
    service.reconcile_actions(scope=current_scope, projected=(), observations=observations)
    assert row.status == "stale" and row.absent_recalculation_count == 1
    now[0] = NOW + timedelta(hours=26)
    service.reconcile_actions(scope=current_scope, projected=(), observations=observations)
    assert row.status == "resolved_by_source_state" and row.absent_recalculation_count == 2


def test_material_replacement_is_deterministically_superseded():
    repository = Repo(); current_scope = scope()
    service = EngineeringPerformanceProjectionService(repository, clock=lambda: NOW)
    observations = {"required_input_readiness": observation()}
    original, replacement = action(subject="old"), action(subject="new")
    service.reconcile_actions(scope=current_scope, projected=(original,), observations=observations)
    service.reconcile_actions(scope=current_scope, projected=(replacement,), observations=observations)
    prior = next(row for row in repository.actions if row.action_key == original.action_key)
    assert prior.status == "superseded"
    assert prior.superseded_by_action_key == replacement.action_key


def test_trends_segment_method_changes_without_fabricating_points():
    repository = Repo(); current_scope = scope(); service = EngineeringPerformanceProjectionService(repository, clock=lambda: NOW)
    first = observation(observed_at=NOW - timedelta(days=2), calculation="calculator.v1")
    second = observation(observed_at=NOW - timedelta(days=1), calculation="calculator.v2")
    service.persist_observations(scope=current_scope, observations={"first": first})
    service.persist_observations(scope=current_scope, observations={"second": second})
    points, limitations = service.trends(scope=current_scope, window_days=7,
                                         indicator_id=None, cadence="daily")
    assert len(points) == 2 and limitations == ()
    assert points[0]["method_changed"] is False
    assert points[1]["method_changed"] is True


def test_historical_handles_are_intersected_with_current_authorization():
    repository = Repo(); current_scope = scope(); service = EngineeringPerformanceProjectionService(repository, clock=lambda: NOW)
    stored = service.persist_observations(
        scope=current_scope,
        observations={"required_input_readiness": observation(handles=("visible", "now-protected"))},
    )[0]
    handles = service.historical_handles(
        scope=current_scope, snapshot_id=stored.id,
        indicator_id="required_input_readiness", currently_authorized=("visible",),
    )
    assert handles == ("visible",)
    foreign = scope(actor=4); foreign.organization_id = current_scope.organization_id
    assert service.historical_handles(
        scope=foreign, snapshot_id=stored.id,
        indicator_id="required_input_readiness", currently_authorized=("visible",),
    ) is None
