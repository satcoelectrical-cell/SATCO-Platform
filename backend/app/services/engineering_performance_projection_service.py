"""Runtime persistence for reproducible PATCH-056 derived projections."""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from uuid import UUID, uuid4

from app.models.engineering_performance import (
    EngineeringNextActionProjection, EngineeringPerformanceSnapshot,
)
from app.services.engineering_performance_intelligence import next_projection_status


CALCULATION_VERSION = "engineering-performance.v1"


class EngineeringPerformanceProjectionService:
    def __init__(self, repository, clock=lambda: datetime.now(timezone.utc)):
        self.repository = repository
        self.clock = clock

    def persist_observations(self, *, scope, observations):
        rows = []
        try:
            for observation in observations.values():
                if (observation.observed_at is None or observation.window_start is None
                        or observation.window_end is None or observation.source_cutoff is None
                        or observation.source_digest is None):
                    raise ValueError("observation provenance is incomplete")
                existing = self.repository.find_snapshot(
                    organization_id=scope.organization_id, project_id=scope.project_id,
                    workspace_id=scope.workspace_id, actor_id=scope.actor_id,
                    indicator_id=observation.indicator_id,
                    indicator_version=observation.indicator_version,
                    window_start=observation.window_start,
                    window_end=observation.window_end,
                    source_digest=observation.source_digest,
                    calculation_version=observation.calculation_method_version,
                )
                if existing is None:
                    existing = EngineeringPerformanceSnapshot(
                        id=uuid4(), organization_id=scope.organization_id,
                        project_id=scope.project_id, workspace_id=scope.workspace_id,
                        actor_id=scope.actor_id, indicator_id=observation.indicator_id,
                        indicator_version=observation.indicator_version,
                        window_start=observation.window_start,
                        window_end=observation.window_end,
                        observed_at=observation.observed_at,
                        source_cutoff=observation.source_cutoff,
                        source_digest=observation.source_digest,
                        source_handles_json=list(observation.source_handles),
                        recomputation_reason="request_calculation",
                        calculation_version=observation.calculation_method_version,
                        observation_state=observation.state,
                        value_json=observation.value,
                        limitation_codes_json=list(observation.limitations),
                        eligible_count=observation.eligible_count,
                        numerator=observation.numerator,
                        denominator=observation.denominator,
                    )
                    self.repository.add_snapshot(existing)
                rows.append(existing)
            self.repository.commit()
            return tuple(rows)
        except Exception:
            self.repository.rollback()
            raise

    @staticmethod
    def _action_digest(observations) -> str:
        payload = [(key, row.source_digest, row.calculation_method_version)
                   for key, row in sorted(observations.items())]
        return sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()

    def reconcile_actions(self, *, scope, projected, observations):
        now = self.clock()
        digest = self._action_digest(observations)
        try:
            existing = self.repository.list_actions(
                organization_id=scope.organization_id, project_id=scope.project_id,
                workspace_id=scope.workspace_id, actor_id=scope.actor_id, lock=True,
            )
            by_key = {row.action_key: row for row in existing}
            current_keys = {action.action_key for action in projected}
            for action in projected:
                row = by_key.get(action.action_key)
                if row is None:
                    row = EngineeringNextActionProjection(
                        id=uuid4(), organization_id=scope.organization_id,
                        project_id=scope.project_id, workspace_id=scope.workspace_id,
                        actor_id=scope.actor_id, action_key=action.action_key,
                        rule_id=action.rule_id, rule_version=action.rule_version,
                        title_code=action.title_code,
                        rationale_codes_json=list(action.rationale_codes),
                        supporting_handle_json=list(action.source_handles),
                        limitation_codes_json=list(action.limitations),
                        first_seen_at=now, last_seen_at=now,
                        absent_recalculation_count=0, status="active",
                        source_digest=digest, calculation_version=CALCULATION_VERSION,
                    )
                    for previous in existing:
                        if (previous.rule_id == action.rule_id
                                and previous.action_key != action.action_key
                                and previous.status in {"active", "stale"}):
                            previous.status = "superseded"
                            previous.superseded_by_action_key = action.action_key
                    self.repository.add_action(row)
                    existing.append(row)
                    by_key[row.action_key] = row
                else:
                    row.last_seen_at = now
                    row.absent_recalculation_count = 0
                    row.status = "active"
                    row.superseded_by_action_key = None
                    row.rationale_codes_json = list(action.rationale_codes)
                    row.supporting_handle_json = list(action.source_handles)
                    row.limitation_codes_json = list(action.limitations)
                    row.source_digest = digest
            for row in existing:
                if row.action_key in current_keys or row.status == "superseded":
                    continue
                row.absent_recalculation_count += 1
                row.status = next_projection_status(
                    active_trigger=False,
                    absent_recalculations=row.absent_recalculation_count,
                    last_seen_at=row.last_seen_at, now=now,
                )
                row.source_digest = digest
            self.repository.commit()
            return tuple(existing)
        except Exception:
            self.repository.rollback()
            raise

    def trends(self, *, scope, window_days: int, indicator_id: str | None,
               cadence: str):
        now = self.clock()
        rows = self.repository.list_snapshots(
            organization_id=scope.organization_id, project_id=scope.project_id,
            workspace_id=scope.workspace_id, actor_id=scope.actor_id,
            after=now - timedelta(days=window_days), indicator_id=indicator_id,
            limit=10001,
        )
        if len(rows) > 10000:
            return (), ("authorized_trend_population_exceeds_bound",)
        selected = {}
        for row in rows:
            instant = row.observed_at.astimezone(timezone.utc)
            bucket = (instant.date().isoformat() if cadence == "daily" else
                      f"{instant.isocalendar().year}-W{instant.isocalendar().week:02d}")
            selected[(row.indicator_id, bucket)] = row
        per_indicator_limit = 180 if cadence == "daily" else 26
        result = []
        for current_indicator in sorted({key[0] for key in selected}):
            indicator_rows = [row for (name, _), row in selected.items()
                              if name == current_indicator]
            indicator_rows.sort(key=lambda row: (row.observed_at, str(row.id)))
            previous_method = None
            for row in indicator_rows[-per_indicator_limit:]:
                method_changed = previous_method is not None and previous_method != row.calculation_version
                result.append({
                    "id": str(row.id), "indicator_id": row.indicator_id,
                    "indicator_version": row.indicator_version,
                    "observed_at": row.observed_at,
                    "source_cutoff": row.source_cutoff,
                    "source_digest": row.source_digest,
                    "calculation_version": row.calculation_version,
                    "observation_state": row.observation_state,
                    "value": row.value_json,
                    "limitations": row.limitation_codes_json,
                    "method_changed": method_changed,
                })
                previous_method = row.calculation_version
        result.sort(key=lambda row: (row["observed_at"], row["indicator_id"]))
        return tuple(result), ()

    def historical_handles(self, *, scope, snapshot_id: UUID, indicator_id: str,
                           currently_authorized: tuple[str, ...]):
        row = self.repository.get_snapshot(
            snapshot_id=snapshot_id, organization_id=scope.organization_id,
            project_id=scope.project_id, workspace_id=scope.workspace_id,
            actor_id=scope.actor_id,
        )
        if row is None or row.indicator_id != indicator_id:
            return None
        allowed = set(currently_authorized)
        return tuple(handle for handle in (row.source_handles_json or ())
                     if handle in allowed)

    @staticmethod
    def action_view(row):
        return {
            "action_key": row.action_key, "rule_id": row.rule_id,
            "rule_version": row.rule_version, "title_code": row.title_code,
            "rationale_codes": row.rationale_codes_json,
            "source_handles": row.supporting_handle_json,
            "limitations": row.limitation_codes_json,
            "first_seen_at": row.first_seen_at, "last_seen_at": row.last_seen_at,
            "status": row.status,
            "superseded_by_action_key": row.superseded_by_action_key,
        }
