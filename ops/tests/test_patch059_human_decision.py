import copy
import importlib.util
import json
import pathlib

import pytest

SCRIPT = pathlib.Path(__file__).parents[1] / "scripts" / "patch059-human-decision.py"
spec = importlib.util.spec_from_file_location("patch059_human_decision", SCRIPT)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def _policy():
    return json.loads((pathlib.Path(__file__).parents[1] / "patch059-single-human-authority-policy.v1.json").read_text())


def _repo():
    return {"id": m.REPOSITORY_ID, "full_name": m.REPOSITORY}


def _issue():
    return {"number": 59, "repository_url": f"https://api.github.com/repos/{m.REPOSITORY}", "state": "open", "locked": True}


def _comment(cid, actor, created, body):
    return {
        "id": cid, "node_id": f"IC_kwDO_test_{cid}",
        "issue_url": f"https://api.github.com/repos/{m.REPOSITORY}/issues/59",
        "user": actor, "created_at": created, "updated_at": created, "body": body,
    }


def _fixture(tmp_path, seconds=905):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    dig = "sha256:" + "1" * 64
    handoff = {
        "release_id": "r59", "release_sequence": 1, "source_sha": "a" * 40,
        "candidate_run_id": 100, "candidate_run_attempt": 1,
        "workflow_run_id": 200, "workflow_run_attempt": 1,
        "manifest_sha256": None, "signing_authorization_sha256": None,
    }
    for name, obj in (
        ("release-manifest.v1.json", {"x": 1}),
        ("human-signing-authorization.json", {"x": 2}),
    ):
        (bundle / name).write_text(json.dumps(obj) + "\n")
    handoff["manifest_sha256"] = m._digest_file(bundle / "release-manifest.v1.json")
    handoff["signing_authorization_sha256"] = m._digest_file(bundle / "human-signing-authorization.json")
    (bundle / "signed-candidate-handoff.v1.json").write_text(json.dumps(handoff) + "\n")
    marker = {
        "schema": m.MARKER_SCHEMA, "purpose": "signed-handoff-temporal-baseline",
        "repository_id": m.REPOSITORY_ID, "repository": m.REPOSITORY,
        "governance_issue_number": 59, "release_id": "r59", "release_sequence": 1,
        "source_sha": "a" * 40, "candidate_run_id": 100, "candidate_run_attempt": 1,
        "manifest_sha256": handoff["manifest_sha256"],
        "signing_authorization_sha256": handoff["signing_authorization_sha256"],
        "signed_handoff_sha256": m._digest_file(bundle / "signed-candidate-handoff.v1.json"),
        "signing_workflow_run_id": 200, "signing_workflow_run_attempt": 1,
        "nonce": "b" * 64,
    }
    mc = _comment(10, m.MARKER_ACTOR, "2026-10-05T10:00:00Z", m.marker_body(marker))
    approval = {
        "schema": m.APPROVAL_SCHEMA, "purpose": "final-release-human-decision", "decision": "approved",
        "repository_id": m.REPOSITORY_ID, "repository": m.REPOSITORY,
        "governance_issue_number": 59, "release_id": "r59", "release_sequence": 1,
        "source_sha": "a" * 40, "candidate_run_id": 100, "candidate_run_attempt": 1,
        "manifest_sha256": marker["manifest_sha256"],
        "signing_authorization_sha256": marker["signing_authorization_sha256"],
        "signed_handoff_sha256": marker["signed_handoff_sha256"],
        "marker_comment_id": 10, "marker_comment_node_id": mc["node_id"],
        "marker_body_sha256": m._digest_bytes(mc["body"].encode()),
        "marker_created_at": mc["created_at"], "nonce": marker["nonce"],
    }
    minute, second = divmod(seconds, 60)
    created = f"2026-10-05T10:{minute:02d}:{second:02d}Z"
    sig = "-----BEGIN SSH SIGNATURE-----\nZmFrZQ==\n-----END SSH SIGNATURE-----\n"
    ac = _comment(11, m.HUMAN_AUTHORITY, created, m.approval_body(approval, sig))
    event = {"action": "created", "comment": copy.deepcopy(ac), "repository": _repo(), "issue": {"number": 59}}
    return bundle, mc, ac, event


def _verify(tmp_path, monkeypatch, seconds=905, mutate=None):
    bundle, marker, approval, event = _fixture(tmp_path, seconds)
    monkeypatch.setattr(m, "_verify_ssh_signature", lambda *_: None)
    comments = [copy.deepcopy(marker), copy.deepcopy(approval)]
    if mutate:
        mutate(marker, approval, event, comments)
    return m.verify_decision(
        policy=_policy(), repository=_repo(), issue=_issue(), event=event,
        marker_comment=marker, approval_comment=approval, comments=comments, bundle=bundle,
    )


def test_905_seconds_passes(tmp_path, monkeypatch):
    assert _verify(tmp_path, monkeypatch, 905)["elapsed_seconds"] == 905


@pytest.mark.parametrize("seconds", [899, 900, 904])
def test_under_recorded_threshold_fails(tmp_path, monkeypatch, seconds):
    with pytest.raises(m.HumanDecisionError, match="905-second"):
        _verify(tmp_path, monkeypatch, seconds)


def test_wrong_human_fails(tmp_path, monkeypatch):
    def bad(_m, a, e, _c):
        a["user"] = {"login": "other", "id": 9, "type": "User"}
        e["comment"] = copy.deepcopy(a)
    with pytest.raises(m.HumanDecisionError):
        _verify(tmp_path, monkeypatch, mutate=bad)


def test_edited_same_second_fails(tmp_path, monkeypatch):
    def bad(_m, a, e, _c):
        a["updated_at"] = "2026-10-05T10:15:06Z"
        e["comment"] = copy.deepcopy(a)
    with pytest.raises(m.HumanDecisionError):
        _verify(tmp_path, monkeypatch, mutate=bad)


def test_duplicate_nonce_fails(tmp_path, monkeypatch):
    def bad(_m, _a, _e, comments):
        comments.append(copy.deepcopy(comments[0]))
    with pytest.raises(m.HumanDecisionError, match="duplicate"):
        _verify(tmp_path, monkeypatch, mutate=bad)


def test_consumed_nonce_fails(tmp_path, monkeypatch):
    def bad(_m, _a, _e, comments):
        comments.append({"body": m.CONSUMPTION_HEADER + "\n" + ("b" * 64)})
    with pytest.raises(m.HumanDecisionError, match="consumed"):
        _verify(tmp_path, monkeypatch, mutate=bad)


def test_wrong_source_binding_fails(tmp_path, monkeypatch):
    def bad(_m, a, e, _c):
        body = a["body"].replace('"source_sha":"'+("a"*40)+'"', '"source_sha":"'+("c"*40)+'"')
        a["body"] = body
        e["comment"] = copy.deepcopy(a)
    with pytest.raises(m.HumanDecisionError):
        _verify(tmp_path, monkeypatch, mutate=bad)


def test_non_created_event_fails(tmp_path, monkeypatch):
    def bad(_m, _a, e, _c):
        e["action"] = "edited"
    with pytest.raises(m.HumanDecisionError, match="created event"):
        _verify(tmp_path, monkeypatch, mutate=bad)


def test_bad_signature_fails_without_monkeypatch(tmp_path):
    bundle, marker, approval, event = _fixture(tmp_path, 905)
    with pytest.raises(m.HumanDecisionError, match="SSH signature"):
        m.verify_decision(
            policy=_policy(), repository=_repo(), issue=_issue(), event=event,
            marker_comment=marker, approval_comment=approval,
            comments=[marker, approval], bundle=bundle,
        )


def test_malformed_timestamp_fails(tmp_path, monkeypatch):
    def bad(_m, a, e, _c):
        a["created_at"] = a["updated_at"] = "not-a-time"
        e["comment"] = copy.deepcopy(a)
    with pytest.raises(m.HumanDecisionError, match="timestamp"):
        _verify(tmp_path, monkeypatch, mutate=bad)


def _mutate_approval_payload(approval_comment, event, key, value):
    body = approval_comment["body"]
    prefix = m.APPROVAL_HEADER + "\n"
    sig_header = "-----BEGIN SSH SIGNATURE-----\n"
    split = body.index(sig_header)
    payload = json.loads(body[len(prefix):split])
    payload[key] = value
    signature = body[split:]
    approval_comment["body"] = m.approval_body(payload, signature)
    event["comment"] = copy.deepcopy(approval_comment)


@pytest.mark.parametrize("key,value", [
    ("repository_id", 1),
    ("repository", "attacker/fork"),
    ("release_id", "other"),
    ("candidate_run_id", 999),
    ("candidate_run_attempt", 2),
    ("manifest_sha256", "sha256:" + "9" * 64),
    ("signing_authorization_sha256", "sha256:" + "8" * 64),
    ("signed_handoff_sha256", "sha256:" + "7" * 64),
    ("marker_comment_id", 999),
    ("marker_comment_node_id", "wrong"),
    ("marker_body_sha256", "sha256:" + "6" * 64),
    ("nonce", "5" * 64),
])
def test_wrong_purpose_bound_approval_field_fails(tmp_path, monkeypatch, key, value):
    def bad(_marker, approval, event, _comments):
        _mutate_approval_payload(approval, event, key, value)
    with pytest.raises(m.HumanDecisionError):
        _verify(tmp_path, monkeypatch, mutate=bad)


def test_missing_live_marker_fails_closed(tmp_path, monkeypatch):
    def bad(_m, _a, _e, comments):
        comments.pop(0)
    with pytest.raises(m.HumanDecisionError, match="duplicate"):
        _verify(tmp_path, monkeypatch, mutate=bad)


def test_wrong_event_repository_fails(tmp_path, monkeypatch):
    def bad(_m, _a, event, _comments):
        event["repository"] = {"id": 1, "full_name": "attacker/fork"}
    with pytest.raises(m.HumanDecisionError, match="created-event"):
        _verify(tmp_path, monkeypatch, mutate=bad)


def test_more_than_one_hundred_comments_can_be_verified_when_full_listing_is_supplied(tmp_path, monkeypatch):
    bundle, marker, approval, event = _fixture(tmp_path, 905)
    monkeypatch.setattr(m, "_verify_ssh_signature", lambda *_: None)
    comments = [copy.deepcopy(marker), copy.deepcopy(approval)]
    for i in range(150):
        comments.append({"body": f"ordinary unrelated comment {i}"})
    result = m.verify_decision(
        policy=_policy(), repository=_repo(), issue=_issue(), event=event,
        marker_comment=marker, approval_comment=approval, comments=comments, bundle=bundle,
    )
    assert result["elapsed_seconds"] == 905
