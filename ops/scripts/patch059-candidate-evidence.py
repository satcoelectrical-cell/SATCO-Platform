#!/usr/bin/env python3
"""Create and verify the exact PATCH-059 candidate-evidence identity."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import stat
import sys
import zipfile
from typing import Any


SCHEMA = "satco.patch059-candidate-evidence/v2"
PRE_DECISION_SCHEMA = "satco.patch059-pre-decision-evidence/v1"
PRE_DECISION_ARTIFACT_SCHEMA = "satco.patch059-pre-decision-artifact/v1"
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
PRE_DECISION_GROUPS = {
    "artifact_digests": {
        "backend": "backend-image.oci.tar",
        "frontend": "frontend-dist.tar",
        "migrations": "migration-set.tar",
    },
    "build_input_sha256": {
        "backend-production-lock": "backend-production.lock",
        "backend-uv-lock": "backend-uv.lock",
        "frontend-package-lock": "frontend-package-lock.json",
        "migration-set": "migration-set.sha256",
    },
    "qualification_sha256": {
        "backend": "backend-qualification.json",
        "frontend": "frontend-qualification.json",
        "migration": "migration-qualification.json",
    },
    "scanner_evidence_sha256": {
        "pip-audit": "pip-audit.json",
        "npm-audit": "npm-audit.json",
        "semgrep": "semgrep.json",
        "gitleaks": "gitleaks.json",
        "trivy": "trivy-backend.json",
    },
    "sbom_sha256": {
        "backend": "backend-sbom.cdx.json",
        "frontend": "frontend-sbom.cdx.json",
    },
}
PRE_DECISION_FILES = frozenset(
    filename for files in PRE_DECISION_GROUPS.values() for filename in files.values()
)
PRE_DECISION_ARCHIVE_FILES = PRE_DECISION_FILES | {"pre-decision-evidence.json"}
PRE_DECISION_KEYS = frozenset(
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
        *PRE_DECISION_GROUPS,
        "created_at",
    }
)
PRE_DECISION_ARTIFACT_KEYS = frozenset(
    {
        "schema",
        "repository",
        "source_sha",
        "release_id",
        "run_id",
        "run_attempt",
        "artifact_id",
        "artifact_name",
        "artifact_digest",
        "archive_sha256",
        "pre_decision_evidence_sha256",
    }
)
RFC3339_UTC = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")


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
    digest = hashlib.sha256()
    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise CandidateEvidenceError("unsafe candidate evidence subject")
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        raise CandidateEvidenceError("missing candidate evidence subject") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    return "sha256:" + digest.hexdigest()


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


def _selected_actor(run: dict[str, object], key: str) -> dict[str, object | None]:
    value = run.get(key)
    return {
        "login": value.get("login") if isinstance(value, dict) else None,
        "id": value.get("id") if isinstance(value, dict) else None,
        "type": value.get("type") if isinstance(value, dict) else None,
    }


def _pre_decision_identity(document: dict[str, object]) -> dict[str, object]:
    return {
        key: document[key]
        for key in (
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
        )
    }


def validate_pre_decision(
    document: object,
    *,
    run: object,
    repository: str,
    source_sha: str,
    release_id: str,
    bundle: pathlib.Path,
    producer_in_progress: bool = False,
) -> dict[str, object]:
    if not isinstance(document, dict) or set(document) != PRE_DECISION_KEYS:
        raise CandidateEvidenceError("closed pre-decision evidence mismatch")
    expected = {
        "schema": PRE_DECISION_SCHEMA,
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
            raise CandidateEvidenceError(f"pre-decision {key} mismatch")
    if not RFC3339_UTC.fullmatch(str(document.get("created_at", ""))):
        raise CandidateEvidenceError("invalid pre-decision creation time")
    identity = _pre_decision_identity(document)
    validate_identity_run_shape(identity)
    validate_run_api(run, identity, producer_in_progress=producer_in_progress)
    for group, files in PRE_DECISION_GROUPS.items():
        values = document.get(group)
        if not isinstance(values, dict) or set(values) != set(files):
            raise CandidateEvidenceError(f"closed pre-decision {group} mismatch")
        for name, filename in files.items():
            if values.get(name) != _digest(bundle / filename):
                raise CandidateEvidenceError(f"pre-decision {filename} substitution")
    return document


def validate_identity_run_shape(identity: dict[str, object]) -> None:
    if not SOURCE_SHA.fullmatch(str(identity.get("source_sha", ""))):
        raise CandidateEvidenceError("invalid candidate source")
    if not RELEASE_ID.fullmatch(str(identity.get("release_id", ""))):
        raise CandidateEvidenceError("invalid candidate release ID")
    for key in ("run_id", "run_attempt"):
        if type(identity.get(key)) is not int or int(identity[key]) < 1:
            raise CandidateEvidenceError(f"invalid candidate {key}")
    for key in ("actor", "triggering_actor"):
        _actor(identity.get(key), key.replace("_", " "))
    expected_url = (
        f"https://github.com/{identity['repository']}/actions/runs/{identity['run_id']}"
    )
    if identity.get("run_url") != expected_url:
        raise CandidateEvidenceError("candidate run URL mismatch")


def create_pre_decision(
    run: object,
    *,
    repository: str,
    source_sha: str,
    release_id: str,
    bundle: pathlib.Path,
    created_at: str,
) -> dict[str, object]:
    if not isinstance(run, dict):
        raise CandidateEvidenceError("invalid candidate run response")
    document: dict[str, object] = {
        "schema": PRE_DECISION_SCHEMA,
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
        "actor": _selected_actor(run, "actor"),
        "triggering_actor": _selected_actor(run, "triggering_actor"),
        "created_at": created_at,
    }
    for group, files in PRE_DECISION_GROUPS.items():
        document[group] = {name: _digest(bundle / filename) for name, filename in files.items()}
    return validate_pre_decision(
        document,
        run=run,
        repository=repository,
        source_sha=source_sha,
        release_id=release_id,
        bundle=bundle,
        producer_in_progress=True,
    )


def _validate_artifact_api(
    artifact: object,
    *,
    repository: str,
    artifact_id: int,
    artifact_name: str,
    artifact_digest: str,
    run_id: int,
    source_sha: str,
) -> None:
    if not isinstance(artifact, dict):
        raise CandidateEvidenceError("invalid pre-decision artifact response")
    if (
        artifact.get("id") != artifact_id
        or artifact.get("name") != artifact_name
        or artifact.get("digest") != artifact_digest
        or artifact.get("expired") is not False
        or artifact.get("url")
        != f"https://api.github.com/repos/{repository}/actions/artifacts/{artifact_id}"
        or artifact.get("archive_download_url")
        != f"https://api.github.com/repos/{repository}/actions/artifacts/{artifact_id}/zip"
    ):
        raise CandidateEvidenceError("pre-decision artifact identity mismatch")
    workflow_run = artifact.get("workflow_run")
    if (
        not isinstance(workflow_run, dict)
        or workflow_run.get("id") != run_id
        or workflow_run.get("head_branch") != BRANCH
        or workflow_run.get("head_sha") != source_sha
    ):
        raise CandidateEvidenceError("pre-decision artifact workflow mismatch")


def extract_pre_decision_archive(
    archive: pathlib.Path, *, bundle: pathlib.Path, expected_digest: str
) -> None:
    if _digest(archive) != expected_digest:
        raise CandidateEvidenceError("pre-decision artifact archive digest mismatch")
    bundle.mkdir(parents=True, exist_ok=False)
    try:
        with zipfile.ZipFile(archive) as source:
            members = source.infolist()
            names = [member.filename for member in members if not member.is_dir()]
            if (
                len(members) != len(names)
                or len(names) != len(set(names))
                or set(names) != PRE_DECISION_ARCHIVE_FILES
            ):
                raise CandidateEvidenceError("closed pre-decision archive mismatch")
            for member in members:
                if member.is_dir():
                    continue
                path = pathlib.PurePosixPath(member.filename)
                mode = member.external_attr >> 16
                if (
                    len(path.parts) != 1
                    or path.name != member.filename
                    or (mode and not stat.S_ISREG(mode))
                ):
                    raise CandidateEvidenceError("unsafe pre-decision archive member")
                target = bundle / path.name
                with source.open(member) as input_file, target.open("xb") as output_file:
                    while block := input_file.read(1024 * 1024):
                        output_file.write(block)
    except (OSError, zipfile.BadZipFile) as exc:
        raise CandidateEvidenceError("invalid pre-decision artifact archive") from exc


def validate_pre_decision_archive_contents(
    archive: pathlib.Path, *, bundle: pathlib.Path
) -> None:
    try:
        with zipfile.ZipFile(archive) as source:
            all_members = source.infolist()
            members = [member for member in all_members if not member.is_dir()]
            names = [member.filename for member in members]
            if (
                len(all_members) != len(members)
                or len(names) != len(set(names))
                or set(names) != PRE_DECISION_ARCHIVE_FILES
            ):
                raise CandidateEvidenceError("closed pre-decision archive mismatch")
            for member in members:
                path = pathlib.PurePosixPath(member.filename)
                mode = member.external_attr >> 16
                if (
                    len(path.parts) != 1
                    or path.name != member.filename
                    or (mode and not stat.S_ISREG(mode))
                ):
                    raise CandidateEvidenceError("unsafe pre-decision archive member")
                digest = hashlib.sha256()
                with source.open(member) as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(block)
                archive_digest = "sha256:" + digest.hexdigest()
                if archive_digest != _digest(bundle / member.filename):
                    raise CandidateEvidenceError(
                        f"pre-decision archive {member.filename} substitution"
                    )
    except (OSError, zipfile.BadZipFile) as exc:
        raise CandidateEvidenceError("invalid pre-decision artifact archive") from exc


def bind_pre_decision_artifact(
    *,
    run: object,
    artifact: object,
    repository: str,
    source_sha: str,
    release_id: str,
    run_id: int,
    run_attempt: int,
    artifact_id: int,
    artifact_name: str,
    artifact_digest: str,
    archive: pathlib.Path,
    bundle: pathlib.Path,
) -> dict[str, object]:
    if not SHA256.fullmatch(artifact_digest):
        raise CandidateEvidenceError("invalid pre-decision artifact digest")
    _validate_artifact_api(
        artifact,
        repository=repository,
        artifact_id=artifact_id,
        artifact_name=artifact_name,
        artifact_digest=artifact_digest,
        run_id=run_id,
        source_sha=source_sha,
    )
    extract_pre_decision_archive(archive, bundle=bundle, expected_digest=artifact_digest)
    evidence_path = bundle / "pre-decision-evidence.json"
    evidence = validate_pre_decision(
        _load(evidence_path),
        run=run,
        repository=repository,
        source_sha=source_sha,
        release_id=release_id,
        bundle=bundle,
    )
    if evidence["run_id"] != run_id or evidence["run_attempt"] != run_attempt:
        raise CandidateEvidenceError("pre-decision run binding mismatch")
    return {
        "schema": PRE_DECISION_ARTIFACT_SCHEMA,
        "repository": repository,
        "source_sha": source_sha,
        "release_id": release_id,
        "run_id": run_id,
        "run_attempt": run_attempt,
        "artifact_id": artifact_id,
        "artifact_name": artifact_name,
        "artifact_digest": artifact_digest,
        "archive_sha256": _digest(archive),
        "pre_decision_evidence_sha256": _digest(evidence_path),
    }


def validate_pre_decision_artifact_identity(
    document: object, *, evidence_path: pathlib.Path, archive_path: pathlib.Path
) -> dict[str, object]:
    if not isinstance(document, dict) or set(document) != PRE_DECISION_ARTIFACT_KEYS:
        raise CandidateEvidenceError("closed pre-decision artifact binding mismatch")
    if document.get("schema") != PRE_DECISION_ARTIFACT_SCHEMA:
        raise CandidateEvidenceError("pre-decision artifact schema mismatch")
    for key in ("run_id", "run_attempt", "artifact_id"):
        if type(document.get(key)) is not int or int(document[key]) < 1:
            raise CandidateEvidenceError(f"invalid pre-decision artifact {key}")
    for key in ("artifact_digest", "archive_sha256", "pre_decision_evidence_sha256"):
        if not SHA256.fullmatch(str(document.get(key, ""))):
            raise CandidateEvidenceError(f"invalid pre-decision artifact {key}")
    if document["artifact_digest"] != document["archive_sha256"]:
        raise CandidateEvidenceError("pre-decision archive binding mismatch")
    if document["archive_sha256"] != _digest(archive_path):
        raise CandidateEvidenceError("pre-decision archive substitution")
    if document["pre_decision_evidence_sha256"] != _digest(evidence_path):
        raise CandidateEvidenceError("pre-decision evidence substitution")
    return document


def verify_pre_decision_custody(
    *,
    identity: object,
    evidence: object,
    run: object,
    artifact: object,
    repository: str,
    source_sha: str,
    release_id: str,
    archive_path: pathlib.Path,
    bundle: pathlib.Path,
) -> None:
    bound = validate_pre_decision_artifact_identity(
        identity,
        evidence_path=bundle / "pre-decision-evidence.json",
        archive_path=archive_path,
    )
    expected_name = f"patch059-pre-decision-{source_sha}-{release_id}"
    if (
        bound.get("repository") != repository
        or bound.get("source_sha") != source_sha
        or bound.get("release_id") != release_id
        or bound.get("artifact_name") != expected_name
    ):
        raise CandidateEvidenceError("pre-decision artifact candidate mismatch")
    validated = validate_pre_decision(
        evidence,
        run=run,
        repository=repository,
        source_sha=source_sha,
        release_id=release_id,
        bundle=bundle,
    )
    if (
        validated["run_id"] != bound["run_id"]
        or validated["run_attempt"] != bound["run_attempt"]
    ):
        raise CandidateEvidenceError("pre-decision custody run mismatch")
    _validate_artifact_api(
        artifact,
        repository=repository,
        artifact_id=int(bound["artifact_id"]),
        artifact_name=str(bound["artifact_name"]),
        artifact_digest=str(bound["artifact_digest"]),
        run_id=int(bound["run_id"]),
        source_sha=source_sha,
    )
    validate_pre_decision_archive_contents(archive_path, bundle=bundle)


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
        "actor": _selected_actor(run, "actor"),
        "triggering_actor": _selected_actor(run, "triggering_actor"),
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
    verify.add_argument("--pre-decision-evidence", required=True)
    verify.add_argument("--pre-decision-artifact", required=True)
    verify.add_argument("--pre-decision-run-json", required=True)
    verify.add_argument("--pre-decision-artifact-json", required=True)
    verify.add_argument("--pre-decision-archive", required=True)
    verify.add_argument("--bundle", required=True)
    pre_create = subparsers.add_parser("create-pre-decision")
    pre_create.add_argument("--run-json", required=True)
    pre_create.add_argument("--repository", required=True)
    pre_create.add_argument("--source-sha", required=True)
    pre_create.add_argument("--release-id", required=True)
    pre_create.add_argument("--bundle", required=True)
    pre_create.add_argument("--created-at", required=True)
    pre_create.add_argument("--output", required=True)
    pre_bind = subparsers.add_parser("bind-pre-decision-artifact")
    pre_bind.add_argument("--run-json", required=True)
    pre_bind.add_argument("--artifact-json", required=True)
    pre_bind.add_argument("--repository", required=True)
    pre_bind.add_argument("--source-sha", required=True)
    pre_bind.add_argument("--release-id", required=True)
    pre_bind.add_argument("--run-id", required=True, type=int)
    pre_bind.add_argument("--run-attempt", required=True, type=int)
    pre_bind.add_argument("--artifact-id", required=True, type=int)
    pre_bind.add_argument("--artifact-name", required=True)
    pre_bind.add_argument("--artifact-digest", required=True)
    pre_bind.add_argument("--archive", required=True)
    pre_bind.add_argument("--bundle", required=True)
    pre_bind.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        if args.command == "create-pre-decision":
            run = _load(pathlib.Path(args.run_json))
            document = create_pre_decision(
                run,
                repository=args.repository,
                source_sha=args.source_sha,
                release_id=args.release_id,
                bundle=pathlib.Path(args.bundle),
                created_at=args.created_at,
            )
            pathlib.Path(args.output).write_text(
                json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        elif args.command == "bind-pre-decision-artifact":
            document = bind_pre_decision_artifact(
                run=_load(pathlib.Path(args.run_json)),
                artifact=_load(pathlib.Path(args.artifact_json)),
                repository=args.repository,
                source_sha=args.source_sha,
                release_id=args.release_id,
                run_id=args.run_id,
                run_attempt=args.run_attempt,
                artifact_id=args.artifact_id,
                artifact_name=args.artifact_name,
                artifact_digest=args.artifact_digest,
                archive=pathlib.Path(args.archive),
                bundle=pathlib.Path(args.bundle),
            )
            pathlib.Path(args.output).write_text(
                json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        else:
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
                verify_pre_decision_custody(
                    identity=_load(pathlib.Path(args.pre_decision_artifact)),
                    evidence=_load(pathlib.Path(args.pre_decision_evidence)),
                    run=_load(pathlib.Path(args.pre_decision_run_json)),
                    artifact=_load(pathlib.Path(args.pre_decision_artifact_json)),
                    repository=args.repository,
                    source_sha=args.source_sha,
                    release_id=args.release_id,
                    archive_path=pathlib.Path(args.pre_decision_archive),
                    bundle=pathlib.Path(args.bundle),
                )
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
