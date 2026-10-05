#!/usr/bin/env python3
"""Create and verify the exact PATCH-059 candidate-evidence identity."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
from typing import Any


SCHEMA = "satco.patch059-candidate-evidence/v2"
WORKFLOW_PATH = ".github/workflows/patch059-candidate-evidence.yml"
EVENT = "workflow_dispatch"
BRANCH = "patch-059-implementation"
SOURCE_SHA = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"sha256:[0-9a-f]{64}\Z")
RELEASE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
EXCEPTION_APPROVER_ID = "github:samiphone651-sys#301386823"
IDENTITY_KEYS = frozenset(
    {
        "schema",
        "repository",
        "workflow_ref",
        "workflow_path",
        "event",
        "branch",
        "source_sha",
        "release_id",
        "run_id",
        "run_attempt",
        "run_url",
        "actor",
        "triggering_actor",
        "security_decision_commit",
        "security_decision_sha256",
    }
)


class CandidateEvidenceError(ValueError):
    pass


def workflow_ref(repository: str) -> str:
    return f"https://github.com/{repository}/{WORKFLOW_PATH}@refs/heads/{BRANCH}"


def _load(path: pathlib.Path) -> object:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                raise CandidateEvidenceError("duplicate JSON member")
            result[key] = value
        return result

    def reject_constant(_value: str) -> None:
        raise CandidateEvidenceError("non-I-JSON constant")

    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=pairs,
            parse_constant=reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CandidateEvidenceError("invalid candidate evidence JSON") from exc


def _digest(path: pathlib.Path) -> str:
    try:
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise CandidateEvidenceError("missing candidate evidence subject") from exc


def _actor(value: object, label: str) -> dict[str, object]:
    if (
        not isinstance(value, dict)
        or set(value) != {"login", "id", "type"}
        or not isinstance(value.get("login"), str)
        or not value["login"]
        or type(value.get("id")) is not int
        or value["id"] < 1
        or value.get("type") not in {"User", "Bot"}
    ):
        raise CandidateEvidenceError(f"invalid candidate {label}")
    return value


def validate_identity(
    document: object,
    *,
    repository: str,
    source_sha: str,
    release_id: str,
    run_id: int | None = None,
    run_attempt: int | None = None,
    security_decision_commit: str | None = None,
    security_decision_sha256: str | None = None,
) -> dict[str, object]:
    if not isinstance(document, dict) or set(document) != IDENTITY_KEYS:
        raise CandidateEvidenceError("closed candidate identity mismatch")
    expected = {
        "schema": SCHEMA,
        "repository": repository,
        "workflow_ref": workflow_ref(repository),
        "workflow_path": WORKFLOW_PATH,
        "event": EVENT,
        "branch": BRANCH,
        "source_sha": source_sha,
        "release_id": release_id,
    }
    for key, value in expected.items():
        if document.get(key) != value:
            raise CandidateEvidenceError(f"candidate {key} mismatch")
    if not SOURCE_SHA.fullmatch(source_sha):
        raise CandidateEvidenceError("invalid candidate source")
    if not RELEASE_ID.fullmatch(release_id):
        raise CandidateEvidenceError("invalid candidate release ID")
    for key in ("run_id", "run_attempt"):
        value = document.get(key)
        if type(value) is not int or value < 1:
            raise CandidateEvidenceError(f"invalid candidate {key}")
    if run_id is not None and document["run_id"] != run_id:
        raise CandidateEvidenceError("candidate run_id mismatch")
    if run_attempt is not None and document["run_attempt"] != run_attempt:
        raise CandidateEvidenceError("candidate run_attempt mismatch")
    _actor(document.get("actor"), "actor")
    _actor(document.get("triggering_actor"), "triggering_actor")
    if not SOURCE_SHA.fullmatch(str(document.get("security_decision_commit", ""))):
        raise CandidateEvidenceError("invalid security decision commit")
    if not SHA256.fullmatch(str(document.get("security_decision_sha256", ""))):
        raise CandidateEvidenceError("invalid security decision digest")
    if (
        security_decision_commit is not None
        and document["security_decision_commit"] != security_decision_commit
    ):
        raise CandidateEvidenceError("candidate security decision commit mismatch")
    if (
        security_decision_sha256 is not None
        and document["security_decision_sha256"] != security_decision_sha256
    ):
        raise CandidateEvidenceError("candidate security decision digest mismatch")
    expected_url = f"https://github.com/{repository}/actions/runs/{document['run_id']}"
    if document.get("run_url") != expected_url:
        raise CandidateEvidenceError("candidate run URL mismatch")
    return document


def validate_run_api(
    run: object,
    identity: dict[str, object],
    *,
    producer_in_progress: bool = False,
) -> None:
    if not isinstance(run, dict):
        raise CandidateEvidenceError("invalid candidate run response")
    repository = identity["repository"]
    expected = {
        "id": identity["run_id"],
        "run_attempt": identity["run_attempt"],
        "path": WORKFLOW_PATH,
        "event": EVENT,
        "head_branch": BRANCH,
        "head_sha": identity["source_sha"],
        "html_url": identity["run_url"],
    }
    for key, value in expected.items():
        if run.get(key) != value:
            raise CandidateEvidenceError(f"candidate run {key} mismatch")
    if producer_in_progress:
        if run.get("status") != "in_progress" or run.get("conclusion") is not None:
            raise CandidateEvidenceError("candidate producer run is not in progress")
    elif run.get("status") != "completed" or run.get("conclusion") != "success":
        raise CandidateEvidenceError("candidate run did not complete successfully")
    for key in ("repository", "head_repository"):
        value = run.get(key)
        if not isinstance(value, dict) or value.get("full_name") != repository:
            raise CandidateEvidenceError(f"candidate run {key} mismatch")
    for key in ("actor", "triggering_actor"):
        value = run.get(key)
        selected = (
            {
                "login": value.get("login"),
                "id": value.get("id"),
                "type": value.get("type"),
            }
            if isinstance(value, dict)
            else None
        )
        if selected != identity[key]:
            raise CandidateEvidenceError(f"candidate run {key} mismatch")


def create_identity(
    run: object,
    *,
    repository: str,
    source_sha: str,
    release_id: str,
    security_decision_commit: str,
    security_decision_path: pathlib.Path,
) -> dict[str, object]:
    if not isinstance(run, dict):
        raise CandidateEvidenceError("invalid candidate run response")

    def selected_actor(key: str) -> dict[str, object | None]:
        value = run.get(key)
        return {
            "login": value.get("login") if isinstance(value, dict) else None,
            "id": value.get("id") if isinstance(value, dict) else None,
            "type": value.get("type") if isinstance(value, dict) else None,
        }

    identity: dict[str, object] = {
        "schema": SCHEMA,
        "repository": repository,
        "workflow_ref": workflow_ref(repository),
        "workflow_path": WORKFLOW_PATH,
        "event": EVENT,
        "branch": BRANCH,
        "source_sha": source_sha,
        "release_id": release_id,
        "run_id": run.get("id"),
        "run_attempt": run.get("run_attempt"),
        "run_url": run.get("html_url"),
        "actor": selected_actor("actor"),
        "triggering_actor": selected_actor("triggering_actor"),
        "security_decision_commit": security_decision_commit,
        "security_decision_sha256": _digest(security_decision_path),
    }
    validated = validate_identity(
        identity,
        repository=repository,
        source_sha=source_sha,
        release_id=release_id,
        security_decision_commit=security_decision_commit,
        security_decision_sha256=_digest(security_decision_path),
    )
    validate_run_api(run, validated, producer_in_progress=True)
    return validated


def validate_exception_authority(path: pathlib.Path) -> None:
    records = _load(path)
    if not isinstance(records, list):
        raise CandidateEvidenceError("invalid High-exception evidence")
    if any(
        not isinstance(record, dict)
        or record.get("approver_id") != EXCEPTION_APPROVER_ID
        for record in records
    ):
        raise CandidateEvidenceError("High exception has wrong Human Authority")


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create")
    verify = subparsers.add_parser("verify")
    for command in (create, verify):
        command.add_argument("--run-json", required=True)
        command.add_argument("--repository", required=True)
        command.add_argument("--source-sha", required=True)
        command.add_argument("--release-id", required=True)
        command.add_argument("--security-decision", required=True)
        command.add_argument("--security-decision-commit", required=True)
        command.add_argument("--exceptions", required=True)
    create.add_argument("--output", required=True)
    verify.add_argument("--identity", required=True)
    verify.add_argument("--run-id", required=True, type=int)
    args = parser.parse_args()
    try:
        run = _load(pathlib.Path(args.run_json))
        decision_path = pathlib.Path(args.security_decision)
        validate_exception_authority(pathlib.Path(args.exceptions))
        if args.command == "create":
            identity = create_identity(
                run,
                repository=args.repository,
                source_sha=args.source_sha,
                release_id=args.release_id,
                security_decision_commit=args.security_decision_commit,
                security_decision_path=decision_path,
            )
            pathlib.Path(args.output).write_text(
                json.dumps(identity, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        else:
            identity = validate_identity(
                _load(pathlib.Path(args.identity)),
                repository=args.repository,
                source_sha=args.source_sha,
                release_id=args.release_id,
                run_id=args.run_id,
                run_attempt=run.get("run_attempt") if isinstance(run, dict) else None,
                security_decision_commit=args.security_decision_commit,
                security_decision_sha256=_digest(decision_path),
            )
            validate_run_api(run, identity)
    except (CandidateEvidenceError, OSError) as exc:
        print(f"BLOCK: {exc}", file=sys.stderr)
        return 2
    print("PATCH059_CANDIDATE_EVIDENCE_VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
