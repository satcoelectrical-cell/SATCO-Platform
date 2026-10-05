#!/usr/bin/env python3
"""Pinned offline verifier for ADR-032 PATCH-059 release-ready bundles."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import stat
import subprocess
import sys
from typing import Any, Callable


MANIFEST_SCHEMA = "satco.patch059-release-manifest/v1"
POLICY_SCHEMA = "satco.patch059-single-human-authority-policy/v1"
SIGNING_AUTHORIZATION_SCHEMA = "satco.patch059-human-signing-authorization/v2"
HANDOFF_SCHEMA = "satco.patch059-signed-candidate-handoff/v1"
APPROVAL_SCHEMA = "satco.patch059-human-release-approval/v2"
FINALIZATION_SCHEMA = "satco.patch059-release-finalization/v2"
OPERATING_MODE = "single-human-authority"
HUMAN_AUTHORITY = {"login": "samiphone651-sys", "id": 301386823, "type": "User"}
SIGNING_ENVIRONMENT = "patch058-protected-release"
FINAL_APPROVAL_ENVIRONMENT = "patch059-final-release-approval"
CANDIDATE_SCHEMA = "satco.patch059-candidate-evidence/v2"
CANDIDATE_WORKFLOW_PATH = ".github/workflows/patch059-candidate-evidence.yml"
SIGNING_WORKFLOW_PATH = ".github/workflows/patch059-sign-release.yml"
CANDIDATE_EVENT = "workflow_dispatch"
CANDIDATE_BRANCH = "patch-059-implementation"
MINIMUM_FINAL_APPROVAL_DELAY_SECONDS = 900
SHA256 = re.compile(r"sha256:[0-9a-f]{64}\Z")
RAW_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
SOURCE_SHA = re.compile(r"[0-9a-f]{40}\Z")
RELEASE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
ARTIFACT_FILES = {
    "backend": "backend-image.oci.tar",
    "frontend": "frontend-dist.tar",
    "migrations": "migration-set.tar",
}
SIGNED_FILES = {
    **ARTIFACT_FILES,
    "manifest": "release-manifest.v1.json",
    "approval": "human-release-approval.json",
    "finalization": "release-finalization.v2.json",
}
DOSSIER_SECTION_FILES = {
    "artifacts": ARTIFACT_FILES,
    "build_inputs": {
        "backend-production-lock": "backend-production.lock",
        "backend-uv-lock": "backend-uv.lock",
        "frontend-package-lock": "frontend-package-lock.json",
        "migration-set": "migration-set.sha256",
    },
    "qualification_evidence": {
        "backend": "backend-qualification.json",
        "frontend": "frontend-qualification.json",
        "migration": "migration-qualification.json",
    },
    "security_evidence": {
        "pip-audit": "pip-audit.json",
        "npm-audit": "npm-audit.json",
        "semgrep": "semgrep.json",
        "gitleaks": "gitleaks.json",
        "trivy": "trivy-backend.json",
        "vulnerability_gate": "vulnerability-gate.json",
    },
    "exceptions": {
        "high_findings": "resolved-high-exceptions.json",
        "security_decision": "security-decision.json",
    },
    "sboms": {
        "backend": "backend-sbom.cdx.json",
        "frontend": "frontend-sbom.cdx.json",
    },
}
DOSSIER_KEYS = {
    "schema_version", "release_id", "source_commit", "artifacts",
    "build_inputs", "qualification_evidence", "security_evidence",
    "exceptions", "sboms", "provenance", "signature_verification",
    "human_signing_authorization", "human_release_approval", "created_at",
}
PRE_DECISION_PROVENANCE_FILES = {
    "pre-decision-evidence": "pre-decision-evidence.json",
    "pre-decision-artifact": "pre-decision-artifact.json",
    "pre-decision-run": "pre-decision-run.json",
    "pre-decision-artifact-api": "pre-decision-artifact-api.json",
}


class ReleaseVerificationError(ValueError):
    pass


def _load(path: pathlib.Path) -> object:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                raise ReleaseVerificationError("duplicate JSON member")
            result[key] = value
        return result

    def reject_constant(_value: str) -> None:
        raise ReleaseVerificationError("non-I-JSON constant")

    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_size > 8 * 1024 * 1024
        ):
            raise ReleaseVerificationError("unsafe evidence file")
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            raw = stream.read(8 * 1024 * 1024 + 1)
        if len(raw) > 8 * 1024 * 1024:
            raise ReleaseVerificationError("oversized evidence file")
        return json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=pairs,
            parse_constant=reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseVerificationError("invalid evidence JSON") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _digest(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ReleaseVerificationError("unsafe release subject")
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ReleaseVerificationError("missing release subject") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    return "sha256:" + digest.hexdigest()


def _time(value: object) -> dt.datetime:
    if not isinstance(value, str):
        raise ReleaseVerificationError("invalid timestamp")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReleaseVerificationError("invalid timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ReleaseVerificationError("naive timestamp")
    return parsed.astimezone(dt.timezone.utc)


def _release_id(value: object) -> str:
    if not isinstance(value, str) or not RELEASE_ID.fullmatch(value):
        raise ReleaseVerificationError("invalid release ID")
    return value


def _closed(document: object, keys: set[str], schema: str) -> dict[str, object]:
    if (
        not isinstance(document, dict)
        or set(document) != keys
        or document.get("schema") != schema
    ):
        raise ReleaseVerificationError("closed evidence schema mismatch")
    return document


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _verify_pre_decision_custody(
    root: pathlib.Path, *, repository: str, source_sha: str, release_id: str
) -> None:
    script = pathlib.Path(__file__).with_name("patch059-candidate-evidence.py")
    spec = importlib.util.spec_from_file_location("patch059_candidate_evidence", script)
    if spec is None or spec.loader is None:
        raise ReleaseVerificationError("pre-decision verifier unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        module.verify_pre_decision_custody(
            identity=_load(root / "pre-decision-artifact.json"),
            evidence=_load(root / "pre-decision-evidence.json"),
            run=_load(root / "pre-decision-run.json"),
            artifact=_load(root / "pre-decision-artifact-api.json"),
            repository=repository,
            source_sha=source_sha,
            release_id=release_id,
            archive_path=root / "pre-decision-artifact.zip",
            bundle=root,
        )
    except (OSError, module.CandidateEvidenceError) as exc:
        raise ReleaseVerificationError("pre-decision custody mismatch") from exc


def validate_authority_policy(
    policy: object, *, repository: str, require_configured: bool = True
) -> dict[str, object]:
    keys = {
        "schema", "mode", "repository", "branch", "workflow_path",
        "human_authority", "dispatcher", "signing_environment",
        "final_environment", "minimum_final_approval_delay_seconds", "claims",
    }
    document = _closed(policy, keys, POLICY_SCHEMA)
    if (
        document.get("mode") != OPERATING_MODE
        or document.get("repository") != repository
        or document.get("branch") != CANDIDATE_BRANCH
        or document.get("workflow_path") != SIGNING_WORKFLOW_PATH
        or document.get("human_authority") != HUMAN_AUTHORITY
        or document.get("minimum_final_approval_delay_seconds")
        != MINIMUM_FINAL_APPROVAL_DELAY_SECONDS
        or document.get("claims")
        != {
            "personnel_independence": False,
            "dual_human_control": False,
            "quorum": False,
        }
    ):
        raise ReleaseVerificationError("authority policy mismatch")
    dispatcher = document.get("dispatcher")
    if not isinstance(dispatcher, dict) or set(dispatcher) != {
        "status", "login", "id", "type", "app_id", "installation_id"
    } or dispatcher.get("type") != "Bot":
        raise ReleaseVerificationError("dispatcher policy mismatch")
    status = dispatcher.get("status")
    if status == "CONFIGURED":
        for key in ("id", "app_id", "installation_id"):
            if type(dispatcher.get(key)) is not int or dispatcher[key] < 1:
                raise ReleaseVerificationError("invalid configured dispatcher")
        if not isinstance(dispatcher.get("login"), str) or not dispatcher["login"]:
            raise ReleaseVerificationError("invalid configured dispatcher")
        if (
            dispatcher["login"] == HUMAN_AUTHORITY["login"]
            or dispatcher["id"] == HUMAN_AUTHORITY["id"]
        ):
            raise ReleaseVerificationError("Human Authority cannot be dispatcher")
    elif status == "UNRESOLVED":
        if any(
            dispatcher.get(key) is not None
            for key in ("login", "id", "app_id", "installation_id")
        ):
            raise ReleaseVerificationError("invalid unresolved dispatcher")
        if require_configured:
            raise ReleaseVerificationError("dispatcher identity unresolved")
    else:
        raise ReleaseVerificationError("dispatcher policy mismatch")
    expected_environments = {
        "signing_environment": {
            "name": SIGNING_ENVIRONMENT,
            "reviewers": [HUMAN_AUTHORITY],
            "prevent_self_review": True,
            "can_admins_bypass": False,
            "branches": ["patch-058", CANDIDATE_BRANCH],
        },
        "final_environment": {
            "name": FINAL_APPROVAL_ENVIRONMENT,
            "reviewers": [HUMAN_AUTHORITY],
            "prevent_self_review": True,
            "can_admins_bypass": False,
            "branches": [CANDIDATE_BRANCH],
            "wait_timer_minutes": 15,
        },
    }
    for key, expected in expected_environments.items():
        if document.get(key) != expected:
            raise ReleaseVerificationError(f"{key} policy mismatch")
    return document


def _api_actor(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ReleaseVerificationError("workflow actor missing")
    actor = {"login": value.get("login"), "id": value.get("id"), "type": value.get("type")}
    if (
        not isinstance(actor["login"], str)
        or not actor["login"]
        or type(actor["id"]) is not int
        or actor["id"] < 1
        or actor["type"] not in {"User", "Bot"}
    ):
        raise ReleaseVerificationError("invalid workflow actor")
    return actor


def validate_protected_run(
    policy: dict[str, object],
    run: object,
    *,
    repository: str,
    source_sha: str,
) -> dict[str, object]:
    validate_authority_policy(policy, repository=repository, require_configured=True)
    if not SOURCE_SHA.fullmatch(source_sha):
        raise ReleaseVerificationError("invalid protected-run source")
    if not isinstance(run, dict):
        raise ReleaseVerificationError("invalid workflow run response")
    expected_url = f"https://github.com/{repository}/actions/runs/{run.get('id')}"
    expected = {
        "run_attempt": 1,
        "path": SIGNING_WORKFLOW_PATH,
        "event": "workflow_dispatch",
        "head_branch": CANDIDATE_BRANCH,
        "head_sha": source_sha,
        "html_url": expected_url,
    }
    if type(run.get("id")) is not int or run["id"] < 1:
        raise ReleaseVerificationError("invalid protected run ID")
    for key, value in expected.items():
        if run.get(key) != value:
            raise ReleaseVerificationError(f"protected run {key} mismatch")
    for key in ("repository", "head_repository"):
        value = run.get(key)
        if not isinstance(value, dict) or value.get("full_name") != repository:
            raise ReleaseVerificationError(f"protected run {key} mismatch")
    dispatcher = policy["dispatcher"]
    expected_actor = {
        "login": dispatcher["login"],  # type: ignore[index]
        "id": dispatcher["id"],  # type: ignore[index]
        "type": "Bot",
    }
    actor = _api_actor(run.get("actor"))
    triggering_actor = _api_actor(run.get("triggering_actor"))
    if actor != expected_actor or triggering_actor != expected_actor:
        raise ReleaseVerificationError("protected run dispatcher mismatch")
    if actor == HUMAN_AUTHORITY or triggering_actor == HUMAN_AUTHORITY:
        raise ReleaseVerificationError("Human-dispatched protected run")
    return {
        "id": run["id"],
        "attempt": run["run_attempt"],
        "url": run["html_url"],
        "actor": actor,
        "triggering_actor": triggering_actor,
    }


def validate_environment_policy(
    policy: dict[str, object],
    environment: object,
    branch_policies: object,
    *,
    stage: str,
) -> None:
    key = "signing_environment" if stage == "signing" else "final_environment"
    expected = policy[key]
    if not isinstance(expected, dict) or not isinstance(environment, dict):
        raise ReleaseVerificationError("invalid Environment policy")
    if (
        environment.get("name") != expected["name"]
        or environment.get("can_admins_bypass") is not False
        or environment.get("deployment_branch_policy")
        != {"protected_branches": False, "custom_branch_policies": True}
    ):
        raise ReleaseVerificationError("Environment policy mismatch")
    rules = environment.get("protection_rules")
    if not isinstance(rules, list):
        raise ReleaseVerificationError("Environment protection rules missing")
    reviewers = [rule for rule in rules if isinstance(rule, dict) and rule.get("type") == "required_reviewers"]
    if len(reviewers) != 1 or reviewers[0].get("prevent_self_review") is not True:
        raise ReleaseVerificationError("Environment reviewer policy mismatch")
    raw_reviewers = reviewers[0].get("reviewers")
    if not isinstance(raw_reviewers, list) or len(raw_reviewers) != 1:
        raise ReleaseVerificationError("Environment reviewer mismatch")
    raw = raw_reviewers[0]
    reviewer = raw.get("reviewer") if isinstance(raw, dict) else None
    if (
        not isinstance(raw, dict)
        or raw.get("type") != "User"
        or not isinstance(reviewer, dict)
        or {"login": reviewer.get("login"), "id": reviewer.get("id"), "type": reviewer.get("type")}
        != HUMAN_AUTHORITY
    ):
        raise ReleaseVerificationError("Environment reviewer mismatch")
    timers = [rule for rule in rules if isinstance(rule, dict) and rule.get("type") == "wait_timer"]
    if stage == "final":
        if len(timers) != 1 or timers[0].get("wait_timer") != 15:
            raise ReleaseVerificationError("final Environment wait timer mismatch")
    elif timers:
        raise ReleaseVerificationError("unexpected signing Environment wait timer")
    allowed_types = {"required_reviewers", "branch_policy"}
    if stage == "final":
        allowed_types.add("wait_timer")
    if any(not isinstance(rule, dict) or rule.get("type") not in allowed_types for rule in rules):
        raise ReleaseVerificationError("unexpected Environment protection rule")
    if not isinstance(branch_policies, dict) or set(branch_policies) != {"total_count", "branch_policies"}:
        raise ReleaseVerificationError("invalid Environment branch policy response")
    values = branch_policies.get("branch_policies")
    if not isinstance(values, list):
        raise ReleaseVerificationError("Environment branch policies missing")
    if any(
        not isinstance(item, dict)
        or set(item) != {"id", "node_id", "name", "type"}
        or item.get("type") != "branch"
        or not isinstance(item.get("name"), str)
        for item in values
    ):
        raise ReleaseVerificationError("invalid Environment branch policy")
    branches = sorted(item["name"] for item in values)
    if (
        type(branch_policies.get("total_count")) is not int
        or branch_policies.get("total_count") != len(values)
        or branches != sorted(expected["branches"])
    ):
        raise ReleaseVerificationError("Environment branch restriction mismatch")


def _approval_event(
    policy: dict[str, object],
    history: object,
    *,
    stage: str,
    expected_comment: str,
) -> dict[str, object]:
    key = "signing_environment" if stage == "signing" else "final_environment"
    environment_name = policy[key]["name"]  # type: ignore[index]
    if not isinstance(history, list):
        raise ReleaseVerificationError("invalid approval history")
    events = []
    for item in history:
        environments = item.get("environments") if isinstance(item, dict) else None
        if not isinstance(environments, list):
            raise ReleaseVerificationError("invalid approval history event")
        if any(
            isinstance(env, dict) and env.get("name") == environment_name
            for env in environments
        ):
            events.append(item)
    if len(events) != 1 or events[0].get("state") != "approved":
        raise ReleaseVerificationError("one distinct approved Environment event required")
    event = events[0]
    reviewer = _api_actor(event.get("user"))
    if reviewer != HUMAN_AUTHORITY or event.get("comment") != expected_comment:
        raise ReleaseVerificationError("approval evidence mismatch")
    submitted_at = event.get("submitted_at")
    _time(submitted_at)
    canonical = {
        "decision": "approved",
        "comment": expected_comment,
        "submitted_at": submitted_at,
        "environment": environment_name,
        "reviewer": reviewer,
    }
    return {**canonical, "digest": _canonical_digest(canonical)}


def validate_signing_job_result(
    response: object, *, run_id: int, source_sha: str
) -> dict[str, object]:
    if not isinstance(response, dict) or not isinstance(response.get("jobs"), list):
        raise ReleaseVerificationError("invalid workflow-jobs response")
    jobs = response["jobs"]
    matches = [
        job
        for job in jobs
        if isinstance(job, dict)
        and job.get("name") == "sign-candidate"
        and job.get("run_id") == run_id
    ]
    if (
        type(response.get("total_count")) is not int
        or response["total_count"] != len(jobs)
        or len(matches) != 1
    ):
        raise ReleaseVerificationError("signing job result missing or ambiguous")
    job = matches[0]
    if (
        job.get("status") != "completed"
        or job.get("conclusion") != "success"
        or job.get("head_sha") != source_sha
        or job.get("run_attempt") != 1
    ):
        raise ReleaseVerificationError("signing job did not complete successfully")
    return {
        "id": job.get("id"),
        "name": "sign-candidate",
        "result": "success",
    }


def _subjects(statement: object) -> dict[str, str]:
    if not isinstance(statement, dict):
        raise ReleaseVerificationError("invalid provenance")
    result: dict[str, str] = {}
    for subject in statement.get("subject", []):
        if (
            not isinstance(subject, dict)
            or set(subject) != {"name", "digest"}
            or not isinstance(subject["digest"], dict)
            or set(subject["digest"]) != {"sha256"}
            or subject["name"] in result
        ):
            raise ReleaseVerificationError("invalid provenance subjects")
        digest = "sha256:" + str(subject["digest"]["sha256"])
        if not SHA256.fullmatch(digest):
            raise ReleaseVerificationError("invalid provenance digest")
        result[str(subject["name"])] = digest
    return result


def _descriptor_digest(dossier: dict[str, object], section: str, name: str) -> str:
    try:
        descriptor = dossier[section][name]  # type: ignore[index]
    except (KeyError, TypeError) as exc:
        raise ReleaseVerificationError("incomplete dossier") from exc
    if not isinstance(descriptor, dict) or not SHA256.fullmatch(
        str(descriptor.get("digest", ""))
    ):
        raise ReleaseVerificationError("invalid dossier descriptor")
    return str(descriptor["digest"])


def _verify_descriptor(
    root: pathlib.Path,
    descriptor: object,
    expected_filename: str,
    *,
    status: str | None = None,
) -> str:
    expected_keys = {"reference", "digest"}
    if status is not None:
        expected_keys.add("status")
    if (
        not isinstance(descriptor, dict)
        or set(descriptor) != expected_keys
        or descriptor.get("reference") != expected_filename
        or (status is not None and descriptor.get("status") != status)
    ):
        raise ReleaseVerificationError("invalid dossier descriptor")
    digest = str(descriptor.get("digest", ""))
    if not SHA256.fullmatch(digest):
        raise ReleaseVerificationError("invalid dossier descriptor")
    path = root / expected_filename
    if path.parent != root or _digest(path) != digest:
        raise ReleaseVerificationError("missing or substituted dossier evidence")
    return digest


def create_signing_authorization(
    *,
    policy_path: pathlib.Path,
    run_path: pathlib.Path,
    environment_path: pathlib.Path,
    branch_policies_path: pathlib.Path,
    approvals_path: pathlib.Path,
    bundle: pathlib.Path,
    repository: str,
    release_id: str,
    source_sha: str,
) -> dict[str, object]:
    _release_id(release_id)
    policy = validate_authority_policy(
        _load(policy_path), repository=repository, require_configured=True
    )
    run = validate_protected_run(
        policy, _load(run_path), repository=repository, source_sha=source_sha
    )
    validate_environment_policy(
        policy,
        _load(environment_path),
        _load(branch_policies_path),
        stage="signing",
    )
    root = bundle.resolve(strict=True)
    candidate_path = root / "candidate-identity.json"
    candidate = _load(candidate_path)
    candidate = _closed(
        candidate,
        {
            "schema", "repository", "workflow_ref", "workflow_path", "event",
            "branch", "source_sha", "release_id", "run_id", "run_attempt",
            "run_url", "actor", "triggering_actor", "security_decision_commit",
            "security_decision_sha256",
        },
        CANDIDATE_SCHEMA,
    )
    expected_candidate_workflow = (
        f"https://github.com/{repository}/{CANDIDATE_WORKFLOW_PATH}"
        f"@refs/heads/{CANDIDATE_BRANCH}"
    )
    if (
        candidate.get("repository") != repository
        or candidate.get("workflow_ref") != expected_candidate_workflow
        or candidate.get("workflow_path") != CANDIDATE_WORKFLOW_PATH
        or candidate.get("event") != CANDIDATE_EVENT
        or candidate.get("branch") != CANDIDATE_BRANCH
        or candidate.get("source_sha") != source_sha
        or candidate.get("release_id") != release_id
        or type(candidate.get("run_id")) is not int
        or candidate["run_id"] < 1
        or type(candidate.get("run_attempt")) is not int
        or candidate["run_attempt"] < 1
        or candidate.get("run_url")
        != f"https://github.com/{repository}/actions/runs/{candidate['run_id']}"
        or any(
            not isinstance(candidate.get(key), dict)
            or set(candidate[key]) != {"login", "id", "type"}
            or _api_actor(candidate[key]) != candidate[key]
            for key in ("actor", "triggering_actor")
        )
        or not SOURCE_SHA.fullmatch(
            str(candidate.get("security_decision_commit", ""))
        )
        or not SHA256.fullmatch(
            str(candidate.get("security_decision_sha256", ""))
        )
    ):
        raise ReleaseVerificationError("candidate authorization identity mismatch")
    decision_path = root / "security-decision.json"
    decision = _load(decision_path)
    if (
        not isinstance(decision, dict)
        or candidate.get("security_decision_commit") != decision.get("decisionCommit")
        or candidate.get("security_decision_sha256") != _digest(decision_path)
    ):
        raise ReleaseVerificationError("candidate security decision mismatch")
    artifacts = {
        name: _digest(root / filename) for name, filename in ARTIFACT_FILES.items()
    }
    comment = (
        f"SIGN PATCH-059 release_id={release_id} source_sha={source_sha} "
        f"candidate_run_id={candidate['run_id']} "
        f"candidate_run_attempt={candidate['run_attempt']}"
    )
    approval = _approval_event(
        policy, _load(approvals_path), stage="signing", expected_comment=comment
    )
    dispatcher_policy = policy["dispatcher"]
    dispatcher = {
        "login": dispatcher_policy["login"],  # type: ignore[index]
        "id": dispatcher_policy["id"],  # type: ignore[index]
        "type": "Bot",
        "app_id": dispatcher_policy["app_id"],  # type: ignore[index]
        "installation_id": dispatcher_policy["installation_id"],  # type: ignore[index]
    }
    return {
        "schema": SIGNING_AUTHORIZATION_SCHEMA,
        "decision": "approved",
        "purpose": "protected-signing-authorization",
        "operating_mode": OPERATING_MODE,
        "policy_sha256": _digest(policy_path),
        "authority": HUMAN_AUTHORITY,
        "dispatcher": dispatcher,
        "release_id": release_id,
        "source_sha": source_sha,
        "candidate_run_id": candidate["run_id"],
        "candidate_run_attempt": candidate["run_attempt"],
        "candidate_identity_sha256": _digest(candidate_path),
        "artifact_digests": artifacts,
        "security_decision_commit": decision["decisionCommit"],
        "security_decision_sha256": _digest(decision_path),
        "workflow_run_id": run["id"],
        "workflow_run_attempt": run["attempt"],
        "workflow_run_url": run["url"],
        "workflow_actor": run["actor"],
        "workflow_triggering_actor": run["triggering_actor"],
        "workflow_run_evidence_sha256": _digest(run_path),
        "job": "sign-candidate",
        "environment": SIGNING_ENVIRONMENT,
        "environment_policy_sha256": _canonical_digest(
            {
                "environment": _load(environment_path),
                "branch_policies": _load(branch_policies_path),
            }
        ),
        "environment_evidence_sha256": _digest(environment_path),
        "branch_policies_evidence_sha256": _digest(branch_policies_path),
        "approval_history_evidence_sha256": _digest(approvals_path),
        "approval_comment": comment,
        "approval_submitted_at": approval["submitted_at"],
        "approval_event_sha256": approval["digest"],
        "created_at": approval["submitted_at"],
    }


def create_signed_handoff(
    *,
    policy_path: pathlib.Path,
    bundle: pathlib.Path,
    release_id: str,
    release_sequence: int,
    source_sha: str,
    workflow_run_id: int,
    workflow_run_attempt: int,
    created_at: str,
) -> dict[str, object]:
    _release_id(release_id)
    root = bundle.resolve(strict=True)
    candidate = _load(root / "candidate-identity.json")
    manifest = _load(root / "release-manifest.v1.json")
    signing = _load(root / "human-signing-authorization.json")
    _time(created_at)
    if (
        not isinstance(candidate, dict)
        or not isinstance(manifest, dict)
        or not isinstance(signing, dict)
        or signing.get("schema") != SIGNING_AUTHORIZATION_SCHEMA
        or signing.get("policy_sha256") != _digest(policy_path)
        or signing.get("release_id") != release_id
        or signing.get("source_sha") != source_sha
        or signing.get("candidate_run_id") != candidate.get("run_id")
        or signing.get("candidate_run_attempt") != candidate.get("run_attempt")
        or manifest.get("release_id") != release_id
        or manifest.get("release_sequence") != release_sequence
        or manifest.get("source_sha") != source_sha
        or signing.get("artifact_digests") != manifest.get("artifacts")
        or workflow_run_attempt != 1
    ):
        raise ReleaseVerificationError("signed handoff input mismatch")
    return {
        "schema": HANDOFF_SCHEMA,
        "policy_sha256": _digest(policy_path),
        "release_id": release_id,
        "release_sequence": release_sequence,
        "source_sha": source_sha,
        "candidate_run_id": candidate["run_id"],
        "candidate_run_attempt": candidate["run_attempt"],
        "candidate_identity_sha256": _digest(root / "candidate-identity.json"),
        "artifact_digests": manifest["artifacts"],
        "manifest_sha256": _digest(root / "release-manifest.v1.json"),
        "signing_authorization_sha256": _digest(root / "human-signing-authorization.json"),
        "release_provenance_sha256": _digest(root / "release-provenance.intoto.json"),
        "signature_verification_sha256": _digest(root / "signature-verification-summary.json"),
        "workflow_run_id": workflow_run_id,
        "workflow_run_attempt": workflow_run_attempt,
        "signing_job": "sign-candidate",
        "signing_job_result": "success",
        "created_at": created_at,
    }


def create_final_approval(
    *,
    policy_path: pathlib.Path,
    run_path: pathlib.Path,
    environment_path: pathlib.Path,
    branch_policies_path: pathlib.Path,
    approvals_path: pathlib.Path,
    jobs_path: pathlib.Path,
    bundle: pathlib.Path,
    repository: str,
    release_id: str,
    release_sequence: int,
    source_sha: str,
) -> dict[str, object]:
    _release_id(release_id)
    policy = validate_authority_policy(
        _load(policy_path), repository=repository, require_configured=True
    )
    run = validate_protected_run(
        policy, _load(run_path), repository=repository, source_sha=source_sha
    )
    signing_job = validate_signing_job_result(
        _load(jobs_path), run_id=run["id"], source_sha=source_sha
    )
    validate_environment_policy(
        policy,
        _load(environment_path),
        _load(branch_policies_path),
        stage="final",
    )
    root = bundle.resolve(strict=True)
    manifest_path = root / "release-manifest.v1.json"
    signing_path = root / "human-signing-authorization.json"
    handoff_path = root / "signed-candidate-handoff.v1.json"
    manifest = _load(manifest_path)
    signing = _load(signing_path)
    handoff = _load(handoff_path)
    if not all(isinstance(value, dict) for value in (manifest, signing, handoff)):
        raise ReleaseVerificationError("invalid final approval inputs")
    if (
        signing.get("schema") != SIGNING_AUTHORIZATION_SCHEMA  # type: ignore[union-attr]
        or handoff.get("schema") != HANDOFF_SCHEMA  # type: ignore[union-attr]
        or signing.get("authority") != HUMAN_AUTHORITY  # type: ignore[union-attr]
        or handoff.get("signing_authorization_sha256") != _digest(signing_path)  # type: ignore[union-attr]
        or handoff.get("manifest_sha256") != _digest(manifest_path)  # type: ignore[union-attr]
        or handoff.get("release_id") != release_id  # type: ignore[union-attr]
        or handoff.get("release_sequence") != release_sequence  # type: ignore[union-attr]
        or handoff.get("source_sha") != source_sha  # type: ignore[union-attr]
        or handoff.get("signing_job_result") != signing_job["result"]  # type: ignore[union-attr]
    ):
        raise ReleaseVerificationError("final approval binding mismatch")
    manifest_digest = _digest(manifest_path)
    signing_digest = _digest(signing_path)
    handoff_digest = _digest(handoff_path)
    comment = (
        f"FINAL PATCH-059 release_id={release_id} release_sequence={release_sequence} "
        f"source_sha={source_sha} manifest_sha256={manifest_digest} "
        f"signing_authorization_sha256={signing_digest} "
        f"signed_handoff_sha256={handoff_digest}"
    )
    event = _approval_event(
        policy, _load(approvals_path), stage="final", expected_comment=comment
    )
    decided_at = _time(event["submitted_at"])
    handoff_created_at = _time(handoff["created_at"])  # type: ignore[index]
    if (decided_at - handoff_created_at).total_seconds() < MINIMUM_FINAL_APPROVAL_DELAY_SECONDS:
        raise ReleaseVerificationError("final approval occurred before minimum delay")
    if event["digest"] == signing.get("approval_event_sha256"):  # type: ignore[union-attr]
        raise ReleaseVerificationError("approval event reused across purposes")
    dispatcher_policy = policy["dispatcher"]
    dispatcher = {
        "login": dispatcher_policy["login"],  # type: ignore[index]
        "id": dispatcher_policy["id"],  # type: ignore[index]
        "type": "Bot",
        "app_id": dispatcher_policy["app_id"],  # type: ignore[index]
        "installation_id": dispatcher_policy["installation_id"],  # type: ignore[index]
    }
    return {
        "schema": APPROVAL_SCHEMA,
        "decision": "approved",
        "purpose": "final-release-approval",
        "operating_mode": OPERATING_MODE,
        "policy_sha256": _digest(policy_path),
        "authority": HUMAN_AUTHORITY,
        "dispatcher": dispatcher,
        "release_id": release_id,
        "release_sequence": release_sequence,
        "source_sha": source_sha,
        "manifest_sha256": manifest_digest,
        "signed_handoff_sha256": handoff_digest,
        "signing_authorization_sha256": signing_digest,
        "artifacts": manifest["artifacts"],  # type: ignore[index]
        "provenance_sha256": _digest(root / "release-provenance.intoto.json"),
        "dossier_sha256": _digest(root / "release-dossier.pending.v1.json"),
        "high_exceptions_sha256": _digest(root / "resolved-high-exceptions.json"),
        "security_decision_sha256": _digest(root / "security-decision.json"),
        "candidate_identity_sha256": _digest(root / "candidate-identity.json"),
        "workflow_run_id": run["id"],
        "workflow_run_attempt": run["attempt"],
        "workflow_run_url": run["url"],
        "workflow_actor": run["actor"],
        "workflow_triggering_actor": run["triggering_actor"],
        "workflow_run_evidence_sha256": _digest(run_path),
        "signing_job_result": signing_job["result"],
        "signing_jobs_evidence_sha256": _digest(jobs_path),
        "job": "finalize",
        "environment": FINAL_APPROVAL_ENVIRONMENT,
        "environment_policy_sha256": _canonical_digest(
            {
                "environment": _load(environment_path),
                "branch_policies": _load(branch_policies_path),
            }
        ),
        "environment_evidence_sha256": _digest(environment_path),
        "branch_policies_evidence_sha256": _digest(branch_policies_path),
        "approval_history_evidence_sha256": _digest(approvals_path),
        "approval_comment": comment,
        "approval_submitted_at": event["submitted_at"],
        "approval_event_sha256": event["digest"],
        "signed_handoff_created_at": handoff["created_at"],  # type: ignore[index]
        "minimum_delay_seconds": MINIMUM_FINAL_APPROVAL_DELAY_SECONDS,
        "run_url": run["url"],
    }


def create_finalization(
    *,
    policy_path: pathlib.Path,
    bundle: pathlib.Path,
    repository: str,
    issuer: str,
    workflow_ref: str,
    finalized_at: str,
) -> dict[str, object]:
    root = bundle.resolve(strict=True)
    policy = validate_authority_policy(
        _load(policy_path), repository=repository, require_configured=True
    )
    signing = _load(root / "human-signing-authorization.json")
    handoff = _load(root / "signed-candidate-handoff.v1.json")
    approval = _load(root / "human-release-approval.json")
    manifest = _load(root / "release-manifest.v1.json")
    if not all(isinstance(value, dict) for value in (signing, handoff, approval, manifest)):
        raise ReleaseVerificationError("invalid finalization inputs")
    if (
        signing.get("schema") != SIGNING_AUTHORIZATION_SCHEMA  # type: ignore[union-attr]
        or handoff.get("schema") != HANDOFF_SCHEMA  # type: ignore[union-attr]
        or approval.get("schema") != APPROVAL_SCHEMA  # type: ignore[union-attr]
        or signing.get("authority") != HUMAN_AUTHORITY  # type: ignore[union-attr]
        or approval.get("authority") != HUMAN_AUTHORITY  # type: ignore[union-attr]
        or signing.get("approval_event_sha256") == approval.get("approval_event_sha256")  # type: ignore[union-attr]
        or approval.get("signing_authorization_sha256") != _digest(root / "human-signing-authorization.json")  # type: ignore[union-attr]
        or approval.get("signed_handoff_sha256") != _digest(root / "signed-candidate-handoff.v1.json")  # type: ignore[union-attr]
        or approval.get("manifest_sha256") != _digest(root / "release-manifest.v1.json")  # type: ignore[union-attr]
    ):
        raise ReleaseVerificationError("finalization binding mismatch")
    if _time(finalized_at) < _time(approval["approval_submitted_at"]):  # type: ignore[index]
        raise ReleaseVerificationError("finalization predates approval")
    return {
        "schema": FINALIZATION_SCHEMA,
        "operating_mode": OPERATING_MODE,
        "policy_sha256": _digest(policy_path),
        "release_id": approval["release_id"],  # type: ignore[index]
        "release_sequence": approval["release_sequence"],  # type: ignore[index]
        "source_sha": approval["source_sha"],  # type: ignore[index]
        "repository": repository,
        "issuer": issuer,
        "workflow_ref": workflow_ref,
        "manifest_sha256": approval["manifest_sha256"],  # type: ignore[index]
        "artifacts": approval["artifacts"],  # type: ignore[index]
        "provenance_sha256": approval["provenance_sha256"],  # type: ignore[index]
        "dossier_sha256": approval["dossier_sha256"],  # type: ignore[index]
        "candidate_identity_sha256": approval["candidate_identity_sha256"],  # type: ignore[index]
        "signing_authorization_sha256": _digest(root / "human-signing-authorization.json"),
        "signed_handoff_sha256": _digest(root / "signed-candidate-handoff.v1.json"),
        "final_approval_sha256": _digest(root / "human-release-approval.json"),
        "signing_approval_event_sha256": signing["approval_event_sha256"],  # type: ignore[index]
        "final_approval_event_sha256": approval["approval_event_sha256"],  # type: ignore[index]
        "finalized_at": finalized_at,
    }


Runner = Callable[..., subprocess.CompletedProcess[str]]


def verify_bundle(
    bundle: pathlib.Path,
    *,
    repository: str,
    issuer: str,
    workflow_ref: str,
    source_sha: str,
    release_id: str,
    release_sequence: int,
    manifest_sha256: str,
    now: dt.datetime,
    cosign: str = "cosign",
    runner: Runner = subprocess.run,
) -> dict[str, object]:
    root = bundle.resolve(strict=True)
    if not root.is_dir() or not SOURCE_SHA.fullmatch(source_sha):
        raise ReleaseVerificationError("invalid expected identity")
    _release_id(release_id)
    if not RAW_SHA256.fullmatch(manifest_sha256) or release_sequence < 1:
        raise ReleaseVerificationError("invalid expected release")

    def file(name: str) -> pathlib.Path:
        path = root / name
        if path.parent != root:
            raise ReleaseVerificationError("unsafe bundle path")
        return path

    policy_path = file("single-human-authority-policy.v1.json")
    policy = validate_authority_policy(
        _load(policy_path), repository=repository, require_configured=True
    )
    policy_digest = _digest(policy_path)

    manifest = _closed(
        _load(file("release-manifest.v1.json")),
        {
            "schema", "release_id", "release_sequence", "source_sha", "artifacts",
            "expected_alembic_head", "configuration_schema", "provenance_sha256",
            "dossier_sha256", "candidate_identity_sha256", "created_at",
        },
        MANIFEST_SCHEMA,
    )
    actual_manifest_digest = _digest(file("release-manifest.v1.json"))
    if actual_manifest_digest != "sha256:" + manifest_sha256:
        raise ReleaseVerificationError("manifest deployment digest mismatch")
    if (
        manifest["release_id"] != release_id
        or manifest["release_sequence"] != release_sequence
        or manifest["source_sha"] != source_sha
    ):
        raise ReleaseVerificationError("manifest candidate mismatch")
    artifacts = manifest["artifacts"]
    if not isinstance(artifacts, dict) or set(artifacts) != set(ARTIFACT_FILES):
        raise ReleaseVerificationError("manifest artifacts mismatch")
    actual_artifacts = {
        name: _digest(file(filename)) for name, filename in ARTIFACT_FILES.items()
    }
    if artifacts != actual_artifacts:
        raise ReleaseVerificationError("artifact substitution")

    candidate_identity_path = file("candidate-identity.json")
    candidate_identity = _closed(
        _load(candidate_identity_path),
        {
            "schema", "repository", "workflow_ref", "workflow_path", "event",
            "branch", "source_sha", "release_id", "run_id", "run_attempt",
            "run_url", "actor", "triggering_actor", "security_decision_commit",
            "security_decision_sha256",
        },
        CANDIDATE_SCHEMA,
    )
    expected_candidate_workflow = (
        f"https://github.com/{repository}/{CANDIDATE_WORKFLOW_PATH}"
        f"@refs/heads/{CANDIDATE_BRANCH}"
    )
    if (
        manifest["candidate_identity_sha256"] != _digest(candidate_identity_path)
        or candidate_identity.get("repository") != repository
        or candidate_identity.get("workflow_ref") != expected_candidate_workflow
        or candidate_identity.get("workflow_path") != CANDIDATE_WORKFLOW_PATH
        or candidate_identity.get("event") != CANDIDATE_EVENT
        or candidate_identity.get("branch") != CANDIDATE_BRANCH
        or candidate_identity.get("source_sha") != source_sha
        or candidate_identity.get("release_id") != release_id
        or type(candidate_identity.get("run_id")) is not int
        or int(candidate_identity["run_id"]) < 1
        or type(candidate_identity.get("run_attempt")) is not int
        or int(candidate_identity["run_attempt"]) < 1
        or candidate_identity.get("run_url")
        != f"https://github.com/{repository}/actions/runs/{candidate_identity['run_id']}"
        or any(
            not isinstance(candidate_identity.get(key), dict)
            or set(candidate_identity[key]) != {"login", "id", "type"}
            or _api_actor(candidate_identity[key]) != candidate_identity[key]
            for key in ("actor", "triggering_actor")
        )
        or not SOURCE_SHA.fullmatch(str(candidate_identity.get("security_decision_commit", "")))
        or not SHA256.fullmatch(str(candidate_identity.get("security_decision_sha256", "")))
    ):
        raise ReleaseVerificationError("candidate producer identity mismatch")
    _verify_pre_decision_custody(
        root, repository=repository, source_sha=source_sha, release_id=release_id
    )

    candidate_provenance = _load(file("provenance.intoto.json"))
    if manifest["provenance_sha256"] != _digest(file("provenance.intoto.json")):
        raise ReleaseVerificationError("candidate provenance substitution")
    candidate_external = (
        candidate_provenance.get("predicate", {})  # type: ignore[union-attr]
        .get("buildDefinition", {})
        .get("externalParameters", {})
    )
    if (
        candidate_external.get("repository") != repository
        or candidate_external.get("revision") != source_sha
        or candidate_external.get("releaseId") != release_id
        or _subjects(candidate_provenance) != actual_artifacts
    ):
        raise ReleaseVerificationError("candidate provenance mismatch")
    try:
        pre_decision_descriptors = _subjects(
            {
                "subject": candidate_provenance["predicate"]["satco"][  # type: ignore[index]
                    "qualificationEvidence"
                ]
            }
        )
    except (KeyError, TypeError) as exc:
        raise ReleaseVerificationError("candidate pre-decision provenance missing") from exc
    expected_pre_decision = {
        name: _digest(file(filename))
        for name, filename in PRE_DECISION_PROVENANCE_FILES.items()
    }
    if any(
        pre_decision_descriptors.get(name) != digest
        for name, digest in expected_pre_decision.items()
    ):
        raise ReleaseVerificationError("candidate pre-decision provenance mismatch")

    dossier_path = file("release-dossier.pending.v1.json")
    dossier = _load(dossier_path)
    if not isinstance(dossier, dict) or set(dossier) != DOSSIER_KEYS:
        raise ReleaseVerificationError("invalid dossier")
    if (
        dossier.get("schema_version") != "v1"
        or dossier.get("release_id") != release_id
        or dossier.get("source_commit") != source_sha
        or manifest["dossier_sha256"] != _digest(dossier_path)
        or dossier.get("human_release_approval", {}).get("status") != "pending"  # type: ignore[union-attr]
        or dossier.get("human_signing_authorization", {}).get("status") != "approved"  # type: ignore[union-attr]
    ):
        raise ReleaseVerificationError("candidate dossier mismatch")
    _time(dossier.get("created_at"))
    for section, expected_files in DOSSIER_SECTION_FILES.items():
        descriptors = dossier.get(section)
        if not isinstance(descriptors, dict) or set(descriptors) != set(expected_files):
            raise ReleaseVerificationError("incomplete dossier")
        for name, expected_filename in expected_files.items():
            _verify_descriptor(root, descriptors[name], expected_filename)
    if {
        name: _descriptor_digest(dossier, "artifacts", name)
        for name in ARTIFACT_FILES
    } != actual_artifacts:
        raise ReleaseVerificationError("dossier artifact mismatch")
    if _verify_descriptor(
        root, dossier.get("provenance"), "provenance.intoto.json"
    ) != manifest["provenance_sha256"]:
        raise ReleaseVerificationError("dossier provenance mismatch")
    _verify_descriptor(
        root,
        dossier.get("signature_verification"),
        "signature-verification-summary.json",
    )
    _verify_descriptor(
        root,
        dossier.get("human_signing_authorization"),
        "human-signing-authorization.json",
        status="approved",
    )

    exceptions_path = file("resolved-high-exceptions.json")
    decision_path = file("security-decision.json")
    exceptions_digest = _digest(exceptions_path)
    decision_digest = _digest(decision_path)
    if _descriptor_digest(dossier, "exceptions", "high_findings") != exceptions_digest:
        raise ReleaseVerificationError("dossier exception mismatch")
    if _descriptor_digest(dossier, "exceptions", "security_decision") != decision_digest:
        raise ReleaseVerificationError("dossier security-decision mismatch")
    exceptions = _load(exceptions_path)
    if not isinstance(exceptions, list):
        raise ReleaseVerificationError("invalid High exceptions")
    for exception in exceptions:
        if (
            not isinstance(exception, dict)
            or exception.get("status") != "active"
            or exception.get("severity") != "HIGH"
            or exception.get("approver_id") != "github:samiphone651-sys#301386823"
            or exception.get("source_revision") != source_sha
            or exception.get("artifact_digest") != actual_artifacts["backend"]
            or _time(exception.get("expires_at")) <= now
        ):
            raise ReleaseVerificationError("stale or mismatched High exception")
    decision = _load(decision_path)
    if (
        not isinstance(decision, dict)
        or set(decision)
        != {
            "schemaVersion", "mode", "candidateRevision", "artifactDigest",
            "exceptionEvidenceDigest", "decisionCommit", "decisionRef",
        }
        or decision.get("schemaVersion") != "PATCH-058-security-decision-v1"
        or decision.get("mode") != "post-build-human-decision"
        or decision.get("candidateRevision") != source_sha
        or decision.get("artifactDigest") != actual_artifacts["backend"]
        or decision.get("exceptionEvidenceDigest") != exceptions_digest
        or not SOURCE_SHA.fullmatch(str(decision.get("decisionCommit", "")))
        or decision.get("decisionRef") != "refs/heads/patch-058-security-decisions"
        or candidate_identity.get("security_decision_commit")
        != decision.get("decisionCommit")
        or candidate_identity.get("security_decision_sha256") != decision_digest
    ):
        raise ReleaseVerificationError("security-decision mismatch")

    release_provenance_path = file("release-provenance.intoto.json")
    release_provenance = _load(release_provenance_path)
    release_external = (
        release_provenance.get("predicate", {})  # type: ignore[union-attr]
        .get("buildDefinition", {})
        .get("externalParameters", {})
    )
    expected_subjects = actual_artifacts | {"manifest": actual_manifest_digest}
    if (
        release_external
        != {
            "releaseId": release_id,
            "releaseSequence": release_sequence,
            "repository": repository,
            "revision": source_sha,
            "workflow": workflow_ref,
            "candidateEvidence": candidate_identity,
        }
        or _subjects(release_provenance) != expected_subjects
    ):
        raise ReleaseVerificationError("release provenance mismatch")
    release_provenance_digest = _digest(release_provenance_path)

    signing_path = file("human-signing-authorization.json")
    signing = _closed(
        _load(signing_path),
        {
            "schema", "decision", "purpose", "operating_mode", "policy_sha256",
            "authority", "dispatcher", "release_id", "source_sha",
            "candidate_run_id", "candidate_run_attempt", "candidate_identity_sha256",
            "artifact_digests", "security_decision_commit", "security_decision_sha256",
            "workflow_run_id", "workflow_run_attempt", "workflow_run_url",
            "workflow_actor", "workflow_triggering_actor",
            "workflow_run_evidence_sha256", "job", "environment",
            "environment_policy_sha256", "environment_evidence_sha256",
            "branch_policies_evidence_sha256", "approval_history_evidence_sha256",
            "approval_comment",
            "approval_submitted_at", "approval_event_sha256", "created_at",
        },
        SIGNING_AUTHORIZATION_SCHEMA,
    )
    dispatcher_policy = policy["dispatcher"]
    expected_dispatcher = {
        "login": dispatcher_policy["login"],  # type: ignore[index]
        "id": dispatcher_policy["id"],  # type: ignore[index]
        "type": "Bot",
        "app_id": dispatcher_policy["app_id"],  # type: ignore[index]
        "installation_id": dispatcher_policy["installation_id"],  # type: ignore[index]
    }
    expected_sign_comment = (
        f"SIGN PATCH-059 release_id={release_id} source_sha={source_sha} "
        f"candidate_run_id={candidate_identity['run_id']} "
        f"candidate_run_attempt={candidate_identity['run_attempt']}"
    )
    signing_run = validate_protected_run(
        policy,
        _load(file("protected-run.json")),
        repository=repository,
        source_sha=source_sha,
    )
    signing_environment = _load(file("signing-environment.json"))
    signing_branches = _load(file("signing-branch-policies.json"))
    validate_environment_policy(
        policy, signing_environment, signing_branches, stage="signing"
    )
    signing_event = _approval_event(
        policy,
        _load(file("signing-approvals.json")),
        stage="signing",
        expected_comment=expected_sign_comment,
    )
    signing_environment_digest = _canonical_digest(
        {
            "environment": signing_environment,
            "branch_policies": signing_branches,
        }
    )
    if (
        signing.get("decision") != "approved"
        or signing.get("purpose") != "protected-signing-authorization"
        or signing.get("operating_mode") != OPERATING_MODE
        or signing.get("policy_sha256") != policy_digest
        or signing.get("authority") != HUMAN_AUTHORITY
        or signing.get("dispatcher") != expected_dispatcher
        or signing.get("release_id") != release_id
        or signing.get("source_sha") != source_sha
        or signing.get("candidate_run_id") != candidate_identity["run_id"]
        or signing.get("candidate_run_attempt") != candidate_identity["run_attempt"]
        or signing.get("candidate_identity_sha256") != _digest(candidate_identity_path)
        or signing.get("artifact_digests") != actual_artifacts
        or signing.get("security_decision_commit") != decision["decisionCommit"]
        or signing.get("security_decision_sha256") != decision_digest
        or signing.get("workflow_run_id") != signing_run["id"]
        or signing.get("workflow_run_attempt") != signing_run["attempt"]
        or signing.get("workflow_run_url") != signing_run["url"]
        or signing.get("workflow_actor") != signing_run["actor"]
        or signing.get("workflow_triggering_actor") != signing_run["triggering_actor"]
        or signing.get("workflow_run_evidence_sha256")
        != _digest(file("protected-run.json"))
        or signing.get("job") != "sign-candidate"
        or signing.get("environment") != SIGNING_ENVIRONMENT
        or signing.get("environment_policy_sha256") != signing_environment_digest
        or signing.get("environment_evidence_sha256")
        != _digest(file("signing-environment.json"))
        or signing.get("branch_policies_evidence_sha256")
        != _digest(file("signing-branch-policies.json"))
        or signing.get("approval_history_evidence_sha256")
        != _digest(file("signing-approvals.json"))
        or signing.get("approval_comment") != expected_sign_comment
        or signing.get("approval_submitted_at") != signing_event["submitted_at"]
        or signing.get("approval_event_sha256") != signing_event["digest"]
        or _time(signing.get("created_at")) != _time(signing.get("approval_submitted_at"))
    ):
        raise ReleaseVerificationError("signing authorization mismatch")

    handoff_path = file("signed-candidate-handoff.v1.json")
    handoff = _closed(
        _load(handoff_path),
        {
            "schema", "policy_sha256", "release_id", "release_sequence", "source_sha",
            "candidate_run_id", "candidate_run_attempt", "candidate_identity_sha256",
            "artifact_digests", "manifest_sha256", "signing_authorization_sha256",
            "release_provenance_sha256", "signature_verification_sha256",
            "workflow_run_id", "workflow_run_attempt", "signing_job",
            "signing_job_result", "created_at",
        },
        HANDOFF_SCHEMA,
    )
    if handoff != {
        "schema": HANDOFF_SCHEMA,
        "policy_sha256": policy_digest,
        "release_id": release_id,
        "release_sequence": release_sequence,
        "source_sha": source_sha,
        "candidate_run_id": candidate_identity["run_id"],
        "candidate_run_attempt": candidate_identity["run_attempt"],
        "candidate_identity_sha256": _digest(candidate_identity_path),
        "artifact_digests": actual_artifacts,
        "manifest_sha256": actual_manifest_digest,
        "signing_authorization_sha256": _digest(signing_path),
        "release_provenance_sha256": release_provenance_digest,
        "signature_verification_sha256": _digest(file("signature-verification-summary.json")),
        "workflow_run_id": signing["workflow_run_id"],
        "workflow_run_attempt": 1,
        "signing_job": "sign-candidate",
        "signing_job_result": "success",
        "created_at": handoff["created_at"],
    }:
        raise ReleaseVerificationError("signed handoff mismatch")
    handoff_created_at = _time(handoff["created_at"])

    approval = _closed(
        _load(file("human-release-approval.json")),
        {
            "schema", "decision", "purpose", "operating_mode", "policy_sha256",
            "authority", "dispatcher", "release_id", "release_sequence", "source_sha",
            "manifest_sha256", "signed_handoff_sha256", "signing_authorization_sha256",
            "artifacts", "provenance_sha256", "dossier_sha256", "high_exceptions_sha256",
            "security_decision_sha256", "candidate_identity_sha256", "workflow_run_id",
            "workflow_run_attempt", "workflow_run_url", "workflow_actor",
            "workflow_triggering_actor", "workflow_run_evidence_sha256", "job",
            "signing_job_result", "signing_jobs_evidence_sha256",
            "environment", "environment_policy_sha256", "environment_evidence_sha256",
            "branch_policies_evidence_sha256", "approval_history_evidence_sha256",
            "approval_comment", "approval_submitted_at",
            "approval_event_sha256", "signed_handoff_created_at", "minimum_delay_seconds",
            "run_url",
        },
        APPROVAL_SCHEMA,
    )
    authority = approval["authority"]
    expected_final_comment = (
        f"FINAL PATCH-059 release_id={release_id} release_sequence={release_sequence} "
        f"source_sha={source_sha} manifest_sha256={actual_manifest_digest} "
        f"signing_authorization_sha256={_digest(signing_path)} "
        f"signed_handoff_sha256={_digest(handoff_path)}"
    )
    final_run = validate_protected_run(
        policy,
        _load(file("final-run.json")),
        repository=repository,
        source_sha=source_sha,
    )
    final_environment = _load(file("final-environment.json"))
    final_branches = _load(file("final-branch-policies.json"))
    validate_environment_policy(
        policy, final_environment, final_branches, stage="final"
    )
    final_event = _approval_event(
        policy,
        _load(file("final-approvals.json")),
        stage="final",
        expected_comment=expected_final_comment,
    )
    final_environment_digest = _canonical_digest(
        {
            "environment": final_environment,
            "branch_policies": final_branches,
        }
    )
    signing_job = validate_signing_job_result(
        _load(file("final-jobs.json")),
        run_id=final_run["id"],
        source_sha=source_sha,
    )
    if (
        approval["decision"] != "approved"
        or approval.get("purpose") != "final-release-approval"
        or approval.get("operating_mode") != OPERATING_MODE
        or approval.get("policy_sha256") != policy_digest
        or authority != HUMAN_AUTHORITY
        or approval.get("dispatcher") != expected_dispatcher
        or approval["release_id"] != release_id
        or approval["release_sequence"] != release_sequence
        or approval["source_sha"] != source_sha
        or approval["manifest_sha256"] != actual_manifest_digest
        or approval.get("signed_handoff_sha256") != _digest(handoff_path)
        or approval.get("signing_authorization_sha256") != _digest(signing_path)
        or approval["artifacts"] != actual_artifacts
        or approval["provenance_sha256"] != release_provenance_digest
        or approval["dossier_sha256"] != manifest["dossier_sha256"]
        or approval["high_exceptions_sha256"] != exceptions_digest
        or approval["security_decision_sha256"] != decision_digest
        or approval["candidate_identity_sha256"] != manifest["candidate_identity_sha256"]
        or approval["environment"] != FINAL_APPROVAL_ENVIRONMENT
        or approval.get("workflow_run_id") != final_run["id"]
        or approval.get("workflow_run_attempt") != final_run["attempt"]
        or approval.get("workflow_run_url") != final_run["url"]
        or approval.get("workflow_actor") != final_run["actor"]
        or approval.get("workflow_triggering_actor") != final_run["triggering_actor"]
        or approval.get("workflow_run_evidence_sha256")
        != _digest(file("final-run.json"))
        or approval.get("signing_job_result") != signing_job["result"]
        or approval.get("signing_jobs_evidence_sha256")
        != _digest(file("final-jobs.json"))
        or final_run != signing_run
        or approval.get("job") != "finalize"
        or approval.get("approval_comment") != expected_final_comment
        or approval.get("environment_policy_sha256") != final_environment_digest
        or approval.get("environment_evidence_sha256")
        != _digest(file("final-environment.json"))
        or approval.get("branch_policies_evidence_sha256")
        != _digest(file("final-branch-policies.json"))
        or approval.get("approval_history_evidence_sha256")
        != _digest(file("final-approvals.json"))
        or approval.get("approval_submitted_at") != final_event["submitted_at"]
        or approval.get("approval_event_sha256") != final_event["digest"]
        or approval.get("approval_event_sha256") == signing.get("approval_event_sha256")
        or approval.get("signed_handoff_created_at") != handoff.get("created_at")
        or approval.get("minimum_delay_seconds") != MINIMUM_FINAL_APPROVAL_DELAY_SECONDS
        or not approval["run_url"]
    ):
        raise ReleaseVerificationError("final Human approval mismatch")
    decided_at = _time(approval["approval_submitted_at"])
    if (decided_at - handoff_created_at).total_seconds() < MINIMUM_FINAL_APPROVAL_DELAY_SECONDS:
        raise ReleaseVerificationError("final approval occurred before minimum delay")
    for exception in exceptions:
        if _time(exception["expires_at"]) <= decided_at:
            raise ReleaseVerificationError("exception stale at approval")

    finalization = _closed(
        _load(file("release-finalization.v2.json")),
        {
            "schema", "operating_mode", "policy_sha256", "release_id",
            "release_sequence", "source_sha", "repository", "issuer", "workflow_ref",
            "manifest_sha256", "artifacts", "provenance_sha256", "dossier_sha256",
            "candidate_identity_sha256", "signing_authorization_sha256",
            "signed_handoff_sha256", "final_approval_sha256",
            "signing_approval_event_sha256", "final_approval_event_sha256", "finalized_at",
        },
        FINALIZATION_SCHEMA,
    )
    if finalization != {
        "schema": FINALIZATION_SCHEMA,
        "operating_mode": OPERATING_MODE,
        "policy_sha256": policy_digest,
        "release_id": release_id,
        "release_sequence": release_sequence,
        "source_sha": source_sha,
        "repository": repository,
        "issuer": issuer,
        "workflow_ref": workflow_ref,
        "manifest_sha256": actual_manifest_digest,
        "artifacts": actual_artifacts,
        "provenance_sha256": release_provenance_digest,
        "dossier_sha256": manifest["dossier_sha256"],
        "candidate_identity_sha256": manifest["candidate_identity_sha256"],
        "signing_authorization_sha256": _digest(signing_path),
        "signed_handoff_sha256": _digest(handoff_path),
        "final_approval_sha256": _digest(file("human-release-approval.json")),
        "signing_approval_event_sha256": signing["approval_event_sha256"],
        "final_approval_event_sha256": approval["approval_event_sha256"],
        "finalized_at": finalization["finalized_at"],
    } or _time(finalization["finalized_at"]) < decided_at:
        raise ReleaseVerificationError("finalization mismatch")

    version = runner(
        [cosign, "version"], check=True, capture_output=True, text=True
    )
    if "v2.6.0" not in version.stdout + version.stderr:
        raise ReleaseVerificationError("unapproved cosign version")
    common = [
        "--offline",
        "--certificate-identity",
        workflow_ref,
        "--certificate-oidc-issuer",
        issuer,
        "--certificate-github-workflow-repository",
        repository,
        "--certificate-github-workflow-sha",
        source_sha,
    ]
    for name, filename in SIGNED_FILES.items():
        runner(
            [
                cosign, "verify-blob", "--bundle", str(file(f"{name}-signature.bundle.json")),
                *common, str(file(filename)),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    runner(
        [
            cosign, "verify-blob-attestation",
            "--bundle", str(file("manifest-provenance-attestation.bundle.json")),
            "--type", "slsaprovenance1", *common, str(file("release-manifest.v1.json")),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return finalization


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)

    gate = commands.add_parser("gate-run")
    gate.add_argument("--policy", required=True)
    gate.add_argument("--run-json", required=True)
    gate.add_argument("--repository", required=True)
    gate.add_argument("--source-sha", required=True)

    signing = commands.add_parser("signing-authorization")
    final = commands.add_parser("final-approval")
    for command in (signing, final):
        command.add_argument("--policy", required=True)
        command.add_argument("--run-json", required=True)
        command.add_argument("--environment-json", required=True)
        command.add_argument("--branch-policies-json", required=True)
        command.add_argument("--approvals-json", required=True)
        command.add_argument("--bundle", required=True)
        command.add_argument("--repository", required=True)
        command.add_argument("--release-id", required=True)
        command.add_argument("--source-sha", required=True)
        command.add_argument("--output", required=True)
    final.add_argument("--release-sequence", required=True, type=int)
    final.add_argument("--jobs-json", required=True)

    handoff = commands.add_parser("handoff")
    handoff.add_argument("--policy", required=True)
    handoff.add_argument("--bundle", required=True)
    handoff.add_argument("--release-id", required=True)
    handoff.add_argument("--release-sequence", required=True, type=int)
    handoff.add_argument("--source-sha", required=True)
    handoff.add_argument("--workflow-run-id", required=True, type=int)
    handoff.add_argument("--workflow-run-attempt", required=True, type=int)
    handoff.add_argument("--created-at", required=True)
    handoff.add_argument("--output", required=True)

    finalization = commands.add_parser("finalization")
    finalization.add_argument("--policy", required=True)
    finalization.add_argument("--bundle", required=True)
    finalization.add_argument("--repository", required=True)
    finalization.add_argument("--issuer", required=True)
    finalization.add_argument("--workflow-ref", required=True)
    finalization.add_argument("--finalized-at", required=True)
    finalization.add_argument("--output", required=True)

    verify = commands.add_parser("verify")
    verify.add_argument("--bundle", required=True)
    verify.add_argument("--repository", required=True)
    verify.add_argument("--issuer", required=True)
    verify.add_argument("--workflow-ref", required=True)
    verify.add_argument("--source-sha", required=True)
    verify.add_argument("--release-id", required=True)
    verify.add_argument("--release-sequence", required=True, type=int)
    verify.add_argument("--manifest-sha256", required=True)
    verify.add_argument("--now", required=True)
    verify.add_argument("--cosign", default="cosign")
    args = parser.parse_args()
    try:
        result: dict[str, object] | None = None
        if args.command == "gate-run":
            policy = validate_authority_policy(
                _load(pathlib.Path(args.policy)),
                repository=args.repository,
                require_configured=True,
            )
            validate_protected_run(
                policy,
                _load(pathlib.Path(args.run_json)),
                repository=args.repository,
                source_sha=args.source_sha,
            )
        elif args.command == "signing-authorization":
            result = create_signing_authorization(
                policy_path=pathlib.Path(args.policy),
                run_path=pathlib.Path(args.run_json),
                environment_path=pathlib.Path(args.environment_json),
                branch_policies_path=pathlib.Path(args.branch_policies_json),
                approvals_path=pathlib.Path(args.approvals_json),
                bundle=pathlib.Path(args.bundle),
                repository=args.repository,
                release_id=args.release_id,
                source_sha=args.source_sha,
            )
        elif args.command == "handoff":
            result = create_signed_handoff(
                policy_path=pathlib.Path(args.policy),
                bundle=pathlib.Path(args.bundle),
                release_id=args.release_id,
                release_sequence=args.release_sequence,
                source_sha=args.source_sha,
                workflow_run_id=args.workflow_run_id,
                workflow_run_attempt=args.workflow_run_attempt,
                created_at=args.created_at,
            )
        elif args.command == "final-approval":
            result = create_final_approval(
                policy_path=pathlib.Path(args.policy),
                run_path=pathlib.Path(args.run_json),
                environment_path=pathlib.Path(args.environment_json),
                branch_policies_path=pathlib.Path(args.branch_policies_json),
                approvals_path=pathlib.Path(args.approvals_json),
                jobs_path=pathlib.Path(args.jobs_json),
                bundle=pathlib.Path(args.bundle),
                repository=args.repository,
                release_id=args.release_id,
                release_sequence=args.release_sequence,
                source_sha=args.source_sha,
            )
        elif args.command == "finalization":
            result = create_finalization(
                policy_path=pathlib.Path(args.policy),
                bundle=pathlib.Path(args.bundle),
                repository=args.repository,
                issuer=args.issuer,
                workflow_ref=args.workflow_ref,
                finalized_at=args.finalized_at,
            )
        else:
            verify_bundle(
                pathlib.Path(args.bundle),
                repository=args.repository,
                issuer=args.issuer,
                workflow_ref=args.workflow_ref,
                source_sha=args.source_sha,
                release_id=args.release_id,
                release_sequence=args.release_sequence,
                manifest_sha256=args.manifest_sha256,
                now=_time(args.now),
                cosign=args.cosign,
            )
        if result is not None:
            pathlib.Path(args.output).write_text(
                json.dumps(result, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
    except (OSError, subprocess.CalledProcessError, ReleaseVerificationError) as exc:
        print(f"BLOCK: {exc}", file=sys.stderr)
        return 2
    print(f"PATCH059_{args.command.upper().replace('-', '_')}_VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
