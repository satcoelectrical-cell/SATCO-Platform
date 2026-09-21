"""Exact-artifact Evidence availability tests without a database or data-plane call."""
from datetime import datetime, timedelta, timezone
from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.adapters.supporting_file_object_store import InMemoryPrivateSupportingFileObjectStore
from app.models.evidence_command import EvidenceActor
from app.models.supporting_file_command import SupportingFileScope
from app.ports.supporting_file import SupportingFileAvailabilityFact
from app.services.engineering_performance import evidence_availability
from app.services.evidence_availability_service import (
    EvidenceAvailabilityIncomplete, EvidenceAvailabilityService,
)
from app.services.supporting_file_service import SupportingFileService
from app.exceptions.supporting_file import SupportingFileProtectedNotFound


NOW = datetime(2026, 9, 20, tzinfo=timezone.utc)


class _FileRepository:
    def __init__(self, asset):
        self.asset = asset
        self.observations = []

    def get_scoped(self, asset_id, organization_id):
        return self.asset if (asset_id, organization_id) == (
            self.asset.id, self.asset.organization_id,
        ) else None

    def record_availability(self, observation):
        self.observations.append(observation)

    def stage_outbox(self, record):
        pass

    def stage_audit(self, **kwargs):
        pass

    def availability_at_exact_cutoff(self, *, asset_id, organization_id, cutoff):
        return next((row for row in reversed(self.observations) if
                     row.asset_id == asset_id and row.organization_id == organization_id
                     and row.observed_at == cutoff), None)


class _FileUow:
    def __init__(self, repository):
        self.repository = repository
        self.commits = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        raise AssertionError("unexpected rollback")


class _AllowFiles:
    def require_read(self, **kwargs):
        pass

    def require_mutation(self, **kwargs):
        pass


def _file_owner():
    org, asset_id = uuid4(), uuid4()
    objects = InMemoryPrivateSupportingFileObjectStore()
    key = "objects/" + "a" * 64
    first = objects.put_private(key=key, content=BytesIO(b"exact"),
                                media_type="application/pdf")
    asset = SimpleNamespace(
        id=asset_id, organization_id=org, project_id=7, workspace_id=12,
        version=2,
        storage_key=first.key, object_version=first.version,
        byte_size=first.byte_size, content_digest=first.sha256,
    )
    repo = _FileRepository(asset)
    uow = _FileUow(repo)
    service = SupportingFileService(uow=uow, objects=objects, scanner=None,
                                    authorization=_AllowFiles())
    return service, uow, objects, asset, SupportingFileScope(org, 7, 12)


def test_exact_version_current_and_prospective_history():
    owner, uow, objects, asset, scope = _file_owner()
    original_asset_version = asset.version
    past = NOW - timedelta(days=1)
    assert owner.read_exact_availability(actor_id=3, scope=scope, asset_id=asset.id,
                                         source_cutoff=past).state == "indeterminate"
    assert asset.version == original_asset_version
    assert owner.read_exact_availability(actor_id=3, scope=scope,
                                         asset_id=asset.id).state == "available"
    observed = owner.observe_exact_availability(actor_id=3, scope=scope,
                                                asset_id=asset.id)
    assert observed.state == "available" and observed.source_event_id is not None
    assert uow.commits == 1
    assert owner.read_exact_availability(actor_id=3, scope=scope, asset_id=asset.id,
                                         source_cutoff=observed.verified_at).state == "available"
    assert owner.read_exact_availability(actor_id=3, scope=scope, asset_id=asset.id,
                                         source_cutoff=observed.verified_at + timedelta(microseconds=1)).state == "indeterminate"
    # A same-key successor object cannot substitute for the linked exact version.
    objects.put_private(key=asset.storage_key, content=BytesIO(b"new"),
                        media_type="application/pdf")
    objects.delete_exact(asset.storage_key, asset.object_version)
    assert owner.read_exact_availability(actor_id=3, scope=scope,
                                         asset_id=asset.id).state == "unavailable"
    lost = owner.observe_exact_availability(actor_id=3, scope=scope,
                                            asset_id=asset.id)
    assert lost.state == "unavailable"
    assert owner.read_exact_availability(actor_id=3, scope=scope, asset_id=asset.id,
                                         source_cutoff=lost.verified_at).state == "unavailable"
    assert owner.read_exact_availability(actor_id=3, scope=scope, asset_id=asset.id,
                                         source_cutoff=past).state == "indeterminate"
    assert asset.version == original_asset_version


def test_protected_artifact_does_not_probe_or_leak():
    owner, uow, objects, asset, scope = _file_owner()

    class Deny:
        def require_read(self, **kwargs):
            raise SupportingFileProtectedNotFound()

        def require_mutation(self, **kwargs):
            raise SupportingFileProtectedNotFound()

    owner.authorization = Deny()
    with pytest.raises(SupportingFileProtectedNotFound):
        owner.read_exact_availability(actor_id=9, scope=scope, asset_id=asset.id)
    with pytest.raises(SupportingFileProtectedNotFound):
        owner.observe_exact_availability(actor_id=9, scope=scope, asset_id=asset.id)
    assert not uow.repository.observations and uow.commits == 0


class _EvidenceRepo:
    def __init__(self, rows, links):
        self.rows, self.links = rows, links
        self.changed = False

    def availability_population(self, **kwargs):
        visible = self._visible(**kwargs)
        return len(visible), self.changed

    def _visible(self, **kwargs):
        rows = [row for row in self.rows if (
                    row.project_id == kwargs["project_id"]
                    or (kwargs["project_wide"] and kwargs["workspace_id"] is None
                        and row.project_id is None))
                and row.created_at <= kwargs["source_cutoff"]]
        if kwargs["workspace_id"] is not None:
            rows = [row for row in rows if row.workspace_id == kwargs["workspace_id"]]
        elif not kwargs["project_wide"]:
            rows = [row for row in rows if row.workspace_id in kwargs["visible_workspaces"]]
        return sorted(rows, key=lambda row: (row.created_at, row.id))

    def list_authorized_availability_page(self, **kwargs):
        rows = self._visible(**kwargs)
        anchor = kwargs["anchor"]
        if anchor is not None:
            rows = [row for row in rows if (row.created_at, row.id) > anchor]
        return rows[:kwargs["limit"]]

    def list_graph_links_for_evidence(self, **kwargs):
        return self.links.get(kwargs["evidence_id"], ())


class _EvidenceUow:
    def __init__(self, repo):
        self.evidence = repo

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class _Visibility:
    def __init__(self, project_wide=False, workspaces=(12,)):
        self.result = project_wide, workspaces

    def availability_scope(self, **kwargs):
        return self.result


class _Facts:
    def __init__(self, states):
        self.states = states

    def read_exact_availability(self, *, asset_id, source_cutoff, **kwargs):
        state = self.states.get(asset_id, "indeterminate")
        return SupportingFileAvailabilityFact(
            asset_id, "version-one", state,
            source_cutoff if state != "indeterminate" else None,
            uuid4() if state != "indeterminate" else None,
            "historical_availability_unproven" if state == "indeterminate" else None,
        )


def _evidence_owner(rows, links, states, *, project_wide=False, workspaces=(12,)):
    repo = _EvidenceRepo(rows, links)
    service = EvidenceAvailabilityService(
        uow_factory=lambda: _EvidenceUow(repo),
        authorization=_Visibility(project_wide, workspaces),
        availability_reader=_Facts(states),
        clock=SimpleNamespace(now=lambda: NOW + timedelta(days=1)),
    )
    return service, repo


def _row(workspace=12):
    return SimpleNamespace(id=uuid4(), version=1, project_id=7,
                           workspace_id=workspace, created_at=NOW - timedelta(days=1))


def test_evidence_link_rules_and_free_form_indeterminate():
    rows = [_row() for _ in range(5)]
    asset_ids = [uuid4() for _ in range(5)]
    links = {
        rows[0].id: (),
        rows[1].id: (SimpleNamespace(asset_id=asset_ids[0]),),
        rows[2].id: (SimpleNamespace(asset_id=asset_ids[1]),
                     SimpleNamespace(asset_id=asset_ids[2])),
        rows[3].id: (SimpleNamespace(asset_id=asset_ids[3]),
                     SimpleNamespace(asset_id=asset_ids[4])),
    }
    states = {asset_ids[0]: "available", asset_ids[1]: "unavailable",
              asset_ids[2]: "unavailable", asset_ids[3]: "unavailable"}
    service, _ = _evidence_owner(rows, links, states)
    page = service.list_page(actor=EvidenceActor(3, uuid4()), project_id=7,
                             workspace_id=12, source_cutoff=NOW)
    found = {item.evidence_id: item for item in page.items}
    assert found[rows[0].id].state == "indeterminate"
    assert found[rows[1].id].state == "available"
    assert found[rows[2].id].state == "unavailable"
    assert found[rows[3].id].state == "indeterminate"
    assert page.traversal_complete and page.next_cursor is None
    states[asset_ids[4]] = "available"
    service, _ = _evidence_owner(rows, links, states)
    page = service.list_page(actor=EvidenceActor(3, uuid4()), project_id=7,
                             workspace_id=12, source_cutoff=NOW)
    assert next(x for x in page.items if x.evidence_id == rows[3].id).state == "available"


def test_visibility_first_keyset_pagination_and_incomplete_traversal():
    actor = EvidenceActor(3, uuid4())
    hidden = [_row(workspace=99) for _ in range(3)]
    visible = [_row(workspace=12) for _ in range(6)]
    for index, row in enumerate([*hidden, *visible]):
        row.created_at = NOW - timedelta(days=1) + timedelta(minutes=index)
    service, repo = _evidence_owner([*hidden, *visible], {}, {})
    cursor, collected = None, []
    while True:
        page = service.list_page(actor=actor, project_id=7, workspace_id=None,
                                 source_cutoff=NOW, page_size=2, cursor=cursor)
        collected.extend(page.items)
        if page.next_cursor is None:
            assert page.traversal_complete
            break
        assert not page.traversal_complete
        cursor = page.next_cursor
    assert {row.evidence_id for row in collected} == {row.id for row in visible}
    assert all(row.state == "indeterminate" for row in collected)
    assert not hasattr(page, "total")
    incomplete = evidence_availability(collected[:2], source_cutoff=NOW,
                                       population_complete=False)
    assert incomplete.denominator is None
    first = service.list_page(actor=actor, project_id=7, workspace_id=None,
                              source_cutoff=NOW, page_size=2)
    changed = "A" if first.next_cursor[10] != "A" else "B"
    with pytest.raises(EvidenceAvailabilityIncomplete):
        service.list_page(actor=actor, project_id=7, workspace_id=None,
                          source_cutoff=NOW, page_size=2,
                          cursor=first.next_cursor[:10] + changed + first.next_cursor[11:])
    repo.changed = True
    with pytest.raises(EvidenceAvailabilityIncomplete):
        service.list_page(actor=actor, project_id=7, workspace_id=None,
                          source_cutoff=NOW, page_size=2, cursor=first.next_cursor)


def test_projectwide_population_keeps_visible_global_evidence_unknown():
    actor = EvidenceActor(4, uuid4())
    global_row = _row(workspace=None)
    global_row.project_id = None
    service, _ = _evidence_owner([global_row], {}, {}, project_wide=True)
    page = service.list_page(actor=actor, project_id=7, workspace_id=None,
                             source_cutoff=NOW)
    assert page.traversal_complete and len(page.items) == 1
    assert page.items[0].project_id is None
    assert page.items[0].state == "indeterminate"


class _SnapshotOwner:
    def __init__(self, states):
        self.states = states
        self.snapshots = {}
        self.items = {}
        self.checked = []
        self.operations = []

    def begin_population_availability_snapshot(self, **values):
        self.operations.append("begin")
        row = SimpleNamespace(
            id=values["snapshot_id"], actor_id=values["actor_id"],
            organization_id=values["scope"].organization_id,
            project_id=values["scope"].project_id,
            workspace_id=values["scope"].workspace_id,
            source_cutoff=values["source_cutoff"], status="incomplete",
            method_version="evidence-availability.v1", limitation_codes=[],
        )
        self.snapshots[row.id] = row
        self.items[row.id] = []
        return row

    def observe_exact_availability_batch(self, *, asset_ids, snapshot_id,
                                         source_cutoff, **kwargs):
        self.operations.append("observe")
        facts = []
        for asset_id in asset_ids:
            checked_at = source_cutoff + timedelta(microseconds=len(self.checked) + 1)
            self.checked.append(checked_at)
            state = self.states.get(asset_id, "indeterminate")
            facts.append(SupportingFileAvailabilityFact(
                asset_id, f"exact-{asset_id}", state,
                source_cutoff if state != "indeterminate" else None,
                uuid4() if state != "indeterminate" else None,
                "probe_indeterminate" if state == "indeterminate" else None,
                checked_at,
            ))
        return tuple(facts)

    def record_population_availability_item(self, *, snapshot_id, **values):
        self.operations.append("item")
        self.items[snapshot_id].append(SimpleNamespace(
            evidence_id=values["evidence_id"],
            evidence_version=values["evidence_version"],
            project_id=values["evidence_project_id"],
            workspace_id=values["evidence_workspace_id"],
            state=values["state"],
            artifact_versions=[[str(asset_id), version] for asset_id, version in values["artifact_versions"]],
            source_event_ids=[str(value) for value in values["source_event_ids"]],
            limitation_codes=list(values["limitations"]),
        ))

    def finalize_population_availability_snapshot(self, *, snapshot_id,
                                                  complete, limitations, **kwargs):
        self.operations.append("finalize")
        row = self.snapshots[snapshot_id]
        row.status = "complete" if complete else "incomplete"
        row.limitation_codes = list(limitations)
        return row

    def read_population_availability_snapshot(self, *, snapshot_id, **kwargs):
        self.operations.append("read")
        return self.snapshots[snapshot_id], tuple(self.items[snapshot_id])


class _SnapshotClock:
    def __init__(self, current=NOW):
        self.current = current

    def now(self):
        value = self.current
        self.current += timedelta(microseconds=1)
        return value


class _TrackedVisibility(_Visibility):
    def __init__(self, result, events):
        self.result = result
        self.events = events

    def availability_scope(self, **kwargs):
        self.events.append("authorize")
        return self.result


class _TrackedEvidenceRepo(_EvidenceRepo):
    def __init__(self, rows, links, events):
        super().__init__(rows, links)
        self.events = events

    def availability_population(self, **kwargs):
        self.events.append("population")
        return super().availability_population(**kwargs)


def _snapshot_service(rows, links, states, *, allowed=True):
    events = []
    repo = _TrackedEvidenceRepo(rows, links, events)
    owner = _SnapshotOwner(states)
    service = EvidenceAvailabilityService(
        uow_factory=lambda: _EvidenceUow(repo),
        authorization=_TrackedVisibility((False, (12,)) if allowed else None, events),
        availability_reader=owner, clock=_SnapshotClock(),
    )
    return service, repo, owner, events


def test_owner_population_snapshot_has_one_cutoff_and_complete_multipage_population():
    rows = [_row() for _ in range(55)]
    assets = [uuid4() for _ in rows]
    links = {row.id: (SimpleNamespace(asset_id=asset_id),)
             for row, asset_id in zip(rows, assets)}
    service, _, owner, events = _snapshot_service(
        rows, links, {asset_id: "available" for asset_id in assets},
    )
    actor = EvidenceActor(3, uuid4())
    snapshot = service.issue_snapshot(actor=actor, project_id=7, workspace_id=12)
    assert snapshot.status == "complete" and len(snapshot.items) == 55
    assert events[0] == "authorize" and events.count("population") == 2
    assert {item.source_cutoff for item in snapshot.items} == {snapshot.source_cutoff}
    assert len(set(owner.checked)) == 55
    assert all(checked > snapshot.source_cutoff for checked in owner.checked)
    assert all(item.artifact_versions[0][1].startswith("exact-") for item in snapshot.items)
    assert owner.operations[0] == "begin" and owner.operations[-1] == "finalize"


def test_snapshot_evidence_rules_preserve_unknown_and_do_not_use_free_form():
    rows = [_row() for _ in range(4)]
    assets = [uuid4() for _ in range(5)]
    links = {
        rows[0].id: (),
        rows[1].id: (SimpleNamespace(asset_id=assets[0]), SimpleNamespace(asset_id=assets[1])),
        rows[2].id: (SimpleNamespace(asset_id=assets[2]), SimpleNamespace(asset_id=assets[3])),
        rows[3].id: (SimpleNamespace(asset_id=assets[3]), SimpleNamespace(asset_id=assets[4])),
    }
    states = {assets[0]: "unavailable", assets[1]: "available",
              assets[2]: "unavailable", assets[3]: "unavailable",
              assets[4]: "indeterminate"}
    service, _, _, _ = _snapshot_service(rows, links, states)
    result = service.issue_snapshot(actor=EvidenceActor(3, uuid4()),
                                    project_id=7, workspace_id=12)
    found = {item.evidence_id: item for item in result.items}
    assert found[rows[0].id].state == "indeterminate"
    assert found[rows[0].id].limitations == ("no_exact_artifact_basis",)
    assert found[rows[1].id].state == "available"
    assert found[rows[2].id].state == "unavailable"
    assert found[rows[3].id].state == "indeterminate"


def test_snapshot_identity_removes_request_time_equality_and_prevents_batch_mixing():
    row, asset = _row(), uuid4()
    service, _, owner, _ = _snapshot_service(
        [row], {row.id: (SimpleNamespace(asset_id=asset),)}, {asset: "available"},
    )
    actor = EvidenceActor(3, uuid4())
    first = service.issue_snapshot(actor=actor, project_id=7, workspace_id=12)
    service.clock.current = first.source_cutoff + timedelta(microseconds=1)
    restored = service.read_snapshot(actor=actor, project_id=7, workspace_id=12,
                                     snapshot_id=first.snapshot_id)
    assert restored.source_cutoff == first.source_cutoff
    assert restored.items[0].state == "available"
    owner.states[asset] = "unavailable"
    second = service.issue_snapshot(actor=actor, project_id=7, workspace_id=12)
    restored_first = service.read_snapshot(actor=actor, project_id=7, workspace_id=12,
                                           snapshot_id=first.snapshot_id)
    assert second.snapshot_id != first.snapshot_id
    assert second.source_cutoff != first.source_cutoff
    assert restored_first.items[0].state == "available"
    assert second.items[0].state == "unavailable"


def test_incomplete_snapshot_never_produces_complete_denominator():
    rows = [_row() for _ in range(5)]
    service, repo, _, _ = _snapshot_service(rows, {}, {})
    repo.changed = True
    snapshot = service.issue_snapshot(actor=EvidenceActor(3, uuid4()),
                                      project_id=7, workspace_id=12)
    assert snapshot.status == "incomplete" and snapshot.items == ()
    result = evidence_availability(snapshot.items, source_cutoff=snapshot.source_cutoff,
                                   population_complete=False)
    assert result.state == "indeterminate" and result.denominator is None


def test_denial_precedes_population_and_discloses_no_count():
    rows = [_row() for _ in range(7)]
    service, _, owner, events = _snapshot_service(rows, {}, {}, allowed=False)
    with pytest.raises(Exception) as caught:
        service.issue_snapshot(actor=EvidenceActor(9, uuid4()),
                               project_id=7, workspace_id=12)
    assert caught.type.__name__ == "EvidenceProtectedNotFound"
    assert events == ["authorize"] and owner.operations == []
