"""Evidence-owned, actor-safe exact-artifact availability read for PATCH-056."""
import base64
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import hmac
import json
from uuid import UUID, uuid4

from app.core.config import settings
from app.exceptions.evidence import EvidenceProtectedNotFound
from app.models.supporting_file_command import SupportingFileScope


class EvidenceAvailabilityIncomplete(RuntimeError):
    """The authorized population changed or traversal cannot be proven complete."""


@dataclass(frozen=True, slots=True)
class EvidenceAvailabilityItem:
    evidence_id: UUID
    evidence_version: int
    project_id: int | None
    workspace_id: int | None
    state: str
    source_cutoff: datetime
    artifact_versions: tuple[tuple[UUID, str], ...]
    source_event_ids: tuple[UUID, ...]
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EvidenceAvailabilityPage:
    items: tuple[EvidenceAvailabilityItem, ...]
    next_cursor: str | None
    source_cutoff: datetime
    traversal_complete: bool


@dataclass(frozen=True, slots=True)
class EvidenceAvailabilitySnapshot:
    snapshot_id: UUID
    source_cutoff: datetime
    status: str
    method_version: str
    items: tuple[EvidenceAvailabilityItem, ...]
    limitations: tuple[str, ...] = ()


class EvidenceAvailabilityService:
    MAX_PAGE = 50

    def __init__(self, *, uow_factory, authorization, availability_reader, clock):
        self.uow_factory = uow_factory
        self.authorization = authorization
        self.availability_reader = availability_reader
        self.clock = clock

    @staticmethod
    def _key() -> bytes:
        return sha256((settings.SECRET_KEY + ":evidence-availability:v1").encode()).digest()

    @classmethod
    def _encode(cls, payload: dict) -> str:
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        signature = hmac.new(cls._key(), raw, sha256).digest()
        return base64.urlsafe_b64encode(raw + signature).decode().rstrip("=")

    @classmethod
    def _decode(cls, token: str) -> dict:
        try:
            padded = token + "=" * (-len(token) % 4)
            packed = base64.urlsafe_b64decode(padded)
            raw, signature = packed[:-32], packed[-32:]
            if len(packed) < 33 or not hmac.compare_digest(
                signature, hmac.new(cls._key(), raw, sha256).digest()
            ):
                raise ValueError("signature")
            return json.loads(raw)
        except Exception as exc:
            raise EvidenceAvailabilityIncomplete("invalid continuation") from exc

    def _classify(self, *, uow, item, actor, source_cutoff):
        links = uow.evidence.list_graph_links_for_evidence(
            evidence_id=item.id, organization_id=actor.organization_id,
            project_id=item.project_id, workspace_id=item.workspace_id, limit=11,
        )
        if not links:
            return EvidenceAvailabilityItem(item.id, item.version, item.project_id,
                                            item.workspace_id, "indeterminate", source_cutoff,
                                            (), (), ("no_exact_artifact_basis",))
        if len(links) > 10:
            raise EvidenceAvailabilityIncomplete("invalid exact-artifact population")
        if item.project_id is None:
            raise EvidenceAvailabilityIncomplete("projectless Evidence has invalid artifact links")
        states, versions, events, limitations = [], [], [], []
        scope = SupportingFileScope(actor.organization_id, item.project_id, item.workspace_id)
        for link in links:
            try:
                fact = self.availability_reader.read_exact_availability(
                    actor_id=actor.actor_id, scope=scope, asset_id=link.asset_id,
                    source_cutoff=source_cutoff,
                )
            except Exception:
                states.append("indeterminate")
                limitations.append("exact_artifact_owner_unavailable_or_protected")
                continue
            if fact.asset_id != link.asset_id or fact.state not in {
                "available", "unavailable", "indeterminate",
            }:
                raise EvidenceAvailabilityIncomplete("invalid owner availability result")
            states.append(fact.state)
            if fact.state != "indeterminate":
                if fact.verified_at != source_cutoff or fact.source_event_id is None:
                    raise EvidenceAvailabilityIncomplete("unverified historical artifact state")
                versions.append((fact.asset_id, fact.object_version))
                events.append(fact.source_event_id)
            elif fact.limitation:
                limitations.append(fact.limitation)
        state = ("available" if "available" in states else
                 "unavailable" if states and all(s == "unavailable" for s in states) else
                 "indeterminate")
        if state == "indeterminate" and not limitations:
            limitations.append("historical_availability_unproven")
        return EvidenceAvailabilityItem(item.id, item.version, item.project_id,
                                        item.workspace_id, state, source_cutoff,
                                        tuple(versions), tuple(events), tuple(sorted(set(limitations))))

    def _observe_snapshot_item(self, *, uow, item, actor, snapshot_id, source_cutoff):
        links = uow.evidence.list_graph_links_for_evidence(
            evidence_id=item.id, organization_id=actor.organization_id,
            project_id=item.project_id, workspace_id=item.workspace_id, limit=11,
        )
        if not links:
            return EvidenceAvailabilityItem(
                item.id, item.version, item.project_id, item.workspace_id,
                "indeterminate", source_cutoff, (), (), ("no_exact_artifact_basis",),
            )
        if len(links) > 10 or item.project_id is None:
            raise EvidenceAvailabilityIncomplete("invalid exact-artifact population")
        scope = SupportingFileScope(actor.organization_id, item.project_id, item.workspace_id)
        try:
            facts = self.availability_reader.observe_exact_availability_batch(
                actor_id=actor.actor_id, scope=scope,
                asset_ids=tuple(link.asset_id for link in links),
                snapshot_id=snapshot_id, source_cutoff=source_cutoff,
            )
        except Exception:
            return EvidenceAvailabilityItem(
                item.id, item.version, item.project_id, item.workspace_id,
                "indeterminate", source_cutoff, (), (),
                ("exact_artifact_owner_unavailable_or_protected",),
            )
        if len(facts) != len(links) or {fact.asset_id for fact in facts} != {
            link.asset_id for link in links
        }:
            raise EvidenceAvailabilityIncomplete("invalid exact-artifact batch result")
        states, versions, events, limitations = [], [], [], []
        for fact in facts:
            if fact.state not in {"available", "unavailable", "indeterminate"}:
                raise EvidenceAvailabilityIncomplete("invalid owner availability result")
            states.append(fact.state)
            if not fact.object_version:
                raise EvidenceAvailabilityIncomplete("missing exact artifact version")
            versions.append((fact.asset_id, fact.object_version))
            if fact.state == "indeterminate":
                limitations.append(fact.limitation or "exact_artifact_observation_indeterminate")
            elif (fact.verified_at != source_cutoff or fact.source_event_id is None
                  ):
                raise EvidenceAvailabilityIncomplete("incoherent exact-artifact batch result")
            else:
                events.append(fact.source_event_id)
        state = ("available" if "available" in states else
                 "unavailable" if states and all(value == "unavailable" for value in states)
                 else "indeterminate")
        return EvidenceAvailabilityItem(
            item.id, item.version, item.project_id, item.workspace_id, state,
            source_cutoff, tuple(versions), tuple(events),
            tuple(sorted(set(limitations))),
        )

    def issue_snapshot(self, *, actor, project_id: int,
                       workspace_id: int | None) -> EvidenceAvailabilitySnapshot:
        """Issue one prospective owner snapshot; authorization precedes population."""
        scope_result = self.authorization.availability_scope(
            actor=actor, project_id=project_id, workspace_id=workspace_id,
        )
        if scope_result is None:
            raise EvidenceProtectedNotFound()
        project_wide, visible_workspaces = scope_result
        source_cutoff, snapshot_id = self.clock.now(), uuid4()
        scope = SupportingFileScope(actor.organization_id, project_id, workspace_id)
        self.availability_reader.begin_population_availability_snapshot(
            actor_id=actor.actor_id, scope=scope, snapshot_id=snapshot_id,
            source_cutoff=source_cutoff,
            visible_workspace_ids=tuple(sorted(visible_workspaces)),
        )
        persisted: list[EvidenceAvailabilityItem] = []
        limitations: tuple[str, ...] = ()
        complete = False
        try:
            with self.uow_factory() as uow:
                expected, changed = uow.evidence.availability_population(
                    organization_id=actor.organization_id, project_id=project_id,
                    workspace_id=workspace_id, project_wide=project_wide,
                    visible_workspaces=visible_workspaces, source_cutoff=source_cutoff,
                )
                if changed or expected > 5000:
                    raise EvidenceAvailabilityIncomplete("authorized population unavailable")
                anchor = None
                for _ in range(101):
                    rows = uow.evidence.list_authorized_availability_page(
                        organization_id=actor.organization_id, project_id=project_id,
                        workspace_id=workspace_id, project_wide=project_wide,
                        visible_workspaces=visible_workspaces, source_cutoff=source_cutoff,
                        anchor=anchor, limit=51,
                    )
                    visible = rows[:50]
                    for item in visible:
                        observed = self._observe_snapshot_item(
                            uow=uow, item=item, actor=actor,
                            snapshot_id=snapshot_id, source_cutoff=source_cutoff,
                        )
                        self.availability_reader.record_population_availability_item(
                            actor_id=actor.actor_id, scope=scope, snapshot_id=snapshot_id,
                            evidence_id=observed.evidence_id,
                            evidence_version=observed.evidence_version,
                            evidence_project_id=observed.project_id,
                            evidence_workspace_id=observed.workspace_id,
                            state=observed.state,
                            artifact_versions=observed.artifact_versions,
                            source_event_ids=observed.source_event_ids,
                            limitations=observed.limitations,
                        )
                        persisted.append(observed)
                    if len(rows) <= 50:
                        break
                    anchor = (visible[-1].created_at, visible[-1].id)
                else:
                    raise EvidenceAvailabilityIncomplete("authorized population bound exceeded")
                final_count, final_changed = uow.evidence.availability_population(
                    organization_id=actor.organization_id, project_id=project_id,
                    workspace_id=workspace_id, project_wide=project_wide,
                    visible_workspaces=visible_workspaces, source_cutoff=source_cutoff,
                )
                if final_changed or final_count != expected or len(persisted) != expected:
                    raise EvidenceAvailabilityIncomplete("authorized population changed")
                complete = True
        except EvidenceAvailabilityIncomplete as exc:
            limitations = (str(exc).replace(" ", "_"),)
        except Exception:
            limitations = ("owner_snapshot_unavailable",)
        self.availability_reader.finalize_population_availability_snapshot(
            actor_id=actor.actor_id, scope=scope, snapshot_id=snapshot_id,
            complete=complete, limitations=limitations,
            completed_at=self.clock.now(),
        )
        return EvidenceAvailabilitySnapshot(
            snapshot_id, source_cutoff, "complete" if complete else "incomplete",
            "evidence-availability.v1", tuple(persisted) if complete else (), limitations,
        )

    def read_snapshot(self, *, actor, project_id: int, workspace_id: int | None,
                      snapshot_id: UUID) -> EvidenceAvailabilitySnapshot:
        scope_result = self.authorization.availability_scope(
            actor=actor, project_id=project_id, workspace_id=workspace_id,
        )
        if scope_result is None:
            raise EvidenceProtectedNotFound()
        scope = SupportingFileScope(actor.organization_id, project_id, workspace_id)
        snapshot, rows = self.availability_reader.read_population_availability_snapshot(
            actor_id=actor.actor_id, scope=scope, snapshot_id=snapshot_id,
        )
        items = tuple(EvidenceAvailabilityItem(
            row.evidence_id, row.evidence_version, row.project_id, row.workspace_id,
            row.state, snapshot.source_cutoff,
            tuple((UUID(asset_id), version) for asset_id, version in row.artifact_versions),
            tuple(UUID(value) for value in row.source_event_ids),
            tuple(row.limitation_codes),
        ) for row in rows)
        return EvidenceAvailabilitySnapshot(
            snapshot.id, snapshot.source_cutoff, snapshot.status,
            snapshot.method_version, items if snapshot.status == "complete" else (),
            tuple(snapshot.limitation_codes),
        )

    def list_page(self, *, actor, project_id: int, workspace_id: int | None,
                  source_cutoff: datetime, page_size: int = 20,
                  cursor: str | None = None) -> EvidenceAvailabilityPage:
        if (not isinstance(source_cutoff, datetime) or source_cutoff.tzinfo is None
                or source_cutoff.utcoffset() is None or not 1 <= page_size <= self.MAX_PAGE
                or project_id < 1 or (workspace_id is not None and workspace_id < 1)):
            raise EvidenceAvailabilityIncomplete("invalid authorized traversal request")
        scope = self.authorization.availability_scope(
            actor=actor, project_id=project_id, workspace_id=workspace_id,
        )
        if scope is None:
            raise EvidenceProtectedNotFound()
        project_wide, visible_workspaces = scope
        visibility = sha256(json.dumps({"project_wide": project_wide,
                                        "workspaces": visible_workspaces}).encode()).hexdigest()
        now = self.clock.now()
        if source_cutoff > now:
            raise EvidenceAvailabilityIncomplete("future source cutoff")
        anchor, processed, expected = None, 0, None
        if cursor is not None:
            state = self._decode(cursor)
            if (state.get("v") != 1 or state.get("actor") != actor.actor_id
                    or state.get("organization") != str(actor.organization_id)
                    or state.get("project") != project_id
                    or state.get("workspace") != workspace_id
                    or state.get("visibility") != visibility
                    or state.get("cutoff") != source_cutoff.isoformat()
                    or state.get("size") != page_size):
                raise EvidenceAvailabilityIncomplete("continuation scope changed")
            try:
                issued_at = datetime.fromisoformat(state["issued_at"])
                anchor = (datetime.fromisoformat(state["anchor_at"]), UUID(state["anchor_id"]))
                processed, expected = state["processed"], state["expected"]
                if (issued_at.tzinfo is None or now - issued_at > timedelta(minutes=15)
                        or not 0 <= processed < expected or type(expected) is not int):
                    raise ValueError("expired or invalid continuation")
            except (KeyError, TypeError, ValueError) as exc:
                raise EvidenceAvailabilityIncomplete("invalid continuation") from exc
        with self.uow_factory() as uow:
            count, changed = uow.evidence.availability_population(
                organization_id=actor.organization_id, project_id=project_id,
                workspace_id=workspace_id, project_wide=project_wide,
                visible_workspaces=visible_workspaces, source_cutoff=source_cutoff,
            )
            if changed or (expected is not None and count != expected):
                raise EvidenceAvailabilityIncomplete("authorized population changed")
            expected = count if expected is None else expected
            candidates = uow.evidence.list_authorized_availability_page(
                organization_id=actor.organization_id, project_id=project_id,
                workspace_id=workspace_id, project_wide=project_wide,
                visible_workspaces=visible_workspaces, source_cutoff=source_cutoff,
                anchor=anchor, limit=page_size + 1,
            )
            visible = candidates[:page_size]
            items = tuple(self._classify(uow=uow, item=item, actor=actor,
                                         source_cutoff=source_cutoff) for item in visible)
            final_count, final_changed = uow.evidence.availability_population(
                organization_id=actor.organization_id, project_id=project_id,
                workspace_id=workspace_id, project_wide=project_wide,
                visible_workspaces=visible_workspaces, source_cutoff=source_cutoff,
            )
            if final_changed or final_count != expected:
                raise EvidenceAvailabilityIncomplete("authorized population changed")
            processed += len(visible)
            more = len(candidates) > page_size
            if (more and processed >= expected) or (not more and processed != expected):
                raise EvidenceAvailabilityIncomplete("authorized traversal changed")
            next_cursor = None
            if more:
                last = visible[-1]
                next_cursor = self._encode({
                    "v": 1, "actor": actor.actor_id,
                    "organization": str(actor.organization_id),
                    "project": project_id, "workspace": workspace_id,
                    "visibility": visibility, "cutoff": source_cutoff.isoformat(),
                    "size": page_size, "issued_at": state["issued_at"] if cursor else now.isoformat(),
                    "anchor_at": last.created_at.isoformat(), "anchor_id": str(last.id),
                    "processed": processed, "expected": expected,
                })
            return EvidenceAvailabilityPage(items, next_cursor, source_cutoff, not more)
