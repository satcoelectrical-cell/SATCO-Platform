"""PATCH-059 release-evidence verification fixtures; no fixture is real approval."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import zipfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _module(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    assert spec and spec.loader
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


release_evidence = _module(
    "patch059_release_evidence", "ops/scripts/patch059-release-evidence.py"
)
candidate_evidence = _module(
    "patch059_candidate_evidence", "ops/scripts/patch059-candidate-evidence.py"
)

REPOSITORY = "satcoelectrical-cell/SATCO-Platform"
SOURCE = "a" * 40
RELEASE_ID = "patch059-fixture-only"
SEQUENCE = 59
ISSUER = "https://token.actions.githubusercontent.com"
WORKFLOW = (
    "https://github.com/satcoelectrical-cell/SATCO-Platform/.github/workflows/"
    "patch059-sign-release.yml@refs/heads/patch-059-implementation"
)
NOW = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)
HUMAN = {"login": "samiphone651-sys", "id": 301386823, "type": "User"}
BOT_POLICY = {
    "status": "CONFIGURED",
    "login": "fixture-dispatcher[bot]",
    "id": 987654,
    "type": "Bot",
    "app_id": 7654,
    "installation_id": 8765,
}
BOT_ACTOR = {
    "login": BOT_POLICY["login"],
    "id": BOT_POLICY["id"],
    "type": "Bot",
}


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _subjects(values: dict[str, str]) -> list[dict[str, object]]:
    return [
        {"name": name, "digest": {"sha256": digest.removeprefix("sha256:")}}
        for name, digest in sorted(values.items())
    ]


def _policy(tmp_path: Path) -> Path:
    document = json.loads(
        (ROOT / "ops/patch059-single-human-authority-policy.example.v1.json")
        .read_text(encoding="utf-8")
    )
    document["dispatcher"] = deepcopy(BOT_POLICY)
    path = tmp_path / "single-human-authority-policy.v1.json"
    _write(path, document)
    return path


def _protected_run(run_id: int = 700) -> dict[str, object]:
    return {
        "id": run_id,
        "run_attempt": 1,
        "path": ".github/workflows/patch059-sign-release.yml",
        "event": "workflow_dispatch",
        "head_branch": "patch-059-implementation",
        "head_sha": SOURCE,
        "html_url": f"https://github.com/{REPOSITORY}/actions/runs/{run_id}",
        "repository": {"full_name": REPOSITORY},
        "head_repository": {"full_name": REPOSITORY},
        "actor": deepcopy(BOT_ACTOR),
        "triggering_actor": deepcopy(BOT_ACTOR),
    }


def _candidate_run(*, producer: bool = False) -> dict[str, object]:
    return {
        "id": 123456,
        "run_attempt": 2,
        "path": ".github/workflows/patch059-candidate-evidence.yml",
        "event": "workflow_dispatch",
        "head_branch": "patch-059-implementation",
        "head_sha": SOURCE,
        "status": "in_progress" if producer else "completed",
        "conclusion": None if producer else "success",
        "html_url": f"https://github.com/{REPOSITORY}/actions/runs/123456",
        "repository": {"full_name": REPOSITORY},
        "head_repository": {"full_name": REPOSITORY},
        "actor": deepcopy(HUMAN),
        "triggering_actor": deepcopy(HUMAN),
    }


def _pre_decision_fixture(tmp_path: Path):
    source = tmp_path / "pre-source"
    source.mkdir()
    for filename in candidate_evidence.PRE_DECISION_FILES:
        (source / filename).write_bytes(("pre-decision:" + filename).encode("utf-8"))
    producer_run = _candidate_run(producer=True)
    evidence = candidate_evidence.create_pre_decision(
        producer_run,
        repository=REPOSITORY,
        source_sha=SOURCE,
        release_id=RELEASE_ID,
        bundle=source,
        created_at="2026-10-03T09:00:00Z",
    )
    _write(source / "pre-decision-evidence.json", evidence)
    archive = tmp_path / "pre-decision.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as output:
        for filename in sorted(candidate_evidence.PRE_DECISION_ARCHIVE_FILES):
            output.write(source / filename, filename)
    digest = _digest(archive)
    artifact = {
        "id": 7654321,
        "name": f"patch059-pre-decision-{SOURCE}-{RELEASE_ID}",
        "digest": digest,
        "expired": False,
        "url": f"https://api.github.com/repos/{REPOSITORY}/actions/artifacts/7654321",
        "archive_download_url": f"https://api.github.com/repos/{REPOSITORY}/actions/artifacts/7654321/zip",
        "workflow_run": {
            "id": producer_run["id"],
            "head_branch": "patch-059-implementation",
            "head_sha": SOURCE,
        },
    }
    return source, archive, evidence, artifact


def _environment(stage: str) -> tuple[dict[str, object], dict[str, object]]:
    final = stage == "final"
    branches = ["patch-059-implementation"] if final else ["patch-058", "patch-059-implementation"]
    rules: list[dict[str, object]] = [
        {
            "type": "required_reviewers",
            "prevent_self_review": True,
            "reviewers": [{"type": "User", "reviewer": deepcopy(HUMAN)}],
        },
        {"type": "branch_policy"},
    ]
    if final:
        rules.append({"type": "wait_timer", "wait_timer": 15})
    return (
        {
            "name": "patch059-final-release-approval" if final else "patch058-protected-release",
            "can_admins_bypass": False,
            "deployment_branch_policy": {
                "protected_branches": False,
                "custom_branch_policies": True,
            },
            "protection_rules": rules,
        },
        {
            "total_count": len(branches),
            "branch_policies": [
                {"id": index, "node_id": f"node-{index}", "name": name, "type": "branch"}
                for index, name in enumerate(branches, start=1)
            ],
        },
    )


def _approval(environment: str, comment: str, _submitted_at: str) -> list[dict[str, object]]:
    # Real GitHub Environment review history has no Human submitted_at field.
    return [
        {
            "state": "approved",
            "comment": comment,
            "user": deepcopy(HUMAN),
            "environments": [{"name": environment}],
        }
    ]


def _fixture(tmp_path: Path) -> dict[str, object]:
    policy_path = _policy(tmp_path)
    artifacts = {
        "backend": tmp_path / "backend-image.oci.tar",
        "frontend": tmp_path / "frontend-dist.tar",
        "migrations": tmp_path / "migration-set.tar",
    }
    for name, path in artifacts.items():
        path.write_bytes(("fixture-" + name).encode("ascii"))
    digests = {name: _digest(path) for name, path in artifacts.items()}

    _write(tmp_path / "resolved-high-exceptions.json", [])
    decision = {
        "schemaVersion": "PATCH-058-security-decision-v1",
        "mode": "post-build-human-decision",
        "candidateRevision": SOURCE,
        "artifactDigest": digests["backend"],
        "exceptionEvidenceDigest": _digest(tmp_path / "resolved-high-exceptions.json"),
        "decisionCommit": "b" * 40,
        "decisionRef": "refs/heads/patch-058-security-decisions",
    }
    _write(tmp_path / "security-decision.json", decision)
    candidate = candidate_evidence.create_identity(
        _candidate_run(producer=True),
        repository=REPOSITORY,
        source_sha=SOURCE,
        release_id=RELEASE_ID,
        security_decision_commit=decision["decisionCommit"],
        security_decision_path=tmp_path / "security-decision.json",
    )
    _write(tmp_path / "candidate-identity.json", candidate)
    _write(
        tmp_path / "provenance.intoto.json",
        {
            "subject": _subjects(digests),
            "predicate": {
                "buildDefinition": {
                    "externalParameters": {
                        "repository": REPOSITORY,
                        "revision": SOURCE,
                        "releaseId": RELEASE_ID,
                    }
                }
            },
        },
    )

    run_path = tmp_path / "protected-run.json"
    sign_env_path = tmp_path / "signing-environment.json"
    sign_branches_path = tmp_path / "signing-branch-policies.json"
    sign_approvals_path = tmp_path / "signing-approvals.json"
    _write(run_path, _protected_run())
    signing_environment, signing_branches = _environment("signing")
    _write(sign_env_path, signing_environment)
    _write(sign_branches_path, signing_branches)
    sign_comment = (
        f"SIGN PATCH-059 release_id={RELEASE_ID} source_sha={SOURCE} "
        "candidate_run_id=123456 candidate_run_attempt=2"
    )
    _write(
        sign_approvals_path,
        _approval("patch058-protected-release", sign_comment, "2026-10-03T10:00:00Z"),
    )
    signing = release_evidence.create_signing_authorization(
        policy_path=policy_path,
        run_path=run_path,
        environment_path=sign_env_path,
        branch_policies_path=sign_branches_path,
        approvals_path=sign_approvals_path,
        bundle=tmp_path,
        repository=REPOSITORY,
        release_id=RELEASE_ID,
        source_sha=SOURCE,
    )
    _write(tmp_path / "human-signing-authorization.json", signing)

    _write(tmp_path / "signature-verification-summary.json", {"source_commit": SOURCE})
    for expected_files in release_evidence.DOSSIER_SECTION_FILES.values():
        for filename in expected_files.values():
            path = tmp_path / filename
            if not path.exists():
                if path.suffix == ".json":
                    _write(path, {"fixture": filename})
                else:
                    path.write_bytes(b"fixture")
    pre_decision = candidate_evidence.create_pre_decision(
        _candidate_run(producer=True),
        repository=REPOSITORY,
        source_sha=SOURCE,
        release_id=RELEASE_ID,
        bundle=tmp_path,
        created_at="2026-10-03T09:00:00Z",
    )
    _write(tmp_path / "pre-decision-evidence.json", pre_decision)
    pre_archive = tmp_path / "pre-decision-artifact.zip"
    with zipfile.ZipFile(pre_archive, "w", compression=zipfile.ZIP_STORED) as output:
        for filename in sorted(candidate_evidence.PRE_DECISION_ARCHIVE_FILES):
            output.write(tmp_path / filename, filename)
    pre_archive_digest = _digest(pre_archive)
    pre_artifact_api = {
        "id": 7654321,
        "name": f"patch059-pre-decision-{SOURCE}-{RELEASE_ID}",
        "digest": pre_archive_digest,
        "expired": False,
        "url": f"https://api.github.com/repos/{REPOSITORY}/actions/artifacts/7654321",
        "archive_download_url": f"https://api.github.com/repos/{REPOSITORY}/actions/artifacts/7654321/zip",
        "workflow_run": {
            "id": 123456,
            "head_branch": "patch-059-implementation",
            "head_sha": SOURCE,
        },
    }
    _write(tmp_path / "pre-decision-run.json", _candidate_run())
    _write(tmp_path / "pre-decision-artifact-api.json", pre_artifact_api)
    _write(
        tmp_path / "pre-decision-artifact.json",
        {
            "schema": "satco.patch059-pre-decision-artifact/v1",
            "repository": REPOSITORY,
            "source_sha": SOURCE,
            "release_id": RELEASE_ID,
            "run_id": 123456,
            "run_attempt": 2,
            "artifact_id": 7654321,
            "artifact_name": pre_artifact_api["name"],
            "artifact_digest": pre_archive_digest,
            "archive_sha256": pre_archive_digest,
            "pre_decision_evidence_sha256": _digest(
                tmp_path / "pre-decision-evidence.json"
            ),
        },
    )
    provenance = json.loads((tmp_path / "provenance.intoto.json").read_text())
    provenance["predicate"]["satco"] = {
        "qualificationEvidence": [
            {
                "name": name,
                "digest": {"sha256": _digest(tmp_path / filename).removeprefix("sha256:")},
            }
            for name, filename in sorted(
                release_evidence.PRE_DECISION_PROVENANCE_FILES.items()
            )
        ]
    }
    _write(tmp_path / "provenance.intoto.json", provenance)
    dossier_sections = {
        section: {
            name: {"reference": filename, "digest": _digest(tmp_path / filename)}
            for name, filename in expected_files.items()
        }
        for section, expected_files in release_evidence.DOSSIER_SECTION_FILES.items()
    }
    dossier = {
        "schema_version": "v1",
        "release_id": RELEASE_ID,
        "source_commit": SOURCE,
        **dossier_sections,
        "provenance": {
            "reference": "provenance.intoto.json",
            "digest": _digest(tmp_path / "provenance.intoto.json"),
        },
        "signature_verification": {
            "reference": "signature-verification-summary.json",
            "digest": _digest(tmp_path / "signature-verification-summary.json"),
        },
        "human_signing_authorization": {
            "status": "approved",
            "reference": "human-signing-authorization.json",
            "digest": _digest(tmp_path / "human-signing-authorization.json"),
        },
        "human_release_approval": {
            "status": "pending",
            "reference": "patch059-final-release-approval",
        },
        "created_at": "2026-10-03T10:01:00Z",
    }
    _write(tmp_path / "release-dossier.pending.v1.json", dossier)
    manifest = {
        "schema": "satco.patch059-release-manifest/v1",
        "release_id": RELEASE_ID,
        "release_sequence": SEQUENCE,
        "source_sha": SOURCE,
        "artifacts": digests,
        "expected_alembic_head": "e05900000002",
        "configuration_schema": "v1",
        "candidate_identity_sha256": _digest(tmp_path / "candidate-identity.json"),
        "provenance_sha256": _digest(tmp_path / "provenance.intoto.json"),
        "dossier_sha256": _digest(tmp_path / "release-dossier.pending.v1.json"),
        "created_at": "2026-10-03T10:02:00Z",
    }
    _write(tmp_path / "release-manifest.v1.json", manifest)
    manifest_digest = _digest(tmp_path / "release-manifest.v1.json")
    _write(
        tmp_path / "release-provenance.intoto.json",
        {
            "subject": _subjects(digests | {"manifest": manifest_digest}),
            "predicate": {
                "buildDefinition": {
                    "externalParameters": {
                        "releaseId": RELEASE_ID,
                        "releaseSequence": SEQUENCE,
                        "repository": REPOSITORY,
                        "revision": SOURCE,
                        "workflow": WORKFLOW,
                        "candidateEvidence": candidate,
                    }
                }
            },
        },
    )
    handoff = release_evidence.create_signed_handoff(
        policy_path=policy_path,
        bundle=tmp_path,
        release_id=RELEASE_ID,
        release_sequence=SEQUENCE,
        source_sha=SOURCE,
        workflow_run_id=700,
        workflow_run_attempt=1,
        created_at="2026-10-03T10:15:00Z",
    )
    _write(tmp_path / "signed-candidate-handoff.v1.json", handoff)

    final_env_path = tmp_path / "final-environment.json"
    final_branches_path = tmp_path / "final-branch-policies.json"
    final_approvals_path = tmp_path / "final-approvals.json"
    final_run_path = tmp_path / "final-run.json"
    _write(final_run_path, _protected_run(800))
    final_environment, final_branches = _environment("final")
    _write(final_env_path, final_environment)
    _write(final_branches_path, final_branches)
    final_decision = {
        "schema": "satco.patch059-final-decision-evidence/v1",
        "purpose": "verified-final-release-human-decision",
        "repository_id": 1311705732,
        "repository": REPOSITORY,
        "governance_issue_number": 59,
        "release_id": RELEASE_ID,
        "release_sequence": SEQUENCE,
        "source_sha": SOURCE,
        "candidate_run_id": 123456,
        "candidate_run_attempt": 2,
        "manifest_sha256": manifest_digest,
        "signing_authorization_sha256": _digest(tmp_path / "human-signing-authorization.json"),
        "signed_handoff_sha256": _digest(tmp_path / "signed-candidate-handoff.v1.json"),
        "signing_workflow_run_id": 700,
        "signing_workflow_run_attempt": 1,
        "nonce": "d" * 64,
        "marker": {"id": 10, "node_id": "marker", "created_at": "2026-10-03T10:15:00Z", "updated_at": "2026-10-03T10:15:00Z", "body_sha256": "sha256:" + "1" * 64, "user": {"login": "github-actions[bot]", "id": 41898282, "type": "Bot"}},
        "approval": {"id": 11, "node_id": "approval", "created_at": "2026-10-03T10:30:05Z", "updated_at": "2026-10-03T10:30:05Z", "body_sha256": "sha256:" + "2" * 64, "ssh_signature_sha256": "sha256:" + "3" * 64, "user": deepcopy(HUMAN)},
        "elapsed_seconds": 905,
        "minimum_recorded_delay_seconds": 905,
        "ssh_principal": "samiphone651-sys",
        "ssh_namespace": "satco-patch059-final-approval-v1",
        "ssh_key_fingerprint": "SHA256:0QRoi7nAjRewgACw6V18QJzePt7MdhPr01zpaTJbojw",
        "ssh_github_key_id": 1219405,
    }
    _write(tmp_path / "final-decision-evidence.json", final_decision)
    final_decision_digest = _digest(tmp_path / "final-decision-evidence.json")
    final_comment = (
        f"FINALIZE PATCH-059 release_id={RELEASE_ID} release_sequence={SEQUENCE} "
        f"source_sha={SOURCE} final_decision_comment_id=11 "
        f"final_decision_sha256={final_decision_digest} "
        f"final_decision_body_sha256={final_decision['approval']['body_sha256']}"
    )
    _write(final_approvals_path, _approval("patch059-final-release-approval", final_comment, "2026-10-03T10:31:00Z"))
    approval = release_evidence.create_final_approval(
        policy_path=policy_path,
        run_path=final_run_path,
        environment_path=final_env_path,
        branch_policies_path=final_branches_path,
        approvals_path=final_approvals_path,
        decision_path=tmp_path / "final-decision-evidence.json",
        bundle=tmp_path,
        repository=REPOSITORY,
        release_id=RELEASE_ID,
        release_sequence=SEQUENCE,
        source_sha=SOURCE,
    )
    _write(tmp_path / "human-release-approval.json", approval)
    finalization = release_evidence.create_finalization(
        policy_path=policy_path,
        bundle=tmp_path,
        repository=REPOSITORY,
        issuer=ISSUER,
        workflow_ref=WORKFLOW,
        finalized_at="2026-10-03T10:31:00Z",
    )
    _write(tmp_path / "release-finalization.v2.json", finalization)
    return {
        "manifest": manifest,
        "signing": signing,
        "handoff": handoff,
        "approval": approval,
        "finalization": finalization,
        "manifest_digest": manifest_digest.removeprefix("sha256:"),
    }


@pytest.fixture(autouse=True)
def _stub_final_human_decision_verifier(monkeypatch):
    def verify(root):
        return json.loads((root / "final-decision-evidence.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(release_evidence, "_verify_final_human_decision", verify)

class FixtureCosign:
    """Deterministic test double; explicitly not protected signing."""

    def __init__(self, *, reject: bool = False):
        self.reject = reject
        self.commands: list[list[str]] = []

    def __call__(self, command, **_kwargs):
        self.commands.append(command)
        if self.reject and command[1] != "version":
            raise subprocess.CalledProcessError(1, command)
        output = "cosign v2.6.0" if command[1] == "version" else "Verified OK"
        return subprocess.CompletedProcess(command, 0, stdout=output, stderr="")


def _verify(tmp_path: Path, state: dict[str, object], runner=None):
    return release_evidence.verify_bundle(
        tmp_path,
        repository=REPOSITORY,
        issuer=ISSUER,
        workflow_ref=WORKFLOW,
        source_sha=SOURCE,
        release_id=RELEASE_ID,
        release_sequence=SEQUENCE,
        manifest_sha256=state["manifest_digest"],
        now=NOW,
        runner=runner or FixtureCosign(),
    )


def test_offline_verifier_accepts_fully_bound_v2_bundle(tmp_path):
    state = _fixture(tmp_path)
    runner = FixtureCosign()
    assert _verify(tmp_path, state, runner)["release_id"] == RELEASE_ID
    verified = [command for command in runner.commands if command[1] == "verify-blob"]
    assert {Path(command[-1]).name for command in verified} == {
        "backend-image.oci.tar",
        "frontend-dist.tar",
        "migration-set.tar",
        "release-manifest.v1.json",
        "human-release-approval.json",
        "release-finalization.v2.json",
    }


@pytest.mark.parametrize(
    ("filename", "key", "value"),
    [
        ("candidate-identity.json", "event", "push"),
        ("candidate-identity.json", "security_decision_commit", "c" * 40),
        ("pre-decision-artifact.json", "source_sha", "c" * 40),
        ("human-signing-authorization.json", "authority", {"login": "other", "id": 1, "type": "User"}),
        ("signed-candidate-handoff.v1.json", "workflow_run_attempt", 2),
        ("human-release-approval.json", "minimum_delay_seconds", 0),
        ("release-finalization.v2.json", "repository", "attacker/fork"),
    ],
)
def test_offline_verifier_rejects_identity_authority_and_binding_mutations(
    tmp_path, filename, key, value
):
    state = _fixture(tmp_path)
    path = tmp_path / filename
    document = json.loads(path.read_text(encoding="utf-8"))
    document[key] = value
    _write(path, document)
    with pytest.raises(release_evidence.ReleaseVerificationError):
        _verify(tmp_path, state)



@pytest.mark.parametrize(
    "evidence_name",
    sorted(release_evidence.PRE_DECISION_PROVENANCE_FILES),
)
def test_offline_verifier_rejects_missing_pre_decision_provenance_binding(
    tmp_path, evidence_name
):
    state = _fixture(tmp_path)
    provenance_path = tmp_path / "provenance.intoto.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    evidence = provenance["predicate"]["satco"]["qualificationEvidence"]
    provenance["predicate"]["satco"]["qualificationEvidence"] = [
        descriptor
        for descriptor in evidence
        if descriptor["name"] != evidence_name
    ]
    _write(provenance_path, provenance)

    manifest_path = tmp_path / "release-manifest.v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["provenance_sha256"] = _digest(provenance_path)
    _write(manifest_path, manifest)
    state["manifest_digest"] = _digest(manifest_path).removeprefix("sha256:")

    with pytest.raises(
        release_evidence.ReleaseVerificationError,
        match="candidate pre-decision provenance mismatch",
    ):
        _verify(tmp_path, state)


@pytest.mark.parametrize(
    "evidence_name",
    sorted(release_evidence.PRE_DECISION_PROVENANCE_FILES),
)
def test_offline_verifier_rejects_substituted_pre_decision_provenance_digest(
    tmp_path, evidence_name
):
    state = _fixture(tmp_path)
    provenance_path = tmp_path / "provenance.intoto.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))

    for descriptor in provenance["predicate"]["satco"]["qualificationEvidence"]:
        if descriptor["name"] == evidence_name:
            descriptor["digest"]["sha256"] = "0" * 64
            break
    else:
        raise AssertionError(f"fixture missing {evidence_name}")

    _write(provenance_path, provenance)

    manifest_path = tmp_path / "release-manifest.v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["provenance_sha256"] = _digest(provenance_path)
    _write(manifest_path, manifest)
    state["manifest_digest"] = _digest(manifest_path).removeprefix("sha256:")

    with pytest.raises(
        release_evidence.ReleaseVerificationError,
        match="candidate pre-decision provenance mismatch",
    ):
        _verify(tmp_path, state)


def test_offline_verifier_rejects_unresolved_dispatcher_policy(tmp_path):
    state = _fixture(tmp_path)
    unresolved = json.loads(
        (ROOT / "ops/patch059-single-human-authority-policy.example.v1.json")
        .read_text(encoding="utf-8")
    )
    _write(tmp_path / "single-human-authority-policy.v1.json", unresolved)
    with pytest.raises(release_evidence.ReleaseVerificationError, match="dispatcher identity unresolved"):
        _verify(tmp_path, state)


def test_offline_verifier_rejects_reused_approval_event(tmp_path):
    state = _fixture(tmp_path)
    approval = deepcopy(state["approval"])
    approval["approval_event_sha256"] = state["signing"]["approval_event_sha256"]
    _write(tmp_path / "human-release-approval.json", approval)
    with pytest.raises(release_evidence.ReleaseVerificationError):
        _verify(tmp_path, state)


@pytest.mark.parametrize("snapshot", ["protected-run.json", "final-run.json"])
def test_offline_verifier_rejects_retained_dispatcher_snapshot_substitution(
    tmp_path, snapshot
):
    state = _fixture(tmp_path)
    path = tmp_path / snapshot
    document = json.loads(path.read_text(encoding="utf-8"))
    document["actor"] = deepcopy(HUMAN)
    _write(path, document)
    with pytest.raises(release_evidence.ReleaseVerificationError):
        _verify(tmp_path, state)


def test_offline_verifier_rejects_retained_environment_snapshot_substitution(tmp_path):
    state = _fixture(tmp_path)
    path = tmp_path / "final-environment.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["protection_rules"][0]["prevent_self_review"] = False
    _write(path, document)
    with pytest.raises(release_evidence.ReleaseVerificationError):
        _verify(tmp_path, state)


def test_offline_verifier_rejects_any_raw_api_snapshot_byte_change(tmp_path):
    state = _fixture(tmp_path)
    path = tmp_path / "protected-run.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["otherwise_unused_api_field"] = "changed"
    _write(path, document)
    with pytest.raises(release_evidence.ReleaseVerificationError):
        _verify(tmp_path, state)


def test_offline_verifier_rejects_same_signing_and_final_run(tmp_path):
    state = _fixture(tmp_path)
    _write(tmp_path / "final-run.json", _protected_run(700))
    with pytest.raises(release_evidence.ReleaseVerificationError):
        _verify(tmp_path, state)


def test_final_approval_generator_rejects_less_than_recorded_threshold(tmp_path):
    _fixture(tmp_path)
    decision_path = tmp_path / "final-decision-evidence.json"
    decision = json.loads(decision_path.read_text())
    decision["elapsed_seconds"] = 904
    _write(decision_path, decision)
    with pytest.raises(release_evidence.ReleaseVerificationError):
        release_evidence.create_final_approval(
            policy_path=tmp_path / "single-human-authority-policy.v1.json",
            run_path=tmp_path / "final-run.json",
            environment_path=tmp_path / "final-environment.json",
            branch_policies_path=tmp_path / "final-branch-policies.json",
            approvals_path=tmp_path / "final-approvals.json",
            decision_path=decision_path,
            bundle=tmp_path,
            repository=REPOSITORY,
            release_id=RELEASE_ID,
            release_sequence=SEQUENCE,
            source_sha=SOURCE,
        )


def test_offline_verifier_rejects_unauthenticated_fixture(tmp_path):
    state = _fixture(tmp_path)
    with pytest.raises(subprocess.CalledProcessError):
        _verify(tmp_path, state, FixtureCosign(reject=True))


def test_protected_workflow_is_narrow_separate_and_fail_closed():
    workflow = (ROOT / ".github/workflows/patch059-sign-release.yml").read_text(encoding="utf-8")
    assert "preflight:" in workflow
    assert "needs: preflight" in workflow
    assert "environment: patch058-protected-release" in workflow
    assert "environment: patch059-final-release-approval" in workflow
    assert "gate-run" in workflow
    assert "--policy ops/patch059-single-human-authority-policy.v1.json" in workflow
    assert "cp ops/patch059-single-human-authority-policy.v1.json bundle/single-human-authority-policy.v1.json" in workflow
    assert "single-human-authority-policy.example.v1.json" not in workflow
    assert "signed-candidate-handoff.v1.json" in workflow
    assert "release-finalization.v2.json" in workflow
    assert "cosign-release: v2.6.0" in workflow
    assert "inputs.ref" not in workflow


def test_candidate_evidence_accepts_only_exact_authenticated_run(tmp_path):
    _write(tmp_path / "security-decision.json", {"decisionCommit": "b" * 40})
    identity = candidate_evidence.create_identity(
        _candidate_run(producer=True),
        repository=REPOSITORY,
        source_sha=SOURCE,
        release_id=RELEASE_ID,
        security_decision_commit="b" * 40,
        security_decision_path=tmp_path / "security-decision.json",
    )
    candidate_evidence.validate_run_api(_candidate_run(), identity)


def test_candidate_producer_rejects_already_completed_or_unsuccessful_run(tmp_path):
    _write(tmp_path / "security-decision.json", {"decisionCommit": "b" * 40})
    with pytest.raises(
        candidate_evidence.CandidateEvidenceError,
        match="producer run is not in progress",
    ):
        candidate_evidence.create_identity(
            _candidate_run(),
            repository=REPOSITORY,
            source_sha=SOURCE,
            release_id=RELEASE_ID,
            security_decision_commit="b" * 40,
            security_decision_path=tmp_path / "security-decision.json",
        )


def test_candidate_exception_requires_the_sole_human_authority(tmp_path):
    path = tmp_path / "exceptions.json"
    _write(path, [{"approver_id": "someone-else"}])
    with pytest.raises(
        candidate_evidence.CandidateEvidenceError,
        match="wrong Human Authority",
    ):
        candidate_evidence.validate_exception_authority(path)
    _write(path, [{"approver_id": "github:samiphone651-sys#301386823"}])
    candidate_evidence.validate_exception_authority(path)


@pytest.mark.parametrize("release_id", ["line\nbreak", "یونی‌کد", "a" * 129, "-leading"])
def test_candidate_and_release_verifiers_reject_ambiguous_release_ids(
    tmp_path, release_id
):
    _write(tmp_path / "security-decision.json", {"decisionCommit": "b" * 40})
    with pytest.raises(candidate_evidence.CandidateEvidenceError):
        candidate_evidence.create_identity(
            _candidate_run(producer=True),
            repository=REPOSITORY,
            source_sha=SOURCE,
            release_id=release_id,
            security_decision_commit="b" * 40,
            security_decision_path=tmp_path / "security-decision.json",
        )
    with pytest.raises(
        release_evidence.ReleaseVerificationError, match="invalid release ID"
    ):
        release_evidence.verify_bundle(
            tmp_path,
            repository=REPOSITORY,
            issuer=ISSUER,
            workflow_ref=WORKFLOW,
            source_sha=SOURCE,
            release_id=release_id,
            release_sequence=SEQUENCE,
            manifest_sha256="0" * 64,
            now=NOW,
            runner=FixtureCosign(),
        )


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("path", ".github/workflows/attacker.yml"),
        ("event", "pull_request"),
        ("head_branch", "main"),
        ("head_sha", "b" * 40),
        ("conclusion", "failure"),
        ("run_attempt", 3),
        ("actor", {"login": "attacker", "id": 1, "type": "User"}),
        ("repository", {"full_name": "attacker/fork"}),
    ],
)
def test_candidate_evidence_rejects_run_api_substitution(tmp_path, key, value):
    _write(tmp_path / "security-decision.json", {"decisionCommit": "b" * 40})
    run = _candidate_run()
    producer_run = _candidate_run(producer=True)
    identity = candidate_evidence.create_identity(
        producer_run,
        repository=REPOSITORY,
        source_sha=SOURCE,
        release_id=RELEASE_ID,
        security_decision_commit="b" * 40,
        security_decision_path=tmp_path / "security-decision.json",
    )
    run[key] = value
    with pytest.raises(candidate_evidence.CandidateEvidenceError):
        candidate_evidence.validate_run_api(run, identity)


def test_candidate_producer_workflow_has_exact_non_reusable_trigger():
    workflow = (ROOT / ".github/workflows/patch059-candidate-evidence.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in workflow
    assert "pull_request:" not in workflow
    assert "push:" not in workflow
    assert "workflow_call:" not in workflow
    assert "actions: read" in workflow
    assert "candidate-identity.json" in workflow
    assert "produce-pre-decision:" in workflow
    assert "finalize-post-decision:" in workflow
    assert "bind-pre-decision-artifact" in workflow
    assert "PRE-DECISION ONLY" in workflow
    post_decision = workflow.split("  finalize-post-decision:", 1)[1]
    assert "docker buildx build" not in post_decision
    assert "npm ci" not in post_decision
    assert "uv run pytest" not in post_decision
    bind_step = post_decision.split(
        "      - name: Bind final candidate identity and provenance without rebuilding", 1
    )[1].split("      - name: Upload exact successful candidate evidence", 1)[0]
    assert "GH_TOKEN: ${{ github.token }}" in bind_step
    refresh = chr(34) + "$GITHUB_API_URL/repos/$GITHUB_REPOSITORY/actions/runs/$GITHUB_RUN_ID" + chr(34)
    assert refresh in bind_step
    assert bind_step.index(refresh) < bind_step.index(
        "python3 ops/scripts/patch059-candidate-evidence.py create"
    )


def test_pre_decision_handoff_binds_exact_run_artifact_and_scanner_evidence(tmp_path):
    _source, archive, _evidence, artifact = _pre_decision_fixture(tmp_path)
    run = _candidate_run()
    extracted = tmp_path / "extracted"
    identity = candidate_evidence.bind_pre_decision_artifact(
        run=run,
        artifact=artifact,
        repository=REPOSITORY,
        source_sha=SOURCE,
        release_id=RELEASE_ID,
        run_id=run["id"],
        run_attempt=run["run_attempt"],
        artifact_id=artifact["id"],
        artifact_name=artifact["name"],
        artifact_digest=artifact["digest"],
        archive=archive,
        bundle=extracted,
    )
    assert identity["schema"] == "satco.patch059-pre-decision-artifact/v1"
    candidate_evidence.validate_pre_decision_artifact_identity(
        identity,
        evidence_path=extracted / "pre-decision-evidence.json",
        archive_path=archive,
    )


@pytest.mark.parametrize(
    ("target", "key", "value"),
    [
        ("run", "id", 999),
        ("run", "run_attempt", 9),
        ("run", "path", ".github/workflows/attacker.yml"),
        ("run", "event", "push"),
        ("run", "head_branch", "main"),
        ("run", "head_sha", "b" * 40),
        ("run", "repository", {"full_name": "attacker/fork"}),
        ("artifact", "id", 999),
        ("artifact", "digest", "sha256:" + "0" * 64),
        ("artifact", "url", "https://api.github.com/repos/attacker/fork/actions/artifacts/7654321"),
        ("artifact", "expired", True),
    ],
)
def test_pre_decision_handoff_rejects_run_or_artifact_substitution(
    tmp_path, target, key, value
):
    _source, archive, _evidence, artifact = _pre_decision_fixture(tmp_path)
    run = _candidate_run()
    selected = run if target == "run" else artifact
    selected[key] = value
    with pytest.raises(candidate_evidence.CandidateEvidenceError):
        candidate_evidence.bind_pre_decision_artifact(
            run=run,
            artifact=artifact,
            repository=REPOSITORY,
            source_sha=SOURCE,
            release_id=RELEASE_ID,
            run_id=123456,
            run_attempt=2,
            artifact_id=7654321,
            artifact_name=f"patch059-pre-decision-{SOURCE}-{RELEASE_ID}",
            artifact_digest=_digest(archive),
            archive=archive,
            bundle=tmp_path / "extracted",
        )


def test_pre_decision_handoff_rejects_substituted_scanner_evidence(tmp_path):
    source, archive, evidence, artifact = _pre_decision_fixture(tmp_path)
    (source / "trivy-backend.json").write_bytes(b"substituted scanner evidence")
    replacement = tmp_path / "substituted.zip"
    with zipfile.ZipFile(replacement, "w", compression=zipfile.ZIP_STORED) as output:
        for filename in sorted(candidate_evidence.PRE_DECISION_ARCHIVE_FILES):
            output.write(source / filename, filename)
    artifact["digest"] = _digest(replacement)
    with pytest.raises(
        candidate_evidence.CandidateEvidenceError,
        match="trivy-backend.json substitution",
    ):
        candidate_evidence.bind_pre_decision_artifact(
            run=_candidate_run(),
            artifact=artifact,
            repository=REPOSITORY,
            source_sha=SOURCE,
            release_id=RELEASE_ID,
            run_id=123456,
            run_attempt=2,
            artifact_id=7654321,
            artifact_name=artifact["name"],
            artifact_digest=artifact["digest"],
            archive=replacement,
            bundle=tmp_path / "extracted",
        )


def test_pre_decision_handoff_rejects_archive_byte_substitution(tmp_path):
    _source, archive, _evidence, artifact = _pre_decision_fixture(tmp_path)
    archive.write_bytes(archive.read_bytes() + b"substitution")
    with pytest.raises(
        candidate_evidence.CandidateEvidenceError,
        match="archive digest mismatch",
    ):
        candidate_evidence.bind_pre_decision_artifact(
            run=_candidate_run(),
            artifact=artifact,
            repository=REPOSITORY,
            source_sha=SOURCE,
            release_id=RELEASE_ID,
            run_id=123456,
            run_attempt=2,
            artifact_id=7654321,
            artifact_name=artifact["name"],
            artifact_digest=artifact["digest"],
            archive=archive,
            bundle=tmp_path / "extracted",
        )
