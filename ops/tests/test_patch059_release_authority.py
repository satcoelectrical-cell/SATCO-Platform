"""Security tests for PATCH-059 single-Human release authority evidence."""
from __future__ import annotations

import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "patch059_release_authority",
    ROOT / "ops/scripts/patch059-release-evidence.py",
)
assert SPEC and SPEC.loader
authority = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(authority)

REPOSITORY = "satcoelectrical-cell/SATCO-Platform"
SOURCE = "a" * 40
BOT = {
    "status": "CONFIGURED",
    "login": "fixture-dispatcher[bot]",
    "id": 987654,
    "type": "Bot",
    "app_id": 7654,
    "installation_id": 8765,
}
RUN12_FINALIZE_COMMENT = (
    "FINALIZE PATCH-059 "
    "release_id=patch059-predecision-0a3988f-20261006 release_sequence=1 "
    "source_sha=0a3988f661371f4e23d0309b80c7c19d18b7981d "
    "final_decision_comment_id=6023137899 "
    "final_decision_sha256=sha256:2eff69a8d8a56f8c0a7f0a6047e37722968f138b502620a84151cd75f52e01b8 "
    "final_decision_body_sha256=sha256:c9643ca6faf386cc27bf02e32079d449cbb2fa79cdad053f291405b70faa1796"
)


def _run12_approval_history() -> list[dict[str, object]]:
    """Exact field shape returned by Run #12's approvals endpoint."""
    environment = {
        "id": 23459487664,
        "node_id": "EN_kwDOTi8KhM8AAAAFdktfsA",
        "name": "patch059-final-release-approval",
        "url": (
            "https://api.github.com/repos/satcoelectrical-cell/SATCO-Platform/"
            "environments/patch059-final-release-approval"
        ),
        "html_url": (
            "https://github.com/satcoelectrical-cell/SATCO-Platform/deployments/"
            "activity_log?environments_filter=patch059-final-release-approval"
        ),
        "created_at": "2026-10-05T05:38:35Z",
        "updated_at": "2026-10-05T05:38:35Z",
        "can_admins_bypass": False,
    }
    return [
        {
            "user": {
                "login": "github-actions[bot]",
                "id": 41898282,
                "node_id": "MDM6Qm90NDE4OTgyODI=",
                "avatar_url": "https://avatars.githubusercontent.com/in/15368?v=4",
                "gravatar_id": "",
                "url": "https://api.github.com/users/github-actions%5Bbot%5D",
                "html_url": "https://github.com/apps/github-actions",
                "followers_url": "https://api.github.com/users/github-actions%5Bbot%5D/followers",
                "following_url": "https://api.github.com/users/github-actions%5Bbot%5D/following{/other_user}",
                "gists_url": "https://api.github.com/users/github-actions%5Bbot%5D/gists{/gist_id}",
                "starred_url": "https://api.github.com/users/github-actions%5Bbot%5D/starred{/owner}{/repo}",
                "subscriptions_url": "https://api.github.com/users/github-actions%5Bbot%5D/subscriptions",
                "organizations_url": "https://api.github.com/users/github-actions%5Bbot%5D/orgs",
                "repos_url": "https://api.github.com/users/github-actions%5Bbot%5D/repos",
                "events_url": "https://api.github.com/users/github-actions%5Bbot%5D/events{/privacy}",
                "received_events_url": "https://api.github.com/users/github-actions%5Bbot%5D/received_events",
                "type": "Bot",
                "user_view_type": "public",
                "site_admin": False,
            },
            "state": "approved",
            "comment": "15 minute wait timer",
            "environments": [deepcopy(environment)],
        },
        {
            "user": {
                "login": "samiphone651-sys",
                "id": 301386823,
                "node_id": "U_kgDOEfbMRw",
                "avatar_url": "https://avatars.githubusercontent.com/u/301386823?v=4",
                "gravatar_id": "",
                "url": "https://api.github.com/users/samiphone651-sys",
                "html_url": "https://github.com/samiphone651-sys",
                "followers_url": "https://api.github.com/users/samiphone651-sys/followers",
                "following_url": "https://api.github.com/users/samiphone651-sys/following{/other_user}",
                "gists_url": "https://api.github.com/users/samiphone651-sys/gists{/gist_id}",
                "starred_url": "https://api.github.com/users/samiphone651-sys/starred{/owner}{/repo}",
                "subscriptions_url": "https://api.github.com/users/samiphone651-sys/subscriptions",
                "organizations_url": "https://api.github.com/users/samiphone651-sys/orgs",
                "repos_url": "https://api.github.com/users/samiphone651-sys/repos",
                "events_url": "https://api.github.com/users/samiphone651-sys/events{/privacy}",
                "received_events_url": "https://api.github.com/users/samiphone651-sys/received_events",
                "type": "User",
                "user_view_type": "public",
                "site_admin": False,
            },
            "state": "approved",
            "comment": RUN12_FINALIZE_COMMENT,
            "environments": [deepcopy(environment)],
        },
    ]


def _example_policy() -> dict[str, object]:
    return json.loads(
        (ROOT / "ops/patch059-single-human-authority-policy.example.v1.json")
        .read_text(encoding="utf-8")
    )


def _policy() -> dict[str, object]:
    policy = _example_policy()
    policy["dispatcher"] = deepcopy(BOT)
    return policy


def _run() -> dict[str, object]:
    actor = {"login": BOT["login"], "id": BOT["id"], "type": "Bot"}
    return {
        "id": 456789,
        "run_attempt": 1,
        "path": ".github/workflows/patch059-sign-release.yml",
        "event": "workflow_dispatch",
        "head_branch": "patch-059-implementation",
        "head_sha": SOURCE,
        "html_url": f"https://github.com/{REPOSITORY}/actions/runs/456789",
        "repository": {"full_name": REPOSITORY},
        "head_repository": {"full_name": REPOSITORY},
        "actor": deepcopy(actor),
        "triggering_actor": deepcopy(actor),
    }


def _environment(stage: str) -> tuple[dict[str, object], dict[str, object]]:
    final = stage == "final"
    name = "patch059-final-release-approval" if final else "patch058-protected-release"
    branches = ["patch-059-implementation"] if final else ["patch-058", "patch-059-implementation"]
    rules: list[dict[str, object]] = [
        {
            "type": "required_reviewers",
            "prevent_self_review": True,
            "reviewers": [
                {
                    "type": "User",
                    "reviewer": deepcopy(authority.HUMAN_AUTHORITY),
                }
            ],
        },
        {"type": "branch_policy"},
    ]
    if final:
        rules.append({"type": "wait_timer", "wait_timer": 15})
    environment = {
        "name": name,
        "can_admins_bypass": False,
        "deployment_branch_policy": {
            "protected_branches": False,
            "custom_branch_policies": True,
        },
        "protection_rules": rules,
    }
    branch_policies = {
        "total_count": len(branches),
        "branch_policies": [
            {"id": index, "node_id": f"node-{index}", "name": branch, "type": "branch"}
            for index, branch in enumerate(branches, start=1)
        ],
    }
    return environment, branch_policies


def test_unresolved_policy_is_documented_but_fails_the_execution_gate():
    policy = _example_policy()
    validated = authority.validate_authority_policy(
        policy, repository=REPOSITORY, require_configured=False
    )
    assert validated["human_authority"] == {
        "login": "samiphone651-sys",
        "id": 301386823,
        "type": "User",
    }
    assert validated["claims"] == {
        "personnel_independence": False,
        "dual_human_control": False,
        "quorum": False,
    }
    with pytest.raises(authority.ReleaseVerificationError, match="dispatcher identity unresolved"):
        authority.validate_authority_policy(
            policy, repository=REPOSITORY, require_configured=True
        )


def test_configured_non_human_dispatcher_and_exact_run_are_accepted():
    policy = authority.validate_authority_policy(
        _policy(), repository=REPOSITORY, require_configured=True
    )
    assert authority.validate_protected_run(
        policy, _run(), repository=REPOSITORY, source_sha=SOURCE
    )["attempt"] == 1


@pytest.mark.parametrize(("key", "value"), [("login", "samiphone651-sys"), ("id", 301386823)])
def test_policy_rejects_human_authority_as_configured_dispatcher(key, value):
    policy = _policy()
    policy["dispatcher"][key] = value
    with pytest.raises(
        authority.ReleaseVerificationError,
        match="Human Authority cannot be dispatcher",
    ):
        authority.validate_authority_policy(
            policy, repository=REPOSITORY, require_configured=True
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("run_attempt", 2),
        ("event", "push"),
        ("head_branch", "main"),
        ("head_sha", "b" * 40),
        ("actor", {"login": "samiphone651-sys", "id": 301386823, "type": "User"}),
        ("triggering_actor", {"login": "someone-else[bot]", "id": 2, "type": "Bot"}),
    ],
)
def test_protected_run_rejects_reruns_wrong_source_and_wrong_dispatcher(field, value):
    run = _run()
    run[field] = value
    with pytest.raises(authority.ReleaseVerificationError):
        authority.validate_protected_run(
            _policy(), run, repository=REPOSITORY, source_sha=SOURCE
        )


@pytest.mark.parametrize("stage", ["signing", "final"])
def test_exact_environment_policy_is_accepted(stage):
    environment, branches = _environment(stage)
    authority.validate_environment_policy(
        _policy(), environment, branches, stage=stage
    )


@pytest.mark.parametrize(
    ("stage", "mutation"),
    [
        ("signing", "self_review"),
        ("signing", "admin_bypass"),
        ("signing", "wrong_reviewer"),
        ("signing", "wrong_branch"),
        ("final", "missing_timer"),
        ("final", "wrong_timer"),
    ],
)
def test_environment_policy_fails_closed(stage, mutation):
    environment, branches = _environment(stage)
    if mutation == "self_review":
        environment["protection_rules"][0]["prevent_self_review"] = False
    elif mutation == "admin_bypass":
        environment["can_admins_bypass"] = True
    elif mutation == "wrong_reviewer":
        environment["protection_rules"][0]["reviewers"][0]["reviewer"]["id"] = 1
    elif mutation == "wrong_branch":
        branches["branch_policies"][0]["name"] = "main"
    elif mutation == "missing_timer":
        environment["protection_rules"] = environment["protection_rules"][:-1]
    else:
        environment["protection_rules"][-1]["wait_timer"] = 14
    with pytest.raises(authority.ReleaseVerificationError):
        authority.validate_environment_policy(
            _policy(), environment, branches, stage=stage
        )


def test_approval_event_is_exactly_attributable_and_purpose_bound():
    comment = "SIGN fixture"
    history = [
        {
            "state": "approved",
            "comment": comment,
            "submitted_at": "2026-10-03T10:00:00Z",
            "user": deepcopy(authority.HUMAN_AUTHORITY),
            "environments": [{"name": "patch058-protected-release"}],
        }
    ]
    event = authority._approval_event(
        _policy(), history, stage="signing", expected_comment=comment
    )
    assert event["reviewer"] == authority.HUMAN_AUTHORITY
    history[0]["comment"] = "FINAL fixture"
    with pytest.raises(authority.ReleaseVerificationError):
        authority._approval_event(
            _policy(), history, stage="signing", expected_comment=comment
        )


def test_run12_human_approval_and_github_wait_timer_are_accepted():
    event = authority._approval_event(
        _policy(),
        _run12_approval_history(),
        stage="final",
        expected_comment=RUN12_FINALIZE_COMMENT,
    )
    assert event["reviewer"] == authority.HUMAN_AUTHORITY
    assert event["comment"] == RUN12_FINALIZE_COMMENT
    assert event["environment"] == "patch059-final-release-approval"


def test_run12_shape_without_human_approval_is_rejected():
    history = _run12_approval_history()[:1]
    with pytest.raises(
        authority.ReleaseVerificationError,
        match="one distinct Human approved Environment event required",
    ):
        authority._approval_event(
            _policy(), history, stage="final", expected_comment=RUN12_FINALIZE_COMMENT
        )


def test_run12_shape_without_github_wait_timer_is_rejected():
    history = _run12_approval_history()[1:]
    with pytest.raises(
        authority.ReleaseVerificationError,
        match="one distinct GitHub wait-timer approval event required",
    ):
        authority._approval_event(
            _policy(), history, stage="final", expected_comment=RUN12_FINALIZE_COMMENT
        )


def test_run12_shape_with_duplicate_github_wait_timer_is_rejected():
    history = _run12_approval_history()
    history.append(deepcopy(history[0]))
    with pytest.raises(
        authority.ReleaseVerificationError,
        match="one distinct GitHub wait-timer approval event required",
    ):
        authority._approval_event(
            _policy(), history, stage="final", expected_comment=RUN12_FINALIZE_COMMENT
        )


def test_run12_shape_with_unauthorized_user_approval_is_rejected():
    history = _run12_approval_history()
    history[1]["user"] = {"login": "attacker", "id": 1, "type": "User"}
    with pytest.raises(
        authority.ReleaseVerificationError, match="unexpected Environment approval actor"
    ):
        authority._approval_event(
            _policy(), history, stage="final", expected_comment=RUN12_FINALIZE_COMMENT
        )


def test_run12_shape_with_multiple_human_approvals_is_rejected():
    history = _run12_approval_history()
    duplicate = deepcopy(history[1])
    duplicate["comment"] = "second Human approval event"
    history.append(duplicate)
    with pytest.raises(
        authority.ReleaseVerificationError,
        match="one distinct Human approved Environment event required",
    ):
        authority._approval_event(
            _policy(), history, stage="final", expected_comment=RUN12_FINALIZE_COMMENT
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("comment", "14 minute wait timer", "invalid GitHub wait-timer approval event"),
        ("state", "pending", "non-approved Environment event"),
        ("user", {"login": "github-actions[bot]", "id": 1, "type": "Bot"},
         "unexpected Environment approval actor"),
    ],
)
def test_run12_shape_with_malformed_or_spoofed_timer_is_rejected(
    field, value, message
):
    history = _run12_approval_history()
    history[0][field] = value
    with pytest.raises(authority.ReleaseVerificationError, match=message):
        authority._approval_event(
            _policy(), history, stage="final", expected_comment=RUN12_FINALIZE_COMMENT
        )


def test_run12_shape_with_wrong_human_environment_is_rejected():
    history = _run12_approval_history()
    history[1]["environments"][0]["name"] = "production"
    with pytest.raises(
        authority.ReleaseVerificationError,
        match="one distinct Human approved Environment event required",
    ):
        authority._approval_event(
            _policy(), history, stage="final", expected_comment=RUN12_FINALIZE_COMMENT
        )


@pytest.mark.parametrize("comment", [None, "FINALIZE PATCH-059 wrong"])
def test_run12_shape_with_missing_or_wrong_finalize_comment_is_rejected(comment):
    history = _run12_approval_history()
    history[1]["comment"] = comment
    with pytest.raises(authority.ReleaseVerificationError, match="approval evidence mismatch"):
        authority._approval_event(
            _policy(), history, stage="final", expected_comment=RUN12_FINALIZE_COMMENT
        )


def test_environment_approval_without_submitted_at_is_authenticated_without_inventing_time():
    policy = _policy()
    comment = "SIGN PATCH-059 release_id=r source_sha=" + ("a" * 40) + " candidate_run_id=1 candidate_run_attempt=1"
    history = [{
        "state": "approved", "comment": comment, "user": deepcopy(authority.HUMAN_AUTHORITY),
        "environments": [{"name": "patch058-protected-release"}],
    }]
    event = authority._approval_event(policy, history, stage="signing", expected_comment=comment)
    assert "submitted_at" not in event
    assert event["reviewer"] == authority.HUMAN_AUTHORITY


def test_environment_approval_does_not_accept_runner_time_as_human_time():
    policy = _policy()
    comment = "SIGN PATCH-059 release_id=r source_sha=" + ("a" * 40) + " candidate_run_id=1 candidate_run_attempt=1"
    history = [{
        "state": "approved", "comment": comment, "user": deepcopy(authority.HUMAN_AUTHORITY),
        "runner_local_time": "2099-01-01T00:00:00Z",
        "environments": [{"name": "patch058-protected-release"}],
    }]
    event = authority._approval_event(policy, history, stage="signing", expected_comment=comment)
    assert "submitted_at" not in event
    assert "runner_local_time" not in event
