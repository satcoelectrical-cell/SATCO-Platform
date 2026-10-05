#!/usr/bin/env python3
"""Fail-closed GitHub evidence for the PATCH-059 Human decision interval.

GitHub issue-comment ``created_at`` values are the only temporal inputs used by
this module.  Handoff document timestamps and runner clocks are deliberately
not accepted as substitutes for the server-created marker/decision interval.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import secrets
import stat
import subprocess
import tempfile
from typing import Any


POLICY_SCHEMA = "satco.patch059-single-human-authority-policy/v1"
MARKER_SCHEMA = "satco.patch059-handoff-marker/v1"
APPROVAL_SCHEMA = "satco.patch059-final-approval-comment/v1"
DECISION_SCHEMA = "satco.patch059-final-decision-evidence/v1"
CONSUMPTION_SCHEMA = "satco.patch059-final-approval-consumption/v1"
MARKER_HEADER = "SATCO PATCH-059 HANDOFF_MARKER v1"
APPROVAL_HEADER = "SATCO PATCH-059 FINAL_APPROVAL v1"
CONSUMPTION_HEADER = "SATCO PATCH-059 FINAL_APPROVAL_CONSUMED v1"
APPROVAL_NAMESPACE = "satco-patch059-final-approval-v1"
HUMAN_AUTHORITY = {"login": "samiphone651-sys", "id": 301386823, "type": "User"}
MARKER_ACTOR = {"login": "github-actions[bot]", "id": 41898282, "type": "Bot"}
REPOSITORY = "satcoelectrical-cell/SATCO-Platform"
REPOSITORY_ID = 1311705732
MINIMUM_RECORDED_DELAY_SECONDS = 905
SSH_PUBLIC_KEY = (
    "ssh-ed25519 "
    "AAAAC3NzaC1lZDI1NTE5AAAAILtC0QdiVnIF0QYMlVTBN/r0cnzEvetni1ucRlzL7UQa"
)
SSH_FINGERPRINT = "SHA256:0QRoi7nAjRewgACw6V18QJzePt7MdhPr01zpaTJbojw"
SSH_GITHUB_KEY_ID = 1219405
SSH_PRINCIPAL = "samiphone651-sys"
MAX_JSON_BYTES = 8 * 1024 * 1024
MAX_COMMENT_BYTES = 16 * 1024
SHA256 = re.compile(r"sha256:[0-9a-f]{64}\Z")
SOURCE_SHA = re.compile(r"[0-9a-f]{40}\Z")
RELEASE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
NODE_ID = re.compile(r"[A-Za-z0-9_=-]{1,128}\Z")
NONCE = re.compile(r"[0-9a-f]{64}\Z")
GITHUB_TIME = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?Z\Z"
)


class HumanDecisionError(ValueError):
    pass


def _load(path: pathlib.Path) -> object:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                raise HumanDecisionError("duplicate JSON member")
            result[key] = value
        return result

    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_size > MAX_JSON_BYTES
        ):
            raise HumanDecisionError("unsafe evidence file")
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            raw = stream.read(MAX_JSON_BYTES + 1)
        return json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=pairs,
            parse_constant=lambda _value: (_ for _ in ()).throw(
                HumanDecisionError("non-I-JSON constant")
            ),
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HumanDecisionError("invalid evidence JSON") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _write_json(path: pathlib.Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _closed(value: object, keys: set[str], schema: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys or value.get("schema") != schema:
        raise HumanDecisionError("closed schema mismatch")
    return value


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("ascii")


def _digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _digest_file(path: pathlib.Path) -> str:
    descriptor: int | None = None
    digest = hashlib.sha256()
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise HumanDecisionError("unsafe evidence subject")
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise HumanDecisionError("missing evidence subject") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    return "sha256:" + digest.hexdigest()


def _time(value: object) -> dt.datetime:
    if not isinstance(value, str) or not GITHUB_TIME.fullmatch(value):
        raise HumanDecisionError("invalid GitHub timestamp")
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
            dt.timezone.utc
        )
    except ValueError as exc:
        raise HumanDecisionError("invalid GitHub timestamp") from exc


def validate_policy(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise HumanDecisionError("invalid authority policy")
    if (
        value.get("schema") != POLICY_SCHEMA
        or value.get("repository") != REPOSITORY
        or value.get("repository_id") != REPOSITORY_ID
        or value.get("human_authority") != HUMAN_AUTHORITY
        or value.get("marker_actor") != MARKER_ACTOR
        or value.get("minimum_final_approval_delay_seconds")
        != MINIMUM_RECORDED_DELAY_SECONDS
        or value.get("human_ssh_signing_key")
        != {
            "github_key_id": SSH_GITHUB_KEY_ID,
            "algorithm": "ssh-ed25519",
            "public_key": SSH_PUBLIC_KEY,
            "fingerprint": SSH_FINGERPRINT,
            "principal": SSH_PRINCIPAL,
            "namespace": APPROVAL_NAMESPACE,
        }
    ):
        raise HumanDecisionError("Human decision policy mismatch")
    return value


def _validate_repository(value: object) -> None:
    if (
        not isinstance(value, dict)
        or value.get("id") != REPOSITORY_ID
        or value.get("full_name") != REPOSITORY
    ):
        raise HumanDecisionError("repository identity mismatch")


def _validate_issue(value: object, issue_number: int) -> None:
    if (
        not isinstance(value, dict)
        or value.get("number") != issue_number
        or value.get("repository_url") != f"https://api.github.com/repos/{REPOSITORY}"
        or value.get("state") != "open"
        or value.get("locked") is not True
        or "pull_request" in value
    ):
        raise HumanDecisionError("governance issue mismatch")


def _actor(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise HumanDecisionError("comment actor missing")
    result = {"login": value.get("login"), "id": value.get("id"), "type": value.get("type")}
    if (
        not isinstance(result["login"], str)
        or type(result["id"]) is not int
        or result["type"] not in {"User", "Bot"}
    ):
        raise HumanDecisionError("invalid comment actor")
    return result


def _validate_comment(
    value: object, *, issue_number: int, expected_actor: dict[str, object]
) -> dict[str, object]:
    if not isinstance(value, dict):
        raise HumanDecisionError("invalid GitHub comment")
    body = value.get("body")
    if not isinstance(body, str) or not body or len(body.encode("utf-8")) > MAX_COMMENT_BYTES:
        raise HumanDecisionError("invalid GitHub comment body")
    comment_id = value.get("id")
    node_id = value.get("node_id")
    created_at = value.get("created_at")
    updated_at = value.get("updated_at")
    if (
        type(comment_id) is not int
        or comment_id < 1
        or not isinstance(node_id, str)
        or not NODE_ID.fullmatch(node_id)
        or value.get("issue_url")
        != f"https://api.github.com/repos/{REPOSITORY}/issues/{issue_number}"
        or _actor(value.get("user")) != expected_actor
        or created_at != updated_at
    ):
        raise HumanDecisionError("GitHub comment identity mismatch")
    _time(created_at)
    return {
        "id": comment_id,
        "node_id": node_id,
        "created_at": created_at,
        "updated_at": updated_at,
        "body": body,
        "body_sha256": _digest_bytes(body.encode("utf-8")),
        "user": expected_actor,
    }


MARKER_KEYS = {
    "schema", "purpose", "repository_id", "repository", "governance_issue_number",
    "release_id", "release_sequence", "source_sha", "candidate_run_id",
    "candidate_run_attempt", "manifest_sha256", "signing_authorization_sha256",
    "signed_handoff_sha256", "signing_workflow_run_id",
    "signing_workflow_run_attempt", "nonce",
}
APPROVAL_KEYS = {
    "schema", "purpose", "decision", "repository_id", "repository",
    "governance_issue_number", "release_id", "release_sequence", "source_sha",
    "candidate_run_id", "candidate_run_attempt", "manifest_sha256",
    "signing_authorization_sha256", "signed_handoff_sha256", "marker_comment_id",
    "marker_comment_node_id", "marker_body_sha256", "marker_created_at", "nonce",
}


def _validate_common_payload(value: dict[str, object]) -> None:
    if (
        value.get("repository_id") != REPOSITORY_ID
        or value.get("repository") != REPOSITORY
        or type(value.get("governance_issue_number")) is not int
        or value["governance_issue_number"] < 1
        or not isinstance(value.get("release_id"), str)
        or not RELEASE_ID.fullmatch(value["release_id"])
        or type(value.get("release_sequence")) is not int
        or value["release_sequence"] < 1
        or not isinstance(value.get("source_sha"), str)
        or not SOURCE_SHA.fullmatch(value["source_sha"])
        or type(value.get("candidate_run_id")) is not int
        or value["candidate_run_id"] < 1
        or type(value.get("candidate_run_attempt")) is not int
        or value["candidate_run_attempt"] < 1
        or any(
            not isinstance(value.get(key), str) or not SHA256.fullmatch(value[key])
            for key in (
                "manifest_sha256",
                "signing_authorization_sha256",
                "signed_handoff_sha256",
            )
        )
        or not isinstance(value.get("nonce"), str)
        or not NONCE.fullmatch(value["nonce"])
    ):
        raise HumanDecisionError("decision payload identity mismatch")


def marker_body(payload: dict[str, object]) -> str:
    return MARKER_HEADER + "\n" + _canonical_bytes(payload).decode("ascii")


def approval_body(payload: dict[str, object], signature: str) -> str:
    if not signature.startswith("-----BEGIN SSH SIGNATURE-----\n") or not signature.endswith(
        "-----END SSH SIGNATURE-----\n"
    ):
        raise HumanDecisionError("invalid SSH signature armor")
    return APPROVAL_HEADER + "\n" + _canonical_bytes(payload).decode("ascii") + signature


def consumption_body(payload: dict[str, object]) -> str:
    return CONSUMPTION_HEADER + "\n" + _canonical_bytes(payload).decode("ascii")


def _parse_marker_body(body: str) -> dict[str, object]:
    prefix = MARKER_HEADER + "\n"
    if not body.startswith(prefix):
        raise HumanDecisionError("HANDOFF_MARKER header mismatch")
    raw = body[len(prefix):]
    if not raw.endswith("\n") or "\n" in raw[:-1]:
        raise HumanDecisionError("HANDOFF_MARKER canonical framing mismatch")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HumanDecisionError("invalid HANDOFF_MARKER payload") from exc
    payload = _closed(payload, MARKER_KEYS, MARKER_SCHEMA)
    if _canonical_bytes(payload).decode("ascii") != raw:
        raise HumanDecisionError("non-canonical HANDOFF_MARKER payload")
    if (
        payload.get("purpose") != "signed-handoff-temporal-baseline"
        or type(payload.get("signing_workflow_run_id")) is not int
        or payload["signing_workflow_run_id"] < 1
        or payload.get("signing_workflow_run_attempt") != 1
    ):
        raise HumanDecisionError("HANDOFF_MARKER purpose mismatch")
    _validate_common_payload(payload)
    return payload


def _parse_approval_body(body: str) -> tuple[dict[str, object], str]:
    prefix = APPROVAL_HEADER + "\n"
    signature_header = "-----BEGIN SSH SIGNATURE-----\n"
    if not body.startswith(prefix):
        raise HumanDecisionError("FINAL_APPROVAL header mismatch")
    split = body.find(signature_header, len(prefix))
    if split < 0:
        raise HumanDecisionError("FINAL_APPROVAL signature missing")
    raw = body[len(prefix):split]
    signature = body[split:]
    if not raw.endswith("\n") or "\n" in raw[:-1]:
        raise HumanDecisionError("FINAL_APPROVAL canonical framing mismatch")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HumanDecisionError("invalid FINAL_APPROVAL payload") from exc
    payload = _closed(payload, APPROVAL_KEYS, APPROVAL_SCHEMA)
    if _canonical_bytes(payload).decode("ascii") != raw:
        raise HumanDecisionError("non-canonical FINAL_APPROVAL payload")
    if payload.get("purpose") != "final-release-human-decision" or payload.get("decision") != "approved":
        raise HumanDecisionError("FINAL_APPROVAL purpose mismatch")
    _validate_common_payload(payload)
    if (
        type(payload.get("marker_comment_id")) is not int
        or payload["marker_comment_id"] < 1
        or not isinstance(payload.get("marker_comment_node_id"), str)
        or not NODE_ID.fullmatch(payload["marker_comment_node_id"])
        or not isinstance(payload.get("marker_body_sha256"), str)
        or not SHA256.fullmatch(payload["marker_body_sha256"])
    ):
        raise HumanDecisionError("FINAL_APPROVAL marker binding mismatch")
    _time(payload.get("marker_created_at"))
    if not signature.endswith("-----END SSH SIGNATURE-----\n"):
        raise HumanDecisionError("invalid SSH signature armor")
    return payload, signature


def _verify_ssh_signature(payload: dict[str, object], signature: str) -> None:
    with tempfile.TemporaryDirectory(prefix="patch059-ssh-") as directory:
        root = pathlib.Path(directory)
        allowed = root / "allowed_signers"
        signature_path = root / "approval.sig"
        allowed.write_text(f"{SSH_PRINCIPAL} namespaces=\"{APPROVAL_NAMESPACE}\" {SSH_PUBLIC_KEY}\n", encoding="ascii")
        signature_path.write_text(signature, encoding="ascii")
        result = subprocess.run(
            [
                "ssh-keygen", "-Y", "verify", "-f", str(allowed), "-I",
                SSH_PRINCIPAL, "-n", APPROVAL_NAMESPACE, "-s", str(signature_path),
            ],
            input=_canonical_bytes(payload),
            capture_output=True,
            check=False,
        )
    if result.returncode != 0:
        raise HumanDecisionError("FINAL_APPROVAL SSH signature verification failed")


def create_marker(
    *, policy: object, repository: object, issue: object, bundle: pathlib.Path,
    issue_number: int, signing_run_id: int, signing_run_attempt: int,
) -> tuple[dict[str, object], str]:
    validate_policy(policy)
    _validate_repository(repository)
    _validate_issue(issue, issue_number)
    root = bundle.resolve(strict=True)
    handoff = _load(root / "signed-candidate-handoff.v1.json")
    if not isinstance(handoff, dict):
        raise HumanDecisionError("invalid signed handoff")
    candidate = _load(root / "candidate-identity.json")
    if not isinstance(candidate, dict):
        raise HumanDecisionError("invalid candidate identity")
    payload: dict[str, object] = {
        "schema": MARKER_SCHEMA,
        "purpose": "signed-handoff-temporal-baseline",
        "repository_id": REPOSITORY_ID,
        "repository": REPOSITORY,
        "governance_issue_number": issue_number,
        "release_id": handoff.get("release_id"),
        "release_sequence": handoff.get("release_sequence"),
        "source_sha": handoff.get("source_sha"),
        "candidate_run_id": candidate.get("run_id"),
        "candidate_run_attempt": candidate.get("run_attempt"),
        "manifest_sha256": _digest_file(root / "release-manifest.v1.json"),
        "signing_authorization_sha256": _digest_file(root / "human-signing-authorization.json"),
        "signed_handoff_sha256": _digest_file(root / "signed-candidate-handoff.v1.json"),
        "signing_workflow_run_id": signing_run_id,
        "signing_workflow_run_attempt": signing_run_attempt,
        "nonce": secrets.token_hex(32),
    }
    _validate_common_payload(payload)
    if (
        signing_run_attempt != 1
        or handoff.get("workflow_run_id") != signing_run_id
        or handoff.get("workflow_run_attempt") != signing_run_attempt
        or handoff.get("candidate_run_id") != payload["candidate_run_id"]
        or handoff.get("candidate_run_attempt") != payload["candidate_run_attempt"]
        or handoff.get("manifest_sha256") != payload["manifest_sha256"]
        or handoff.get("signing_authorization_sha256")
        != payload["signing_authorization_sha256"]
    ):
        raise HumanDecisionError("HANDOFF_MARKER signed-handoff mismatch")
    return payload, marker_body(payload)


def validate_marker_comment(
    *, policy: object, repository: object, issue: object, comment: object,
) -> tuple[dict[str, object], dict[str, object]]:
    validate_policy(policy)
    _validate_repository(repository)
    if not isinstance(comment, dict) or type(comment.get("id")) is not int:
        raise HumanDecisionError("invalid HANDOFF_MARKER comment")
    body = comment.get("body")
    if not isinstance(body, str):
        raise HumanDecisionError("invalid HANDOFF_MARKER comment")
    payload = _parse_marker_body(body)
    issue_number = int(payload["governance_issue_number"])
    _validate_issue(issue, issue_number)
    summary = _validate_comment(comment, issue_number=issue_number, expected_actor=MARKER_ACTOR)
    return payload, summary


def validate_approval_comment(
    *, policy: object, repository: object, issue: object, comment: object,
) -> tuple[dict[str, object], dict[str, object]]:
    validate_policy(policy)
    _validate_repository(repository)
    if not isinstance(comment, dict) or not isinstance(comment.get("body"), str):
        raise HumanDecisionError("invalid FINAL_APPROVAL comment")
    payload, signature = _parse_approval_body(comment["body"])
    issue_number = int(payload["governance_issue_number"])
    _validate_issue(issue, issue_number)
    summary = _validate_comment(comment, issue_number=issue_number, expected_actor=HUMAN_AUTHORITY)
    _verify_ssh_signature(payload, signature)
    summary["ssh_signature_sha256"] = _digest_bytes(signature.encode("ascii"))
    return payload, summary


def verify_decision(
    *, policy: object, repository: object, issue: object, event: object,
    marker_comment: object, approval_comment: object, comments: object,
    bundle: pathlib.Path,
) -> dict[str, object]:
    validate_policy(policy)
    _validate_repository(repository)
    marker, marker_summary = validate_marker_comment(
        policy=policy, repository=repository, issue=issue, comment=marker_comment
    )
    approval, approval_summary = validate_approval_comment(
        policy=policy, repository=repository, issue=issue, comment=approval_comment
    )
    if not isinstance(event, dict) or event.get("action") != "created":
        raise HumanDecisionError("FINAL_APPROVAL must be a created event")
    event_comment = event.get("comment")
    event_repository = event.get("repository")
    event_issue = event.get("issue")
    if (
        not isinstance(event_comment, dict)
        or event_comment.get("id") != approval_summary["id"]
        or event_comment.get("node_id") != approval_summary["node_id"]
        or event_comment.get("body") != approval_summary["body"]
        or event_comment.get("created_at") != approval_summary["created_at"]
        or event_comment.get("updated_at") != approval_summary["updated_at"]
        or _actor(event_comment.get("user")) != HUMAN_AUTHORITY
        or not isinstance(event_repository, dict)
        or event_repository.get("id") != REPOSITORY_ID
        or event_repository.get("full_name") != REPOSITORY
        or not isinstance(event_issue, dict)
        or event_issue.get("number") != marker["governance_issue_number"]
    ):
        raise HumanDecisionError("created-event/live-comment mismatch")
    common = (
        "repository_id", "repository", "governance_issue_number", "release_id",
        "release_sequence", "source_sha", "candidate_run_id", "candidate_run_attempt",
        "manifest_sha256", "signing_authorization_sha256", "signed_handoff_sha256",
        "nonce",
    )
    if any(approval.get(key) != marker.get(key) for key in common):
        raise HumanDecisionError("FINAL_APPROVAL/HANDOFF_MARKER binding mismatch")
    if (
        approval.get("marker_comment_id") != marker_summary["id"]
        or approval.get("marker_comment_node_id") != marker_summary["node_id"]
        or approval.get("marker_body_sha256") != marker_summary["body_sha256"]
        or approval.get("marker_created_at") != marker_summary["created_at"]
    ):
        raise HumanDecisionError("FINAL_APPROVAL marker identity mismatch")
    elapsed = (
        _time(approval_summary["created_at"]) - _time(marker_summary["created_at"])
    ).total_seconds()
    if elapsed < MINIMUM_RECORDED_DELAY_SECONDS:
        raise HumanDecisionError("FINAL_APPROVAL occurred before 905-second threshold")
    root = bundle.resolve(strict=True)
    if (
        _digest_file(root / "release-manifest.v1.json") != marker["manifest_sha256"]
        or _digest_file(root / "human-signing-authorization.json")
        != marker["signing_authorization_sha256"]
        or _digest_file(root / "signed-candidate-handoff.v1.json")
        != marker["signed_handoff_sha256"]
    ):
        raise HumanDecisionError("live decision/bundle digest mismatch")
    handoff = _load(root / "signed-candidate-handoff.v1.json")
    if (
        not isinstance(handoff, dict)
        or handoff.get("release_id") != marker["release_id"]
        or handoff.get("release_sequence") != marker["release_sequence"]
        or handoff.get("source_sha") != marker["source_sha"]
        or handoff.get("candidate_run_id") != marker["candidate_run_id"]
        or handoff.get("candidate_run_attempt") != marker["candidate_run_attempt"]
        or handoff.get("workflow_run_id") != marker["signing_workflow_run_id"]
        or handoff.get("workflow_run_attempt") != marker["signing_workflow_run_attempt"]
    ):
        raise HumanDecisionError("live decision/signed-handoff mismatch")
    if not isinstance(comments, list):
        raise HumanDecisionError("invalid governance comment listing")
    markers = 0
    approvals = 0
    consumptions = 0
    for item in comments:
        body = item.get("body") if isinstance(item, dict) else None
        if not isinstance(body, str):
            raise HumanDecisionError("invalid governance comment listing")
        if body.startswith(MARKER_HEADER + "\n"):
            candidate = _parse_marker_body(body)
            if candidate.get("release_id") == marker["release_id"] or candidate.get("nonce") == marker["nonce"]:
                markers += 1
        elif body.startswith(APPROVAL_HEADER + "\n"):
            candidate, _signature = _parse_approval_body(body)
            if candidate.get("release_id") == marker["release_id"] or candidate.get("nonce") == marker["nonce"]:
                approvals += 1
        elif body.startswith(CONSUMPTION_HEADER + "\n") and marker["nonce"] in body:
            consumptions += 1
    if markers != 1 or approvals != 1 or consumptions != 0:
        raise HumanDecisionError("duplicate, replayed, or consumed decision evidence")
    return {
        "schema": DECISION_SCHEMA,
        "purpose": "verified-final-release-human-decision",
        "repository_id": REPOSITORY_ID,
        "repository": REPOSITORY,
        "governance_issue_number": marker["governance_issue_number"],
        "release_id": marker["release_id"],
        "release_sequence": marker["release_sequence"],
        "source_sha": marker["source_sha"],
        "candidate_run_id": marker["candidate_run_id"],
        "candidate_run_attempt": marker["candidate_run_attempt"],
        "manifest_sha256": marker["manifest_sha256"],
        "signing_authorization_sha256": marker["signing_authorization_sha256"],
        "signed_handoff_sha256": marker["signed_handoff_sha256"],
        "signing_workflow_run_id": marker["signing_workflow_run_id"],
        "signing_workflow_run_attempt": marker["signing_workflow_run_attempt"],
        "nonce": marker["nonce"],
        "marker": {key: marker_summary[key] for key in ("id", "node_id", "created_at", "updated_at", "body_sha256", "user")},
        "approval": {key: approval_summary[key] for key in ("id", "node_id", "created_at", "updated_at", "body_sha256", "ssh_signature_sha256", "user")},
        "elapsed_seconds": int(elapsed),
        "minimum_recorded_delay_seconds": MINIMUM_RECORDED_DELAY_SECONDS,
        "ssh_principal": SSH_PRINCIPAL,
        "ssh_namespace": APPROVAL_NAMESPACE,
        "ssh_key_fingerprint": SSH_FINGERPRINT,
        "ssh_github_key_id": SSH_GITHUB_KEY_ID,
    }


def create_consumption(
    *, decision: object, comments: object, decision_run_id: int,
    final_run_id: int, final_run_attempt: int,
) -> tuple[dict[str, object], str]:
    if not isinstance(decision, dict) or decision.get("schema") != DECISION_SCHEMA:
        raise HumanDecisionError("invalid decision evidence")
    if final_run_attempt != 1 or decision_run_id < 1 or final_run_id < 1:
        raise HumanDecisionError("invalid consumption run identity")
    nonce = decision.get("nonce")
    release_id = decision.get("release_id")
    if not isinstance(comments, list):
        raise HumanDecisionError("invalid governance comment listing")
    for item in comments:
        body = item.get("body") if isinstance(item, dict) else None
        if isinstance(body, str) and body.startswith(CONSUMPTION_HEADER + "\n") and (
            str(nonce) in body or str(release_id) in body
        ):
            raise HumanDecisionError("FINAL_APPROVAL already consumed")
    approval = decision.get("approval")
    if not isinstance(approval, dict):
        raise HumanDecisionError("decision approval identity missing")
    payload: dict[str, object] = {
        "schema": CONSUMPTION_SCHEMA,
        "purpose": "single-use-final-workflow-authorization",
        "repository_id": REPOSITORY_ID,
        "repository": REPOSITORY,
        "governance_issue_number": decision.get("governance_issue_number"),
        "release_id": release_id,
        "source_sha": decision.get("source_sha"),
        "nonce": nonce,
        "approval_comment_id": approval.get("id"),
        "approval_body_sha256": approval.get("body_sha256"),
        "decision_workflow_run_id": decision_run_id,
        "final_workflow_run_id": final_run_id,
        "final_workflow_run_attempt": final_run_attempt,
    }
    return payload, consumption_body(payload)


def prepare_approval_payload(*, policy: object, repository: object, issue: object, marker_comment: object) -> dict[str, object]:
    marker, summary = validate_marker_comment(policy=policy, repository=repository, issue=issue, comment=marker_comment)
    payload = {
        "schema": APPROVAL_SCHEMA, "purpose": "final-release-human-decision", "decision": "approved",
        "repository_id": marker["repository_id"], "repository": marker["repository"],
        "governance_issue_number": marker["governance_issue_number"], "release_id": marker["release_id"],
        "release_sequence": marker["release_sequence"], "source_sha": marker["source_sha"],
        "candidate_run_id": marker["candidate_run_id"], "candidate_run_attempt": marker["candidate_run_attempt"],
        "manifest_sha256": marker["manifest_sha256"], "signing_authorization_sha256": marker["signing_authorization_sha256"],
        "signed_handoff_sha256": marker["signed_handoff_sha256"], "marker_comment_id": summary["id"],
        "marker_comment_node_id": summary["node_id"], "marker_body_sha256": summary["body_sha256"],
        "marker_created_at": summary["created_at"], "nonce": marker["nonce"],
    }
    payload = _closed(payload, APPROVAL_KEYS, APPROVAL_SCHEMA)
    _validate_common_payload(payload)
    _time(payload["marker_created_at"])
    return payload

def assemble_approval(*, payload: object, signature: str) -> str:
    payload = _closed(payload, APPROVAL_KEYS, APPROVAL_SCHEMA)
    body = approval_body(payload, signature)
    parsed, parsed_signature = _parse_approval_body(body)
    _verify_ssh_signature(parsed, parsed_signature)
    return body

def _output_reference(payload: dict[str, object], output: pathlib.Path) -> None:
    values = {
        "marker_comment_id": payload.get("marker_comment_id"),
        "issue_number": payload.get("governance_issue_number"),
        "source_sha": payload.get("source_sha"),
    }
    if not all(isinstance(value, (str, int)) for value in values.values()):
        raise HumanDecisionError("invalid approval reference")
    _write_json(output, values)


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)

    marker = commands.add_parser("create-marker")
    marker.add_argument("--policy", required=True)
    marker.add_argument("--repository-json", required=True)
    marker.add_argument("--issue-json", required=True)
    marker.add_argument("--bundle", required=True)
    marker.add_argument("--issue-number", required=True, type=int)
    marker.add_argument("--signing-run-id", required=True, type=int)
    marker.add_argument("--signing-run-attempt", required=True, type=int)
    marker.add_argument("--payload-output", required=True)
    marker.add_argument("--comment-output", required=True)
    marker.add_argument("--request-output", required=True)

    validate_marker = commands.add_parser("validate-marker")
    validate_marker.add_argument("--policy", required=True)
    validate_marker.add_argument("--repository-json", required=True)
    validate_marker.add_argument("--issue-json", required=True)
    validate_marker.add_argument("--comment-json", required=True)
    validate_marker.add_argument("--output", required=True)

    prepare = commands.add_parser("prepare-approval")
    prepare.add_argument("--policy", required=True)
    prepare.add_argument("--repository-json", required=True)
    prepare.add_argument("--issue-json", required=True)
    prepare.add_argument("--marker-json", required=True)
    prepare.add_argument("--payload-output", required=True)

    assemble = commands.add_parser("assemble-approval")
    assemble.add_argument("--payload", required=True)
    assemble.add_argument("--signature", required=True)
    assemble.add_argument("--comment-output", required=True)
    assemble.add_argument("--request-output", required=True)

    reference = commands.add_parser("approval-reference")
    reference.add_argument("--policy", required=True)
    reference.add_argument("--repository-json", required=True)
    reference.add_argument("--issue-json", required=True)
    reference.add_argument("--comment-json", required=True)
    reference.add_argument("--output", required=True)

    verify = commands.add_parser("verify-decision")
    for name in ("policy", "repository-json", "issue-json", "event-json", "marker-json", "approval-json", "comments-json", "bundle", "output"):
        verify.add_argument("--" + name, required=True)

    consume = commands.add_parser("create-consumption")
    consume.add_argument("--decision", required=True)
    consume.add_argument("--comments-json", required=True)
    consume.add_argument("--decision-run-id", required=True, type=int)
    consume.add_argument("--final-run-id", required=True, type=int)
    consume.add_argument("--final-run-attempt", required=True, type=int)
    consume.add_argument("--payload-output", required=True)
    consume.add_argument("--comment-output", required=True)
    consume.add_argument("--request-output", required=True)

    mutation = commands.add_parser("reject-mutation")
    mutation.add_argument("--event-json", required=True)

    args = parser.parse_args()
    try:
        if args.command == "create-marker":
            payload, body = create_marker(
                policy=_load(pathlib.Path(args.policy)),
                repository=_load(pathlib.Path(args.repository_json)),
                issue=_load(pathlib.Path(args.issue_json)),
                bundle=pathlib.Path(args.bundle),
                issue_number=args.issue_number,
                signing_run_id=args.signing_run_id,
                signing_run_attempt=args.signing_run_attempt,
            )
            _write_json(pathlib.Path(args.payload_output), payload)
            pathlib.Path(args.comment_output).write_text(body, encoding="utf-8")
            _write_json(pathlib.Path(args.request_output), {"body": body})
        elif args.command == "validate-marker":
            payload, summary = validate_marker_comment(
                policy=_load(pathlib.Path(args.policy)),
                repository=_load(pathlib.Path(args.repository_json)),
                issue=_load(pathlib.Path(args.issue_json)),
                comment=_load(pathlib.Path(args.comment_json)),
            )
            _write_json(pathlib.Path(args.output), {"payload": payload, "comment": summary})
        elif args.command == "prepare-approval":
            payload = prepare_approval_payload(
                policy=_load(pathlib.Path(args.policy)),
                repository=_load(pathlib.Path(args.repository_json)),
                issue=_load(pathlib.Path(args.issue_json)),
                marker_comment=_load(pathlib.Path(args.marker_json)),
            )
            pathlib.Path(args.payload_output).write_bytes(_canonical_bytes(payload))
        elif args.command == "assemble-approval":
            signature = pathlib.Path(args.signature).read_text(encoding="ascii")
            body = assemble_approval(payload=_load(pathlib.Path(args.payload)), signature=signature)
            pathlib.Path(args.comment_output).write_text(body, encoding="utf-8")
            _write_json(pathlib.Path(args.request_output), {"body": body})
        elif args.command == "approval-reference":
            payload, _summary = validate_approval_comment(
                policy=_load(pathlib.Path(args.policy)),
                repository=_load(pathlib.Path(args.repository_json)),
                issue=_load(pathlib.Path(args.issue_json)),
                comment=_load(pathlib.Path(args.comment_json)),
            )
            _output_reference(payload, pathlib.Path(args.output))
        elif args.command == "verify-decision":
            result = verify_decision(
                policy=_load(pathlib.Path(args.policy)),
                repository=_load(pathlib.Path(args.repository_json)),
                issue=_load(pathlib.Path(args.issue_json)),
                event=_load(pathlib.Path(args.event_json)),
                marker_comment=_load(pathlib.Path(args.marker_json)),
                approval_comment=_load(pathlib.Path(args.approval_json)),
                comments=_load(pathlib.Path(args.comments_json)),
                bundle=pathlib.Path(args.bundle),
            )
            _write_json(pathlib.Path(args.output), result)
        elif args.command == "create-consumption":
            payload, body = create_consumption(
                decision=_load(pathlib.Path(args.decision)),
                comments=_load(pathlib.Path(args.comments_json)),
                decision_run_id=args.decision_run_id,
                final_run_id=args.final_run_id,
                final_run_attempt=args.final_run_attempt,
            )
            _write_json(pathlib.Path(args.payload_output), payload)
            pathlib.Path(args.comment_output).write_text(body, encoding="utf-8")
            _write_json(pathlib.Path(args.request_output), {"body": body})
        else:
            event = _load(pathlib.Path(args.event_json))
            if not isinstance(event, dict) or event.get("action") not in {"edited", "deleted"}:
                raise HumanDecisionError("expected edited/deleted issue_comment event")
            comment = event.get("comment")
            body = comment.get("body") if isinstance(comment, dict) else None
            if isinstance(body, str) and body.startswith((MARKER_HEADER, APPROVAL_HEADER, CONSUMPTION_HEADER)):
                raise HumanDecisionError("governed PATCH-059 comment was edited or deleted")
            raise HumanDecisionError("ambiguous issue_comment mutation fails closed")
    except HumanDecisionError as exc:
        print(f"PATCH-059 Human decision verification failed: {exc}", file=os.sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
